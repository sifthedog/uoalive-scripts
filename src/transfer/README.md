# transfer — move everything out of one container and into another

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/transfer.js` | Target a container to empty, a container to fill, then optionally the items to move |

## Why it exists

`dist/boxes.js` empties containers into your own backpack and `dist/lumberjack.js` loads a pack
animal out of it. Both hardcode one end of the move. This one asks for both.

## What dist/transfer.js does

1. **Asks for the container to empty.** A chest, a bag, a corpse, a pack animal's backpack, your own.
2. **Asks for the container to fill.**
3. **Asks which items to move.** Click one of each — a valorite ingot, a diamond — and press ESC when
   done. Every stack sharing that **art and hue** goes across, so a valorite ingot does not take the
   verite ones with it. **ESC straight away moves everything.**
4. **Opens the source, and every bag inside it,** one level deeper per pass.
5. **Moves the items across at any depth**, so the destination ends up flat. The bags themselves stay
   where they were — moving one would undo the flattening.
6. **Stops when the source is empty**, or when a pass moves nothing.

### Before you paste it

- Both containers have to be within reach — a move is a drag, and the shard will refuse one you
  cannot touch.
- **Both ends get double-clicked to open them,** so a misclick on something that is not a container
  *uses* it. On a potion that means drinking it.
- Nothing else is checked. It does not watch your weight, it does not call the guards, and it does
  not care what is in the items. It is a one-shot, not a run to leave unattended.

### How to run it

```bash
npm run build
```

Then paste `dist/transfer.js` into the client's script editor.

```
transfer: target the container to empty
transfer: target the container to fill
transfer: target one of each item to move, ESC to move all of it
transfer: nothing targeted
transfer: metal chest (0x4005f1a1) -> Backpack (0x0000f5c2), moving everything
transfer:   0x1bf2/0x08a5 x412
transfer:   0x0f16/0x0 x3
transfer: moved 2 stacks, 418 items
```

## What to set

Everything lives in [`config.ts`](config.ts).

| Setting | Default | What it is for |
| --- | --- | --- |
| `OPEN_DELAY` | `800` | How long a double-click has to reach the server and the contents to come back |
| `MOVE_DELAY` | `600` | The pause between moves. Moves are asynchronous, so this is not a wait for one to land |
| `MAX_PASSES` | `12` | Backstop. A pass either opens one level deeper or moves what it can see |
| `MAX_PICKS` | `20` | Backstop on the item selection, which normally ends with ESC |
| `OPL_TIMEOUT` | `2000` | How long to wait for the tooltip that names a pick |
| `LOG_EVERY_ITEM` | `true` | A line per stack moved, as `art/hue xN` |

## When it goes wrong

**`transfer: no container to empty` / `transfer: nowhere to put it`**

ESC on one of the first two cursors. Both ends are required; only the item list is optional.

**`transfer: that is the same container twice`**

The same serial was targeted twice.

**`transfer: 0x… would not open - stand closer, or open it yourself first`**

The contents came back `undefined` after the double-click, which is what a container that never
opened reads as. Usually out of range.

**`transfer: N left behind, nothing moved on the last pass`**

Every remaining item was told to move and none of them did. The destination is full, the source is
out of range, or the shard is refusing in silence. It says nothing about *why* because the client
does not: `moveItem` reports only that the packet went out.

**`contents: 0x… 0x… '…' would not answer`.** The client failed the `contents` read rather than
answering it. That bag is treated as one that has not been opened, and skipped until something opens
it — which `openNested` in [`lib/sift.ts`](../lib/sift.ts) does on the next pass, so a nested bag still gets emptied.

**A bag came across whole instead of being emptied**

Its art is not in `CONTAINER_GRAPHICS` in [`lib/containers.ts`](../lib/containers.ts) and the client
had never opened it, so it reads as a plain item. Open it by hand once and run again, or add the
graphic — the run cannot double-click to find out, because `player.use()` on a non-container *uses*
it, and on a potion that means drinking it.

## Notes on the shard

Written against UOAlive.

- Items are matched by graphic **and** hue, never by name. Names arrive only with tooltip data, so a
  pack you have not hovered over would match nothing.
- A bag the run opened and emptied is remembered as a bag. Otherwise it answers `[]` afterwards,
  which is indistinguishable from a plain item, and the next pass would move it.
- A destination that is *inside* the source is skipped whole, contents and all, so it cannot be fed
  into itself.
