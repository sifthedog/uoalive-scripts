import { vi } from 'vitest';

// A fake of the ClassicUO scripting environment, good enough to run the scripts' logic without a
// client. The real globals are ambient `declare const`s, so everything here goes on globalThis by
// assignment - see installGlobals for why that rather than vi.stubGlobal.

// The client's Item/Mobile are classes with far more members than any test needs. Tests describe
// only the fields the code under test reads, and these do the cast once so the tests stay readable.
export const item = (fields: Partial<Item> & { serial: number; graphic: number }): Item =>
  fields as unknown as Item;

export const mobile = (fields: Partial<Mobile> & { serial: number; graphic: number }): Mobile =>
  ({ _tag: 'Mobile', ...fields }) as unknown as Mobile;

// A land tile or static as getTerrainList returns them
export const tile = (fields: {
  x: number;
  y: number;
  z?: number;
  graphic: number;
  isLand?: boolean;
}) => ({ z: 0, isLand: false, ...fields });

// Real values, copied from types/classicuo.d.ts. walk.ts builds its direction table from Directions
// at import time and haul.ts reads Layers.Backpack, so wrong values would fail silently rather than
// loudly.
export const Directions = {
  North: 0,
  Right: 1,
  East: 2,
  Down: 3,
  South: 4,
  Left: 5,
  West: 6,
  Up: 7,
} as const;

export const Layers = { Invalid: 0, OneHanded: 1, TwoHanded: 2, Backpack: 21 } as const;

// The client's Skills/Spells/BuffDebuffs are real TypeScript enums, so they carry the reverse mapping
// and plan.ts leans on it to make a spell name itself in a log line. The stand-ins do the same, or a
// test would pass on a script that logs 'spell 402' at every stage change.
const enumOf = (members: Record<string, number>): Record<string, number | string> => {
  const table: Record<string, number | string> = { ...members };

  for (const [name, value] of Object.entries(members)) {
    table[value] = name;
  }

  return table;
};

// Real values, copied from types/classicuo.d.ts, and only the members the scripts name
export const Skills = enumOf({ Meditation: 46, Bushido: 52 });

export const Spells = enumOf({
  HonorableExecution: 401,
  Confidence: 402,
  Evasion: 403,
  CounterAttack: 404,
  LightningStrike: 405,
  MomentumStrike: 406,
});

export const BuffDebuffs = enumOf({
  ActiveMeditation: 1013,
  HonorableExecution: 1092,
  Confidence: 1093,
  Evasion: 1094,
  CounterAttack: 1095,
  LightningStrike: 1096,
  MomentumStrike: 1097,
});

// What getSkill answers with. Tenths, like the client: 74.6 is 746.
export const skill = (fields: { value: number; name?: string; cap?: number }) => ({
  index: 52,
  name: 'Bushido',
  lock: 0,
  base: fields.value,
  cap: 1200,
  canBeUsable: true,
  ...fields,
});

export interface FakePlayer {
  // The character's own serial, which mount.ts double-clicks to get off a mount
  serial: number;
  x: number;
  y: number;
  z: number;
  weight: number;
  weightMax: number;
  isDead: boolean;
  mana: number;
  maxMana: number;
  backpack?: { serial: number; contents?: Item[] };
  equippedItems: { oneHanded?: Item; twoHanded?: Item; mount?: Item };
  use: ReturnType<typeof vi.fn>;
  equip: ReturnType<typeof vi.fn>;
  moveItem: ReturnType<typeof vi.fn>;
  moveItemOnGroundOffset: ReturnType<typeof vi.fn>;
  run: ReturnType<typeof vi.fn>;
  say: ReturnType<typeof vi.fn>;
  useItemInHand: ReturnType<typeof vi.fn>;
  cast: ReturnType<typeof vi.fn>;
  useSkill: ReturnType<typeof vi.fn>;
  getSkill: ReturnType<typeof vi.fn>;
  hasBuffDebuff: ReturnType<typeof vi.fn>;
  waitForBuffDebuff: ReturnType<typeof vi.fn>;
}

export interface FakeClient {
  findObject: ReturnType<typeof vi.fn>;
  findAllMobilesOfType: ReturnType<typeof vi.fn>;
  findItemOnLayer: ReturnType<typeof vi.fn>;
  getTerrainList: ReturnType<typeof vi.fn>;
  getStatic: ReturnType<typeof vi.fn>;
  headMsg: ReturnType<typeof vi.fn>;
  queryItemOPL: ReturnType<typeof vi.fn>;
  sendSellRequest: ReturnType<typeof vi.fn>;
  closeAllGumps: ReturnType<typeof vi.fn>;
}

export interface FakeTarget {
  // Whether a cursor is up, which the harvest scripts read only to report it
  open: boolean;

  cancel: ReturnType<typeof vi.fn>;
  wait: ReturnType<typeof vi.fn>;
  terrain: ReturnType<typeof vi.fn>;
  waitTargetEntity: ReturnType<typeof vi.fn>;
  waitTargetSelf: ReturnType<typeof vi.fn>;
  query: ReturnType<typeof vi.fn>;
}

