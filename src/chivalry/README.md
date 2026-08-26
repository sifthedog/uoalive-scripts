# chivalry — raise Chivalry through its five bands

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/chivalry.js` | Casts the spell that still gains at the level Chivalry has reached, meditates when the mana runs out, and stops when the last stage is done |

| Band | Spell | Mana | Tithing | Needs | What it is |
| --- | --- | --- | --- | --- | --- |
| 40.0 – 45.0 | Consecrate Weapon | 10 | 10 | 15.0 | Enchants **what is in hand** — the one band that wants a weapon |
| 45.0 – 60.0 | Divine Fury | 15 | 10 | 25.0 | A self buff |
| 60.0 – 70.0 | Enemy of One | 20 | 10 | 45.0 | A self buff, and a **toggle** — casting it again takes it off |
| 70.0 – 90.0 | Holy Light | 10 | 10 | 55.0 | An **area attack**. It hits everything non-blue around you |
| 90.0 – 120.0 | Noble Sacrifice | 20 | 30 | 65.0 | Heals nearby allies **at the cost of your own hit points** — see below |

## Why it exists

It is `src/training/` for a different skill. The loop, the cast, the skill read, the mana wait and the
bandaging are all `src/lib/`; what is here is the table, the wordings, and the three things a paladin
does that a samurai does not.

- **Every cast spends tithing points as well as mana** — 10, or 30 on the last band. Tithing is gold
  given at a shrine, a walk and a gump away from anything this loop can do, so running out is an
  **ending** (`noTithing`). The client publishes no such stat, so nothing can read the balance.
- **Only the first band wants a weapon.** Consecrate Weapon enchants what is in hand, and meditation
  is refused while anything is in one — so an armed run stows for every trance and draws again
  afterwards. It draws back the *exact* weapon it took, by serial, so anything on it comes back too.
  An empty-handed run has nothing in hand to put back and never attempts the draw, but it is still
  undressed for the trance if the shard turns out to refuse one with armour on.
- **Noble Sacrifice can floor you.** Where it finds anything to heal it sets the caster's hit points,
  mana and stamina to **1**. Solo it finds nothing and costs only the mana and the tithing.

## What it does

1. **Waits for the skill list**, then reads Chivalry. A client that has not answered is never read as
   `0` — see `src/training/README.md`, *Notes on the shard*.
1. **Bandages the character** if it is under `HURT_FLOOR`, before the guards get to look at it.
1. **Picks the stage** the value falls in: the first row whose `upTo` the value is under.
1. **Meditates if the pool is short** — stowing what is in hand first, taking the armour off too if
   the shard has refused a trance for it, and putting every piece back by serial on every way out of
   the wait.
1. **Casts the stage's spell**, and reads whether it landed from the mana that left the pool and the
   buff that went up, falling back on the journal for *why* when it did not.
1. **Pauses `CAST_DELAY`** and goes round again, until 120.0 is passed.

| Outcome | What the loop does |
| --- | --- |
| `cast` | Tallies it and clears the fault counters |
| `disabled` | Tallies it too — Enemy of One coming off is a cast the shard charged for |
| `fizzled` | Counted, not tallied |
| `noTithing` | **Stops.** Go and tithe |
| `noMana` | Says the stage's `mana` is understated, then gathers mana |
| `alreadyCasting` | Backs off, growing. Never counted towards a stop |
| `noWeapon` | Draws the weapon again, and only stops if that fails |
| `unskilled` | Stops — including the karma refusals, which mean the same thing |
| `saving` | Sits out the world save and resets the counters |
| `throttled` | Backs off, growing, up to `MAX_THROTTLED` in a row |
| anything else | Unreadable — logged once per stretch and carried on with. It ends nothing on its own: only `MAX_STALE` cycles with no cast *and* no movement in the skill does |

### Before you paste it

- **Tithe first.** A long run is thousands of tithing points; at 30 a cast the last band eats them
  fastest. The run ends by name when they are gone.
- **Hold the weapon you want to consecrate**, if you are starting at 40.0. The graphic is learned from
  it at start-up and that is what the re-arm matches on. Starting empty-handed is fine from 45.0 up,
  and the run says which case it thinks it is in.
- **Stand somewhere empty**, and train the last two bands **alone**. Holy Light hits every non-blue
  nearby; Noble Sacrifice drops you to 1 hit point if a pet, a party member or a passing blue is
  within range of being healed.
- **Carry clean bandages.** They are what stands between Noble Sacrifice and the health floor.
- **Keep your karma positive.** Enemy of One and Noble Sacrifice want it, and without it the run stops
  saying this character cannot use the spell.
- It aims at **120.0**, which needs the power scrolls. The start-up line says so if the shard caps you
  lower.

### How to run it

```
npm run build
```

then paste `dist/chivalry.js` into the in-game script editor.

## What to set

Everything is in `config.ts`.

| Setting | What it is for |
| --- | --- |
| `STAGES` | One row per band: cast `spell` until the skill reaches `upTo`, at `mana` a cast |
| `STAGES[].upTo` | In the client's tenths — 74.6 is `746`, so 120.0 is `1200`. Exclusive |
| `STAGES[].buff` | Optional. Holy Light and Noble Sacrifice have none — they put nothing up |
| `WEAPON_NAME` | Substring match for the draw, used only before a graphic has been learned |
| `SPARE_BAG_SERIAL` | The bag inside the pack to open when a plain search misses |
| `DISARM_*` | How long a stow is given before it is reissued, and how many times |
| `STRIP_LAYERS` | Every layer that comes off for a trance, in the order it comes off — which is also the order it goes back on. Hands first. `Layers.Necklace` is in because that layer carries gorgets; the rest of the jewellery is deliberately absent |
| `STRIP_MOVE_DELAY` | Pause between the individual moves inside one strip, to stay under the shard's action throttle |
| `STRIP_AT_ONCE` | On strips the armour from the first trance instead of waiting to be refused once |
| `HURT_FLOOR` | The fraction of maximum health below which the run bandages, then stops |
| `BANDAGE` / `BANDAGE_*` | Whether to heal at that floor, with what, and for how long |
| `DISABLED_IS_PROGRESS` | **On**: Enemy of One toggling off is a cast |
| `SKIP_WHEN_BUFFED` | **Off**: gating on the buff would cap the run at one cast per buff duration |
| `CAST_DELAY` / `CAST_TIMEOUT` | The pacing between casts, and how long the shard may take to answer |
| `MEDITATE_*` / `MANA_*` | The mana wait — see `src/training/README.md` |
| `MAX_STALE` | Cycles with no cast *and* no movement in the skill before the run gives up. The only ending left for a run that is getting nowhere; a dry mana stretch is charged what it cost in cycles |
| `OUTCOME_TEXT` / `MEDITATE_OUTCOME_TEXT` / `HEAL_OUTCOME_TEXT` | What the shard says. Mostly guesses |

## When it goes wrong

- **`outcome unreadable - carrying on`** — the phrase tables do not match this shard. Read
  the journal and copy the real wording into the right bucket. The run no longer
  ends over it — the closing lines say how many went unread, and the commonest cause is a cast that worked: a stage whose buff was already
  standing has no transition to show, so only the mana can prove it, and a client that has not
  refreshed that figure yet leaves the loop nothing to read.
- **`N cycles without a cast or a change in the skill`** — the only ending left for a run that is
  getting nowhere. It replaces the old unreadable-outcome and mana-never-came-back endings, and it
  cannot fire while the skill is still moving, however unreadable the outcomes are.
- **`out of tithing points for ...`** — go to a shrine, tithe gold, paste it again.
- **`the shard says this character cannot use Enemy of One`** — usually karma rather than skill.
- **`could not get the weapon back in hand`** — the run stops rather than carrying on, because a
  character holding nothing cannot consecrate a weapon and cannot defend itself.
- **`hurt (n/m)`** — the floor, after the bandaging failed to lift you off it. On the last band that
  means something within range keeps being healed by your own Noble Sacrifice. Train it alone.
- **`refused for mana at N`** — the stage's `mana` is lower than the shard actually charges. Raise it.

## Notes on the shard

Everything in `src/training/README.md` under *Notes on the shard* applies here too. What is specific:

- **Tithing is a second currency and the client does not report it.** There is no `player.tithing`,
  so the shard saying so is the only way the script learns the pouch is empty — hence its own bucket
  and its own ending, rather than five unknowns and a wrong diagnosis.
- **Chivalry mana costs fall as the skill rises.** The figures in `STAGES` are the base costs, so they
  are ceilings: the wait gathers a little more than the cast needs, which costs a little sitting still.
- **Karma is not a bucket.** A character without it cannot cast Enemy of One or Noble Sacrifice at
  all, which is exactly what `unskilled` already means and exactly what stopping is the right answer
  to, so the karma wordings live in that bucket.
- **The weapon half is decided once.** An unconditional draw on a character who never held anything
  finds nothing in the pack and ends a run that was training Divine Fury perfectly well. `index.ts`
  reads the hands at start-up and passes the by-graphic draw only if there was something in them. The
  trance's own stow and restore are unconditional, because `src/lib/gear.ts` only ever puts back what
  it took — so there is nothing for an empty-handed run to get wrong.

### Known unverified

- **Every phrase in all three tables.** RunUO-family guesses. Nothing load-bearing depends on them: a
  cast is proved by the mana and the buff, a heal by the hits, and a miss surfaces as `unknown`.
- **The tithing costs.** They are the OSI figures. Nothing in the script spends them itself — they are
  in the table above so you can work out how long a run will last.
- **Whether Enemy of One toggles on this shard.** If it does not, `DISABLED_IS_PROGRESS` costs nothing
  — the bucket simply never matches.
