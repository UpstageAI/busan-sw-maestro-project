const CARDS = [
  {
    icon: 'edit_calendar',
    title: '커리큘럼 설계',
    desc: '학습 대상과 수준을 입력하여 맞춤형 계획을 세웁니다.',
    clickable: false,
  },
  {
    icon: 'auto_awesome',
    title: 'AI 기반 추천',
    desc: 'AI가 분석한 최적의 학습 경로와 자료를 제안받습니다.',
    clickable: false,
  },
  {
    icon: 'picture_as_pdf',
    title: 'PDF 다운로드',
    desc: '완성된 커리큘럼을 PDF 파일로 저장하거나 복사합니다.',
    clickable: false,
  },
  {
    icon: 'monitoring',
    title: '학습 리포트',
    desc: '진행 상황을 시각적으로 확인하고 성장을 기록합니다.',
    clickable: false,
  },
];

function GuideSection() {
  return (
    <section className="mp-guide-section">
      <h2 className="mp-guide-title">학습 플래너 활용 가이드</h2>

      <div className="mp-guide-grid">
        {CARDS.map(({ icon, title, desc, clickable }) => (
          <div
            key={title}
            className={`mp-guide-card${clickable ? ' clickable' : ''}`}
          >
            <div className="mp-guide-icon-wrap">
              <span className="material-symbols-outlined">{icon}</span>
            </div>
            <div className="mp-guide-card-body">
              <h3 className="mp-guide-card-title">{title}</h3>
              <p className="mp-guide-card-desc">{desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default GuideSection;
