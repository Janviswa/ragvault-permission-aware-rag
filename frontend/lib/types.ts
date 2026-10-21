export type Role = "Admin" | "Manager" | "Employee";

export type Me = {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  tenant_id: string;
  tenant_name: string;
};

export type DocumentItem = {
  id: number;
  title: string;
  file_name: string;
  classification: string;
  created_at: string;
  summary: string;
  word_count: number;
};

export type DocumentDetails = {
  id: number;
  title: string;
  file_name: string;
  content: string | null;
  tenant_id: string;
  classification: string;
};

export type Source = {
  document_id: number;
  title: string;
  file_name: string;
  chunk_index: number;
};

export type RestrictedDocument = {
  document_id: number;
  title: string;
  file_name: string;
  classification: string;
  required_roles: string[];
  your_role: string;
};

export type ChatMessage = {
  id: number | string;
  role: "user" | "assistant";
  content: string;
  sources: Source[];
  restricted: RestrictedDocument | null;
  created_at?: string;
  /** true while the answer is still being written */
  streaming?: boolean;
};

export type ChatSummary = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type ChatDetail = { id: number; title: string; messages: ChatMessage[] };

export type QueryResponse = {
  question: string;
  answer: string;
  sources: Source[];
  chat_id: number;
  restricted: RestrictedDocument | null;
};

export type MyAccessRequest = {
  id: number;
  document_id: number;
  document_title: string;
  file_name: string;
  classification: string;
  status: "pending" | "approved" | "rejected";
  reason: string | null;
  requested_at: string;
  decided_at: string | null;
  decided_by: string | null;
  /** set when the approval was temporary */
  access_expires_at: string | null;
  approvers: string[];
};

export type AdminAccessRequest = {
  id: number;
  user_id: number;
  user_name: string;
  user_email: string;
  user_role: string;
  document_id: number;
  document_title: string;
  document_classification: string;
  status: "pending" | "approved" | "rejected";
  reason: string | null;
  requested_at: string;
  decided_at: string | null;
  decided_by: string | null;
  access_expires_at: string | null;
};

export type AdminUser = {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
};

export type Permission = { id: number; document_id: number; user_id: number | null; role: string | null; permission: string };

export type TemporaryAccess = {
  id: number;
  document_id: number;
  document_title: string;
  user_id: number;
  user_email: string;
  expires_at: string;
};

export type SecurityEvent = {
  id: number;
  event_type: string;
  severity: "low" | "medium" | "high" | "critical" | string;
  status: string;
  user_id: number | null;
  details: string | null;
  created_at: string;
};

export type AuditLog = {
  id: number;
  user_id: number | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  status: string;
  details: string | null;
  created_at: string;
};

export type AnalyticsSummary = {
  totals: { users: number; active_users: number; documents: number; pending_requests: number; open_security_events: number };
  users_by_role: Record<string, number>;
  documents_by_classification: Record<string, number>;
  open_events_by_severity: Record<string, number>;
  range: "7d" | "1m" | "3m";
  bucket_days: number;
  activity: ActivityPoint[];
  today: { queries: number; document_views: number; security_events: number };
};

export type AnalyticsRange = AnalyticsSummary["range"];

export type LeakageResult = {
  ran_at: string;
  passed: boolean;
  users_tested: number;
  probes: number;
  capped: boolean;
  leaks: { user_id: number; user_email: string; document_id: number; probe_document_id: number }[];
};

export type Health = { api?: string; postgres?: string; qdrant?: string };

export type ActivityPoint = { date: string; queries: number; document_views: number; security_events: number };

export type MyAnalytics = {
  scope: "me";
  totals: { documents: number; questions: number; chats: number; requests_pending: number; requests_approved: number; requests_rejected: number };
  range: AnalyticsRange;
  bucket_days: number;
  activity: ActivityPoint[];
  today: { queries: number; document_views: number; security_events: number };
};
