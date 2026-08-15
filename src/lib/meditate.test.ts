import { beforeEach, describe, expect, it, vi } from 'vitest';
import { installGlobals, item, type FakeWorld } from '../test-support/uo.js';
import { dead, firstReason } from './guards.js';
import { createManaWait, type ManaWait, type MeditateText } from './meditate.js';

const katana = item({ serial: 0x4000_0101, graphic: 0x13ff, name: 'a katana' });

let world: FakeWorld;

const TEXT: MeditateText = {
  trance: ['You enter a meditative trance.'],
  full: ['You are at peace'],
  blocked: ['You cannot focus your concentration with an equipped shield'],
  unfocused: ['You cannot focus your concentration.'],
  saving: ['The world is saving'],
};

// The two hooks a weapon trainer passes, standing in for src/training/weapon.ts - which has its own
// tests. What this module has to get right is that they are called, and that the restore is called on
// every way out of the wait.
const stow = (): boolean => {
  const held = world.player.equippedItems.oneHanded;

  if (!held) {
    return true;
  }

  world.player.moveItem(held.serial, 0x40000000);

  return world.player.equippedItems.oneHanded === undefined;
};

const restore = (): boolean => {
  world.player.equip(katana.serial);

  return world.player.equippedItems.oneHanded !== undefined;
};

const waitFor = (overrides: Partial<Parameters<typeof createManaWait>[0]> = {}): ManaWait =>
  createManaWait({
    prefix: 'train',
    outcomeText: TEXT,
    meditate: true,
    toFull: true,
    timeoutMs: 20_000,
    attempts: 4,
    startTimeoutMs: 2000,
    pollMs: 500,
    logEveryMs: 10_000,
    regenTimeoutMs: 120_000,
    stow,
    restore,
    stopReason: () => firstReason(dead),
    resetBeat: vi.fn(),
    waitOutSave: vi.fn(),
    ...overrides,
  });

// A character holding a weapon, on a client that lets it be stowed and drawn again
const armed = (): void => {
  world.player.equippedItems.oneHanded = katana;

  world.player.moveItem.mockImplementation(() => {
    world.player.equippedItems.oneHanded = undefined;
    world.player.backpack = { serial: 0x40000000, contents: [katana] };

    return 1;
  });

  world.player.equip.mockImplementation(() => {
    world.player.equippedItems.oneHanded = katana;
  });
};

const fillsThePool = (): void => {
  world.player.useSkill.mockImplementation(() => {
    world.player.mana = 50;
  });
};

beforeEach(() => {
  world = installGlobals();
  world.player.mana = 0;
  world.player.maxMana = 50;
});

describe('manaTarget', () => {
  it('is the whole pool, so one trance pays for many casts', () => {
    expect(waitFor().manaTarget(10)).toBe(50);
  });

  // The stat-refresh fault. Taken raw, a ceiling of 0 would make every wait end the instant it
  // started, and the run would cast with no mana forever.
  it('never takes a maximum of 0 as the target', () => {
    world.player.maxMana = 0;

    expect(waitFor().manaTarget(10)).toBe(10);
  });

  it('gathers only what the cast needs when the wait is not to full', () => {
    expect(waitFor({ toFull: false }).manaTarget(10)).toBe(10);
  });
});

