import { beforeEach, describe, expect, it, vi } from 'vitest';

import { installGlobals, mobile, Notorieties, type FakeWorld } from '../test-support/uo.js';
import { createThreatWatch } from './threat.js';

let world: FakeWorld;
let clock = 0;

vi.mock('./clock.js', () => ({ now: () => clock }));

const monster = (fields: Partial<Mobile> = {}) =>
  mobile({
    serial: 0x00099999,
    graphic: 0x0021,
    name: 'a ratman',
    x: 102,
    y: 100,
    hits: 100,
    maxHits: 100,
    notoriety: Notorieties.Gray,
    ...fields,
  });

// The notorieties CALL_ON_SIGHT_NOTORIETY names - a player killer rather than the local wildlife
const aggressor = (fields: Partial<Mobile> = {}) =>
  monster({ name: 'Rakan', notoriety: Notorieties.Murderer, ...fields });

const watch = (overrides: Partial<Parameters<typeof createThreatWatch>[0]> = {}) =>
  createThreatWatch({
    prefix: 'mining',
    range: 12,
    hostile: 30,
    callOnSight: 14,
    companionName: 'beetle',
    call: 'guards',
    calls: 3,
    callDelay: 10_000,
    replyWait: 800,
    noGuardsText: ['The guards cannot be called here'],
    attackText: [],
    guardedText: ['under the protection'],
    unguardedText: ['left the protection'],
    ...overrides,
  });

const said = (): string[] => world.log.mock.calls.map(([line]) => String(line));

beforeEach(() => {
  clock = 0;
  world = installGlobals({ player: { x: 100, y: 100 } });
});

