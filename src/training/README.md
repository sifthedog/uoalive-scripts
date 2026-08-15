# training — raise a skill by casting through a table of stages

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/train.js` | Casts the ability that still gains at the level the skill has reached, meditates when the mana runs out, and stops when the last stage is done |

Configured for **Bushido** out of the box. The stage table in `config.ts` is the whole policy, so
another skill is another table rather than another loop: the loop itself is `src/lib/trainer.ts`, and
`src/necromancy/` is that same loop with a different table under it.

What is in this folder is what Bushido decides — the table, the wordings, the guards, and which
weapon to draw. The cast, the skill read, the mana wait and the stow-and-draw are `src/lib/cast.ts`,
`src/lib/skill.ts`, `src/lib/meditate.ts` and `src/lib/weapon.ts`.

## Why it exists

Written by hand this is a chain of `if (value < 600) … else if (value < 750) …`, and the chain is
where the bugs live: the bounds, their order and whether they cover the whole range are spread across
the branches, so a branch that can never run looks exactly like one that has not run yet.

The script this replaced had `else if (bushido.value < 105)` sitting after the `< 750` branch — `105`
is **10.5**, not 105.0 — so Evasion was never cast once. The table makes each band a row, sorts them,
and `src/lib/stages.test.ts` checks the bounds.

## What it does

1. **Waits for the skill list**, then reads the skill. It never treats a client that has not answered
   as `0` — see *Notes on the shard*.
2. **Picks the stage** the value falls in: the first row whose `upTo` the value is under. The same
   call answers *which ability* and *is there anything left to do*, so the two cannot disagree.
3. **Gathers mana if the pool is short**, which means **stowing the weapon, meditating, and drawing
   the weapon again**. These are weapon abilities and meditation is refused while anything is in hand,
   so the run cannot hold one state for both halves — see *Notes on the shard*.
4. **Casts the stage's ability**, and reads whether it landed from the mana that left the pool and the
   buff that went up, falling back on the journal for *why* when it did not.
5. **Pauses `CAST_DELAY`** and goes round again, until the last stage's `upTo` is passed.

| Outcome | What the loop does |
| --- | --- |
| `cast` | Tallies it and clears the fault counters |
| `fizzled` | Counted, not tallied. A failed casting roll — ordinary, and commoner the lower the skill |
| `alreadyUp` | Waits `BUFF_WAIT`. Not a fault. Only reached with `SKIP_WHEN_BUFFED` on, or when the shard refuses in words |
| `disabled` | Says so: the buff gate is not seeing this ability, so the cast toggled it back off |
| `noMana` | Says the stage's `mana` is understated, then gathers mana |
| `noWeapon` | Draws the weapon again, and only stops if that fails |
| `unskilled` | Stops — the table is aimed at a skill this character cannot use |
| `saving` | Sits out the world save and resets the counters |
| `cooldown` | Backs off, growing. **Never** counted towards a stop — the ability is working as designed |
| `throttled` | Backs off, growing, up to `MAX_THROTTLED` in a row |
| anything else | Counts against `MAX_UNKNOWN`; five in a row ends the run |

### Before you paste it

- Stand somewhere safe. The script **does not move, fight or heal**, and it spends most of its time
  meditating with the weapon in the pack. It stops if you die, and that is the whole of its combat plan.
- Have the weapon you want to train with **in hand**. The graphic is learned from it at start-up, and
  that is what the re-arm matches on afterwards.
- Set `WEAPON_NAME` to something that matches that weapon, for the one case the graphic cannot cover:
  a draw attempted before anything was ever held.
- Check `STAGES` against the skill you actually have. It aims at **105.0**, which needs a power
  scroll; without one the shard caps at 100.0, the run says so at start-up and then never finishes.

### How to run it

```
npm run build
```

then paste `dist/train.js` into the in-game script editor.

## What to set

Everything is in `config.ts`.

### The stages

| Setting | What it is for |
| --- | --- |
| `SKILL` | The skill being trained. `SKILL_LABEL` names it in log lines until the skill list arrives |
| `STAGES` | One row per band: cast `spell` until the skill reaches `upTo`, at `mana` a cast |
| `STAGES[].upTo` | In the client's tenths — 74.6 is `746`, so 105.0 is `1050`. Exclusive |
| `STAGES[].buff` | Optional. Stops the run re-issuing an ability that is already standing, and proves a cast landed without reading the journal |

Rows may be written in any order — `plan.ts` sorts them, and the start-up line prints them in the
order they will be worked.

### The weapon

| Setting | What it is for |
| --- | --- |
| `WEAPON_NAME` | Substring match for the draw, used only before a graphic has been learned |
| `SPARE_BAG_SERIAL` | The bag inside the pack to open when a plain search misses |
| `DISARM_TIMEOUT` / `DISARM_POLL` / `DISARM_ATTEMPTS` | How long a stow is given before it is reissued, and how many times |
| `STRIP_LAYERS` | Every layer that comes off for a trance, in the order it comes off — which is also the order it goes back on. Hands first. Jewellery is deliberately absent, and so is `Layers.Necklace`, because that layer carries gorgets too |
| `STRIP_MOVE_DELAY` | Pause between the individual moves inside one strip, to stay under the shard's action throttle |
| `STRIP_AT_ONCE` | On strips the armour from the first trance instead of waiting to be refused once |

### Mana

| Setting | What it is for |
| --- | --- |
| `MEDITATE` | Off is a run that waits on natural regeneration and never touches the weapon |
| `MEDITATE_TO_FULL` | Fill the pool, or stop as soon as the next cast is affordable |
| `MEDITATE_TIMEOUT` / `MEDITATE_ATTEMPTS` | How long one trance is given, and how many are tried before the stretch is called a failure |
| `MANA_POLL` / `MANA_LOG_EVERY` | How often the pool is read, and how often the wait says how it is coming along |
| `REGEN_TIMEOUT` | How long to wait on natural regeneration when meditation is off or refused |
| `MAX_HUNGRY` | Failed mana stretches in a row before the run gives up |

`MEDITATE_TO_FULL` is **on**, and the reason is the kit rather than the mana: every stretch of
meditation costs a stow and a draw, paid per stretch — and on a shard that also refuses a trance with
armour on, that is up to thirty item moves rather than two. Filling the pool spreads the cost over
many casts.

### Casting and stopping

| Setting | What it is for |
| --- | --- |
| `CAST_TIMEOUT` | How long the shard may take to say something about a cast |
| `CAST_DELAY` | The pause between casts. This is pacing, not a wait — see *Notes on the shard* |
| `COOLDOWN_BACKOFF` / `COOLDOWN_BACKOFF_MAX` | The growing wait when an ability refuses on its own timer. The ceiling is far above `THROTTLE_BACKOFF_MAX` because a cooldown can be most of a minute |
| `SKIP_WHEN_BUFFED` | Leave an ability that is already standing alone instead of recasting it. **Off** — this shard allows the recast, and gating would cap the run at one cast per buff duration |
| `BUFF_WAIT` | How long to leave a standing ability before looking again, where it is skipped |
| `MAX_BLIND_READS` | Cycles the client may answer nothing for the skill before the run stops |
| `OUTCOME_TEXT` / `MEDITATE_OUTCOME_TEXT` | What the shard says. Mostly guesses — see *Known unverified* |

There is **no stall watchdog**, deliberately: this script's cycles are mostly mana coming back on
purpose, so a character with a big pool and slow regeneration would trip it while training perfectly
well. The heartbeat stays, because the trances are the longest silences in the repo.

## When it goes wrong

- **`unreadable outcome (n/5), check OUTCOME_TEXT`** — the phrase tables do not match this shard.
  Read the journal, copy the real wording into the right bucket. This is the expected first-run
  failure, and it is loud on purpose.
- **The run trains fine at Confidence and stalls once it reaches CounterAttack.** The draw is not
  landing: Confidence does not need a weapon on most shards and CounterAttack does. Check
  `WEAPON_NAME`, and check the weapon is not in a bag inside a bag (`SPARE_BAG_SERIAL`).
- **`could not get the weapon back in hand`** — the run stops rather than carrying on, because a
  character holding nothing cannot cast these abilities and cannot defend itself.
- **`shard says wait (n/20)` while casting Evasion.** If it reaches 20 the run stops, and it should
  not: that is the ability's cooldown being read as the action throttle. Check that
  `OUTCOME_TEXT.cooldown` carries the exact wording your shard uses, and that it is listed before
  `throttled`.
- **`the shard refuses meditation (blocked)`** — by the time this fires the weapon *and* everything
  on `STRIP_LAYERS` is already off, so what is refusing the trance is something the run cannot reach:
  jewellery, a layer missing from the list, or a shard that gates meditation another way. The run
  degrades to natural regeneration rather than stopping.
- **`the trance was refused with armour on - took more off, trying again`** — expected, once, on a
  shard that blocks on armour. The lesson latches, so every later trance strips fully up front. Seeing
  it more than once a run means the latch is not holding.
- **`… would not go back on`** — a piece the restore could not return. The run carries on slightly
  weaker and retries it at the next trance; only an empty *hand* ends the run.
- **`refused for mana at N`** — the stage's `mana` is lower than the shard actually charges. Raise it.
- **It stops at 100.0 saying nothing is left to train.** The last stage aims at 105.0 and you have no
  power scroll. The start-up line warned about this.
- **`the client stopped reporting the skill`** — five cycles in a row where `getSkill` answered
  nothing. Usually a client that has lost the skill list; repaste.

## Notes on the shard

- **`player.getSkill()` returns `undefined`, and the typings say so** — the JSDoc example in
  `types/classicuo.d.ts` does not compile under `strict`. Every read goes through `skill.ts`, and a
  blind client is **never** read as `0`: `0` is a real skill value, and taking it would cast the
  first band's ability at a character who has capped the skill.
- **Skill values are integers in tenths.** 74.6 arrives as `746`. Every bound in `STAGES` is in those
  units, and every log line divides by ten to print it.
- **Meditation and weapon abilities want opposite things.** The run stows the weapon for the trance
  and draws it again afterwards, and the draw sits on a single exit path every outcome flows through
  — a timeout, a refusal and a guard firing mid-trance all reach it. Getting this wrong is silent and
  total in both directions.
- **`player.maxMana` reads 0 while the client is refreshing stats**, exactly as `weightMax` does,
  and a ceiling of 0 makes "wait until the pool is full" true the instant it is asked. Read through
  `src/lib/vitals.ts`, and recomputed on every poll rather than captured once.
- **Waiting on `mana != maxMana` does not work.** A regenerating pool passes a figure as often as it
  lands on it, and a maximum that moves — a stat refresh, a buff, a ring taken off — is never equal to
  anything for long. The comparison is `>=`.
- **The same ability can be recast while its buff is still up** — confirmed in play, and why
  `SKIP_WHEN_BUFFED` is off: gating on the buff would cap the run at one cast per buff duration. On a
  RunUO-family shard these are `SpecialMove`s and a second cast *disables* the first, so the gate is
  kept as a setting for a shard that behaves that way.
- **The success wording for an ability is the least trustworthy thing in the phrase table.** Unlike
  the harvest scripts, the journal's job here is to explain failures: a cast is proved by the mana
  leaving the pool and the buff arriving, both of which are wording-free.
- **Evasion has a cooldown of its own, and it is not the action throttle.** `'You must wait before
  trying again'` is the ability's timer; `'You must wait to perform another action'` is the shard
  refusing the run. One is normal and one is worth giving up over, and the first *contains* the bare
  `'You must wait'` that `THROTTLED_TEXT` ends in — so the cooldown bucket is listed first to win the
  match. Bucketed together, the Evasion stage ends every run that reaches it.
