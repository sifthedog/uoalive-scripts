import { beforeEach, describe, expect, it, vi } from 'vitest';
import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { createBandager, type Bandager, type HealText } from './heal.js';

const BANDAGE_GRAPHIC = 0x0e21;

const bandages = item({ serial: 0x4000_0201, graphic: BANDAGE_GRAPHIC, name: 'clean bandages' });

const TEXT: HealText = {
  healed: ['You finish applying the bandages'],
  noBandages: ['You do not have a bandage'],
  interrupted: ['You have been interrupted'],
};

let world: FakeWorld;

// The floor this run bandages to, written the way src/necromancy/guards.ts writes it
const FLOOR = 0.5;

const bandager = (): Bandager =>
  createBandager({
    prefix: 'necro',
    graphic: BANDAGE_GRAPHIC,
    outcomeText: TEXT,
    timeoutMs: 8000,
    cursorTimeoutMs: 2000,
    attempts: 4,
    recovered: () => world.player.hits >= world.player.maxHits * FLOOR,
    waitOutSave: vi.fn(),
  });

// A pack with bandages in it
const stocked = (): void => {
  world.client.findType.mockReturnValue(bandages);
};

// One application that puts a fixed amount back
const heals = (by: number): void => {
  world.player.use.mockImplementation(() => {
    world.player.hits += by;
  });
};

beforeEach(() => {
  world = installGlobals();
  world.player.hits = 30;
  world.player.maxHits = 100;
});

describe('mend', () => {
  it('does nothing at all to a character who is above the floor', () => {
    world.player.hits = 100;
    stocked();

    expect(bandager().mend()).toBe(true);
    expect(world.player.use).not.toHaveBeenCalled();
  });

  it('uses a bandage from the pack and answers the cursor with the character', () => {
    stocked();
    heals(40);

    expect(bandager().mend()).toBe(true);
    expect(world.player.use).toHaveBeenCalledWith(bandages.serial);
    expect(world.target.waitTargetSelf).toHaveBeenCalled();
  });

  // The pack rather than the world: findType with no source would happily return a bandage lying on
  // the floor, and using that opens a cursor over nothing
  it('looks for bandages in the pack rather than anywhere in the world', () => {
    stocked();
    heals(40);

    bandager().mend();

    expect(world.client.findType).toHaveBeenCalledWith(
      BANDAGE_GRAPHIC,
      undefined,
      world.player.backpack?.serial,
    );
  });

  // One bandage heals a fraction of a pool, so the wait is for the floor and not for one application
  it('keeps bandaging until the character is back above the floor', () => {
    stocked();
    heals(10);

    expect(bandager().mend()).toBe(true);
    expect(world.player.use).toHaveBeenCalledTimes(2);
  });

  it('gives up after enough bandages rather than standing there forever', () => {
    stocked();
    heals(0);

    expect(bandager().mend()).toBe(false);
    expect(world.player.use).toHaveBeenCalledTimes(4);
  });

  // The one failure nothing retried fixes, and the caller's answer to it is to let the guard end the
  // run - so it is said once rather than attempted three more times
  it('stops looking once the pack has no bandages left', () => {
    const mender = bandager();

    expect(mender.mend()).toBe(false);
    expect(mender.empty()).toBeDefined();
    expect(world.player.use).not.toHaveBeenCalled();
  });

  it('does not go back to the pack on a later cycle once it has run out', () => {
    const mender = bandager();

    mender.mend();
    world.client.findType.mockClear();
    mender.mend();

    expect(world.client.findType).not.toHaveBeenCalled();
  });

  // The shard's word for it, in case the pack search found something that was not really there
  it('takes the shard s word that there are no bandages', () => {
    stocked();
    world.journal.waitForTextAny.mockReturnValue('You do not have a bandage');

    const mender = bandager();

    expect(mender.mend()).toBe(false);
    expect(mender.empty()).toBeDefined();
    expect(world.player.use).toHaveBeenCalledTimes(1);
  });

  // An interrupted bandage is answered by another bandage, which is exactly what an empty pack is not
  it('applies another bandage after one that was interrupted', () => {
    stocked();
    world.journal.waitForTextAny.mockReturnValue('You have been interrupted');

    expect(bandager().mend()).toBe(false);
    expect(world.player.use).toHaveBeenCalledTimes(4);
  });

  // The hits are the proof, exactly as the mana is for a cast: a shard whose wordings this table has
  // wrong still heals
  it('reads health that went up as a heal, with the journal silent', () => {
    stocked();
    heals(40);

    expect(bandager().mend()).toBe(true);
  });

  it('does not use a bandage when no cursor ever opened', () => {
    stocked();
    world.target.waitTargetSelf.mockReturnValue(false);

    expect(bandager().mend()).toBe(false);
  });

  it('cancels a cursor left open by something else before it uses the bandage', () => {
    stocked();
    heals(40);

    bandager().mend();

    expect(world.target.cancel).toHaveBeenCalled();
  });

  // Nothing is going to heal a corpse, and the guard is about to end the run anyway
  it('stops bandaging a character who has died mid-application', () => {
    stocked();
    world.player.use.mockImplementation(() => {
      world.player.isDead = true;
    });

    expect(bandager().mend()).toBe(false);
    expect(world.player.use).toHaveBeenCalledTimes(1);
  });
});
