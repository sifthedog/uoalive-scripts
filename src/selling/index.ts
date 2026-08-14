import { die } from '../lib/die.js';
import { HOIST_FROM_BAGS } from './config.js';
import { hoistToPack } from './hoist.js';
import { pickItem } from './pick.js';
import { sellAll } from './sell.js';

const picked = pickItem() ?? die('sell: nothing to sell');

log(`sell: selling '${picked.name}'`);

if (HOIST_FROM_BAGS) {
  hoistToPack(picked.name);
}

const sold = sellAll(picked.name);

log(`sell: ${sold} x '${picked.name}' sold`);
