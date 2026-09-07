# legion — scripts for TazUO

Python scripts for [TazUO](https://tazuo.org)'s Legion Scripting engine. Everything else in this
repo targets the **ClassicUO web client** (TypeScript in `src/`, bundled into `dist/`); these are a
different client with a different language and a different API, so no code is shared between them.

| Script | What it does |
| --- | --- |
| `tame.py` | Target one animal, then work through every animal of that type in reach: tame it, rename it, and set it on something |
| `buffs.py` | Watches the buff bar and recasts Consecrate Weapon and Divine Fury as each lapses |
| `mining.py` | Walks to the nearest vein, swings, consolidates the ore, and smelts it against a fire beetle |
| `mine-here.py` | Stands still and works the spot you are on until it runs dry, then smelts and stops |
| `lumberjack.py` | Chops the nearest tree, turns the logs into boards, and loads the boards onto your pack animals |
| `arms-lore.py` | Target a weapon, then read it every half second until Arms Lore caps |
| `bowcraft.py` | Trains Bowcraft from 30 to cap: makes whatever the band still gains on, restocks wood from the containers and pack animals you pick, and sells to the nearest bowyer |
| `magery.py` | Trains Magery on the four spells that gain without a victim, meditating when the pool runs dry |
| `mysticism.py` | Trains Mysticism on the five spells that gain without a victim, meditating when the pool runs dry |
| `bod.py` | Target a small Blacksmithing bulk order deed: crafts what it asks for from the ingots in your pack, puts each qualifying piece into the deed, and stops when it is full |

## How to run it

1. Drop the file from **`legion/dist/`** in TazUO's `LegionScripts` folder. Each one is
   self-contained; nothing else has to go with it.
2. Open **Legion Script** from the top menu, and run it from the Script Manager.
3. Answer the cursor each script raises. `tame.py` wants an animal, and another after each tame;
   `mining.py` and `mine-here.py` want your fire beetle; `lumberjack.py` wants your pack animals,
   one after another; `arms-lore.py` wants the weapon to read; `bowcraft.py` wants every container
   or pack animal holding logs or boards, and none at all if you are carrying the wood already.
   `bod.py` wants the deed to fill. `magery.py`, `mysticism.py` and `buffs.py` raise none. ESC
   declines, and each script says what it does instead.

## How it is built

The sources are in `legion/src/`, and `python3 legion/build.py` inlines each entry and everything it
imports into one file in `legion/dist/`. `dist/` is committed, because that is what gets pasted.
`--watch` rebuilds on change.

```
src/uo/            the shared library, one concept per file
src/<script>/      index.py, config.py, and that script's own decisions
src/test_support/  the fake client the suite runs against
src/skilldb/       host CPython, not a script - see The attempt log
```

`python3 legion/skilldb.py convert <logs>` turns what the scripts record into two CSV tables. It is
the only thing here that is not pasted into the game.

`python3 legion/run-tests.py` runs the suite. It needs neither the game nor a shard: `test_support/uo.py`
is a fake `API`, installed both ways the real one is reachable — as a builtin, and as `import API`.
It is deliberately inert, so a test that wants an outcome has to say so.

- **Nothing in `src/uo/` imports a script folder's `config.py`.** The parameters come in through
  the call.
- **The Script Manager's stop arrives as an exception** thrown out of the next `API.Pause`, and the
  client gives the thread two seconds to unwind on it before declaring the script stuck. A catch-all
  around a loop must re-raise when `API.StopRequested` is set.
- **Nothing in `src/uo/` holds mutable module state.** State lives on an object, so the bundled
  artifact and the same module imported under test behave identically — `global` binds to the
  defining module, and a flat bundle would hide the difference.
- **The bundle is one flat namespace.** Two modules defining the same top-level name is a build
  error, as is `import x as y`, `import *`, an import below the top level, and importing a name its
  module does not define.
- **`import API` at the top of a source file is what gives an editor autocomplete.** The bundler
  strips it and emits one for the artifact; Legion then strips that and injects the real `API` as a
  builtin. Run `-updateapi` in game to refresh the local `API.py` stub.
- **Sibling imports at runtime would work, and are deliberately not used.** `LegionScripts/` is on
  `sys.path`, and a folder whose name starts with `_` is skipped by the Script Manager, so a package
  could live there. Two things make bundling the better answer: the module cache is on by default,
  so an edited shared module needs a client restart, and a module reached by IronPython's real
  import machinery cannot carry `import API` — `LegionScripts/API.py` is the autocomplete stub, and
  importing it shadows the injected builtin with something whose every call returns `None`.

**Legion runs IronPython 3.4.2, so the language level is Python 3.4.** Anything newer is a
`SyntaxError` at load: f-strings, variable annotations, the walrus operator, PEP 448 unpacking, and
numeric underscores, so `100000`, never `100_000`. Use `%` formatting. `python3 -m py_compile`
proves nothing about this, so `build.py` walks the AST of every source and refuses all of it.

## The shared library

```
alert       a command run on the machine through .NET, so a warning does not depend on the game
buffbar     the buff bar, re-read every time because ApiBuff never refreshes
cast        a spell, and the two silent proofs a shard that says nothing still leaves
clock       the one time.time(), so tests have one thing to fake
convert     resource -> product, judged by the pack diff, with a per-hue write-off
craftmenu   a craft gump: opening it, walking the categories, reading and pressing the rows
crafttool   the tool a craft menu is opened with, found in the pack by art or by name
entity      hex, the guarded player read, Chebyshev, find-a-mobile
gear        what is in either hand
guards      the stop conditions, composed per script
gump        waiting for a gump, and reading what it says
heartbeat   'still here', on the clock rather than per cycle
journal     the phrase table, the reverse lookup off it, and the tail of what was said
log         the script's own prefix
loop        the throttle backoff and the stall watchdog
mana        the pool, watched in slices so the guards get a look in
meditate    filling the pool, and retiring the skill when the shard refuses it
menu        a context menu entry, matched by its text
mount       getting off the mount, proved by the flag
notoriety   the values the threat scans are handed
pace        the shard's skill timer, learned from its refusals rather than configured
pack        counting and diffing what the backpack holds
phrases     the shard's own wordings, as far as they do not depend on the script
record      one line per attempt, buffered a cycle so the gain it earned is in it
retry       act, poll for the proof
roam        walking to the next spot, and waiting where there is nothing but a clock
save        sitting out a world save
scan        the crow-flight sort, the route probe, and the shortest way in
skill       every read of GetSkill, and what a client that has not answered means
stages      the band table: which row trains now, and what one of its cycles costs
survey      the dead-end report: what the run actually saw
target      answering a self cursor the pre-target did not take
terrain     the land and statics cache, one pair of calls per coordinate for the run
threat      noticing trouble and sounding the ambush alarm, without ending the run over it
tiles       what is worked out, unreachable, or not the resource at all
timings     the constants the scripts agreed on
tool        find it, learn its graphic, equip it, notice it break
travel      chasing a mobile, and following one between the slices of a wait
vitals      position, weight and mana, as one phrase
weight      the one place WeightMax is read
```

`probe-target.py` sits outside all of this: it is the throwaway diagnostic that answered how this
shard takes a self-target, and its own header says to delete it once the answer is known.

## The attempt log

Five scripts append one line per attempt to `DATA_PATH`, and `skilldb.py` turns those lines into two
tables. Every counter these scripts keep is otherwise an int in memory, reported through `SysMsg` and
gone when the run ends; this is the same information written down.

`open()` is a builtin, so this needs no import and `HOISTED` is untouched — which is the only reason
`src/uo/record.py` formats its JSON by hand rather than calling `json.dumps`. The standard library
*is* on `sys.path` at runtime, but a file of numbers and two short strings is not worth relaxing the
bundler's one rule for.

**A bare filename lands in TazUO's working directory** — not beside the script, and not in this repo.
Set an absolute path if you want it somewhere you will find it. `DATA_PATH = ""` turns a script's
recording off entirely. The file is opened, appended to and closed per row, so a client killed
mid-run loses at most the one row still in the air, and a run that cannot write says so once and
carries on training.

### What counts as an attempt

Only what the shard clearly called a success or a failure. A throttle, a dry mana pool, a world save
and an outcome no `OUTCOME_TEXT` matched all write nothing. A guessed row would be worse than a
missing one: the missing row shows up in the run's own closing tally, and the wrong one never does.

| Script | success | failure | Left out |
| --- | --- | --- | --- |
| `magery.py` | `cast`, and `disabled` where `DISABLED_IS_PROGRESS` | `fizzled` | the mana wait, the buff already standing, everything unread |
| `mysticism.py` | the same | `fizzled` | the same, plus the health floor |
| `tame.py` | `tamed` | `failed` | `pending` — the shard took the attempt and never said how it went |
| `arms-lore.py` | `read` | `missed` | a use that raised no cursor, and any wording the table has not got |
| `bowcraft.py` | `made` | `failed` | `noMaterial`, `wrongRow`, a worn tool, the sell trips |

### Why a row waits a cycle

`skill_to` is not read straight after the outcome. The client applies a gain some time after the
shard grants it, so a value read at the outcome is usually still the old one. The row is buffered and
written at the **next** skill read instead, one pace delay later.

That is what makes carrying both values worth the trouble. A scroll of alacrity moves the skill 0.2
to 0.5 in one go, and a row that recorded only the band it started in could not tell that apart from
several ordinary gains. Recording every attempt rather than only the ones that gained is the same
argument: a progression that stopped because the wood ran out is still fully described.

### The row

```json
{"v":1,"id":"0x40012345/1757030000123/17","t":1757030042.500,"char":"Kaldor",
 "serial":"0x40012345","skill":"Magery","from":74.6,"to":74.7,
 "outcome":"cast","ok":true,
 "consumed":[{"name":"oak boards","graphic":"0x1bd7","hue":2010,"qty":6}]}
```

`id` is `serial/run-start-in-milliseconds/sequence`, so it is stable across re-conversions and two
runs cannot mint the same one. `to` is `null` where the client was not answering when the row
settled. `consumed` is left off entirely unless something was measured — see `bowcraft.py` below,
which is the only script that measures it.

### Turning it into a table

```
python3 legion/skilldb.py convert ~/TazUO/LegionScripts/skill-attempts.jsonl --out legion/data
```

Every file named is merged into one pair of tables, so a log copied off each character joins the
rest. Rows are recognised by their `id`, so converting the same log twice changes nothing, and a
half-written line is reported with its file and line number and skipped rather than being fatal.

`attempts.csv` is `id, ts, at_utc, character, serial, skill, skill_from, skill_to, gain, outcome,
success`. `consumed.csv` is `id, name, graphic, hue, quantity` — one row per material, joined back by
`id`, because a craft can spend several things at once and a column pair per material would cap how
many at whatever seemed enough on the day. `gain` is `skill_to - skill_from`, rounded to a tenth
because `74.7 - 74.6` is `0.09999999999999432` in binary floating point. The 0.1-band question that
started all this — how many attempts did 40.0 to 40.1 cost — is a `GROUP BY skill_from` over that
table rather than a shape the file was forced into.

`src/skilldb/` is the one folder under `src/` that is **not** a Legion script: it is host CPython,
run by `skilldb.py`, and it is not in `build.py`'s `ENTRIES`, so nothing holds it to what IronPython
3.4 can parse. It lives there so `run-tests.py`'s discovery finds `convert_test.py` for free.


## tame.py

Target one creature. That sets the **type** the run hunts for, and it works through everything of
that type in reach before asking you for another. Per cycle, on whichever animal it is working:

1. **Check the stop conditions** — dead, hurt below `HEALTH_FLOOR`, or no follower slots left.
2. **Sit out a world save** if one is running, without charging the refusals to anything.
3. **Check the creature still resolves**, and **chase it** if it is further than `TAME_RANGE`.
4. **Pre-target it, then `UseSkill("Animal Taming")`** — so the shard's cursor is answered before it
   is raised, and no cursor is left hanging for the next cycle to trip over.
5. **Wait twice**: once for the shard to say the attempt started or to refuse it, then again for the
   attempt to resolve — both in slices, pathfinding after the animal between them.
6. **Pause for the current pace**, which is not a constant — see below.

When the animal accepts you it is renamed to `PET_NAME` and dealt with according to `AFTER_TAME`,
and the run moves to the next animal of the same type. The cursor comes back up only when there are
none left in sight. **ESC ends the session**, and so does the Script Manager's stop button, and so
does letting the cursor time out after `TARGET_TIMEOUT`.

| Outcome | What happens |
| --- | --- |
| `tamed` | Counted, then renamed and dealt with |
| `failed` | The skill check failed, which still rolled the skill. The ordinary cycle |
| `pending` | The attempt started and never resolved. Counted up to `MAX_PENDING`, then stops the run |
| `angry` | Waits `ANGRY_DELAY` up to `MAX_ANGRY`, then gives up on this animal |
| `contested` | Another tamer has it. Counted up to `MAX_CONTESTED` |
| `tooFar` | Chases it. `MAX_AWAY` chases that gain no ground give up on this animal |
| `throttled` | The shard's own timer. The pace is *raised* as well as backed off from |
| `saving` | Waits the save out and carries on |
| `hopeless`, `notAnimal`, `alreadyTame`, `unskilled` | Gives up on this animal |
| anything else | Counted unreadable and said, but never stops the run |

Only the guards, `throttled` and `pending` end the **session**. Everything else that goes wrong ends
the current **animal**.

### Hunting the rest

The animal you target by hand sets the type — its **body graphic, in any colour** — and from then on
`API.GetAllMobiles(graphic, distance)` finds the next one, already sorted by distance. Left out:

- **Anything the run has already finished with**, tamed or given up on. Held in a set that lasts
  until the script is restarted; without it the scan picks the same unreachable animal straight back
  up and the run makes no progress.
- **Anything that is already a pet** — `IsRenamable` is true for pets and followers, which is every
  animal a `kill` or `keep` run has kept.
- **Anything named `PET_NAME`.** Releasing hands the follower slot back but leaves the name, so this
  is the only thing standing between a released `sifinha` and being tamed over and over.
- Anything dead, and anything the client has stopped tracking.

`HUNT_RADIUS = 0` turns the hunt off and asks for every animal.

### The chase

`API.PathfindEntity` does the walking, and the result is graded three ways because only one of them
counts against `MAX_AWAY`:

- **`closed`** — pathfinding reached `TAME_RANGE`.
- **`gained`** — it did not, but the gap is smaller than it was. That is progress and buys another
  cycle, so something that keeps walking off is followed for as long as you are gaining on it.
- **`stuck`** — no ground made up. `MAX_AWAY` of these in a row writes the animal off.

**The chase carries on during the attempt.** An attempt takes up to `TAME_START_TIMEOUT` plus
`TAME_RESOLVE_TIMEOUT` to answer and the animal walks the whole time, so both waits are taken in
`TAME_WAIT_SLICE` slices with a non-blocking pathfind between them. A chase that never lands an
attempt is ended by the stall watch after `STALL_STOP` cycles.

### What happens to each tame

| `AFTER_TAME` | What happens |
| --- | --- |
| `kill` | Ordered to attack. The cursor the shard raises is **left up for you to click** |
| `release` | Let go, so the follower slot comes back |
| `keep` | Neither. It stays yours and stays where it is |

- **Wait for the handover first.** The tame lands in the journal before the shard has finished
  making the animal yours, and until it has, the rename packet is refused and the context menu comes
  back without a Release entry. Both used to fail on that race, sometimes together. The run now
  waits for `IsRenamable` — the shard saying the handover is done — for up to `PET_SETTLE_TIMEOUT`,
  and goes ahead anyway if it never arrives.
- **Rename second.** Once it is not your pet the rename is refused. `API.Rename` returns nothing and
  a refusal is silent, so the new name is polled for and the packet reissued up to `RENAME_ATTEMPTS`
  times. `PET_NAME = ''` skips it.
- **A miss ends the animal, never the session.** The totals are repeated once at the end of the run.
- **The kill order is given, then the script gets out of the way.** Nothing here answers the cursor;
  what the pet attacks is always your click. After `KILL_PICK_TIMEOUT` the run says `unanswered` and
  carries on.
- **Keeping the tames fills the follower slots**, and a shard with no room refuses every attempt
  without saying why — so the run stops itself with `no follower slots left`.
- **Releasing:** the proof is `IsRenamable` going back to false, polled up to `RELEASE_TIMEOUT`.
  Which button of the confirmation gump means yes is worked out rather than configured — the release
  is tried once per id in `RELEASE_CONFIRM_BUTTONS` until the animal is let go, and the id that
  worked is logged and reused. Each candidate gets `RELEASE_ATTEMPTS` goes, because a confirm that
  arrives late loses a press and because the retry is what reads the entry going missing as proof:
  it is on the menu only while the animal is yours. A menu that comes back without the entry *before*
  any press is a menu asked for early, not a refusal, and is retried `RELEASE_ATTEMPTS` times.
  A confirmation that could not be answered is closed, because it is modal on some clients and would
  refuse the context menu of every animal after it.
- **The confirm gump is identified by the gump id changing**, polled through `API.HasGump()`, and
  answered with `API.ReplyGump(button, gump)` naming that id. `API.WaitForGump()` with no id cannot
  do this job: it resolves to whatever `LastGumpID` already is, so it returns true instantly and
  answers a stale gump when one is open, and waits for an id that will never reappear when none is.

### The pace

Nothing reports the shard's skill delay, and guessing it low re-arms the very timer it is waiting
out. `TAME_DELAY` is a **floor**, not the cadence: `PACE_STEP` is added every time the shard refuses
and taken back only after `PACE_EASE_AFTER` attempts have landed.

### Before you run it

- The animal must be **wild** and within your skill.
- Nothing needs to be in the pack, and nothing is picked up.
- **A failed tame can turn the animal on you.** This script does not fight, heal or run — it stops at
  `HEALTH_FLOOR`. Do not leave it on something that can kill you.
- It pathfinds to the animal, so stand somewhere the path is not a fence.
- **A released animal is wild again** and can turn on you the same way a failed tame can.
- With `AFTER_TAME = 'kill'` the run **stops to wait for your click** after every tame, and the pets
  stay yours until the follower slots run out.

### What to set

The config block is the top of `tame.py`. **Every timing is in seconds** — `API.Pause` takes seconds
where the ClassicUO port took milliseconds.

| Setting | Default | What it is for |
| --- | --- | --- |
| `PET_NAME` | `'sifinha'` | What each tame is renamed to. Empty skips the rename |
| `AFTER_TAME` | `'kill'` | What becomes of each tame: `kill`, `release` or `keep` |
| `TAME_START_TIMEOUT` | `3.0` | How long the shard has to say the attempt started, or refuse it |
| `TAME_RESOLVE_TIMEOUT` | `15.0` | How long a started attempt has to resolve |
| `TAME_WAIT_SLICE` | `0.5` | How long a slice of either wait is, and so how often the animal is followed |
| `TAME_RANGE` | `2` | Pathfound into before every attempt |
| `CHASE_TIMEOUT` | `10` | How long one blocking pathfind may take |
| `HUNT_RADIUS` | `12` | How far it looks for the next of the type. 0 asks for every animal |
| `TAME_DELAY`, `PACE_STEP`, `PACE_MAX`, `PACE_EASE_AFTER` | `1.5`, `0.4`, `8.0`, `5` | The pace floor, and how it learns the shard's timer |
| `ANGRY_DELAY` / `MAX_ANGRY` | `10.0` / `10` | How long an angry creature is left, and for how many cycles |
| `MAX_AWAY` | `10` | Chases that gain no ground before the animal is written off |
| `MAX_CONTESTED` | `20` | Cycles another tamer may hold it |
| `MAX_PENDING` | `10` | Attempts that start and never resolve before the run stops |
| `MAX_THROTTLED` | `20` | Refusals in a row before the run stops. A backstop — the pace should get there first |
| `HEALTH_FLOOR` | `0.5` | Fraction of your health at which the run stops |
| `TARGET_TIMEOUT` | `60.0` | How long you have to answer the taming cursor before the run ends |
| `KILL_MENU_TEXT`, `RELEASE_MENU_TEXT` | `['Kill', 'Attack']`, `['Release']` | Context menu entries, matched as case-insensitive fragments |
| `KILL_CURSOR_TIMEOUT` | `2.0` | How long the shard has to raise the cursor |
| `KILL_PICK_TIMEOUT` / `_POLL` | `60.0` / `0.25` | How long you have to click the victim |
| `RELEASE_CONFIRM_BUTTONS` | `[1, 2, 0]` | Release is retried with each in turn until the animal is let go |
| `RELEASE_CONFIRM_TEXT` | fragments | Wordings the confirmation gump is checked against |
| `RELEASE_CONFIRM_TIMEOUT` / `_POLL` | `3.0` / `0.15` | How long the confirmation gump has to arrive |
| `RELEASE_ATTEMPTS` | `3` | Goes each candidate button gets, and early menus tolerated |
| `PET_SETTLE_TIMEOUT` / `_POLL` | `5.0` / `0.25` | How long the shard has to finish making the animal yours |
| `RENAME_ATTEMPTS` | `3` | Times the rename packet is reissued before giving up |
| `MENU_RETRY_DELAY` | `0.5` | Between a menu that arrived without the entry and asking again |
| `RELEASE_TIMEOUT` / `_POLL` | `3.0` / `0.25` | How long `IsRenamable` has to go back to false |
| `RENAME_TIMEOUT` / `_POLL` | `3.0` / `0.25` | How long the new name has to arrive |
| `OUTCOME_TEXT` | — | The shard's wordings. All guesses but two; see below |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each attempt is appended, one JSON object per line. `""` records nothing |

### When it goes wrong

**`attempts kept starting and never resolving`** — the shard took the attempts and said nothing
within `TAME_RESOLVE_TIMEOUT`. Raise it.

**`outcome unreadable - carrying on`** — the shard words that result differently. Add the wording to
`OUTCOME_TEXT`.

**`shard says wait (n/20), now pacing at Ns`** — working as intended for the first few cycles. A run
of them that never stops means the real delay is above `PACE_MAX`.

**`could not rename '…'`**, **`could not order '…' to kill (noEntry)`** or **`could not release '…'
(noEntry)`** — the entry is worded differently, or is not on the menu at all. Set `KILL_MENU_TEXT` /
`RELEASE_MENU_TEXT` to what the shard actually sends. If it is preceded by `is not showing as yours
yet`, the shard is slower than `PET_SETTLE_TIMEOUT` at handing the animal over — raise that instead,
and the menu wordings are fine.

**`could not order '…' to kill (noCursor)`** — the entry was pressed and the shard raised no cursor.
Either it wants the order given another way, or `KILL_CURSOR_TIMEOUT` is short.

**`no follower slots left`** — every slot is taken, which is where `AFTER_TAME = 'kill'` or `'keep'`
ends up. Stable the pets, or switch to `'release'`.

**`could not release '…' (stillPet)`** — every id in `RELEASE_CONFIRM_BUTTONS` was tried and the
animal is still yours. Add whatever id the gump's yes button really is.

**`found no gump to confirm the release with`** — no new gump id appeared within
`RELEASE_CONFIRM_TIMEOUT` of pressing Release. Either the shard sends no confirmation on this shard,
or it is slower than three seconds; raise `RELEASE_CONFIRM_TIMEOUT`.

**`could not get near '…'`** — `MAX_AWAY` chases in a row gained no ground at all. Something is in
the way, or the animal is genuinely faster than you.

### Notes on the API

- **`API.Pause` takes seconds.** Every constant ported from `src/taming/config.ts` was divided by
  1000; a stray millisecond value is a multi-minute freeze.
- **`Skill.Value` is a float** — `74.6`, not the client's tenths `746`. It reads `0.0` until the
  skill list arrives, which is also a real skill value, so the reader reports `unknown` rather than
  coercing it.
- **There is no blocking journal wait.** `InJournalAny` answers yes/no, so the two-stage read polls
  the `OUTCOME_TEXT` buckets **in order** — which is what makes bucket order load-bearing, and why
  `unskilled`, `saving` and `throttled` sit last. Matches are consumed as they are read.
- **`HitsMax` and `FollowersMax` read 0** before the client has been told, so both guards check for
  a positive ceiling first.
- **The pre-target is cancelled on every exit path**, or an attempt the shard never answered leaves
  it armed for the next cycle.

### Known unverified

- **Every phrase in `OUTCOME_TEXT` but `tamed` and `failed`.** RunUO-family guesses, written against
  UOAlive; a miss shows up as an `unknown` outcome rather than a silent wrong turn.
- **`TAME_RESOLVE_TIMEOUT` of 15 seconds**, a guess at the ceiling of an attempt rather than a
  measurement. `MAX_PENDING` turns a wrong one into a diagnosable stop.
- **Whether `IsRenamable` flips before the attempt returns.** If it does not, the fallback simply
  never fires and the journal carries the run.
- **That a released animal keeps the name it was given.** The whole of the `PET_NAME` filter rests on
  it; if this shard clears the name on release, a `release` run tames the same animals round and
  round, and the fix is `AFTER_TAME = 'keep'` or a shorter `HUNT_RADIUS`.
- **Which button of the confirmation gump means yes.** `the release gump answers to button N` is
  what says which one won; pin `RELEASE_CONFIRM_BUTTONS` to it once it is known.
- **Whether `API.PreTarget` beats the server's cursor** on this shard. If it does not, the attempt
  reads as `pending` and the fix is `UseSkill` followed by `WaitForTarget` + `Target`.

## buffs.py

Watches the buff bar and recasts each entry in `KEEP` as it lapses — **Consecrate Weapon** and
**Divine Fury** out of the box. A keeper meant to run alongside a fight: it does not walk, heal,
loot or stow, and death is the only thing that stops it. Per cycle:

1. **Check the stop conditions** — dead is the only one.
2. **Sit out a world save** if one is running.
3. **Walk the `KEEP` table in order.** Already standing → nothing to do; set aside or retired →
   skipped; needs a weapon and both hands empty → skipped until you draw something; short of the
   entry's mana or tithing → skipped, said once per stretch; otherwise cast it, read the journal,
   and pause `CAST_DELAY` before the next entry.
4. **Poll again** after `POLL`.

Nothing counts cycles against the run — a keeper standing over a character with both buffs up is
working, not stalled. The heartbeat is what proves it is alive.

| Outcome | What happens |
| --- | --- |
| `cast` | Counted; the buff is up |
| `fizzled` / `alreadyUp` | Nothing — the next pass tries again |
| `noMana` | Logged: this entry's `mana` is understated for this shard |
| `noTithing` | Retired for the rest of the run — nothing a script does refills tithing points |
| `unskilled` | Retired: the shard refuses it at this skill or karma |
| `noWeapon` | Set aside for `SET_ASIDE` |
| `cooldown` / `throttled` / `alreadyCasting` | Backed off, growing each time; `MAX_THROTTLED` in a row ends the run |
| `saving` | Waited out |
| unread | Counted; `MAX_MISSES` in a row sets the entry aside |

The run ends when you stop it, when the character dies, or when every entry has been retired.

### How a cast is read

In order, and the order is load-bearing: snapshot whether the buff is standing → return
`alreadyUp` if it is → snapshot mana → cancel a live cursor → clear the journal → cast → poll the
`OUTCOME_TEXT` buckets for `CAST_TIMEOUT`.

If the shard said nothing this table knows, two proofs remain: the buff **transitioned** from down
to up, or mana strictly decreased. A buff that was already standing proves nothing, which is why
the snapshot is taken first. A journal wording wins over both, so a fizzle that spent mana still
reads `fizzled`.

### Telling a buff apart

`API.BuffExists(name)` is a case-insensitive substring match on the buff's **localized title**, so
it breaks on a non-English client. This script walks `API.ActiveBuffs()` and matches
`str(buff.Type)` — the client's own `BuffIconType`, the same enum the TypeScript version uses —
against the row's `buff`, falling back to a title substring. The first pass that finds any buff at
all dumps every `Type`/`Title` pair it sees, so a shard whose ids differ is diagnosable from the
run's own output.

**There is no time-remaining.** `ApiBuff.Timer` is an absolute client-tick deadline and the client's
tick counter is not exposed to scripts, so a buff can only be recast *after* it lapses, never
before. `POLL` is therefore roughly how long a lapsed buff stays down.

### Before you run it

- **The buff bar is the whole of the check.** A shard that sends no buff packet for these spells
  leaves the run casting every pass and burning tithing. The first cast of each spell logs
  `<spell> up` for exactly this reason — no `up` line in the first minute means the id is wrong.
- **Tithe first.** Both spells spend tithing points as well as mana.
- **Consecrate Weapon needs a weapon in hand.** Fists are refused. The entry is skipped while both
  hands are empty and picked up the moment you draw.
- **Nothing is stowed, walked, healed or looted.**

### What to set

The config block is the top of `buffs.py`. **Every timing is in seconds.**

| Setting | Default | What it is for |
| --- | --- | --- |
| `KEEP` | Consecrate Weapon, Divine Fury | The table. One row per buff: `spell`, `buff`, `title`, `mana`, `tithing`, and `needs_weapon` where the shard wants one |
| `KEEP_UP` | `True` | Off is a run that puts the buffs up once and stops |
| `POLL` | `1.0` | Between passes, and so how long a lapsed buff stays down |
| `CAST_DELAY` | `0.6` | Between two casts inside one pass, to stay under the action throttle |
| `CAST_TIMEOUT` / `CAST_WAIT_SLICE` | `1.0` / `0.2` | How long the shard has to say something about a cast, and how finely that is polled |
| `MAX_MISSES` | `5` | Casts that did nothing, in a row, before an entry is set aside |
| `SET_ASIDE` | `60.0` | How long a refused entry is left alone |
| `MAX_THROTTLED` | `20` | Refusals in a row before the run stops |
| `MAX_CYCLES` | `100_000` | The backstop — a day at `POLL` |
| `OUTCOME_TEXT` | guesses | The journal phrases. Correct these first when anything goes wrong |

Adding a buff is one row. `buff` is required: a spell the client publishes no buff for cannot be
told apart from one that never went up, and the run would recast it every pass forever.

### When it goes wrong

**No `<spell> up` line, ever** — either the row's `buff` is not the `BuffIconType` this shard
sends, or the bar is not being published. Read the `buff bar: ...` dump. Nothing else in the script
works until that is right.

**`did nothing 5 times - set aside`** — the cast produced no journal line this table knows, put no
buff up and spent no mana. Cast it by hand and read what the shard actually says.

**`costs more than 10 mana here`** — raise that entry's `mana`. The gate is there so a cast is never
issued into a refusal that still costs a cycle.

**`0/10 tithing points`** or **`out of tithing points`** — go and tithe. The gate skips the entry;
the shard's own refusal retires it for the run.

**`nothing in hand` repeated** — you are unarmed, or the client is not reporting the layer. Only
`onehanded` and `twohanded` are consulted.

### Notes on the API

- **`API.CastSpell` matches partially** — "Fireba" casts Fireball — so `KEEP` carries full names.
- **`API.ActiveBuffs()` objects never refresh** after they are handed over, so the bar is re-read
  every time the answer matters.
- **The tithing gate is not in the ClassicUO version**, which logs "the client publishes no tithing
  stat" and leaves it ungated. That comment is wrong on both clients: `API.Player.TithingPoints`
  exists. Since a `noTithing` retires the entry for the whole run, a character who forgot to tithe
  would otherwise lose both buffs on the first pass.
- **`API.ContextMenu(serial, text, timeout)` gives up the moment the shard sends a menu without a
  matching entry** — it does not keep waiting for the timeout. So an entry that is merely not there
  *yet* is reported the same as one that will never be there, which is why the early menu is retried.
- **The cursor cancel is guarded** (`if API.HasTarget()`), unlike `src/lib/cast.ts`, which cancels
  unconditionally — that left the next cursor unusable in the run it was copied from.

### Known unverified

- **Every phrase in `OUTCOME_TEXT` except the tithing ones.** RunUO-family guesses, written against
  UOAlive; a miss shows up as a miss, not as a silent wrong turn.
- **The `mana` figures.** These are the TypeScript's (10 and 15); the client's own Chivalry table
  says 10 for both, and the shard charges a paladin less as Chivalry rises. The gate is pessimistic
  on purpose and `noMana` is what corrects it upward.
- **The tithing costs**, read off the client's `SpellsChivalry.cs` as 10 each rather than measured.
- **Whether `noWeapon` is ever reached.** The hand check should get there first.

## mining.py

Gets off the mount, finds the nearest vein, walks to it, swings, consolidates the ore, and smelts it
against a **fire beetle** — a pet that works as a portable forge, which is why this run never walks
to town. It is also why it has to dismount first: the beetle is usually both the ride out and the
smelter, and a beetle you are sitting on cannot be targeted with an ore stack.

**`ORE_TILE_GRAPHICS` ships as a stock RunUO guess** and it is the one setting most likely to be
wrong for your shard. Everything else degrades gracefully; this one ends runs. A dead end prints
every art it saw, in hex and decimal, with `MATCHES` beside the ones the config accepts — that
listing is how the real numbers get found.

Before the loop: off the mount, the beetle cursor, consolidate the pack, and smelt if it is already
over the limit — in that order, so a run pasted with a full pack can take its first swing and the
beetle you click is one standing next to you.

Per cycle:

1. **Check the stop conditions** — dead, or the pack at its item cap.
2. **Sit out a world save.** Every step below reads that silence as its own kind of failure.
3. **Get off the mount**, asked every cycle so a remount costs one cycle rather than the run.
4. **Equip a pickaxe.** Also every cycle. Spares come out of the pack.
5. **The weight backstop.** If the pack is genuinely over the limit, smelt now.
6. **Scan for a vein** within `SCAN_RADIUS` *and* `MINE_Z_RANGE` of your own elevation, skipping
   tiles the run has parked and tiles `API.GetPath` can find no route to.
7. **Walk to it** with `API.Pathfind` if it is further than `MINE_RANGE`.
8. **Swing**, and branch on what the shard says.

| Outcome | What the loop does |
| --- | --- |
| `dug` | Wait for the ore to land, then consolidate the pack to one pile per metal |
| `empty` | Park that tile for `RESPAWN_DELAY`, **and smelt** — the spot has run dry |
| `nothingNearby` | Park the `HARVEST_BANK` block you stand in and everything within `MINE_RANGE`, so the next scan looks further and the character walks off. **And smelt** |
| `notOre` | Ban the whole graphic, not just the tile — a wrong band in `ORE_TILE_GRAPHICS` is a whole stretch of mountain |
| `tooFar` | The shard disagreeing about the range. Set the tile aside rather than swinging again |
| `notSeen` | Line of sight. Permanent — neither walking closer nor waiting fixes it |
| `packFull` | Consolidate. Forty piles of one becoming one pile of forty gives back thirty-nine slots |
| `wornOut` | The pickaxe broke; the next cycle equips a spare |
| `saving` | Sit it out; no counter is held against it |
| `throttled` | Back off further each time, and give up after `MAX_THROTTLED` |
| `noCursor` | No cursor and the journal explained nothing. Backed off like a throttle, stops after `MAX_NO_CURSOR` |
| anything else | Unreadable. `MAX_UNKNOWN` in a row ends the run — check `OUTCOME_TEXT` |

**When it smelts:** on a spot running dry, not on a schedule and not at the end. The character is
about to walk somewhere else anyway and the beetle has been following it. It costs nothing on the
passes with nothing to do, because the smelt asks whether any pile is worth smelting *before* it
looks for the beetle.

### Before you run it

- Stand on the mountain face or in the cave you mean to work.
- **A pickaxe in hand.** The run learns its graphic from what you are holding. Spares go in the pack.
- **The fire beetle nearby**, and yours. It opens a cursor at startup for you to click it — ESC to
  let the script find one instead. Without a beetle the run still mines; it stops when the pack
  fills, saying smelting freed nothing.
- Being mounted is fine — it gets off by itself.

## mine-here.py

The stationary half of `mining.py`. It stands where you put it, swings until the shard says there is
nothing left, smelts what it mined, and stops. Same prologue.

It can leave out the scan, the walk and the respawn wait because the swing answers the target cursor
with *yourself* and lets the shard pick the ore — so a swing is aimed by where the character stands
rather than by naming a tile, which is all the vein scan exists to decide.

| Outcome | What the loop does |
| --- | --- |
| `dug` | Wait for the ore to land, then consolidate the pack to one pile per metal |
| `empty`, `nothingNearby` | **The spot is worked out.** Consolidate, smelt, and stop. One branch, not two — the pair differ by scope, and scope only matters to a run with somewhere else to walk |
| `notOre` | Nothing here can be mined. No art to ban and nowhere to walk, so it is an ending |
| `tooFar`, `notSeen` | Neither is answerable by moving, so both stop |
| `packFull` | Consolidate — the item cap, not the weight |
| `wornOut`, `saving`, `throttled`, `noCursor`, unreadable | As `mining.py` |

**It does not move.** Not to a better tile, and not to the beetle: it smelts against a beetle already
inside `SMELT_RANGE` and otherwise keeps the ore as ore and says so. That is an invariant of the
file rather than of the loop, and it is checkable — `grep -c 'Pathfind\|GetPath' legion/mine-here.py`
must answer `0`.

That is also what makes weight a real ending here. If it stops saying *smelting freed nothing — the
beetle has to be standing next to you*, call the beetle over and run it again.

### Before you run it

- **Stand on the vein**, within swinging distance. A first swing that comes back worked-out ends the
  run and says `no swing ever landed`, since that message from a run that never landed one means you
  were in the wrong place.
- **The fire beetle within `SMELT_RANGE`**, and yours. Further off and the ore stays ore.
- A pickaxe in hand, spares in the pack. Being mounted is fine.
- `ORE_TILE_GRAPHICS`, `SCAN_RADIUS`, `MINE_RANGE`, `MINE_Z_RANGE`, `RESPAWN_DELAY` and the
  pathfinding settings are not in this file at all — it never moves.

### What to set

The config block is the top of each file. **Every timing is in seconds** — `API.Pause` takes seconds
where the ClassicUO port took milliseconds — except `PATHFIND_TIMEOUT`, whose API takes a
whole-second int.

#### Finding the ore — `mining.py` only

| Setting | Default | What it is for |
| --- | --- | --- |
| `ORE_TILE_GRAPHICS` | stock RunUO bands | **The important one.** The land tiles the shard calls a mountain or a cave floor. Fill it in from what a dead-end run lists |
| `NOT_ORE_GRAPHICS` | empty | The override, and a seed only — a refusal learned on the shard goes to the run's memory, not back here |
| `ORE_STATIC_NAME` | `cave`, `rock`, `mountain`, `ore` | Cave floors are *statics*, and those the client names. Wider than it looks — `rock` also names the pebbles scattered over half the world — but that is the cheap direction: the first swing at one gets `notOre` and the art is banned |
| `MINE_RANGE` | `2` | Where walking stops and swinging starts — not a range the shard enforces, since the swing names no tile |
| `MINE_Z_RANGE` | `20` | How far above or below you a tile may sit and still be worth walking to. A mountain face 40 z up passes the 2D distance test and the walk at it never closes |
| `SCAN_RADIUS` / `SURVEY_ARTS` | `12` / `15` | How far the loop looks, and how many arts it lists on a dead end |
| `PATHFIND_TIMEOUT` | `10` | How long one blocking `API.Pathfind` may take |
| `MAX_VEIN_WALKS` | `4` | Cycles spent walking to one vein before it is written off |
| `MAX_PATH_PROBES` | `24` | At most how many of the nearest matches a full sweep pays an `API.GetPath` for. It stops early once no farther match can have a shorter route |
| `HARVEST_BANK` | `8` | The block *no harvestable resources nearby* is about on RunUO-family shards, parked whole |
| `RESPAWN_DELAY` / `UNREACHABLE_DELAY` | `1500.0` / `300.0` | How long a worked-out tile, and a tile with no route, are left alone |
| `NOTHING_NEARBY_HINT` | `5` | Empty spots in a row before it says `ORE_TILE_GRAPHICS` is probably wrong |

#### The tool

| Setting | Default | What it is for |
| --- | --- | --- |
| `PICKAXE_NAME` | `pickaxe` | Matched against the name; the graphic is learned from the one you start holding |
| `SPARE_BAG_SERIAL` | `None` | A bag to search as well. Rarely needed — `API.ItemsInContainer` already reads the pack recursively |
| `DIG_TIMEOUT` | `8.0` | A swing plays its animation before the result arrives |
| `DIG_TARGET_TIMEOUT` / `_POLL` | `4.0` / `0.1` | How long to watch for the cursor before reading the swing as refused, and how often |
| `DIG_PROMPT_TEXT` | `Where do you wish to dig` | **The sentence the shard opens the cursor with**, waited on as the cursor itself. Get this wrong and every swing may report `no target cursor` |
| `EQUIP_ATTEMPTS` / `_TIMEOUT` / `_POLL` | `3` / `2.0` / `0.2` | Equip pacing |
| `DISMOUNT_TIMEOUT` / `_POLL` / `_ATTEMPTS` | `2.0` / `0.2` / `3` | Getting off the mount |

#### Ore, metals and smelting

| Setting | Default | What it is for |
| --- | --- | --- |
| `ORE_GRAPHICS` | four arts | The arts an ore pile is drawn with. A set to match against and nothing more — never a way to read a stack's size |
| `ORE_NAME_WORD` | `ore` | The whole-word fallback for a shard whose ore wears an unknown art. A whole word, or `sycamore` would put something in the smelter |
| `FIRE_BEETLE_GRAPHICS` / `_SERIAL` | `0xa9` / `None` | The stock body, and a way to pin one exactly and skip the search |
| `PICK_BEETLE` | `True` | A cursor at startup to click your beetle, ESC to fall back to the search. A picked beetle is pinned |
| `PICK_TIMEOUT` | `60.0` | How long you have to answer that cursor — it waits on a person, not the shard |
| `BEETLE_SCAN_RADIUS` / `SMELT_RANGE` | `18` / `2` | How far to look, and how close to stand |
| `MIN_SMELT_AMOUNT` | `2` | Two ore make an ingot, so a stack of one cannot be smelted and the refusal is silent |
| `SMELT_ATTEMPTS` | `3` | Silent failures in a row before giving up on a hue. More than one, because a throttled or stale attempt also looks silent |
| `MAX_SMELT_PASSES`, `SMELT_DELAY`, `SMELT_TIMEOUT`, `SMELT_POLL` | `60`, `0.7`, `4.0`, `0.2` | Smelting loop bounds and pacing |
| `COMBINE_DELAY`, `COMBINE_TIMEOUT`, `COMBINE_POLL`, `MAX_COMBINE_ATTEMPTS` | `0.7`, `2.0`, `0.2`, `12` | Consolidation pacing and its backstop |
| `ORE_SETTLE_TIMEOUT` / `_POLL` | `1.5` / `0.15` | How long to wait for a swing's ore, which arrives after the sentence announcing it |
| `ORE_METALS` | RunUO's nine | Metal names. One this shard has that these do not joins the set off its first tooltip |
| `METAL_LINE_EXTRA` / `NOT_METAL_WORDS` | `" '-"` / flags | Which tooltip line is the metal: letters and these only, and not one of the flags every item can carry |
| `METAL_MISSES` / `METAL_ASKS` | `3` / `3` | How many tooltips carrying no metal line before the lookup stops asking, and how many passes one pile gets. A tooltip not there yet is requested and read next pass, never waited for |
| `DIFFERENT_ORE_TEXT` | RunUO's wording | The shard refusing two piles as different metals. The backstop for a pile no tooltip named |
| `INGOT_GRAPHICS` | four arts | A seed only — the real graphic is learned by diffing the pack across the first smelt |

#### Trouble and stopping

`WATCH_FOR_TROUBLE` is the whole feature: each cycle scans `THREAT_RANGE` for a hostile, watches
your hits and the beetle's, and logs `trouble` / `clear`. Nothing calls the guards. `PACK_LIMIT` is
the item-cap guard and there is deliberately **no weight guard** — one would fire before the smelt
could ever run.

| name | default | what it is |
|---|---|---|
| `AMBUSH_TEXT` | `["been ambushed"]` | Fragment of what your character says on an ambush. The journal line carries the name first |
| `AMBUSH_WARNING` / `AMBUSH_HUE` | `"AMBUSHED!"` / `33` | Shown over your head once per ambush |
| `AMBUSH_ALARM` | `afplay` on a system sound | A command run on this Mac, outside the game, so the client's sound setting does not matter. Any file `afplay` can play. Restarted when it ends while trouble lasts, never layered |
| `AMBUSH_NOTICES` | one `osascript` notification | Commands run once per ambush. `["say", "ambushed"]` is a spoken one |
| `AMBUSH_REPEATS` | `30` | Starts the alarm gets. It stops sooner once a hostile has come and gone |

### When it goes wrong

**`no ore in range` while standing on a mountain.** The likeliest failure: `ORE_TILE_GRAPHICS` does
not match this shard's tile numbering. The stop prints the commonest arts under your feet in hex and
decimal, with `MATCHES` against the ones the config accepts.

**`n vein(s) matched but had no walkable route`.** Ore the scan recognised and `API.GetPath` would
not answer for. A few is ordinary — a mountain has two sides. All of them, in a spot you can plainly
walk out of, means `GetPath` will not answer for a tile you can only stand *beside*.

**Five spots in a row with nothing to harvest.** Same cause as the first, caught earlier.

**`unreadable outcome, check OUTCOME_TEXT`.** The shard words its harvest messages differently. Read
the journal after a swing and correct `OUTCOME_TEXT`.

**`no target cursor (n/20), backing off`.** The shard declined to start the swing and said nothing
about why. A run of them with a pickaxe in hand means the refusal is worded in a way
`THROTTLED_TEXT` does not have — add it and it becomes a throttle, which costs the run nothing. If
you can see *Where do you wish to dig?* on screen while the log says this, correct `DIG_PROMPT_TEXT`.

**`overweight … and smelting freed nothing`.** No beetle in range, a beetle that is not yours, or
every hue written off. The run clears the write-offs, consolidates and smelts once more before
giving up — once, not once per cycle.

**`tooltips are not naming the metal here`.** Three piles in a row answered with a bare name, so the
run falls back to telling the metals apart the slow way — attempt a pair, read the refusal. Ordinary
on a shard with no OPL. If the metal *is* on screen and this still fires, `NOT_METAL_WORDS` is
eating the line.

**`the shard refused two piles both read as 'x'`.** The line being read as the metal is not the
metal. Correct `METAL_LINE_EXTRA` or `NOT_METAL_WORDS` against what the tooltip actually shows.

**`could not get off the mount`.** `API.Dismount` is not how this shard dismounts.

**`no pickaxe`.** Nothing in hand and no spare found. The failure path logs every graphic it saw.

### Notes on the API

- **`API.Pause` takes seconds.** Every constant ported from `src/mining/config.ts` was divided by
  1000, except `PATHFIND_TIMEOUT`, whose API takes a whole-second int already.
- **There is no blocking journal wait**, so `OUTCOME_TEXT` is a list of `(name, phrases)` tuples
  polled in **declaration order** rather than resolved by which phrase arrived first. That makes the
  order load-bearing in a way it was not in TypeScript, and it is why `saving` and `throttled` sit
  last: `THROTTLED_TEXT` ends in a bare `You must wait` that longer sentences contain.
- **Nothing clears the whole journal.** `API.ClearJournal` takes a filter, and each action clears
  only the lines it is about to wait on: a wholesale clear before every swing wiped the ambush
  warning before the threat watch's once-a-cycle look at it.
- **Which reads consume and which do not.** Only the outcome read passes `clearMatches=True`.
  Everything that merely observes — the save check, the throttle and unskilled checks inside the
  smelt, `DIFFERENT_ORE_TEXT` — reads without consuming, because each is read more than once.
  Consuming the ore refusal inside the merge poll would make the combine's own refusal branch
  unreachable and silently split a metal.
- **Every call that reads game state is one client frame.** The client queues it for the game
  thread and drains the queue once per `Update`, so a sweep's tile reads and route probes scale with
  the FPS cap, and "reduce FPS when inactive" slows every wait several times over. Journal reads
  stay on the script thread. A refused `API.GetPath` is a full A* to its node budget, which is why
  the scan parks the tile for `UNREACHABLE_DELAY` rather than asking again next sweep.
- **`API.Pathfind` and `API.GetPath` replace the web client's walkability grid.** `src/lib/grid.ts`
  (382 lines), `tiles.ts`, `flags.ts` and `walk.ts` have no counterpart here, and neither do the
  tile flags, the `MAX_CLIMB`/`PLAYER_HEIGHT`/`STEP_HEADROOM` approximation, or the route budget.
- **`API.Dismount` exists**, so the web client's double-click-yourself workaround is gone.
- **`API.ItemsInContainer(container, True)` reads the pack recursively** in one call, which replaces
  the whole of `src/lib/containers.ts`. The item-cap guard and the combine still count the **top
  level only**, because the cap is per container.
- **`API.ItemNameAndProps` returns a flat string**, not a property list: line 0 is the name and the
  metal is one of the lines under it, so "no properties" becomes "one line and nothing else".
- **`ApiStatic` carries its own `Name`**, so there is no static-tiledata lookup and no name cache.
- **There is no `getTerrainList`.** `API.GetTile` gives the land tile and `API.GetStaticsAt` the
  statics, and the two tiledata tables are still numbered separately — so every ban keys `land:231`
  rather than `231`, or one ban would hide an unrelated art.
- **`API.GetAllMobiles` takes a range**, so `THREAT_RANGE` is an argument rather than a post-filter.
- **`API.Notoriety` members are passed through to the scans, never compared or OR-ed.** The `API.py`
  stub lists every one as `= 1`, which is a stub-generation artifact; only the runtime knows their
  real values.
- **`re` is deliberately not imported, though it would now work.** `ScriptFile.SetupPythonEngine`
  puts `iplib/`, `LegionScripts/` and the script's own folder on `sys.path`, so the standard library
  is genuinely there. The three config regexes stay plain-string tests because they are clearer that
  way, not because the import would fail.
- **The tile memory is per-run.** `src/lib/store.ts` parked it on `globalThis` because the QuickJS
  context survives a restart; nothing here does, so a restarted run re-learns every ban.
  `API.SavePersistentVar` exists and is deliberately not used.

### Known unverified

- **`ORE_TILE_GRAPHICS`**, which is the one that matters. Copied from the stock RunUO mountain and
  cave tables, unconfirmed against UOAlive.
- `OUTCOME_TEXT`, on the same footing. `empty` matters most: it is what parks a vein.
- **Three phrasings that do not obviously agree.** `You cannot mine there` sits in `empty`, so it
  parks the tile; on most shards that sentence means the tile is not mineable at all, which is
  `notOre` and a permanent ban. `There is nothing here to harvest` and `There is no ore here to
  mine` are close enough that a hybrid wording lands in whichever bucket comes first.
- Whether **`API.TargetSelf()` after `API.UseObject(pickaxe)` is how this shard aims a dig**, and
  whether `API.TargetResource(serial, 0)` is the better call. It is deliberately not used: it
  bypasses the `DIG_PROMPT_TEXT` read and the noCursor/throttled distinction.
- Whether **`API.HasTarget()` is honest** where the web client's `target.open` was not, and so
  whether waiting on `DIG_PROMPT_TEXT` as well is still earning its place.
- Whether **`API.GetPath` answers for a tile you can only stand beside**, and whether it is cheap
  enough for `MAX_PATH_PROBES` candidates a sweep.
- Whether **`API.Pathfind` closes on a mountain face 20 z up**. Its own docstring says it fails at
  large distances; `SCAN_RADIUS` is 12, probably inside that, but unmeasured.
- Whether **`API.GetTile` answers the land tile** or the topmost object at that coordinate. If the
  latter, every land match is wrong — and the dead-end survey is what says so.
- Whether `ApiStatic.IsCave` is a better static test than the name list. It is printed by the survey
  and nothing branches on it.
- Whether **`"onehanded"` is the layer** a pickaxe lands on here.
- Whether **`Amount` reads 0 for a stack the client has no data for**, the way `item.amount` did.
  `MIN_SMELT_AMOUNT` is written on the assumption that it does.
- `RESPAWN_DELAY` and `MINE_Z_RANGE`, neither measured on this shard.
- The fire beetle body `0xa9`, whether a beetle smelts by being targeted with an ore stack here, and
  whether it has to be yours. `IsRenamable` is what tells your pet from a stranger's.
- `DIFFERENT_ORE_TEXT`, the stock RunUO wording. A shard that words it differently reaches the
  grouping as silence, which splits the pair for the pass and says so.
- **The ambush alarm** — whether the script engine lets `import clr` reach
  `System.Diagnostics.Process`; a refusal is logged once as `could not run afplay`. Also whether
  the encounter spawns come up gray or red so `trouble` keeps it sounding, and whether the
  `Notoriety` members are distinct at runtime.

## lumberjack.py

Works a patch of forest: finds the nearest tree, walks to it, chops, turns the logs into boards as
the weight climbs, and puts the boards onto your pack animals. Ported from `dist/lumberjack.js`,
**without that script's `BOUNDS` box** — the ClassicUO run never steps outside a rectangle of
hardcoded coordinates, and this one roams. `API.Pathfind` does the walking, so `src/lib/grid.ts`'s
walkability map, the route flood and the climb rules have no counterpart here, exactly as in
`mining.py`.

Before the loop: learn the axe from what you are holding, say what is in the pack, raise the
pack-animal cursor, and haul once if the pack already arrived over `HAUL_BUFFER` — in that order, so
a pack pasted in full is not stopped on cycle zero by the weight guard before a haul ever ran.

Per cycle:

1. **Check the stop conditions** — dead, overweight beyond `WEIGHT_BUFFER`, or the pack at its item
   cap.
2. **Sit out a world save.** Every step below reads that silence as its own kind of failure.
3. **Equip an axe**, every cycle, so a broken one costs a cycle rather than the run. Spares come out
   of the pack.
4. **Haul, if the weight is over `HAUL_BUFFER`.** Boards are made first — only boards ever go on an
   animal — then every animal in range is walked to and filled, nearest first.
5. **Scan for a tree** within `SCAN_RADIUS` *and* `CHOP_Z_RANGE` of your own elevation, skipping
   tiles the run has parked and trees `API.GetPath` can find no route to. If that box is dry, sweep
   again out to `ROAM_RADIUS`.
6. **Walk to it** with `API.Pathfind` if it is further than `CHOP_RANGE`.
7. **Chop**, and branch on what the shard says.

| Outcome | What the loop does |
| --- | --- |
| `chopped` | Count it and carry on |
| `empty` | Out of wood. Parks the trunk, or the whole spot when `AIM_AT_SELF` — see below |
| `nothingNearby` | The shard answering about everything in reach. **Always** parks the ground within `CHOP_RANGE`, whichever way the swing was aimed |
| `notTree` | Set the tree aside, and ban the whole art as well when the swing named it |
| `tooFar` | The shard disagreeing about the range. Set the tile aside |
| `notSeen` | Line of sight. Permanent — neither walking closer nor waiting fixes it |
| `packFull` | Haul. One log stack converts to one board stack, so consolidating would give back almost nothing; what frees slots is boards leaving for the animal |
| `wornOut` | The axe broke; the next cycle equips a spare |
| `saving` | Sit it out; no counter is held against it |
| `throttled` | Back off further each time, and give up after `MAX_THROTTLED` |
| `noCursor` | No cursor and the journal explained nothing. Backed off like a throttle, stops after `MAX_NO_CURSOR` |
| anything else | Unreadable. `MAX_UNKNOWN` in a row ends the run — check `OUTCOME_TEXT` |

When nothing within `ROAM_RADIUS` is choppable but something is regrowing, the loop **idles until
the soonest one is due** rather than ending the run — sliced into `IDLE_POLL` sleeps, because one
blocking sleep of twenty minutes leaves the client unresponsive with no way to stop the script, and
nothing would watch for trouble meanwhile.

However the run ends, it makes boards and unloads one last time.

### How the swing is aimed

`AIM_AT_SELF` decides it, and it is the one setting that changes what two of the outcomes above
*mean*.

**`True`, the default.** `API.TargetSelf()`, the way `mining.py` and `mine-here.py` swing: this
shard takes a self-target as *harvest what is in reach* and picks the tree itself. The scan still
earns its place — it is what decides where to stand — but the shard chooses what the axe lands on.
Two consequences the loop handles:

- **`empty` is about the spot, not the trunk.** So it parks every tree within `CHOP_RANGE` for
  `REGROW_DELAY`, not just the one the scan picked. Parking a single tile left `mining.py` swinging
  at the neighbour the shard had just written off, for the same sentence. `nothingNearby` — *There
  are no harvestable resources nearby* — is that answer said outright, and parks the ground either
  way.
- **`notTree` bans no art.** The shard chose what to refuse, so banning the art of the trunk the
  scan happened to pick could write off a perfectly good tree. The tile is set aside one at a time
  instead — slower across a stand of scenery, but never wrong about which art it was.

**`False`.** `API.Target(x, y, z, graphic)` names the scanned tree's tile and its art — the
four-argument overload, and the counterpart of the web client's `target.terrain`. The graphic is
never left off: without it the target is the *land* tile, which the shard answers as mining rather
than as chopping. A static carries no serial, so naming the tile and its art is the only other way
to aim at one at all. Aimed this way `empty` parks that trunk alone and `notTree` bans the whole
art, which is what `dist/lumberjack.js` does.

### Boards and hauling

Logs become boards by **using the axe and targeting the log stack** — the inverse of smelting, where
the ore is used and the forge targeted. Stock RunUO answers with a sound and no message, so the
result is read from a pack diff, and that diff also *names* the board graphic — which is why
`BOARD_GRAPHICS` is a seed only and a wrong guess corrects itself on the first conversion.

Hue is deliberately not part of the log match: a shard with special woods hues its logs, and those
still count, still convert and still need hauling. Hue *is* what the converter's write-offs are
keyed on, so one wood refusing does not stop the rest.

**Only boards go onto an animal, never logs.** A log that leaves as a log never comes back as a
board, so a wood given up on stays in the pack and every haul reconsiders it — the verdict is a
backstop for one pass, not for the run.

All the animals get loaded, not just the nearest: one that stops accepting is full rather than
broken, so what is left goes to the next. An animal that takes **nothing at all** is written off and
skipped for the rest of the run — one that took a partial load keeps its turn and is tried again on
the next haul. Their packs come from `ApiMobile.Backpack`, falling back to
`API.FindLayer("backpack", serial)`. **The web client's double-click fallback is deliberately not
ported** — it is a `UseObject` on a rideable giant beetle, which mounts you, and nothing in this file
dismounts.

Two latches end the walking for good, and both say so: no animal found at all, and
`MAX_EMPTY_HAULS` hauls in a row that freed no weight, which is what a set of full animals looks
like — and reached without walking anywhere now, since the written-off animals are skipped. After
either, the run keeps chopping — and keeps converting, since boards weigh less than the logs they
came from — until the overweight guard stops it.

### Before you run it

- Stand in the forest you mean to work. There is no bounds box, so it will wander after the wood.
- **An axe in hand.** The run learns its graphic from what you are holding; spares go in the pack.
  Axes are two-handed and hatchets one-handed, and both layers are read, in that order.
- **Your pack animals nearby**, if you want hauling. Only your own count — the search keeps the ones
  whose `IsRenamable` is true. Without one the run still chops; it stops when the weight guard fires.
- Being mounted is fine. Unlike `mining.py` this run never dismounts, since there is no pet it has to
  target. It does warn at the cursor, in case the animal you want is the one you are sitting on.

### What to set

The config block is the top of `lumberjack.py`. **Every timing is in seconds** except
`PATHFIND_TIMEOUT`, whose API takes a whole-second int.

| Setting | Default | What it is for |
| --- | --- | --- |
| `AIM_AT_SELF` | `True` | How the cursor is answered, and what `empty` and `notTree` are evidence about. See above |
| `AXE_NAMES` / `NOT_AXE_NAMES` | `axe`, `hatchet` (+plurals) / `pickaxe`, `shovel` | Matched as **whole words**, and the exclusion is load-bearing: `axe` is inside `pickaxe`, so a substring match equips the mining tool the moment the real axe breaks. The graphic is learned from the one you start holding, and the exclusion vetoes even that |
| `SPARE_BAG_SERIAL` | `None` | A bag to search as well. Rarely needed — `API.ItemsInContainer` already reads the pack recursively |
| `TREE_GRAPHICS` / `NOT_TREE_GRAPHICS` | empty | The overrides, asked before `IsTree`. Fill the first in from what a dead-end run lists |
| `TREE_NAME` | `['tree']` | The name fallback for a build that leaves `ApiStatic.IsTree` unset |
| `CHOP_RANGE` / `CHOP_Z_RANGE` | `2` / `20` | Where walking stops and swinging starts, and how far above or below you a tree may sit and still be worth walking to |
| `SCAN_RADIUS` / `ROAM_RADIUS` | `12` / `24` | The ordinary sweep, and the wider one paid only on a cycle that would otherwise stand still |
| `SURVEY_ARTS` | `15` | Arts named when a sweep comes up empty, commonest first |
| `PATHFIND_TIMEOUT` | `10` | How long one blocking `API.Pathfind` may take |
| `MAX_TREE_WALKS` | `4` | Cycles spent walking to one tree before it is written off |
| `MAX_PATH_PROBES` | `24` | How many of the nearest matches a sweep pays an `API.GetPath` for |
| `REGROW_DELAY` / `UNREACHABLE_DELAY` | `1500.0` / `300.0` | How long a chopped-out tree, and one with no route, are left alone |
| `EMPTY_HINT` | `5` | Empty spots in a row before it says the tree test is probably matching scenery |
| `CHOP_TIMEOUT` | `8.0` | A swing plays its animation before the result arrives |
| `CHOP_TARGET_TIMEOUT` / `_POLL` | `4.0` / `0.1` | How long to watch for the cursor before reading the swing as refused, and how often |
| `CHOP_PROMPT_TEXT` | three wordings | **The sentence the shard opens the cursor with**, waited on as the cursor itself. Get this wrong and every swing may report `no target cursor` |
| `LOG_GRAPHICS` / `LOG_NAME_WORDS` | four arts / `log`, `logs` | The arts a log stack is drawn with, and the whole-word fallback for a shard whose logs wear an unknown art |
| `BOARD_GRAPHICS` / `BOARD_NAME_WORDS` | four arts / `board`, `boards` | A seed only — the real graphic is learned by diffing the pack across the first conversion |
| `CONVERT_ATTEMPTS` | `3` | Silent failures in a row before giving up on a hue for that pass. A save, a throttle and a cursor that never opened are all excluded, so reaching this means the wood really did not work |
| `MAX_CONVERT_PASSES`, `CONVERT_DELAY`, `CONVERT_TIMEOUT`, `CONVERT_POLL` | `60`, `0.7`, `4.0`, `0.2` | Conversion bounds and pacing |
| `PACK_ANIMAL_GRAPHICS` / `_SERIALS` | pack horse, pack llama, giant beetle / `[]` | The stock bodies, and a way to pin an exact list and skip the search |
| `PICK_PACK_ANIMALS` / `MAX_PICKS` / `PICK_TIMEOUT` | `True` / `8` / `60.0` | A cursor at startup to click your animals, ESC when done. A picked list is pinned for the run |
| `ANIMAL_SCAN_RADIUS` / `UNLOAD_RANGE` | `18` / `2` | How far to look, and how close to stand to move items across |
| `MOVE_DELAY` | `0.7` | Between moves, to stay under the action throttle |
| `HAUL_BUFFER` / `WEIGHT_BUFFER` | `120` / `40` | The headroom at which it goes to haul, and the one at which it stops. The first is deliberately the wider, so hauling always gets its turn first |
| `MAX_EMPTY_HAULS` | `3` | Hauls in a row that freed no weight before the animals are taken to be full |
| `OUTCOME_TEXT` | guesses | The shard's wordings. Correct these first when anything goes wrong |

Trouble and stopping carry the same names and defaults as `mining.py`.

### When it goes wrong

**`no tree in range` in a forest.** Nothing matched and nothing is on cooldown. The stop prints the
statics under your feet in hex *and* decimal, with `MATCHES`, `IsTree` and the name beside each —
that listing is how `TREE_GRAPHICS` or `TREE_NAME` gets corrected.

**`n tree(s) matched but had no walkable route`.** Trees the scan recognised and `API.GetPath` would
not answer for. A few is ordinary. All of them, somewhere you can plainly walk out of, means
`GetPath` will not answer for a tile you can only stand *beside*.

**`5 spots in a row had nothing to chop`.** Same cause as the first, caught earlier: the tree test is
matching scenery the shard will not harvest.

**`unreadable outcome, check OUTCOME_TEXT`.** The expected first-run failure — most of the phrasings
are stock RunUO guesses, and the ClassicUO script they came from was never run either. Read the
journal after a chop and correct them. The first live run hit this on *There are no harvestable
resources nearby*, which is now the `nothingNearby` bucket.

**It looks like it is mining rather than chopping.** Two causes, in order of likelihood. First, check
the opening `axe graphic is 0x… ('name')` line: if it names a pickaxe, the tool match picked up the
wrong thing — `AXE_NAMES` is whole-word and excludes `pickaxe` precisely because `axe` is a
substring of it, so this should no longer happen, but a shard whose pickaxe is named something else
wants that name in `NOT_AXE_NAMES`. Second, `AIM_AT_SELF` hands the choice of resource to the shard:
standing on rock with nothing choppable in reach, a shard that falls through to ore will dig with
whatever is in your hand. Set `AIM_AT_SELF = False` and the swing names the tree instead.

**`no target cursor (n/20), backing off`.** The shard declined to start the swing and said nothing
about why. A run of them with an axe in hand means the refusal is worded in a way `THROTTLED_TEXT`
does not have — add it and it becomes a throttle, which costs the run nothing. If you can see the
prompt on screen while the log says this, correct `CHOP_PROMPT_TEXT`. The line names what is in the
hand, because the axe layer is the other thing likely to be wrong.

**`no pack animal found`** or **`3 hauls freed nothing - the animals are full`.** Both latch the
walking off for the rest of the run and let it chop on until the weight guard stops it. Click the
animals at startup, check `PACK_ANIMAL_GRAPHICS`, or pin `PACK_ANIMAL_SERIALS`.

**`'X' took nothing, leaving it out of the rest of the run`** and **`all n pack animal(s) are full,
nothing left to load`.** Expected, not a fault — a full animal is only emptied at the bank, and that
ends the run. A world save is excluded: it says `took nothing while the world is saving` instead and
the animal keeps its turn.

**`N logs would not convert, keeping them in the pack`.** The wood is never hauled as logs, so the
weight stays. Check the journal is not saying you are unskilled, and confirm `BOARD_GRAPHICS`
against the shard before raising `CONVERT_ATTEMPTS`.

### Notes on the API

- **`API.Target` is overloaded**, and IronPython picks between them by arity: `API.Target(serial)`
  answers a cursor with an item, `API.Target(x, y, z, graphic)` with a location. The converter uses
  the first, the tile-aimed chop the second. All four arguments go in positionally — the fourth
  defaults to `1337`, which is the land-tile case the ClassicUO script found to be wrong.
- **`API.GetStaticsInArea` sweeps a whole box in one call**, and every `ApiStatic` carries its own
  `X`/`Y`/`Z`. Trees are statics, so nothing here calls `API.GetTile`, and `mining.py`'s nested
  coordinate loop, its `terrain_cache` and its land-versus-static art keys are all gone with it. No
  cache sits behind the sweep either: a sweep is one call, and a felled tree that changes art would
  go stale in one.
- **`ApiStatic` carries `IsTree`**, so there is no tiledata lookup and no name regex — the web
  client had to match the tiledata *name*, which is `src/lumberjacking/`'s known over-reach.
- **`ApiStatic` extends `ApiGameObject`, not `ApiEntity`, so a static has no serial.** That is why a
  tile-aimed chop has to name coordinates and an art.
- **`API.FindLayer` takes an optional serial**, so another mobile's pack is
  `API.FindLayer("backpack", serial)` — and `ApiMobile.Backpack` answers it directly, which is
  asked first.
- **`API.Pause` takes seconds**, so every constant ported from `src/lumberjacking/config.ts` was
  divided by 1000. `PATHFIND_TIMEOUT` is the exception: its API takes a whole-second int.
- **There is no blocking journal wait**, so `OUTCOME_TEXT` is a list of `(name, phrases)` tuples
  polled in **declaration order**. That makes the order load-bearing, and it is why `saving` and
  `throttled` sit last: `THROTTLED_TEXT` ends in a bare `You must wait` that longer sentences
  contain.
- **The tree memory is per-run.** `src/lumberjacking/memory.ts` parks it on `globalThis` because the
  QuickJS context survives a restart; nothing here does, so there is no `RESET_MEMORY` and a
  restarted run re-learns every ban. `API.SavePersistentVar` exists and is deliberately not used.
- **`WeightMax` reads 0** before the client has been told, against which every weight is overweight —
  a live mining run ended at 436/453 on exactly that. Both weight tests check for a positive ceiling
  first.
- **`mining.py`'s metal machinery has no counterpart**, and neither does its consolidation. Both
  exist to answer *may these two piles be merged?*, which only arises because the shard refuses
  cross-metal merges silently and names the metal only in a tooltip. Logs are told apart by graphic
  and hue outright, so `API.ItemNameAndProps` is never called here.

### Known unverified

- **Confirmed:** a self-target harvests wood here. A live run answered *You chop some ash logs and
  put them into your backpack*, so `AIM_AT_SELF = True` is right for this shard, and the `chopped`
  and `nothingNearby` wordings are measured rather than guessed.
- **Whether a self-target reaches for ore** when nothing choppable is in reach and the character is
  standing on rock. If it does, the answer is `AIM_AT_SELF = False`.
- **`API.Target(x, y, z, graphic)` as the other way**, and that IronPython binds the four-argument
  overload by arity. If it binds `Target(serial)` instead, tile-aimed chops read as unreadable — a
  diagnosable stop, not a silent wrong turn.
- **That the graphic must be passed.** Taken from a *web client* finding about `target.terrain`, not
  re-measured here.
- **`ApiStatic.IsTree`.** Never used before in this repo, and the one live data point says the
  client's idea of a tree over-reaches: `0xc9e`, *o'hii tree*, refused with *You can't use an axe on
  that*. The art ban is what makes a wrong `IsTree` cost one swing per art rather than a run — and it
  is off under `AIM_AT_SELF`, where the shard rather than the scan chose the target.
- **Which static of a tree is the trunk.** One tree is several statics, and `CHOP_Z_RANGE` plus the
  per-tile cooldown are the only things keeping the run off the foliage. Neither is a real test.
- **Whether a chopped-out tree changes art.** If it does, `still_tree` drops it on the next cycle,
  which is the intended behaviour but is untested.
- `OUTCOME_TEXT`, on the same footing as `mining.py`'s. `empty` matters most: it is what parks ground.
- **`REGROW_DELAY`.** 25 minutes is a guess at the shard's respawn timer, unchanged from the
  TypeScript.
- **`LOG_GRAPHICS` and `BOARD_GRAPHICS`**, both of which assume log and board stacks change art with
  size the way ore does. The board set corrects itself on the first conversion's pack diff; the log
  set does not, which is what `LOG_NAME_WORDS` is for.
- **Whether boards actually weigh less than logs here.** If they do not, converting frees nothing and
  only the animal relieves the pack.
- **The pack animal bodies**, and whether `ApiMobile.Backpack` or `API.FindLayer("backpack", serial)`
  resolves for a mobile that is not you. The double-click fallback is deliberately absent, so a shard
  that publishes neither means no hauling at all; `PACK_ANIMAL_SERIALS` pins an exact list.
- **Whether `API.RequestTarget` returning falsy is ESC** rather than a timeout, which is what ends
  the multi-pick.
- **`"twohanded"` and `"onehanded"` as the layers** an axe lands on here.
- **What `API.GetStaticsInArea` costs at `ROAM_RADIUS`** — 49 tiles a side, walked attribute by
  attribute through interop, once per dry cycle.
- The ambush alarm, on the same footing as `mining.py`'s.

## arms-lore.py

Target one weapon, then use **Arms Lore** on it every `DELAY` seconds until the skill hits its cap
or you stop the script. It does not walk, and the weapon can sit in your pack.

### Before you run it

- The weapon has to stay where the client can resolve it — dropped or handed away ends the run.
- A use the shard refuses raises no cursor, so the pass times out after `TARGET_TIMEOUT` and the
  next one asks again. Nothing is recorded for it.

### What to set

| Setting | Default | What it is for |
| --- | --- | --- |
| `DELAY` | `0.5` | Seconds between uses. Below the shard's skill timer this just spends passes on refusals |
| `TARGET_TIMEOUT` | `1.0` | How long a use is given to put a cursor up |
| `READ_TIMEOUT` | `1.5` | How long a reading is given to say what it found |
| `READ_POLL` | `0.1` | How often the journal is asked during that wait |
| `PICK_TIMEOUT` | `30.0` | How long the opening cursor waits for you |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each reading is appended. `""` records nothing |

### Known unverified

- **Every phrase in `OUTCOME_TEXT` is a guess.** Nothing in this repo has watched Arms Lore on this
  shard. The refusals are a reconstruction of the stock RunUO wording, and `read` is a list of stems
  — `damage`, `durability`, `quality` — rather than any one sentence, because a shard reports what
  it found in wording no two agree on. The journal is cleared before every use, so a stem only ever
  sees this reading's own text, which is the same bargain `evalint` makes on the ClassicUO side.
- What this costs when it is wrong is visible rather than silent: an unmatched outcome is counted,
  reported at the end as `N outcome(s) went unread`, and **not** recorded. Watch one run, read what
  the shard actually says, and correct the table.
- **A wrong table also slows the run down.** A reading whose wording no bucket matches waits out the
  whole of `READ_TIMEOUT` before the pass gives up, so a run that reports every outcome as unread is
  also crawling. That is the symptom to look for; the fix is the wording, not a shorter timeout.

## magery.py

Trains **Magery** by casting whichever of four spells still gains at the level the skill has reached,
meditating when the pool runs dry, and stopping when the last band is done. It raises no cursor of
its own — start it and leave it. Per cycle:

1. **Check the stop conditions** — dead is the only one.
2. **Read the skill**, and pick the band the value falls in.
3. **Meditate if the pool is short of the row's `mana`**, filling it right up.
4. **Cast the row's spell**, answering its own cursor, and read whether it landed.
5. **Pace**, and go round again, until 120.0 is passed.

| Band | Spell | Circle | Mana | Cursor | What it is |
| --- | --- | --- | --- | --- | --- |
| ≤ 45.0 | Bless | 3rd | 9 | at self | A self buff |
| 45.0 – 60.0 | Arch Protection | 4th | 11 | at self | A self buff |
| 60.0 – 80.0 | Invisibility | 6th | 20 | at self | A self buff |
| 80.0 – 120.0 | Earthquake | 8th | 50 | none | An **area attack**. It hits everything around you |

Every guide trains Magery with damage spells thrown at a creature, and this loop has no way to find
one, keep it alive or keep it in range. These are the spells the same guides name as gaining without
a victim. The 5th and 7th circles are skipped: every 7th-circle spell wants a cursor over ground or a
gump answered, and neither is something this loop can do.

| Outcome | What happens |
| --- | --- |
| `cast` | Tallied, and the fault counters cleared |
| `fizzled` | Counted, not tallied. Ordinary, and commoner the further a circle is above the skill |
| `alreadyCasting` | Waits `CASTING_WAIT`, flat. **Never** counted towards a stop. This is where *you have not yet recovered from casting a spell* lands |
| `alreadyUp` | Waits `BUFF_WAIT`. Only reached with `SKIP_WHEN_BUFFED` on, or a refusal in words |
| `disabled` | Tallied — a shard that treats one of these as a toggle still charged for the cast |
| `noMana` | Says the row's `mana` is understated, then gathers mana |
| `noReagents` | **Stops.** Nothing waited for refills a pouch |
| `unskilled` | **Stops** — the table is aimed at a skill this character cannot use |
| `saving` | Sits the world save out and resets the counters |
| `throttled` | Backs off, growing, `MAX_THROTTLED` in a row ends the run |
| anything else | Unreadable — said once per stretch and carried on with. It ends nothing on its own |

`MAX_STALE` cycles with no cast **and** no movement in the skill is the only ending left for a run
that is getting nowhere, and it cannot fire while the skill is still moving, however unreadable the
outcomes are. A dry mana stretch is charged what it cost in cycles rather than one, so one stretch is
worth however many casting cycles fit inside it.

### How a cast is read

In order: snapshot whether the buff is standing → snapshot mana → cancel a live cursor → clear the
journal → cast → answer the cursor if one comes up → poll the `OUTCOME_TEXT` buckets.

A successful cast says nothing this table knows, so two silent proofs carry it: the buff
**transitioned** from down to up, or mana strictly decreased. A buff already standing proves nothing,
which is why the snapshot is taken first. The journal is read first on every slice, so a fizzle that
somehow spent mana still reads `fizzled`.

The poll gives up early once `API.Player.IsCasting` has gone up and come back down — the incantation
is over, so the mana has either left the pool or it never will. `cast_timeout` is the ceiling on that
wait rather than the thing timing the cast.

**Nothing waits out the recovery afterwards.** `pace` is the row's `cast_delay` and nothing more.
Holding the next cast back while `IsRecovering` was still set made a Bless cycle several seconds of
standing still, and it buys nothing the shard does not already say: a cast issued too early is
refused in words, and that refusal costs one flat `CASTING_WAIT` and is never counted towards a stop.
One or two of those a band is the pacing working — it is how the run finds this shard's real cast
time without being told it. A band that is mostly them wants its `cast_delay` raised.

### The self cursor

**A pre-target queued before the cast is what answers it**, which is the order the client's own
`CastSpell` example uses. **The type has to be the one the shard raises**, so it comes off the row's
`target_kind` and defaults to `beneficial`, which is what every band here wants. A pre-target set to
`"neutral"` — the stub's default, and what `tame.py` passes — does not fire at all: the cursor is
left standing and the cast is spent for nothing. The pre-target is cancelled after every cast, or
one the cast never used stays armed for whatever the next one raises.

The post-cast answer is kept as a fallback for a shard where the pre-target does not land. It is
tried from inside the outcome poll — so it costs nothing on a cast the pre-target already took — and
issues `API.Target(API.Player)`, `API.TargetSelf()` and `API.Target(API.Player.Serial)` in turn until
the cursor goes down, **latching whichever worked** and saying so once:

```
mage: the cursor answers to Target(player)
```

No such line means the pre-target took every cursor, which is the ordinary case. `Target(player)` is
first because it is the one that answered a standing cursor when it was measured. Each candidate is
guarded on its own: `Target` is an overloaded C# method and handing it the wrong shape throws rather
than failing quietly, which would otherwise end the run through the loop's catch.

**`mage: the cursor would not take a self target`** on every cast means neither the pre-target nor
any of the three landed, and this shard wants the spell targeted some other way.

### Timing, measured

The first live run read every cast as unreadable, and the cause was one number. On this shard a
3rd-circle cast raises its cursor at **1.6s** and takes the mana at **1.8s**; `cast_timeout` was
`1.2`, so the read window closed before the spell finished and the proof never arrived inside it.
Every row's timeout is now that circle's measured time with a margin on top.

The same figure explains the older symptom of the cursor sitting up unanswered: a wait of 1.2s gave
up 0.4s before the cursor existed.

`legion/probe-target.py` is the throwaway that measured it — three casts of Bless, reporting when the
cursor appears and which of the pre-target types and answer calls the shard takes. Run it again if
any of this stops holding.

### The mana wait

Meditation is used with **whatever the character is holding** — nothing here undresses anyone. A
shard that refuses a trance with something in hand says so, and that refusal retires meditation for
the whole run and falls back on natural regeneration, which is slower but always available. So empty
your hands before you start; the start-up line says so if they are not.

`MEDITATE_TO_FULL` fills the pool rather than stopping as soon as the next cast is affordable, which
matters most on the last band at 50 mana a cast. The comparison is `>=`, never `!=` — a regenerating
pool passes a figure as often as it lands on it.

### Before you run it

- **Stand somewhere empty, and never in town.** The last band is Earthquake for forty skill points
  and it hits everything around you — in town that is the guards, and near anything blue it is a
  criminal flag. The script does not move, fight or heal.
- **Empty your hands.** Meditation is refused while anything is held, and this run will not put it
  away for you.
- **Carry reagents**, or wear a 100% Lower Reagent Cost suit. Running out ends the run by name.
- **Below about 30.0, buy the skill from an NPC trainer first.** The first row covers everything
  under 45.0, and at 25 it is mostly fizzles.
- It aims at **120.0**, which needs the power scrolls. The run stops at whatever the shard caps the
  skill at, and the start-up line says so when that is lower.

### What to set

The config block is the top of `magery.py`. **Every timing is in seconds.**

| Setting | Default | What it is for |
| --- | --- | --- |
| `STAGES` | four rows | One row per band: cast `spell` until the skill reaches `up_to`, at `mana` a cast |
| `STAGES[].up_to` | — | The skill value the row trains to, exclusive. A float — `74.6`, not the web client's tenths |
| `STAGES[].buff` | — | A `BuffIconType` member name, matched against `str(buff.Type)`. Earthquake has none and trains on the mana proof |
| `STAGES[].target` | `self` | Answers the row's own cursor. Every row but Earthquake |
| `STAGES[].cast_timeout` | 3.0 – 5.0 | **The one worth tuning.** The ceiling on how long *this row's* cast is read for. Below the spell's real cast time every success reads as unreadable |
| `STAGES[].cast_delay` | 0.3 – 0.6 | The whole of the pause between two casts. Too short costs one `CASTING_WAIT` per overshoot, which is the cheap mistake |
| `CAST_TIMEOUT` / `CAST_DELAY` | `2.0` / `0.75` | The fallback for a row that names neither. Every shipped row names both |
| `PROOF_GRACE` | `0.6` | How long after `IsCasting` falls the proof is still waited for — the mana lands a beat behind the flag |
| `SELF_TARGET_TIMEOUT` / `_POLL` | `1.0` / `0.1` | How long the cursor has to go down before the next way of answering it is tried |
| `SELF_ANSWERS` | three | The fallbacks for a cursor the pre-target did not take, tried in order |
| `CASTING_WAIT` | `0.5` | Flat wait after a cast the shard refused because the last one had not released you |
| `SKIP_WHEN_BUFFED` | `False` | **Off**: gating on the buff would cap the run at one cast per buff duration |
| `DISABLED_IS_PROGRESS` | `True` | **On**: a toggle is still a cast the shard charged for |
| `MEDITATE` | `True` | Off waits for natural regeneration instead |
| `MEDITATE_TO_FULL` | `True` | Fill the pool, or stop as soon as the next cast is affordable |
| `MEDITATE_TIMEOUT` / `_ATTEMPTS` / `_START_TIMEOUT` | `20.0` / `4` / `2.0` | One trance's watch, how many trances a stretch gets, and how long the shard has to say the trance started |
| `MANA_POLL` / `MANA_LOG_EVERY` | `0.5` / `10.0` | How finely the pool is watched, and how often it is reported |
| `REGEN_TIMEOUT` | `120.0` | The natural-regeneration fallback, and the price of one dry stretch |
| `MAX_STALE` | `500` | Cycles with no cast *and* no movement in the skill before the run gives up |
| `MAX_BLIND_READS` | `5` | Cycles the client may answer nothing for the skill before the run stops |
| `SKILL_TIMEOUT` / `SKILL_POLL` | `1.0` / `0.5` | How long the skill list is waited for at start-up |
| `MAX_THROTTLED` | `20` | Refusals in a row before the run stops |
| `MAX_CYCLES` | `5000` | The backstop |
| `OUTCOME_TEXT` / `MEDITATE_OUTCOME_TEXT` | guesses | What the shard says. Correct these first when anything goes wrong |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each cast is appended, one JSON object per line. `""` records nothing |

There is **no stall watchdog** and **no health floor**. The first because this run's cycles are mostly
mana coming back on purpose; the second because nothing in this table hurts the caster, so the only
thing that can take its health is something that wandered up.

### When it goes wrong

**`the cursor would not take a self target`** — neither the pre-target nor any of the three
fallbacks brought the cursor down. The cast is wasted and the next one cancels the cursor.

**`outcome unreadable - carrying on`** — usually **not** the phrase tables. A cast that worked says
nothing, so it is proved by the mana leaving the pool, and a `cast_timeout` shorter than the spell's
real cast time closes the window before that happens — which is exactly what the first live run did
on every band. Suspect the row's `cast_timeout` first, and only then the wordings. The other cause
is a row whose buff was already standing: it has no transition to show, so only the mana can prove
it.

**No `buff bar: ...` line, ever** — the client is publishing no buffs, so three of the four rows have
only the mana to prove themselves by. The dump is printed the first time any buff is seen.

**`buff bar:` prints ids this table does not use** — copy the `Type` you see into that row's `buff`.

**`N cycles without a cast or a change in the skill`** — the only ending for a run that is getting
nowhere. It cannot fire while the skill is still moving.

**`the shard refuses meditation (blocked)`** — something is in hand. Put it away and restart; the run
has already fallen back on natural regeneration for the rest of the session.

**`refused for mana at N`** — the row's `mana` is lower than the shard actually charges. Raise it.

**`out of reagents for ...`** — refill, or get the LRC suit.

**The log fills with *you have not yet recovered from casting a spell*.** That row's `cast_delay` is
shorter than this shard's recovery for it. One or two a band is the pacing working; a run that is
mostly this should raise the figure. Note that a refusal this table does **not** know is far more
expensive than one it does — an unread outcome spends the row's whole `cast_timeout` before it gives
up, where a matched one is read in a single `CAST_WAIT_SLICE`. That is what made the first paced run
look like it was standing still.

**Casts land but the skill does not move.** The circle has stopped gaining at this level; that is
what the next row is for, and it means the bound between them wants moving down.

**`Magery is capped at 100.0`** — no power scroll. The start-up line warned.

### Notes on the API

- **`API.CastSpell` matches partially**, so `STAGES` carries full spell names.
- **`API.PreTarget` only fires on a matching cursor type.** A spell cursor reports as `beneficial`
  here; the stub's default is `neutral`, and with that the pre-target silently never fires.
- **`API.HasTarget()` does report a server-raised spell cursor**, as both `any` and `beneficial`.
- **`Skill.Value` is a float** — `74.6`, not the web client's tenths `746` — and it reads `0.0`
  before the skill list arrives, which is also a real skill value. The reader reports `unknown`
  rather than coercing, and `MAX_BLIND_READS` bounds it.
- **`ManaMax` reads 0** before the client has been told, and a ceiling of 0 makes "wait until full"
  true the instant it is asked, so the target is recomputed on every poll and guarded.
- **`API.Player.IsCasting` and `IsRecovering` have no ClassicUO web-client equivalent.** They are
  what lets this port pace itself instead of converging on the shard's refusals. `IsCasting` is
  published here, going true 0.2s into a cast — but it falls *before* the mana leaves the pool, which
  is what `PROOF_GRACE` is for.
- **`API.ActiveBuffs()` objects never refresh** after they are handed over, so the bar is re-read
  every time the answer matters.
- **There is no blocking journal wait.** `InJournalAny` answers yes/no, so the outcome read polls the
  buckets **in order**, which is what makes bucket order load-bearing.
- **The cursor cancel is guarded** (`if API.HasTarget()`), unlike `src/lib/cast.ts`, which cancels
  unconditionally — that left the next cursor unusable in the run it was copied from.

### Known unverified

- **Every phrase in `OUTCOME_TEXT` except the recovery one, and every phrase in
  `MEDITATE_OUTCOME_TEXT` except the trance line.** RunUO-family guesses, written against UOAlive; a
  miss shows up as an unread outcome rather than as a silent wrong turn — but it is not free, see
  *When it goes wrong*.
- **Three of the four `BuffIconType` names.** `Bless` is confirmed off a live `buff bar:` dump; the
  other three are read from the same enum and the dump is what confirms them.
- **The band bounds.** A reading of the AFK guides — *50–86 Invisibility, 86 upwards Earthquake* is
  the one they agree on — not something measured on this shard. If a band stops gaining before its
  `up_to`, move the bound down.
- **Whether Arch Protection raises a cursor here.** It is marked `target: self`, which is right where
  it does; where it does not, the wait costs that row its `cast_timeout` on every cast.
- **The `cast_timeout` figures above the 3rd circle.** Only the 3rd was measured (1.8s); the other
  three are scaled from it, and a band that reads unreadable throughout wants its own raised.

## mysticism.py

Trains **Mysticism** by casting whichever of five spells still gains at the level the skill has
reached, meditating when the pool runs dry, and stopping when the last band is done. It raises no
cursor of its own — start it and leave it. Per cycle:

1. **Check the stop conditions** — dead, and a health floor the two area bands make worth having.
2. **Read the skill**, and pick the band the value falls in.
3. **Meditate if the pool is short of the row's `mana`**, filling it right up.
4. **Cast the row's spell**, answering its own cursor, and read whether it landed.
5. **Pace**, and go round again, until 120.0 is passed.

It is the same loop as `magery.py` on the same shared modules — `uo/cast.py`,
`uo/target.py`, `uo/mana.py`, `uo/meditate.py`, `uo/stages.py` — so *How a cast is read*, *The self
cursor* and *The mana wait* over there describe this one too. Only the table, the cursor kinds and
the health floor are its own.

| Band | Spell | Mana | Cursor | What it is |
| --- | --- | --- | --- | --- |
| ≤ 40.0 | Nether Bolt | 4 | none answered | The cheapest thing in the book |
| 40.0 – 63.0 | Stone Form | 11 | at self, beneficial | A **toggle**. Every other cast takes it back off |
| 63.0 – 80.0 | Cleansing Winds | 20 | at self, beneficial | A heal and cure, centred on the target |
| 80.0 – 95.0 | Hail Storm | 40 | at self, **harmful** | An **area attack**, centred on you |
| 95.0 – 120.0 | Nether Cyclone | 50 | at self, **harmful** | An **area drain**, centred on you |

The four bands from 40.0 up are the training table as the guides give it. Nether Bolt below them is
this script's own addition, so a character who has not bought the skill yet still has something to
cast — but a trainer sells the first thirty points faster than this loop grinds them, and the
start-up line says so.

**Nether Bolt answers no cursor.** The mana goes and the skill is rolled as the incantation ends, so
the cursor it raises is simply left for the next cycle's guarded cancel to take down. That is the
same shape the last two bands fall back to if a harmful self-target turns out not to be allowed here
— see *Known unverified*.

| Outcome | What happens |
| --- | --- |
| `cast` | Tallied, and the fault counters cleared |
| `fizzled` | Counted, not tallied. Ordinary, and commoner the further a band is above the skill |
| `alreadyCasting` | Waits `CASTING_WAIT`, flat. **Never** counted towards a stop |
| `alreadyUp` | Waits `BUFF_WAIT`. Only reached with `SKIP_WHEN_BUFFED` on, or a refusal in words |
| `disabled` | Tallied — this is Stone Form toggling off, and the shard charged for that cast |
| `formLocked` | **Stops.** Every band above Stone Form is unreachable while the form is up, and nothing here drops it |
| `noMana` | Says the row's `mana` is understated, then gathers mana |
| `noReagents` | **Stops.** Nothing waited for refills a pouch |
| `unskilled` | **Stops** — the table is aimed at a skill this character cannot use |
| `saving` | Sits the world save out and resets the counters |
| `throttled` | Backs off, growing, `MAX_THROTTLED` in a row ends the run |
| anything else | Unreadable — said once per stretch and carried on with. It ends nothing on its own |

`MAX_STALE` cycles with no cast **and** no movement in the skill is the only ending left for a run
that is getting nowhere, and it cannot fire while the skill is still moving. A dry mana stretch is
charged what it cost in cycles rather than one.

### Stone Form is a toggle

`SKIP_WHEN_BUFFED` is off, so the row casts every cycle: on, off, on. Each of those is a cast the
shard charged mana for and rolled the skill on, which is why `DISABLED_IS_PROGRESS` is on and the
`disabled` bucket is tallied rather than warned about. The buff transition only proves the casts that
turn it **on** — the ones that turn it off are proved by the mana instead, which is the ordinary
silent proof and needs no wording.

### The health floor

The last two bands are harmful spells centred on the caster, and **nothing in this script heals**.
`HURT_FLOOR` stops the run at half health rather than watching it die. On a shard that excludes the
caster from their own area spell — which is the assumption the table is built on — it never fires,
and what trips it is something that wandered up.

### Before you run it

- **Stand somewhere empty, and never in town.** The top two bands are area attacks for forty skill
  points. In town that is the guards, and near anything blue it is a criminal flag. The script does
  not move, fight or heal.
- **Carry a Mysticism spellbook**, and the reagents for it — the standard eight plus Dragon's Blood,
  Fertile Dirt, Daemon Bone and Bone — or wear a 100% Lower Reagent Cost suit. Running out ends the
  run by name.
- **Empty your hands.** Meditation is refused while anything is held, and this run will not put it
  away for you.
- **Focus or Imbuing sets the damage, not the gain.** Neither is needed for this to train.
- **Below about 30.0, buy the skill from an NPC trainer first.**
- It aims at **120.0**, which needs the power scrolls. The run stops at whatever the shard caps the
  skill at, and the start-up line says so when that is lower.

### What to set

The config block is the top of `mysticism.py`. **Every timing is in seconds.** Everything below
`STAGES` is `magery.py`'s *What to set* block with the same defaults and the same meanings; only
these are this script's own.

| Setting | Default | What it is for |
| --- | --- | --- |
| `STAGES` | five rows | One row per band: cast `spell` until the skill reaches `up_to`, at `mana` a cast |
| `STAGES[].up_to` | — | The skill value the row trains to, exclusive. A float — `63.0`, not the web client's tenths |
| `STAGES[].target` | `self` on four | Answers the row's own cursor. Nether Bolt does not |
| `STAGES[].target_kind` | `harmful` on two | The cursor type the shard raises. Defaults to `beneficial`; the area rows say otherwise |
| `STAGES[].buff` | Stone Form only | A `BuffIconType` member name, matched against `str(buff.Type)`. The other four train on the mana proof |
| `STAGES[].cast_timeout` | 3.0 – 5.0 | **The one worth tuning.** Below the spell's real cast time every success reads as unreadable |
| `STAGES[].cast_delay` | 0.3 – 0.6 | The whole of the pause between two casts |
| `FIRST_BAND` | `40.0` | Where the guides' table starts. Under it the start-up line points at the trainer |
| `HURT_FLOOR` | `0.5` | The fraction of max hits the run stops below. Magery has none; the area bands here earn it |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each attempt is appended, one JSON object per line. `""` records nothing |

### When it goes wrong

**`a form is blocking ...`** — this shard will not let Stone Form and the rest of the book coexist,
so the bands above 63.0 cannot be reached with the form up. Drop it and start again. If it turns out
this shard never does that, the `formLocked` wordings are the guess to delete.

**`the cursor would not take a self target`** on the Hail Storm or Nether Cyclone band — the harmful
self-target is the guess. Delete `"target"` and `"target_kind"` from those two rows; they then behave
like Nether Bolt, where the mana proves the cast and the next cycle cancels the standing cursor.

**`outcome unreadable - carrying on`** — usually the row's `cast_timeout`, not the wordings. See `magery.py`'s
*When it goes wrong*, which had exactly this on its first live run.

**`buff bar:` prints an id this table does not use** — copy the `Type` you see into Stone Form's
`buff`. Until then the `title` fallback and the mana proof carry that row.

**`hurt (N/M)`** — something is hitting you, or this shard does include the caster in their own area
spell. If it is the latter, the top two bands want a different plan.

**`refused for mana at N`** — the row's `mana` is lower than the shard actually charges. Raise it.

### Known unverified

- **`"StoneForm"` as the `BuffIconType` name.** Read from the enum, not off a live run. The first
  `mystic: buff bar: ...` line is what confirms it; the `title` fallback and the mana proof cover it
  either way.
- **A harmful self-target.** The guides all say to target yourself with Hail Storm and Nether
  Cyclone, but whether the shard raises that cursor as `harmful` and then accepts the caster as its
  own target is not something this was measured against. `legion/probe-target.py` is the diagnostic
  if it needs settling.
- **Whether the caster takes their own area damage.** The table assumes not. `HURT_FLOOR` is what
  catches it if the assumption is wrong.
- **Every phrase in `OUTCOME_TEXT`**, including the `formLocked` bucket, which no live run has
  produced. RunUO-family guesses; a miss shows up as an unread outcome rather than a wrong turn.
- **The band bounds and the mana figures.** The bounds are the guides' table as given; the mana is
  the standard Mysticism cost ladder. A band that stops gaining before its `up_to` wants the bound
  moved down, and `refused for mana at N` is what a wrong cost looks like.
- **The `cast_timeout` figures.** Scaled from the 1.8s a 3rd-circle Magery cast was measured at on
  this shard, not measured for these spells.

## bowcraft.py

Trains **Bowcraft/Fletching** from 30 to its cap by making whatever the current band still gains on.
It pulls wood 300 at a time out of what you point at — **logs and boards both**, counted as one
pool, because the menu crafts from either and the lumberjack run brings boards home — and unloads to
the nearest bowyer every `SELL_AT` items so the pack never becomes the reason it stops. It is the
only script here that drives a crafting gump.

**What you can point at is a chest or a pack animal.** A target that resolves as an item is a
container, remembered by the spot it was standing in; one that resolves as a creature is a pack
animal, and what is read and pulled from is the backpack it wears, re-resolved every time because a
pet walks. Your own pack never needs picking — it is where the wood is counted from — and neither
does anything at all: press ESC at the cursor and the run works through the wood you are carrying.

The band table, from the shard's own gain rates:

| Bowcraft | Makes |
| --- | --- |
| 30 – 60 | `LOW_BAND_ITEM` — a bow by default, fukiya darts the other way |
| 60 – 70 | crossbow |
| 70 – 80 | composite bow |
| 80 – 90 | heavy crossbow |
| 90 – cap | `HIGH_BAND_ITEM` — a repeating crossbow by default, a yumi the other way |

The first row whose ceiling the value is under wins, so the ceilings are exclusive and the bands butt
together. `API.GetSkill().Value` is a float percentage here — the `src/training/` tables are in the
client's tenths and would be wrong by 10x if they were copied over.

Each cycle:

1. **Read the skill.** A band it does not cover ends the run; a band change re-selects the row.
2. **Sell** once the pack holds `SELL_AT` products, and for no other reason. It stays where the sale
   left it rather than walking back. A trip that buys nothing does not own the cycle — the crafting
   below still gets its turn.
3. **Restock** if the pack is under `RESTOCK_AT` wood, walking to a container that is out of reach. A
   pack too short to restock but long enough to make something crafts instead of waiting. **The pack
   is read first**: wood sitting in a bag inside it is brought up before anything is fetched, since
   the craft may not reach into a bag. The pack is then filled to `BATCH_SIZE`. Weight is never a
   reason to stop short or end the run: when the shard refuses a move as too heavy and the pack
   holds anything to sell, the run sells first and loads on the next cycle. With nothing to sell it
   crafts down what it has.
4. **Open the craft menu** by using the fletcher's tools, if one is not already up.
5. **Press the row**, or `MAKE LAST` once the row is known.
6. **Read the outcome** out of the journal, the gump's `NOTICES` panel **and the pack**, all three on
   every pass. The pack is not checked last: a success whose wording this table does not carry is
   still a success, and waiting out `CRAFT_TIMEOUT` for a line that was never coming is a silent
   ten-second stall on a craft that worked.

When something cannot be read or cannot be acted on — an unreadable outcome, a refusal for materials
— the run prints **the gump's own text, the journal's last lines, and the wood in the pack by hue**,
twice per stretch. A refusal nobody can read is the one thing a log cannot be fixed from.

### Wood is not one resource

`1580 Boards` and `74 Oak Boards` are two different resources to the craft menu, and **it spends only
the one it is set to** — a pack full of oak is a pack full of nothing to a menu set to regular. So
`WOOD_TYPE` decides everything the run does with wood: what a restock pulls, what counts as stock,
and what is only weight.

The type is read off the **name** first — that is where the shard writes it, `Oak Boards` against a
plain `Boards` — and off the **hue** when the tooltip has not arrived yet:

| Wood | Hue |
| --- | --- |
| regular | `0` |
| ash | `1191` |
| oak | `2010` |

That table is incomplete, and deliberately so: a colour in neither table is *not* treated as regular,
it is reported as `unknown` with its hue in the `the pack holds …` line, which is where the missing
rows come from. Add them to `WOOD_HUES` as you meet them.

Wood of another type is **put back** into the container or animal it came from, at the moment that
one is open and in reach, so it costs no walking and takes its weight off you. Set
`RETURN_WRONG_WOOD` to `False` to leave it in the pack instead. Everywhere the pack is reported you
see both halves: `4 boards (300 oak set aside) in the pack`.

To work oak instead, set `WOOD_TYPE = "oak"` **and** set the menu's material to oak by hand.

### A vendor that will not buy

`MAX_SELL_MISSES` trips in a row that bought nothing pause the trips for `SELL_RETRY_AFTER` cycles
rather than ending the run, so it does not walk to the vendor and back on every pass while the
crafting waits.

### Finding the row

The gump numbers its buttons `1 + type + index * 20`: categories are type 0 (**1** Materials, **21**
Ammunition, **41** Weapons), the arrow on a `SELECTIONS` row is type 1 (2, 22, 42, 62, …), and
`MAKE LAST` is **47**. Those numbers are read off this shard's own menu; the stock 7-step numbering
puts `MAKE LAST` on the Ammunition category.

**`RECIPES` names the buttons for the rows this menu is known to carry**, so the common products cost
no searching at all. It is a shortcut, not a source of truth: what proves a craft is still the pack,
and a row the table gets wrong hands that product to the walk below for the rest of the run.

**The category is walked** for anything `RECIPES` does not cover. Pressing one only redraws the
`SELECTIONS` panel, so the run presses each in turn until a page lists the product and remembers
which button that was.

**The row is read, then proved.** `API.GetGumpContents()` is split into lines, everything past the
last category name is taken as this page's rows, and the row whose text equals the product name gives
the index. That is a guess about the order the client emits its labels in, so it is only the first
candidate: what settles it is the pack. A craft that added none of the product's graphics landed on
the wrong row, and the next candidate is tried — at most `MAX_ITEM_PROBES` of them, then the category
itself is written off and another one is tried.

Both matches are whole-row, never substrings: `crossbow` is inside `crossbow bolt`, and a substring
match finds the crossbow in **Ammunition** and never reaches **Weapons** at all.

Once a row has made the right item, every craft after it is `MAKE LAST`. A band change, a worn out
tool, or a row that produced the wrong graphic sends it back through the categories. A `MAKE LAST`
that produced the wrong graphic only presses the proven row again: the shard forgot, the row did not
move.

### Waiting for the menu

`API.HasGump()` answers the gump's **`ServerSerial`** — its *type* id, which every page of one craft
menu shares — and `API.ReplyGump()` **disposes** the gump it answers before the shard sends the next
page. So the wait after a button is *"is the menu back"*, never *"is the id different"*: the id is
the same for the main page, every category page and the page that comes back after a craft.

That also means a stray server gump has to be closed before the tools are used, since "a gump is
there" would otherwise be answered by the wrong one.

### Recognising the menu

**Whatever the tools open is the menu.** The title is a cliloc the client resolves, and
`GetGumpContents` on some builds answers nothing for it, so the title only *recognises* a gump that is
already up. A gump the tools opened is used either way, and one that does not name itself is reported
once with its first line.

### Outcomes

| Outcome | What it means |
| --- | --- |
| `made` | The pack gained one of the product's graphics. This is the only proof that counts |
| `failed` | The shard says the craft failed. Still a gain and still spends the wood, so the loop counts it as progress |
| `noMaterial` | *You do not have sufficient wood* — restocks on the next cycle. `MAX_NO_MATERIAL` of them with wood still in the pack ends the run naming what is in there, which is what a shard that crafts from only one of logs and boards looks like from in here |
| `wrongRow` | It made something, and none of it was the product. Moves to the next candidate row |
| `toolWorn` | The tools broke. Looks for another pair and re-selects the row |
| `skillTooLow` | Ends the run: the band table and the shard disagree about what is craftable |
| `noRow` | Ends the run: no row in any category made the product |
| `noTool` | No fletcher's tools in the pack. Retried `MAX_NO_TOOL` times before it ends the run |
| `noGump` | The tools opened no craft menu. Retried the same way, and said with its own wording so the two are never one message |
| `throttled` | *You must wait* — backs off further each time, capped at `THROTTLE_BACKOFF_MAX` |
| `saving` | A world save, sat out rather than read as a failure |

### What a craft spent

`made` and `failed` are the two outcomes that reach `DATA_PATH`, and they are the only ones here
that carry `consumed` rows. What went is **measured**, by counting the pack either side of the craft
— never read off `RECIPES`, which is what the *menu* is told a recipe costs rather than what this
shard charged.

Only whitelisted stacks are counted: everything `WOOD_KINDS` knows, including the arts `WoodBook`
learns by name as the run goes, plus `MATERIAL_GRAPHICS`. Anything else that shrank mid-craft — a
potion drunk — is not a material. Only the *lost* side of the diff is taken: the product lands in the
same pack, and a product is not a cost. A failed craft is read once the pack has moved and then held
still for a poll, or after `REFUND_SETTLE`, because the shard's refund lands after its failure line.

A craft that spent nothing writes an attempt row and no consumed rows, which is the truthful answer
rather than a missing one. The pack is only counted at all when `DATA_PATH` is set.

### Before you run it

- **Bowcraft has to be at `MIN_SKILL` or above.** Below it the run refuses to start rather than
  grinding a band the table does not cover.
- **It stops at the shard's cap.** A character already there is refused before the cursor, and a
  run that reaches it mid-way ends by name. The start-up line shows the cap it is training toward.
- **Fletcher's tools in your pack**, and spares if you want the run to outlast one pair.
- **What you pick has to be reachable.** A container is opened and its position recorded when you
  click it, and the run pathfinds back to that spot; a pack animal is pathfound to by serial, so it
  can wander. Either one it cannot reach is skipped for that restock, not dropped.
- **Never picked is fine.** With nothing picked the run crafts down the wood in your pack and stops
  when it runs out. It only refuses to start when the pack is empty *and* nothing was picked.
- **The bowyer is found by tooltip as well as by name.** A shopkeeper is named *Alger* and titled
*the bowyer*, and only the tooltip carries the title — matching the name alone reported *no bowyer
within 18* while standing next to one. The name pass runs first because it is free; the tooltips are
requested only when that finds nothing. Set `VENDOR_SERIAL` to skip the search entirely.

**It sells from next to the vendor, through the vendor's own menu.** The run walks to
`VENDOR_RANGE` — 1, adjacent — and re-asks where the vendor is after each walk, because a pathfind
that ends early leaves you standing short and nothing else would notice. Then it sends the context
menu's **Sell** entry, matched by its text so no index is guessed, falling back to saying
`vendor sell` for a menu with no such entry. Either way it waits for the pack to drop; it does not
drive the sell gump itself, so **the auto-sell agent still has to be configured** for the bowyer.
- **`SELL_AT` counts amounts, not stacks.** Fukiya darts stack ten to a craft, so 20 is two crafts
  — raise it if you run the darts band.

### What to set

| Setting | Default | What it is for |
| --- | --- | --- |
| `SKILL_NAMES` | `Bowcraft`, … | Tried in order; the first the client answers to is the one used |
| `MIN_SKILL` | `30.0` | Below this the run refuses to start |
| `LOW_BAND_ITEM` / `HIGH_BAND_ITEM` | `bow` / `repeating crossbow` | The two bands that offer a choice |
| `BANDS` | see above | Ceiling and product, first row the value is under wins |
| `PRODUCTS` | table | Row name as the gump spells it, and the graphics it arrives as |
| `CATEGORY_NAMES` | `materials`, … | Only used to find where the group rows end and the item rows begin |
| `TOOL_GRAPHICS` / `TOOL_NAME_WORDS` | `0x1022` | Fletcher's tools. An art learned by name joins the set |
| `LOG_GRAPHICS` / `BOARD_GRAPHICS` | four arts each | A stack's graphic changes with its size, so each is a set. An art learned by name joins its kind |
| `WOOD_KINDS` | logs, boards | What counts as material. Counted as one pool, reported apart |
| `WOOD_TYPE` | `regular` | The wood the menu is set to. The only wood that is pulled or counted |
| `WOOD_TYPES` / `WOOD_HUES` | oak, ash, … / `0`, `1191`, `2010` | How a wood is named and hued. Incomplete — the log names what is missing |
| `RETURN_WRONG_WOOD` | `True` | Puts wood of another type back where it came from rather than carrying it |
| `MATERIAL_GRAPHICS` | feathers, shafts | What a craft can spend that is not wood, for the consumed rows. A graphic that is not in here is simply not measured |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each craft is appended, with what it spent. `""` records nothing |
| `BATCH_SIZE` / `RESTOCK_AT` | `300` / `25` | What a restock fills the pack to, and what triggers one |
| `SELL_AT` | `20` | Products in the pack before a sell trip |
| `TOO_HEAVY_TEXT` | *That container cannot hold more weight* | The shard refusing a move for weight. A refusal with products in the pack is the other thing that triggers a sell trip |
| `BOWYER_TITLES` / `SELL_PHRASE` | `bowyer`, … / `vendor sell` | Matched against the name **and** the tooltip, and what is said to it |
| `VENDOR_SERIAL` | `None` | Set it to a vendor's serial to skip the search |
| `VENDOR_SCAN_RADIUS` / `VENDOR_RANGE` | `18` / `1` | How far it looks for a bowyer, and how close it stands — adjacent |
| `SELL_ENTRY` / `VENDOR_STEPS` | `sell` / `3` | The context menu entry, matched by text, and the walks it spends getting there |
| `MAX_PICKS` | `8` | A backstop only — the selection ends when you press ESC |
| `CONTAINER_RANGE` | `2` | How close the run stands to a container or a pack animal before it pulls |
| `CRAFT_TITLE` | `BOWCRAFT AND FLETCHING` | Recognises a gump that is already open. Never refuses one |
| `BUTTON_STRIDE` | `20` | The gap between buttons. Change it and every derived button moves |
| `MAKE_LAST_BUTTON` | `47` | The one button that is not derived |
| `RECIPES` | table | `(category button, row button)` for the known rows, so they cost no probing |
| `MAX_CATEGORIES` / `MAX_ITEM_ROWS` | `6` / `12` | How far the walk goes for anything not in `RECIPES` |
| `MAX_ITEM_PROBES` | `8` | Crafts spent finding the row before the category is written off |
| `CRAFT_TIMEOUT` / `CRAFT_SETTLE` | `10.0` / `1.5` | How long the shard has to answer, and the pack to show it |
| `MAX_SELL_MISSES` / `SELL_RETRY_AFTER` | `3` / `25` | Trips that bought nothing before the run stops trying, and the cycles it waits before asking again. Neither ends the run |
| `MIN_CRAFT_WOOD` | `10` | The largest recipe in `BANDS`. Under this there is nothing to make, which is the only thing that makes a short pack worth a cycle of its own |
| `MAX_NO_MATERIAL` | `3` | Refusals for material in a row, with wood still in the pack, before the run ends |

### When it goes wrong

**`the gump text does not name 'crossbow' on a row of its own, walking the rows`** followed by
**`rows seen: …`** — the line split did not find the item rows. The run still works, it just pays
crafts to find the row. Read what it saw: if the names are there but spelled differently, correct the
key in `PRODUCTS`; if the block is the group names instead, this shard emits its labels the other way
round from stock.

**`no category lists 'yumi'`** — the name in `PRODUCTS` is not what the `SELECTIONS` row says, or the
item is not in this shard's Bowcraft menu at all. Open the menu by hand and read the row.

**`could not find the SELECTIONS row for 'repeating crossbow'`** — every category was walked and no
row made it. Same cause, and the same fix.

**`the tools opened a gump that does not name BOWCRAFT AND FLETCHING - it starts '…'`** — said once,
and not an error: the run uses the gump anyway. Read the line to check the tools really did open the
craft menu and not something else. `(no text)` means the client answers nothing for the gump's text,
which is ordinary for a cliloc header.

**`the button table is out of date for 'crossbow', walking the categories for it instead`** — the
`RECIPES` button made something else, so this shard's menu has moved that row. The run corrects
itself by walking; fix the entry to save it the crafts.

**`unreadable outcome (n/5), check OUTCOME_TEXT`** — the shard's wordings are not the ones in the
table. A success does not need one, because the pack diff proves it; a refusal does.

**`refused for materials - the gump says '…'`**, followed by the journal and
**`the pack holds 300 boards hue 0x7d1`** — the shard will not spend the wood you are carrying. Read
the hue: `0x0` is plain wood, anything else is oak, ash, yew or heartwood, and **the menu spends only
the wood type it is set to**. That is the usual cause of a refusal over a full pack. Set the menu's
material by hand once, or carry the wood it is asking for. If instead the hues are `0x0` and it still
refuses, the gump's own words in that line say what it actually wants.

**`could not get next to 'Alger', trying again next time`** — three walks did not put the run
adjacent to the vendor. A door, a counter or a crowd; it keeps crafting and tries again rather than
selling from too far away, which is what silently sold nothing before.

**`the vendor bought nothing - is the auto-sell agent on?`** — the run said `vendor sell` and the
pack did not move. Not an ending: `MAX_SELL_MISSES` of them in a row pause the trips for
`SELL_RETRY_AFTER` cycles and the run keeps crafting.

**`out of wood`** — what you picked is empty and the pack is under `MIN_CRAFT_WOOD`. It counts what is in them at startup, so the opening
line tells you how long that will last. A container it cannot reach also pulls nothing, and that
does not end the run here: it shows up as `restocking` cycles and the stall watch ends them.

### Notes on the API

- **`API.HasGump()` answers the gump id, not a bool**, and a new gump is the id *changing* against a
  snapshot. `API.WaitForGump()` with no id cannot do this job for the reason `tame.py` gives.
- **`API.ReplyGump(button, gump)` and `API.GumpContains(text, gump)` both take the gump id second.**
- **`API.CloseGump()` with no id closes the last gump**, which is as likely to be the craft menu as
  the one you meant, so the sell trip names the id it is closing.
- **The shard answers a craft in the gump's `NOTICES` panel, not only the journal**, which is why
  `read_outcome` polls both. Reading the journal alone spends `CRAFT_TIMEOUT` on every refusal.
- **Moves are asynchronous**, so a restock re-counts the pack between them rather than trusting
  `API.MoveItem`'s return.

### Known unverified

- **Whether the item rows really are everything past the last category name.** That is stock RunUO's
  control order. The pack diff is what covers it being wrong.
- **Whether a row index is per-page or absolute** once the list pages. Nothing here pages, so a
  product that is not on the first page of its category is found by probing rather than by paging —
  and the button that pages is not known.
- **Whether `API.GetGumpContents` resolves the shard's localized row names** or hands back the raw
  cliloc numbers. If it is the latter, every run walks the rows.
- **Whether `API.RequestTarget` returning falsy is ESC** rather than a timeout, which is what ends the
  container multi-pick.
- **The product graphics.** They are the stock arts; a shard that reskins one makes every craft of it
  read as `wrongRow`.

## bod.py

Fills one **small** Blacksmithing bulk order deed. Target the deed; the run reads what it asks
for off the tooltip, crafts it from the ingots in your pack, puts each piece the deed will take
into it through the deed's own gump, and stops when the count reaches the total. Large deeds are
refused at the cursor. Nothing is restocked and nothing is thrown away: what the deed will not
take stays in the pack.

The request is read from the deed's tooltip: `amount to make`, the `<item>: <done>` line, `All
items must be exceptional`, and `All items must be made with <material> ingots`. A deed that
names no material is an iron deed, and the menu is set to iron for it.

Each cycle:

1. **Check the stop conditions** — dead, or stopped from the Script Manager. Sit out a world save.
2. **Done** when the count reaches the total.
3. **Look for a piece the deed would take** in the top level of the pack. Each item's tooltip is
   read once: the name has to be the deed's item (with the material folded in, `dull copper
   platemail gorget`, or on a line of its own), `exceptional` has to be on it when the deed says
   so. A piece the deed refused is never offered again.
4. **Combine it** if there is one: open the deed, press the combine button, answer the cursor
   with the piece. The piece leaving the pack is the proof; the shard's wording is read as well.
5. **Otherwise craft one**: open the smith menu with the hammer or tongs in the pack, set the
   material once, find the row by name, `MAKE LAST` once the row has proven itself. A new item in
   the pack is the proof, and its tooltip says whether the row was right.

| Outcome | What happens |
| --- | --- |
| `combined` | Counted. The deed is re-read for up to `REREAD_SETTLE` and the larger count wins |
| `full` | The shard says the deed is complete. Ends the run |
| `notRequested`, `notExceptional`, `wrongMaterial` | The piece is left in the pack and never offered again. `wrongMaterial` also re-selects the menu's material |
| `notInPack` | Ends the run: the deed or the piece is not in your backpack |
| `noCursor` | The combine button raised no cursor. `MAX_NO_CURSOR` of them end the run |
| `made`, `failed` | A craft that landed, or one the shard called a failure. Both spend ingots |
| `wrongRow` | The row made something else; the next candidate row is tried |
| `noMaterial` | Ends the run naming the ingots in the pack and the pieces still owed |
| `noAnvil`, `skillTooLow`, `noRow`, `noMaterialRow` | End the run with the reason |
| `toolWorn`, `noTool`, `noGump`, `throttled`, `saving`, unreadable | As `bowcraft.py` |

### Before you run it

- **The deed in your backpack.** The shard refuses a combine from anywhere else.
- **Stand next to an anvil and a forge.** The shard refuses every craft otherwise, and the run
  stops on the first refusal.
- **Ingots of the kind the deed names**, in your pack. The run crafts until the shard refuses for
  materials, then stops: it never restocks, and it does not count the cost first.
- **A smith's hammer or tongs** in your pack. Spares if you want the run to outlast one.
- **Exceptional deeds produce leftovers.** Every non-exceptional piece stays in the pack; smelt
  them yourself. Watch the weight on a plate deed.
- **Large deeds are not handled.** The cursor refuses one and the run stops.

### What to set

| Setting | Default | What it is for |
| --- | --- | --- |
| `SKILL_NAMES` | `Blacksmithy`, `Blacksmith` | For the start-up line only |
| `TOOL_GRAPHICS` / `TOOL_NAME_WORDS` | hammer, tongs, sledge / `tongs`, `smith` | What opens the menu. Whole words, so a war hammer is not a tool |
| `INGOT_GRAPHICS` / `INGOT_HUES` | stock | For the `in the pack` line. A hue not in the table is reported as a hue |
| `PLAIN_MATERIAL` | `iron` | What a deed with no material line wants |
| `MATERIAL_ALIASES` | `shadow iron` → `shadow` | How the menu row and the item tooltip may shorten the deed's wording |
| `DEED_TEXT` | stock | The tooltip lines, lower-cased fragments |
| `CATEGORY_NAMES` | both spellings | Where the group rows end and the item rows begin |
| `BUTTON_STRIDE`, `*_BUTTON_TYPE`, `MAKE_LAST_BUTTON` | 20, 0/1/5/6, 47 | The menu's numbering. The material page is `1 + 6`, its rows `1 + 5 + i * 20` |
| `BOD_COMBINE_BUTTON` | `2` | The deed gump's *Combine this deed with the item requested* |
| `MAX_ITEM_PROBES` | `4` | Crafts spent finding the row. Each miss costs one item's worth of ingots |
| `OPL_TIMEOUT` / `OPL_ASKS` | `2` / `3` | How long a tooltip has to arrive, and how many times one item is asked |
| `REREAD_SETTLE` | `3.0` | How long the deed's tooltip has to show a combine the pack already proved |
| `MAX_NO_CURSOR` | `3` | Combine presses that raised no cursor before the run stops |
| `OUTCOME_TEXT` / `COMBINE_TEXT` | stock ServUO | The shard's wordings for a craft and for a combine |

### When it goes wrong

**`is not a deed this run can fill: could not read it - the tooltip says '…'`** — the lines are
not the stock ones. Read what it printed and correct `DEED_TEXT`. An empty tooltip means it had
not arrived: run it again.

**`no material row reads 'valorite' - rows seen: …`** — the material page names it differently,
or the character lacks the skill for it and the shard left it off the page. Add the row's
wording to `MATERIAL_ALIASES`.

**`the deed's gump raised no cursor 3 times`** — button 2 is not the combine on this shard. Open
the deed by hand and count the buttons; set `BOD_COMBINE_BUTTON`.

**`the deed refused 0x… (notRequested)`** on a piece that plainly is the item — the deed wants
another graphic of the same name (a female plate, a gargish piece). The row it found is the
wrong one; the pieces stay in the pack and the run keeps crafting from the same row, so stop it
and read the SELECTIONS rows.

**`the deed's tooltip is behind the count`** — said once, and not an error. The pack proved the
combine; the shard's tooltip had not caught up in `REREAD_SETTLE`.

**`the new item's tooltip did not arrive - taking the craft as the product`** — the row could
not be judged, so it is trusted. A wrong row shows up as `notRequested` at the combine instead.

### Notes on the API

- **`API.ItemNameAndProps` is the whole of the deed.** The BOD gump is only ever opened to press
  combine; nothing is read off it.
- **The material page is the craft menu's own gump**: `HasGump()` answers the same id for it, so
  it is walked with `CraftMenu.press` and read with `CraftMenu.item_rows`, the same as a category.
- **The deed gump is closed before the menu is opened, and the menu before the deed**, because
  `HasGump()` answers one id and the wait after a `UseObject` is for any gump.

### Known unverified

- **The material page's wording and order.** Stock is `IRON`, `DULL COPPER`, `SHADOW IRON`, …
  with the count beside each; a row is matched on its leading words, so the count does not matter.
- **Button 7 for the material page and 6/26/46… for its rows**, derived from the stride the
  bowcraft run measured and stock's type numbering, and **button 2 for the combine**.
- **Whether the deed tooltip re-reads after a combine.** If not, every combine says `behind`
  once and the run trusts the pack, which is the right answer anyway.
- **Whether `RootContainer` reads** on this client. If it is `None` the check is skipped and the
  shard's own refusal ends the run.
- **The `exceptional` line and the folded material name**, stock ServUO wording.
