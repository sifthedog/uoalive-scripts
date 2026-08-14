// Tinker's tools. The graphic is the reliable matcher; the name only arrives with tooltip data.
// UOAlive calls them "Tool Kit", so matching on 'tinker' would never hit.
export const TOOL_NAME = 'tool kit';
export const TOOL_GRAPHICS = new Set([0x1eb8, 0x1ebc]);

// Optional: pin the bag holding spare tools instead of discovering it
export const SPARE_BAG_SERIAL: number | undefined = undefined;

// Iron ingots. Like ore piles, an ingot stack's graphic changes with its size, so match the
// whole art range and pin the hue instead - hue 0 is iron, coloured ores keep their own hue.
export const INGOT_GRAPHICS = new Set([0x1bef, 0x1bf0, 0x1bf1, 0x1bf2]);
export const INGOT_HUE = 0;

// Skill gates, in tenths the way getSkill() reports them: 95.0 is 950
export const LOCKPICK_FROM = 450;
export const RING_FROM = 950;
export const STOP_AT = 1000;

// UOAlive's tinkering gump, and the same value across sessions, so it is a type id rather than an
// instance. Pinning it matters: Gump.last goes null on this shard while the gump is still open,
// and Gump.exists(serial) keeps reporting it correctly.
export const GUMP_SERIAL = 0xcd9950d1;

// Buttons are 1 + kind + 20 * row: kind 0 selects a category, 1 makes an item, 2 opens its detail
// box. LAST TEN is not a numbered category, so the nine category buttons start at Jewelry - the
// off-by-one that made an earlier run select Parts while believing it had selected Tools.
export const CATEGORIES = {
  jewelry: 1,
  woodenItems: 21,
  tools: 41,
  parts: 61,
  utensils: 81,
  miscellaneous: 101,
  assemblies: 121,
  traps: 141,
  magicJewelry: 161,
};

// Row 1 is the top of the selections pane. Every row's button is sent whatever page is on screen -
// there are 26 of them against 10 visible - so a row is pressed directly and NEXT PAGE is not used.
export const ITEM_BUTTON = (row: number): number => 2 + (row - 1) * 20;

// Unused: every row's button is live regardless of the page shown, so nothing needs paging to
// reach. Kept at 0 so craft.js skips the hop entirely.
export const NEXT_PAGE_BUTTON: number | undefined = undefined;

// Set `item` with ITEM_BUTTON(row), counting rows from the top of the category's list and carrying
// on across NEXT PAGE - lockpick being the 17th entry in Tools would be ITEM_BUTTON(17) = 322.
export type RecipeName = 'lockpicks' | 'rings';

export interface Recipe {
  label: string;
  category: number;
  nextPages: number;
  // undefined until the probe identifies the button; the run refuses to start without it
  item: number | undefined;
}

// What a recipe looks like once the probe has identified its button
export type CalibratedRecipe = Recipe & { item: number };

export const isCalibrated = (recipe: Recipe): recipe is CalibratedRecipe =>
  recipe.item !== undefined;

export const RECIPES: Record<RecipeName, Recipe> = {
  lockpicks: { label: 'lockpick', category: CATEGORIES.tools, nextPages: 0, item: undefined },
  rings: { label: 'ring', category: CATEGORIES.jewelry, nextPages: 0, item: undefined },
};

// How the shard words each outcome. Matched as substrings, so punctuation drift is harmless.
// These are the stock RunUO strings - PROBE_MODE = 'outcome' confirms them against UOAlive.
export const OUTCOME_TEXT = {
  success: ['You create the item', 'You create an exceptional quality item'],
  failed: ['You failed to create the item'],
  noMaterial: ['You do not have sufficient metal', 'lack the required materials'],
  wornOut: ['You have worn out your tool'],
  throttled: ['You must wait'],
};

// Pause between cycles, to stay under the server's action throttle
export const STEP_DELAY = 400;

// How long a gump page may take to arrive, and how often to look for it
export const GUMP_TIMEOUT = 5000;
export const GUMP_POLL = 200;

// A tinkering craft plays an animation before the server resolves it
export const CRAFT_TIMEOUT = 8000;

