import { parseDate } from "./format";
import type { AuditLog } from "./types";

export type ActivityCategory = "questions" | "documents" | "permissions" | "people" | "security";

export const CATEGORY_LABELS: Record<ActivityCategory, string> = {
  questions: "Questions",
  documents: "Documents",
  permissions: "Access",
  people: "People",
  security: "Security",
};

export type ActivityContext = { users: Map<number, string>; docs: Map<number, string> };

export type Activity = { who: string; what: string; category: ActivityCategory; failed: boolean };

const num = (value: string | undefined) => (value === undefined ? undefined : Number(value));

/** Titles joined for display; with `compact`, only the first is named: “A” +3 more. */
function titles(ids: number[], doc: (id: number) => string, compact: boolean): string {
  if (!compact || ids.length <= 1) return ids.map((id) => `“${doc(id)}”`).join(", ");
  return `“${doc(ids[0])}” +${ids.length - 1} more`;
}

export function describeLog(log: AuditLog, ctx: ActivityContext, compact = false): Activity {
  const details = log.details ?? "";
  const user = (id: number | undefined | null) => (id == null ? "someone" : ctx.users.get(id) ?? `user #${id}`);
  const doc = (id: number | undefined | null) => (id == null ? "a document" : ctx.docs.get(id) ?? `document #${id}`);
  const resourceId = num(log.resource_id ?? undefined);
  const docFromDetails = num(details.match(/document=(\d+)/)?.[1]);
  const forUser = num(details.match(/for user (\d+)/)?.[1]);

  const who = log.user_id == null ? "System" : user(log.user_id);
  const make = (what: string, category: ActivityCategory): Activity => ({ who, what, category, failed: log.status === "failed" });

  switch (log.action) {
    case "rag_query": {
      const ids = (details.match(/documents=([\d,]+)/)?.[1] ?? "").split(",").filter(Boolean).map(Number);
      const refused = num(details.match(/restricted_document=(\d+)/)?.[1]);
      let what = "asked the assistant a question";
      if (refused != null) what += ` and was refused “${doc(refused)}”`;
      else if (ids.length) what += ` and got an answer from ${titles(ids, (id) => doc(id), compact)}`;
      else what += " and no document matched";
      return make(what, "questions");
    }
    case "document_accessed":
      return make(`opened “${doc(resourceId)}”`, "documents");
    case "document_created":
      return make(`added “${doc(resourceId)}”`, "documents");
    case "document_uploaded":
      return make(`uploaded ${details.replace(/^file=/, "") || `“${doc(resourceId)}”`}`, "documents");
    case "document_updated":
      return make(`edited “${doc(resourceId)}”`, "documents");
    case "document_deleted":
      return make(`deleted ${doc(resourceId)}`, "documents");
    case "document_permission_granted": {
      const target = num(details.match(/user=(\d+)/)?.[1]);
      const role = details.match(/role=([^,\s]+)/)?.[1];
      const to = target != null ? user(target) : role && role !== "None" ? `the ${role} role` : "someone";
      return make(`gave ${to} read access to “${doc(docFromDetails)}”`, "permissions");
    }
    case "document_permission_revoked":
      return make(`removed a read grant on “${doc(docFromDetails)}”`, "permissions");
    case "temporary_access_granted":
      return make(`gave ${user(num(details.match(/user (\d+)/)?.[1]))} temporary access to “${doc(resourceId)}”`, "permissions");
    case "temporary_access_revoked":
      return make(`ended ${user(num(details.match(/user (\d+)/)?.[1]))}'s temporary access to “${doc(resourceId)}”`, "permissions");
    case "access_request_submitted":
      return make(`requested access to “${doc(docFromDetails)}”`, "permissions");
    case "access_request_approved": {
      const until = details.match(/expires_at=(\d{4}-\d{2}-\d{2}T[\d:.]+)/)?.[1];
      const when = until ? ` until ${parseDate(until).toLocaleString(undefined, { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" })}` : "";
      return make(`approved ${user(forUser)}'s request for “${doc(resourceId)}”${until ? ` (temporary${when})` : ""}`, "permissions");
    }
    case "access_request_rejected":
      return make(`rejected ${user(forUser)}'s request for “${doc(resourceId)}”`, "permissions");
    case "user_created":
      return make(`created an account for ${user(resourceId)} (${details.match(/role (\w+)/)?.[1] ?? "no role"})`, "people");
    case "user_updated":
      return make(`updated ${user(resourceId)}: ${details}`, "people");
    case "password_changed":
      return make("changed their password", "people");
    case "security_events_reviewed":
      return make(`opened the Security page (${details.replace("count=", "") || "0"} new alerts marked as seen)`, "security");
    case "leakage_test_run":
      return make(`ran the leakage test (${details})`, "security");
    default:
      return make(log.action.replace(/_/g, " "), "documents");
  }
}

