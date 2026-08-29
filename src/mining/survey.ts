import { createSurvey } from '../lib/survey.js';
import { isOre } from './vein.js';

export { describeArt, type Art } from '../lib/survey.js';

export const { surveyTerrain, reportTerrain } = /* @__PURE__ */ createSurvey({
  label: 'survey',
  matches: isOre,
});
