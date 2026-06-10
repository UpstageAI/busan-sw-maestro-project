/** ClarifyScreen · S-03 · FE-A — 확인 질문 화면 래퍼.
 *  ClarifyQuestion 을 중앙 카드에 담는다. 답변 병합 재요청은 App이 처리. */
import { ClarifyQuestion } from '../components/input/ClarifyQuestion';
import styles from './ClarifyScreen.module.css';

interface ClarifyScreenProps {
  question: string;
  options?: string[];
  onSubmit: (answer: string) => void;
  onReset: () => void;
}

export function ClarifyScreen({
  question,
  options,
  onSubmit,
  onReset,
}: ClarifyScreenProps) {
  return (
    <div className={styles.screen}>
      <div className={styles.card}>
        <ClarifyQuestion
          question={question}
          options={options}
          onSubmit={onSubmit}
          onReset={onReset}
        />
      </div>
    </div>
  );
}
