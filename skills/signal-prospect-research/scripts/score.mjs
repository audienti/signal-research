export const rubricVersion = 'fit-v1';
const bands = {
  company: { match: 25, plausible: 18, unknown: 5, mismatch: 0 },
  role: { target: 30, adjacent: 15, unknown: 5, unrelated: 0 },
  relevance: { direct: 30, adjacent: 20, weak: 10, none: 0 },
  evidence: { corroborated: 15, primary: 10, weak: 5, none: 0 },
};
export function scoreProspect(input, cutoff = 70) {
  if (!Number.isInteger(cutoff) || cutoff < 0 || cutoff > 100) throw new Error('Minimum score must be a whole number from 0 to 100.');
  const empty = { score: null, cutoff, status: 'unscored', nextAction: 'research', breakdown: {}, explanation: 'Complete the sourced scoring assessment.' };
  if (!input || input.rubricVersion !== rubricVersion || typeof input.experimentId !== 'string' || !input.experimentId.trim() || typeof input.companyId !== 'string' || !input.companyId.trim()) return empty;
  const breakdown = {};
  for (const [key, values] of Object.entries(bands)) {
    const item = input[key];
    if (!item || !Object.hasOwn(values, item.band) || typeof item.reason !== 'string' || !item.reason.trim()) return empty;
    breakdown[key] = values[item.band];
  }
  if (!Array.isArray(input.sources) || !input.sources.length || !input.sources.every(s => { try { return ['https:', 'http:'].includes(new URL(s).protocol); } catch { return false; } })) return empty;
  // Explicit incompatibility is a zero fit, not a reason to invent points from other dimensions.
  const incompatible = input.company.band === 'mismatch' || input.role.band === 'unrelated' || input.relevance.band === 'none';
  const score = incompatible ? 0 : Object.values(breakdown).reduce((a, b) => a + b, 0);
  const advance = score >= cutoff;
  return { score, cutoff, status: advance ? 'advance' : 'below_cutoff', nextAction: advance ? 'prepare_conversation' : 'retain', breakdown,
    explanation: (incompatible ? 'Explicit mismatch makes overall fit zero. ' : '') + Object.entries(bands).map(([key]) => input[key].reason).join(' ') };
}