- **The Evasion band is rate-limited by that cooldown, not by `CAST_DELAY`.** No timing constant
  shortens it. Confidence and CounterAttack are freely recastable, so the three stages do not run at
  remotely the same speed, and the last one is much the slowest.
- **A fizzle costs no mana here.** `'The spell fizzles'` ended the first live run at five unknowns in
  a row: nothing left the pool, so the mana proof correctly saw no cast and only the wording was
  missing. Fizzles are counted separately in the summary, because a character fizzling most of what
  it casts is training far slower than the cast tally suggests.
- **`'You enter a meditative trance.'` is not a guess** — it is the exact sentence the client's own
  documentation for `journal.waitForTextAny` uses, in a meditation example. It is the only phrase in
  `config.ts` that is not a hypothesis.
- **Two of the endings never ended anything.** The line asking the mana half whether it lost the
  weapon used to assign to the same `stop` the outcome switch had just set, so `unskilled` and the
  twentieth throttle were both overwritten on the way out of the switch. It is `stop = stop ?? …`
  now, and `src/lib/trainer.test.ts` pins both endings.
- **`CAST_DELAY` is pacing, not a wait.** These abilities have a cooldown of their own and the shard
  refuses one that comes too early; a loop with no pause re-arms that timer with every retry. The
  original script had no sleep between casts at all.

