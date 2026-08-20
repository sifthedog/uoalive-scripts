# hiding — training Hiding and Stealth

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/hiding.js` | Stands still, hides, and once hidden spams Stealth until one fails — then hides again |

## Why it exists

Both skills gain from **failure** as readily as from success: a refused hide rolls Hiding, and a
stealth attempt that reveals you rolls Stealth. The training is the repetition.

## What it does

One attempt per cycle, every `ATTEMPT_DELAY`, and it never moves:

| State | What happens |
| --- | --- |
| Not hidden | `useSkill(Hiding)` |
| Hidden | `useSkill(Stealth)` |

A successful stealth leaves you hidden, so the next cycle stealths again. A failed one reveals you,
so the next cycle hides. Both skills at their goal ends the run.

| Outcome | What happens |
| --- | --- |
| `hidden` | Counted. The next cycle stealths |
| `quietly` | Counted. The next cycle stealths again |
| `failed` (either skill) | Counted — a failure rolls the skill too. A failed stealth sends the next cycle back to hiding |
| `notHidden`, `notHiddenWell` | Hides next cycle regardless of the flag, which is also what raises Hiding past the shard's gate |
| `armour` | Stops: the shard will not stealth in it |
| `busy`, `throttled` | Ignored. Neither rolled the skill, and at this cadence a refusal is the shard's usual answer |
| `saving` | Waits the save out and carries on |
| anything else | Counted unreadable and said once per stretch, but never stops the run |

Death ends the run. Either skill moving is treated as proof the attempts are landing whatever the
journal said, so a wrong phrase table never ends a run on its own — the unread total is reported at
the end instead. A run that is genuinely stuck is caught by `STALL_STOP` cycles without a landed
attempt.

### Before you paste it

- Wear **no armour heavier than leather**. The shard refuses to stealth in it and the run stops.
- Stand anywhere. Nothing needs to be in the pack, and nothing is picked up.

### How to run it

```bash
npm run build
```

Then paste `dist/hiding.js` into the client's script editor. The console names both skills and their
goals, then a progress line every `LOG_EVERY` attempts, then a closing line with both deltas.

## What to set

Everything lives in [`config.ts`](config.ts).

| Setting | Default | What it is for |
| --- | --- | --- |
| `HIDING_GOAL` / `STEALTH_GOAL` | `1000` / `1000` | The client's tenths, so 100.0. A cap below either is reported, not corrected |
| `ATTEMPT_DELAY` | `500` | Between every attempt, both skills |
| `HIDE_TIMEOUT` / `STEALTH_TIMEOUT` | `500` | How long the journal is watched for an outcome |
| `MAX_CYCLES` | `50_000` | Well above the shared figure: most cycles are refusals, not attempts |
| `SKILL_TIMEOUT` / `SKILL_POLL` | `5000` / `250` | The skill list arrives asynchronously |
| `MAX_BLIND_READS` | `20` | Cycles the client may go quiet about a skill before the run gives up |
| `HIDE_TEXT` / `STEALTH_TEXT` | — | The shard's wordings. Guesses except the three confirmed lines |

## When it goes wrong

**`outcome unreadable - carrying on`** — the shard words its results differently. The run keeps
going; whatever it actually says goes into the matching bucket, and the closing line says how many
were missed.

**`no progress in 300 cycles`** — nothing has landed for a long stretch. Either the shard is
refusing every attempt, or its wordings are missing from both tables.

**`the shard will not stealth in this armour`** — take it off and run again.

## Notes on the shard

Written against UOAlive. Confirmed lines: `You have hidden yourself well`, `You begin to move
quietly`, `You fail in your attempt to move unnoticed`.

- **A hide does not have to be revealed first.** Using the skill while already hidden rolls it again.
- **`player.isHidden` is the proof the journal cannot give**, but only on a change — a character
  who was already hidden proves nothing about the use just made, and a flag that was already down
  proves nothing about a stealth that was merely refused.
- **A refusal is the expected answer, not a fault.** One shard timer covers both skills, so at
  `ATTEMPT_DELAY` most attempts are refused. They are deliberately uncounted: counted, they would
  end a working run within seconds.
- **No guards are called and no threat is watched for.** `player.say` reveals a hidden character, so
  the call would undo the thing being trained.

### Known unverified

- Every phrase except the three confirmed lines. They are RunUO-family guesses; a miss shows up as
  an `unknown` outcome rather than a silent wrong turn.
- Whether this shard rolls Stealth on the skill use or only on a step taken while hidden. This run
  only ever uses the skill, so it trains Stealth only if the shard rolls on the use.
