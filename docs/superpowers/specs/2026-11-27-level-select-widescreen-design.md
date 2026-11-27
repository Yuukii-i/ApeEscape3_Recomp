# Level select on wide screens (design, approved 2026-11-27)

## Intent
The level select is drawn for 4:3; its carousel only produces enough icons for that width. On wide screens it should
show more levels instead of stretching or leaving the rest empty, without looking broken on ultrawide.

## Behaviour
| Element | Placement (screen wider than 4:3) | Stretched |
|---|---|---|
| Level name, TV picture | centre, as on 4:3 | no |
| Carousel | fills the level-select area with more level icons; nothing spills past the area | no |
| Arrows | follow the carousel's edges | no |
| "16 / 16" counter | right edge of the level-select area | no |
| Cancel / OK bar | kept together, bottom-right edge of the area | no |
| "Level Complete" band | real top-right screen corner at every width (its artwork ends there) | no |
| Sky and scenery | whole screen at every width, no black bars | n/a (3D) |

Level-select area: centred, as wide as the screen but at most 16:9. At 4:3 nothing changes.

## Non-goals
Other menus stay 4:3. No new artwork. No change to carousel input or order.

## Approaches
- A. Make the game draw more carousel entries (chosen: matches the intended look and keeps the game's own
  positions and animation).
- B. Same number of entries, wider spacing: easier, but sparse, and the earlier three-group split could return.
  Fallback only after asking the user.
- Renderer-only repositioning of icons: dropped, the renderer cannot know which carousel slot an icon is.
Earlier attempt (user report): forcing 16:9 split the carousel into previous/current/next groups with other levels
stranded until the selection moved.

## Order
1. Identify the pieces (UI layer, texture, position); move band, counter, Cancel/OK.
2. Find the carousel's visible-entry limit in the game, raise it, move the arrows.
3. Verify with logs/leveselect.padrec at 4:3, 16:9 and ultrawide.
