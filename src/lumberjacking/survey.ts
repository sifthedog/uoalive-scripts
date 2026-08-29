import { createSurvey } from '../lib/survey.js';
import { isTree } from './tree.js';

export const { reportTerrain } = /* @__PURE__ */ createSurvey({
  label: 'survey',
  matches: (graphic, isLand) => !isLand && isTree(graphic),
});
