/** MentorDetailModal · FE-B (Design.md §4.4, S-05) — 멘토 전체 프로필 모달.
 *  추가 API 호출 없음(데이터는 결과 응답에 포함). 포커스 트랩 / ESC·배경·✕ 닫기 /
 *  닫으면 카드로 포커스 복귀. "멘토링 신청/연락" 버튼 없음(MVP 외부 실행 제외). */
import { useEffect, useRef } from 'react';
import type { Mentor } from '../../types/api';
import { Chip } from '../common/Chip';
import styles from './MentorDetailModal.module.css';

interface MentorDetailModalProps {
  mentor: Mentor | null;
  open: boolean;
  onClose: () => void;
}

const FOCUSABLE =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

export function MentorDetailModal({ mentor, open, onClose }: MentorDetailModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const closeBtnRef = useRef<HTMLButtonElement>(null);
  const prevFocusRef = useRef<HTMLElement | null>(null);

  // 열릴 때: 이전 포커스 저장 후 닫기 버튼으로 이동. 닫힐 때: 복귀.
  useEffect(() => {
    if (open) {
      prevFocusRef.current = document.activeElement as HTMLElement;
      // 다음 틱에 포커스(렌더 후)
      const id = window.setTimeout(() => closeBtnRef.current?.focus(), 0);
      return () => window.clearTimeout(id);
    }
    prevFocusRef.current?.focus();
    return undefined;
  }, [open]);

  // ESC 닫기 + 포커스 트랩(Tab 순환)
  useEffect(() => {
    if (!open) return undefined;

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onClose();
        return;
      }
      if (e.key !== 'Tab') return;
      const panel = panelRef.current;
      if (!panel) return;
      const nodes = Array.from(
        panel.querySelectorAll<HTMLElement>(FOCUSABLE),
      ).filter((n) => !n.hasAttribute('disabled'));
      if (nodes.length === 0) return;
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  if (!open || !mentor) return null;

  const titleId = 'mentor-modal-title';

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div
        ref={panelRef}
        className={styles.panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        <header className={styles.header}>
          <span className={styles.avatar} aria-hidden="true">
            {mentor.name.slice(0, 1)}
          </span>
          <div className={styles.headText}>
            <h2 id={titleId} className={styles.name}>
              {mentor.name}
            </h2>
            <p className={styles.summary}>{mentor.profile_summary}</p>
          </div>
          <button
            ref={closeBtnRef}
            type="button"
            className={styles.close}
            onClick={onClose}
            aria-label="닫기"
          >
            ✕
          </button>
        </header>

        <div className={styles.domains}>
          {mentor.domain.map((d) => (
            <Chip key={d} mono>
              #{d}
            </Chip>
          ))}
          {mentor.keywords.map((k) => (
            <Chip key={k}>{k}</Chip>
          ))}
        </div>

        <section className={styles.section}>
          <h3 className={`${styles.secTitle} ${styles.help}`}>
            ✓ 도움을 줄 수 있는 상황
          </h3>
          <ul className={styles.list}>
            {mentor.can_help.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </section>

        <section className={styles.section}>
          <h3 className={`${styles.secTitle} ${styles.less}`}>
            △ 상대적으로 덜 맞는 영역
          </h3>
          <ul className={styles.list}>
            {mentor.less_relevant_for.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </section>

        <section className={styles.section}>
          <h3 className={styles.secTitle}>이 프로젝트 추천 이유</h3>
          <p className={styles.reason}>{mentor.reason}</p>
        </section>

        <p className={styles.note}>멘토링 신청·연락은 직접 진행해 주세요.</p>
      </div>
    </div>
  );
}
