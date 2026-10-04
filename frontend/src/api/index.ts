import { downloadFile, get, post, upload } from "./client";

import type {
  DocumentSummary,
  ExportFormatInfo,
  GenerateResult,
  HealthInfo,
  IntegrationInfo,
  MethodInfo,
  RequirementDoc,
  TestCaseSuite,
} from "./types";

export interface GeneratePayload {
  doc_id?: string | null;
  text?: string | null;
  title?: string;
  methods: string[];
  use_llm: boolean;
  use_llm_in_design: boolean;
  max_items: number;
}

export const api = {
  health: () => get<HealthInfo>("/health"),
  integrations: () => get<IntegrationInfo[]>("/integrations"),

  methods: () => get<MethodInfo[]>("/testcases/methods"),
  exportFormats: () => get<ExportFormatInfo[]>("/export/formats"),

  documents: (limit = 20) => get<DocumentSummary[]>("/documents", { limit }),
  document: (docId: string) => get<DocumentSummary>(`/documents/${docId}`),
  uploadDocument: (file: File) =>
    upload<DocumentSummary>("/documents/upload", file),

  requirement: (docId: string) =>
    get<RequirementDoc>(`/requirements/${docId}`),
  parseRequirement: (payload: {
    doc_id?: string | null;
    text?: string | null;
    title: string;
    use_llm: boolean;
    max_items: number;
  }) => post<RequirementDoc>("/requirements/parse", payload),
  generateFromRequirement: (
    docId: string,
    methods: string[],
    useLlmInDesign: boolean,
  ) =>
    post<TestCaseSuite>(
      `/requirements/${docId}/testcases`,
      undefined,
      { methods: methods.join(","), use_llm_in_design: useLlmInDesign },
    ),

  suites: (limit = 20) => get<TestCaseSuite[]>("/testcases/suites", { limit }),
  suite: (suiteId: string) => get<TestCaseSuite>(`/testcases/${suiteId}`),

  generate: (payload: GeneratePayload) =>
    post<GenerateResult>("/pipeline/generate", payload),

  exportSuite: (suiteId: string, format: string) =>
    downloadFile(`/export/${encodeURIComponent(suiteId)}/${format}`),
};

export { ApiError, saveBlob } from "./client";
export { http } from "./client";
export type * from "./types";
