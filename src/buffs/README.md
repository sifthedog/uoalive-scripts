# buffs — keep Consecrate Weapon and Divine Fury standing

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/buffs.js` | Watches the buff bar and recasts each buff in `KEEP` as it lapses |

## What it does

Per cycle:

1. **Check the stop conditions** — dead is the only one.
2. **Sit out a world save** if one is running.
3. **Walk the `KEEP` table in order.** For each entry:
   - already standing → nothing to do;
   - set aside, or retired → skipped;
   - needs a weapon and both hands are empty → skipped until you draw something;
   - short of the entry's mana → skipped, said once per stretch;
   - otherwise cast it, read the journal, and pause `CAST_DELAY` before the next entry.
4. **Poll again** after `POLL`.

Nothing here counts cycles against the run: a keeper standing over a character with both buffs up is
working, not stalled. The heartbeat is what proves it is alive.

Outcomes and what each one costs the entry:

| Outcome | What happens |
| --- | --- |
| `cast` | Counted; the buff is up |
| `fizzled` / `alreadyUp` | Nothing — the next pass tries again |
| `noMana` | Logged: this entry's `mana` is understated for this shard |
| `noTithing` | Retired for the rest of the run — nothing a script does refills tithing points |
| `unskilled` | Retired: the shard refuses it at this skill or karma |
| `noWeapon` | Set aside for `SET_ASIDE` |
| `cooldown` / `throttled` / `alreadyCasting` | Backed off, growing each time, `MAX_THROTTLED` in a row ends the run |
| `saving` | Waited out |
| unread | Counted; `MAX_MISSES` in a row sets the entry aside |

The run ends when you stop it, when the character dies, or when every entry has been retired.

### Before you paste it

- **The buff bar is the whole of the check.** A shard that does not send buff packets for these
  spells, or sends a different id, leaves the run casting every pass and burning tithing. The first
  cast of each spell is logged for exactly this reason — no `up` line in the first minute means the
  buff id is wrong for this shard.
- **Tithe first.** Both spells spend tithing points as well as mana, and the client publishes no
  tithing stat, so the run cannot tell you how many you have left until the shard refuses a cast.
- **Consecrate Weapon needs a weapon in hand.** Fists are refused. The run skips that entry while
  both hands are empty and picks it up again the moment you draw.
- **Nothing is stowed, walked, healed or looted.** This is a keeper meant to run alongside a fight.

### How to run it

```bash
npm run build
```

Then paste `dist/buffs.js` into the client's script editor.

## What to set

Everything lives in [`config.ts`](config.ts).

| Setting | Default | What it is for |
| --- | --- | --- |
| `KEEP` | Consecrate Weapon, Divine Fury | The table. One row per buff: `spell`, `buff`, `mana`, and `needsWeapon` where the shard wants one |
| `KEEP_UP` | `true` | Off is a run that puts the buffs up once and stops |
| `POLL` | `1000` | Between passes, and so how long a lapsed buff stays down |
| `CAST_DELAY` | `600` | Between two casts inside one pass, to stay under the action throttle |
| `CAST_TIMEOUT` | `1000` | How long the shard is given to say something about a cast |
| `MAX_MISSES` | `5` | Casts that did nothing, in a row, before an entry is set aside |
| `SET_ASIDE` | `60_000` | How long a refused entry is left alone |
| `MAX_CYCLES` | `100_000` | The backstop — a day at `POLL` |
| `OUTCOME_TEXT` | guesses | The journal phrases. Correct these first when anything goes wrong |

Adding a buff is one row. `buff` is required here where `Stage`'s is optional: a spell the client
publishes no buff for cannot be told apart from one that never went up, and the run would recast it
every pass forever.

## When it goes wrong

**No `Consecrate Weapon up` line, ever** — the buff went up in game but the run never says so. Either
`BuffDebuffs.ConsecrateWeapon` is not what this shard sends, or `hasBuffDebuff` is answering `false`
for a buff the bar is plainly showing. Nothing else in the script will work until that is right.

**`did nothing 5 times - set aside`** — the cast produced no journal line this table knows, put no
buff up and spent no mana. Cast it by hand and read what the shard actually says.

**`costs more than 10 mana here`** — raise that entry's `mana`. The gate is there so a cast is never
issued into a refusal that still costs a cycle.

**`out of tithing points`** — go and tithe. That entry is done for the run; the others carry on.

**`nothing in hand`** repeated — you are unarmed, or the client is not reporting the layer. Only
`equippedItems.oneHanded` and `.twoHanded` are consulted.

## Notes on the shard

Written against UOAlive.

- **`player.hasBuffDebuff(BuffDebuffs.X)` is the whole of the check.** There is no duration or
  time-remaining in this API, so a buff can only be recast after it has lapsed, never before.
- **`BuffDebuffs.DivineFury` is `1010` and `BuffDebuffs.ConsecrateWeapon` is `1082`** — not the spell
  ids, which are `205` and `203`.
- **The caster takes a `Castable`, not a `Stage`** ([`src/lib/cast.ts`](../lib/cast.ts)): `upTo` and
  `mana` belong to the skill trainers, and this loop has no skill table to work through.

### Known unverified

- **Every phrase in `OUTCOME_TEXT` except the tithing ones.** RunUO-family guesses.
- **The `mana` figures**, which are the base costs. The shard charges a paladin less as Chivalry
  rises, so the gate is pessimistic and a `noMana` outcome is what corrects it upward.
- **Whether `noWeapon` is ever reached.** The hand check should get there first.
