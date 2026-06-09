import { useState, useEffect } from 'react';
import axios from 'axios';
import NavBar from './NavBar';
import InputPanel from './InputPanel';
import DisplayPanel, { DISPLAY_STATES } from './DisplayPanel';
import GuideSection from './GuideSection';
import { mockGenerate, mockBuild, mockSendEmail, mockChat } from '../mocks/mockApi';
import './MainPage.css';

const USE_MOCK = process.env.REACT_APP_USE_MOCK === 'true';
const API_URL  = USE_MOCK ? '' : (process.env.REACT_APP_API_URL ?? 'http://localhost:8000');

const CHAT_INIT = [{ role: 'ai', text: '안녕하세요! 커리큘럼에 대해 수정이 필요한 부분을 말씀해주세요.' }];

const api = {
  generate: (body) => USE_MOCK ? mockGenerate(body) : axios.post(`${API_URL}/api/generate`, body),
  build:    (body) => USE_MOCK ? mockBuild(body)    : axios.post(`${API_URL}/api/build`, body),
  chat:     (body) => USE_MOCK ? mockChat(body)     : axios.post(`${API_URL}/api/chat`, body),
};

function MainPage() {
  const [displayState, setDisplayState] = useState(DISPLAY_STATES.INITIAL);
  const [studyTarget, setStudyTarget]   = useState('');
  const [level, setLevel]               = useState('beginner');
  const [studyWeeks, setStudyWeeks]     = useState(4);
  const [questions, setQuestions]       = useState([]);
  const [answers, setAnswers]           = useState({});
  const [progress1, setProgress1]       = useState(0);
  const [progress2, setProgress2]       = useState(0);
  const [curriculumMarkdown, setCurriculumMarkdown] = useState('');
  const [generateError, setGenerateError] = useState('');
  const [buildError, setBuildError] = useState('');
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState(CHAT_INIT);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  /* Allow scrolling on this page (index.css disables it globally) */
  useEffect(() => {
    const prev = { overflowY: document.body.style.overflowY, overflowX: document.body.style.overflowX, height: document.body.style.height };
    document.body.style.overflowY = 'auto';
    document.body.style.overflowX = 'hidden';
    document.body.style.height    = 'auto';
    const root = document.getElementById('root');
    const prevRoot = { overflowY: root.style.overflowY, overflowX: root.style.overflowX, height: root.style.height };
    root.style.overflowY = 'auto';
    root.style.overflowX = 'hidden';
    root.style.height    = 'auto';
    return () => {
      document.body.style.overflowY = prev.overflowY;
      document.body.style.overflowX = prev.overflowX;
      document.body.style.height    = prev.height;
      root.style.overflowY = prevRoot.overflowY;
      root.style.overflowX = prevRoot.overflowX;
      root.style.height    = prevRoot.height;
    };
  }, []);

  const handleGenerate = async () => {
    setGenerateError('');
    setDisplayState(DISPLAY_STATES.LOADING_QUESTIONS);
    setProgress1(0);

    let prog = 0;
    const tick = setInterval(() => {
      prog = Math.min(prog + 2, 85);
      setProgress1(prog);
    }, 30);

    try {
      const res = await api.generate({ studyTarget, level, studyWeeks });
      const qs = res.data.questions ?? [];
      setQuestions(qs);
      const initAnswers = {};
      qs.forEach(q => { if (q.defaultValue !== undefined) initAnswers[q.id] = q.defaultValue; });
      setAnswers(initAnswers);
      clearInterval(tick);
      setProgress1(100);
      setTimeout(() => setDisplayState(DISPLAY_STATES.QUESTIONS), 500);
    } catch (err) {
      clearInterval(tick);
      setProgress1(0);
      setDisplayState(DISPLAY_STATES.INITIAL);
      setGenerateError('서버 요청에 실패했습니다. 다시 시도해주세요.');
      console.error('커리큘럼 생성 요청 실패:', err);
    }
  };

  const handleConfirmQuestions = async () => {
    setBuildError('');
    setDisplayState(DISPLAY_STATES.LOADING_BUILD);
    setProgress2(0);

    let prog = 0;
    const tick = setInterval(() => {
      prog = Math.min(prog + 1, 85);
      setProgress2(prog);
    }, 25);

    try {
      const response = await api.build({ studyTarget, level, studyWeeks, ...answers });
      setCurriculumMarkdown(response.data.curriculum ?? response.data);
      clearInterval(tick);
      setProgress2(100);
      setTimeout(() => setDisplayState(DISPLAY_STATES.RESULT), 500);
    } catch (err) {
      clearInterval(tick);
      setProgress2(0);
      setDisplayState(DISPLAY_STATES.QUESTIONS);
      setBuildError('서버 요청에 실패했습니다. 다시 시도해주세요.');
      console.error('커리큘럼 구축 요청 실패:', err);
    }
  };

  const handleChatSend = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const userMsg = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setChatLoading(true);
    try {
      const response = await api.chat({ message: userMsg, curriculum: curriculumMarkdown });
      setCurriculumMarkdown(response.data.curriculum);
      setChatMessages(prev => [...prev, { role: 'ai', text: response.data.reply }]);
    } catch (err) {
      const msg = err.response?.data?.error || '요청 처리 중 오류가 발생했습니다. 다시 시도해주세요.';
      setChatMessages(prev => [...prev, { role: 'ai', text: msg }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleReset = () => {
    setDisplayState(DISPLAY_STATES.INITIAL);
    setStudyTarget('');
    setQuestions([]);
    setAnswers({});
    setProgress1(0);
    setProgress2(0);
    setCurriculumMarkdown('');
    setChatOpen(false);
    setChatMessages(CHAT_INIT);
    setChatInput('');
  };

  const handleCopy = () => {
    const cleaned = curriculumMarkdown
      .replace(/\n\n---\n\n> \*\*수정 반영됨\*\*:[^\n]*/g, '')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
    navigator.clipboard.writeText(cleaned).then(() => {
      alert('커리큘럼 내용이 클립보드에 복사되었습니다.');
    });
  };

  return (
    <div className="mp-root">
      {/* Background */}
      <div className="mp-mesh-bg" />
      <div
        className="mp-paper-texture"
        style={{ backgroundImage: `url(${process.env.PUBLIC_URL}/images/MainBackground.png)` }}
      />
      <div className="mp-glow-sphere mp-glow-1" />
      <div className="mp-glow-sphere mp-glow-2" />

      {/* Nav */}
      <NavBar />

      {/* Main */}
      <main className="mp-main">
        <div className="mp-container">
          <div className="mp-grid">
            {/* Left: Input */}
            <div>
              <InputPanel
                studyTarget={studyTarget}
                setStudyTarget={setStudyTarget}
                level={level}
                setLevel={setLevel}
                studyWeeks={studyWeeks}
                setStudyWeeks={setStudyWeeks}
                onGenerate={handleGenerate}
                generateError={generateError}
              />
            </div>

            {/* Right: Display */}
            <DisplayPanel
              displayState={displayState}
              progress1={progress1}
              progress2={progress2}
              studyTarget={studyTarget}
              questions={questions}
              answers={answers}
              onAnswerChange={(id, val) => setAnswers(prev => ({ ...prev, [id]: val }))}
              curriculumMarkdown={curriculumMarkdown}
              buildError={buildError}
              onConfirmQuestions={handleConfirmQuestions}
              onReset={handleReset}
              onCopy={handleCopy}
              chatOpen={chatOpen}
              onToggleChat={() => setChatOpen(prev => !prev)}
              chatMessages={chatMessages}
              chatInput={chatInput}
              onChatInput={setChatInput}
              onChatSend={handleChatSend}
              chatLoading={chatLoading}
            />
          </div>

          {/* Guide Section */}
          <GuideSection />
        </div>
      </main>
    </div>
  );
}

export default MainPage;
