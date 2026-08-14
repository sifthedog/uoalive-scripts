// exit() is declared as returning void, so the compiler keeps checking the code after it and never
// narrows on it. The throw is unreachable if exit() halts the script, and halts it if it does not.
// The type annotation belongs on the binding rather than the arrow: a `never` return only makes the
// code after a call unreachable when the compiler can see it on the declaration itself.
export const die: (reason: string) => never = (reason) => {
  exit(reason);
  throw new Error(reason);
};
