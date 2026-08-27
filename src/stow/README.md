# stow — watch the pack and stow what you picked

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/stow.js` | Target the items to watch and a container, then move each one out of your pack as it turns up |

`dist/transfer.js` is the one-shot: it drains a container and exits. This one keeps watching, so it
is the script to leave running while you mine, chop, craft or loot.

## What dist/stow.js does

1. **Asks which items to watch.** Click one of each — a valorite ingot, a diamond — and press ESC
   when done. Matching is by **art and hue**, so a valorite ingot does not take the verite ones with
   it. ESC straight away ends the run rather than meaning "everything".
2. **Asks for the container to stow them in.** A chest, a bag on the ground, a pack animal's
   backpack, or a pouch inside your own pack.
3. **Then, every `WATCH_POLL`:** walks the backpack and every bag inside it, at any depth, and moves
   every match into the container.
4. **Opens bags it has not seen before,** one level deeper per pass, once each — including one you
   drop in halfway through the run.
5. **Keeps going when there is nothing to move.** An empty pack is the script working, not a reason
   to stop.
6. **Stops** when you die, when `MAX_QUIET_STOWS` passes in a row issue moves and shift nothing, when
   the destination has been out of the client's sight for `MAX_LOST_DEST` polls, or at the
   `MAX_CYCLES` backstop.

### Before you paste it

- Both ends have to be within reach — a move is a drag, and the shard refuses one you cannot touch.
- **The container gets double-clicked to open it,** so a misclick on something that is not a
  container *uses* it. On a potion that means drinking it. Bags found inside the pack get the same
  treatment; set `OPEN_NESTED` to `false` if you keep loose potions in there, at the cost of not
  searching bags you have not opened yourself.
- **Picking a bag stows the bag whole,** contents and all. That is the opposite of what
  `dist/transfer.js` does with a bag, which flattens it. The run says so at startup for any pick
  whose art is a known container.
- Nothing else is checked. It does not watch your weight and it does not call the guards.

### How to run it

```bash
npm run build
```

Then paste `dist/stow.js` into the client's script editor.

```
stow: target one of each item to stow, ESC when done
stow:   1. iron ingot 0x1bf2/0x0
stow:   2. diamond 0x0f26/0x0
stow: nothing targeted
stow: target the container to stow them in
stow: watching 0x1bf2/0x0, 0x0f26/0x0 -> metal chest (0x4005f1a1)
stow: stowed 412 in 2 stacks, 412 in total
stow: still here - watching, cycle 96, at 1421,1698, 312/455, 412 stowed
stow: stowed 60 in 1 stacks, 472 in total
```

## What to set

Everything lives in [`config.ts`](config.ts).

| Setting | Default | What it is for |
| --- | --- | --- |
| `MAX_CYCLES` | `20_000` | Backstop on the loop — about eleven hours at `WATCH_POLL` |
| `WATCH_POLL` | `2000` | How often the pack is walked when there is nothing to move |
| `OPEN_DELAY` | `800` | How long a double-click has to reach the server and the contents to come back |
| `MOVE_DELAY` | `250` | The pause between one move and the next |
| `SETTLE_TIMEOUT` / `SETTLE_POLL` | `2000` / `100` | How long a pass waits for the stacks to leave the pack, and how often it looks |
| `OPEN_NESTED` | `true` | Whether bags inside the pack get double-clicked open. Off still reads any bag the client already has open |
| `MAX_REOPENS` | `3` | How often a bag that went shut mid-run is opened again before it is left alone |
| `MAX_QUIET_STOWS` | `5` | Passes in a row that issued moves and shifted nothing before the run gives up |
| `STOW_BACKOFF` / `STOW_BACKOFF_MAX` | `2000` / `60_000` | How far one of those passes backs off, and the ceiling |
| `MAX_LOST_DEST` | `30` | Polls the client can fail to see the destination for before the run ends |
| `MAX_PICKS` | `20` | Backstop on the item selection, which normally ends with ESC |
| `OPL_TIMEOUT` | `2000` | How long to wait for the tooltip that names a pick |
| `LOG_EVERY_ITEM` | `false` | A line per stack as it goes, as `art/hue xN` |

## When it goes wrong

**`stow: nothing to watch`**

ESC on the first cursor, or every pick had an unknown art. Unlike `dist/transfer.js`, no picks does
not mean everything — a watcher matching everything would empty your regs and your spare kit into a
chest in the background.

**`stow: nothing knows the art of '…', so it cannot be matched - hover it and run again`**

The click resolved to a serial the client has no art for, which matches nothing. Hover the item so
the client fetches its tooltip, then run again.

**`stow: nowhere to put it`**

ESC on the container cursor.

**`stow: that is the backpack itself - pick a bag or a chest to stow into`**

Every match would have been told to move onto itself.

**`stow: N passes in a row moved nothing, with M still in the pack`**

Every match was told to move and none of them did. The container is full, out of range, or the shard
is refusing in silence. It says nothing about *why* because the client does not: `moveItem` reports
only that the packet went out.

**`stow: 0x… has not been where the client can see it for N polls`**

`client.findObject` stopped answering for the container — you rode far enough that the client dropped
it, or someone picked it up. Coming back within `MAX_LOST_DEST` polls resumes the run.

**`contents: 0x… 0x… '…' would not answer`**

The client failed the `contents` read rather than answering it. That bag is treated as one that has
not been opened, and the next pass opens it.

**A bag was stowed whole instead of being searched**

Its art is not in `CONTAINER_GRAPHICS` in [`lib/containers.ts`](../lib/containers.ts) and the client
had never opened it, so it reads as a plain item. Open it by hand once and run again, or add the
graphic — the run cannot double-click to find out, because `player.use()` on a non-container *uses*
it.

## Notes on the shard

Written against UOAlive.

- The container and everything under it are invisible to the scan, so stowing into a pouch in your
  own pack is safe: the pouch is never moved into itself and what is already inside it is left alone.
- A bag the run opened is remembered as a bag, so it is never double-clicked twice. If it goes
  unreadable again — you closed the window, the client dropped it — it is opened up to `MAX_REOPENS`
  more times and then left alone.
- The set of bags the run has opened only grows. Over an afternoon that is a few thousand serials and
  nothing worth pruning; pruning would risk re-clicking a bag that came back.
- Amounts are counted at the moment of the move. A stack that merged into an identical one at the
  destination answers for the merged total afterwards.
