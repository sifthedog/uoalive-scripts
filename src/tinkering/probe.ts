// Read-only calibration for src/tinkering/config.js. Three invariants keep it from crafting:
//   1. Only category candidates are pressed. RunUO numbers craft-gump buttons 1 + type + index*7,
//      so categories land on 1, 8, 15, ... and items on 2, 9, 16, ...; item buttons are recorded,
//      never pressed.
//   2. Backing out is close() + use(tool), never a button press.
//   3. The ingot total is re-checked after every press; any drop means a press crafted something.
// PROBE_MODE = 'outcome' is the one deliberate exception - see the bottom of the file.
import {
  ALL_OUTCOME_TEXT,
  outcomeFor,
} from './craft.js';
import {
  CRAFT_TIMEOUT,
  GUMP_POLL,
  GUMP_TIMEOUT,
  LOCKPICK_GRAPHIC,
  PROBE_ANNOUNCE,
  PROBE_MAX_TRIALS,
  PROBE_PAGES,
  PROBE_TRIAL_BUTTONS,
  PROBE_TRIAL_DELAY,
  PROBE_TRIAL_PATH,
  OUTCOME_TEXT,
  PROBE_KEYWORDS,
  PROBE_MAX_BUTTON,
  PROBE_MAX_CATEGORIES,
  PROBE_MAX_PAGES,
  PROBE_MODE,
  PROBE_WALK,
  RECIPES,
  STEP_DELAY,
} from './config.js';
import { backToCategories, craftGump, openCraftGump, pageWith } from './gump.js';
import { ingotTotal } from './ingots.js';
import { countsByGraphic, describeDiff, diffCounts } from '../lib/pack.js';
import { die } from '../lib/die.js';
import { hex } from '../lib/entity.js';
import { findTool, toolAlive } from './tool.js';

log('probe: pack contents (graphic / hue / amount / name)');
for (const item of player.backpack?.contents ?? []) {
  log(`probe:   ${hex(item.graphic)} hue ${item.hue ?? 0} x${item.amount ?? 1} "${item.name ?? ''}"`);
}

const skill = player.getSkill(Skills.Tinkering);
log(`probe: tinkering base ${skill?.base}, value ${skill?.value}`);

const baselineIngots = ingotTotal();
log(`probe: ${baselineIngots} ingots matched by INGOT_GRAPHICS + INGOT_HUE`);

const toolSerial = findTool();
if (!toolSerial) {
  die("probe: no tinker's tools in the pack");
}

// Nothing here assumes RunUO's button numbering or that the menu is even a server gump: the
// point is to report what the client actually received, so a miss says why rather than just no.
const acquireGump = (): Gump | undefined => {
  journal.clear();
  player.use(toolSerial);

  let reported = '';

  for (let waited = GUMP_POLL; waited <= GUMP_TIMEOUT; waited += GUMP_POLL) {
    sleep(GUMP_POLL);

    const last = Gump.last;
    const found = craftGump();
    const state = `lastSerial=${hex(Gump.lastSerial)} exists=${Gump.exists(Gump.lastSerial)} last=${last ? 'set' : 'null'} resolved=${found ? 'yes' : 'no'}`;

    if (state !== reported) {
      log(`probe:   +${waited}ms ${state}`);
      reported = state;
    }

    if (found) {
      return found;
    }
  }

  log(`probe: nothing from Gump.last after ${GUMP_TIMEOUT}ms, trying the fallbacks`);

  // A shard may name the menu rather than expose it as the last server gump
  for (const text of ['tinker', 'tinkering', 'craft', 'selection menu']) {
    const found = Gump.findOrWait(text, 1000);
    if (found) {
      log(`probe: found it by text "${text}"`);
      return found;
    }
  }

  // Container and some crafting gumps are local, not server-sent - that is what fromServer false means
  if (Gump.lastSerial) {
    const local = Gump.findOrWait(Gump.lastSerial, 1000, false);
    if (local) {
      log('probe: found it as a LOCAL gump - set fromServer false when opening it');
      return local;
    }
  }

  // A refusal explains a missing gump better than any amount of polling does
  const refusal = journal.waitForTextAny(
    ['must be in your backpack', 'cannot use', 'must wait', 'What do you want', 'do not have'],
    undefined,
    500,
  );
  if (refusal) {
    log(`probe: the shard said "${refusal}" - that is why there is no menu`);
  }

  return undefined;
};