### Known unverified

- **Every phrase in `OUTCOME_TEXT`, and every phrase in `MEDITATE_OUTCOME_TEXT` except the trance
  line.** RunUO-family guesses. Nothing load-bearing depends on them: success is proved by mana and
  buffs, and a miss surfaces as `unknown` rather than as a silent wrong turn.
- **Whether `BuffDebuffs.ActiveMeditation` is published here.** Every use of it is a fast path;
  `false` everywhere is the behaviour without it.
- **Whether `client.findItemOnLayer` answers for the player's own layers on this shard.** Everything
  the strip does rests on it. The start-up survey line is the check: if it names nothing on a dressed
  character, nothing will ever be stripped and the run quietly falls back on natural regeneration.
- **Whether fifteen item moves in one burst trip the shard's action throttle** at `STRIP_MOVE_DELAY`.
  A strip that needs its reissue every trance is the symptom, and it is slow rather than dangerous.
- **Whether a pack near the 120-item cap can refuse the strip.** The run logs what would not move and
  carries on.
- **Whether any shard cares about the order gear goes back on.** Each item owns its own layer, so it
  should not; restore order is strip order, so `STRIP_LAYERS` is the fix if one does.
- **Whether jewellery blocks the trance anywhere.** It is left on deliberately — add `Layers.Ring` and
  the rest to `STRIP_LAYERS` if your shard disagrees.
- **Whether `player.dressKr` / `undressKr` are honoured here.** They would strip in one call rather
  than fifteen, but both return `void`, so there would be no proof to poll — which is the whole safety
  story of every item move in this repo. Worth revisiting only if a shard is confirmed to answer them.
- **Whether two identical weapons in the pack confuse the draw.** `createTool` matches on graphic, so
  it would draw whichever it finds first. Harmless, but the log line would name a weapon you did not
  stow.
