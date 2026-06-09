export type RouteType =
  | "consensus_report"
  | "need_more_context"
  | "definition_enrichment";

export type AnalyzeRequest = {
  text: string;
  senderRole: string;
  receiverRole: string;
  communicationType: string;
};

export type Participant = {
  name: string;
  role: string;
};

export type AnalyzeApiRequest = {
  text: string;
  participants: Participant[];
  communicationType: string;
};

export type JobResponse = {
  job_id: string;
};

export type WorkflowStep =
  | "context_intake"
  | "word_extractor"
  | "role_worker"
  | "risk_term"
  | "synthesis"
  | "report";

export type WorkflowProgressEvent = {
  type: "progress";
  step: WorkflowStep;
  label: string;
};

export type WorkflowDoneEvent = {
  type: "done";
  result: AnalyzeResponse;
};

export type WorkflowErrorEvent = {
  type: "error";
  message: string;
};

export type WorkflowEvent = WorkflowProgressEvent | WorkflowDoneEvent | WorkflowErrorEvent;

export type TermAnalysis = {
  term: string;
  context: string;
  currentMeaning: string;
  plannerView: string | null;
  developerView: string | null;
  designerView: string | null;
  pmView: string | null;
  riskLevel: "낮음" | "보통" | "높음" | string;
  riskReason: string;
  confirmationQuestion: string;
};

export type AnalyzeResponse = {
  summary: string;
  keyRequest: string;
  terms: TermAnalysis[];
  agreementQuestions: string[];
  checklist: string[];
  route?: RouteType;
  message?: string;
};

export type AnalysisHistoryItem = {
  id: string;
  summary: string;
  keyRequest: string;
  senderRole: string;
  createdAt: string;
};

export type TestCase = {
  id: string;
  scenarioName: string;
  primaryUser: string;
  route: RouteType;
  request: AnalyzeRequest;
  response: AnalyzeResponse;
};

export type AnalyzeState = "idle" | "loading" | "success" | "error";

export type AppPage = "analyze" | "history";