const gump = acquireGump();
if (!gump) {
  log(`probe: no menu from tool ${hex(toolSerial)} (graphic 0x1eb8 "Tool Kit")`);
  log('probe: if lastSerial stayed 0x0 the shard sent no gump at all - try double-clicking the');
  log('probe: tools by hand to confirm the menu opens, and say what it looks like.');
  die('probe: could not acquire the tinkering menu');
}

log(`probe: craft gump serial is ${hex(Gump.lastSerial)}  <- GUMP_SERIAL`);

// hasButton is a local lookup, so scanning the whole range costs nothing and needs no sleeps
const scan = (page: Gump): number[] => {
  const found: number[] = [];
  for (let id = 0; id <= PROBE_MAX_BUTTON; id++) {
    if (page.hasButton(id)) {
      found.push(id);
    }
  }
  return found;
};

const describe = (id: number): string => {
  if (id === 0) {
    return `${id}: cancel/back`;
  }

  const type = (id - 1) % 7;
  const index = Math.floor((id - 1) / 7);

  if (type === 0) {
    return `${id}: category #${index + 1}`;
  }
  if (type === 1) {
    return `${id}: item #${index + 1}`;
  }
  return `${id}: type ${type} index ${index}`;
};

const keywords = (page: Gump, where: string): void => {
  const hits = PROBE_KEYWORDS.filter((word) => page.containsText(word));
  log(`probe: ${where} containsText hits: ${hits.length ? hits.join(', ') : 'NONE'}`);
};

// One line per button is unreadable on a gump with a hundred of them, so batch the IDs
const logIDs = (label: string, ids: number[]): void => {
  if (ids.length === 0) {
    log(`probe: ${label}: none`);
    return;
  }
  log(`probe: ${label} (${ids.length}):`);
  for (let start = 0; start < ids.length; start += 24) {
    log(`probe:   ${ids.slice(start, start + 24).join(' ')}`);
  }
};

const categoryButtons = scan(gump);
logIDs('buttons on the page as opened', categoryButtons);
keywords(gump, 'as opened');

// If every category name and every item name is already matchable, the gump holds the whole
// recipe tree at once and containsText cannot tell one page from another.
log('probe: containsText spans the whole gump, so it cannot identify a page - using buttons only');

// A gump this dense is likely paged rather than reply-driven, so find out whether switchPage
// changes which buttons exist. switchPage is client-side navigation and sends no craft reply.
const sameIDs = (a: number[], b: number[]): boolean =>
  a.length === b.length && a.every((id, i) => id === b[i]);

let paged = false;
let previous = categoryButtons;

for (let page = 1; PROBE_PAGES && page <= PROBE_MAX_PAGES; page++) {
  gump.switchPage(page);
  sleep(GUMP_POLL);

  const here = craftGump();
  if (!here || !here.exists) {
    log(`probe: gump closed while switching to page ${page}`);
    break;
  }

  const ids = scan(here);

  // switchPage past the last page leaves the previous one showing, so a repeat means the end
  if (page > 1 && sameIDs(ids, previous)) {
    log(`probe: page ${page} is identical to page ${page - 1}, so that was the last one`);
    break;
  }

  logIDs(`page ${page}${sameIDs(ids, categoryButtons) ? ' (same as opened)' : ''}`, ids);
  if (!sameIDs(ids, categoryButtons)) {
    paged = true;
  }
  previous = ids;
}

if (PROBE_PAGES) {
  log(`probe: switchPage ${paged ? 'CHANGES the button set - this is one paged gump' : 'changes nothing - pages are not how it navigates'}`);
}