export function eventLabel(type: string): string {
  const labels: Record<string, string> = {
    unauthorized_document_access: "Tried to open a document without permission",
    cross_tenant_document_access: "Tried to reach another company's document",
    restricted_document_query: "Asked about a document they can't read",
    leakage_test_failed: "Leakage test failed",
  };
  return labels[type] ?? type.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

export const ATTEMPT_TYPES = new Set(["unauthorized_document_access", "cross_tenant_document_access", "restricted_document_query"]);

/** Pull "document 12" style references out of security event details. */
export function documentIdFromEvent(details: string | null): number | undefined {
  return num(details?.match(/[Dd]ocument (\d+)/)?.[1]);
}

export type Fact = { label: string; value?: string; chips?: string[]; tone?: "ok" | "bad" };

/** Structured details for one audit entry, shown when a timeline item is expanded. */
export function logFacts(log: AuditLog, ctx: ActivityContext): Fact[] {
  const details = log.details ?? "";
  const doc = (id: number) => ctx.docs.get(id) ?? `document #${id}`;
  const user = (id: number) => ctx.users.get(id) ?? `user #${id}`;
  const facts: Fact[] = [];

  facts.push({ label: "Who", value: log.user_id == null ? "System" : user(log.user_id) });
  facts.push({
    label: "When",
    value: parseDate(log.created_at).toLocaleString(undefined, { dateStyle: "full", timeStyle: "medium" }),
  });
  facts.push({ label: "Result", value: log.status === "failed" ? "Failed" : "Succeeded", tone: log.status === "failed" ? "bad" : "ok" });

  const answered = (details.match(/documents=([\d,]+)/)?.[1] ?? "").split(",").filter(Boolean).map(Number);
  const refused = num(details.match(/restricted_document=(\d+)/)?.[1]);
  const single = num(details.match(/document=(\d+)/)?.[1]);
  const isDocResource = /^(document_|temporary_access_|access_request_(approved|rejected))/.test(log.action);
  const resourceId = num(log.resource_id ?? undefined);

  if (answered.length) facts.push({ label: "Answered from", chips: answered.map(doc) });
  if (refused != null) facts.push({ label: "Refused", chips: [doc(refused)], tone: "bad" });
  if (single != null) facts.push({ label: "Document", chips: [doc(single)] });
  else if (isDocResource && resourceId != null) facts.push({ label: "Document", chips: [doc(resourceId)] });

  const forUser = num(details.match(/for user (\d+)/)?.[1] ?? details.match(/to user (\d+)/)?.[1]);
  if (forUser != null) facts.push({ label: "Person", value: user(forUser) });

  const until = details.match(/expires_at=(\d{4}-\d{2}-\d{2}T[\d:.]+)/)?.[1];
  if (until) facts.push({ label: "Access until", value: parseDate(until).toLocaleString(undefined, { dateStyle: "full", timeStyle: "short" }) });

  facts.push({ label: "Event", value: log.action });
  if (details) facts.push({ label: "Details", value: details });
  return facts;
}

export type EventInfo = { title: string; meaning: string; action: string };

/** Plain-language explanation shown when a security alert is expanded. */
export const EVENT_INFO: Record<string, EventInfo> = {
  unauthorized_document_access: {
    title: "Tried to open a document without permission",
    meaning: "Someone asked for a document directly (by its id) that is not on their access list. The request was blocked and nothing was shown.",
    action: "If they genuinely need it, grant access from Documents → Manage (or approve a temporary request). If this keeps repeating for documents they have no reason to open, review their activity in the Timeline.",
  },
  cross_tenant_document_access: {
    title: "Tried to reach another company's document",
    meaning: "A request referenced a document that belongs to a different company. It was blocked. This should never happen through the normal interface.",
    action: "Treat as serious. Review this person's recent activity in the Timeline and consider deactivating the account while you investigate.",
  },
  restricted_document_query: {
    title: "Asked about a document they can't read",
    meaning: "The best answer to their question was in a document they are not allowed to open, so the assistant refused to answer from it and told them which role is required. No content was shown.",
    action: "Usually harmless curiosity or a real need. If it is a real need they can send an access request; consider approving temporary access rather than permanent.",
  },
  leakage_test_failed: {
    title: "Leakage test failed",
    meaning: "The leakage test found that the search returned documents to someone who should not see them, so the retrieval filter is not behaving as intended.",
    action: "Pause sharing of sensitive documents, run the test again from the Security page, and check the document permissions and index. Contact engineering if it still fails.",
  },
};

export function eventInfo(type: string): EventInfo {
  return (
    EVENT_INFO[type] ?? {
      title: eventLabel(type),
      meaning: "A security-relevant event was recorded for this tenant.",
      action: "Check the details below and the person's recent activity in the Timeline.",
    }
  );
}
