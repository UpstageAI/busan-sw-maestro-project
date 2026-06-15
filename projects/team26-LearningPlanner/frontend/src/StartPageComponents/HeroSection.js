import HeroSlideshow from './HeroSlideshow';

function HeroSection({ onNavigateToPlanner }) {
  return (
    <section className="hero-section">
      <HeroSlideshow />

      <div className="hero-content">
        <div className="hero-inner">
          <p className="hero-label">For SMART LEARNERS</p>
          <h1 className="hero-heading">
            성장을 위한 기록,<br />완벽한 학습 파트너.
          </h1>
          <p className="hero-description">
            체계적인 계획부터 복습까지, 당신의 학습 여정을 스마트하게{' '}
            <br />관리하세요.{' '}
            몰입의 즐거움을 더해주는 디지털 학습 도구입니다.
          </p>
          <div className="hero-cta-wrapper">
            <button className="btn-primary" onClick={onNavigateToPlanner}>
              <span>나만의 계획 시작하기</span>
              <span className="material-symbols-outlined">trending_flat</span>
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

export default HeroSection;
