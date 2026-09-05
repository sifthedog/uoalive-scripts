import { beforeEach, describe, expect, it, vi } from 'vitest';
import { installGlobals, type FakeWorld } from '../test-support/uo.js';

let world: FakeWorld;

const loadEvaluate = async (config: Record<string, unknown> = {}) => {
  vi.doMock('./config.js', async () => ({
    ...(await vi.importActual<object>('./config.js')),
    EVAL_TIMEOUT: 100,
    ...config,
  }));

  return import('./evaluate.js');
};

// waitForTextAny answers with the phrase it matched, which is what outcomeFor maps back to a bucket
const says = (line: string) => {
  world.journal.waitForTextAny = vi.fn((text: string[]) => text.find((one) => line.includes(one)) ?? null);
};

beforeEach(() => {
  vi.resetModules();
  vi.doUnmock('./config.js');
  world = installGlobals();
});

describe('evaluateOnce', () => {
  it('uses the skill against the character itself rather than through a cursor of its own', async () => {
    const { evaluateOnce } = await loadEvaluate();

    evaluateOnce();

    expect(world.player.useSkill).toHaveBeenCalledWith(Skills.EvalInt, world.player.serial);
  });

  it('clears the target queue first', async () => {
    const { evaluateOnce } = await loadEvaluate();

    evaluateOnce();

    expect(world.target.clearQueue).toHaveBeenCalled();
  });

  it('cancels a live cursor, and only a live one', async () => {
    const { evaluateOnce } = await loadEvaluate();

    evaluateOnce();
    expect(world.target.cancel).not.toHaveBeenCalled();

    world.target.open = true;
    evaluateOnce();
    expect(world.target.cancel).toHaveBeenCalled();
  });

  it('clears the journal before the attempt, so the read is of this one', async () => {
    const { evaluateOnce } = await loadEvaluate();

    evaluateOnce();

    const [cleared] = world.journal.clear.mock.invocationCallOrder;
    const [used] = world.player.useSkill.mock.invocationCallOrder;

    expect(cleared).toBeLessThan(used);
  });

  it('reads a successful evaluation', async () => {
    const { evaluateOnce } = await loadEvaluate();

    says('That looks like a mind of average intellect');

    expect(evaluateOnce()).toBe('evaluated');
  });

  it('tells a missed check from a refused one', async () => {
    const { evaluateOnce } = await loadEvaluate();

    says('You cannot judge their mental abilities');

    expect(evaluateOnce()).toBe('missed');
  });

  it('reads the shard asking it to wait', async () => {
    const { evaluateOnce } = await loadEvaluate();

    says('You must wait to perform another action');

    expect(evaluateOnce()).toBe('throttled');
  });

  it('stops rather than retries when the shard says the skill is not there', async () => {
    const { evaluateOnce, STOP_REASON } = await loadEvaluate();

    says('You are not skilled enough');

    expect(evaluateOnce()).toBe('unskilled');
    expect(STOP_REASON.unskilled).toBeDefined();
  });

  it('comes back unknown when the shard says nothing', async () => {
    const { evaluateOnce } = await loadEvaluate();

    expect(evaluateOnce()).toBe('unknown');
  });

  it('does not read a miss as an evaluation, though both talk about the mind', async () => {
    const { ALL_OUTCOME_TEXT, outcomeFor } = await loadEvaluate();

    const line = 'You have no idea of their mental abilities';
    const matched = ALL_OUTCOME_TEXT.filter((text) => line.includes(text));

    expect(matched).not.toHaveLength(0);
    expect(matched.map(outcomeFor)).toEqual(matched.map(() => 'missed'));
  });
});
