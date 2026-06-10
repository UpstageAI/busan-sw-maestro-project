/** Banner · 공용 (Design.md §4.8) — status:limited 일 때 결과 상단 안내.
 *  내용은 백엔드 notice 텍스트 그대로 (가공 금지). */
import styles from './Banner.module.css';

interface BannerProps {
  /** 백엔드 notice 그대로 */
  message: string;
}

export function Banner({ message }: BannerProps) {
  return (
    <div className={styles.banner} role="status">
      <span className={styles.mark} aria-hidden="true">
        ⚠
      </span>
      <p className={styles.text}>{message}</p>
    </div>
  );
}
