// exit() is declared as returning void, so the compiler keeps checking the code after it. The throw
// is unreachable if exit() halts the script, and halts it if it does not. The `never` annotation
// belongs on the binding rather than the arrow - only a declaration makes later code unreachable.
export const die: (reason: string) => never = (reason) => {
  exit(reason);
  throw new Error(reason);
};
