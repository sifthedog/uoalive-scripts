import { dead, firstReason, hurt } from '../lib/guards.js';
import { HEALTH_FLOOR } from './config.js';

// Keeping the tames fills the slots, and a shard with no room left refuses every attempt without
// saying why. maxFollowers reads 0 before the client has been told, the way maxMana does.
const full = (): string | undefined =>
  player.maxFollowers > 0 && player.followers >= player.maxFollowers
    ? 'no follower slots left'
    : undefined;

// A health floor where animal-lore has none: a failed tame turns the animal on you. No weight or
// pack check - nothing goes in the pack.
export const stopReason = (): string | undefined => firstReason(dead, hurt(HEALTH_FLOOR), full);