// UOAlive numbers buttons 1 + offset + 20 * group where RunUO uses a stride of 7, so report the
// stride that actually fits before anything tries to derive a button ID from an item's position.
const strideFor = (ids: number[]) => {
  const bases = ids.filter((id) => id > 0);
  for (const stride of [20, 7, 10, 25, 100]) {
    const offsets = new Set(bases.map((id) => (id - 1) % stride));
    if (offsets.size <= 4) {
      return { stride, offsets: [...offsets].sort((a, b) => a - b) };
    }
  }
  return undefined;
};

const shape = strideFor(categoryButtons);
if (shape) {
  const groups = new Set(categoryButtons.filter((id) => id > 0).map((id) => Math.floor((id - 1) / shape.stride)));
  log(`probe: numbering fits id = 1 + offset + ${shape.stride} * group`);
  log(`probe:   ${groups.size} groups, offsets used: ${shape.offsets.join(', ')}`);
}

// Pages are told apart by button presence, so button 2 existing here means the walk below cannot
// distinguish an item page from the page it started on.
if (gump.hasButton(2)) {
  log('probe: button 2 already exists here, so the RunUO-shaped walk cannot tell pages apart');
}

const categories = PROBE_WALK
  ? categoryButtons.filter((id) => id > 0 && (id - 1) % 7 === 0).slice(0, PROBE_MAX_CATEGORIES)
  : [];

if (!PROBE_WALK) {
  log('probe: PROBE_WALK is off, so no button was pressed. Send the lists above.');
}

for (const category of categories) {
  const page = openCraftGump(toolSerial, category);
  if (!page) {
    log(`probe: category page gone before ${category}, stopping the walk`);
    break;
  }

  page.reply(category);

  const itemPage = pageWith(2, GUMP_TIMEOUT);
  if (!itemPage) {
    log(`probe: category ${category} opened nothing with an item button on it`);
    backToCategories(toolSerial, category);
    continue;
  }

  const items = scan(itemPage).filter((id) => (id - 1) % 7 === 1);
  log(`probe: category ${category} -> ${items.length} items: ${items.join(', ')}`);
  keywords(itemPage, `category ${category}`);

  if (ingotTotal() < baselineIngots) {
    die(`probe: ingots dropped after pressing ${category} - that press crafted something, stopping`);
  }

  backToCategories(toolSerial, category);
  sleep(STEP_DELAY);
}

log(`probe: put ${hex(Gump.lastSerial)} in GUMP_SERIAL.`);

if (PROBE_WALK) {
  log('probe: item #N on a category page is button 2 + (N - 1) * 7, counted top to bottom.');
  // containsText is a substring match, so the parts category matches 'ring' through 'springs'
  log('probe: careful - "ring" also matches "springs" and "earrings". Trust the jewelry hit.');
} else {
  log('probe: also say how the menu looks by hand - one window listing everything, or a');
  log('probe: category list you click into - and where lockpick and ring sit in it.');
}

