import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import html2pdf from 'html2pdf.js';

export const DISPLAY_STATES = {
  INITIAL:           'initial',
  LOADING_QUESTIONS: 'loading-questions',
  QUESTIONS:         'questions',
  LOADING_BUILD:     'loading-build',
  RESULT:            'result',
};

/* ── State: Initial ── */
function StateInitial() {
  return (
    <div className="mp-state-initial">
      <div className="mp-hero-img-wrapper">
        <div className="mp-hero-img-glow" />
        <div className="mp-hero-img-circle">
          <img
            className="mp-hero-img"
            alt="Study space atmosphere"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBMVL7_qywioQdcEnR4V1FKr2C_-9gLLrcc3LrZZUvKPeUHq6DK4yBbyaiHAbYHrK7vpaYAmlB45Dpv_m-TOAgq8UqFmyb-v14IEob69ZwOVCpqJ5Zx4ftE0K8PnT2wVfMB8fU5zrNbD7Myxt-oo4_VsBKy67Ba7mKJVhtL2lAiyzAb6O7NUjWLxybiXyrmKfFAit7VPs4NFUUTQYkL5FhVuzKEZO0oSw2nnMnnizFwaQDt5SapcaSnWpZK_UJMDjIIMNzw3unwJpLY"
          />
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h2 className="mp-initial-title">당신의 꿈을 위한 첫걸음</h2>
        <p className="mp-initial-desc">나만을 위한 맞춤형 학습 로드맵을 설계해보세요.</p>
      </div>

      <div className="mp-initial-badges">
        <span className="mp-badge">
          <span className="material-symbols-outlined">lightbulb</span>
          개인화된 학습
        </span>
        <span className="mp-badge">
          <span className="material-symbols-outlined">auto_graph</span>
          효율적인 경로
        </span>
      </div>

      <div className="mp-initial-guide">
        <p>
          <span className="mp-guide-step">1</span> 학습 대상과 역량 수준을 입력하세요.
        </p>
        <p>
          <span className="mp-guide-step">2</span> 목표·시간·방식을 선택하면 AI가 로드맵을 생성합니다.
        </p>
      </div>
    </div>
  );
}

