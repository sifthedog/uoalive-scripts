import { packContents } from '../lib/containers.js';
import { die } from '../lib/die.js';
import { hex } from '../lib/entity.js';
import { dead, firstReason } from '../lib/guards.js';
import { createHeartbeat } from '../lib/heartbeat.js';
import { backoffFor } from '../lib/loop.js';
import { totalMatching } from '../lib/pack.js';
import {
  HEARTBEAT_EVERY,
  HOIST_FROM_BAGS,
  MAX_CYCLES,
  MAX_QUIET_SALES,
  SELL_AT,
  SELL_AT_SLOTS,
  WATCH_BACKOFF,
  WATCH_BACKOFF_MAX,
  WATCH_POLL,
} from './config.js';
import { hoistToPack } from './hoist.js';
import { pickItem } from './pick.js';
import { sellAll } from './sell.js';
import { reasonToSell } from './trigger.js';

// Stand next to a vendor, point at an item once, and this sells a batch of them every time enough
// have piled up. The counting is silent - openSellGump says 'vendor sell' out loud, so polling by
// opening the gump would have the character talking to itself every few seconds all afternoon.

const picked = pickItem() ?? die('sell-watch: nothing to watch');

// Counted by art rather than by name. A graphic is on the item already; a name may have to be asked
// for, and hoist.ts stops asking after three unanswered tooltips - a latch that never resets, which
// over a run of hours would leave the watch blind for the rest of the session. The sale still
// matches by name, because a vendor gump has nothing else to match on.
const isWatched = (item: Item): boolean => item.graphic === picked.graphic;

const held = (): number => totalMatching(isWatched);
const slots = (): number => (packContents() ?? []).length;

const heartbeat = createHeartbeat({
  prefix: 'sell-watch',
  noun: 'sold',
  everyMs: HEARTBEAT_EVERY,
});

// Deliberately not createStallWatch: its job is to end a run that has made no progress in 300
// cycles, and a watch with nothing to sell yet has made no progress on purpose. What needs watching
// here is sales that come back empty, which is the counter below.
let quiet = 0;
let sold = 0;
let stop: string | undefined;

log(
  `sell-watch: watching for ${SELL_AT} x '${picked.name}' ${hex(picked.graphic)} ` +
    `(or ${SELL_AT_SLOTS} pack slots), ${held()} held`,
);

for (let cycle = 0; cycle < MAX_CYCLES && !stop; cycle++) {
  stop = firstReason(dead);
  if (stop) {
    break;
  }

  const inPack = held();
  const due = reasonToSell(inPack, slots());

  if (!due) {
    heartbeat.beat('watching', cycle, sold);
    sleep(WATCH_POLL);
    continue;
  }

  log(`sell-watch: ${due} - selling '${picked.name}'`);

  // Honours the same flag the one-shot script does. Off on this shard, where the vendor reads a
  // bag as readily as the top of the pack, so it costs nothing to leave the branch here.
  if (HOIST_FROM_BAGS) {
    hoistToPack(picked.name);
  }

  const took = sellAll(picked.name);
  sold += took;

  if (took > 0) {
    quiet = 0;
    heartbeat.resetBeat();
    log(`sell-watch: sold ${took}, ${held()} left, ${sold} sold in total`);
    sleep(WATCH_POLL);
    continue;
  }

  // Out of earshot, out of gold, refused in silence, or counting an art whose name the gump does
  // not list - indistinguishable from here, and none of them is fixed by asking again straight
  // away. sellAll has already said which of them it looked like.
  quiet++;

  if (quiet >= MAX_QUIET_SALES) {
    stop = `${MAX_QUIET_SALES} sales in a row took nothing, with ${inPack} x '${picked.name}' still in the pack`;
    break;
  }

  const backoff = backoffFor(quiet, WATCH_BACKOFF, WATCH_BACKOFF_MAX);
  log(`sell-watch: nothing sold (${quiet}/${MAX_QUIET_SALES}), waiting ${backoff / 1000}s`);

  // Reset rather than left to run: this path reports on its own cadence, so the next beat should be
  // a full interval after it rather than landing on top of the line above
  heartbeat.resetBeat();
  sleep(backoff);
}

const reason = stop ?? `hit the ${MAX_CYCLES} cycle backstop`;

log(`sell-watch: ${sold} x '${picked.name}' sold, ${held()} still in the pack`);

// Said through log as well as handed to exit, because how the client renders an exit message is its
// own business and the reason a run ended is the one line that must not be the one that got away
log(`sell-watch: stopping - ${reason}`);
exit(`sell-watch: ${reason}`);
