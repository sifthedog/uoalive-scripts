# evalint — training Evaluating Intelligence

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/eval-int.js` | Evaluate your own character over and over until Evaluating Intelligence reaches `GOAL` |

## Why it exists

Eval Int trains by repetition, and a **failed** check rolls the skill just as a successful one does.
The awkward part is the shard's own skill timer: nothing in the client API reports it, so a loop
written the obvious way asks again before the timer has expired, re-arms it, and produces a run of
`You must wait a few moments` that never clears.

The target is your own character. Eval Int rolls the same whoever it is aimed at, and a target that
cannot wander off, die or be stabled removes the pick step and every ending that goes with one.

## What it does

Per cycle:

1. **Check the stop conditions** — dead, or the skill at `GOAL`.
2. **Sit out a world save** if one is running, without charging the refusals to anything.
3. **Read the skill.** The number moving is treated as proof the reads are landing, whatever the
   journal looked like.
4. **`useSkill(EvalInt, player.serial)`** — the target is passed to the call, not answered into a
   cursor of its own.
5. **Read the journal** for `EVAL_TIMEOUT`, and branch.
6. **Sleep for the current pace**, which is not a constant — see below.

| Outcome | What happens |
| --- | --- |
| `evaluated` | The shard reported an intellect. Counted, and the pace is allowed to ease |
| `missed` | The skill check failed, which still rolled the skill. Counted the same way |
| `throttled` | The shard's own timer. The pace is *raised* as well as backed off from |
| `unskilled` | Stops. No amount of retrying gets past it |
| `saving` | Waits the save out and carries on |
| anything else | Counted unreadable and said once per stretch, but never stops the run |

### The pace

There is no call that reports the shard's skill delay, and guessing it low is the whole of the
problem this script exists to avoid. So `USE_DELAY` is a **floor**, not the cadence:
[`lib/pace.ts`](../lib/pace.ts) adds `PACE_STEP` every time the shard refuses and takes one back only
after `PACE_EASE_AFTER` reads have landed.

Easing after a single success is the trap: it walks straight back into the refusal it just escaped.

### Before you paste it

- Stand anywhere. Nothing walks, nothing is targeted but you, nothing is picked up.

### How to run it

```bash
npm run build
```

Then paste `dist/eval-int.js` into the client's script editor. The console names the skill and the
goal, then a progress line every `LOG_EVERY` reads, then a closing line with the delta.

## What to set

Everything lives in [`config.ts`](config.ts).

| Setting | Default | What it is for |
| --- | --- | --- |
| `GOAL` | `1000` | The client's tenths, so 100.0. A cap below it is reported, not corrected |
| `USE_DELAY`, `PACE_STEP`, `PACE_MAX`, `PACE_EASE_AFTER` | `1000`, `400`, `8000`, `5` | The pace floor, and how it learns the shard's timer |
| `EVAL_TIMEOUT` | `1000` | How long a read is given to produce a sentence. Matched to `USE_DELAY` |
| `MAX_THROTTLED` | shared | Refusals in a row before the run stops. A backstop — the pace should get there first |
| `SKILL_TIMEOUT` / `SKILL_POLL` | `5000` / `250` | The skill list arrives asynchronously |
| `MAX_BLIND_READS` | `20` | Cycles the client may go quiet about the skill before the run gives up |
| `OUTCOME_TEXT` | — | The shard's wordings. All guesses; see below |

## When it goes wrong

**`shard says wait (n/20), now pacing at Nms`** — working as intended for the first few cycles, and
the number in it is the script finding your shard's delay. A run of them that never stops means the
real delay is above `PACE_MAX`; raise it.

**`outcome unreadable - carrying on`** — the shard words its results differently. Copy what the
journal actually prints into `OUTCOME_TEXT`. The run trains regardless: the skill number moving is
what the loop treats as proof.

**`no progress in 1000 cycles`** — nothing has landed for a long stretch, and the skill has not moved
either. Either the wordings are wrong *and* the reads are being refused, or this shard does not gain
on a self-target.

## Notes on the shard

Written against UOAlive.

- **The enum name is `Skills.EvalInt`**, not `EvaluatingIntelligence`.
- **`useSkill` takes the target**, so there is no separate cursor to answer. A cursor left unanswered
  is what leaves the next cycle asking again while the shard is still waiting on this one.
- **The result may arrive over the character's head rather than as a system message**, so the journal
  read leaves `author` undefined.
- **A missed check is training, not a refusal.** The roll happened either way, so it is counted with
  the successes.
- **The success bucket matches on `intellect` and `mind`, not `mental`** — the failure wordings carry
  `mental`, and a stem that matched both would count a miss as a success.

### Known unverified

- **Every phrase in `OUTCOME_TEXT`.** RunUO-family guesses; a miss shows up as an `unknown` outcome
  rather than a silent wrong turn. Correct them against the real journal after the first run.
- **Whether this shard gains Eval Int on a self-target.** The assumption the script is built on. If
  the skill does not move over a few hundred reads, the shard gates it, and the fix is to pass
  another mobile's serial to `useSkill` — [`lib/pick.ts`](../lib/pick.ts)'s `pickOne` is what
  [`src/animallore`](../animallore/index.ts) uses for that.
- **`PACE_MAX` of 8 seconds**, a guess at the ceiling of this shard's skill timer rather than a
  measurement.
