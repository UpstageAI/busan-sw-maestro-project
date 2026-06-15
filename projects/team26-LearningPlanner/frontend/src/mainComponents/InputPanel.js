import { useState } from 'react';

const LEVEL_DESC = {
  beginner:     '기초 개념부터 차근차근',
  intermediate: '핵심 원리 이해와 심화',
  advanced:     '전문가 수준의 실전 문제',
};

const GLIDER_STYLE = {
  beginner: {
    transform: 'translateX(0)',
    background: 'linear-gradient(135deg, #e2e2e2 0%, #bbbbbb 100%)',
    boxShadow: '0 4px 15px rgba(187,187,187,0.3)',
  },
  intermediate: {
    transform: 'translateX(100%)',
    background: 'linear-gradient(135deg, #747878 0%, #444748 100%)',
    boxShadow: '0 4px 15px rgba(68,71,72,0.3)',
  },
  advanced: {
    transform: 'translateX(200%)',
    background: 'linear-gradient(135deg, #333434 0%, #1c1b1b 100%)',
    boxShadow: '0 4px 15px rgba(28,27,27,0.3)',
  },
};

const LABEL_COLOR = {
  beginner:     ['#1c1b1b', '#747878', '#747878'],
  intermediate: ['#747878', '#ffffff', '#747878'],
  advanced:     ['#747878', '#747878', '#ffffff'],
};

function InputPanel({ studyTarget, setStudyTarget, level, setLevel, studyWeeks, setStudyWeeks, onGenerate, generateError }) {
  const [desc, setDesc] = useState(LEVEL_DESC.beginner);
  const [fading, setFading] = useState(false);
  const [showError, setShowError] = useState(false);

  const handleLevelChange = (val) => {
    setLevel(val);
    setFading(true);
    setTimeout(() => {
      setDesc(LEVEL_DESC[val]);
      setFading(false);
    }, 200);
  };

  const colors = LABEL_COLOR[level];

  return (
    <div className="mp-input-panel">
      <h1 className="mp-panel-title">커리큘럼 설정</h1>

      <div className="mp-form-stack">
        {/* Study Target */}
        <div>
          <fieldset className={`mp-fieldset${showError ? ' mp-fieldset-error' : ''}`}>
            <legend className="mp-legend">학습 대상</legend>
            <input
              className="mp-text-input"
              placeholder="예: 초등 수학, 프론트엔드 개발"
              type="text"
              value={studyTarget}
              onChange={(e) => {
                setStudyTarget(e.target.value);
                if (e.target.value.trim()) setShowError(false);
              }}
            />
          </fieldset>
          {showError && (
            <p className="mp-input-error">
              <span className="material-symbols-outlined">error</span>
              학습 대상을 입력해주세요.
            </p>
          )}
        </div>

        {/* Study Duration */}
        <div className="mp-level-group">
          <label className="mp-level-label">학습 기간</label>
          <div className="mp-weeks-row">
            <button
              type="button"
              className="mp-weeks-btn"
              onClick={() => setStudyWeeks(w => Math.max(1, w - 1))}
            >−</button>
            <span className="mp-weeks-value">{studyWeeks}주</span>
            <button
              type="button"
              className="mp-weeks-btn"
              onClick={() => setStudyWeeks(w => Math.min(52, w + 1))}
            >+</button>
          </div>
        </div>

        {/* Level Radio */}
        <div className="mp-level-group">
          <label className="mp-level-label">학습 역량</label>

          <div className="mp-radio-container">
            <input type="radio" id="mp-radio-1" name="mp-level" value="beginner"
              checked={level === 'beginner'} onChange={() => handleLevelChange('beginner')} />
            <label className="mp-radio-label" htmlFor="mp-radio-1"
              style={{ color: colors[0] }}>초급</label>

            <input type="radio" id="mp-radio-2" name="mp-level" value="intermediate"
              checked={level === 'intermediate'} onChange={() => handleLevelChange('intermediate')} />
            <label className="mp-radio-label" htmlFor="mp-radio-2"
              style={{ color: colors[1] }}>중급</label>

            <input type="radio" id="mp-radio-3" name="mp-level" value="advanced"
              checked={level === 'advanced'} onChange={() => handleLevelChange('advanced')} />
            <label className="mp-radio-label" htmlFor="mp-radio-3"
              style={{ color: colors[2] }}>고급</label>

            <span className="mp-glider" style={GLIDER_STYLE[level]} />
          </div>

          <div style={{ padding: '4px 8px' }}>
            <p className={`mp-level-desc${fading ? ' fading' : ''}`}>{desc}</p>
          </div>
        </div>

        {/* Generate Button */}
        <button className="mp-generate-btn" onClick={() => {
          if (!studyTarget.trim()) { setShowError(true); return; }
          onGenerate();
        }}>
          <span className="material-symbols-outlined">auto_awesome</span>
          커리큘럼 생성
        </button>

        {generateError && (
          <p className="mp-input-error">
            <span className="material-symbols-outlined">error</span>
            {generateError}
          </p>
        )}
      </div>
    </div>
  );
}

export default InputPanel;
