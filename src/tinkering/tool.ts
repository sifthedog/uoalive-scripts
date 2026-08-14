import { createTool } from '../lib/tool.js';
import { SPARE_BAG_SERIAL, TOOL_GRAPHICS, TOOL_NAME } from './config.js';

let oplReportsUses = true;

// The tinker's tools are used out of the pack rather than worn, so nothing is ever equipped and the
// hand layers hold whatever they held. `held` answers undefined for that reason, which leaves find()
// as the only half of this that gets used.
const tool = /* @__PURE__ */ createTool({
  label: 'tool',
  name: TOOL_NAME,
  graphics: TOOL_GRAPHICS,
  spareBagSerial: SPARE_BAG_SERIAL,
  held: () => undefined,
  equip: { attempts: 0, timeoutMs: 0, pollMs: 0 },
});

export const isTool = tool.is;
export const rememberTool = tool.remember;

// A worn-out tool is deleted server-side, so a serial that no longer resolves is gone. This is
// the message-independent signal: item.hits is 0 for items the client knows nothing about, and
// a RunUO tool tracks UsesRemaining rather than hits anyway.
export const toolAlive = (serial: number | undefined): serial is number =>
  serial !== undefined && !!client.findObject(serial);

export const findTool = (): number | undefined => tool.find()?.serial;

const usesRemaining = (serial: number): number | undefined => {
  const opl = client.queryItemOPL(serial, 1000);

  for (const property of opl?.properties ?? []) {
    const values = (property.values ?? []).map((value) => value.text).join(' ');
    const match = `${property.text ?? ''} ${values}`.match(/uses remaining[^0-9]*([0-9]+)/i);
    if (match) {
      return Number(match[1]);
    }
  }

  return undefined;
};

// Swapping before the last use means no craft is lost to a mid-craft break. UOAlive may not send
// the property at all, so stop asking after the first miss rather than paying the timeout a cycle.
export const needsSwap = (serial: number | undefined): boolean => {
  if (!toolAlive(serial)) {
    return true;
  }
  if (!oplReportsUses) {
    return false;
  }

  const uses = usesRemaining(serial);
  if (uses === undefined) {
    oplReportsUses = false;
    log('tool: no "uses remaining" property, falling back to detecting the break itself');
    return false;
  }

  return uses <= 1;
};
