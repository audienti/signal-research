import { scoreProspect } from './score.mjs';
let raw = ''; for await (const chunk of process.stdin) raw += chunk;
const { assessment, cutoff } = JSON.parse(raw);
console.log(JSON.stringify(scoreProspect(assessment, cutoff), null, 2));
