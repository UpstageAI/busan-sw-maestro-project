/** App — 단일 viewState 상태 머신 (AGENT.md §4). 라우터 없음.
 *  INPUT → LOADING →(need_clarification) CLARIFY → LOADING → RESULT | EMPTY | ERROR
 *  재검색(low_confidence)은 화면 전환 없이 useRecommend 의 refining 플래그로만 표현. */
import { useRef, useState } from 'react';
import type {
  LimitedResponse,
  RecommendedResponse,
} from './types/api';
import { useRecommend } from './hooks/useRecommend';
import type { SubmitInput } from './hooks/useRecommend';
import { InputScreen } from './screens/InputScreen';
import type { ProjectInput } from './screens/InputScreen';
import { LoadingScreen } from './screens/LoadingScreen';
import { ClarifyScreen } from './screens/ClarifyScreen';
import { ResultScreen } from './screens/ResultScreen';
import { StateView } from './components/result/StateView';

type View = 'INPUT' | 'LOADING' | 'CLARIFY' | 'RESULT' | 'EMPTY' | 'ERROR';

interface ClarifyState {
  question: string;
  options?: string[];
}

function App() {
  const [view, setView] = useState<View>('INPUT');
  const [clarify, setClarify] = useState<ClarifyState | null>(null);
  const [result, setResult] = useState<RecommendedResponse | LimitedResponse | null>(
    null,
  );
  const lastInputRef = useRef<SubmitInput | null>(null);

  const rec = useRecommend();

  /** 추천 실행 + status 에 따라 화면 분기 (AGENT.md §5 표) */
  const run = async (input: SubmitInput) => {
    lastInputRef.current = input;
    setView('LOADING');
    try {
      const res = await rec.submit(input);
      if (res.status === 'need_clarification') {
        // 확인 질문 라운드는 1회 가정. 2회째가 와도 답변 후 결과로 진행하도록 방어
        // (mock 은 clarify_answer 가 있으면 항상 추천을 반환).
        setClarify({ question: res.question, options: res.options });
        setView('CLARIFY');
      } else if (res.mentors.length === 0) {
        setView('EMPTY');
      } else {
        setResult(res);
        setView('RESULT');
      }
    } catch {
      setView('ERROR');
    }
  };

  const handleInputSubmit = (input: ProjectInput) =>
    run({ ...input, clarify_answer: null });

  const handleClarifySubmit = (answer: string) => {
    const base = lastInputRef.current;
    if (!base) return;
    run({ ...base, clarify_answer: answer });
  };

  const handleReset = () => {
    rec.reset();
    setClarify(null);
    setResult(null);
    setView('INPUT');
  };

  const handleRetry = () => {
    if (lastInputRef.current) run(lastInputRef.current);
    else handleReset();
  };

  return (
    <div className="app-shell">
      <main className="app-main">
        {view === 'INPUT' && (
          <InputScreen submitting={false} onSubmit={handleInputSubmit} />
        )}

        {view === 'LOADING' && (
          <LoadingScreen
            step={rec.step}
            refining={rec.refining}
            timedOut={rec.timedOut}
          />
        )}

        {view === 'CLARIFY' && clarify && (
          <ClarifyScreen
            question={clarify.question}
            options={clarify.options}
            onSubmit={handleClarifySubmit}
            onReset={handleReset}
          />
        )}

        {view === 'RESULT' && result && (
          <ResultScreen data={result} onReset={handleReset} />
        )}

        {view === 'EMPTY' && (
          <StateView
            type="empty"
            action={{ label: '다시 입력하기', onClick: handleReset }}
          />
        )}

        {view === 'ERROR' && (
          <StateView
            type="error"
            message={rec.error ?? undefined}
            action={{ label: '다시 시도', onClick: handleRetry }}
          />
        )}
      </main>
    </div>
  );
}

export default App;