describe('createThreatWatch', () => {
  it('says nothing at all on a quiet cycle', () => {
    watch().check();

    expect(world.player.say).not.toHaveBeenCalled();
    expect(said()).toEqual([]);
  });

  it('calls the guards when something hostile is in range', () => {
    world.client.selectEntity.mockReturnValue(aggressor());

    watch().check();

    expect(world.player.say).toHaveBeenCalledWith('guards');
    expect(said().join('\n')).toContain("'Rakan' 0x21 2 tiles off (murderer)");
  });

  it('ignores a hostile further off than the range', () => {
    world.client.selectEntity.mockReturnValue(monster({ x: 130 }));

    watch().check();

    expect(world.player.say).not.toHaveBeenCalled();
  });

  it('ignores your own pet, whatever it is flagged', () => {
    world.client.selectEntity.mockReturnValue(monster({ isRenamable: true }));

    watch().check();

    expect(world.player.say).not.toHaveBeenCalled();
  });

  it('calls the guards on health going down with nothing in sight', () => {
    const check = watch().check;

    check();
    world.player.hits = 80;
    check();

    expect(world.player.say).toHaveBeenCalledWith('guards');
    expect(said().join('\n')).toContain('nothing in sight, you 80/100');
  });

  // The stat-refresh fault src/lib/vitals.ts exists for: a character at full health reads 0 for a
  // cycle, and reading that as ninety points of damage calls the guards at nobody.
  it('does not read a fall to zero hits as damage', () => {
    const check = watch().check;

    check();
    world.player.hits = 0;
    check();

    expect(world.player.say).not.toHaveBeenCalled();
  });

  it('calls the guards on the companion losing health', () => {
    const beetle = monster({ serial: 0x40000009, name: 'Smokey', hits: 90, isRenamable: true });
    const check = watch({ companion: () => beetle }).check;

    check();
    beetle.hits = 60;
    check();

    expect(world.player.say).toHaveBeenCalledWith('guards');
    expect(said().join('\n')).toContain('beetle 60/100');
  });

  // A pet the client has lost track of reports 0, exactly as a dying one on its last point does not
  it('does not read a companion at zero hits as damage', () => {
    const beetle = monster({ serial: 0x40000009, hits: 90, isRenamable: true });
    const check = watch({ companion: () => beetle }).check;

    check();
    beetle.hits = 0;
    check();

    expect(world.player.say).not.toHaveBeenCalled();
  });

  it('calls again once the cooldown has passed, and not before', () => {
    world.client.selectEntity.mockReturnValue(aggressor());
    const check = watch().check;

    check();
    clock = 9000;
    check();

    expect(world.player.say).toHaveBeenCalledTimes(1);

    clock = 11_000;
    check();

    expect(world.player.say).toHaveBeenCalledTimes(2);
  });

  it('stops at the cap for one episode and starts over after it clears', () => {
    world.client.selectEntity.mockReturnValue(aggressor());
    const check = watch({ calls: 2 }).check;

    for (let tick = 0; tick < 6; tick++) {
      clock = tick * 20_000;
      check();
    }

    expect(world.player.say).toHaveBeenCalledTimes(2);

    world.client.selectEntity.mockReturnValue(undefined);
    check();

    expect(said().join('\n')).toContain('mining: clear');

    world.client.selectEntity.mockReturnValue(aggressor());
    clock += 20_000;
    check();

    expect(world.player.say).toHaveBeenCalledTimes(3);
  });

  it('stops calling for good once the shard says the guards cannot be called here', () => {
    world.client.selectEntity.mockReturnValue(aggressor());
    world.journal.waitForTextAny.mockReturnValue('The guards cannot be called here');
    const check = watch().check;

    check();
    clock = 60_000;
    check();

    expect(world.player.say).toHaveBeenCalledTimes(1);
    expect(said().join('\n')).toContain('not calling again this run');
  });

  it('reports what it can work out about guard protection, once', () => {
    world.client.selectEntity.mockReturnValue(aggressor());
    world.journal.containsText.mockImplementation(
      (text: string) => text === 'under the protection',
    );
    const check = watch().check;

    check();
    clock = 60_000;
    check();

    const protection = said().filter((line) => line.includes('guard protection'));

    expect(protection).toEqual(['mining: guard protection - the journal says guarded']);
  });

  // Every wild cat and crow on this shard is gray, and three 'guards' shouted at a passing cat is
  // what CALL_ON_SIGHT_NOTORIETY exists to stop
  describe('a gray that has done nothing', () => {
    const cat = () => monster({ name: 'a cat', graphic: 0x00c9 });

    it('is reported but not called on', () => {
      world.client.selectEntity.mockReturnValue(cat());

      watch().check();

      expect(world.player.say).not.toHaveBeenCalled();
      expect(said().join('\n')).toContain("'a cat' 0xc9 2 tiles off (gray)");
    });

    it('is still only reported once, however many cycles it stands there', () => {
      world.client.selectEntity.mockReturnValue(cat());
      const check = watch().check;

      check();
      clock = 60_000;
      check();

      expect(said().filter((line) => line.includes('trouble'))).toHaveLength(1);
      expect(world.player.say).not.toHaveBeenCalled();
    });

    it('draws the call the moment it takes a bite out of you', () => {
      world.client.selectEntity.mockReturnValue(cat());
      const check = watch().check;

      check();
      expect(world.player.say).not.toHaveBeenCalled();

      world.player.hits = 80;
      check();

      expect(world.player.say).toHaveBeenCalledWith('guards');
    });

    it('draws the call when it goes for the companion instead', () => {
      const beetle = monster({ serial: 0x40000009, hits: 90, isRenamable: true });
      world.client.selectEntity.mockReturnValue(cat());
      const check = watch({ companion: () => beetle }).check;

      check();
      beetle.hits = 60;
      check();

      expect(world.player.say).toHaveBeenCalledWith('guards');
    });

    it('draws the call when the journal says it is attacking you', () => {
      world.client.selectEntity.mockReturnValue(cat());
      world.journal.containsText.mockImplementation((text: string) => text === '*attacks you*');

      watch({ attackText: ['*attacks you*'] }).check();

      expect(world.player.say).toHaveBeenCalledWith('guards');
    });
  });

  it('takes a journal wording as trouble in its own right', () => {
    world.journal.containsText.mockImplementation((text: string) => text === '*is attacking you*');

    watch({ attackText: ['*is attacking you*'] }).check();

    expect(world.player.say).toHaveBeenCalledWith('guards');
  });
});
