export const rubricVersion: string;
export type ScoreResult = { score: number | null; cutoff: number; status: 'advance' | 'below_cutoff' | 'unscored'; nextAction: string; breakdown: Record<string, number>; explanation: string };
export function scoreProspect(input: unknown, cutoff?: number): ScoreResult;
