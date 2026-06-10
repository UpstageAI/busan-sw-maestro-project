/** Chip · 공용 (Design.md §4.2) — default/selected/interactive · 도메인은 mono */
import type { ReactNode } from 'react';
import styles from './Chip.module.css';

type Variant = 'default' | 'selected' | 'interactive';

interface ChipProps {
  variant?: Variant;
  /** 도메인 태그처럼 키워드 느낌을 줄 때 monospace */
  mono?: boolean;
  onClick?: () => void;
  /** interactive/selected 토글 시 선택 상태 알림 */
  selected?: boolean;
  children: ReactNode;
}

export function Chip({
  variant = 'default',
  mono = false,
  onClick,
  selected,
  children,
}: ChipProps) {
  const cls = [styles.chip, styles[variant], mono && styles.mono]
    .filter(Boolean)
    .join(' ');

  if (onClick) {
    return (
      <button
        type="button"
        className={cls}
        onClick={onClick}
        aria-pressed={selected ?? (variant === 'selected')}
      >
        {children}
      </button>
    );
  }

  return <span className={cls}>{children}</span>;
}
