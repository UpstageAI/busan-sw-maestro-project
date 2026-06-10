/** StateView · FE-B (Design.md §4.7, S-06) — 빈/에러/타임아웃 단일 컴포넌트.
 *  아이콘 + 메시지 + 액션 버튼 중앙 정렬. 기본 문구/액션은 type별 기본값. */
import { Button } from '../common/Button';
import styles from './StateView.module.css';

type StateType = 'empty' | 'error' | 'timeout';

interface StateViewProps {
  type: StateType;
  /** 없으면 type별 기본 문구 */
  message?: string;
  action?: { label: string; onClick: () => void };
}

const DEFAULTS: Record<StateType, { icon: string; message: string }> = {
  empty: {
    icon: '🔍',
    message: '적합한 멘토를 찾지 못했어요. 입력을 조금 더 구체화해볼까요?',
  },
  error: { icon: '⚠️', message: '잠시 문제가 생겼어요.' },
  timeout: { icon: '⏳', message: '조금 더 걸리고 있어요…' },
};

export function StateView({ type, message, action }: StateViewProps) {
  const base = DEFAULTS[type];
  return (
    <div className={styles.wrap} role={type === 'error' ? 'alert' : 'status'}>
      <span className={styles.icon} aria-hidden="true">
        {base.icon}
      </span>
      <p className={styles.message}>{message ?? base.message}</p>
      {action && (
        <Button variant={type === 'error' ? 'primary' : 'ghost'} onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