export interface FakeJournal {
  clear: ReturnType<typeof vi.fn>;
  containsText: ReturnType<typeof vi.fn>;
  waitForTextAny: ReturnType<typeof vi.fn>;
}

export interface FakeWorld {
  player: FakePlayer;
  client: FakeClient;
  target: FakeTarget;
  journal: FakeJournal;
  gump: Record<string, ReturnType<typeof vi.fn>>;
  log: ReturnType<typeof vi.fn>;
  sleep: ReturnType<typeof vi.fn>;
  exit: ReturnType<typeof vi.fn>;
}

export interface WorldOverrides {
  player?: Partial<FakePlayer>;
  client?: Partial<FakeClient>;
  target?: Partial<FakeTarget>;
  journal?: Partial<FakeJournal>;
  backpack?: Item[];
}

// Deliberately inert: nothing is found, nothing is in the journal, every wait succeeds. A test that
// depends on an outcome has to say so, so the fixture never quietly supplies the thing under test.
const defaults = (): FakeWorld => ({
  player: {
    serial: 0x00000001,
    x: 100,
    y: 100,
    z: 0,
    weight: 0,
    weightMax: 400,
    isDead: false,

    // Rested and unhurt, which is this fixture's version of inert: a character with nothing to wait
    // for. Deliberately not 0/0 - that is the stat-refresh fault src/lib/vitals.ts exists for, and
    // making it the default would quietly put every test on that path.
    mana: 50,
    maxMana: 50,

    backpack: { serial: 0x40000000, contents: [] },
    equippedItems: {},
    use: vi.fn(),
    equip: vi.fn(),
    moveItem: vi.fn(),
    moveItemOnGroundOffset: vi.fn(),
    run: vi.fn(),
    say: vi.fn(),
    useItemInHand: vi.fn(),
    cast: vi.fn(),
    useSkill: vi.fn(),

    // Inert on the 'nothing is found' side rather than the 'every wait succeeds' side: a skill the
    // client has not been told about, and a buff nobody put up. A trainer test has to supply both,
    // which is the point - the fixture must never quietly answer the question under test.
    getSkill: vi.fn(() => undefined),
    hasBuffDebuff: vi.fn(() => false),
    waitForBuffDebuff: vi.fn(() => null),
  },
  client: {
    findObject: vi.fn(() => undefined),
    findAllMobilesOfType: vi.fn(() => []),
    findItemOnLayer: vi.fn(() => undefined),
    getTerrainList: vi.fn(() => []),
    getStatic: vi.fn(() => undefined),
    headMsg: vi.fn(),
    queryItemOPL: vi.fn(() => undefined),
    sendSellRequest: vi.fn(() => true),
    closeAllGumps: vi.fn(),
  },
  target: {
    open: false,
    cancel: vi.fn(),
    wait: vi.fn(() => true),
    terrain: vi.fn(),
    waitTargetEntity: vi.fn(() => true),
    waitTargetSelf: vi.fn(() => true),
    // Inert like the rest: a cursor nobody clicks answers with nothing
    query: vi.fn(() => undefined),
  },
  journal: {
    clear: vi.fn(),
    containsText: vi.fn(() => false),
    waitForTextAny: vi.fn(() => undefined),
  },
  gump: {
    exists: vi.fn(() => false),
    findOrWait: vi.fn(() => undefined),
    waitForVendorGumpData: vi.fn(() => undefined),
  },
  log: vi.fn(),
  // A no-op, so the poll loops in pickaxe.ts and boards.ts finish instantly instead of
  // busy-waiting the way QuickJS does
  sleep: vi.fn(),
  exit: vi.fn(),
});

// Assigned onto globalThis rather than stubbed, because a module can read globals while it is
// being evaluated - walk.ts builds DIRECTION_BY_STEP from Directions - so the values have to be
// there before the import, not just before the test body.
export const installGlobals = (overrides: WorldOverrides = {}): FakeWorld => {
  const world = defaults();

  Object.assign(world.player, overrides.player);
  Object.assign(world.client, overrides.client);
  Object.assign(world.target, overrides.target);
  Object.assign(world.journal, overrides.journal);

  if (overrides.backpack) {
    world.player.backpack = { serial: 0x40000000, contents: overrides.backpack };
  }

  const scope = globalThis as Record<string, unknown>;

  scope.player = world.player;
  scope.client = world.client;
  scope.target = world.target;
  scope.journal = world.journal;
  scope.Gump = world.gump;
  scope.Directions = Directions;
  scope.Layers = Layers;
  scope.Skills = Skills;
  scope.Spells = Spells;
  scope.BuffDebuffs = BuffDebuffs;
  scope.log = world.log;
  scope.sleep = world.sleep;
  scope.exit = world.exit;

  return world;
};
