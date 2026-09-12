# legion — scripts for TazUO

Python scripts for [TazUO](https://tazuo.org)'s Legion Scripting engine. Everything else in this
repo targets the ClassicUO web client; nothing is shared between the two.

| Script | What it does |
| --- | --- |
| `tame.py` | Target one animal, then work through every animal of that type in reach: tame it, rename it, and set it on something |
| `buffs.py` | Watches the buff bar and recasts Consecrate Weapon and Divine Fury as each lapses |
| `mining.py` | Maps the ore around you, plans the stand spots that cover it, walks them in order, swings, consolidates the ore, and smelts it against a fire beetle |
| `mine-here.py` | Stands still and works the spot you are on until it runs dry, then smelts and stops |
| `lumberjack.py` | Chops the nearest tree, turns the logs into boards, and loads the boards onto your pack animals |
| `fishing.py` | Gets off the mount, says `all guard`, casts the fishing pole once at the nearest water and records what came out. Run it again for the next cast |
| `attack.py` | Turns war mode on and attacks the nearest gray or red mobile within 10 tiles that is not your pet or, by its tooltip, anyone else's. Run it again for the next one |
| `arms-lore.py` | Target a weapon, then read it every half second until Arms Lore caps |
| `bowcraft.py` | Trains Bowcraft from 30 to cap: makes whatever the band still gains on, restocks wood from the containers and pack animals you pick, and sells to the nearest bowyer |
| `tinkering.py` | Trains Tinkering from 20 to cap on the iron ingots you carry: makes whatever the band still gains on, and sells it to the vendor that buys it, unloads it or keeps it as a gump at the start decides |
| `carpentry.py` | Trains Carpentry from 0 to cap on the cheapest recipe each band still gains on, restocks wood the way `bowcraft.py` does, and unloads what it made into the container you pick |
| `inscription.py` | Trains Inscription from 30 to cap on the spell scroll with the fewest reagents each circle gains on, meditating when the pool is short, restocking scrolls and reagents the way `carpentry.py` does, and selling or unloading the scrolls as a gump at the start decides |
| `magery.py` | Trains Magery on the four spells that gain without a victim, meditating when the pool runs dry |
| `mysticism.py` | Trains Mysticism on the five spells that gain without a victim, meditating when the pool runs dry |
| `chivalry.py` | Trains Chivalry on its five spells, gating each cast on tithing points, putting the weapon away for every trance and drawing it again after, and bandaging itself under the health floor |
| `bod.py` | Target a Blacksmithing bulk order deed, small or large: crafts what it asks for from the ingots in your pack, combines the pieces, and for a large deed gets the smalls from the Bulk Order Deed Box and fills them one by one |
| `inventory.py` | Target a bag or chest: writes one JSON line per item in it - name, tier, durability, weight and every tooltip property, parsed and verbatim |

## How to run it

1. Drop the file from `legion/dist/` in TazUO's `LegionScripts` folder. Each one is self-contained.
2. Open **Legion Script** from the top menu and run it from the Script Manager.
3. Answer the cursor. `tame.py` wants an animal, and another after each tame; `mining.py` and
   `mine-here.py` want your fire beetle; `lumberjack.py` wants your pack animals, one after another;
   `arms-lore.py` wants the weapon; `bowcraft.py` wants every container or pack animal holding wood,
   or none if you carry it; `carpentry.py` wants the same, then the container to unload into;
   `tinkering.py` draws a gump asking whether what it makes is sold, unloaded or kept, wants the
   unload container if you press Unload, and under Sell wants it once a band nobody buys from is
   ahead; `inscription.py` wants the containers holding scrolls and reagents, then draws the same
   gump and wants the unload container if you press Unload; `bod.py`
   wants the deed; `inventory.py` wants the bag. `magery.py`, `mysticism.py`, `buffs.py`, `fishing.py` and `attack.py` raise none. ESC
   declines, and each script says what it does instead.

## How it is built

Sources are in `legion/src/`; `python3 legion/build.py` inlines each entry and everything it imports
into one file in `legion/dist/`, which is committed. `--watch` rebuilds on change.

```
src/uo/            the shared library, one concept per file
src/<script>/      index.py, config.py, and that script's own decisions
src/test_support/  the fake client the suite runs against
src/skilldb/       host CPython, not a script - see The attempt log
```

`python3 legion/run-tests.py` runs the suite without the game: `test_support/uo.py` is a fake `API`,
installed as a builtin and as `import API`. It is inert, so a test that wants an outcome has to say so.

- Nothing in `src/uo/` imports a script's `config.py`; parameters come in through the call.
- Nothing in `src/uo/` holds mutable module state. `global` binds to the defining module, and a flat
  bundle would hide the difference between the artifact and the module under test.
- The bundle is one flat namespace: two modules defining the same top-level name is a build error,
  as is `import x as y`, `import *`, a non-top-level import, or importing a name the module lacks.
- `import API` at the top of a source file gives the editor autocomplete. The bundler strips it;
  Legion injects the real `API` as a builtin. `-updateapi` in game refreshes the local `API.py` stub.
- Sibling imports are deliberately not used, though `LegionScripts/` is on `sys.path`: the module
  cache means an edited shared module needs a client restart, and a module reached through real
  import machinery cannot carry `import API` without shadowing the builtin with the stub.
- The Script Manager's stop arrives as an exception out of the next `API.Pause`, with two seconds to
  unwind. A catch-all around a loop must re-raise when `API.StopRequested` is set.

**Legion runs IronPython 3.4.2, so the language level is Python 3.4.** No f-strings, variable
annotations, walrus, PEP 448 unpacking or numeric underscores. Use `%` formatting. `py_compile`
proves nothing; `build.py` walks the AST and refuses all of it.

## The shared library

```
alert       a command run on the machine through .NET, so a warning does not depend on the game
buffbar     the buff bar, re-read every time because ApiBuff never refreshes
cast        a spell, and the two silent proofs a shard that says nothing still leaves
choice      a gump the script draws with one button per option, answered by the first press
clock       the one time.time(), so tests have one thing to fake
components  what one craft takes of each kind, and what the pack is short of
convert     resource -> product, judged by the pack diff, with a per-hue write-off
cost        what one craft of a product takes, and how short the pack is of it
craft       one craft through the menu: the row, MAKE LAST, and the outcome read three ways
craftmenu   a craft gump: opening it, walking the categories, reading and pressing the rows
crafttool   the tool a craft menu is opened with, found in the pack by art or by name
dump        the container the products are unloaded into, and moving them there
entity      hex, the guarded player read, Chebyshev, find-a-mobile
gathered    what a swing and a conversion put in the pack, as attempt rows, below the cap
gear        what is in either hand
hands       what the hands held at start-up, put in the pack for a trance and drawn again by serial
heal        bandaging the character it runs on, proved by the hits rising
guards      the stop conditions, composed per script
gump        waiting for a gump, and reading what it says
heartbeat   'still here', on the clock rather than per cycle
hold        standing still behind a gump the script drew, until its button is pressed
journal     the phrase table, the reverse lookup off it, and the tail of what was said
log         the script's own prefix
loop        the throttle backoff and the stall watchdog
mana        the pool, watched in slices so the guards get a look in
materials   what a craft spent, measured either side of it
meditate    filling the pool, and retiring the skill when the shard refuses it
menu        a context menu entry, matched by its text
mount       getting off the mount, proved by the flag
notoriety   the values the threat scans are handed
pace        the shard's skill timer, learned from its refusals rather than configured
pack        counting and diffing what the backpack holds
phrases     the shard's own wordings, as far as they do not depend on the script
record      one line per attempt, written at the next attempt or at the close so the gain it earned is in it
restock     filling the pack from the picked containers, and putting the wrong wood back
retry       act, poll for the proof
roam        walking to the next spot, and waiting where there is nothing but a clock
save        sitting out a world save
scan        the crow-flight sort, the route probe, and the shortest way in
skill       every read of GetSkill, and what a client that has not answered means
sources     the containers and pack animals picked at the cursor, and reaching them again
stages      the band tables: which row trains now, and what one of its cycles costs
stock       the craft's material in the pack: which kind, which type, and what the menu will spend
survey      the dead-end report: what the run actually saw
target      answering a self cursor the pre-target did not take
terrain     the land and statics cache, one pair of calls per coordinate for the run
threat      noticing trouble and sounding the ambush alarm, without ending the run over it
tiles       what is worked out, unreachable, or not the resource at all
timings     the constants the scripts agreed on
tool        find it, learn its graphic, equip it, notice it break
tooltip     an item's property lines, read into numbers, ranges, flags and text
travel      chasing a mobile, and following one between the slices of a wait
vendor      finding the one who buys, walking up, and selling through the context menu
vitals      position, weight and mana, as one phrase
weight      the one place WeightMax is read
```

## Notes on the API

What the typings do not say, learned on UOAlive. Script-specific notes sit under each script.

- **`API.Pause` takes seconds.** A stray millisecond value is a multi-minute freeze. `PATHFIND_TIMEOUT`
  is the exception: its API takes a whole-second int.
- **There is no blocking journal wait.** `InJournalAny` answers yes/no, so `OUTCOME_TEXT` is polled
  bucket by bucket in declaration order. Order is load-bearing: `saving` and `throttled` sit last
  because `THROTTLED_TEXT` ends in a bare `You must wait` that longer sentences contain.
- **`API.ClearJournal` takes a filter.** Each action clears only the lines it is about to wait on; a
  wholesale clear wiped the ambush warning before the threat watch saw it.
- **`Skill.Value` is a float** (`74.6`, not the web client's `746`) and reads `0.0` until the skill
  list arrives, which is also a real value. The reader reports `unknown` rather than coercing.
- **`HitsMax`, `FollowersMax`, `WeightMax` and `ManaMax` read 0** before the client is told. Every
  guard checks for a positive ceiling first; a live mining run ended at 436/453 on this.
- **`API.CastSpell` matches partially** ("Fireba" casts Fireball), so tables carry full names.
- **`API.PreTarget` only fires on a matching cursor type.** A spell cursor reports as `beneficial`;
  with the stub's default `neutral` it silently never fires.
- **`API.HasTarget()` reports a server-raised spell cursor**, as both `any` and `beneficial`. The
  cursor cancel is guarded on it: an unconditional cancel left the next cursor unusable.
- **`API.Target` is overloaded by arity.** `Target(serial)` answers with an item,
  `Target(x, y, z, graphic)` with a location; the graphic defaults to `1337`, the land tile. Handing
  it the wrong shape throws.
- **`API.ActiveBuffs()` objects never refresh**, so the bar is re-read whenever the answer matters.
  `API.BuffExists(name)` substring-matches the localized title, so `str(buff.Type)` is matched
  instead. `ApiBuff.Timer` is a client-tick deadline with no exposed clock, so there is no
  time-remaining.
- **`API.HasGump()` answers the type id of the *last* gump the shard sent**, not a bool, and every
  page of one craft menu shares it. Any gump the shard re-sends on its own (UOAlive has one whose
  text is chat lines) takes that slot, so nothing waits on "any gump". `WaitForGump(id, secs)`,
  `GumpContains(text, id)`, `GetGumpContents(id)`, `ReplyGump(button, id)` and `CloseGump(id)` address
  a gump by id whichever was last; `GetAllGumps()` lists the open ones and `GetGump(id).Children`
  carries each button's `ButtonID`. `ReplyGump` disposes the gump before the next page arrives.
- **A reply naming a button the gump does not have disconnects you.** ServUO's
  `DisplayGumpResponse` drops the socket for it ("Connection lost: Socket Error"); button 0 is
  always taken. Every press goes through `CraftMenu.reply`, which sends only to the menu's own id
  and only a button read off it, and a gump whose buttons cannot be read is pressed as before.
- **A script can draw its own gump**, through `API.Gumps`: `CreateGump(mouse, movable, keepOpen)`,
  filled with `CreateGumpColorBox`, `CreateGumpLabel` and `CreateSimpleButton`, shown with
  `AddGump`. The flat `API.CreateGump` family still works but prints a deprecation each call.
  `CreateGumpButton`'s default art is the classic APPLY button, with the text drawn behind it. A
  press reaches the script through `Gumps.AddControlOnClick(control, fn)` and only when it calls
  `API.ProcessCallbacks()`, which drains and returns. `gump.IsDisposed` goes true once it is
  closed, and `keepOpen=False` takes it down when the script stops.
- **Once the stop button is pressed every client call answers with nothing** rather than
  throwing: a wait polling a gump or the journal spins until its next `API.Pause`, and a thread
  the interrupt cannot reach is detached after two seconds and left running. A slice loop that
  does anything outside the client - such as starting the alarm process - reads
  `API.StopRequested` first.
- **`API.ContextMenu(serial, text, timeout)` returns the moment a menu without the entry arrives**,
  so an entry that is not there *yet* looks like one that never will be.
- **`API.ItemsInContainer(container, True)` reads the pack recursively.** Item-cap guards and the
  combine count the top level only, because the cap is per container. A bag the client has not
  opened this session reads as empty. Books read as containers too: a shard's own book art goes
  in `NOT_BAG_GRAPHICS` / `NOT_BAG_NAMES` in `uo/tool.py` so the tool search leaves it shut.
- **`API.ItemNameAndProps` returns a flat string**: line 0 is the name, properties are the lines
  under it. A tooltip not yet arrived is empty, not missing.
- **Every call that reads game state is one client frame**, drained once per `Update`, so sweeps
  scale with the FPS cap and "reduce FPS when inactive" slows every wait. Journal reads stay on the
  script thread. A refused `API.GetPath` is a full A* to its node budget.
- **`API.GetTile` gives the land tile and `API.GetStaticsAt` the statics**, numbered separately, so
  bans key `land:231` rather than `231`. `ApiStatic` carries `Name`, `IsTree`, `IsCave` and its own
  coordinates, but extends `ApiGameObject`, so it has no serial.
- **`API.GetAllMobiles` takes a range** and returns sorted by distance. `IsRenamable` is what tells
  your pet from a stranger's.
- **`API.Notoriety` members are passed through, never compared.** The stub lists every one as `= 1`.
- **`API.Player.IsCasting` goes true 0.2s into a cast and falls before the mana leaves the pool.**
- **Moves are asynchronous**, so a restock re-counts the pack rather than trusting `API.MoveItem`.
- **The standard library is on `sys.path`**, but the bundler admits only `API`, `time`, `clr`,
  `System` and `json` outright; `re` stays out.
- **Memory is per-run** unless a script says otherwise. `mining.py` keeps its map and its parked
  tiles in JSON Lines files; bans and permanent write-offs are still re-learned on every start.
  `API.SavePersistentVar` is a SQLite store of strings keyed by name, with no way to list the names,
  so it is deliberately not used for anything bigger than a counter.

**Every phrase in every `OUTCOME_TEXT` is a RunUO-family guess unless a script's notes say it was
measured.** A miss reads as an unread outcome, never a silent wrong turn, but it is not free: an
unread outcome waits out the whole timeout where a matched one is read in a slice. A run that
reports everything as unread is also crawling; fix the wording, not the timeout.

## The attempt log

Thirteen scripts append one JSON line per attempt to `DATA_PATH`; `skilldb.py` turns them into two CSV
tables. A bare filename lands in TazUO's working directory, so set an absolute path. `DATA_PATH = ""`
records nothing. The file is opened and closed per row; a run that cannot write says so once and
carries on.

Only what the shard clearly called a success or a failure is written. Throttles, dry mana, saves and
unread outcomes write nothing; a missing row shows in the closing tally, a guessed one never would.
`chivalry.py` is the exception: a paladin's spell fails without a word, so an attempt it could not
name is written as `unknown` rather than dropped - a file of nothing but `cast` would read as a
paladin who never once failed.

| Script | success | failure | Left out |
| --- | --- | --- | --- |
| `magery.py` | `cast`, and `disabled` where `DISABLED_IS_PROGRESS` | `fizzled` | the mana wait, the buff already standing, everything unread |
| `mysticism.py` | the same | `fizzled` | the same, plus the health floor |
| `chivalry.py` | the same | `fizzled`, and `unknown` for an attempt it could not name | the mana wait, the buff already standing, the health floor, the tithing gate and the weapon moves |
| `tame.py` | `tamed` | `failed` | `pending` |
| `arms-lore.py` | `read` | `missed` | a use that raised no cursor, unread wordings |
| `bowcraft.py` | `made` | `failed` | `noMaterial`, `wrongRow`, a worn tool, the sell trips |
| `tinkering.py` | `made` | `failed` | the same, and the unloading |
| `carpentry.py` | `made` | `failed` | the same, and the unloading |
| `inscription.py` | `made` | `failed` | the same, the mana waits, and the sell trips or unloading |
| `fishing.py` | `caught` | `failed` | no cursor, not biting, out of reach, throttles, unread wordings |
| `mining.py`, `mine-here.py` | `dug`, `smelted` | `failed`, for a swing or a smelt | everything else, and every row once Mining is at its cap |
| `lumberjack.py` | `chopped`, `converted` | `failed`, for a chop or a conversion | everything else, and every row once Lumberjacking is at its cap |

The row is buffered and written when the **next** attempt is recorded, carrying that attempt's
starting value as its `to`, or at the end of the run: the client applies a gain some time after the
shard grants it, so a value read at the outcome is usually still the old one, and one read a cycle
later still misses a gain that lands during a pause. The close runs in a `finally`, so the stop
button, ESC and a throw all write the last row; its `to` is `null` when the client had stopped
answering by then. A row's `from` and `to` are therefore consecutive readings, and a gain that landed
during a pause shows as a row moving more than 0.1. Carrying both values is what lets a scroll of
alacrity's 0.2 to 0.5 jump be told from several ordinary gains.

```json
{"v":1,"id":"0x40012345/1757030000123/17","t":1757030042.500,"char":"Kaldor",
 "serial":"0x40012345","skill":"Magery","used":"Bless","from":74.6,"to":74.7,
 "outcome":"cast",
 "consumed":[{"name":"oak boards","graphic":"0x1bd7","hue":2010,"qty":6}]}
```

`id` is `serial/run-start-ms/sequence`. `used` is what the attempt was made with: the spell, the
item made, the creature, the weapon read. `to` is `null` where the client was not answering.
`consumed` appears only when something was measured, which the crafting scripts do; an
`inscription.py` row carries one entry per kind spent, the blank scroll and each reagent. `gained`
has the same shape and is what `fishing.py` writes: the catch as the pack received it, named off the
journal line. A swing's `gained` is the ore or logs per hue, named off the tooltip's metal or the
pile's own name and measured once the pile has landed and been consolidated; a smelt or board
conversion row carries the ore or logs spent in `consumed` and the ingots or boards per type in
`gained`, and a conversion that spent the resource with nothing made is a `failed` row.

```
python3 legion/skilldb.py convert ~/TazUO/LegionScripts/skill-attempts.jsonl --out legion/data
```

Every file named is merged; rows are recognised by `id`, so re-converting changes nothing, and a
half-written line is reported and skipped. `attempts.csv` is `id, ts, at_utc, character, serial,
skill, used, skill_from, skill_to, gain, outcome`; `consumed.csv` is `id, name, graphic,
hue, quantity`, one row per material. `gain` is rounded to a tenth because `74.7 - 74.6` is not `0.1` in
binary. `src/skilldb/` is host CPython, not in `build.py`'s `ENTRIES`, and lives under `src/` only so
`run-tests.py` finds `convert_test.py`.

## tame.py

Target one creature. That sets the type the run hunts, by body graphic in any colour, and it works
through everything of that type in reach before asking for another. Per cycle:

1. Check the stop conditions: dead, hurt below `HEALTH_FLOOR`, or no follower slots left.
2. Sit out a world save.
3. Check the creature still resolves, and chase it if further than `TAME_RANGE`.
4. Pre-target it, then `UseSkill("Animal Taming")`, so the cursor is answered before it is raised.
5. Wait for the shard to say the attempt started, then for it to resolve, in `TAME_WAIT_SLICE`
   slices with a non-blocking pathfind between them.
6. Pause for the current pace.

A tame is renamed to `PET_NAME` and dealt with per `AFTER_TAME`. The cursor comes back only when
nothing of the type is left. ESC, the stop button, or a cursor timing out after `TARGET_TIMEOUT`
ends the session.

| Outcome | What happens |
| --- | --- |
| `tamed` | Counted, then renamed and dealt with |
| `failed` | The skill check failed, which still rolled the skill. The ordinary cycle |
| `pending` | Started and never resolved. `MAX_PENDING` of them stops the run |
| `angry` | Waits `ANGRY_DELAY` up to `MAX_ANGRY`, then gives up on this animal |
| `contested` | Another tamer has it. Counted up to `MAX_CONTESTED` |
| `tooFar` | Chases it. `MAX_AWAY` chases that gain no ground give up on this animal |
| `throttled` | The shard's own timer. The pace is raised as well as backed off from |
| `saving` | Waits the save out |
| `hopeless`, `notAnimal`, `alreadyTame`, `unskilled` | Gives up on this animal |
| anything else | Counted unreadable and said, never stops the run |

Only the guards, `throttled` and `pending` end the session; everything else ends the animal.

**The hunt** skips anything already finished with (held for the run, or the scan picks the same
unreachable animal straight back up), anything with `IsRenamable` set (a pet), anything named
`PET_NAME` (release hands back the slot but leaves the name), and anything dead or untracked.
`HUNT_RADIUS = 0` asks for every animal.

**The chase** grades each `API.PathfindEntity` as `closed` (reached `TAME_RANGE`), `gained` (closer
than before, buys another cycle) or `stuck`; only `MAX_AWAY` stucks in a row write the animal off.
A chase that never lands an attempt is ended by the stall watch after `STALL_STOP` cycles.

**The pace** is learned, not configured: `TAME_DELAY` is a floor, `PACE_STEP` is added on every
refusal and taken back after `PACE_EASE_AFTER` landed attempts.

| `AFTER_TAME` | What happens |
| --- | --- |
| `kill` | Ordered to attack. The cursor the shard raises is left up for you to click |
| `release` | Let go, so the follower slot comes back |
| `keep` | Stays yours and stays where it is |

- The tame lands in the journal before the handover finishes, and until it does the rename is
  refused and the menu has no Release entry. The run waits for `IsRenamable` up to
  `PET_SETTLE_TIMEOUT`, then goes ahead anyway.
- `API.Rename` returns nothing and a refusal is silent, so the new name is polled for and the packet
  reissued up to `RENAME_ATTEMPTS` times. `PET_NAME = ''` skips it.
- The kill order is given and the script gets out of the way; after `KILL_PICK_TIMEOUT` it says
  `unanswered` and carries on. Keeping the pets fills the slots, and a shard with no room refuses
  every attempt without saying why, hence the guard.
- Release is proved by `IsRenamable` going back to false. The confirm button is worked out: each id
  in `RELEASE_CONFIRM_BUTTONS` gets `RELEASE_ATTEMPTS` goes, the one that worked is logged and
  reused. A menu without the entry before any press is one asked for early, and is retried. An
  unanswerable confirmation is closed, because it is modal on some clients.
- The pre-target is cancelled on every exit path, or an unanswered attempt leaves it armed.

### Before you run it

- The animal must be wild and within your skill. Nothing needs to be in the pack.
- A failed tame, and a released animal, can turn on you. The script does not fight, heal or run; it
  stops at `HEALTH_FLOOR`.
- It pathfinds to the animal, so stand somewhere the path is not a fence.
- With `AFTER_TAME = 'kill'` the run stops for your click after every tame, and the pets stay yours
  until the slots run out.

### What to set

Every timing is in seconds.

| Setting | Default | What it is for |
| --- | --- | --- |
| `PET_NAME` | `'sifinha'` | What each tame is renamed to. Empty skips the rename |
| `AFTER_TAME` | `'kill'` | `kill`, `release` or `keep` |
| `TAME_START_TIMEOUT` | `3.0` | How long the shard has to say the attempt started, or refuse it |
| `TAME_RESOLVE_TIMEOUT` | `15.0` | How long a started attempt has to resolve |
| `TAME_WAIT_SLICE` | `0.5` | Slice of either wait, and so how often the animal is followed |
| `TAME_RANGE` | `2` | Pathfound into before every attempt |
| `CHASE_TIMEOUT` | `10` | How long one blocking pathfind may take |
| `HUNT_RADIUS` | `12` | How far it looks for the next of the type. 0 asks for every animal |
| `TAME_DELAY`, `PACE_STEP`, `PACE_MAX`, `PACE_EASE_AFTER` | `1.5`, `0.4`, `8.0`, `5` | The pace floor, and how it learns the shard's timer |
| `ANGRY_DELAY` / `MAX_ANGRY` | `10.0` / `10` | How long an angry creature is left, and for how many cycles |
| `MAX_AWAY` | `10` | Chases that gain no ground before the animal is written off |
| `MAX_CONTESTED` | `20` | Cycles another tamer may hold it |
| `MAX_PENDING` | `10` | Attempts that start and never resolve before the run stops |
| `MAX_THROTTLED` | `20` | Refusals in a row before the run stops. The pace should get there first |
| `HEALTH_FLOOR` | `0.5` | Fraction of your health at which the run stops |
| `TARGET_TIMEOUT` | `60.0` | How long you have to answer the taming cursor |
| `KILL_MENU_TEXT`, `RELEASE_MENU_TEXT` | `['Kill', 'Attack']`, `['Release']` | Context menu entries, case-insensitive fragments |
| `KILL_CURSOR_TIMEOUT` | `2.0` | How long the shard has to raise the cursor |
| `KILL_PICK_TIMEOUT` / `_POLL` | `60.0` / `0.25` | How long you have to click the victim |
| `RELEASE_CONFIRM_BUTTONS` | `[1, 2, 0]` | Tried in turn until the animal is let go |
| `RELEASE_CONFIRM_TEXT` | fragments | Wordings the confirmation gump is checked against |
| `RELEASE_CONFIRM_TIMEOUT` / `_POLL` | `3.0` / `0.15` | How long the confirmation gump has to arrive |
| `RELEASE_ATTEMPTS` | `3` | Goes each candidate button gets, and early menus tolerated |
| `PET_SETTLE_TIMEOUT` / `_POLL` | `5.0` / `0.25` | How long the shard has to finish making the animal yours |
| `RENAME_ATTEMPTS` | `3` | Times the rename packet is reissued |
| `MENU_RETRY_DELAY` | `0.5` | Between a menu without the entry and asking again |
| `RELEASE_TIMEOUT` / `_POLL` | `3.0` / `0.25` | How long `IsRenamable` has to go back to false |
| `RENAME_TIMEOUT` / `_POLL` | `3.0` / `0.25` | How long the new name has to arrive |
| `OUTCOME_TEXT` | — | The shard's wordings. `tamed` and `failed` are measured |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each attempt is appended. `""` records nothing |

### When it goes wrong

- **`attempts kept starting and never resolving`**: raise `TAME_RESOLVE_TIMEOUT`.
- **`outcome unreadable - carrying on`**: add the wording to `OUTCOME_TEXT`.
- **`shard says wait (n/20), now pacing at Ns`**: intended for the first few cycles. A run that
  never stops means the real delay is above `PACE_MAX`.
- **`could not rename`, `could not order … to kill (noEntry)`, `could not release … (noEntry)`**:
  the entry is worded differently; set `KILL_MENU_TEXT` / `RELEASE_MENU_TEXT`. If preceded by
  `is not showing as yours yet`, raise `PET_SETTLE_TIMEOUT` instead.
- **`could not order … to kill (noCursor)`**: the shard raised no cursor. Another order path, or
  `KILL_CURSOR_TIMEOUT` is short.
- **`no follower slots left`**: stable the pets, or switch to `'release'`.
- **`could not release … (stillPet)`**: every button in `RELEASE_CONFIRM_BUTTONS` failed. Add the
  gump's real yes id.
- **`found no gump to confirm the release with`**: no confirmation on this shard, or raise
  `RELEASE_CONFIRM_TIMEOUT`.
- **`could not get near`**: `MAX_AWAY` chases gained nothing. Something in the way, or it is faster.

### Unverified

- `TAME_RESOLVE_TIMEOUT` is a guess at the ceiling; `MAX_PENDING` makes a wrong one diagnosable.
- Whether `IsRenamable` flips before the attempt returns; if not, the journal carries the run.
- That a released animal keeps its name. If this shard clears it, a `release` run tames the same
  animals round and round; use `'keep'` or a shorter `HUNT_RADIUS`.
- Which confirm button means yes. `the release gump answers to button N` says; pin it.
- Whether `API.PreTarget` beats the server's cursor. If not, attempts read `pending` and the fix is
  `UseSkill` then `WaitForTarget` + `Target`.

## buffs.py

Recasts each entry in `KEEP` as it lapses, Consecrate Weapon and Divine Fury out of the box. Meant to
run alongside a fight: it does not walk, heal, loot or stow, and death is the only stop. Per cycle it
sits out a save, then walks `KEEP` in order: standing, set aside or retired is skipped; needing a
weapon with both hands empty is skipped; short of mana or tithing is skipped and said once per
stretch; otherwise cast, read the journal, pause `CAST_DELAY`. Then `POLL`. Nothing counts cycles
against the run; the heartbeat proves it is alive.

| Outcome | What happens |
| --- | --- |
| `cast` | Counted; the buff is up |
| `fizzled` / `alreadyUp` | Nothing; the next pass tries again |
| `noMana` | Logged: this entry's `mana` is understated |
| `noTithing` | Retired for the run; nothing a script does refills tithing |
| `unskilled` | Retired: refused at this skill or karma |
| `noWeapon` | Set aside for `SET_ASIDE` |
| `cooldown` / `throttled` / `alreadyCasting` | Backed off, growing; `MAX_THROTTLED` in a row ends the run |
| `saving` | Waited out |
| unread | Counted; `MAX_MISSES` in a row sets the entry aside |

**How a cast is read**, in order: snapshot whether the buff stands (return `alreadyUp` if so),
snapshot mana, cancel a live cursor, clear the journal, cast, poll `OUTCOME_TEXT` for `CAST_TIMEOUT`.
A journal wording wins; failing one, the buff transitioning from down to up or mana strictly
decreasing proves the cast. The first pass that sees any buff dumps every `Type`/`Title` pair.

`POLL` is roughly how long a lapsed buff stays down, since there is no time-remaining to recast on.

### Before you run it

- **The buff bar is the whole check.** A shard that publishes no buff for these spells leaves the
  run casting every pass and burning tithing. No `<spell> up` line in the first minute means the id
  is wrong.
- **Tithe first.** Both spells spend tithing points.
- **Consecrate Weapon needs a weapon in hand.** Skipped while both hands are empty.

### What to set

Every timing is in seconds.

| Setting | Default | What it is for |
| --- | --- | --- |
| `KEEP` | Consecrate Weapon, Divine Fury | One row per buff: `spell`, `buff`, `title`, `mana`, `tithing`, `needs_weapon`. `buff` is required, or the run recasts forever |
| `KEEP_UP` | `True` | Off puts the buffs up once and stops |
| `POLL` | `1.0` | Between passes |
| `CAST_DELAY` | `0.6` | Between two casts inside one pass |
| `CAST_TIMEOUT` / `CAST_WAIT_SLICE` | `1.0` / `0.2` | How long the shard has to answer a cast, and how finely that is polled |
| `MAX_MISSES` | `5` | Casts that did nothing, in a row, before an entry is set aside |
| `SET_ASIDE` | `60.0` | How long a refused entry is left alone |
| `MAX_THROTTLED` | `20` | Refusals in a row before the run stops |
| `MAX_CYCLES` | `100000` | The backstop, a day at `POLL` |
| `OUTCOME_TEXT` | guesses | The journal phrases. Correct these first |

### When it goes wrong

- **No `<spell> up` line, ever**: the row's `buff` is not the `BuffIconType` this shard sends, or
  the bar is not published. Read the `buff bar:` dump.
- **`did nothing 5 times - set aside`**: no known wording, no buff, no mana spent. Cast by hand and
  read what the shard says.
- **`costs more than 10 mana here`**: raise that entry's `mana`.
- **`0/10 tithing points`** or **`out of tithing points`**: tithe.
- **`nothing in hand` repeated**: unarmed, or the client is not reporting `onehanded`/`twohanded`.

### Notes

- `API.Player.TithingPoints` exists. Without the gate a character who forgot to tithe loses both
  buffs on the first pass, since `noTithing` retires for the run.
- The `mana` figures are the TypeScript's (10 and 15); the client's Chivalry table says 10 for both,
  and the shard charges less as Chivalry rises. `noMana` corrects the gate upward. Tithing costs are
  read off `SpellsChivalry.cs`, not measured. The tithing phrases are measured; the rest are guesses.

## mining.py

Dismounts, maps the ore around you, plans the stand spots whose 3x3 footprints cover it, walks them
nearest-first, swings, consolidates the ore, and smelts it against a **fire beetle**, a pet that works
as a portable forge. It dismounts because the beetle is usually the ride, and a beetle you sit on
cannot be targeted.

The swing answers the cursor with yourself, so the shard mines where you **stand**; the plan is about
where to stand, and a spot is worked until the shard says its footprint is empty.

**`ORE_TILE_GRAPHICS` ships as a stock RunUO guess** and is the one setting that ends runs when wrong.
A dead end prints every art it saw, hex and decimal, with `MATCHES` beside the accepted ones.

Before the loop: dismount, the beetle cursor, consolidate, and smelt if already over the limit. Per
cycle:

1. Check the stop conditions: dead, or the pack at its item cap.
2. Sit out a world save.
3. Dismount and equip a pickaxe, both every cycle, so a remount or a broken tool costs one cycle.
4. Smelt if the pack is genuinely over the limit.
5. Plan, when there is no spot left: read every tile within `SCAN_RADIUS` and `MINE_Z_RANGE`, pick
   the stand spots whose `MINE_FOOTPRINT` squares cover the most unparked ore (greedy), order them
   nearest-first from where you stand, and print the map. Each spot handed out is probed once with
   `API.GetPath`; one with no route is parked, and past `MAX_PATH_PROBES` in a scan the next goes out
   unprobed. Under `ONLY_CONNECTED_GROUND` every spot is probed, and one whose route steps outside
   the `SCAN_RADIUS` box is parked as off your ground: the client found a way, but round a wall, a
   cliff or up a ramp elsewhere. When nothing on this ground is left, `STOP_WHEN_WORKED_OUT` ends
   the run with the soonest respawn in the reason instead of idling for it.
6. Walk onto it if you are not standing on it (`STAND_RANGE`).
7. Swing, and branch on what the shard says.

| Outcome | What the loop does |
| --- | --- |
| `dug` | Wait for the ore to land, then consolidate to one pile per metal |
| `failed` | *You loosen some rocks but fail to find any useable ore*. A swing that landed, recorded, nothing to wait for |
| `empty`, `nothingNearby` | Park every ore tile in the footprint you stand in for `RESPAWN_DELAY`, drop the spot, and smelt |
| `notOre` | Write the spot off. The graphic is banned only when the footprint holds a single ore art, since the swing named no tile |
| `tooFar` | Write the spot off |
| `notSeen` | Line of sight. Write the spot off |
| `packFull` | Consolidate: forty piles of one become one pile of forty |
| `wornOut` | The next cycle equips a spare |
| `saving` | Sit it out, no counter charged |
| `throttled` | Back off, growing; give up after `MAX_THROTTLED` |
| `noCursor` | No cursor and no explanation. Backed off like a throttle, stops after `MAX_NO_CURSOR` |
| anything else | `MAX_UNKNOWN` in a row ends the run; check `OUTCOME_TEXT` |

Smelting happens when a spot runs dry, since the character is about to walk anyway and the beetle
has been following. The smelt asks whether any pile is worth it before looking for the beetle.

**Reading the map.** `#` is ore, `@` is you, and the spots are numbered `1`-`9` then `a`-`z` in
walking order (`+` past that). One journal line per row, `2 * SCAN_RADIUS + 1` characters wide; the
journal font is not monospaced, so paste the rows into an editor if they do not line up. Ore on the
outer ring of the box is only covered from inside it, and gets its turn after a walk moves the box.

Spots and ore are parked in separate memories: a spot on a cave floor is the same tile as the ore
under it, and a walk that fails writes off the spot for `UNREACHABLE_DELAY` without touching the ore.

**What survives a restart.** Every coordinate the run reads goes to `MAP_PATH`, one JSON line each
(`m` map, `x`, `y`, `l` land `[z, graphic]`, `s` statics `[[z, graphic, name], ...]`), written
after each cycle that read new ground. The next start reads the file whole and says
`map: N coordinate(s) remembered`, so a plan over known ground costs no client reads. Every timed
parking goes to `PARKED_PATH` (`t` tile key, `u` when it is back) as it happens; a start prunes the
expired rows and says `N tile(s) still parked from the last run`. Both files are per map: rows for
another facet are kept but ignored. Delete `MAP_PATH` if the shard changes its ground.
A refused route onto bare land that `API.GetPath` will answer for one tile short is read as the land
art itself being impassable, and that art is planned beside rather than on for the rest of the run.

### Before you run it

- Stand on the mountain face or in the cave you mean to work.
- **A pickaxe in hand.** The graphic is learned from it. Spares go in the pack, loose or in a bag;
  unopened bags are opened once before the run gives up looking.
- **The fire beetle nearby**, and yours. ESC at the cursor lets the script find one. Without a
  beetle the run still mines, and stops when the pack fills.
- Being mounted is fine.

## mine-here.py

The stationary half of `mining.py`. It stands where you put it, swings until the shard says nothing
is left, smelts, and stops. The swing answers the cursor with yourself and lets the shard pick the
ore, so there is no scan, walk or respawn wait.

| Outcome | What the loop does |
| --- | --- |
| `dug` | Wait for the ore, then consolidate |
| `failed` | A swing that found nothing. Recorded, no wait |
| `empty`, `nothingNearby` | Worked out. Consolidate, smelt, stop |
| `notOre`, `tooFar`, `notSeen` | Nothing here answers to moving, so each stops |
| `packFull` | Consolidate |
| `wornOut`, `saving`, `throttled`, `noCursor`, unreadable | As `mining.py` |

**It never moves.** Nothing in `legion/dist/mine-here.py` calls `API.Pathfind` or `API.GetPath`; the
`PathfindEntity` in it is `Beetle.walk_to`, which this run never calls. It smelts
against a beetle inside `SMELT_RANGE` and otherwise keeps the ore and says so, which makes weight a
real ending: call the beetle over and run it again.

### Before you run it

- **Stand on the vein.** A first swing that comes back worked-out ends the run with
  `no swing ever landed`.
- **The fire beetle within `SMELT_RANGE`**, and yours.
- A pickaxe in hand, spares in the pack. Being mounted is fine.

### What to set

Every timing is in seconds except `PATHFIND_TIMEOUT`.

#### Finding the ore (`mining.py` only)

| Setting | Default | What it is for |
| --- | --- | --- |
| `ORE_TILE_GRAPHICS` | stock RunUO bands | **The important one.** The land tiles the shard calls mountain or cave floor. Fill it in from a dead-end listing |
| `NOT_ORE_GRAPHICS` | empty | A seed only; refusals learned on the shard go to the run's memory |
| `ORE_STATIC_NAME` | `cave`, `rock`, `mountain`, `ore` | Cave floors are statics, matched by name. `rock` also matches pebbles, but a wrong match costs one `notOre` swing and the art is banned |
| `MINE_FOOTPRINT` | `1` | The radius a self-target is assumed to harvest: `1` is 3x3. Not measured on the shard |
| `STAND_RANGE` | `0` | How close the walk has to get to the planned tile. `0` stands on it |
| `MIN_SPOT_ORE` | `1` | Ore tiles a footprint has to hold before its spot is worth walking to |
| `PLAN_MAP` | `True` | Print the map to the journal once per plan |
| `MAP_PATH` | `mining-map.jsonl` | Where read ground is kept between runs. A bare filename lands in TazUO's working directory; `""` keeps nothing |
| `PARKED_PATH` | `mining-parked.jsonl` | Where worked-out tiles and their return times are kept between runs. `""` keeps nothing |
| `MINE_Z_RANGE` | `20` | How far above or below you a tile may sit. A face 40 z up passes the 2D test and the walk never closes |
| `SCAN_RADIUS` / `SURVEY_ARTS` | `12` / `15` | How far a plan looks, and how many arts a dead end lists. The first plan reads every land tile in the box, one client frame each: 625 at `12` |
| `PATHFIND_TIMEOUT` | `10` | How long one blocking `API.Pathfind` may take |
| `MAX_VEIN_WALKS` | `4` | Cycles walking to one spot before it is written off |
| `MAX_PATH_PROBES` | `24` | Routes one scan asks `API.GetPath` for before handing a spot out unprobed. Not applied under the ground rule |
| `ONLY_CONNECTED_GROUND` | `True` | A spot whose route leaves the scan box is parked, not walked to |
| `STOP_WHEN_WORKED_OUT` | `True` | End the run once nothing on this ground is left. `False` idles until the soonest respawn, as `lumberjack.py` does |
| `RESPAWN_DELAY` / `UNREACHABLE_DELAY` | `1500.0` / `300.0` | How long a worked-out ore tile, and a routeless spot, are left alone |
| `NOTHING_NEARBY_HINT` | `5` | Spots in a row with nothing to mine before it says `ORE_TILE_GRAPHICS` is probably wrong |

#### The tool

| Setting | Default | What it is for |
| --- | --- | --- |
| `PICKAXE_NAME` | `pickaxe` | Matched against the name; the graphic is learned from the one held |
| `SPARE_BAG_SERIAL` | `None` | A bag to search as well. Rarely needed |
| `DIG_TIMEOUT` | `8.0` | A swing plays its animation before the result arrives |
| `DIG_TARGET_TIMEOUT` / `_POLL` | `4.0` / `0.1` | How long to watch for the cursor before reading the swing as refused |
| `DIG_PROMPT_TEXT` | `Where do you wish to dig` | The sentence the shard opens the cursor with, waited on as the cursor. Wrong, and every swing reports `no target cursor` |
| `EQUIP_ATTEMPTS` / `_TIMEOUT` / `_POLL` | `3` / `2.0` / `0.2` | Equip pacing |
| `DISMOUNT_TIMEOUT` / `_POLL` / `_ATTEMPTS` | `2.0` / `0.2` / `3` | Dismount pacing |

#### Ore, metals and smelting

| Setting | Default | What it is for |
| --- | --- | --- |
| `ORE_GRAPHICS` | four arts | The arts an ore pile is drawn with. Never a way to read a stack's size |
| `ORE_NAME_WORD` | `ore` | Whole-word fallback for an unknown art. Whole, or `sycamore` gets smelted |
| `FIRE_BEETLE_GRAPHICS` / `_SERIAL` | `0xa9` / `None` | The stock body, and a way to pin one |
| `PICK_BEETLE` | `True` | A cursor at startup; ESC falls back to the search |
| `PICK_TIMEOUT` | `60.0` | How long you have to answer that cursor |
| `BEETLE_SCAN_RADIUS` / `SMELT_RANGE` | `18` / `2` | How far to look, and how close to stand |
| `MIN_SMELT_AMOUNT` | `2` | Two ore make an ingot; a stack of one is refused silently |
| `SMELT_ATTEMPTS` | `3` | Silent failures in a row before giving up on a hue. A throttled or stale attempt also looks silent |
| `MAX_SMELT_PASSES`, `SMELT_DELAY`, `SMELT_TIMEOUT`, `SMELT_POLL` | `60`, `0.7`, `4.0`, `0.2` | Smelting bounds and pacing |
| `COMBINE_DELAY`, `COMBINE_TIMEOUT`, `COMBINE_POLL`, `MAX_COMBINE_ATTEMPTS` | `0.7`, `2.0`, `0.2`, `12` | Consolidation pacing and backstop |
| `ORE_SETTLE_TIMEOUT` / `_POLL` | `1.5` / `0.15` | How long to wait for a swing's ore, which lands after the sentence announcing it |
| `ORE_METALS` | RunUO's nine | Metal names. A new one joins the set off its first tooltip |
| `METAL_LINE_EXTRA` / `NOT_METAL_WORDS` | `" '-"` / flags | Which tooltip line is the metal: letters and these only, and not a flag every item carries |
| `METAL_MISSES` / `METAL_ASKS` | `3` / `3` | Tooltips without a metal line before the lookup stops asking, and passes one pile gets. A missing tooltip is read next pass, never waited for |
| `DIFFERENT_ORE_TEXT` | RunUO's wording | The shard refusing two piles as different metals. Backstop for a pile no tooltip named |
| `INGOT_GRAPHICS` | four arts | A seed; the real graphic is learned by diffing the pack across the first smelt |

#### The attempt log

| Setting | Default | What it is for |
| --- | --- | --- |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each swing and each smelt is appended, while Mining is below its cap. `""` records nothing |
| `SKILL_NAMES` | `Mining` | Tried in order. None reading means no rows, and the run says so |
| `SKILL_TIMEOUT` / `SKILL_POLL` | `5.0` / `0.25` | How long the skill list is waited for at start-up |

#### Trouble and stopping

`WATCH_FOR_TROUBLE` scans `THREAT_RANGE` for a hostile each cycle, watches your hits and the beetle's,
and logs `trouble` / `clear`. Nothing calls the guards. `PACK_LIMIT` is the item-cap guard; there is
deliberately no weight guard, which would fire before the smelt could run.

| Setting | Default | What it is for |
| --- | --- | --- |
| `AMBUSH_TEXT` | `["been ambushed"]` | Fragment of what your character says on an ambush |
| `AMBUSH_WARNING` / `AMBUSH_HUE` | `"AMBUSHED!"` / `33` | Shown over your head once per ambush |
| `AMBUSH_ALARM` | `afplay` on a system sound | Run on this Mac, outside the game. Restarted while trouble lasts, never layered |
| `AMBUSH_NOTICES` | one `osascript` notification | Commands run once per ambush. `["say", "ambushed"]` is a spoken one |
| `AMBUSH_REPEATS` | `30` | Starts the alarm gets. Stops sooner once the hostile has gone |
| `AMBUSH_HOLD` | `True` | Stand still behind the gump on an ambush. `False` is the alarm alone |
| `AMBUSH_HOLD_TEXT` / `AMBUSH_HOLD_BUTTON` | a sentence / `Resume` | What the gump says, and what its button says |
| `AMBUSH_HOLD_HUE` | `33` | The text's hue |
| `AMBUSH_HOLD_POLL` | `0.5` | How often the button is read while it waits |

An ambush holds the run: the walk and any cursor are cancelled, a gump goes up in the middle of the
screen, and nothing moves until its button is pressed or the gump is closed. The alarm keeps
restarting for as long as it is up and stops the moment it comes down. Dying, or the stop button,
ends the hold as well.

### When it goes wrong

- **`no ore in range` on a mountain**: `ORE_TILE_GRAPHICS` does not match this shard. Read the
  printed arts.
- **`n spot(s) matched but had no walkable route`**: a few is ordinary. All of them, somewhere you
  can plainly walk, means `GetPath` will not answer for the tile itself; raise `STAND_RANGE` to `1`.
- **`land 0x… cannot be stood on, planning beside it from here on`**: a mountain face. Expected once
  per land art. Every art in the box, in a cave, means the cave floor here is land, not a static.
- **Five spots in a row with nothing to mine**: same cause as the first, caught earlier, or a shard
  that refuses a self-target; the journal after a swing says which.
- **`n ore tile(s) with no spot to stand on`**: every tile that could reach the ore is parked or
  impassable. Ordinary at the edge of a face; wait for a walk to move the box.
- **`unreadable outcome, check OUTCOME_TEXT`**: read the journal after a swing and correct it.
- **`no target cursor (n/20), backing off`**: a run of them with a pickaxe in hand means a refusal
  worded outside `THROTTLED_TEXT`; add it. If *Where do you wish to dig?* is on screen, correct
  `DIG_PROMPT_TEXT`.
- **`overweight … and smelting freed nothing`**: no beetle in range, not yours, or every hue written
  off. The run clears the write-offs and smelts once more before giving up.
- **`tooltips are not naming the metal here`**: ordinary on a shard without OPL; the run tells
  metals apart by attempting a merge. If the metal is on screen, `NOT_METAL_WORDS` is eating it.
- **`the shard refused two piles both read as 'x'`**: the wrong line is being read as the metal.
  Correct `METAL_LINE_EXTRA` or `NOT_METAL_WORDS`.
- **`could not get off the mount`**: `API.Dismount` is not how this shard dismounts.
- **`no pickaxe`**: nothing in hand and no spare found. The log lists every graphic seen.

### Notes

- Only the outcome read consumes journal matches. The save check, the throttle and unskilled
  checks inside the smelt, and `DIFFERENT_ORE_TEXT` read without consuming, because each is read
  more than once; consuming the ore refusal in the merge poll would silently split a metal.
- `API.TargetResource(serial, 0)` is deliberately not used: it bypasses the `DIG_PROMPT_TEXT` read
  and the `noCursor`/`throttled` distinction.

### Unverified

- `ORE_TILE_GRAPHICS`, and `OUTCOME_TEXT`, where `empty` matters most because it parks a vein.
  `You cannot mine there` sits in `empty` but on most shards means `notOre`; `There is nothing here
  to harvest` and `There is no ore here to mine` are close enough that a hybrid lands in whichever
  comes first.
- That a self-target harvests the 3x3 around the character. `MINE_FOOTPRINT` is a guess; on a shard
  where *no harvestable resources nearby* is really about the 8x8 bank, every spot in a bank costs
  a swing and a smelt trip before its footprint is parked.
- Whether `API.GetPath` with `within=1` answers for an impassable goal, which is what tells a land
  art off from a single blocked spot. If not, the run degrades to parking spots one at a time.
- Whether `API.Pathfind` closes on a face 20 z up. `MINE_Z_RANGE` is read from where you stand when
  the plan is made, so a footprint tile 20 z above its spot counts as covered.
- That the beetle standing on a planned spot only costs the two cycles it takes Roam to write the
  spot off.
- That `import json` resolves under the client's IronPython. The standard library is on `sys.path`,
  and `json` is pure Python there, but this is the first bundle to lean on it.
- Whether `API.GetTile` answers the land tile or the topmost object. The survey says so if not.
- Whether `ApiStatic.IsCave` beats the name list. The survey prints it; nothing branches on it.
- Whether `"onehanded"` is a pickaxe's layer, and whether `Amount` reads 0 for a stack the client
  has no data for, which `MIN_SMELT_AMOUNT` assumes.
- `RESPAWN_DELAY`, `MINE_Z_RANGE`, the beetle body `0xa9`, that a beetle smelts by being targeted
  with ore, and `DIFFERENT_ORE_TEXT`.
- Whether `import clr` reaches `System.Diagnostics.Process` (logged once as `could not run afplay`),
  and whether encounter spawns come up gray or red so `trouble` keeps the alarm sounding.

## lumberjack.py

Finds the nearest tree, walks to it, chops, turns logs into boards as the weight climbs, and puts the
boards onto your pack animals. It roams: there is no bounds box.

Before the loop: learn the axe, say what is in the pack, the pack-animal cursor, and haul once if
already over `HAUL_BUFFER`. Per cycle:

1. Check the stop conditions: dead, overweight beyond `WEIGHT_BUFFER`, or the item cap.
2. Sit out a world save.
3. Equip an axe, every cycle. Spares come out of the pack.
4. Haul if over `HAUL_BUFFER`: make boards, then fill every animal in range, nearest first.
5. Scan for a tree within `SCAN_RADIUS` and `CHOP_Z_RANGE`, skipping parked tiles and routeless
   trees. If dry, sweep again out to `ROAM_RADIUS`.
6. Walk to it if further than `CHOP_RANGE`.
7. Chop, and branch on what the shard says.

| Outcome | What the loop does |
| --- | --- |
| `chopped` | Count it, and record the logs it landed per hue |
| `failed` | *You hack at the tree for a while, but fail to produce any useable wood*. A swing that landed, recorded |
| `empty` | Parks the trunk, or the whole spot under `AIM_AT_SELF` |
| `nothingNearby` | Always parks the ground within `CHOP_RANGE` |
| `notTree` | Set the tree aside, and ban the art when the swing named it |
| `tooFar` | Set the tile aside |
| `notSeen` | Line of sight. Permanent |
| `packFull` | Haul. A log stack converts to one board stack, so only boards leaving frees slots |
| `wornOut` | The next cycle equips a spare |
| `saving` | Sit it out |
| `throttled` | Back off, growing; give up after `MAX_THROTTLED` |
| `noCursor` | Backed off like a throttle, stops after `MAX_NO_CURSOR` |
| anything else | `MAX_UNKNOWN` in a row ends the run; check `OUTCOME_TEXT` |

When nothing within `ROAM_RADIUS` is choppable but something is regrowing, the loop idles until the
soonest is due, in `IDLE_POLL` slices so the stop button and the threat watch keep working. However
the run ends, it makes boards and unloads once more.

An ambush holds the run: the walk and any cursor are cancelled, a gump goes up in the middle of the
screen, and nothing moves until its button is pressed or the gump is closed. The alarm keeps
restarting for as long as it is up and stops the moment it comes down. Dying, or the stop button,
ends the hold as well.

**How the swing is aimed.** `AIM_AT_SELF = True` uses `API.TargetSelf()`: the shard takes a
self-target as *harvest what is in reach* and picks the tree, so the scan only decides where to
stand. Then `empty` is about the spot and parks every tree within `CHOP_RANGE` (parking one tile
left the run swinging at the neighbour the shard had just written off), and `notTree` bans no art,
since the shard chose what to refuse. `False` uses `API.Target(x, y, z, graphic)`; without the
graphic the target is the land tile and the shard answers as mining. Aimed this way `empty` parks
one trunk and `notTree` bans the art.

**Boards and hauling.** Logs become boards by using the axe on the log stack. Stock RunUO answers
with a sound only, so the result is a pack diff, which also names the board graphic. Hue is not part
of the log match, since special woods hue their logs, but it keys the converter's write-offs. Only
boards go onto an animal; a wood given up on stays in the pack and every haul reconsiders it. All
animals get loaded: one that stops accepting is full. An animal that takes nothing at all is skipped
for the run; a partial load keeps its turn. Two latches end the walking for good, no animal found
and `MAX_EMPTY_HAULS` hauls that freed nothing; after either, the run chops and converts until the
weight guard stops it. The double-click fallback is not ported: it mounts a rideable beetle.

### Before you run it

- Stand in the forest. It wanders after the wood.
- **An axe in hand.** Axes are two-handed and hatchets one-handed; both layers are read.
- **Your pack animals nearby**, if you want hauling. Only yours count. Without one the run chops
  until the weight guard fires.
- Being mounted is fine; it never dismounts. It warns at the cursor in case the animal you want is
  the one you are sitting on.

### What to set

Every timing is in seconds except `PATHFIND_TIMEOUT`.

| Setting | Default | What it is for |
| --- | --- | --- |
| `AIM_AT_SELF` | `True` | How the cursor is answered. See above |
| `AXE_NAMES` / `NOT_AXE_NAMES` | `axe`, `hatchet` (+plurals) / `pickaxe`, `shovel` | Whole words. `axe` is inside `pickaxe`, so a substring match equips the mining tool when the axe breaks |
| `SPARE_BAG_SERIAL` | `None` | A bag to search as well. Rarely needed |
| `TREE_GRAPHICS` / `NOT_TREE_GRAPHICS` | empty | Overrides, asked before `IsTree`. Fill from a dead-end listing |
| `TREE_NAME` | `['tree']` | Name fallback for a build that leaves `IsTree` unset |
| `CHOP_RANGE` / `CHOP_Z_RANGE` | `2` / `20` | Where walking stops, and how far above or below a tree may sit |
| `SCAN_RADIUS` / `ROAM_RADIUS` | `12` / `24` | The ordinary sweep, and the wider one paid only on a dry cycle |
| `SURVEY_ARTS` | `15` | Arts named when a sweep comes up empty |
| `PATHFIND_TIMEOUT` | `10` | How long one blocking `API.Pathfind` may take |
| `MAX_TREE_WALKS` | `4` | Cycles walking to one tree before it is written off |
| `MAX_PATH_PROBES` | `24` | Nearest matches a sweep pays an `API.GetPath` for |
| `REGROW_DELAY` / `UNREACHABLE_DELAY` | `1500.0` / `300.0` | How long a chopped-out tree, and a routeless one, are left alone |
| `EMPTY_HINT` | `5` | Empty spots in a row before it says the tree test is matching scenery |
| `CHOP_TIMEOUT` | `8.0` | A swing plays its animation before the result arrives |
| `CHOP_TARGET_TIMEOUT` / `_POLL` | `4.0` / `0.1` | How long to watch for the cursor before reading the swing as refused |
| `CHOP_PROMPT_TEXT` | three wordings | The sentence the shard opens the cursor with. Wrong, and every swing reports `no target cursor` |
| `LOG_GRAPHICS` / `LOG_NAME_WORDS` | four arts / `log`, `logs` | Log arts, and the whole-word fallback |
| `BOARD_GRAPHICS` / `BOARD_NAME_WORDS` | four arts / `board`, `boards` | A seed; the real graphic is learned from the first conversion's diff |
| `CONVERT_ATTEMPTS` | `3` | Silent failures in a row before giving up on a hue for the pass. Saves, throttles and no-cursor are excluded |
| `MAX_CONVERT_PASSES`, `CONVERT_DELAY`, `CONVERT_TIMEOUT`, `CONVERT_POLL` | `60`, `0.7`, `4.0`, `0.2` | Conversion bounds and pacing |
| `PACK_ANIMAL_GRAPHICS` / `_SERIALS` | pack horse, pack llama, giant beetle / `[]` | Stock bodies, and a way to pin an exact list |
| `PICK_PACK_ANIMALS` / `MAX_PICKS` / `PICK_TIMEOUT` | `True` / `8` / `60.0` | A cursor at startup, ESC when done. A picked list is pinned |
| `ANIMAL_SCAN_RADIUS` / `UNLOAD_RANGE` | `18` / `2` | How far to look, and how close to stand |
| `MOVE_DELAY` | `0.7` | Between moves |
| `HAUL_BUFFER` / `WEIGHT_BUFFER` | `120` / `40` | Headroom at which it hauls, and at which it stops. The first is wider so hauling gets its turn |
| `MAX_EMPTY_HAULS` | `3` | Hauls that freed nothing before the animals are taken to be full |
| `OUTCOME_TEXT` | guesses | `chopped` and `nothingNearby` are measured |
| `LOG_SETTLE_TIMEOUT` / `_POLL` | `1.5` / `0.15` | How long a recorded swing waits for its logs, which land after the sentence announcing them |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each chop and each conversion is appended, while Lumberjacking is below its cap. `""` records nothing |
| `SKILL_NAMES` | `Lumberjacking` | Tried in order. None reading means no rows, and the run says so |
| `SKILL_TIMEOUT` / `SKILL_POLL` | `5.0` / `0.25` | How long the skill list is waited for at start-up |

Trouble and stopping, the hold included, carry the same names and defaults as `mining.py`.

### When it goes wrong

- **`no tree in range` in a forest**: the listing shows each static with `MATCHES`, `IsTree` and
  its name; correct `TREE_GRAPHICS` or `TREE_NAME` from it.
- **`n tree(s) matched but had no walkable route`**: as `mining.py`.
- **`5 spots in a row had nothing to chop`**: the tree test is matching scenery.
- **`unreadable outcome, check OUTCOME_TEXT`**: read the journal after a chop and correct it.
- **It looks like it is mining.** Check the opening `axe graphic is …` line; a shard whose pickaxe
  is named otherwise wants that name in `NOT_AXE_NAMES`. Otherwise `AIM_AT_SELF` let the shard fall
  through to ore; set it `False`.
- **`no target cursor (n/20), backing off`**: as `mining.py`, with `CHOP_PROMPT_TEXT`. The line
  names what is in hand, because the axe layer is the other likely fault.
- **`no pack animal found`** or **`3 hauls freed nothing - the animals are full`**: both latch the
  walking off. Click the animals at startup, check `PACK_ANIMAL_GRAPHICS`, or pin the serials.
- **`'X' took nothing`** or **`all n pack animal(s) are full`**: expected. A save is excluded and
  the animal keeps its turn.
- **`N logs would not convert`**: check the journal for unskilled, and `BOARD_GRAPHICS`, before
  raising `CONVERT_ATTEMPTS`.

### Notes

- `API.GetStaticsInArea` sweeps a box in one call and trees are statics, so nothing here calls
  `API.GetTile` and there is no cache: a felled tree that changes art would go stale in one.
- Another mobile's pack is `ApiMobile.Backpack`, falling back to `API.FindLayer("backpack", serial)`.
- Logs are told apart by graphic and hue, so none of `mining.py`'s metal or merge machinery exists.

### Unverified

- Confirmed: a self-target harvests wood here (*You chop some ash logs and put them into your
  backpack*).
- Whether a self-target reaches for ore on rock with nothing choppable in reach.
- That IronPython binds the four-argument `Target` by arity, and that the graphic must be passed
  (a web-client finding). A miss reads as unreadable.
- `ApiStatic.IsTree` over-reaches: `0xc9e`, *o'hii tree*, refused with *You can't use an axe on
  that*. The art ban limits that to one swing per art, and is off under `AIM_AT_SELF`.
- Which static of a tree is the trunk; only `CHOP_Z_RANGE` and the cooldown keep the run off the
  foliage. Whether a chopped-out tree changes art.
- `REGROW_DELAY`, the log and board art sets (the board set corrects itself; the log set has
  `LOG_NAME_WORDS`), and whether boards weigh less than logs here.
- The pack animal bodies, and whether `Backpack` or `FindLayer` resolves for another mobile. Neither
  means no hauling; pin `PACK_ANIMAL_SERIALS`.
- Whether `API.RequestTarget` returning falsy is ESC rather than a timeout, which ends the multi-pick.
- The hold gump's layout, and that a right-click close sets `IsDisposed`.
- `"twohanded"` and `"onehanded"` as the axe layers.
- What `API.GetStaticsInArea` costs at `ROAM_RADIUS`, 49 tiles a side through interop.

## fishing.py

One cast, then it stops: get off the mount, say `GUARD_PHRASE`, double-click the fishing pole,
answer the cursor with the nearest water tile, read the shard's answer, append one row. Run it again
for the next cast. There is no loop, no stall watch and no heartbeat.

1. Wait for the skill to read, and stop if you are dead or Fishing is capped.
2. Dismount, up to `DISMOUNT_ATTEMPTS` times.
3. Say `GUARD_PHRASE`.
4. Find the pole in either hand, then in the pack. Nothing is equipped.
5. Read the land and statics within `FISH_RANGE` and take the water tile nearest by crow flight.
6. Use the pole, wait for the cursor, answer it with `Target(x, y, z, graphic)`.
7. Read the outcome. A catch is named off the text past the colon of `You pull out an item: …`.

| Outcome | What it means |
| --- | --- |
| `caught` | `You pull out an item: …`. Recorded with what the pack gained |
| `failed` | `You fish a while, but fail to catch anything`. Recorded |
| `empty` | The fish are not biting here. Move along the shore |
| `tooFar` | The shard wants you closer to the water |
| `notWater` | The shard refused the tile. `WATER_LAND_GRAPHICS` or `WATER_STATIC_GRAPHICS` is wrong for this shard |
| `mounted` | The shard still sees you mounted |
| `noCursor` | The pole raised no cursor and the shard said nothing |
| `throttled` / `saving` | Run it again in a moment |
| `unknown` | Nothing matched. The journal's last lines are printed |

Only `caught` and `failed` are recorded. The row is written after `GAIN_SETTLE`, or as soon as the
skill value moves, because the client applies the gain after the outcome line. A `caught` row waits
`CATCH_SETTLE` for the pack to show the fish first.

### Before you run it

- **A fishing pole in hand or in the pack.** A held one is preferred.
- **Stand within `FISH_RANGE` tiles of water**, on foot or mounted; it dismounts you.
- **`GUARD_PHRASE` is said every run.** Set it to `""` if the guards are already set or you have
  none.
- **`DATA_PATH` is relative to TazUO's working directory.** Set an absolute path.

### What to set

| Setting | Default | What it is for |
| --- | --- | --- |
| `GUARD_PHRASE` | `all guard` | Said before the cast. `""` says nothing |
| `POLE_GRAPHICS` / `POLE_NAME_WORDS` | `0x0DBF` / `fishing`, `pole` | A pack art learned by name joins the set |
| `HAND_LAYERS` | `twohanded`, `onehanded` | Where a held pole is looked for |
| `WATER_LAND_GRAPHICS` / `WATER_STATIC_GRAPHICS` | stock RunUO bands | **The important one.** What counts as water. Statics are numbered apart from land |
| `FISH_RANGE` | `4` | How far it looks for water. RunUO's fishing range |
| `PROMPT_TEXT` | *Where do you want to fish* | The cursor prompt, a guess. `HasTarget` is what the wait leans on |
| `CURSOR_TIMEOUT` / `NO_CURSOR_READ` | `2.0` / `1.0` | How long the pole has to raise a cursor, and how long a refusal is listened for when it does not |
| `CAST_TIMEOUT` | `12.0` | How long the shard has to answer after the cast animation |
| `CATCH_SETTLE` / `GAIN_SETTLE` | `1.5` / `2.0` | How long the pack has to show the fish, and the client the gain |
| `DISMOUNT_ATTEMPTS` | `3` | Before *could not get off the mount* |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each cast is appended. `""` records nothing |

### When it goes wrong

- **`no water within 4 tiles`**: nothing in either table is in range. Stand nearer the water, or
  the shard's water arts are not the stock ones: read them off a `mine-here.py` style survey, or
  off `API.GetTile` and `API.GetStaticsAt` at a tile you can fish from by hand, and add them.
- **`the shard says that tile is not water`**: the table matched an art the shard does not fish.
  Same fix.
- **`the pole raised no cursor`**: the pole was refused silently. Check it is a fishing pole and
  not worn out.
- **`unreadable outcome, check OUTCOME_TEXT`**: the last journal lines are printed under it; copy
  the shard's wording into the matching bucket.
- **`caught something the journal did not name`**: the catch line had no colon. The row is still
  written, with an empty name.

### Notes

- The catch bucket is read off the journal tail rather than through `InJournalAny`, because that
  clears the line and the name is on it.
- A self-target is refused for fishing on this shard, which is why the tile is named.

### Unverified

- Every water band. They are RunUO's `Fishing.cs` tables with the static ids brought down by
  `0x4000`.
- Whether `Target(x, y, z, graphic)` on a *land* water tile is taken. The land art is passed as
  read; if the shard wants the default, try `1337` in its place.
- The cursor prompt and every wording in `OUTCOME_TEXT`.
- That a pole in the pack is accepted without being equipped.
- The catch line's shape on this shard. Anything past the first colon is the name.

## attack.py

One attack, then it stops: scan the mobiles within `RANGE`, keep the gray, criminal, enemy and
murderer ones, drop yourself, the dead and your own pets, drop anything whose tooltip carries an
`OWNED_PROP_WORDS` word, turn war mode on and attack the nearest one left. Run it again for the next
one. There is no loop, no chase and no heartbeat: the client's own follow does the closing.

1. Stop if you are dead.
2. `GetAllMobiles` with the hostile notoriety list. Blue never comes back, and on ServUO a pet or
   summon takes its owner's colour, so an innocent player's pets are out before anything is read.
3. Skip yourself, the dead, and anything with `IsRenamable` set.
4. Nearest first, read the tooltip and skip it if any `OWNED_PROP_WORDS` word is in it. Only the
   ones in line are read.
5. `SetWarMode(True)`, `Attack(serial)`, say who.

### What to set

| Setting | Default | What it is for |
| --- | --- | --- |
| `RANGE` | `10` | How far out it looks. The API's own `NearestMobile` default |
| `OWNED_PROP_WORDS` | `(tame)`, `(summoned)`, `(bonded)` | Tooltip words that mark someone's creature. ServUO's `AddNameProperties` wording, case-insensitive |
| `OPL_TIMEOUT` | `1` | Whole seconds a tooltip the client has not fetched yet is waited for. The API takes an int |

### When it goes wrong

- **`nothing hostile within 10 tiles`**: nothing gray or red is in range, or everything in range
  was yours, dead, or read as owned.
- **It attacked a player's pet or summon**: read the pet's tooltip and put the shard's wording in
  `OWNED_PROP_WORDS`.
- **It attacked a gray or red player**: a player is not told from a monster. Only the tooltip words
  screen anything that passes the notoriety scan.

### Unverified

- The three tooltip words on this shard. They are ServUO's, read off `BaseCreature`.
- That `Attack` after `SetWarMode(True)` starts a swing without a target cursor.
- That a gray pet of a criminal or murderer carries the same tooltip words as a blue one.

## arms-lore.py

Target one weapon, then use Arms Lore on it every `DELAY` seconds until the skill caps or you stop
the script. The weapon can sit in your pack.

- The weapon has to stay resolvable; dropped or handed away ends the run.
- A refused use raises no cursor, so the pass times out after `TARGET_TIMEOUT`. Nothing is recorded.

| Setting | Default | What it is for |
| --- | --- | --- |
| `DELAY` | `0.5` | Seconds between uses. Below the skill timer this only spends passes on refusals |
| `TARGET_TIMEOUT` | `1.0` | How long a use has to put a cursor up |
| `READ_TIMEOUT` | `1.5` | How long a reading has to say what it found |
| `READ_POLL` | `0.1` | How often the journal is asked |
| `PICK_TIMEOUT` | `30.0` | How long the opening cursor waits for you |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each reading is appended. `""` records nothing |

Nothing here has watched Arms Lore on this shard. `read` is a list of stems (`damage`,
`durability`, `quality`) rather than a sentence, because shards report the reading in different
wording. Unmatched outcomes are counted and reported as `N outcome(s) went unread`.

## magery.py

Casts whichever of four spells still gains at the current level, meditates when the pool runs dry,
and stops past 120.0. It raises no cursor of its own. Per cycle: check dead, read the skill and pick
the band, meditate if short of the row's `mana`, cast and read the outcome, pace.

| Band | Spell | Circle | Mana | Cursor | What it is |
| --- | --- | --- | --- | --- | --- |
| ≤ 45.0 | Bless | 3rd | 9 | at self | A self buff |
| 45.0 – 60.0 | Arch Protection | 4th | 11 | at self | A self buff |
| 60.0 – 80.0 | Invisibility | 6th | 20 | at self | A self buff |
| 80.0 – 120.0 | Earthquake | 8th | 50 | none | An area attack. It hits everything around you |

These are the spells the guides name as gaining without a victim. The 5th and 7th circles are
skipped: every 7th-circle spell wants a ground cursor or a gump.

| Outcome | What happens |
| --- | --- |
| `cast` | Tallied, fault counters cleared |
| `fizzled` | Counted, not tallied. Commoner the further a circle is above the skill |
| `alreadyCasting` | Waits `CASTING_WAIT`, flat. Never counted towards a stop |
| `alreadyUp` | Waits `BUFF_WAIT`. Only with `SKIP_WHEN_BUFFED` on, or a refusal in words |
| `disabled` | Tallied: a shard that treats one of these as a toggle still charged for it |
| `noMana` | Says the row's `mana` is understated, then gathers mana |
| `noReagents` | Stops |
| `unskilled` | Stops |
| `saving` | Sits it out and resets the counters |
| `throttled` | Backs off, growing; `MAX_THROTTLED` in a row ends the run |
| anything else | Unreadable, said once per stretch. Ends nothing on its own |

`MAX_STALE` cycles with no cast and no movement in the skill is the only ending for a run getting
nowhere, and it cannot fire while the skill moves. A dry mana stretch is charged what it cost in
cycles.

**How a cast is read**, in order: snapshot the buff, snapshot mana, cancel a live cursor, clear the
journal, cast, answer the cursor, poll `OUTCOME_TEXT`. A success says nothing, so the buff
transitioning from down to up or mana strictly decreasing proves it; a standing buff proves nothing.
The poll gives up once `IsCasting` has gone up and come back down, plus `PROOF_GRACE` because the
mana lands after the flag. `cast_timeout` is the ceiling, not the timer.

**One late look**, and only for the attempt that needs it. An outcome nothing proved inside the
window is not an outcome that never arrived - the shard's answer was measured landing a beat behind
the incantation. So before giving up, the cast stands through the `cast_delay` it owes anyway and
reads all three proofs once more. A proved cast never reaches it and never pays for it; `pace` knows
the delay has already been spent. Raising `cast_timeout` would buy the same second look and charge
every attempt in the run for it.

**Nothing waits out the recovery.** `pace` is the row's `cast_delay` only. Waiting on `IsRecovering`
made a Bless cycle several seconds of standing still; a cast issued too early is refused in words
and costs one flat `CASTING_WAIT`. One or two a band is the pacing finding the shard's real cast
time; a band that is mostly them wants `cast_delay` raised.

**The self cursor** is answered by a pre-target queued before the cast, typed off the row's
`target_kind` (default `beneficial`). It is cancelled after every cast, or an unused one stays armed
for the next cursor. If it does not land, the outcome poll tries `API.Target(API.Player)`,
`API.TargetSelf()` and `API.Target(API.Player.Serial)` in turn until the cursor goes down, latches
the one that worked, and says `the cursor answers to Target(player)` once.

**Timing, measured.** A 3rd-circle cast raises its cursor at 1.6s and takes the mana at 1.8s.
A `cast_timeout` of 1.2 read every cast as unreadable and left the cursor unanswered. Every row's
timeout is now the measured time with a margin.

**The mana wait** meditates with whatever is in hand. A refused trance retires meditation for the
run and falls back on natural regeneration. `MEDITATE_TO_FULL` fills the pool, which matters most at
50 mana a cast; the comparison is `>=`, since a regenerating pool passes a figure more often than it
lands on it.

### Before you run it

- **Stand somewhere empty, never in town.** The last band is Earthquake. The script does not move,
  fight or heal.
- **Empty your hands**, or meditation is refused.
- **Carry reagents**, or wear 100% LRC. Running out ends the run.
- **Below about 30.0, buy the skill from a trainer.** At 25 the first row is mostly fizzles.
- It aims at 120.0, which needs power scrolls; the run stops at the shard's cap.

### What to set

Every timing is in seconds.

| Setting | Default | What it is for |
| --- | --- | --- |
| `STAGES` | four rows | One row per band: cast `spell` until the skill reaches `up_to`, at `mana` a cast |
| `STAGES[].up_to` | — | The skill value the row trains to, exclusive. A float, `74.6` |
| `STAGES[].buff` | — | A `BuffIconType` member name, matched against `str(buff.Type)`. Earthquake has none |
| `STAGES[].target` | `self` | Answers the row's cursor. Every row but Earthquake |
| `STAGES[].cast_timeout` | 3.0 – 5.0 | **The one worth tuning.** Below the real cast time every success reads unreadable |
| `STAGES[].cast_delay` | 0.3 – 0.6 | The whole pause between two casts. Too short costs one `CASTING_WAIT` per overshoot |
| `CAST_TIMEOUT` / `CAST_DELAY` | `2.0` / `0.75` | Fallback for a row that names neither |
| `PROOF_GRACE` | `0.6` | How long after `IsCasting` falls the proof is still waited for |
| `SELF_TARGET_TIMEOUT` / `_POLL` | `1.0` / `0.1` | How long the cursor has to go down before the next answer is tried |
| `SELF_ANSWERS` | three | Fallbacks for a cursor the pre-target did not take |
| `CASTING_WAIT` | `0.5` | Flat wait after a cast refused for not having released you |
| `SKIP_WHEN_BUFFED` | `False` | Off: gating on the buff caps the run at one cast per buff duration |
| `DISABLED_IS_PROGRESS` | `True` | A toggle is still a charged cast |
| `MEDITATE` | `True` | Off waits for natural regeneration |
| `MEDITATE_TO_FULL` | `True` | Fill the pool, or stop when the next cast is affordable |
| `MEDITATE_TIMEOUT` / `_ATTEMPTS` / `_START_TIMEOUT` | `20.0` / `4` / `2.0` | One trance's watch, trances a stretch gets, and how long the shard has to say it started |
| `MANA_POLL` / `MANA_LOG_EVERY` | `0.5` / `10.0` | How finely the pool is watched, and how often reported |
| `REGEN_TIMEOUT` | `120.0` | The natural-regeneration fallback |
| `MAX_STALE` | `500` | Cycles with no cast and no movement before the run gives up |
| `MAX_BLIND_READS` | `5` | Cycles the client may answer nothing for the skill |
| `SKILL_TIMEOUT` / `SKILL_POLL` | `1.0` / `0.5` | How long the skill list is waited for at start-up |
| `MAX_THROTTLED` | `20` | Refusals in a row before the run stops |
| `MAX_CYCLES` | `5000` | The backstop |
| `OUTCOME_TEXT` / `MEDITATE_OUTCOME_TEXT` | guesses | The recovery line and the trance line are measured |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each cast is appended. `""` records nothing |

There is no stall watchdog, because cycles are mostly mana coming back on purpose, and no health
floor, because nothing here hurts the caster.

### When it goes wrong

- **`the cursor would not take a self target`**: neither the pre-target nor the fallbacks landed.
  The cast is wasted; the next one cancels the cursor. Every cast means this shard targets the spell
  some other way.
- **`outcome unreadable - carrying on`**: usually the row's `cast_timeout`, not the wordings. The
  other cause is a buff already standing, leaving only the mana to prove the cast.
- **No `buff bar:` line, ever**: the client publishes no buffs, so three rows rely on mana alone.
- **`buff bar:` prints ids the table lacks**: copy the `Type` into that row's `buff`.
- **`N cycles without a cast or a change in the skill`**: the run is getting nowhere.
- **`the shard refuses meditation (blocked)`**: something is in hand. Put it away and restart.
- **`refused for mana at N`**: raise the row's `mana`.
- **`out of reagents`**: refill, or LRC.
- **The log fills with *you have not yet recovered from casting a spell***: raise that row's
  `cast_delay`.
- **Casts land but the skill does not move**: the bound between rows wants moving down.
- **`Magery is capped at 100.0`**: no power scroll.

### Unverified

- `Bless` is confirmed off a live `buff bar:` dump; the other three `BuffIconType` names are read
  from the enum.
- The band bounds are the AFK guides' (*50–86 Invisibility, 86 up Earthquake*), not measured.
- Whether Arch Protection raises a cursor here. Where it does not, the row costs its `cast_timeout`
  per cast.
- The `cast_timeout` figures above the 3rd circle are scaled from the one measured.

## mysticism.py

The same loop as `magery.py` on the same shared modules, so *How a cast is read*, *The self cursor*
and *The mana wait* there describe this one. Its own are the table, the cursor kinds and a health
floor.

| Band | Spell | Mana | Cursor | What it is |
| --- | --- | --- | --- | --- |
| ≤ 40.0 | Nether Bolt | 4 | none answered | The cheapest thing in the book |
| 40.0 – 63.0 | Stone Form | 11 | at self, beneficial | A toggle. Every other cast takes it off |
| 63.0 – 80.0 | Cleansing Winds | 20 | at self, beneficial | A heal and cure |
| 80.0 – 95.0 | Hail Storm | 40 | at self, harmful | An area attack, centred on you |
| 95.0 – 120.0 | Nether Cyclone | 50 | at self, harmful | An area drain, centred on you |

The four bands from 40.0 are the guides' table. Nether Bolt is this script's addition so an unbought
skill has something to cast; a trainer is faster, and the start-up line says so. Nether Bolt answers
no cursor: the mana goes as the incantation ends, and the cursor is left for the next cycle's
guarded cancel.

The outcomes are `magery.py`'s, plus `formLocked`, which stops: every band above Stone Form is
unreachable while the form is up, and nothing here drops it. `disabled` here is Stone Form toggling
off, a cast the shard charged for, so `DISABLED_IS_PROGRESS` is on and the bucket is tallied. The
buff transition proves the casts that turn it on; the mana proves the ones that turn it off.

**The health floor.** The last two bands are harmful spells centred on the caster, and nothing here
heals. `HURT_FLOOR` stops the run at half health. On a shard that excludes the caster from their own
area spell it never fires.

### Before you run it

- **Stand somewhere empty, never in town.** The top two bands are area attacks. The script does not
  move, fight or heal.
- **A Mysticism spellbook and its reagents**: the standard eight plus Dragon's Blood, Fertile Dirt,
  Daemon Bone and Bone, or 100% LRC.
- **Empty your hands**, or meditation is refused.
- Focus or Imbuing sets the damage, not the gain. Neither is needed.
- **Below about 30.0, buy the skill from a trainer.**
- It aims at 120.0, which needs power scrolls; the run stops at the shard's cap.

### What to set

Everything below `STAGES` is `magery.py`'s block with the same defaults. These are its own:

| Setting | Default | What it is for |
| --- | --- | --- |
| `STAGES` | five rows | One row per band |
| `STAGES[].target` | `self` on four | Nether Bolt does not answer its cursor |
| `STAGES[].target_kind` | `harmful` on two | The cursor type the shard raises. Defaults to `beneficial` |
| `STAGES[].buff` | Stone Form only | The other four train on the mana proof |
| `FIRST_BAND` | `40.0` | Where the guides' table starts. Under it the start-up line points at the trainer |
| `HURT_FLOOR` | `0.5` | Fraction of max hits the run stops below |

### When it goes wrong

- **`a form is blocking …`**: drop Stone Form and start again. If this shard never does this, the
  `formLocked` wordings are the guess to delete.
- **`the cursor would not take a self target`** on Hail Storm or Nether Cyclone: the harmful
  self-target is the guess. Delete `target` and `target_kind` from those rows; they then behave like
  Nether Bolt.
- **`outcome unreadable - carrying on`**: the row's `cast_timeout`, as in `magery.py`.
- **`buff bar:` prints an id the table lacks**: copy the `Type` into Stone Form's `buff`.
- **`hurt (N/M)`**: something is hitting you, or this shard includes the caster in their own area
  spell. If the latter, the top two bands want another plan.
- **`refused for mana at N`**: raise the row's `mana`.

### Unverified

- `"StoneForm"` as the `BuffIconType` name, read from the enum. The `title` fallback and the mana
  proof cover it either way.
- A harmful self-target: whether the shard raises the cursor as `harmful` and accepts the caster.
- Whether the caster takes their own area damage.
- The `formLocked` bucket, which no live run has produced.
- The band bounds, the mana ladder, and the `cast_timeout` figures, scaled from Magery's 3rd circle.

## chivalry.py

The same loop as `magery.py` on the same shared modules, so *How a cast is read* and *The mana wait*
there describe this one. Its own are the table, a tithing gate, the weapon stowed around every trance,
and bandaging under a health floor. No band raises a cursor.

| Band | Spell | Mana | Tithing | Needs | What it is |
| --- | --- | --- | --- | --- | --- |
| ≤ 45.0 | Consecrate Weapon | 10 | 10 | 15.0 | Enchants **what is in hand** - the one band that wants a weapon |
| 45.0 – 60.0 | Divine Fury | 15 | 10 | 25.0 | A self buff |
| 60.0 – 70.0 | Enemy of One | 20 | 10 | 45.0 | A self buff, and a **toggle** - casting it again takes it off |
| 70.0 – 90.0 | Holy Light | 10 | 10 | 55.0 | An **area attack** on everything non-blue around you |
| 90.0 – 120.0 | Noble Sacrifice | 20 | 30 | 65.0 | Heals nearby allies **at the cost of your own hit points** |

The outcomes are `magery.py`'s minus `noReagents`, plus:

| Outcome | What happens |
| --- | --- |
| `noTithing` | **Stops.** Go and tithe. The same gate is asked of `API.Player.TithingPoints` before every cast, so the run normally stops before the shard has to say it |
| `noWeapon` | Draws the weapon again, and stops only if that fails or nothing was ever held |
| `disabled` | Tallied: Enemy of One coming off is a cast the shard charged for |
| `unskilled` | Stops - including the karma refusals, which mean the same thing |
| `unknown` | Recorded as a row rather than dropped, and the journal is shown with the first few |

**How a fizzle is read**, and the one place this loop differs from `magery.py`'s reading: a paladin's
spell fails in silence - a sound, and nothing said at all - so `OUTCOME_TEXT` has nothing to match
and the buff and the mana both stay where they were. What separates that from a cast the shard never
started is the tithing point, which is taken for the roll rather than for the result: read before
the cast, read again once the two proofs of a success have had their whole window, and a drop with
no mana behind it is written down as `fizzled`. Chivalry is the only school handed that reader, so
`magery.py` and `mysticism.py` read exactly as they did.

That reading rests on the shard charging tithing for a failed roll, which it does: a Holy Light band
at 74.0 read 52 attempts as 35 `fizzled`, 14 `cast` and 3 `unknown`, where every one of those
failures had been going unread. The journal printed under the `unknown` ones is empty of anything
but the mantra, which is the silence this is working around.

**The weapon.** Meditation is refused with anything in hand, and Consecrate Weapon wants one. What
is in either hand at start-up is remembered by serial, moved to the pack before every trance, and
equipped again on every way out of the mana wait - a wait the guards ended included. A character who
starts empty-handed never touches any of that, and the first band stops the run instead.

**The health floor** is for Noble Sacrifice, which sets the caster's hits, mana and stamina to 1
where it finds anything to heal - a pet or a passing blue is enough. Under `HURT_FLOOR` the run
bandages itself at the top of the cycle, *before* the guards look, and the floor ends only a run the
bandages could not get back above it. The hits rising are the proof; the wordings only explain a
failure. A pack with no bandages is said at start-up and the floor goes back to being a stop.

### Before you run it

- **Stand somewhere empty, never in town.** Holy Light is an area attack. The script does not move
  or fight.
- **Tithe gold at a shrine.** Every cast spends 10 points, Noble Sacrifice 30, and nothing here
  refills them. The start-up line says how many you have.
- **Hold the weapon you mean to train the first band with**, or start above 45.0 empty-handed.
- **Carry clean bandages** (`0x0E21`) for the last band, or set `BANDAGE = False` and accept the stop.
- **Below about 40.0, buy the skill from a trainer.** Consecrate Weapon opens at 15.0 but is mostly
  fizzles down there.
- It aims at 120.0, which needs power scrolls; the run stops at the shard's cap.

### What to set

Everything below `STAGES` is `magery.py`'s block with the same defaults. These are its own:

| Setting | Default | What it is for |
| --- | --- | --- |
| `STAGES` | five rows | One row per band. No row has a `target` |
| `STAGES[].tithing` | `10`, `30` on the last | Gated before the cast; under it the run stops |
| `STAGES[].needs_weapon` | Consecrate Weapon only | The band that stops an empty-handed run |
| `STAGES[].cast_timeout` / `cast_delay` | `2.0` / `0.5` | Paladin incantations are short; raise the delay if the log fills with the recovery line |
| `FIRST_BAND` | `40.0` | Under it the start-up line points at the trainer |
| `HAND_LAYERS` | `onehanded`, `twohanded` | The layers a trance wants empty. A shield sits on `onehanded` |
| `EQUIP_ATTEMPTS` / `_TIMEOUT` / `_POLL` | `3` / `2.0` / `0.2` | How long each stow or draw has to land |
| `HURT_FLOOR` | `0.5` | Fraction of max hits the run bandages under, and stops under if that fails |
| `BANDAGE` | `True` | Off is a run that simply stops when hurt |
| `BANDAGE_GRAPHIC` | `0x0E21` | Clean bandages; the bloodied ones are a different item |
| `BANDAGE_ATTEMPTS` / `_TIMEOUT` / `_CURSOR_TIMEOUT` | `4` / `8.0` / `1.0` | Applications per stretch, how long one has to finish, how long the cursor has to come |
| `HEAL_OUTCOME_TEXT` | guesses | Only explain the failures; the hits are the proof |
| `MAX_UNREAD_REPORTS` | `5` | How many unreadable stretches show the journal before it goes quiet |
| `JOURNAL_TAIL_SECONDS` / `_LINES` | `20.0` / `10` | How much of it they show |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each cast is appended. `""` records nothing |

### When it goes wrong

- **`out of tithing points (N/M)`**: tithe more gold. The run cannot.
- **`nothing in hand for Consecrate Weapon`**: draw a weapon and restart, or start past 45.0.
- **`could not put 0x… in the pack`** / **`could not draw 0x… again`**: the move did not land inside
  `EQUIP_TIMEOUT`. A pack at its item cap refuses the stow; a weapon that broke refuses the draw.
- **`the shard refuses meditation (blocked)`** with the weapon stowed: something else is in a hand
  layer this table does not name. Add it to `HAND_LAYERS`.
- **`hurt (N/M)`** after `bandaging`: the bandages could not keep up, or ran out. Stand further from
  anything Noble Sacrifice can find.
- **`no cursor for the bandage`**: the use raised nothing inside `BANDAGE_CURSOR_TIMEOUT`.
- **`outcome unreadable - carrying on`**: an attempt where the journal, the buff, the mana and the
  tithing all said nothing, and still said nothing at the late look. The first `MAX_UNREAD_REPORTS`
  of them print the journal underneath - if a line there names the outcome, put it in
  `OUTCOME_TEXT`. These are not the recovery refusals, which the journal names and which are never
  recorded: 43 of them across 1056 rows gained skill at 18.6%, against 18.2% for `fizzled` and 40.7%
  for `cast`, so they are rolls that happened and were read too late, not casts that never went off.

### Unverified

- Every wording apart from `noTithing` and the recovery line, which `buffs.py` measured on UOAlive.
- The `BuffIconType` names, read from the enum, and the `title` fallbacks that cover them.
- The band bounds and the `cast_timeout` figures. Nothing here has been timed against a paladin's
  incantations.
- Whether `API.MoveItem` to the pack unequips on this client, and whether `API.EquipItem` draws a
  weapon back by serial. `uo/tool.py` proves the draw for a pickaxe.
- That Holy Light and Noble Sacrifice spend mana with nothing in range, which is the only proof
  those two bands have.

## bowcraft.py

Trains Bowcraft/Fletching from 30 to cap by making whatever the current band gains on. It pulls wood
`BATCH_SIZE` at a time out of what you point at, logs and boards both, and sells to the nearest
bowyer every `SELL_AT` items.

**What you point at is a chest or a pack animal.** An item is a container, remembered by where it
stood; a creature is a pack animal, whose backpack is re-resolved every time because a pet walks.
ESC with nothing picked works through the wood you carry.

| Bowcraft | Makes |
| --- | --- |
| 30 – 60 | `LOW_BAND_ITEM`: a bow by default, fukiya darts the other way |
| 60 – 70 | crossbow |
| 70 – 80 | composite bow |
| 80 – 90 | heavy crossbow |
| 90 – cap | `HIGH_BAND_ITEM`: a repeating crossbow by default, a yumi the other way |

Ceilings are exclusive; the first row the value is under wins. Each cycle:

1. Read the skill. An uncovered band ends the run; a band change re-selects the row.
2. Sell once the pack holds `SELL_AT` products. A trip that buys nothing does not own the cycle.
3. Restock if under `RESTOCK_AT` wood, walking to an out-of-reach container. The pack is read first,
   so wood in a bag inside it is brought up before anything is fetched, then filled to `BATCH_SIZE`.
   When the shard refuses a move as too heavy and there is anything to sell, the run sells first;
   otherwise it crafts down what it has.
4. Open the craft menu with the fletcher's tools if one is not up.
5. Press the row, or `MAKE LAST` once the row is known.
6. Read the outcome from the journal, the gump's `NOTICES` panel and the pack, all three on every
   pass. A success in wording the table lacks is still a success.

When something cannot be read or acted on, the run prints the gump's text, the journal's last lines
and the wood in the pack by hue, twice per stretch.

**Wood is not one resource.** `Boards` and `Oak Boards` are different resources to the menu, which
spends only the type it is set to. `WOOD_TYPE` decides what a restock pulls and what counts as stock.
The type is read off the name first and off the hue when the tooltip has not arrived:

| Wood | Hue |
| --- | --- |
| regular | `0` |
| ash | `1191` |
| oak | `2010` |

A hue in neither table is reported as `unknown` with its hue in the `the pack holds …` line; add rows
to `WOOD_HUES` as you meet them. Wood of another type is put back where it came from while that
container is open (`RETURN_WRONG_WOOD`). To work oak, set `WOOD_TYPE = "oak"` and the menu's
material by hand.

**Finding the row.** Buttons are `1 + type + index * 20`: categories are type 0 (**1** Materials,
**21** Ammunition, **41** Weapons), the arrow on a `SELECTIONS` row is type 1, and `MAKE LAST` is
**47**, read off this shard's menu. `RECIPES` names the buttons for known rows; it is a shortcut, and
the pack is still what proves a craft. Anything else walks the categories: each is pressed until a
page lists the product, then each row's details page (its button plus one, which spends nothing) is
opened until one names the product, and the pack proves the craft. Rows carry on across the pages
the client splits a long category into, so `MAX_ITEM_ROWS` counts the category, not a page. A menu
with no details pages falls back to reading the row off `GetGumpContents` as the text past the last
category name, and a craft that added none of the product's graphics tries the next candidate, up
to `MAX_ITEM_PROBES`, then the next category. Matches are whole-row: `crossbow` is inside `crossbow
bolt`, and a substring match finds Ammunition first. Once a row has made the item,
every craft after is `MAKE LAST`, when the menu has that button; a band change, a worn tool or a
wrong graphic sends it back. A `RECIPES` button the menu does not have is never sent: the product
goes to the walk instead.

**Recognising the menu.** A gump naming `CRAFT_TITLE`, or one whose rows include a `CATEGORY_NAMES`
entry or `LAST TEN`, is the menu, wherever it sits among the open gumps. Any other gump is ignored
and reported once with its first line, never closed. Failing both, whatever the tools newly opened
is the menu, reported once: the title is a cliloc that `GetGumpContents` may answer nothing for.

| Outcome | What it means |
| --- | --- |
| `made` | The pack gained a product graphic. The only proof that counts |
| `failed` | The shard says the craft failed. Still a gain and still spends wood |
| `noMaterial` | Restocks next cycle. `MAX_NO_MATERIAL` with wood still in the pack ends the run naming it |
| `wrongRow` | Made something that is not the product. Next candidate row |
| `toolWorn` | Looks for another pair and re-selects the row |
| `skillTooLow` | Ends the run: the band table and the shard disagree |
| `noRow` | Ends the run: no row in any category made the product |
| `noTool` | Retried `MAX_NO_TOOL` times, then ends the run |
| `noGump` | The tools opened no menu. Retried the same way |
| `throttled` | Backs off, capped at `THROTTLE_BACKOFF_MAX` |
| `saving` | Sat out |

**What a craft spent** is measured by counting the pack either side, never read off `RECIPES`. Only
`WOOD_KINDS` (including arts `StockBook` learns by name) and `MATERIAL_GRAPHICS` are counted, and only
the lost side of the diff. A failed craft is read once the pack has moved and held still for a poll,
or after `REFUND_SETTLE`, because the refund lands after the failure line. The pack is only counted
when `DATA_PATH` is set.

### Before you run it

- **Bowcraft at `MIN_SKILL` or above**, and below the cap. The start-up line shows the cap.
- **Fletcher's tools in your pack**, and spares.
- **What you pick has to be reachable.** A container is pathfound to by its recorded spot, an animal
  by serial. Either one out of reach is skipped for that restock.
- **The bowyer is found by tooltip as well as by name**: *Alger* is titled *the bowyer* only in the
  tooltip, and the name pass alone reported *no bowyer within 18* next to one. `VENDOR_SERIAL`
  skips the search.
- **It sells from adjacent, through the vendor's context menu**, re-asking where the vendor is after
  each walk because a pathfind that ends early leaves you short. It sends the **Sell** entry matched
  by text, falling back to saying `vendor sell`, and waits for the pack to drop. It does not drive
  the sell gump, so **the auto-sell agent still has to be configured** for the bowyer.
- **`SELL_AT` counts amounts, not stacks.** Fukiya darts stack ten to a craft.

### What to set

| Setting | Default | What it is for |
| --- | --- | --- |
| `SKILL_NAMES` | `Bowcraft`, … | Tried in order |
| `MIN_SKILL` | `30.0` | Below this the run refuses to start |
| `LOW_BAND_ITEM` / `HIGH_BAND_ITEM` | `bow` / `repeating crossbow` | The two bands with a choice |
| `BANDS` | see above | Ceiling and product |
| `PRODUCTS` | table | Row name as the gump spells it, and the graphics it arrives as |
| `CATEGORY_NAMES` | `materials`, … | Where the group rows end and the item rows begin |
| `TOOL_GRAPHICS` / `TOOL_NAME_WORDS` | `0x1022` | Fletcher's tools. An art learned by name joins the set |
| `LOG_GRAPHICS` / `BOARD_GRAPHICS` | four arts each | A stack's art changes with size. An art learned by name joins its kind |
| `WOOD_KINDS` | logs, boards | What counts as material. One pool, reported apart |
| `WOOD_TYPE` | `regular` | The wood the menu is set to. The only wood pulled or counted |
| `WOOD_TYPES` / `WOOD_HUES` | oak, ash, … / `0`, `1191`, `2010` | Incomplete; the log names what is missing |
| `RETURN_WRONG_WOOD` | `True` | Put other wood back rather than carry it |
| `MATERIAL_GRAPHICS` | feathers, shafts | Non-wood a craft can spend, for the consumed rows |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each craft is appended, with what it spent. `""` records nothing |
| `BATCH_SIZE` / `RESTOCK_AT` | `300` / `25` | What a restock fills to, and what triggers one |
| `SELL_AT` | `20` | Products in the pack before a sell trip |
| `TOO_HEAVY_TEXT` | *That container cannot hold more weight* | The shard refusing a move for weight |
| `BOWYER_TITLES` / `SELL_PHRASE` | `bowyer`, … / `vendor sell` | Matched against name and tooltip, and what is said |
| `VENDOR_SERIAL` | `None` | Skip the search |
| `VENDOR_SCAN_RADIUS` / `VENDOR_RANGE` | `18` / `1` | How far it looks, and how close it stands |
| `SELL_ENTRY` / `VENDOR_STEPS` | `sell` / `3` | The context menu entry, and walks spent getting there |
| `MAX_PICKS` | `8` | A backstop; ESC ends the selection |
| `CONTAINER_RANGE` | `2` | How close it stands before it pulls |
| `CRAFT_TITLE` | `BOWCRAFT AND FLETCHING` | Recognises a gump already open. Never refuses one |
| `BUTTON_STRIDE` | `20` | Every derived button moves with it |
| `MAKE_LAST_BUTTON` | `47` | The one button not derived |
| `RECIPES` | table | `(category button, row button)` for known rows |
| `MAX_CATEGORIES` / `MAX_ITEM_ROWS` | `6` / `12` | How far the walk goes |
| `MAX_ITEM_PROBES` | `8` | Crafts spent finding the row before the category is written off |
| `CRAFT_TIMEOUT` / `CRAFT_SETTLE` | `10.0` / `1.5` | How long the shard has to answer, and the pack to show it |
| `MAX_SELL_MISSES` / `SELL_RETRY_AFTER` | `3` / `25` | Trips that bought nothing before trips pause, and cycles before asking again. Neither ends the run |
| `MIN_CRAFT_WOOD` | `10` | The largest recipe. Under this there is nothing to make |
| `MAX_NO_MATERIAL` | `3` | Refusals for material in a row, with wood in the pack, before the run ends |

### When it goes wrong

- **`the gump text does not name 'crossbow' on a row of its own`** then **`rows seen: …`**: the
  split missed the item rows. The run pays crafts to find the row instead. If the names are spelled
  differently, fix `PRODUCTS`; if the block is the group names, this shard emits labels the other
  way round.
- **`no category lists 'yumi'`** or **`could not find the SELECTIONS row`**: the name in `PRODUCTS`
  is not what the row says, or the item is not in this shard's menu. Open it by hand.
- **`the tools opened a gump that does not name BOWCRAFT AND FLETCHING`**: said once, and used
  anyway. `(no text)` is ordinary for a cliloc header.
- **`ignoring gump 0x… - it is not the craft menu`**: a gump the shard keeps up beside the menu.
  Harmless; the line says what it starts with. **`gump 0x… has no button 47`**: `MAKE_LAST_BUTTON`
  or a `RECIPES` entry is wrong for this menu, and the row is walked for instead of pressed blind.
- **`the button table is out of date for 'crossbow'`**: the `RECIPES` button made something else.
  The walk corrects it; fix the entry to save the crafts.
- **`unreadable outcome (n/5), check OUTCOME_TEXT`**: a success needs no wording; a refusal does.
- **`refused for materials - the gump says '…'`** with **`the pack holds 300 boards hue 0x7d1`**:
  the menu spends only the wood type it is set to. `0x0` is plain; anything else is a special wood.
  Set the menu's material or carry what it asks for.
- **`could not get next to 'Alger'`**: three walks did not land adjacent. It keeps crafting and
  tries again rather than selling from too far, which silently sold nothing before.
- **`the vendor bought nothing - is the auto-sell agent on?`**: `MAX_SELL_MISSES` in a row pause
  the trips.
- **`out of wood`**: what you picked is empty and the pack is under `MIN_CRAFT_WOOD`. A container
  it cannot reach shows as `restocking` cycles and the stall watch ends them.

### Notes

- The shard answers a craft in the gump's `NOTICES` panel as well as the journal; reading the
  journal alone spends `CRAFT_TIMEOUT` on every refusal.
- `API.GetSkill().Value` is a float percentage; the `src/training/` tables are in tenths and would
  be wrong by 10x.

### Unverified

- Whether the item rows are everything past the last category name. The pack diff covers it.
- Whether a row index is per-page or absolute once the list pages. Nothing here pages.
- Whether `GetGumpContents` resolves localized row names or hands back cliloc numbers. If the
  latter, every run walks the rows.
- Whether `API.RequestTarget` returning falsy is ESC, which ends the multi-pick.
- The product graphics are stock; a reskinned one reads every craft as `wrongRow`.

## tinkering.py

Trains Tinkering from 20 to cap on the iron ingots in your pack. There is no restock: it makes the
band's item until the pack is short of a craft, and does with it what the gump at the start says.
Everything under the loop is shared with `bowcraft.py`, which is where the craft menu, the row walk
and the outcomes are described.

| Tinkering | Makes | Ingots | Sells to |
| --- | --- | --- | --- |
| 20 – 30 | iron key | 3 | tinker |
| 30 – 40 | hammer | 1 | tinker |
| 40 – 45 | tongs | 1 | blacksmith or tinker |
| 45 – 95 | lockpick | 1 | provisioner |
| 95 – 111.8 | ring | 3 | jeweler |
| 111.8 – cap | fancy wind chimes | 15 | nobody: unloaded |

Ceilings are exclusive; the first row the value is under wins. Before the loop: the tools, then a
gump with **Sell**, **Unload** and **Keep**. Unload asks for the container; Sell asks for it only
when a band nobody buys from is ahead. A closed gump, no press in `OUTPUT_CHOICE.timeout`, or ESC at
the Unload cursor all mean keep. Each cycle:

1. Read the skill. An uncovered band ends the run; a band change re-selects the row and gives the
   sell trips a fresh start, since the vendor changes with it.
2. Selling, sell once the pack holds `SELL_AT` of the band's product. Only that product is counted:
   tongs left from the band before do not send the run to a provisioner that will not take them. A
   band with no buyer unloads every `DUMP_AT` instead, as `carpentry.py` does; with nothing picked,
   the run ends at `MAX_HELD`. Unloading, every band unloads at `DUMP_AT`. Keeping, the run ends at
   `MAX_HELD`. What is unloaded or counted toward `MAX_HELD` is only what the run made: a key carried
   in stays in the pack.
3. Stop when the pack holds fewer iron ingots than the band's recipe takes.
4. Open the menu with the tinker's tools, press the row or `MAKE LAST`, and read the outcome.

**Iron only.** The menu is left on iron, and only iron is counted or spent. Coloured ingots are
named from the tooltip, or from `INGOT_HUES` while it has not arrived, and reported as set aside.
A refusal for material with enough iron in the pack first lifts ingots out of any bag inside it,
then counts toward `MAX_NO_MATERIAL`, since a menu set to another metal is the one thing left.

### Before you run it

- **Tinkering at `MIN_SKILL` or above**, and below the cap.
- **Tinker's tools in your pack**, and spares.
- **Iron ingots in your pack.** A bag inside it is emptied up to the top level at the start.
- **Stand near the band's vendor**, within `VENDOR_SCAN_RADIUS`. The run asks for the vendor by
  the title in `VENDORS` and pauses the trips when nobody answers, the way `bowcraft.py` does.
- **The auto-sell agent has to be configured** for each product, per vendor.
- **Something to unload into**, in reach: the cursor asks for it on Unload, and on Sell when the
  wind chimes band is ahead. A trash barrel destroys them; a chest keeps them.

### What to set

| Setting | Default | What it is for |
| --- | --- | --- |
| `BANDS` | see above | Ceiling and product |
| `PRODUCTS` | table | Row name as the gump spells it, and the graphics it arrives as |
| `INGOT_COST` / `MIN_CRAFT_INGOTS` | table / `1` | When the pack is too short to try |
| `VENDORS` | table | Per product: the noun for the log, and the titles matched on name and tooltip. `None` when nobody buys it |
| `OUTPUT_CHOICE` / `OUTPUT_OPTIONS` | a sentence, three buttons | The gump at the start |
| `DUMP_AT` / `MAX_HELD` | `10` / `60` | Products before an unload, and where a keeping run, or a Sell run with nowhere to put the unsold, ends |
| `TOOL_GRAPHICS` / `TOOL_NAME_WORDS` | stock / `tinker` | An art learned by name joins the set |
| `INGOT_HUES` | nine rows | Names the ingots set aside |
| `CATEGORY_NAMES` | stock | Where the group rows end and the item rows begin |
| `RECIPES` | wind chimes | `(category button, row button)`. Copy the `is the row on button` lines in |
| `MAX_CATEGORIES` / `MAX_ITEM_ROWS` | `10` / `24` | How far the walk goes; the Tools group runs past twenty rows |
| `SELL_AT` | `10` | Products in the pack before a sell trip |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each craft is appended, with what it spent. `""` records nothing |

### When it goes wrong

- **`the pack holds no ingots, and one iron key takes 3 ingots`** at the start, or **`out of
  iron ingots`** later: what is in the pack is all it uses.
- **`the shard refused 40 ingots in the pack 3 times`**: the menu's material is not iron. The gump's
  own words are printed above it.
- **`no jeweler within 18`**: said once per band. Walk to one; the trips retry on their own.
- **`the gump text does not name 'iron key' on a row of its own`**: the row is spelled differently
  on this shard. `rows seen` lists what it read; fix `BANDS` and `PRODUCTS` to match.
- **`the pack holds 60 unsold and nothing was picked to unload into`**, or **`the pack holds 60 and
  nothing was picked to unload into`** on a keeping run: pick a container next time.
- **`nothing was pressed in 60s`**: the gump timed out, so everything is kept. Press faster, or
  raise `OUTPUT_CHOICE.timeout`.
- **`3 unloads in a row moved nothing`**: the container is full, locked down, or not a container.

### Unverified

- The tool graphics and every product graphic but the iron key and the hammer are stock art.
- `MAKE_LAST_BUTTON` and the button stride are assumed to be `bowcraft.py`'s, as the same gump.
- Whether the SELECTIONS row says `iron key` or `key`.
- On a page whose rows cannot be split from the text, `ring` is also inside `earrings`, `springs`
  and `key ring`, and the fallback substring match could settle on the wrong category.

## carpentry.py

Trains Carpentry from 0 to cap on the cheapest recipe each band still gains on. Wood is pulled from
what you point at the way `bowcraft.py` does it, and everything made goes into one more container
you point at, since no vendor buys a deed. Everything under the loop is shared with `bowcraft.py`,
which is where the craft menu, the row walk and the outcomes are described.

| Carpentry | Makes | Wood |
| --- | --- | --- |
| 0 – 11 | barrel staves | 5 |
| 11 – 36 | barrel lid | 4 |
| 36 – 40.7 | dartboard (south) | 5 |
| 40.7 – 42.1 | wooden box | 10 |
| 42.1 – 67.1 | dark wooden sign hanger | 5 |
| 67.1 – 70 | ballot box | 5 |
| 70 – 73.6 | bokuto | 6 |
| 73.6 – 98.6 | quarter staff | 6 |
| 98.6 – 103.9 | gnarled staff | 7 |
| 103.9 – 105 | tetsubo | 10 |
| 105 – 106.5 | black staff | 9 |
| 106.5 – 111.8 | easel (south) | 20 |
| 111.8 – 115 | plain wooden chest | 30 |
| 115 – 119.7 | rustic bench (south) | 35 |
| 119.7 – cap | display case (south) | 40, and 10 ingots |

Each ceiling is the row's minimum skill plus 25, where the stock recipe reaches 100% and stops
gaining. Ceilings are exclusive; the first row the value is under wins. Each cycle:

1. Read the skill. An uncovered band ends the run; a band change re-selects the row.
2. Unload once the pack holds `DUMP_AT` products. With nothing picked to unload into, the run ends
   at `MAX_HELD` instead.
3. Restock if under `RESTOCK_AT` wood, as `bowcraft.py` does. When the shard refuses a move as too
   heavy, the run unloads first. Out of wood with the pack short of the band's recipe ends the run.
4. Open the menu with a carpentry tool, press the row or `MAKE LAST`, and read the outcome.

**What is unloaded** is only what the run made: every addon is a deed, and the deed art is also a
house deed's, so nothing that was in the pack when the run started is ever moved. A trash barrel
destroys it; a chest keeps it.

### Before you run it

- **Carpentry below the cap**, with the power scrolls read for the bands past 100.
- **A carpentry tool in your pack**, and spares. Saw, planes, nails, froe, inshave and scorp are
  known by art and by name; a hammer only by art, since a smith's hammer carries the word too.
- **Wood in your pack or in what you pick.** Logs and boards both count; only `WOOD_TYPE` is spent.
- **Something to unload into**, in reach: a trash barrel in the house is the usual answer.
- **The display case needs 75 Tinkering** and ingots in the pack. It is the only row that gains
  past 119.7; without it the run stops there, refused for materials.

### What to set

| Setting | Default | What it is for |
| --- | --- | --- |
| `BANDS` | see above | Ceiling and product |
| `PRODUCTS` | table | Row name as the gump spells it, and the graphics it arrives as |
| `WOOD_COST` / `MIN_CRAFT_WOOD` | table / `5` | When the pack is too short to try |
| `DEED_GRAPHICS` | `0x14F0` | What every addon lands as |
| `TOOL_GRAPHICS` / `TOOL_NAME_WORDS` | stock / `saw`, … | An art learned by name joins the set |
| `CATEGORY_NAMES` | the wiki's groups | Where the group rows end and the item rows begin |
| `RECIPES` | wind chimes | `(category button, row button)`. Copy the `is the row on button` lines in |
| `MAX_CATEGORIES` / `MAX_ITEM_ROWS` | `12` / `48` | How far the walk goes; Furniture and the add-ons run to forty rows |
| `DUMP_AT` / `MAX_HELD` | `10` / `60` | Products before an unload, and the most kept with nowhere to put them |
| `MAX_DUMP_MISSES` | `3` | Unloads in a row that moved nothing before the run ends |
| `BATCH_SIZE` / `RESTOCK_AT` | `300` / `40` | What a restock fills to, and what triggers one |
| `MATERIAL_GRAPHICS` | ingots | Non-wood a craft can spend, for the consumed rows |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each craft is appended, with what it spent. `""` records nothing |

### When it goes wrong

- **`the gump text does not name 'dartboard (south)' on a row of its own`**: the row is spelled
  differently on this shard. `rows seen` lists what it read; fix `BANDS`, `PRODUCTS` and
  `WOOD_COST` to match. The addon rows are the likeliest: the wiki names them without the facing.
- **`no category lists 'dark wooden sign hanger'`**: the shard may not have the item. Put a
  Trinsic-style chair (15 wood, 42.1) in its place, and the ballot box from 47.3.
- **`the shard refused 300 boards in the pack 3 times`**: the menu's material is not `WOOD_TYPE`.
- **`the pack holds 60 products and nothing was picked to unload into`**: pick a container next time,
  or raise `MAX_HELD`.
- **`3 unloads in a row moved nothing`**: the container is full, locked down, or not a container.

### Unverified

- Every row name and product graphic is stock ServUO, none read off UOAlive. The walk finds a row
  by its text, so a wrong name costs categories walked, not wood.
- The ceilings assume the stock minimum-plus-25 gain window. A row that hits 100% success early has
  stopped gaining; move its ceiling down.
- Whether the wooden container engraving tool's ceiling is 100 on this shard. If it is, it covers
  75 to 100 for 4 wood and 2 ingots, cheaper than the staves.
- Whether a deed moved into a trash barrel is destroyed silently or asks first.

## inscription.py

Trains Inscription from 30 to cap on the spell scroll with the fewest reagents in each circle the
guides train through. Every scroll spends a blank scroll, one of each reagent and mana, so the run
meditates when the pool is short, pulls scrolls and reagents from what you point at the way
`carpentry.py` does, and asks at the start what to do with the scrolls it makes. Everything under the
loop is shared with `bowcraft.py`, which is where the craft menu, the row walk and the outcomes are
described; the meditation is `magery.py`'s.

| Inscription | Circle | Makes | Reagents | Mana |
| --- | --- | --- | --- | --- |
| 30 – 55 | 4th | lightning | mandrake root, sulfurous ash | 11 |
| 55 – 65 | 5th | magic reflection | garlic, mandrake root, spider's silk | 14 |
| 65 – 85 | 6th | reveal | bloodmoss, sulfurous ash | 20 |
| 85 – 94 | 7th | flamestrike | spider's silk, sulfurous ash | 40 |
| 94 – cap | 8th | resurrection | bloodmoss, garlic, ginseng | 50 |

Ceilings are exclusive; the first row the value is under wins. `SPELLS` carries every spell of the
fourth to eighth circles with its art and reagents, so swapping a band is one edit of `BANDS`. Before
the loop: the pen, the cursor for every container or pack animal holding scrolls and reagents, then a
gump with **Sell**, **Unload** and **Keep**. Unload asks for the container; a closed gump, no press in
`OUTPUT_CHOICE.timeout`, or ESC at that cursor all mean keep. Each cycle:

1. Read the skill. An uncovered band ends the run; a band change re-selects the row and says what it
   takes.
2. Sell once the pack holds `SELL_AT` of the band's scroll, or unload once it holds `DUMP_AT` scrolls
   the run made. Keeping them, the run ends at `MAX_HELD`.
3. Restock when the pack pays for fewer than `RESTOCK_AT` crafts: only the kinds the band spends,
   each filled to `BATCH_SIZE`. A move the shard refuses as too heavy unloads first. Short of a kind
   with none of it left in what you picked ends the run, naming the kind.
4. Meditate when the pool is under the band's mana, as `magery.py` does. `MAX_DRY` waits in a row
   that brought nothing end the run.
5. Open the menu with the pen, press the row or `MAKE LAST`, and read the outcome.

**The consumed rows** measure the pack either side of the craft, so a row lists the blank scroll and
each reagent by kind, and a failure lists what the shard kept. `noMana` is the one outcome the other
crafting scripts do not have: the pool is gated before the craft, so seeing it means the circle's
figure in `MANA_BY_CIRCLE` is under what this shard charges.

**What is sold or unloaded** is only what the run made: `keep_existing` remembers the scrolls in the
pack at the start, so a recall scroll you carried in is neither moved nor counted. The sell trip
counts the band's scroll by art, so it does count one you carried in.

### Before you run it

- **Inscription at 30 or above**, bought from an NPC mage or scribe, and below the cap.
- **A scribe's pen in your pack**, and spares.
- **Empty hands**, or meditation is refused and the run falls back on natural regeneration.
- **Blank scrolls and the band's reagents in your pack or in what you pick.** Blank scrolls weigh a
  stone each, which is why `BATCH_SIZE` is a hundred.
- **Selling:** stand within `VENDOR_SCAN_RADIUS` of a mage or scribe, with the auto-sell agent set
  for each scroll. **Unloading:** something to unload into, in reach; a trash barrel destroys them.

### What to set

| Setting | Default | What it is for |
| --- | --- | --- |
| `BANDS` | see above | Ceiling and spell. Any `SPELLS` row |
| `SPELLS` | forty rows | Row name as the gump spells it: circle, scroll art, reagents |
| `MANA_BY_CIRCLE` | stock RunUO | Mana a scroll of each circle costs; `noMana` says it is understated |
| `STOCK_KINDS` | nine rows | Blank scrolls and the eight reagents, by art and name words |
| `BATCH_SIZE` / `RESTOCK_AT` | `100` / `20` | What each kind is filled to, and the crafts left that trigger it |
| `OUTPUT_CHOICE` / `OUTPUT_OPTIONS` | a sentence, three buttons | The gump at the start |
| `SELL_AT` / `DUMP_AT` / `MAX_HELD` | `20` / `20` / `60` | Scrolls before a sell trip, an unload, or the end of a keeping run |
| `VENDOR_TITLES` | `mage`, `scribe` | Matched on the name and the tooltip |
| `MEDITATE` / `MEDITATE_TO_FULL` | `True` / `True` | As `magery.py` |
| `MAX_DRY` | `5` | Mana waits in a row that brought nothing before the run ends |
| `TOOL_GRAPHICS` / `TOOL_NAME_WORDS` | stock / `pen` | An art learned by name joins the set |
| `CATEGORY_NAMES` | UOAlive's paired circles, and the singles | Where the group rows end and the item rows begin |
| `RECIPES` | the five bands | `(category button, row button)` on UOAlive. Copy the `is the row on button` lines in for any other spell |
| `MAX_CATEGORIES` / `MAX_ITEM_ROWS` | `14` / `16` | How far the walk goes; UOAlive pairs the circles, sixteen rows over two pages |
| `DATA_PATH` | `skill-attempts.jsonl` | Where each craft is appended, with what it spent. `""` records nothing |

### When it goes wrong

- **`nothing picked, and the pack is short of 1 mandrake root for one lightning`**: carry the band's
  reagents, or pick a container holding them.
- **`out of 1 sulfurous ash - ...`**: the pack and everything you picked are out of that kind.
- **`refused for mana at N - raise MANA_BY_CIRCLE`**: this shard charges more than stock for the circle.
- **`mana is not coming back`**: meditation is refused or broken every time, and natural
  regeneration did not reach the figure inside `REGEN_TIMEOUT`. Empty your hands.
- **`the shard refused ... in the pack 3 times`**: everything the recipe takes is there and the shard
  still refuses, so the row pressed is another spell. Read `rows seen` and correct `BANDS`.
- **`the gump text does not name 'magic reflection' on a row of its own`**: the row is spelled
  differently on this shard. `rows seen` lists what it read; fix `BANDS` and `SPELLS` to match.
- **`no mage or scribe within 18`**: walk to one; the trips retry on their own.
- **`nothing was pressed in 60s`**: the gump timed out, so the scrolls are kept. Press faster, or
  raise `OUTPUT_CHOICE.timeout`.

### Unverified

- Every wording in `OUTCOME_TEXT` and `MEDITATE_OUTCOME_TEXT` but the trance line, the success and
  the failure, and every art: the pen, the blank scroll, the reagents and the scrolls are stock
  RunUO, none read off UOAlive.
- Whether the row says `magic reflection` or `magic reflect`.

### Notes

- UOAlive's menu pairs the circles: **1** First - Second, **21** Third - Fourth, **41** Fifth -
  Sixth, **61** Seventh - Eighth, then Necromancy, Other and Mysticism. `GetGumpContents` hands it
  back as one line, every page included, and the row buttons of the second page are in the gump
  from the start: lightning is row 13 of Third - Fourth, button 262, without turning a page.
- A success says `You inscribe the spell and put the scroll in your backpack` and a failure
  `You fail to inscribe the scroll, and the scroll is ruined`, both in the gump's NOTICES panel
  only, never in the journal. The notice is read off `GetGumpContents` as well as
  `GumpContains`, and the unreadable report drops the Meditation and Focus gains that the spent
  mana's regeneration writes over it.
- The scroll art is `0x1F2D` plus the spell id: stock RunUO has reactive armor out of sequence
  at `0x1F2D` and every later scroll one under `0x1F2E` plus the id. Lightning reads `0x1F4A`
  (8010) on UOAlive, which is that formula. A made whose table art never lands is still checked
  against the whole pack, and a new art whose name says the product is taken as it for the rest
  of the run, with a line naming it to put in `SPELLS`.
- The blank scroll is `0x0EF3` or `0x0E34`, the same scroll turned the other way.
- The mana figures, and whether the shard checks mana before or after spending the reagents.
- `MAKE_LAST_BUTTON` and the button stride are assumed to be `bowcraft.py`'s, as the same gump.
- Whether a mage buys scrolls on this shard, and which. Unload is the safe answer.
- Whether the craft menu survives the meditation trance being used behind it.

## bod.py

Fills one Blacksmithing bulk order deed, small or large. Target the deed; the run reads the request
off the tooltip, makes one piece to prove the row, then `MAKE NUMBER`s the rest with the tongs in
your salvage bag, hands the bag to the deed's *combine with contained items*, salvages what the deed
would not take, and goes round until the count reaches the total. A large deed is that once per
entry, with each filled small combined into the large one. Nothing is restocked.

The tooltip lines read are `amount to make`, `<item>: <done>`, `All items must be exceptional` and
`All items must be made with <material> ingots`; no material means iron.

**Pre-flight.** Before the first craft, unless `CHECK_BEFORE_START = False`, either of these stops
the run with the numbers:

- Ingots: `INGOT_COST` per piece times pieces owed, of the deed's material, counted by name then
  hue. An item the table lacks is said and not checked. An exceptional deed will take more.
- Tool charges: every smith tool's `Uses Remaining` summed against the pieces owed. A tool without
  that line is said and not checked.

Each cycle:

1. Check the stop conditions: dead, or the stop button. Sit out a save.
2. Done when the count reaches the total.
3. Count the pieces the deed would take, anywhere in the pack. Each tooltip is read once: the name
   must be the deed's item, with the material folded in or on its own line, and `exceptional` when
   the deed says so. Stacks and bags are never asked. A refused piece is never offered again.
4. Combine if any are waiting: open the deed, press *combine with contained items*, answer the
   cursor with the bag. The pieces leaving the bag are the proof and the count; the wording is read
   only when none left, because a mixed bag gets a refusal per piece alongside the successes. Then
   `Salvage All` the bag if it holds judged pieces the deed did not take.
5. Otherwise craft. The first time, one piece off the `RECIPES` row, or the row the page's text
   names, so a wrong row costs one item's ingots; its tooltip proves the row. Nothing is pressed on
   a guess: a row that made something else, or a page naming no row, stops the run with what it saw.
   After that, the row's details page, `MAKE NUMBER`, and the number owed typed into the prompt.
   The auto craft says nothing when it ends, so the batch is counted from the pack and the failure
   lines, and `BATCH_IDLE` seconds of silence ends it. A refusal mid-batch presses `CANCEL MAKE`.

So a deed for ten exceptional axes makes ten, combines the seven exceptional ones, salvages three,
and makes three more. Out of ingots with pieces waiting, they go in before the run ends.

| Outcome | What happens |
| --- | --- |
| `combined` | Counted by the pieces that left. The deed is re-read for up to `REREAD_SETTLE` and the larger count wins |
| `full` | Ends the run |
| `notRequested`, `notExceptional`, `wrongMaterial` | Nothing left the bag. Every offered piece is left there and never offered again, since the shard does not say which it meant. `wrongMaterial` re-selects the menu's material |
| `notInPack` | Ends the run: the deed or the bag is not in your backpack |
| `noCursor` | `MAX_NO_CURSOR` of them end the run |
| `made`, `failed` | The proving craft. Both spend ingots |
| `batch` | A batch ended, by count or by going quiet. The log says how many it made and failed |
| `wrongRow` | Ends the run naming what it made; fix `RECIPES` |
| `noMaterial` | Ends the run naming the ingots in the pack and the pieces still owed |
| `noAnvil`, `skillTooLow`, `noRow`, `noMaterialRow` | End the run with the reason |
| `toolWorn`, `noTool`, `noGump`, `throttled`, `saving`, unreadable | As `bowcraft.py` |

### Large deeds

A large deed lists several items at one size, quality and material, and is filled with filled small
deeds of each. The run reads the entries still at 0, reuses matching small deeds already in the
pack (the fuller one when there are two), runs the pre-flight over every pending small at once, and
only then uses the Bulk Order Deed Box for the entries with no small: the large deed goes into the
box, the box is double-clicked, and the run waits for the large deed to be back with new deeds
beside it. The box is used at most once a run. Each small is filled in the large deed's order, then
the large deed is opened and *Combine this deed with the item requested* is answered with the filled
small; the small leaving the pack is the proof. The run stops when every entry reads done.

| Large combine reply | What happens |
| --- | --- |
| `The orders have been combined.` or the small deed gone | Next entry |
| `The maximum amount of requested items have already been combined` | Taken as done |
| `is not completed`, `not a bulk order for this large request`, `must be of exceptional quality`, `same resource type`, `different requested amounts` | Ends the run naming the small deed: the match was wrong |

### Before you run it

- **The deed in your backpack.**
- **For a large deed, the Bulk Order Deed Box in your backpack too**, empty, and the gold it
  charges. The smalls it makes land in your main pack.
- **Stand next to an anvil and a forge.** The first refusal stops the run.
- **Ingots of the kind the deed names.** The run never restocks.
- **A salvage bag in your pack with the tongs in it.** The run opens it at start; the shard drops
  each craft beside the tool, which is what makes the bag the thing the deed is aimed at. Tongs are
  used ahead of a hammer. Without a bag the pack itself is offered and nothing is salvaged.
- **Exceptional deeds produce leftovers.** They stay in the bag until the deed is full, then
  `Salvage All` turns them back into ingots. Watch the weight on a plate deed.
- **Tick "Disable this popup (use chat instead)" on TazUO's Server Prompt dialog** the first time.
  The answer goes through either way, but the dialog otherwise stays up for the whole batch.

### What to set

| Setting | Default | What it is for |
| --- | --- | --- |
| `SKILL_NAMES` | `Blacksmithy`, `Blacksmith` | For the start-up line only |
| `TOOL_GRAPHICS` / `TOOL_NAME_WORDS` | hammer, tongs, sledge / `tongs`, `smith` | Whole words, so a war hammer is not a tool |
| `TOOL_PREFERENCE` / `TOOL_BAG_NAMES` | tongs / `salvage bag` | Which tool wins when several are found, and the bag opened at start |
| `INGOT_GRAPHICS` / `INGOT_HUES` | stock | How ingots are counted and told apart. An unknown hue is reported as a hue |
| `CHECK_BEFORE_START` / `INGOT_COST` / `USES_TEXT` | `True` / the wiki table / `uses remaining` | The pre-flight: ingots per piece from uoalive.com/wiki/Blacksmithy, and the charges line |
| `DEED_GRAPHICS` / `DEED_NAME_WORDS` | `0x2258` / `bulk order deed` | How small deeds in the pack are found for a large one |
| `BOX_NAMES` / `BOX_TIMEOUT` | `bulk order deed box` / `10.0` | The box, and how long it has to put the deeds in the pack |
| `LARGE_COMBINE_BUTTON` / `LARGE_COMBINE_TEXT` | `2` / stock | The large deed gump's combine, and the shard's replies |
| `PLAIN_MATERIAL` | `iron` | What a deed with no material line wants |
| `MATERIAL_ALIASES` | `shadow iron` → `shadow` | How the menu row and tooltip may shorten the wording |
| `MATERIAL_ORDER` | iron … valorite | The material page's rows in stock order, pressed blind when the page's text cannot be split |
| `DEED_TEXT` | stock | The tooltip lines, lower-cased fragments |
| `CATEGORY_NAMES` | both spellings | Where the group rows end |
| `BUTTON_STRIDE`, `*_BUTTON_TYPE` | 20, 0/1/5/6 | A row's details button is its row button plus one; the material page is `1 + 6`, its rows `1 + 5 + i * 20` |
| `BOD_COMBINE_BUTTON` | `4` | *Combine this deed with contained items*; 2 is the one-item combine |
| `MAKE_NUMBER_BUTTON` / `CANCEL_MAKE_BUTTON` | `2` / `227` | On the row's details page, and on the menu |
| `PROMPT_DELAY` | `0.8` | How long the number prompt takes to arrive |
| `CRAFT_INTERVAL` / `BATCH_IDLE` | `3.0` / `8.0` | A batch's time budget per piece, and the silence that ends one |
| `SALVAGE_AT_END` / `SALVAGE_ENTRIES` | `True` / `Salvage All` | The bag's context entry once the deed is full |
| `DONE_SOUND` | `afplay` on a system sound | Played once on this Mac when the deed is filled. `[]` turns it off |
| `RECIPES` | the reference table | `(category button, row button)` per item as the deed names it. The only way an item the page's text does not name is crafted |
| `OPL_TIMEOUT` / `OPL_ASKS` | `2` / `3` | How long a tooltip has to arrive, and how many times one item is asked |
| `REREAD_SETTLE` | `3.0` | How long the deed's tooltip has to show a combine the pack proved |
| `MAX_NO_CURSOR` | `3` | Combine presses that raised no cursor before the run stops |
| `OUTCOME_TEXT` / `COMBINE_TEXT` | stock ServUO | Wordings for a craft and a combine |

### When it goes wrong

- **`not enough: 140 iron ingots for 10 axe (14 each), and the pack holds 120`** or **`not enough:
  6 uses left across 2 tool(s) for 10 pieces owed`**: the pre-flight. Load more, or set
  `CHECK_BEFORE_START = False`.
- **`no ingot cost is known for '…'`**: add the item to `INGOT_COST`; the run goes on unchecked.
- **`no bulk order deed box in the pack`**: buy one, or put the small deeds in the pack yourself.
- **`the large deed did not go into the box`** or **`the box put no deeds in the pack within
  10s`**: the move was refused (the box holds another deed, or is not yours) or the box did nothing
  (no gold). The second line says whether the large deed came back out.
- **`still no small deed for … after the box`**: the box made deeds the run could not match. Open
  one and compare size, quality and material.
- **`the large deed refused the small deed 0x… (notComplete)`**: the small reads full to the run
  and not to the shard. Open it; if short, run it again.
- **`is not a deed this run can fill: could not read it`**: correct `DEED_TEXT` from what it
  printed. An empty tooltip had not arrived; run it again.
- **`the material page has no rows past a category name - pressing row N … on the stock
  order`**: none of `CATEGORY_NAMES` is on the page as a line of its own. Add the group names;
  until then `MATERIAL_ORDER` is pressed blind, which is right on a stock shard.
- **`no material row reads 'valorite' - the page says …`**: the page names it differently, or the
  character lacks the skill and the shard left it off. Add the wording to `MATERIAL_ALIASES`.
- **`the deed's gump raised no cursor 3 times`**: button 4 is not the container combine here.
  Count the buttons and set `BOD_COMBINE_BUTTON`.
- **`button 62 made 'ringmail leggings', not a 'ringmail tunic'`** then **`the row for … made
  something else`**: the `RECIPES` entry is wrong. Correct it, or drop it and let the walk find the row.
- **`no row on button 1's page reads '…'`**: the item is not in `RECIPES` and the page's text does
  not name it. Add the entry from the page text in that line.
- **`the deed took none of the 5 offered (notRequested)`** on pieces that plainly are the item:
  the deed wants another graphic of the same name (female plate, gargish). Stop it and read the
  SELECTIONS rows.
- **`the bag's menu has no Salvage All entry`**: set `SALVAGE_ENTRIES`, or salvage by hand.
- **`the batch of 7 made nothing`** with the gump and journal text: `MAKE NUMBER` did not start.
  The details button is not the row's plus one, `MAKE_NUMBER_BUTTON` is not 2, or the prompt
  arrived after `PROMPT_DELAY`. Counted unreadable and tried again.
- **`batch of 10: 4 made, 2 failed (batch)`** with fewer than asked: the batch went quiet for
  `BATCH_IDLE`. The next cycle asks for what is still owed.
- **`the deed's tooltip is behind the count`**: said once; the pack proved the combine.
- **`the new item's tooltip did not arrive - taking the craft as the product`**: trusted. A wrong
  row shows as `notRequested` at the combine.

### Notes

- `API.ItemNameAndProps` is the whole of the deed; the gump is opened only to press combine.
- `GetGumpContents` hands the smith menu back as one line, `<CENTER>` tags and all, so rows cannot
  be told from labels; that is why `RECIPES` is how rows are found. The material rows are the
  exception: they read `IRON (1587) DULL COPPER (111) …` after the `DO NOT COLOR` toggle and split
  on the counts.
- The material page is the craft menu's own gump, same id, pressed like a category.
- The deed gump is the one that says bulk order among the open gumps, or the one the deed newly
  opened; it is closed after the combine. The menu is never closed for it.
- `API.ItemsInContainer(API.Backpack, True)` reads into the bag once it has been opened, which is
  why it is opened at start and the pieces need no second cursor.

### Unverified

- The material page's order is stock on a live run: `IRON`, `DULL COPPER`, `SHADOW`, `COPPER`,
  `BRONZE`, `GOLD`, `AGAPITE`, `VERITE`, `VALORITE`. Unverified is whether a character without the
  skill for a metal still sees its row, which the index rests on.
- Button 7 for the material page, 6/26/46… for its rows, and button 4 for the container combine.
- Whether the deed takes the bag as the container, and whether it stops at the total or says
  `provided more than` for the extras.
- Whether `Salvage All` needs a forge in reach, and what it does with pieces the deed left.
- Whether the deed tooltip re-reads after a combine. If not, every combine says `behind` once.
- The pack check accepts a `Container` or `RootContainer` of either the backpack or you. A deed in
  a bag inside the pack passes it, and the shard's own refusal ends the run instead.
- The `exceptional` line and the folded material name, stock ServUO wording.
- That the auto craft keeps the material the menu was set to. The details button, the prompt and
  `API.PromptResponse` are seen working on a live run.
- The large flow, all of it: that `API.MoveItem` into the box is accepted, that `0x2258` is the
  deed art here, that button 2 on the large gump is the combine, and the stock ServUO wordings.

## inventory.py

Target a bag or chest, and every item in it is written to `DATA_PATH`, one JSON line each. The
backpack itself, a bag inside it, or a chest on the ground all serve; ESC at the cursor stops.

1. The container is opened, then listed. With `RECURSIVE` each bag inside is opened and listed too,
   breadth first, up to `MAX_CONTAINERS`.
2. The tooltips are asked for `OPL_BATCH` items at a time, `OPL_WAIT` apart, and each is read with
   `OPL_TIMEOUT` to arrive. A row is written the moment its tooltip is read, so a stop halfway keeps
   what was read.
3. What did not come is asked again `RETRIES` times, then written anyway with the client's name,
   `"lines":[]` and `"unread":true`.
4. The closing line says how many rows went out, from how many containers, and how many had no
   tooltip.

```json
{"v":1,"scan":"0x40001000/1757030000123","t":1757030042.5,"char":"Kaldor",
 "bag":"0x40001000","serial":"0x40012345","graphic":"0xf61","hue":0,"amount":1,
 "container":"0x40001000","name":"Longsword","tier":"Greater Artifact",
 "durability":{"current":45,"max":50},"weight":3,
 "props":{"antique":true,"hit chance increase":15,"weapon damage":[13,15],"weapon speed":2.5},
 "lines":["Longsword","Greater Artifact","Durability 45 / 50","Weight: 3 Stones",
          "Hit Chance Increase 15%","Weapon Damage 13 - 15","Weapon Speed 2.5s","Antique"]}
```

`scan` is `bag serial/run-start-ms`, the same for every row of one run. `container` is the bag the
item sits in, so a nested bag reconstructs. `lines` is the tooltip as read, and the rest is parsed
off it: the first line is `name`; a line that is one of `TIER_TEXT` is `tier`; a line starting with
`DURABILITY_TEXT` gives `current` and `max`; one starting with `WEIGHT_TEXT` gives the number.
Everything else lands in `props`, keyed by the lowercased text before the number: a trailing number
(`15%`, `+20%`, `-10`, `2.5s`) is the value, a `13 - 15` is a pair, a line with a colon and no number
keeps its text (`"skill required": "Swordsmanship"`), a line starting with `PREFIX_TEXT` keeps the
rest as text (`"crafted by": "Kaldor"`), and a line with none of that is a flag (`"antique": true`).
`tier`, `durability` and `weight` are `null` where the tooltip has no such line. Keys in `props` are
sorted, and a repeated key keeps the last value.

### What to set

| Setting | Default | What it is for |
| --- | --- | --- |
| `DATA_PATH` | `bag-items.jsonl` | Where each row is appended. `""` records nothing. A bare name lands in TazUO's working directory |
| `RECURSIVE` | `True` | Open and read the bags inside the bag |
| `MAX_CONTAINERS` | `50` | How many containers one run opens, the target included |
| `OPEN_DELAY` | `0.6` | Seconds after opening a container before it is listed |
| `OPL_BATCH` | `25` | Tooltips asked for in one request |
| `OPL_WAIT` | `1.0` | Seconds given a batch to arrive |
| `OPL_TIMEOUT` | `1` | Whole seconds one read waits for its tooltip. The API takes an int |
| `RETRIES` | `2` | Further ask-and-read rounds for what did not come |
| `PICK_TIMEOUT` | `30.0` | How long the opening cursor waits for you |
| `TIER_TEXT` | the ServUO ItemPower lines | Matched as the whole line, case ignored, kept as the shard wrote it |
| `DURABILITY_TEXT` | `["durability"]` | Line starts read as current and max |
| `WEIGHT_TEXT` | `["weight"]` | Line starts read as the weight |
| `PREFIX_TEXT` | `["crafted by"]` | Line starts whose remainder is text |

### When it goes wrong

- **`nothing targeted - stopping`**: the cursor timed out or was declined.
- **`0x... is not an item - target a bag or chest`**: a mobile or the ground was targeted.
- **`reading 0 items`**: the container listed empty. A bag out of reach opens nothing; stand next
  to a chest, and raise `OPEN_DELAY` if the client is slow to draw it.
- **`N without a tooltip`**: the rows are there with `"unread":true`. Raise `OPL_WAIT` or
  `RETRIES`, or run it again on the same bag: the tooltips the client has seen once come back at
  once.
- **`cannot write ...`**: said once; the run reads on without recording. Check `DATA_PATH`.

### Unverified

- That `UseObject` on a bag inside a chest on the ground opens it for the listing, as it does for
  one in the pack.
- The ItemPower wording on this shard. `TIER_TEXT` carries both `Minor` and `Lesser` because the
  stock names are not certain; a tier that does not match lands in `props` as a flag, so the
  tooltip line is never lost.
- Whether tooltips here carry a `Weight:` line at all, and whether durability reads `45 / 50`.
