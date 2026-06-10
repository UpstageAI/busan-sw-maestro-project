/** Button · 공용 (Design.md §4.1) — primary/ghost/text · md/sm · loading 시 중복 제출 차단 */
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './Button.module.css';

type Variant = 'primary' | 'ghost' | 'text';
type Size = 'md' | 'sm';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  /** 로딩 중에는 스피너 표시 + 버튼 잠금(중복 제출 방지) */
  loading?: boolean;
  children: ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  className,
  type = 'button',
  ...rest
}: ButtonProps) {
  const cls = [styles.btn, styles[variant], styles[size], className]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      type={type}
      className={cls}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading && <span className={styles.spinner} aria-hidden="true" />}
      <span>{children}</span>
    </button>
  );
}
