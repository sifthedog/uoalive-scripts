# animallore — training Animal Lore

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/animal-lore.js` | Target a creature once, then read it over and over until Animal Lore reaches `GOAL` |

## Why it exists

Animal Lore trains by repetition on a single creature, and a **failed** read rolls the skill just as
a successful one does. What makes it awkward to script is that the shard says nothing when a read
works — it opens a gump and nothing else — so a loop written the obvious way has no idea whether it
is training or being refused, and keeps asking either way. That is what produces a run of
`You must wait a few moments` that never clears: every attempt re-arms the shard's skill timer, so
sitting there longer does not help while the script is still hammering.

## What it does

Target the creature once at the start. Then, per cycle:

1. **Check the stop conditions** — dead, the creature gone, the skill at `GOAL`.
2. **Sit out a world save** if one is running, without charging the refusals to anything.
3. **Read the skill.** The number moving is treated as proof the reads are landing, whatever the
   journal looked like.
4. **`useSkill(AnimalLore, serial)`** — the creature is passed to the call, not answered into a
   cursor of its own.
5. **Poll for the gump, then the journal**, and branch.
6. **Close the gump**, by name.
7. **Sleep for the current pace**, which is not a constant — see below.

| Outcome | What happens |
| --- | --- |
| `lored` | The gump opened. Counted, and the pace is allowed to ease |
| `missed` | The skill check failed, which still rolled the skill. Counted the same way |
| `throttled` | The shard's own timer. The pace is *raised* as well as backed off from |
| `tooFar` | Counted and waited on up to `MAX_AWAY` — a pet wanders off and wanders back |
| `notAnimal`, `notYours`, `unskilled` | Stops. No amount of retrying gets past any of them |
| `saving` | Waits the save out and carries on |
| anything else | Counted unreadable and said once per stretch, but never stops the run |

### The pace

There is no call that reports the shard's skill delay, and guessing it low is the whole of the
problem this script exists to avoid. So `READ_DELAY` is a **floor**, not the cadence:
[`pace.ts`](pace.ts) adds `PACE_STEP` every time the shard refuses and takes one back only after
`PACE_EASE_AFTER` reads have landed. A run settles on the real delay within a few cycles instead of
oscillating between a read and a refusal.

Easing after a single success is the trap: it walks straight back into the refusal it just escaped,
and half the cycles go to waiting.

### Before you paste it

- Stand **next to the creature** and stay there. Nothing walks in this script.
- It must be something the shard will lore — your own tamed pet is the safe choice.
- Nothing needs to be in the pack, and nothing is picked up.

### How to run it

```bash
npm run build
```

Then paste `dist/animal-lore.js` into the client's script editor and target the creature when the
cursor comes up. The console names the creature and the skill, then a progress line every `LOG_EVERY`
reads, then a closing line with the delta.

## What to set

Everything lives in [`config.ts`](config.ts).

| Setting | Default | What it is for |
| --- | --- | --- |
| `GOAL` | `1000` | The client's tenths, so 100.0. A cap below it is reported, not corrected |
| `LORE_GUMP_TEXT` | `Loyalty Rating` | How the gump is recognised. Its own wording — `Attributes` would match half the gumps in the game |
| `LORE_GUMP_BUTTON` | `undefined` | The id the gump's ✕ answers to, for a shard that sends it non-closable. Only needed if the run says the gump would not close |
| `LORE_TIMEOUT` / `LORE_POLL` | `2000` / `150` | How long a read is given to produce a gump or a sentence, and how often both are checked |
| `READ_DELAY`, `PACE_STEP`, `PACE_MAX`, `PACE_EASE_AFTER` | `1000`, `400`, `8000`, `5` | The pace floor, and how it learns the shard's timer |
| `MAX_AWAY` | `20` | Reads in a row out of range before the run gives up on the creature coming back |
| `MAX_THROTTLED` | shared | Refusals in a row before the run stops. A backstop — the pace should get there first |
| `SKILL_TIMEOUT` / `SKILL_POLL` | `5000` / `250` | The skill list arrives asynchronously |
| `MAX_BLIND_READS` | `20` | Cycles the client may go quiet about the skill before the run gives up |
| `OUTCOME_TEXT` | — | The shard's wordings. All guesses; see below |

## When it goes wrong

**`shard says wait (n/20), now pacing at Nms`** — working as intended for the first few cycles, and
the number in it is the script finding your shard's delay. A run of them that never stops means the
real delay is above `PACE_MAX`; raise it.

**`outcome unreadable - carrying on`** — the shard words its results differently, *or* the gump is
not being recognised. Check `LORE_GUMP_TEXT` against what is actually drawn on it first, since a
successful read has no sentence to match.

**`the gump did not close`** — the server sent it non-closable, so its ✕ is a real button rather
than a window control. Probe the ids with `hasButton` and set `LORE_GUMP_BUTTON`. Said once per run,
not once per read.

**`no progress in 1000 cycles`** — nothing has landed for a long stretch. Either the creature is not
lorable, or both the gump text and the wordings are wrong.

**`'…' is gone`** — the creature stopped resolving. Stabled, killed, or led away.

## Notes on the shard

Written against UOAlive.

- **A read that works says nothing at all.** The gump is the only proof, which is why
  [`lore.ts`](lore.ts) polls for it rather than waiting on the journal — a plain journal wait would
  cost the whole `LORE_TIMEOUT` on every success, which is every cycle that matters.
- **The gump is checked before the journal each poll**, because success is the common case and the
  silent one.
- **`useSkill` takes the target**, so there is no separate cursor to answer. A cursor left unanswered
  is what leaves the next cycle asking again while the shard is still waiting on this one.
- **`target.query()` answers with a `TargetInfo`, not a serial** — the serial has to be read off it.
  [`lib/pick.ts`](../lib/pick.ts) does that, and is what this script targets through.
- **`Gump.closeAll()` is not used.** It is the client's *Close Gumps* hotkey and shuts your pack,
  your vendor window and everything else along with the lore gump.
- **A missed read is training, not a refusal.** `You can't think of anything you know offhand` is a
  failed skill check, and the roll happened either way — so it is counted with the successes.

### Known unverified

- **Every phrase in `OUTCOME_TEXT`.** RunUO-family guesses; a miss shows up as an `unknown` outcome
  rather than a silent wrong turn. `missed` matters most — read wrong, it costs the run its count of
  what is actually training.
- **`LORE_GUMP_TEXT`.** `Loyalty Rating` is read off a UOAlive pet gump. A shard whose gump words it
  differently reads every successful lore as `unknown`.
- **Whether the gump closes.** The one on UOAlive draws its own ✕, which is what a non-closable gump
  looks like; `LORE_GUMP_BUTTON` is there for that and is unset until someone confirms the id.
- **`PACE_MAX` of 8 seconds**, which is a guess at the ceiling of this shard's skill timer rather
  than a measurement.
- Whether this shard rolls the skill on a read of a creature already lored recently, or gates
  repeat reads on the same target the way some shards gate taming.
