// Read-only calibration for ORE_TILE_GRAPHICS in src/mining/config.js. It never swings, never
// targets and never moves - it only asks the client what is on the ground around you.
//
// It exists because a mountainside is a *land* tile, and land tiles have no name in this API:
// getStatic reads the static tiledata, and getTile answers with flags and nothing else. So unlike
// lumberjacking, which can ask the client whether a static is called a tree, mining has to be told
// which graphics are ore-bearing. Stand on the face you intend to work and run this: the bands it
// prints are what belongs in the config, instead of the stock RunUO guess that ships there.
import { ORE_TILE_GRAPHICS, PROBE_RADIUS } from './config.js';
import { reportTerrain } from './survey.js';

log(`probe: ORE_TILE_GRAPHICS currently holds ${ORE_TILE_GRAPHICS.size} graphics`);

const found = reportTerrain(PROBE_RADIUS);
const matched = found.filter((art) => art.matches);

if (matched.length === 0) {
  log('probe: nothing here matches. The land graphics above are the candidates to add.');
} else {
  const tiles = matched.reduce((total, art) => total + art.tiles, 0);
  log(`probe: ${matched.length} art(s) match, covering ${tiles} tiles`);
}

log('probe: put the land graphics you mean to mine into ORE_TILE_GRAPHICS, then run dist/mining.js');