// Hard cycle cap, so a mis-calibrated button ID cannot spin forever
export const MAX_CYCLES = 5000;

// How many cycles may resolve into nothing observable before giving up
export const MAX_UNKNOWN = 5;

// How many times the gump may fail to come back before the run ends
export const MAX_REOPENS = 5;

// Consecutive "you must wait" refusals before giving up, and the backoff between them. The pause
// grows each time: a fixed retry shorter than the shard's own timer re-arms the throttle it is
// waiting out, and that spins silently rather than ending.
export const MAX_THROTTLED = 20;
export const THROTTLE_BACKOFF = 1000;
export const THROTTLE_BACKOFF_MAX = 8000;

// Progress line every this many crafts
export const LOG_EVERY = 25;

// Stop this far short of the weight cap, and this far short of the 125-item container limit
export const WEIGHT_BUFFER = 40;
export const PACK_LIMIT = 120;

// Probe only: highest button ID to test. Ten categories at a stride of 20 reach 181, and the
// bottom-row buttons sit past that, so 160 truncated the scan and hid the last two categories.
export const PROBE_MAX_BUTTON = 600;
export const PROBE_MAX_CATEGORIES = 12;

// What a finished lockpick looks like, so a trial press can prove which button made it. From the
// probe's own pack dump; the ring graphic is filled in once a trial press produces one.
export const LOCKPICK_GRAPHIC = 0x14fc;
export const RING_GRAPHIC: number | undefined = undefined;

// Probe only: switchPage closed the gump on UOAlive, so leave this off unless retesting it
export const PROBE_PAGES = false;
export const PROBE_MAX_PAGES = 12;

// Probe only: buttons to press before trialling, so a trial can run inside a category. LAST TEN
// is category row 0, and it lists recipes you have made by hand on a single page - no NEXT PAGE
// needed, which is what makes it reachable when the bottom-row buttons are still unidentified.
// Empty on purpose: a path is replayed before every single trial, so a wrong first step gets
// pressed dozens of times and drowns out the one button being identified.
export const PROBE_TRIAL_PATH: number[] = [];

// Probe only: which buttons a trial run presses. Empty means the item rows of the page it lands
// on, which is what you want after walking into a category. The kind-6 bottom row was tried and
// none of 7..247 made anything, so MAKE LAST is not reachable that way.
// The low buttons the first scan actually reported, which is where the categories and the top of
// the selections pane should live. Announced one at a time so each ID can be matched to an entry.
export const PROBE_TRIAL_BUTTONS = [1, 2, 3, 7, 21, 22, 23, 41, 42, 43, 61, 62, 63];

// Probe only: cap on presses per trial run, so a trial cannot spend the whole ingot stack
export const PROBE_MAX_TRIALS = 13;

// Probe only: how long to let a trial press resolve before reading the pack back. Long enough to
// watch the menu react, since which button an ID maps to is read off the screen, not the log.
export const PROBE_TRIAL_DELAY = 2500;

// Probe only: call out the button ID overhead just before pressing it, so the number can be
// matched to whichever entry in the menu visibly reacts.
export const PROBE_ANNOUNCE = true;

// Probe only: press category-shaped buttons to map the item lists. Keep this off until the
// layout is understood - on an unfamiliar gump a "category" press may well craft something.
export const PROBE_WALK = false;

// Probe only: words to test containsText() against on every page
export const PROBE_KEYWORDS = [
  'tinker',
  'tools',
  'parts',
  'utensils',
  'assemblies',
  'jewelry',
  'traps',
  'wooden',
  'miscellaneous',
  'lockpick',
  'ring',
];

// Probe only. 'scan' presses nothing. 'trial' presses one button at a time and reports what each
// one did, which is how the item buttons get identified. 'outcome' crafts exactly ONE lockpick to
// learn how the shard reports a result, and needs RECIPES.lockpicks filled in first.
// 'scan' is the safe default and presses nothing. Do not leave this on 'trial': the button
// numbering is not understood, so a trial run presses arbitrary entries - it has crafted junk and
// toggled NON QUEST ITEM in the past.
export const PROBE_MODE: 'scan' | 'trial' | 'outcome' = 'scan';