/* ── State: Loading ── */
function StateLoading({ text, progress }) {
  return (
    <div className="mp-state-loading">
      <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <p className="mp-loading-text">{text}</p>
        <p className="mp-loading-pct">{progress}%</p>
      </div>
      <div className="mp-progress-bar">
        <div className="mp-progress-fill" style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}

/* ── State: Questions ── */
function StateQuestions({ questions, answers, onAnswerChange, onConfirm, buildError }) {
  const [submitted, setSubmitted] = React.useState(false);

  const errors = React.useMemo(() => {
    const errs = {};
    questions.forEach(q => {
      if (!q.required) return;
      const val = answers[q.id];
      if (q.type === 'text' && !val?.trim()) errs[q.id] = true;
      if (q.type === 'choice' && !val) errs[q.id] = true;
    });
    return errs;
  }, [questions, answers]);

  const handleConfirm = () => {
    setSubmitted(true);
    if (Object.keys(errors).length > 0) return;
    onConfirm();
  };

  return (
    <div className="mp-state-questions">
      <div className="mp-questions-header">
        <h2 className="mp-questions-title">맞춤형 분석을 위한 추가 질문</h2>
        <p className="mp-questions-sub">더 정확한 로드맵을 위해 아래 정보를 입력해주세요.</p>
      </div>

      <div style={{ maxWidth: '560px', margin: '0 auto', width: '100%' }}>
        {questions.map(q => (
          <div key={q.id} className="mp-question-block">
            <label className="mp-q-label">{q.label}</label>

            {q.type === 'text' && (
              <input
                className={`mp-q-input${submitted && errors[q.id] ? ' mp-input-invalid' : ''}`}
                placeholder={q.placeholder}
                type="text"
                value={answers[q.id] ?? ''}
                onChange={e => onAnswerChange(q.id, e.target.value)}
              />
            )}

            {q.type === 'select' && (
              <select
                className="mp-q-select"
                value={answers[q.id] ?? q.defaultValue ?? ''}
                onChange={e => onAnswerChange(q.id, e.target.value)}
              >
                {q.options.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            )}

            {q.type === 'choice' && (
              <div className={`mp-pref-grid${submitted && errors[q.id] ? ' mp-pref-invalid' : ''}`}>
                {q.options.map(opt => (
                  <button
                    key={opt.value}
                    className={`mp-pref-btn${answers[q.id] === opt.value ? ' selected' : ''}`}
                    onClick={() => onAnswerChange(q.id, opt.value)}
                  >
                    <span className="material-symbols-outlined">
                      {/^[a-z][a-z0-9_]*$/.test(opt.icon) ? opt.icon : 'help_outline'}
                    </span>
                    <span className="mp-pref-label">{opt.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}

        {submitted && Object.keys(errors).length > 0 && (
          <p className="mp-input-error">
            <span className="material-symbols-outlined">error</span>
            필수 항목을 모두 입력해주세요.
          </p>
        )}
        {buildError && (
          <p className="mp-input-error">
            <span className="material-symbols-outlined">error</span>
            {buildError}
          </p>
        )}

        <button className="mp-confirm-btn" onClick={handleConfirm}>
          확인 및 커리큘럼 구축
          <span className="material-symbols-outlined">arrow_forward</span>
        </button>
      </div>
    </div>
  );
}

function normalizeMarkdown(md) {
  return md
    .replace(/\r\n/g, '\n')                    // CRLF → LF
    .replace(/\r/g, '\n')                       // CR → LF
    .replace(/([^\n])(#{1,6} )/g, '$1\n\n$2')  // inline heading → blank line before
    .replace(/\n(#{1,6} )/g, '\n\n$1')          // single newline before heading → blank line
    .replace(/\n{3,}/g, '\n\n');                 // collapse excess blank lines
}

/* ── State: Result ── */
function StateResult({ studyTarget, curriculumMarkdown, onReset, onCopy, chatOpen, onToggleChat }) {
  const handleDownloadPdf = () => {
    const element = document.getElementById('mp-markdown-body');
    html2pdf().set({
      margin: 10,
      filename: `${studyTarget}_커리큘럼.pdf`,
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
    }).from(element).save();
  };

  return (
    <div className="mp-state-result">
      <div className="mp-result-header">
        <div>
          <h2 className="mp-result-title">{studyTarget} 마스터 로드맵</h2>
          <p className="mp-result-sub">AI에 의해 생성된 개별화된 로드맵입니다.</p>
        </div>
        <div className="mp-result-actions">
          <button className="mp-icon-btn" onClick={onCopy} title="복사하기">
            <span className="material-symbols-outlined">content_copy</span>
          </button>
          <button className="mp-icon-btn" onClick={handleDownloadPdf} title="PDF 다운로드">
            <span className="material-symbols-outlined">download</span>
          </button>
          <button
            className={`mp-icon-btn${chatOpen ? ' mp-icon-btn--active' : ''}`}
            onClick={onToggleChat}
            title="AI와 수정하기"
          >
            <span className="material-symbols-outlined">chat</span>
          </button>
          <button className="mp-reset-btn" onClick={onReset}>다시 만들기</button>
        </div>
      </div>

      <div className="mp-result-body">
        <div className="mp-markdown" id="mp-markdown-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {normalizeMarkdown(curriculumMarkdown)}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

/* ── Chat Panel ── */
function ChatPanel({ messages, input, onInputChange, onSend, loading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="mp-chat-panel">
      <div className="mp-chat-header">
        <span className="material-symbols-outlined mp-chat-header-icon">chat</span>
        <span className="mp-chat-header-title">AI와 커리큘럼 수정하기</span>
      </div>

      <div className="mp-chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`mp-chat-msg mp-chat-msg--${msg.role}`}>
            {msg.role === 'ai' && (
              <span className="material-symbols-outlined mp-chat-avatar">smart_toy</span>
            )}
            <div className="mp-chat-bubble">{msg.text}</div>
            {msg.role === 'user' && (
              <span className="material-symbols-outlined mp-chat-avatar">person</span>
            )}
          </div>
        ))}
        {loading && (
          <div className="mp-chat-msg mp-chat-msg--ai">
            <span className="material-symbols-outlined mp-chat-avatar">smart_toy</span>
            <div className="mp-chat-bubble mp-chat-typing">
              <span /><span /><span />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="mp-chat-input-row">
        <input
          className="mp-chat-input"
          placeholder="메시지를 입력하세요..."
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="mp-chat-send"
          onClick={onSend}
          disabled={loading || !input.trim()}
        >
          <span className="material-symbols-outlined">send</span>
        </button>
      </div>
    </div>
  );
}

/* ── DisplayPanel ── */
function DisplayPanel({
  displayState,
  progress1,
  progress2,
  studyTarget,
  questions,
  answers,
  onAnswerChange,
  curriculumMarkdown,
  buildError,
  onConfirmQuestions,
  onReset,
  onCopy,
  chatOpen,
  onToggleChat,
  chatMessages,
  chatInput,
  onChatInput,
  onChatSend,
  chatLoading,
}) {
  const centered =
    displayState === DISPLAY_STATES.INITIAL ||
    displayState === DISPLAY_STATES.LOADING_QUESTIONS ||
    displayState === DISPLAY_STATES.LOADING_BUILD;

  const isResult = displayState === DISPLAY_STATES.RESULT;

  return (
    <div className="mp-display-col">
      <div className={`mp-display-container${centered ? '' : ' align-start'}`}>
        {displayState === DISPLAY_STATES.INITIAL && <StateInitial />}

        {displayState === DISPLAY_STATES.LOADING_QUESTIONS && (
          <StateLoading text="질문을 생성하고 있습니다..." progress={progress1} />
        )}

        {displayState === DISPLAY_STATES.QUESTIONS && (
          <StateQuestions
            questions={questions}
            answers={answers}
            onAnswerChange={onAnswerChange}
            onConfirm={onConfirmQuestions}
            buildError={buildError}
          />
        )}

        {displayState === DISPLAY_STATES.LOADING_BUILD && (
          <StateLoading text="맞춤형 커리큘럼을 구축하고 있습니다..." progress={progress2} />
        )}

        {isResult && (
          <StateResult
            studyTarget={studyTarget}
            curriculumMarkdown={curriculumMarkdown}
            onReset={onReset}
            onCopy={onCopy}
            chatOpen={chatOpen}
            onToggleChat={onToggleChat}
          />
        )}
      </div>

      {isResult && chatOpen && (
        <ChatPanel
          messages={chatMessages}
          input={chatInput}
          onInputChange={onChatInput}
          onSend={onChatSend}
          loading={chatLoading}
        />
      )}
    </div>
  );
}

export default DisplayPanel;
