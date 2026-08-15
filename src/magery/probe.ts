// Read-only calibration for the trance strip: it takes nothing off, casts nothing and moves nothing.
// It exists because a strip that does nothing has two completely different causes and the run cannot
// tell them apart from the inside.
//
//  1. The client is not answering `findItemOnLayer` for the player's own layers, so gear.ts sees a
//     naked character and there is nothing for it to take off. Section one below settles that.
//  2. The client answers fine, but this shard's refusal wording is not in MEDITATE_OUTCOME_TEXT's
//     `blocked` list - so the run reads the refusal as `unknown`, never asks for the deeper strip, and
//     the armour stays on. Every phrase in that list is a RunUO-family guess. Section two settles it
//     by using the skill once, dressed, and reporting which wording actually came back.
//
// Stand somewhere safe, wearing exactly what you would train in, with the mana pool NOT full - a full
// pool answers 'You are at peace' and tells us nothing. Then run this.

import { STRIP_LAYERS } from './config.js';

log('probe: --- 1. what the client says is on the character ---');

const named: Array<[string, number]> = Object.entries(Layers).filter(
  (entry): entry is [string, number] => typeof entry[1] === 'number',
);

const seen: string[] = [];

for (const [name, layer] of named) {
  const item = client.findItemOnLayer(player.serial, layer);

  if (item) {
    seen.push(`${name}=${(item.graphic >>> 0).toString(16)} '${item.name ?? ''}'`);
  }
}

// The other view of the same character. The two agree in the real client, so a disagreement here is
// the whole answer: gear.ts reads the first one, and it is the one that can come back empty.
const worn = Object.entries(player.equippedItems).filter(([, item]) => item !== undefined);

log(`probe: findItemOnLayer sees ${seen.length} piece(s): ${seen.join(', ') || 'NOTHING'}`);
log(`probe: equippedItems sees ${worn.length} piece(s): ${worn.map(([key]) => key).join(', ')}`);

if (seen.length === 0 && worn.length > 0) {
  log('probe: >>> findItemOnLayer answers nothing for the player on this shard.');
  log('probe: >>> That is the fault. Nothing will ever be stripped until it is worked around.');
} else if (seen.length < worn.length) {
  log('probe: >>> the two views disagree - the layers missing above will never be stripped');
}

const strippable = STRIP_LAYERS.filter(
  (layer) => client.findItemOnLayer(player.serial, layer) !== undefined,
).length;

log(`probe: ${strippable} of those sit on a layer STRIP_LAYERS actually lists`);

if (strippable < seen.length) {
  log('probe: the rest are on layers STRIP_LAYERS leaves out - jewellery and Necklace, by default');
}

if (player.backpack === undefined) {
  log('probe: >>> the client reports no backpack, so no strip can ever land');
}

log('probe: --- 2. what the shard says when it refuses a trance ---');

if (player.mana >= player.maxMana && player.maxMana > 0) {
  log('probe: the pool is full, so the answer will be "at peace" and will tell us nothing.');
  log('probe: spend some mana and run this again.');
} else {
  // Deliberately wider than any one folder's table: the point is to find the wording, so every
  // RunUO/ServUO phrasing worth trying goes in and the log says which one landed.
  const CANDIDATES = [
    'You enter a meditative trance',
    'You are at peace',
    'You cannot focus your concentration with an equipped weapon',
    'You cannot focus your concentration with an equipped shield',
    'You cannot meditate with a weapon equipped',
    'You cannot meditate while holding',
    'You are preoccupied with thoughts of battle',
    'You cannot focus your concentration',
    'You lose your concentration',
    'Regenerative forces cannot penetrate your armor',
    'Your armor is too heavy',
    'You must wait',
    'You are not skilled enough',
  ];

  journal.clear();
  player.useSkill(Skills.Meditation);

  const matched = journal.waitForTextAny(CANDIDATES, undefined, 3000);

  if (matched) {
    log(`probe: the shard said "${matched}"`);
  } else {
    log('probe: the shard said none of the wordings this probe knows.');
    log('probe: read the journal by eye and copy the exact line into MEDITATE_OUTCOME_TEXT.blocked.');
  }

  // The proof that does not go through the journal at all
  const buff = player.waitForBuffDebuff(BuffDebuffs.ActiveMeditation, 2000);

  log(`probe: ActiveMeditation buff answered ${buff === null ? 'nothing' : String(buff)}`);

  if (buff === true) {
    log('probe: the trance STARTED while dressed - armour is not what is blocking you here.');
    log('probe: if mana still crawls, this shard slows regeneration rather than refusing the trance,');
    log('probe: and STRIP_AT_ONCE = true is the setting that answers it.');
  }
}

log('probe: --- what to do with this ---');
log('probe: armour only comes off after a refusal whose wording is in MEDITATE_OUTCOME_TEXT.blocked.');
log('probe: if section 2 shows no such refusal, set STRIP_AT_ONCE = true in config.ts instead.');
