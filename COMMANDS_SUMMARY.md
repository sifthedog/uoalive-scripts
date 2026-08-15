# Commands — summary

Two edits, in this order:

1. Paste `wiki/Commands.wiki` into `uoalive.com/wiki/index.php?title=Commands&action=edit`. Preview before saving.
2. Paste `wiki/Mycommands.wiki` (one line, a redirect) into `uoalive.com/wiki/index.php?title=Mycommands&action=edit`.

Doing it in that order means there is never a moment where both pages are stale.

`wiki/Commands.original.wiki` and `wiki/Mycommands.original.wiki` are the live pages as they were before the edit.

## Edit summaries (for the wiki box)

Commands:

```
Reorganized into 14 task-based sections with tables: skill shortcuts keyed by skill (40 bullets -> 23 rows), a single "Toggles and defaults" table, staff commands separated out. Links 24 -> 44 unique. Absorbs Mycommands, which now redirects here. No commands lost.
```

Mycommands:

```
Redirect to [[Commands]]. The two pages were 90% duplicates; Commands now carries the full categorized list.
```

## Post for the GM

> I merged `Mycommands` into `Commands` and reorganized it.
>
> - **`Mycommands` had 101 command names and not one description.** It was a three-column table in no discernible order, last edited July 2025. It is now a redirect.
> - **`Commands` was one flat alphabetical list**, so you could only find a command if you already knew its name. It is now **14 sections by what you are trying to do**: skills, your character, money, fixing things, pets, chat, finding people, toggles, games, encounters, reputation, quests, helping new players, staff.
> - **The 40 skill-shortcut bullets are now 23 rows**, keyed by skill rather than by spelling, so `[disco` `[discord` `[discordance` sit on one line and link to the skill's page.
> - **New "Toggles and defaults" table.** Every on/off switch on the shard with its default, in one place. This was the single most scattered thing on the old page, and it is what a new player actually needs.
> - **Staff commands are labelled.** `[GiveToken`, `[CreateEventMoongate` and `[DeleteEventMoongate` were sitting among player commands with nothing marking them as gated.
> - **Links 24 -> 44 unique.** The old page named systems without linking them: Invasions, Encounters, Champion Spawns, Factions, Fish Monger, Profile, Currencies, Chat, Emote, Veteran Rewards, UOAlive Games, Quests all have pages and now get linked.
> - **No command was lost.** All 113 from both pages are on the new one.
>
> **Both lists have drifted from the game and I need you to check the list at the bottom of this post before I add anything to the page.** Patch notes from the last year document about 18 player commands that appear on neither page. I have not put any of them on the page yet.

## Numbers

`Commands` 8,854 -> 11,276 bytes · `Mycommands` 2,240 -> 23 bytes (redirect) · commands documented **113** (was 113 across two pages, 101 of them undescribed on `Mycommands`) · unique links 24 -> **44** · sections 2 -> 17 · tables 1 -> 15 · images 2, both kept.

Verified against the wiki API: all 48 link and image targets exist. No red links, no duplicate headings, no em dashes. `[[Category:NewPlayers]]` was dropped, it has no category page and `Commands` was its only member; `Quality of Life` and `Custom Content` are kept.

## Needs confirming in game before it goes on the page

These are all sourced from dated patch notes but appear on neither command page. Type them and tell me which are real, and I will add them.

| Command | What the patch note says | Source |
| --- | --- | --- |
| `[MyPath` | View and manage your skill gain path | Jul 10 2026 |
| `[Hunger` | Your hunger meter and the hunger guide | Jul 15 2026 |
| `[MyRent` | City Rental status gump | Jul 06 2026 |
| `[PartyLootOn` / `[PartyLootOff` | Whether party members may loot your corpse and your pet corpses, pack animals included | Jul 10 2026 |
| `[JoinGame` | Join a nearby festival game without double-clicking the totem | May 22 2026 |
| `[LeaveGame` | Leave a game you are stuck in | May 22 2026 |
| `[GameGump` | Reopen the game gump you accidentally closed | May 22 2026 |
| `[JoustLeave` | Leave the jousting queue or match | Jun 26 2026 |
| `[AnimalTraining` | Target a pet, opens the web Animal Training Planner with it imported | Jun 18 2026 |
| `[AnimalTrainingCode` | Same, but generates a paste code instead of opening the browser | Jun 18 2026 |
| `[FixWeight` | Recalculates carried weight. Also added as a Weight option inside `[FixMe` | Jul 15 2026 |

Perilous Path set, all documented on the `Pariah` page, probably wants its own section rather than being scattered through the others:

`[PariahStatus` · `[Tedium` · `[PariahGuides` · `[PACTS` (read-only for players since July 2026) · `[Cutpurse` · `[Snoop` · `[PerilousLives`

Should be **off** any player list: `[PariahBounty`, `[PariahBounties`, `[TheNamesThatRemain` and `[PerilousLeaderboard` became board-only on Jul 15 2026, and `[PariahCutpurse` and `[PariahToggle` were deleted as redundant aliases the same day. None of them are on the new page.

I also found ~25 staff commands in the same patch notes (`[PACTSAAdmin`, `[EncounterCompaction`, `[GMHunger`, `[GMTedium`, `[CheckResources`, `[ClearEscort`, `[NujelmGolems`, `[RefreshFillable`, `[FillableCrates`, `[SecureCityRentalContainers`, `[CleanPariahGuilds`, `[CleanPariahAlliances`, `[TetheredPetAudit`, `[EncounterTierAuditReport`, `[ToggleGlobalIDOCEffects`, `[didtheyspam`, and the `[SetP.A.C.T.S.` family). They are deliberately not on this page. Say the word and I will draft a separate `Staff Commands` page.

## Questions

1. **`[ClearRC`** is on both pages with no description anywhere on the wiki, and no patch note mentions it. What is RC? Its row on the new page is currently blank.
2. **`[Doom`** has no description either. I pointed it at the `Doom` page as a placeholder. What does typing it actually do?
3. **`[Achievements`** was on `Mycommands` and missing from `Commands`. The `Quality Of Life` page claims it shows *other players'* achievements while `[MyAchievements` shows your own. I could not source that, so the new page says only "opens the achievements gump". Which is right? Achievements still have no wiki page of their own.
4. **`[Points` collides with points.** `[Points` and `[PointsLanguage` are the pointing gesture, but `[Challenge` is "for points" and `[TopPlayers` ranks "points". Two systems, one word. Worth renaming one in the docs?
5. **Is `[MyCommands` in game the only authoritative list?** `[Hunger` has its own page and is on `Quality Of Life`, but was on neither command page, so the drift is not a one-off. If there is a source file I can diff against, this stops being a manual job.
