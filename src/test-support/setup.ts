import { installGlobals } from './uo.js';

// Seeds the globals once before any test module is imported, so the modules that read them while
// being evaluated find something. Individual tests call installGlobals again to describe the world
// they need.
installGlobals();
