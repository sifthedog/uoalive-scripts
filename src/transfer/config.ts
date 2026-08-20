// A double-click has to reach the server and the contents have to come back
export const OPEN_DELAY = 800;

// Moves are asynchronous, so this is a pause between them rather than a wait for one to land
export const MOVE_DELAY = 600;

// Each pass either opens one level deeper or moves what it can see, so this covers both the nesting
// and the retries
export const MAX_PASSES = 12;

// A backstop only - the selection ends when you press ESC
export const MAX_PICKS = 20;

export const OPL_TIMEOUT = 2000;

export const LOG_EVERY_ITEM = true;
