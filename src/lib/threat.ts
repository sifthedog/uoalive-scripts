import { now } from './clock.js';
import { distanceTo, hex, nameOf } from './entity.js';
import { hitsCeiling } from './vitals.js';

export interface ThreatOptions {
  prefix: string;
  range: number;

  // A SearchEntityOptions bitmask
  hostile: number;

  companion?: () => Mobile | undefined;
  companionName: string;

  call: string;
  calls: number;
  callDelay: number;
  replyWait: number;
  noGuardsText: string[];
  attackText: string[];
  guardedText: string[];
  unguardedText: string[];
}

export interface ThreatWatch {
  check: () => void;
}

// Notorieties, so the line that opens an episode says why the thing matched HOSTILE_NOTORIETY
const NOTORIETY = [
  'unknown',
  'innocent',
  'ally',
  'gray',
  'criminal',
  'enemy',
  'murderer',
  'invulnerable',
];

// 0 is what the client reports while it is refreshing stats, and what it reports for a mobile it has
// lost track of, so a fall to 0 is no news at all.
const dropped = (was: number, is: number): boolean => was > 0 && is > 0 && is < was;

export const createThreatWatch = (options: ThreatOptions): ThreatWatch => {
  let lastHits = 0;
  let lastCompanionHits = 0;
  let lastCall = 0;
  let calls = 0;
  let episode = false;
  let noGuards = false;
  let saidProtection = false;
  let zone: string | undefined;

  const nearest = (mask: number, type: number): Mobile | undefined => {
    const found = client.selectEntity(mask, SearchEntityRangeOptions.Nearest, type, false);

    if (!found || found.serial === player.serial || found.isDead) {
      return undefined;
    }

    return distanceTo(found) <= options.range ? found : undefined;
  };

  // isRenamable is how the rest of the repo tells your own pet from a stranger's, and a pet flagged
  // gray by whatever it was fighting would otherwise read as the thing attacking you.
  const hostileNear = (): Mobile | undefined => {
    const found = nearest(options.hostile, SearchEntityTypeOptions.Any);

    return found && !found.isRenamable ? found : undefined;
  };

  const readZone = (): void => {
    if (options.guardedText.some((text) => journal.containsText(text))) {
      zone = 'guarded';
    } else if (options.unguardedText.some((text) => journal.containsText(text))) {
      zone = 'unguarded';
    }
  };

  // Nothing in the API answers this. A yellow human is a guard or a vendor, and either one means a
  // town, which is the best the client can be asked.
  const protection = (): string => {
    if (zone) {
      return `the journal says ${zone}`;
    }

    const yellow = nearest(SearchEntityOptions.Invulnerable, SearchEntityTypeOptions.Human);

    return yellow
      ? `an invulnerable '${nameOf(yellow)}' in sight, so probably a town`
      : 'nothing in sight to say either way';
  };

  const callGuards = (): void => {
    if (noGuards || (options.calls > 0 && calls >= options.calls)) {
      return;
    }

    const at = now();

    if (calls > 0 && at - lastCall < options.callDelay) {
      return;
    }

    lastCall = at;
    calls++;

    if (!saidProtection) {
      saidProtection = true;
      log(`${options.prefix}: guard protection - ${protection()}`);
    }

    log(
      `${options.prefix}: calling the guards (${calls}${options.calls > 0 ? `/${options.calls}` : ''})`,
    );
    player.say(options.call);

    if (options.noGuardsText.length === 0) {
      return;
    }

    const refused = journal.waitForTextAny(options.noGuardsText, undefined, options.replyWait);

    if (refused) {
      noGuards = true;
      log(`${options.prefix}: the shard says '${refused}' - not calling again this run`);
    }
  };

  const describe = (hostile: Mobile | undefined, friend: Mobile | undefined): string => {
    const who = hostile
      ? `'${nameOf(hostile)}' ${hex(hostile.graphic)} ${distanceTo(hostile)} tiles off ` +
        `(${NOTORIETY[hostile.notoriety] ?? hostile.notoriety})`
      : 'nothing in sight';

    const mine = `you ${player.hits}/${hitsCeiling() ?? '?'}`;
    const theirs = friend
      ? `, ${options.companionName} ${friend.hits}/${friend.maxHits || '?'}`
      : '';

    return `${who}, ${mine}${theirs}`;
  };

  return {
    check: () => {
      readZone();

      const hits = player.hits;
      const hurt = dropped(lastHits, hits);

      if (hits > 0) {
        lastHits = hits;
      }

      const friend = options.companion?.();
      const friendHits = friend?.hits ?? 0;
      const friendHurt = dropped(lastCompanionHits, friendHits);

      if (friendHits > 0) {
        lastCompanionHits = friendHits;
      }

      const said = options.attackText.some((text) => journal.containsText(text));
      const hostile = hostileNear();

      if (!hostile && !hurt && !friendHurt && !said) {
        if (episode) {
          episode = false;
          calls = 0;
          log(`${options.prefix}: clear`);
        }

        return;
      }

      if (!episode) {
        episode = true;
        log(`${options.prefix}: trouble - ${describe(hostile, friend)}`);
      }

      callGuards();
    },
  };
};
