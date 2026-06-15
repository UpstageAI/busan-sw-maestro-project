const MOCK_CURRICULUM = `
# Python 마스터 로드맵

## 1단계: 기초 다지기 (1~2주)

### 핵심 개념
- 변수, 자료형, 연산자
- 조건문 (if / elif / else)
- 반복문 (for / while)
- 함수 정의 및 호출

### 추천 자료
- **영상**: 점프 투 파이썬 (유튜브)
- **문서**: 파이썬 공식 튜토리얼 (docs.python.org)

---

## 2단계: 중급 개념 (3~4주)

### 핵심 개념
- 리스트, 딕셔너리, 튜플, 집합
- 클래스와 객체지향 프로그래밍
- 파일 입출력
- 예외 처리 (try / except)

### 추천 자료
- **영상**: 모두의 파이썬 (인프런)
- **실습**: 백준 온라인 저지 (단계별 문제풀기)

---

## 3단계: 실전 프로젝트 (5~8주)

### 프로젝트 아이디어
1. **웹 스크래핑**: BeautifulSoup + requests로 데이터 수집
2. **데이터 분석**: pandas + matplotlib으로 시각화
3. **간단한 API 서버**: FastAPI로 REST API 개발

### 추천 자료
- **문서**: FastAPI 공식 문서
- **강의**: 파이썬으로 배우는 데이터 분석 (Coursera)

---

## 학습 팁

> 매일 30분 이상 코드를 직접 작성하는 것이 중요합니다.
> 에러 메시지를 두려워하지 말고, 읽고 이해하는 연습을 하세요.

| 주차 | 목표 | 완료 기준 |
|------|------|-----------|
| 1~2주 | 기초 문법 | 간단한 계산기 구현 |
| 3~4주 | OOP 이해 | 클래스 기반 프로그램 작성 |
| 5~8주 | 프로젝트 완성 | GitHub에 코드 업로드 |
`;

const delay = (ms) => new Promise((res) => setTimeout(res, ms));

export const mockGenerate = async () => {
  await delay(800);
  return {
    data: {
      questions: [
        {
          id: 'prob1',
          label: '1. 구체적인 학습 목표는 무엇인가요?',
          type: 'text',
          placeholder: '예: 취업용 포트폴리오 제작, 자격증 취득',
          required: true,
        },
        {
          id: 'prob2',
          label: '2. 하루 평균 학습 가능한 시간은?',
          type: 'select',
          defaultValue: '1-2',
          options: [
            { value: '1-2', label: '1~2시간 (틈틈이 학습)' },
            { value: '3-5', label: '3~5시간 (집중 학습)' },
            { value: '6+',  label: '6시간 이상 (전일제 학습)' },
          ],
        },
        {
          id: 'prob3',
          label: '3. 선호하는 학습 방식은?',
          type: 'choice',
          required: true,
          options: [
            { value: 'video', label: '영상 중심',        icon: 'play_circle' },
            { value: 'text',  label: '텍스트/문서 중심', icon: 'menu_book' },
          ],
        },
      ],
    },
  };
};

export const mockBuild = async () => {
  await delay(1200);
  return { data: { curriculum: MOCK_CURRICULUM } };
};

export const mockSendEmail = async ({ email }) => {
  await delay(900);
  console.log(`[Mock] 이메일 전송 완료 → ${email}`);
  return { data: { message: 'sent' } };
};

export const mockChat = async ({ message, curriculum }) => {
  await delay(1000);
  const updated = curriculum + `\n\n---\n\n> **수정 반영됨**: "${message}" 요청이 적용되었습니다.`;
  return {
    data: {
      curriculum: updated,
      reply: `"${message}" 요청을 반영하여 커리큘럼을 업데이트했습니다.`,
    },
  };
};
