/** ClarifyQuestion · FE-A (Design.md §4.6, S-03) — 확인 질문 1개 + 선택지/자유입력.
 *  질문은 항상 하나. 선택지 클릭 또는 자유 입력 중 하나라도 채워지면 제출 활성. */
import { useState } from 'react';
import { Button } from '../common/Button';
import { Chip } from '../common/Chip';
import styles from './ClarifyQuestion.module.css';

interface ClarifyQuestionProps {
  question: string;
  options?: string[];
  onSubmit: (answer: string) => void;
  onReset: () => void;
}

export function ClarifyQuestion({
  question,
  options,
  onSubmit,
  onReset,
}: ClarifyQuestionProps) {
  const [picked, setPicked] = useState<string | null>(null);
  const [free, setFree] = useState('');

  const answer = (free.trim() || picked || '').trim();
  const canSubmit = answer.length > 0;

  return (
    <div className={`${styles.wrap} view-enter`}>
      <p className={styles.kicker}>추천을 위해 한 가지만 확인할게요</p>
      <h2 className={styles.question}>{question}</h2>

      {options && options.length > 0 && (
        <div className={styles.options} role="group" aria-label="선택지">
          {options.map((opt) => (
            <Chip
              key={opt}
              variant={picked === opt ? 'selected' : 'interactive'}
              selected={picked === opt}
              onClick={() => setPicked(picked === opt ? null : opt)}
            >
              {opt}
            </Chip>
          ))}
        </div>
      )}

      <textarea
        className={styles.textarea}
        placeholder="또는 직접 입력…"
        value={free}
        onChange={(e) => setFree(e.target.value)}
        rows={3}
      />

      <div className={styles.actions}>
        <Button variant="ghost" onClick={onReset}>
          처음으로
        </Button>
        <Button
          variant="primary"
          disabled={!canSubmit}
          onClick={() => canSubmit && onSubmit(answer)}
        >
          답변하고 계속
        </Button>
      </div>
    </div>
  );
}
