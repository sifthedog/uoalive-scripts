// The client refreshes weight and weightMax independently and reports a max of 0 before it has been
// told, against which every weight in the game is overweight. A mining run ended at
// *overweight (436/453)* on exactly that. Every read of the limit goes through here.
export const overweight = (buffer = 0): boolean =>
  player.weightMax > 0 && player.weight > player.weightMax - buffer;
