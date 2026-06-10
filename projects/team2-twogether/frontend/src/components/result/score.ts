/** 점수 색 규칙 (Design.md §2.1):
 *  score ≥ 80 → success / 60~79 → ink / < 60 또는 limited → warn */
export type ScoreTone = 'success' | 'ink' | 'warn';

export function scoreTone(score: number, limited = false): ScoreTone {
  if (limited || score < 60) return 'warn';
  if (score >= 80) return 'success';
  return 'ink';
}
