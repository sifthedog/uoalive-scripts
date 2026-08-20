# lockpicking — training Lockpicking on one locked box

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/lockpick-training.js` | Target a locked container, pick at it until the lockpicks run out or Lockpicking reaches `GOAL` |

## Why it exists

Lockpicking gains from **failed** attempts, so training it means picking at a lock that is too hard
for you, over and over, until the skill catches up. A box you can already open teaches nothing.

## What it does

It asks once for the container, then each cycle:

1. **Double-click the container.** Some shards will not open a lockpicking cursor for a container the
   client has never asked about (`POKE_BOX`).
2. **Double-click a lockpick** found in the pack by graphic, falling back to the name.
3. **Answer the cursor with the container**, then read the journal against `OUTCOME_TEXT`.

| Outcome | What happens |
| --- | --- |
| `failed`, `broke` | Counted as an attempt — both rolled the skill. `broke` is also counted separately |
| `picked` | Stops: an open box cannot train anything more |
| `tooHard`, `notLocked`, `tooFar`, `noPicks` | Stops, saying which |
| `saving` | Waits the save out, then carries on with every fault counter reset |
| `throttled`, `noCursor` | Backs off further each time, gives up after `MAX_THROTTLED` / `MAX_NO_CURSOR` |
| anything else | Counted unreadable and said once per stretch, but never stops the run |

An empty pack, a skill at `GOAL`, and death each end the run. The skill moving is treated as proof
the attempts are landing whatever the journal said, so a wrong `OUTCOME_TEXT` never ends a run on its
own — the total is reported at the end instead. The one backstop left is `STALL_STOP` cycles in which
neither the journal nor the skill moved.

### Before you paste it

- Stand **next to** the container. Nothing here walks.
- Carry lockpicks and a box locked above your skill. Nothing needs to be equipped.
- A box that opens ends the run, so pick one you cannot get into yet.

### How to run it

```bash
npm run build
```

Then paste `dist/lockpick-training.js` into the client's script editor and click the container when
it asks. The console names the box, the skill and the lockpick count, then a progress line every
`LOG_EVERY` attempts, then a closing line with the skill delta.

## What to set

Everything lives in [`config.ts`](config.ts).

| Setting | Default | What it is for |
| --- | --- | --- |
| `GOAL` | `1000` | The client's tenths, so 100.0. A cap below this is reported, not corrected |
| `LOCKPICK_GRAPHICS` | `0x14fb` | The stock art. A lockpick found by name logs its graphic to paste back in |
| `LOCKPICK_NAME` | `'lockpick'` | Substring match against the name, for a shard with another art |
| `POKE_BOX` / `POKE_DELAY` | `true` / 600 | The double-click on the container before the one on the lockpick |
| `ATTEMPT_DELAY` | 1200 | Pacing between attempts, under the shard's action throttle |
| `PICK_TIMEOUT` | 5000 | How long the journal is watched for an outcome |
| `SKILL_TIMEOUT` / `SKILL_POLL` | 5000 / 250 | The skill list arrives asynchronously |
| `MAX_BLIND_READS` | 20 | Cycles the client may go quiet about the skill before the run gives up |
| `STALL_WARN` / `STALL_STOP` | 100 / 1000 | Cycles in which neither the journal nor the skill moved. Far above the shared figures: at high skill a run picks for minutes between tenths |
| `OUTCOME_TEXT` | — | The shard's wordings. Guesses until a live run confirms them |

## When it goes wrong

**`lockpicks: none found. Pack holds: …`** — `LOCKPICK_GRAPHICS` is wrong for this shard. The
graphic that repeats as often as you have lockpicks is the one to paste in.

**`outcome unreadable - carrying on`** — the shard words its results differently. The run keeps
going; whatever it actually says goes into the matching bucket, and the closing line says how many
were missed.

**`no target cursor`** — the lockpick click did not open one. Usually the lockpick is gone, or the
shard refused and said something `OUTCOME_TEXT` does not have.

**`that container is not locked`** — the box is open, or was never locked. Lock it and run again.

## Notes on the shard

Written against UOAlive.

- **Only a broken pick changes the pack**, and a stack keeps its serial while its `amount` drops — so
  the count, not `client.findObject`, is what a silent shard is read with.
- **The journal is cleared after the container click, not before it.** The container answers that
  click with a line of its own, and cleared any earlier that line is what the attempt reads back.
- **The cursor is cancelled only when one is open.** An unconditional cancel just before an action
  left `target.open` false for the cursor that followed — the same fault
  [`mining/dig.ts`](../mining/dig.ts) documents.

### Known unverified

- Every phrase in `OUTCOME_TEXT`. They are RunUO-family guesses; a miss shows up as an `unknown`
  outcome rather than a silent wrong turn.
- Whether `POKE_BOX` is needed at all here. It is what the run was asked for, and it costs a
  double-click and `POKE_DELAY` per attempt if it is not.
