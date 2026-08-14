import { findIn, openContainers } from '../lib/containers.js';
import { SPARE_BAG_SERIAL, TOOL_GRAPHICS, TOOL_NAME } from './config.js';

let toolGraphic: number | undefined;
let spareBagSerial = SPARE_BAG_SERIAL;
let oplReportsUses = true;

// Names are empty until the client has tooltip data, so prefer the graphic once we know it
export const isTool = (item: Item): boolean =>
  (toolGraphic !== undefined && item.graphic === toolGraphic) ||
  TOOL_GRAPHICS.has(item.graphic) ||
  (item.name ?? '').toLowerCase().includes(TOOL_NAME);

export const rememberTool = (item: Item | undefined): void => {
  if (item && toolGraphic === undefined) {
    toolGraphic = item.graphic;
    log(`tool: tinker's tools graphic is 0x${item.graphic.toString(16)}`);
  }
};

// A worn-out tool is deleted server-side, so a serial that no longer resolves is gone. This is
// the message-independent signal: item.hits is 0 for items the client knows nothing about, and
// a RunUO tool tracks UsesRemaining rather than hits anyway.
export const toolAlive = (serial: number | undefined): serial is number =>
  serial !== undefined && !!client.findObject(serial);

export const findTool = (): number | undefined => {
  let tool = findIn(player.backpack?.contents, isTool);

  if (!tool && openContainers(spareBagSerial)) {
    tool = findIn(player.backpack?.contents, isTool);
  }

  if (!tool) {
    const graphics = (player.backpack?.contents ?? [])
      .map((item) => `0x${item.graphic.toString(16)}`)
      .join(', ');
    log(`tool: no tinker's tools left. Top level of pack holds: ${graphics}`);
    return undefined;
  }

  rememberTool(tool);

  // Remember the bag it came from so the next switch reopens only that one
  if (tool.container && tool.container !== player.backpack?.serial) {
    spareBagSerial = tool.container;
  }

  return tool.serial;
};

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
