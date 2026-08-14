// The client refreshes weight and weightMax independently, and reports a max of 0 in the window
// before it has been told - against which every weight in the game is overweight. A mining run
// ended at *overweight (436/453)* on exactly that: the branch opened on a max of 0, and the figure
// had recovered by the time anything read it again, so the stop printed a weight comfortably
// inside the limit it claimed to have exceeded. Every read of the limit goes through here.
export const overweight = (buffer = 0): boolean =>
  player.weightMax > 0 && player.weight > player.weightMax - buffer;
