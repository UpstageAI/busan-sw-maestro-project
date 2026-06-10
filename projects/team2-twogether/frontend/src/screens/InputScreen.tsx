/** InputScreen · S-01 · FE-A — 프로젝트 상황 자유 입력 + 추천받기.
 *  공백만 차단(짧은 입력은 통과 — 부족 판단은 백엔드 몫). 제출 시 버튼 잠금. */
import { useState } from 'react';
import { Button } from '../components/common/Button';
import { Chip } from '../components/common/Chip';
import styles from './InputScreen.module.css';

export interface ProjectInput {
  project_text: string;
  tech_stack?: string[];
  stage?: string;
}

interface InputScreenProps {
  submitting?: boolean;
  onSubmit: (input: ProjectInput) => void;
}

const STAGES = ['아이디어·기획', '개발 초기', '개발 중반', '배포 준비', '운영'];

/** 예시 프롬프트 — 클릭 시 textarea 를 채운다(데모 시나리오 3종) */
const EXAMPLES: { label: string; text: string }[] = [
  {
    label: '배포 고민',
    text: '우리 팀은 웹 백엔드는 어느 정도 구현했지만, 모델 서빙과 배포 경험이 부족합니다. 곧 배포를 해야 하는데 어떤 멘토를 만나야 할지 모르겠습니다.',
  },
  {
    label: '구조 리뷰',
    text: '기획과 사용자 문제 정의는 정리됐는데, 지금 설계한 시스템 구조가 적절한지 확신이 없습니다.',
  },
  {
    label: '실시간 영상',
    text: 'WebRTC 기반 실시간 영상 처리를 하려는데 관련 경험이 부족해 어디부터 봐야 할지 막막합니다.',
  },
];

export function InputScreen({ submitting = false, onSubmit }: InputScreenProps) {
  const [text, setText] = useState('');
  const [stack, setStack] = useState<string[]>([]);
  const [stackDraft, setStackDraft] = useState('');
  const [stage, setStage] = useState('');

  const canSubmit = text.trim().length > 0 && !submitting;

  const addStack = () => {
    const v = stackDraft.trim();
    if (v && !stack.includes(v)) setStack([...stack, v]);
    setStackDraft('');
  };

  const handleSubmit = () => {
    if (!canSubmit) return;
    onSubmit({
      project_text: text.trim(),
      tech_stack: stack.length ? stack : undefined,
      stage: stage || undefined,
    });
  };

  return (
    <div className={`${styles.screen} view-enter`}>
      <h1 className={styles.title}>
        멘토를 찾고 싶은 프로젝트 상황을
        <br />
        편하게 적어주세요
      </h1>

      <textarea
        className={styles.textarea}
        placeholder="프로젝트 설명, 기술 스택, 진행 단계, 지금 고민을 편하게 적어주세요."
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={6}
        aria-label="프로젝트 상황 입력"
      />

      <div className={styles.examples}>
        <span className={styles.examplesLabel}>예시</span>
        {EXAMPLES.map((ex) => (
          <Chip key={ex.label} variant="interactive" onClick={() => setText(ex.text)}>
            {ex.label}
          </Chip>
        ))}
      </div>

      <details className={styles.optional}>
        <summary className={styles.summary}>선택 입력 (기술 스택 · 진행 단계)</summary>

        <div className={styles.optBody}>
          <div className={styles.field}>
            <span className={styles.fieldLabel}>기술 스택</span>
            <div className={styles.stackRow}>
              {stack.map((s) => (
                <Chip
                  key={s}
                  variant="selected"
                  onClick={() => setStack(stack.filter((x) => x !== s))}
                >
                  {s} ✕
                </Chip>
              ))}
              <input
                className={styles.stackInput}
                placeholder="입력 후 Enter"
                value={stackDraft}
                onChange={(e) => setStackDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addStack();
                  }
                }}
              />
            </div>
          </div>

          <div className={styles.field}>
            <span className={styles.fieldLabel}>진행 단계</span>
            <select
              className={styles.select}
              value={stage}
              onChange={(e) => setStage(e.target.value)}
            >
              <option value="">선택 안 함</option>
              {STAGES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>
      </details>

      <div className={styles.footer}>
        <Button
          variant="primary"
          disabled={!canSubmit}
          loading={submitting}
          onClick={handleSubmit}
        >
          추천받기
        </Button>
      </div>
    </div>
  );
}
