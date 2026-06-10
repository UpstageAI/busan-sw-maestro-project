/** LoadingScreen · S-02 · FE-A — 분석 진행 화면.
 *  StepProgress 래핑. refining 안내 / timeout 힌트 처리. */
import { StepProgress } from '../components/input/StepProgress';
import styles from './LoadingScreen.module.css';

interface LoadingScreenProps {
  step: number;
  refining: boolean;
  timedOut: boolean;
}

export function LoadingScreen({ step, refining, timedOut }: LoadingScreenProps) {
  return (
    <div className={`${styles.screen} view-enter`}>
      <h1 className={styles.title}>에이전트가 프로젝트를 분석하고 있어요</h1>
      <div className={styles.card}>
        <StepProgress current={step} refining={refining} />
      </div>
      {timedOut && (
        <p className={styles.timeout} role="status">
          조금 더 걸리고 있어요…
        </p>
      )}
    </div>
  );
}
