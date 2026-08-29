# arrows — picking spent ammunition up off the floor

Builds one script:

| Script | What it does |
| --- | --- |
| `dist/arrows.js` | Watches the ground and moves every arrow and crossbow bolt within reach into your backpack |

## Why it exists

Shooting a butte scatters arrows across the ground and the client gives you no way to sweep them up
— every stack is a drag into the pack. This is that sweep, on a loop, so it can be left running while
you shoot.

## What it does

Per cycle:

1. **Check the stop conditions** — dead, overweight, pack full.
2. **Sit out a world save** if one is running. Everything attempted during a save is refused, and
   five of those in a row would otherwise end the run on the quiet counter below.
3. **Scan the ground** for every graphic in `AMMO_GRAPHICS` and keep what is within `GRAB_RANGE`.
4. **Nothing in reach** → heartbeat and poll again. This is the script waiting for you to shoot, so
   it counts neither as a stall nor against the cycle backstop — a run left watching an empty floor
   does not end on its own.
5. **Otherwise sweep** — one `moveItem` per stack, `MOVE_DELAY` apart.
6. **Poll until the stacks leave the floor.** `moveItem` returns before the server has answered, so
   a stack still on the floor is simply not counted — and polling for the proof means a move that
   lands in 100ms costs 100ms instead of the worst case.

A sweep that moved nothing backs off, sets those stacks aside for `BLOCKED_DELAY` and is counted;
`MAX_QUIET_SWEEPS` of them in a row ends the run. That is the pack being full in a way the guard did
not catch, or the client thinking a stack is closer than the server does. The counter is cleared
whenever there is nothing in reach, so it means sweeps in a row and not sweeps in a session.

### Before you paste it

- **Nothing walks.** Arrows that flew past the target stay where they landed — step over to them and
  the next cycle takes them.
- **Arrows inside a corpse are not taken.** They have a container, so they are not on the floor.
- Arrows already in your pack or in a bag are left alone, for the same reason.
- Any hue is taken. There is no name check and no tooltip query anywhere in this script.

### How to run it

```bash
npm run build
```

Then paste `dist/arrows.js` into the client's script editor. The first line is a census — how many of
each configured graphic the client can see in the whole world — so a wrong graphic shows up
immediately rather than as an afternoon of silence.

## What to set

Everything lives in [`config.ts`](config.ts).

| Setting | Default | What it is for |
| --- | --- | --- |
| `AMMO_GRAPHICS` | `0x0f3f`, `0x1bfb` | Arrow and crossbow bolt. Add anything else you want swept up |
| `GRAB_RANGE` | `2` | The shard's reach. Raising it past what the server allows just makes every sweep quiet |
| `MOVE_DELAY` | `250` | Between one move and the next. Raise it if sweeps start coming back partial |
| `WATCH_POLL` | `400` | Between scans that found nothing in reach. A client-side scan, so it costs no packets |
| `SETTLE_TIMEOUT` / `SETTLE_POLL` | `2000` / `100` | How long a sweep waits for the stacks to leave the floor, and how often it looks |
| `MAX_QUIET_SWEEPS` | `5` | Sweeps in a row that issued moves and shifted nothing, before the run stops |
| `BLOCKED_DELAY` | `60_000` | How long a stack the server would not move is left alone |
| `PRUNE_EVERY` | `50` | Idle passes between sweeps of the blocked map for stacks that have gone |
| `MAX_CYCLES` | `100_000` | Sweeps before the run stops. Idle polls do not count |
| `SWEEP_BACKOFF` / `SWEEP_BACKOFF_MAX` | `1000` / `8000` | How far a quiet sweep backs off, and the ceiling |
| `WEIGHT_BUFFER` | `20` | Stones kept clear of the limit, so the stop lands before the shard starts refusing |
| `PACK_LIMIT` | shared | Top-level pack slots before the run stops |

## When it goes wrong

**`0x0f3f x0, 0x1bfb x0 in the world`** with arrows plainly on the floor — the graphics are wrong for
this shard. Hover one and read its art, then correct `AMMO_GRAPHICS`.

**The opening line counts them, but nothing is ever taken.** Read the `under …` serials in that line:
they are the parents the client reports. Anything other than `0x0` or `0xffffffff` is a container
convention this script does not know, and belongs in `GROUND` in [`floor.ts`](floor.ts).

**`n on the floor, nearest N tiles away`** — they are further out than `GRAB_RANGE`. Said once per
run, because a floor of out-of-reach stacks logs identically to an empty one otherwise.

**`nothing moved (n/5)`** — the stacks are in reach as far as the client is concerned but the server
disagrees, or the pack will not take them. Stand directly on the pile. Each of those stacks is then
left alone for `BLOCKED_DELAY`, so one arrow the server will not move cannot end the run.

**`pack is full (120 items at the top level)`** — the pack's item cap, not its weight. Bag the arrows
or empty it.

**It sits on `still here - watching` while arrows are on the floor** — they are further than
`GRAB_RANGE`. Nothing in this script walks.

## Notes on the shard

Written against UOAlive.

- **`client.findAllItemsOfType(graphic, undefined, 'world')` is the whole of the ground scan.** There
  is no unfiltered item enumeration in this API — every item search is keyed on a graphic, which is
  why `AMMO_GRAPHICS` is a list rather than a filter.
- **A ground item's `container` is 0 *or* the world serial `0xffffffff`**, depending on the client,
  and nothing documents which. Reading only 0 as the ground rejected every stack on the floor, so
  both count. That field is the whole ground filter, and it is what keeps the arrows already in your
  own pack out of a sweep.
- **`findAllItemsOfType` takes a `range` of its own, and it is not used here.** What it means next to
  a `'world'` source is undocumented; `distanceTo` is Chebyshev, which is how the shard measures
  reach.
- **`moveItem`'s return says only that the packet went out.** Progress is judged by rescanning, the
  same way [`transfer`](../transfer/move.ts) judges a pass — but polled rather than slept through,
  which is [`boxes/drop.ts`](../boxes/drop.ts)'s lesson in reverse.
- **A throttled sweep comes back partial, not empty**, so it counts as progress and the stragglers
  are taken next cycle. That is why `MOVE_DELAY` errs fast: being wrong costs a cycle, not the run.

### Known unverified

- **Both graphics.** `0x0f3f` and `0x1bfb` are the stock arrow and crossbow bolt arts. The startup
  census is there to catch a shard where they are not.
- **Which serial this client calls 'no container'.** Both known conventions are accepted and the
  opening line prints what it actually saw, so a third one shows up as a number rather than silence.
- **`GRAB_RANGE` of 2.** The usual reach on a RunUO-family shard, not a measurement on this one.
