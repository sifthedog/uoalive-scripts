# magery — raise Magery on the spells that gain without a victim

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/magery.js` | Casts the spell that still gains at the level Magery has reached, meditates when the mana runs out, and stops when the last stage is done |

| Band | Spell | Circle | Mana | Cursor | What it is |
| --- | --- | --- | --- | --- | --- |
| ≤ 50.0 | Bless | 3rd | 9 | at self | A self buff |
| 50.0 – 65.0 | Arch Protection | 4th | 11 | at self | A self buff |
| 65.0 – 85.0 | Invisibility | 6th | 20 | at self | A self buff |
| 85.0 – 120.0 | Earthquake | 8th | 50 | none | An **area attack**. It hits everything around you |

## Why it exists

It is `src/training/` for a different skill — the loop, the cast, the skill read and the mana wait are
all `src/lib/` — but the table is the part worth reading, because it is not the one the guides give.

Magery gains from casting something hard enough for the skill you have, and **every guide does that
with damage spells thrown at a creature**. This trainer has no way to find one, keep it alive or keep
it in range, so the table uses the spells the same guides name as gaining without a victim — cast at
the character or at nobody, and repeatable as fast as the mana allows.

The 5th and 7th circles are skipped on purpose: every 7th-circle spell wants a cursor over ground or a
gump answered, and neither is something this loop can do. The cost is a slightly wider band, not a
slower one — an 8th-circle cast still rolls the skill when it fizzles.

## What it does

1. **Waits for the skill list**, then reads Magery. A client that has not answered is never read as
   `0` — see `src/training/README.md`, *Notes on the shard*.
1. **Picks the stage** the value falls in: the first row whose `upTo` the value is under.
1. **Meditates if the pool is short**, filling it right up — at 50 mana a cast that is most of the
   last band.
1. **Casts the stage's spell**, and reads whether it landed from the mana that left the pool and the
   buff that went up, falling back on the journal for *why* when it did not.
1. **Pauses `CAST_DELAY`** and goes round again, until 120.0 is passed.

| Outcome | What the loop does |
| --- | --- |
| `cast` | Tallies it and clears the fault counters |
| `alreadyCasting` | Backs off, growing. **Never** counted towards a stop — the last cast simply has not finished |
| `fizzled` | Counted, not tallied. Ordinary, and commoner the further a circle is above the skill |
| `noReagents` | **Stops.** Nothing waited for refills a pouch |
| `noMana` | Says the stage's `mana` is understated, then gathers mana |
| `disabled` | Tallies it — a shard that treats one of these as a toggle still charged for the cast |
| `alreadyUp` | Waits `BUFF_WAIT`. Only reached with `SKIP_WHEN_BUFFED` on, or when the shard refuses in words |
| `unskilled` | Stops — the table is aimed at a skill this character cannot use |
| `saving` | Sits out the world save and resets the counters |
| `throttled` | Backs off, growing, up to `MAX_THROTTLED` in a row |
| anything else | Counts against `MAX_UNKNOWN`; five in a row ends the run |

### Before you paste it

- **Stand somewhere empty, and never in town.** The last band is Earthquake for 35 skill points, and
  it hits everything around you — in town that is the guards, and near anything blue it is a criminal
  flag. The script does not move, fight or heal.
- **Your kit comes off for each trance and goes straight back on.** Meditation is refused while
  anything is held — a mage weapon counts — so the run stows what is in hand before every trance and
  puts it back before the next cast. It puts back the *exact* items it took, by serial, so Faster
  Casting, Lower Mana Cost and Mana Regeneration come back with them. A spellbook in the pack is never
  touched. If the shard also refuses a trance with armour on, the run finds that out from its own
  refusal, takes the armour off too, and remembers for the rest of the run — jewellery is left alone.
  `STRIP_LAYERS` is the list, if your shard disagrees.
- **Carry reagents**, or wear a 100% Lower Reagent Cost suit, which is what every guide recommends and
  what makes this run cheap. Running out ends the run by name.
- **Below about 30.0, buy the skill from an NPC trainer first.** The first row covers everything under
  50.0, and at 25 it is mostly fizzles.
- It aims at **120.0**, which needs the power scrolls. The start-up line says so if the shard caps you
  lower.

### How to run it

```
npm run build
```

then paste `dist/magery.js` into the in-game script editor.

## What to set

Everything is in `config.ts`.

| Setting | What it is for |
| --- | --- |
| `STAGES` | One row per band: cast `spell` until the skill reaches `upTo`, at `mana` a cast |
| `STAGES[].upTo` | In the client's tenths — 74.6 is `746`, so 120.0 is `1200`. Exclusive |
| `STAGES[].buff` | Optional. Earthquake has none — it puts nothing up, and trains on the mana proof |
| `STAGES[].target` | `'self'` casts through `castTo` at your own character. Every row but Earthquake |
| `CAST_DELAY` | **The one worth tuning.** An 8th-circle cast is seconds long; too short and the shard spends the band saying *you are already casting* |
| `CAST_TIMEOUT` | How long the shard may take to say something about a cast |
| `COOLDOWN_BACKOFF` / `_MAX` | The growing wait after a cast that came in too early. This is what finds the real pace |
| `SKIP_WHEN_BUFFED` | **Off**: gating on the buff would cap the run at one cast per buff duration |
| `DISABLED_IS_PROGRESS` | **On**: a toggle is still a cast the shard charged for |
| `MEDITATE_TO_FULL` | Fill the pool, or stop as soon as the next cast is affordable. **On**, and it matters most here |
| `STRIP_LAYERS` | Every layer that comes off for a trance, in the order it comes off — which is also the order it goes back on. Hands first. Jewellery is deliberately absent, and so is `Layers.Necklace`, because that layer carries gorgets too |
| `STRIP_MOVE_DELAY` | Pause between the individual moves inside one strip, to stay under the shard's action throttle |
| `STRIP_AT_ONCE` | On strips the armour from the first trance instead of waiting to be refused once |
| `MEDITATE_*` / `MANA_*` / `MAX_HUNGRY` | The mana wait — see `src/training/README.md` |
| `MAX_BLIND_READS` | Cycles the client may answer nothing for the skill before the run stops |
| `OUTCOME_TEXT` / `MEDITATE_OUTCOME_TEXT` | What the shard says. Mostly guesses — see *Known unverified* |

There is **no stall watchdog** and **no health floor**. The first because this script's cycles are
mostly mana coming back on purpose; the second because nothing in this table hurts the caster, so the
only thing that can take its health is something that wandered up.

## When it goes wrong

- **`unreadable outcome (n/5), check OUTCOME_TEXT`** — the phrase tables do not match this shard.
  Read the journal, copy the real wording into the right bucket. Expected on the first run.
- **The log fills with the backoff and almost nothing lands.** `CAST_DELAY` is shorter than this
  shard's cast time for the band you are on. Raise it; the backoff is a converger, not a cure.
- **`out of reagents for ...`** — refill, or get the LRC suit.
- **`refused for mana at N`** — the stage's `mana` is lower than the shard actually charges. Raise it.
- **Casts land but the skill does not move.** The circle has stopped gaining at this level; that is
  what the next row is for, and it means the bound between them wants moving down.
- **It stops at 100.0 saying nothing is left to train.** No power scroll. The start-up line warned.

## Notes on the shard

Everything in `src/training/README.md` under *Notes on the shard* applies here too. What is specific:

- **A spell is not an ability, and the pacing is the difference.** An 8th-circle spell has an
  incantation seconds long, and a loop that comes back in half a second issues the next cast into the
  middle of it. That is what `alreadyCasting` is, and why `CAST_DELAY` starts at 3000 rather than 500.
- **A failed cast still trains.** The skill check is what fizzles, so a fizzle is a roll that
  happened — which is why the tally is reported beside the casts.
- **Earthquake is the only row with nothing to prove itself by.** No buff, so the mana leaving the
  pool is the whole proof — the same position Wither is in for necromancy.
- **`castTo` answers its own cursor**, and `castOnce` cancels any cursor left open before it casts, so
  a self-targeted row can never leave one hanging for the next one to trip over.

### Known unverified

- **Every phrase in `OUTCOME_TEXT`, and every phrase in `MEDITATE_OUTCOME_TEXT` except the trance
  line.** RunUO-family guesses; a miss surfaces as `unknown`, loudly.
- **The band bounds.** They are a reading of the AFK guides — *50–86 Invisibility, 86 upwards
  Earthquake* is the one they agree on — not something measured on this shard. If a band stops gaining
  before its `upTo`, move the bound down; that is what the table is for.
- **Whether Arch Protection opens a cursor here.** It is marked `target: 'self'`, which is right where
  it does; where it does not, the queued answer is harmless because the next row wants the same thing.
- **`CAST_DELAY` at 3000.** A first guess at the slowest row, not a measurement.