// Presses one button at a time and reports what each did to the pack and to the button set. A
// button that changes the buttons without touching the pack is navigation; one that adds an item
// is a craft, and the graphic it added says which recipe it was.
if (PROBE_MODE === 'trial') {
  // Every press has to start from the same place: a category press moves the selections pane, so
  // trialling without re-walking would test each button against a different list than the last.
  const walkTo = (announce: boolean): Gump | undefined => {
    // Closing is only needed to undo a previous walk. With no path there is nothing to undo, and
    // reopening would risk the tool-use being throttled straight after the close.
    if (PROBE_TRIAL_PATH.length) {
      craftGump()?.close();
      sleep(GUMP_POLL);
    }

    let page = craftGump();

    for (let attempt = 0; !page && attempt < 2; attempt++) {
      player.use(toolSerial);
      page = pageWith(PROBE_TRIAL_PATH[0] ?? 1, GUMP_TIMEOUT) ?? craftGump();
    }

    if (!page) {
      log(`probe: gump did not reopen (lastSerial ${hex(Gump.lastSerial)}, exists ${Gump.exists(Gump.lastSerial)})`);
      return undefined;
    }

    for (const step of PROBE_TRIAL_PATH) {
      page.reply(step);
      sleep(PROBE_TRIAL_DELAY);

      const landed = craftGump();
      if (!landed) {
        return undefined;
      }
      page = landed;
      if (announce) {
        logIDs(`buttons after ${step}`, scan(page));
      }
    }

    return page;
  };

  const landed = walkTo(true);
  if (!landed) {
    die(
      PROBE_TRIAL_PATH.length
        ? `probe: could not walk the path ${PROBE_TRIAL_PATH.join(' -> ')}`
        : 'probe: the menu was not open and would not reopen',
    );
  }

  // Only item-shaped buttons by default: a category press just renavigates, and pressing every
  // button would spend ingots learning nothing about which row makes what.
  const candidates = (
    PROBE_TRIAL_BUTTONS.length ? PROBE_TRIAL_BUTTONS : scan(landed).filter((id) => (id - 2) % 20 === 0)
  ).slice(0, PROBE_MAX_TRIALS);
  log(`probe: trialling ${candidates.length} buttons: ${candidates.join(' ')}`);

  for (const id of candidates) {
    const open = walkTo(false);
    if (!open) {
      log(`probe: could not get back to the start before ${id}, stopping`);
      break;
    }

    const buttonsBefore = scan(open);
    const packBefore = countsByGraphic();

    // Overhead rather than log-only: the log cannot say which entry a button ID belongs to, but
    // whoever is watching the menu can, and the number has to be on screen at the moment it reacts.
    if (PROBE_ANNOUNCE) {
      client.headMsg(`btn ${id}`, player, 66);
      sleep(600);
    }

    open.reply(id);
    sleep(PROBE_TRIAL_DELAY);

    // REPAIR ITEM and ENHANCE ITEM raise a target cursor, which would swallow every later press
    target.cancel();

    const after = craftGump();
    const changes = describeDiff(diffCounts(packBefore, countsByGraphic()));
    const navigated = after ? !sameIDs(scan(after), buttonsBefore) : false;

    log(`probe: ${id} -> pack: ${changes}${after ? (navigated ? ' | NAVIGATED' : '') : ' | GUMP CLOSED'}`);

    if (changes.includes(`0x${LOCKPICK_GRAPHIC.toString(16)}`)) {
      log(`probe: *** ${id} is the lockpick button - put it in RECIPES.lockpicks.item ***`);
      break;
    }
  }
}

// The only path in either script that crafts. It makes exactly one lockpick and reports where the
// result text turned up, which is what settles whether OUTCOME_TEXT can be matched at all.
if (PROBE_MODE === 'outcome') {
  const recipe = RECIPES.lockpicks;

  if (recipe.category === undefined || recipe.item === undefined) {
    die('probe: outcome mode needs RECIPES.lockpicks filled in first');
  }

  const categoryPage = openCraftGump(toolSerial, recipe.category);
  if (!categoryPage) {
    die('probe: outcome mode could not open the category page');
  }
  categoryPage.reply(recipe.category);

  const itemPage = pageWith(recipe.item, GUMP_TIMEOUT);
  if (!itemPage) {
    die(`probe: outcome mode found no button ${recipe.item} - RECIPES.lockpicks.item is wrong`);
  }

  const before = ingotTotal();
  journal.clear();
  log(`probe: outcome mode crafting one ${recipe.label}`);
  itemPage.reply(recipe.item);

  const matched = journal.waitForTextAny(ALL_OUTCOME_TEXT, undefined, CRAFT_TIMEOUT);
  log(`probe: journal matched ${matched ? `"${matched}" -> ${outcomeFor(matched)}` : 'NOTHING'}`);

  const after = craftGump();
  for (const [name, strings] of Object.entries(OUTCOME_TEXT)) {
    const inGump = strings.filter((text) => after?.containsText(text));
    if (inGump.length) {
      log(`probe: the returned gump contains the ${name} text: ${inGump.join(', ')}`);
    }
  }

  log(`probe: ingots ${before} -> ${ingotTotal()}, tool still exists: ${toolAlive(toolSerial)}`);
}
