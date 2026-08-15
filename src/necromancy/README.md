# necromancy — raise Necromancy through its five bands

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/necro.js` | Casts the spell that still gains at the level Necromancy has reached, meditates when the mana runs out, and stops when the last stage is done |

| Band | Spell | Mana | What it is |
| --- | --- | --- | --- |
| 40.0 – 50.0 | Pain Spike | 5 | Cast **at your own character** |
| 50.0 – 70.0 | Horrific Beast | 11 | A form, which stands until it is re-cast |
| 70.0 – 90.0 | Wither | 23 | An **area attack**. It hits everything standing near you |
| 90.0 – 100.0 | Lich Form | 23 | A form, and it **drains your health** while you are in it |
| 100.0 – 120.0 | Vampiric Embrace | 23 | A form |

## Why it exists

It is `src/training/` for a different skill, and the whole reason it is a folder rather than a copy:
the loop, the cast, the skill read and the mana wait are all in `src/lib/`, and what is here is the
table, the wordings, and the three things Necromancy does that Bushido does not.

- **Three of the five bands are transformations.** A form stands until it is re-cast, so
  `SKIP_WHEN_BUFFED` has to be off and the toggle back off is counted as the cast it is
  (`DISABLED_IS_PROGRESS`) — the shard rolls the skill and charges the mana for it either way.
- **The run hurts its own character.** Pain Spike is cast at it and Lich Form drains it, so there is
  a health floor (`HURT_FLOOR`) rather than only a check for a corpse — and at that floor the run
  **bandages itself**, before the guard is asked. The guard is what is left when that cannot keep up.
- **Nothing is ever held.** These are spellbook spells and meditation wants empty hands, so unlike the
  weapon trainer the two halves of the run want the same thing — there is no stow, no draw, and no
  `noWeapon` outcome.

## What it does

1. **Waits for the skill list**, then reads Necromancy. A client that has not answered is never read
   as `0` — see `src/training/README.md`, *Notes on the shard*.
1. **Bandages the character** if it is under `HURT_FLOOR`, one bandage at a time until it is back
   above the line or the pack is empty. Then, and only then, the guards get to look at it.
2. **Picks the stage** the value falls in: the first row whose `upTo` the value is under. The same
   call answers *which spell* and *is there anything left to do*.
3. **Meditates if the pool is short**, filling it right up before going back to casting.
4. **Casts the stage's spell**, and reads whether it landed from the mana that left the pool and the
   buff that went up or came down, falling back on the journal for *why* when it did not.
5. **Pauses `CAST_DELAY`** and goes round again, until 120.0 is passed.

| Outcome | What the loop does |
| --- | --- |
| `cast` | Tallies it and clears the fault counters |
| `disabled` | Tallies it too — the form coming off is how you leave it |
| `fizzled` | Counted, not tallied. A failed casting roll — ordinary, and commoner the lower the skill |
| `noReagents` | **Stops.** Nothing waited for refills a pouch |
| `formLocked` | **Stops.** The shard will not cast in the form the character is in — see *Known unverified* |
| `noMana` | Says the stage's `mana` is understated, then gathers mana |
| `alreadyUp` | Waits `BUFF_WAIT`. Only reached with `SKIP_WHEN_BUFFED` on, or when the shard refuses in words |
| `unskilled` | Stops — the table is aimed at a skill this character cannot use |
| `saving` | Sits out the world save and resets the counters |
| `throttled` | Backs off, growing, up to `MAX_THROTTLED` in a row |
| `alreadyCasting` | Waits `CASTING_WAIT` and asks again. Never counted towards a stop — the last cast simply has not finished |
| anything else | Counts against `MAX_UNKNOWN`; five in a row ends the run |

### Before you paste it

- **Stand somewhere empty.** Wither is an area attack and hits everything near you for a fifth of the
  run. In town that is the guards; near anything tamed or blue it is a criminal flag. The script does
  not move, fight or heal.
- **Your kit comes off for each trance and goes straight back on.** Meditation is refused while
  anything is held, so the run stows what is in hand before every trance and puts it back before the
  next cast — the *exact* items, by serial, so Faster Casting, Lower Mana Cost and Mana Regeneration
  come back with them. If the shard also refuses a trance with armour on, the run learns that from its
  own refusal, takes the armour off too, and remembers; jewellery is left alone. `STRIP_LAYERS` is the
  list. The start-up line names everything that will come off — if it names nothing on a dressed
  character, the client is not answering and the run will fall back on natural regeneration.
- **Carry reagents**, and enough of them: bat wing, daemon blood, grave dust, nox crystal and pig
  iron. Running out ends the run by name.
- **Carry clean bandages** — bloodied ones are a different item and cannot be applied. The start-up
  line says so if the pack has none, and without them the health floor goes back to being only a stop.
- **Check where your skill actually is.** The table starts at 40.0; below that the first band still
  casts Pain Spike, which the shard allows from 20.0.
- It aims at **120.0**, which needs the power scrolls. Without them the shard caps at 100.0, the
  start-up line says so, and the run will sit at the cap until it is stopped by hand.

### How to run it

```
npm run build
```

then paste `dist/necro.js` into the in-game script editor.

## What to set

Everything is in `config.ts`.

| Setting | What it is for |
| --- | --- |
| `STAGES` | One row per band: cast `spell` until the skill reaches `upTo`, at `mana` a cast |
| `STAGES[].upTo` | In the client's tenths — 74.6 is `746`, so 120.0 is `1200`. Exclusive |
| `STAGES[].buff` | Optional. Proves a cast landed without reading the journal. Wither has none |
| `STAGES[].target` | `'self'` casts through `castTo` at your own character. Only Pain Spike wants it |
| `HURT_FLOOR` | The fraction of maximum health below which the run bandages itself, and stops if that did not work |
| `BANDAGE` | Off is a run that simply stops at the floor instead of healing |
| `BANDAGE_GRAPHIC` | `0xE21`, a clean bandage. A bloodied one is a different item |
| `BANDAGE_ATTEMPTS` | Bandages to spend on getting back above the floor before giving the run to the guard |
| `BANDAGE_TIMEOUT` | How long one application is given. Bandaging is seconds, not milliseconds |
| `HEAL_OUTCOME_TEXT` | What the shard says about a bandage. A heal is proved by the hits, so these only explain failures |
| `SKIP_WHEN_BUFFED` | **Off**, and it has to be: a form does not expire, so gating on its buff casts once and then waits forever |
| `DISABLED_IS_PROGRESS` | **On**: the toggle-off is a cast the shard charged for |
| `MEDITATE_TO_FULL` | Fill the pool, or stop as soon as the next cast is affordable |
| `STRIP_LAYERS` | Every layer that comes off for a trance, in the order it comes off — which is also the order it goes back on. Hands first. Jewellery is deliberately absent, and so is `Layers.Necklace`, because that layer carries gorgets too |
| `STRIP_MOVE_DELAY` | Pause between the individual moves inside one strip, to stay under the shard's action throttle |
| `STRIP_AT_ONCE` | On strips the armour from the first trance instead of waiting to be refused once |
| `MEDITATE_TIMEOUT` / `MEDITATE_ATTEMPTS` | How long one trance is given, and how many are tried before the stretch is a failure |
| `MANA_POLL` / `MANA_LOG_EVERY` | How often the pool is read, and how often the wait reports |
| `REGEN_TIMEOUT` | How long to wait on natural regeneration when meditation is off or refused |
| `MAX_HUNGRY` | Failed mana stretches in a row before the run gives up |
| `CAST_TIMEOUT` / `CAST_DELAY` | How long the shard may take to say something, and the pacing between casts |
| `MAX_BLIND_READS` | Cycles the client may answer nothing for the skill before the run stops |
| `OUTCOME_TEXT` / `MEDITATE_OUTCOME_TEXT` | What the shard says. Mostly guesses — see *Known unverified* |

There is **no stall watchdog**, deliberately, for the reason `src/training/README.md` gives: this
script's cycles are mostly mana coming back on purpose. The heartbeat stays.

## When it goes wrong

- **`unreadable outcome (n/5), check OUTCOME_TEXT`** — the phrase tables do not match this shard.
  Read the journal, copy the real wording into the right bucket. This is the expected first-run
  failure, and it is loud on purpose.
- **`out of reagents for ...`** — refill the pouch. Nothing else went wrong.
- **`the shard will not cast X in the form this character is in`** — see *Known unverified* below.
  The band cannot train itself; leave the form by hand, or train that band another way.
- **`hurt (n/m)`** — the health floor, *after* the bandaging failed to lift the character off it.
  Either the pack ran out (the line above it says so) or the drain is faster than a bandage heals,
  which on the Lich Form band is a real possibility for a character with low Healing.
- **`no bandages left in the pack`** — said once. The run carries on, unhealed, until the floor stops
  it.
- **`the shard refuses meditation (blocked)`** — by the time this fires everything on `STRIP_LAYERS`
  is already off, so what is refusing the trance is something the run cannot reach: jewellery, a layer
  missing from the list, or a shard that gates meditation another way. The run degrades to natural
  regeneration rather than stopping.
- **`the trance was refused with armour on - took more off, trying again`** — expected, once, on a
  shard that blocks on armour. The lesson latches for the rest of the run.
- **`… would not go back on`** — a piece the restore could not return. The run carries on slightly
  weaker and retries it at the next trance.
- **`refused for mana at N`** — the stage's `mana` is lower than the shard actually charges. Raise it.
- **It stops at 100.0 saying nothing is left to train.** No power scroll. The start-up line warned.
- **Casts land but the skill does not move.** The band's spell has stopped gaining at this level; that
  is what the next row is for, and it means the bound between them wants moving.

## Notes on the shard

Everything in `src/training/README.md` under *Notes on the shard* applies here too — the tenths, the
blind read, `maxMana` reading 0 mid-refresh, `>=` rather than `!=` on the pool. What is specific to
this script:

- **A transformation is not a buff with a duration.** The thing that takes a form off is casting it
  again, which makes the buff useless as a gate and useful as proof: going in is proved by the buff
  arriving, coming out by the mana leaving the pool.
- **Necromancy consumes reagents**, which is a first for this repo — every other script here spends
  nothing but time. `noReagents` is its own outcome for that reason: bucketed as unknown it would cost
  five cycles and then blame the phrase table.
- **Pain Spike is cast at the character.** It is the only row with a cursor, and it goes through
  `player.castTo(spell, player)` so no cursor is ever left hanging — an unanswered target cursor
  breaks every action after it.
- **Wither hits everything nearby.** It is the only spell in either trainer that touches anything but
  the caster.
- **A bandage is proved by the health going up**, not by the journal: the wording differs from shard
  to shard and the stat does not. The phrase table only explains the failures.
- **The healing runs before the guards, and that ordering is the feature.** The guard that ends the
  run measures the same floor the bandaging heals to, so a mend that ran after it would never run.

### Known unverified

- **Whether this shard lets a spell be cast while in Horrific Beast form.** On OSI it does not, and
  the only spell that matters is the form spell itself, which is what reverts it. If that is refused
  too, the 50–70 band cannot train itself; `formLocked` says so, and its wordings are guesses.
- **Whether re-casting a form to revert rolls the skill.** On a RunUO-family shard the removal goes
  through the same sequence check, so it should. If it does not, the form bands train at half the rate
  the cast tally suggests.
- **Every phrase in `OUTCOME_TEXT`, and every phrase in `MEDITATE_OUTCOME_TEXT` except the trance
  line.** Nothing load-bearing depends on them: a cast is proved by mana and buffs, and a miss
  surfaces as `unknown` rather than as a silent wrong turn.
- **The mana figures.** They are the OSI costs. Too low names itself as `noMana`; too high costs a
  little sitting still.
- **Whether `BuffDebuffs.PainSpike` is published on a self-cast.** It is only ever used as one of two
  proofs, and the mana leaving the pool is the other.
