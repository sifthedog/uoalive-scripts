# taming — Animal Taming

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/tame.js` | Target one animal, then work through every animal of that type in reach: tame it, rename it, and set it on something |

## What it does

Target one creature. That sets the **type** the run hunts for — see below — and it works through
everything of that type in reach before asking you for another. Per cycle, on whichever animal it is
working:

1. **Check the stop conditions** — dead, or hurt below `HEALTH_FLOOR`.
2. **Sit out a world save** if one is running, without charging the refusals to anything.
3. **Check the creature still resolves**, and **chase it** if it is further than `TAME_RANGE` — see
   below.
4. **`useSkill(AnimalTaming, serial)`** — the creature is passed to the call, not answered into a
   cursor of its own.
5. **Wait twice**: once for the shard to say the attempt started or to refuse it, then again for the
   attempt to resolve — both in slices, following the animal between them.
6. **Sleep for the current pace**, which is not a constant — see below.

When the animal accepts you it is renamed to `PET_NAME` and then dealt with according to
`AFTER_TAME`, and the run moves to the next animal of the same type. The cursor comes back up only
when there are none left in sight. **ESC ends the session.**

| Outcome | What happens |
| --- | --- |
| `tamed` | Counted, then renamed and dealt with. The cursor comes back up |
| `failed` | The skill check failed, which still rolled the skill. The ordinary cycle |
| `pending` | The attempt started and never resolved. Counted up to `MAX_PENDING`, then stops the run |
| `angry` | Waits `ANGRY_DELAY` up to `MAX_ANGRY`, then gives up on this animal |
| `contested` | Another tamer has it. Counted up to `MAX_CONTESTED` |
| `tooFar` | Chases it. `MAX_AWAY` chases that gain no ground give up on this animal |
| `throttled` | The shard's own timer. The pace is *raised* as well as backed off from |
| `saving` | Waits the save out and carries on |
| `hopeless`, `notAnimal`, `alreadyTame`, `unskilled` | Gives up on this animal. The cursor comes back up |
| anything else | Counted unreadable and said, but never stops the run |

Only the guards, `throttled` and `pending` end the **session**. Everything else that goes wrong ends
the current **animal**.

### Hunting the rest

The animal you target by hand sets the type — its **body graphic, in any colour** — and from then on
the run finds the next one itself with
`client.findAllMobilesOfType(graphic, null, null, null, HUNT_RADIUS)`. Only when nothing of that type
is left in sight does the cursor come back, and whatever you pick then sets the type again.

Left out of the hunt:

- **Anything the run has already finished with**, tamed or given up on. Held in a list that lasts
  until the script is re-pasted. Without it the scan picks the same unreachable animal straight back
  up and the run makes no progress.
- **Anything that is already a pet** — `isRenamable` is true for pets and followers, which is every
  animal a `kill` or `keep` run has kept.
- **Anything named `PET_NAME`.** Releasing hands the follower slot back but leaves the name, so this
  is the only thing standing between a released `sifinha` and being tamed over and over.
- Anything dead, anything the client has stopped tracking (`graphic` reads 0), and anything further
  than `HUNT_RADIUS`.

Distance is measured here rather than left to the scan's own `range` argument, whose meaning next to
those arguments is undocumented — the same reasoning as [`sweep/floor.ts`](../sweep/floor.ts). Names
read empty until the client has tooltip data, so the animal about to be taken is asked for by
tooltip; the others are not, which keeps it to one lookup per animal rather than one per scan.

`HUNT_RADIUS = 0` turns the hunt off and asks for every animal.

### The chase

An animal wanders while you tame it, so the walk is a chase rather than a trip to a fixed spot:
[`lib/entity.ts`](../lib/entity.ts)'s `approach` re-reads where the animal is before every step, and
`player.run` is what it steps with.

- **It closes to `TAME_APPROACH` (1), not to `TAME_RANGE` (2).** Stopping at the range the loop tests
  against leaves one step by the animal enough to break it again, so every cycle became a walk. It
  also means a `tooFar` at distance 2 now moves you, where before the walk returned as already-close.
- **`MAX_AWAY` counts chases that gained nothing, not chases that failed to catch it.** A chase that
  closed the gap from eight tiles to three is progress and buys another cycle, so something that
  keeps walking off is followed for as long as you are gaining on it.
- **`TAME_MAX_STEPS` (40) is its own**, higher than the shared `MAX_STEPS`, because an ore vein stays
  where it was scanned and an animal does not.
- **The chase carries on during the attempt.** An attempt blocks for as long as the shard takes to
  answer — up to `TAME_START_TIMEOUT` plus `TAME_RESOLVE_TIMEOUT` — and the animal walks the whole
  time. So both waits are taken in `TAME_WAIT_SLICE` slices with a step between them, rather than one
  long block with the script stood still. A line that lands mid-step is not lost:
  `waitForTextAny` reads the journal as it stands, which is the same property the two-stage wait
  already relies on.
- A chase that never lands an attempt is ended by the stall watch after `STALL_STOP` cycles.

### What happens to each tame

Every success is renamed to `PET_NAME`, and then `AFTER_TAME` decides what becomes of it.

| `AFTER_TAME` | What happens |
| --- | --- |
| `kill` | Ordered to attack. The cursor the shard raises is **left up for you to click** |
| `release` | Let go, so the follower slot comes back |
| `keep` | Neither. It stays yours and stays where it is |

None of the three has a call in the client API, so all of them go through the creature's **context
menu** — `popupMenu` for the entry, `prompt` for the name a rename asks for. Entries are matched on
their text rather than by index, so a shard that words them differently costs a log line instead of
pressing the wrong thing.

- **Rename first.** Once it is not your pet the Rename entry is gone from its menu.
- **A miss ends the animal, never the session.** `could not rename '…' (noEntry) - carrying on`, and
  the cursor comes back up. The totals are repeated once at the end of the run.
- `PET_NAME = ''` skips the rename.

#### Ordering the kill

The script gives the order and then gets out of the way: **what the pet attacks is always your
click.** Nothing here answers the cursor.

- The cursor is waited for with `target.wait`, then `target.open` is polled until you have answered
  it, for up to `KILL_PICK_TIMEOUT`. The taming cursor comes back only after that.
- A live cursor is cancelled before the order goes in, or `target.wait` would answer for whatever was
  already up.
- **You do not have to click.** After `KILL_PICK_TIMEOUT` the run says `unanswered` and carries on;
  the cursor is tidied up by the next taming prompt, which cancels a stale one before it asks.
- **Keeping the tames fills the follower slots**, and a shard with no room refuses every attempt
  without saying why — so the run stops itself with `no follower slots left`.

#### Releasing

- **The proof of a release is `isRenamable` going back to false**, polled for up to
  `RELEASE_TIMEOUT` — the same flag the tame itself is read off, in the other direction.
- **The confirmation gump is looked for three ways**, because one client does not report it the way
  the next one does: the serial the server sent it with (`Gump.lastSerial` moving), then whatever
  `Gump.last` holds whether or not the serial moved, then `RELEASE_CONFIRM_TEXT` by wording. Nothing
  else in a taming cycle opens a gump, so the first of those to answer is the right gump.
- **A confirmation that could not be answered is closed** before the animal is written off: it is
  modal on some clients and would refuse the context menu of every animal after it.
- **Which button means yes is worked out, not configured.** The release is tried once per id in
  `RELEASE_CONFIRM_BUTTONS` until the animal is actually let go; the id that worked is logged and
  reused for the rest of the run, so only the first animal costs more than one press.
- **The release entry going missing is the better proof.** It is on the menu only while the animal is
  yours, so an entry that has gone since the last press means the press worked — which is what
  carries the run when the client's `isRenamable` does not refresh.

### The pace

There is no call that reports the shard's skill delay, and guessing it low re-arms the very timer it
is waiting out. So `TAME_DELAY` is a **floor**, not the cadence: [`lib/pace.ts`](../lib/pace.ts) adds
`PACE_STEP` every time the shard refuses and takes one back only after `PACE_EASE_AFTER` attempts
have landed.

### Before you paste it

- The animal must be **wild** and within your skill.
- Nothing needs to be in the pack, and nothing is picked up.
- **A failed tame can turn the animal on you.** This script does not fight, heal or run — it stops at
  `HEALTH_FLOOR`. Do not leave it on something that can kill you.
- It walks to the animal, so stand somewhere the path is not a fence.
- **A released animal is wild again** and can turn on you the same way a failed tame can.
- With `AFTER_TAME = 'kill'` the run **stops to wait for your click** after every tame, and the pets
  stay yours until the follower slots run out.

## How to run it

```bash
npm run build
```

Then paste `dist/tame.js` into the client's script editor and target the animal when the cursor comes
up. Target another after each tame; press ESC to finish.

## What to set

Everything lives in [`config.ts`](config.ts).

| Setting | Default | What it is for |
| --- | --- | --- |
| `TAME_START_TIMEOUT` | `3000` | How long the shard has to say the attempt started, or refuse it |
| `TAME_WAIT_SLICE` | `500` | How long a slice of either wait is, and so how often the animal is followed |
| `TAME_RESOLVE_TIMEOUT` | `15000` | How long a started attempt has to resolve |
| `TAME_RANGE` | `2` | Walked into before every attempt |
| `TAME_DELAY`, `PACE_STEP`, `PACE_MAX`, `PACE_EASE_AFTER` | `1500`, `400`, `8000`, `5` | The pace floor, and how it learns the shard's timer |
| `ANGRY_DELAY` / `MAX_ANGRY` | `10000` / `10` | How long an angry creature is left, and for how many cycles |
| `HUNT_RADIUS` | `12` | How far it looks for the next of the type. 0 asks for every animal |
| `TAME_APPROACH` | `1` | How near the chase closes to, nearer than `TAME_RANGE` on purpose |
| `TAME_MAX_STEPS` | `40` | Steps one chase may take |
| `MAX_AWAY` | `10` | Chases that gain no ground before the animal is written off |
| `MAX_CONTESTED` | `20` | Cycles another tamer may hold it |
| `MAX_PENDING` | `10` | Attempts that start and never resolve before the run stops |
| `HEALTH_FLOOR` | `0.5` | Fraction of your health at which the run stops |
| `MAX_THROTTLED` | shared | Refusals in a row before the run stops. A backstop — the pace should get there first |
| `PET_NAME` | `'sifinha'` | What each tame is renamed to. Empty skips the rename |
| `AFTER_TAME` | `'kill'` | What becomes of each tame: `kill`, `release` or `keep` |
| `KILL_MENU_TEXT` | `['Kill', 'Attack']` | Menu entry for the order, matched as case-insensitive fragments |
| `KILL_CURSOR_TIMEOUT` | `2000` | How long the shard has to raise the cursor |
| `KILL_PICK_TIMEOUT` / `_POLL` | `60000` / `250` | How long you have to click the victim |
| `RENAME_MENU_TEXT`, `RELEASE_MENU_TEXT` | `['Rename']`, `['Release']` | Menu entries, matched as case-insensitive fragments |
| `RELEASE_CONFIRM_BUTTONS` | `[1, 2, 0]` | Release is retried with each in turn until the animal is let go |
| `RELEASE_CONFIRM_TEXT` | fragments | Wordings to find the gump by, when the serial does not identify it |
| `RELEASE_CONFIRM_TIMEOUT` / `_POLL` | `1500` / `150` | How long the confirmation gump has to arrive |
| `RELEASE_TIMEOUT` / `RELEASE_POLL` | `3000` / `250` | How long `isRenamable` has to go back to false |
| `MENU_TIMEOUT` / `PROMPT_TIMEOUT` | `2000` / `2000` | How long the context menu and the name prompt have to open |
| `OUTCOME_TEXT` | — | The shard's wordings. All guesses but two; see below |

## When it goes wrong

**`attempts kept starting and never resolving`** — the shard took the attempts and said nothing
within `TAME_RESOLVE_TIMEOUT`. Raise it.

**`outcome unreadable - carrying on`** — the shard words that result differently. Add the wording to
`OUTCOME_TEXT`.

**`shard says wait (n/20), now pacing at Nms`** — working as intended for the first few cycles. A run
of them that never stops means the real delay is above `PACE_MAX`.

**`could not rename '…' (noEntry)`**, **`could not order '…' to kill (noEntry)`** or **`could not
release '…' (noEntry)`** — the entry is worded differently, or is not on the menu at all. Log the menu
the shard sends and set `RENAME_MENU_TEXT` / `KILL_MENU_TEXT` / `RELEASE_MENU_TEXT`.

**`could not order '…' to kill (noCursor)`** — the entry was pressed and the shard raised no cursor.
Either it wants the order given another way, or `KILL_CURSOR_TIMEOUT` is short.

**`could not order '…' to kill (unanswered)`** — nobody clicked a victim inside `KILL_PICK_TIMEOUT`.
Working as intended if you walked away.

**`no follower slots left`** — every slot is taken, which is where `AFTER_TAME = 'kill'` or `'keep'`
ends up. Stable the pets, or switch to `'release'`.

**`could not release '…' (stillPet)`** — every id in `RELEASE_CONFIRM_BUTTONS` was tried and the
animal is still yours. Add whatever id the gump's yes button really is.

**`found no gump to confirm the release with - lastSerial A -> B, last …`** — none of the three ways
found it. The numbers are the diagnosis: `A -> B` unchanged means the client never tracked the gump,
and `last null` means it did not hold it either. Add the gump's actual wording to
`RELEASE_CONFIRM_TEXT`.

**`the release gump does not admit to a button N - pressing it anyway`** — `hasButton` disagrees with
the candidate list. Harmless on its own; it only matters alongside a `stillPet`.

**`could not get near '…'`** — `MAX_AWAY` chases in a row gained no ground at all. Something is in
the way, or the animal is genuinely faster than you.

## Notes on the shard

Written against UOAlive.

- **An attempt resolves in two steps.** The shard says it started, then answers seconds later, so
  [`tame.ts`](tame.ts) waits twice, each wait in slices. The second wait goes out over `RESOLUTION_TEXT` — the phrase list
  with the `starting` bucket removed — because the start line is still in the journal and a full list
  would match it again and spin. Filtered rather than cleared: a second `journal.clear()` can throw
  away a resolution that landed in the same tick.
- **`author` is left undefined on every wait**, because the shard routes these lines over the
  creature's head as object text rather than as System.
- **`isRenamable` is the proof that does not go through the journal.** It is true for pets and
  followers, so `false → true` across one attempt is a tame even when the wording was not recognised.
- **Distance is measured, not inferred.** The cycle closes the gap before attempting, so a wrong
  `tooFar` wording costs an unread outcome rather than a run that never closes the gap.
- **Renaming and releasing exist only on the context menu.** The typings have no rename call at all,
  only the read-only `isRenamable`, so `lib/menu.ts` asks for the menu and answers it by entry text.
- **The skill is not required to be readable.** Unlike the trainers, the goal here is a sentence, so a
  client that will not report Animal Taming costs a log line and nothing else.

### Known unverified

- **Every phrase in `OUTCOME_TEXT` but `tamed` and `failed`.** RunUO-family guesses; a miss shows up
  as an `unknown` outcome rather than a silent wrong turn.
- **`TAME_RESOLVE_TIMEOUT` of 15 seconds**, which is a guess at the ceiling of an attempt rather than
  a measurement. `MAX_PENDING` is what turns a wrong one into a diagnosable stop.
- **Whether `isRenamable` flips before the attempt returns.** If it does not, the fallback simply
  never fires and the journal carries the run.
- Whether this shard says anything at all when another tamer is working the same creature.
- **That a released animal keeps the name it was given.** The whole of the `PET_NAME` filter rests on
  it: if this shard clears the name on release, a `release` run will tame the same animals round and
  round, and the fix is `AFTER_TAME = 'keep'` or a shorter `HUNT_RADIUS`.
- **Which button of the confirmation gump means yes.** The gump itself is confirmed — this shard does
  ask — but the id is found by trying the candidates, and `tame: the release gump answers to button N`
  is what says which one won. Pin `RELEASE_CONFIRM_BUTTONS` to it once it is known.
