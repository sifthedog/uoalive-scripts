import { die } from '../lib/die.js';
import { HOIST_FROM_BAGS } from './config.js';
import { hoistToPack } from './hoist.js';
import { pickItems } from './pick.js';
import { describeCounts, sellAll } from './sell.js';

const picked = pickItems('sell');

if (picked.length === 0) {
  die('sell: nothing to sell');
}

const names = picked.map((item) => item.name);

log(`sell: selling ${names.map((name) => `'${name}'`).join(', ')}`);

if (HOIST_FROM_BAGS) {
  for (const name of names) {
    hoistToPack(name);
  }
}

const sold = sellAll(names);

log(`sell: ${describeCounts(sold.byName) || 'nothing'} sold, ${sold.total} in all`);
