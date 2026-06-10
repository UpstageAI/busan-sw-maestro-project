/** StepProgress · FE-A (Design.md §4.5, S-02) — 에이전트 파이프라인 단계 표시.
 *  완료 ✓ / 진행 ◐(펄스) / 대기 ○. refining 이면 하단 보정 안내 한 줄. */
import styles from './StepProgress.module.css';

/** 고정 4단계 */
const STEPS = ['입력 분석', '약점 분석', '멘토 검색', '적합도 평가'] as const;

interface StepProgressProps {
  /** 진행 중 단계 index (0..3) */
  current: number;
  /** 재검색 중이면 하단 안내 표시 */
  refining?: boolean;
}

export function StepProgress({ current, refining = false }: StepProgressProps) {
  return (
    <div className={styles.wrap} aria-live="polite">
      <ul className={styles.list}>
        {STEPS.map((label, i) => {
          const state = i < current ? 'done' : i === current ? 'active' : 'wait';
          const mark = state === 'done' ? '✓' : state === 'active' ? '◐' : '○';
          return (
            <li key={label} className={`${styles.step} ${styles[state]}`}>
              <span className={styles.mark} aria-hidden="true">
                {mark}
              </span>
              <span className={styles.label}>{label}</span>
              <span className="sr-only">
                {state === 'done' ? '완료' : state === 'active' ? '진행 중' : '대기'}
              </span>
            </li>
          );
        })}
      </ul>

      {refining && (
        <p className={styles.refining}>검색 질의를 보정해 다시 찾는 중…</p>
      )}
    </div>
  );
}
