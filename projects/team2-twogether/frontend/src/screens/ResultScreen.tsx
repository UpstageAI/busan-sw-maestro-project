/** ResultScreen · S-04 · FE-B — 약점 요약 + 멘토 카드 2~3개 (+limited 배너).
 *  카드 클릭 → 상세 모달(S-05). [다시 입력하기] → 새 세션(S-01). */
import { useState } from 'react';
import type {
  LimitedResponse,
  Mentor,
  RecommendedResponse,
} from '../types/api';
import { Banner } from '../components/common/Banner';
import { Button } from '../components/common/Button';
import { MentorCard } from '../components/result/MentorCard';
import { MentorDetailModal } from '../components/result/MentorDetailModal';
import styles from './ResultScreen.module.css';

interface ResultScreenProps {
  data: RecommendedResponse | LimitedResponse;
  onReset: () => void;
}

export function ResultScreen({ data, onReset }: ResultScreenProps) {
  const [selected, setSelected] = useState<Mentor | null>(null);
  const limited = data.status === 'limited';

  return (
    <div className={`${styles.screen} view-enter`}>
      <section className={styles.gaps} aria-label="분석된 약점">
        <span className={styles.gapsLabel}>분석된 약점</span>
        <p className={styles.gapsText}>{data.gaps.join(' · ')}</p>
      </section>

      {limited && <Banner message={(data as LimitedResponse).notice} />}

      <h2 className={styles.heading}>추천 멘토</h2>

      <ul className={styles.list}>
        {data.mentors.map((mentor, i) => (
          <li
            key={mentor.name}
            className={styles.item}
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <MentorCard mentor={mentor} limited={limited} onOpen={setSelected} />
          </li>
        ))}
      </ul>

      <div className={styles.footer}>
        <Button variant="ghost" onClick={onReset}>
          다시 입력하기
        </Button>
      </div>

      <MentorDetailModal
        mentor={selected}
        open={selected !== null}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}