describe('regainMana', () => {
  it('does nothing when the pool is already there', () => {
    world.player.mana = 50;
    armed();

    expect(waitFor().regainMana(10)).toBe(true);
    expect(world.player.moveItem).not.toHaveBeenCalled();
    expect(world.player.useSkill).not.toHaveBeenCalled();
  });

  // The comparison the original script got wrong. It waited on `mana != maxMana`, and a regenerating
  // pool passes a figure as often as it lands on it - so a pool that overshot never satisfied it.
  it('is satisfied by a pool that overshot the target', () => {
    world.player.mana = 60;

    expect(waitFor().regainMana(10)).toBe(true);
    expect(world.player.useSkill).not.toHaveBeenCalled();
  });

  it('does not read a maximum of 0 as a pool that is already full', () => {
    world.player.maxMana = 0;
    world.player.mana = 5;
    fillsThePool();

    waitFor().regainMana(10);

    expect(world.player.useSkill).toHaveBeenCalled();
  });

  // Meditation is refused with anything in hand, so the stow is what makes the trance possible at all
  it('stows the weapon before it uses the skill', () => {
    armed();
    fillsThePool();

    waitFor().regainMana(10);

    expect(world.player.moveItem).toHaveBeenCalledWith(katana.serial, 0x40000000);
    expect(world.player.useSkill).toHaveBeenCalledWith(Skills.Meditation);
  });

  it('draws the weapon again once the pool is full', () => {
    armed();
    fillsThePool();

    const mana = waitFor();

    expect(mana.regainMana(10)).toBe(true);
    expect(world.player.equippedItems.oneHanded).toBe(katana);
    expect(mana.blocked()).toBeUndefined();
  });

  // The invariant that matters: every way out of the wait goes past the draw. A character left
  // holding nothing casts into a permanent refusal and cannot defend itself.
  it('draws the weapon again even when the mana never came back', () => {
    armed();

    expect(waitFor().regainMana(10)).toBe(false);
    expect(world.player.equippedItems.oneHanded).toBe(katana);
  });

  it('draws the weapon again when a guard ends the wait', () => {
    armed();
    world.player.isDead = true;

    expect(waitFor().regainMana(10)).toBe(false);
    expect(world.player.equippedItems.oneHanded).toBe(katana);
  });

  it('reports a weapon it could not get back, which is the one thing that ends the run', () => {
    armed();
    fillsThePool();
    world.player.equip.mockImplementation(() => undefined);

    const mana = waitFor();
    mana.regainMana(10);

    expect(mana.blocked()).toBeDefined();
  });

  // A caster's hands are empty already, so there is nothing to take off and nothing that can be left
  // in the pack
  it('meditates with no hooks at all, and can never report a lost weapon', () => {
    fillsThePool();

    const mana = waitFor({ stow: undefined, restore: undefined });

    expect(mana.regainMana(10)).toBe(true);
    expect(world.player.useSkill).toHaveBeenCalledWith(Skills.Meditation);
    expect(world.player.moveItem).not.toHaveBeenCalled();
    expect(mana.blocked()).toBeUndefined();
  });

  it('waits on natural regeneration rather than meditating when meditation is off', () => {
    armed();

    expect(waitFor({ meditate: false }).regainMana(10)).toBe(false);
    expect(world.player.useSkill).not.toHaveBeenCalled();
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  // Using the skill again is at best a wasted action and at worst the shard ending the very trance
  // this attempt is waiting on
  it('does not use the skill again while a trance is already running', () => {
    armed();
    world.player.hasBuffDebuff.mockReturnValue(true);

    waitFor().regainMana(10);

    expect(world.player.useSkill).not.toHaveBeenCalled();
  });

  it('gives up rather than hanging when the pool never moves', () => {
    armed();

    expect(waitFor().regainMana(10)).toBe(false);
    expect(world.player.useSkill).toHaveBeenCalledTimes(4);
  });

  // Only once there is nothing left to take off. What is refusing the trance is then something the
  // run cannot reach, and nothing retried fixes it.
  it('stops meditating for the rest of the run once the shard refuses outright', () => {
    armed();
    world.journal.waitForTextAny.mockReturnValue(
      'You cannot focus your concentration with an equipped shield',
    );

    const mana = waitFor({ stripMore: () => false });

    mana.regainMana(10);
    world.player.moveItem.mockClear();
    mana.regainMana(10);

    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  // A world save is silent in exactly the way a refusal is, so it must not be read as one
  it('does not give up meditation over a world save', () => {
    armed();
    world.journal.waitForTextAny.mockReturnValue('The world is saving');

    const mana = waitFor();

    mana.regainMana(10);
    world.player.moveItem.mockClear();
    mana.regainMana(10);

    expect(world.player.moveItem).toHaveBeenCalled();
  });

  // A refusal with the hands already empty says the armour is the problem, and a caller that can
  // undress answers it by undressing rather than by writing off the rest of the run
  it('takes more off and uses the skill again when the shard refuses the trance', () => {
    armed();
    fillsThePool();
    world.journal.waitForTextAny.mockReturnValueOnce(
      'You cannot focus your concentration with an equipped shield',
    );

    const stripMore = vi.fn(() => true);

    waitFor({ stripMore }).regainMana(10);

    expect(stripMore).toHaveBeenCalledTimes(1);
    expect(world.player.useSkill).toHaveBeenCalledTimes(2);
  });

  // The escalation costs one attempt and can only ever cost one, because stripMore answers false from
  // its second call onwards. Without that this loops until the attempt budget runs out.
  it('asks for a deeper strip once, then gives up the way it always did', () => {
    armed();
    world.journal.waitForTextAny.mockReturnValue(
      'You cannot focus your concentration with an equipped shield',
    );

    let more = true;
    const stripMore = vi.fn(() => {
      const answer = more;
      more = false;

      return answer;
    });

    const mana = waitFor({ stripMore });

    mana.regainMana(10);
    world.player.moveItem.mockClear();
    mana.regainMana(10);

    expect(stripMore).toHaveBeenCalledTimes(2);
    expect(world.player.moveItem).not.toHaveBeenCalled();
  });

  it('never asks for a deeper strip when the shard says the skill is too low', () => {
    armed();
    world.journal.waitForTextAny.mockReturnValue('You are not skilled enough');

    const stripMore = vi.fn(() => true);

    waitFor({
      outcomeText: { ...TEXT, unskilled: ['You are not skilled enough'] },
      stripMore,
    }).regainMana(10);

    expect(stripMore).not.toHaveBeenCalled();
  });

  it('puts everything back after a deeper strip that did not save the trance', () => {
    armed();
    world.journal.waitForTextAny.mockReturnValue(
      'You cannot focus your concentration with an equipped shield',
    );

    expect(waitFor({ stripMore: () => true }).regainMana(10)).toBe(false);
    expect(world.player.equip).toHaveBeenCalledWith(katana.serial);
  });

  it('behaves as it always did for a caller that cannot strip any further', () => {
    armed();
    world.journal.waitForTextAny.mockReturnValue(
      'You cannot focus your concentration with an equipped shield',
    );

    waitFor().regainMana(10);

    expect(world.player.useSkill).toHaveBeenCalledTimes(1);
  });

  // The difference between one item and fifteen: a strip that moves four pieces and fails on the
  // fifth answers false, and gating the restore on that answer leaves those four in the pack for the
  // rest of the run
  it('puts back what a stow had already moved even though the stow itself failed', () => {
    armed();

    const restore = vi.fn(() => true);

    waitFor({
      stow: () => {
        world.player.moveItem(katana.serial, 0x40000000);

        return false;
      },
      restore,
    }).regainMana(10);

    expect(restore).toHaveBeenCalled();
  });

  // Nothing was taken off, so there is nothing to put back - and calling restore at a character this
  // wait never touched is how an unarmed run ends on a draw that finds nothing
  it('does not restore on a run that never undressed anybody', () => {
    armed();

    const restore = vi.fn(() => true);

    waitFor({ meditate: false, restore }).regainMana(10);

    expect(restore).not.toHaveBeenCalled();
  });

  // The latch is one run's, not the process's - which is the whole reason this is a factory
  it('does not carry a refusal over into another script s wait', () => {
    armed();
    world.journal.waitForTextAny.mockReturnValue(
      'You cannot focus your concentration with an equipped shield',
    );

    waitFor().regainMana(10);
    world.player.moveItem.mockClear();
    waitFor().regainMana(10);

    expect(world.player.moveItem).toHaveBeenCalled();
  });
});
