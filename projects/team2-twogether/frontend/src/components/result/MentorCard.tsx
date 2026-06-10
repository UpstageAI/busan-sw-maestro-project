/** MentorCard · FE-B (Design.md §4.3, S-04) — 추천 결과의 핵심 카드.
 *  reason 은 백엔드 텍스트 그대로(3줄 클램프). 클릭 시 상세 모달을 연다. */
import type { Mentor } from '../../types/api';
import { Chip } from '../common/Chip';
import { scoreTone } from './score';
import styles from './MentorCard.module.css';

interface MentorCardProps {
  mentor: Mentor;
  /** limited 응답이면 배지 톤다운(warn) */
  limited?: boolean;
  onOpen: (mentor: Mentor) => void;
}

export function MentorCard({ mentor, limited = false, onOpen }: MentorCardProps) {
  const tone = scoreTone(mentor.score, limited);

  return (
    <button
      type="button"
      className={styles.card}
      onClick={() => onOpen(mentor)}
      aria-label={`${mentor.name} 멘토 상세 보기, 적합도 ${mentor.score}`}
    >
      <div className={styles.top}>
        <span className={styles.avatar} aria-hidden="true">
          {mentor.name.slice(0, 1)}
        </span>
        <span className={styles.name}>{mentor.name}</span>
        <span className={`${styles.score} ${styles[tone]}`}>
          적합 {mentor.score}
        </span>
      </div>

      <div className={styles.domains}>
        {mentor.domain.map((d) => (
          <Chip key={d} mono>
            #{d}
          </Chip>
        ))}
      </div>

      <p className={styles.reason}>{mentor.reason}</p>

      {mentor.can_help.length > 0 && (
        <p className={styles.help}>
          <span className={styles.helpLabel}>도움 영역</span>
          {mentor.can_help.slice(0, 2).join(' · ')}
        </p>
      )}
    </button>
  );
}
