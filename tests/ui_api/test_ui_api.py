from datetime import datetime, timedelta

import app.admin.security as admin_security


# ---------- auth ----------

def test_me_includes_company_name(client, login):
    me = client.get("/auth/me", headers=login("emma@acme.test")).json()
    assert me["tenant_name"] == "Acme Industries"
    assert me["role"] == "Employee"


def test_change_password(client, login):
    headers = login("emma@acme.test")
    bad = client.post("/auth/change-password", headers=headers, json={"current_password": "nope", "new_password": "a-new-long-password"})
    assert bad.status_code == 400
    short = client.post("/auth/change-password", headers=headers, json={"current_password": "correct-horse-battery", "new_password": "short"})
    assert short.status_code == 422
    ok = client.post("/auth/change-password", headers=headers, json={"current_password": "correct-horse-battery", "new_password": "a-new-long-password"})
    assert ok.status_code == 200
    assert client.post("/auth/login", json={"email": "emma@acme.test", "password": "a-new-long-password"}).status_code == 200


# ---------- documents ----------

def test_employee_sees_only_authorized_documents_with_summary(client, login):
    docs = client.get("/documents", headers=login("emma@acme.test")).json()
    assert [d["title"] for d in docs] == ["Employee Handbook"]
    assert docs[0]["summary"].startswith("Employee Handbook")
    assert docs[0]["word_count"] > 10


# ---------- RAG + chats ----------

def test_query_creates_chat_and_persists_messages(client, login, llm_calls):
    headers = login("emma@acme.test")
    first = client.post("/rag/query", headers=headers, json={"question": "What is the work from home policy?"}).json()
    assert first["restricted"] is None
    assert first["sources"] and first["sources"][0]["file_name"] == "Employee_Handbook.pdf"
    chat_id = first["chat_id"]

    second = client.post("/rag/query", headers=headers, json={"question": "How many days of paid leave?", "chat_id": chat_id}).json()
    assert second["chat_id"] == chat_id

    chat = client.get(f"/chats/{chat_id}", headers=headers).json()
    assert [m["role"] for m in chat["messages"]] == ["user", "assistant", "user", "assistant"]
    assert chat["messages"][1]["sources"][0]["title"] == "Employee Handbook"

    listing = client.get("/chats", headers=headers).json()
    assert len(listing) == 1 and listing[0]["message_count"] == 4
    assert listing[0]["title"].startswith("What is the work from home")


def test_restricted_question_returns_access_restricted_and_skips_llm(client, login, llm_calls):
    headers = login("emma@acme.test")
    reply = client.post("/rag/query", headers=headers, json={"question": "What is the salary of the employees in the company?"}).json()

    assert reply["restricted"] == {
        "document_id": reply["restricted"]["document_id"],
        "title": "Salary Report",
        "file_name": "Salary_Report.pdf",
        "classification": "Confidential",
        "required_roles": ["Manager"],
        "your_role": "Employee",
    }
    assert reply["sources"] == []
    assert llm_calls == []  # the model never saw anything
    assert "80000" not in reply["answer"] and "engineers" not in reply["answer"]

    # persisted so the chat history can re-render the restricted card
    chat = client.get(f"/chats/{reply['chat_id']}", headers=headers).json()
    assert chat["messages"][1]["restricted"]["title"] == "Salary Report"

    # and it is visible to admins as a security event
    events = client.get("/admin/security/events", headers=login("admin@acme.test")).json()
    assert any(e["event_type"] == "restricted_document_query" for e in events)


def test_authorized_user_gets_real_answer_not_restricted(client, login, llm_calls):
    reply = client.post("/rag/query", headers=login("mark@acme.test"), json={"question": "What is the salary of the employees in the company?"}).json()
    assert reply["restricted"] is None
    assert any(s["title"] == "Salary Report" for s in reply["sources"])
    assert len(llm_calls) == 1


def test_admin_never_gets_restricted(client, login):
    reply = client.post("/rag/query", headers=login("admin@acme.test"), json={"question": "salary of the employees"}).json()
    assert reply["restricted"] is None


def test_chats_are_private_to_their_owner(client, login):
    chat_id = client.post("/rag/query", headers=login("emma@acme.test"), json={"question": "work from home policy"}).json()["chat_id"]
    other = login("eli@acme.test")
    assert client.get(f"/chats/{chat_id}", headers=other).status_code == 404
    assert client.delete(f"/chats/{chat_id}", headers=other).status_code == 404
    assert client.post("/rag/query", headers=other, json={"question": "hi", "chat_id": chat_id}).status_code == 404
    assert client.get("/chats", headers=other).json() == []
    assert client.get(f"/chats/{chat_id}", headers=login("admin@acme.test")).status_code == 404


def test_delete_chat(client, login):
    headers = login("emma@acme.test")
    chat_id = client.post("/rag/query", headers=headers, json={"question": "work from home policy"}).json()["chat_id"]
    assert client.delete(f"/chats/{chat_id}", headers=headers).status_code == 200
    assert client.get(f"/chats/{chat_id}", headers=headers).status_code == 404
    assert client.get("/chats", headers=headers).json() == []


def test_llm_failure_returns_502_and_stores_nothing(client, login, monkeypatch):
    import app.rag.routes as rag_routes

    def boom(**kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(rag_routes, "generate_answer", boom)
    headers = login("emma@acme.test")
    response = client.post("/rag/query", headers=headers, json={"question": "work from home policy"})
    assert response.status_code == 502
    assert client.get("/chats", headers=headers).json() == []


# ---------- access requests ----------

def test_request_flow_end_to_end(client, login, world):
    emma, admin = login("emma@acme.test"), login("admin@acme.test")

    assert client.post(f"/documents/{world['salary']}/access-request", headers=emma, json={"reason": "Budget planning"}).status_code == 200

    mine = client.get("/me/access-requests", headers=emma).json()
    assert len(mine) == 1
    assert mine[0]["document_title"] == "Salary Report"
    assert mine[0]["status"] == "pending"
    assert mine[0]["approvers"] == ["Jane Admin"]
    assert mine[0]["decided_by"] is None

    pending = client.get("/admin/access-requests", headers=admin).json()
    assert pending[0]["user_name"] == "Emma Employee"
    assert pending[0]["document_title"] == "Salary Report"
    assert pending[0]["document_classification"] == "Confidential"

    assert client.post(f"/admin/access-requests/{pending[0]['id']}/approve", headers=admin).status_code == 200

    mine = client.get("/me/access-requests", headers=emma).json()
    assert mine[0]["status"] == "approved" and mine[0]["decided_by"] == "Jane Admin" and mine[0]["approvers"] == []
    assert client.get("/admin/access-requests", headers=admin).json() == []
    assert client.get("/admin/access-requests?status=approved", headers=admin).json()[0]["status"] == "approved"
    assert len(client.get("/admin/access-requests?status=all", headers=admin).json()) == 1
    assert client.get("/admin/access-requests?status=bogus", headers=admin).status_code == 422

    # approval takes effect for retrieval immediately
    reply = client.post("/rag/query", headers=emma, json={"question": "What is the salary of the employees in the company?"}).json()
    assert reply["restricted"] is None
    assert any(s["title"] == "Salary Report" for s in reply["sources"])


def test_my_requests_only_lists_own(client, login, world):
    client.post(f"/documents/{world['salary']}/access-request", headers=login("emma@acme.test"), json={})
    assert client.get("/me/access-requests", headers=login("eli@acme.test")).json() == []


def test_rejected_request_records_decider(client, login, world):
    emma, admin = login("emma@acme.test"), login("admin@acme.test")
    client.post(f"/documents/{world['salary']}/access-request", headers=emma, json={})
    rid = client.get("/admin/access-requests", headers=admin).json()[0]["id"]
    client.post(f"/admin/access-requests/{rid}/reject", headers=admin)
    mine = client.get("/me/access-requests", headers=emma).json()[0]
    assert mine["status"] == "rejected" and mine["decided_by"] == "Jane Admin"


# ---------- admin: users, analytics, security ----------

def test_admin_endpoints_reject_non_admins(client, login):
    emma = login("emma@acme.test")
    for method, path in [("get", "/admin/analytics/summary"), ("get", "/admin/users"), ("post", "/admin/security/leakage-test"), ("get", "/admin/audit")]:
        assert getattr(client, method)(path, headers=emma).status_code == 403, path
    assert client.patch("/admin/users/1", headers=emma, json={"role": "Admin"}).status_code == 403


def test_patch_user(client, login, world):
    admin = login("admin@acme.test")
    ok = client.patch(f"/admin/users/{world['employee']}", headers=admin, json={"role": "Manager"})
    assert ok.status_code == 200 and ok.json()["role"] == "Manager"
    assert client.patch(f"/admin/users/{world['employee']}", headers=admin, json={"is_active": False}).json()["is_active"] is False
    # deactivated users can no longer log in
    assert client.post("/auth/login", json={"email": "emma@acme.test", "password": "correct-horse-battery"}).status_code == 401

    assert client.patch(f"/admin/users/{world['admin']}", headers=admin, json={"role": "Employee"}).status_code == 400
    assert client.patch(f"/admin/users/{world['admin']}", headers=admin, json={"is_active": False}).status_code == 400
    assert client.patch(f"/admin/users/{world['globex_admin']}", headers=admin, json={"role": "Employee"}).status_code == 404
    assert client.patch(f"/admin/users/{world['employee']}", headers=admin, json={}).status_code == 400
    assert client.patch(f"/admin/users/{world['employee']}", headers=admin, json={"role": "Root"}).status_code == 422

    logs = client.get("/admin/audit", headers=admin).json()
    assert any(l["action"] == "user_updated" and "role: Employee -> Manager" in l["details"] for l in logs)


def test_analytics_summary(client, login):
    emma, admin = login("emma@acme.test"), login("admin@acme.test")
    client.post("/rag/query", headers=emma, json={"question": "work from home policy"})
    client.post("/rag/query", headers=emma, json={"question": "salary of the employees"})
    summary = client.get("/admin/analytics/summary", headers=admin).json()

    assert summary["totals"]["users"] == 4  # globex user excluded
    assert summary["totals"]["documents"] == 2
    assert summary["users_by_role"] == {"Admin": 1, "Manager": 1, "Employee": 2}
    assert summary["documents_by_classification"] == {"Internal": 1, "Confidential": 1}
    assert len(summary["activity"]) == 7
    today = summary["activity"][-1]
    assert today["queries"] == 2
    assert today["security_events"] >= 1
    assert summary["totals"]["open_security_events"] >= 1


def test_leakage_test_passes_when_acl_filter_holds(client, login):
    result = client.post("/admin/security/leakage-test", headers=login("admin@acme.test")).json()
    assert result["passed"] is True and result["leaks"] == []
    assert result["probes"] >= 2  # emma + eli each blocked from the salary report
    assert result["users_tested"] == 2


def test_leakage_test_fails_loudly_when_filter_leaks(client, login, world, monkeypatch):
    class Hit:
        payload = {"document_id": world["salary"]}

    monkeypatch.setattr(admin_security, "search_documents", lambda **kwargs: [Hit()])
    admin = login("admin@acme.test")
    result = client.post("/admin/security/leakage-test", headers=admin).json()
    assert result["passed"] is False and result["leaks"]
    events = client.get("/admin/security/events", headers=admin).json()
    assert any(e["event_type"] == "leakage_test_failed" and e["severity"] == "critical" for e in events)


def test_audit_log_records_documents_touched_by_query(client, login):
    client.post("/rag/query", headers=login("emma@acme.test"), json={"question": "work from home policy"})
    logs = client.get("/admin/audit", headers=login("admin@acme.test")).json()
    query_log = next(l for l in logs if l["action"] == "rag_query")
    assert "documents=" in query_log["details"]


def test_access_request_audit_log_names_the_document(client, login, world):
    client.post(f"/documents/{world['salary']}/access-request", headers=login("emma@acme.test"), json={})
    logs = client.get("/admin/audit", headers=login("admin@acme.test")).json()
    submitted = next(l for l in logs if l["action"] == "access_request_submitted")
    assert submitted["details"] == f"document={world['salary']}"


def test_editing_a_document_keeps_its_access_rules(client, login, world):
    admin = login("admin@acme.test")
    assert client.patch(f"/documents/{world['handbook']}", headers=admin, json={"title": "Staff Handbook 2026"}).status_code == 200
    emma = login("emma@acme.test")
    reply = client.post("/rag/query", headers=emma, json={"question": "work from home policy"}).json()
    assert any(s["title"] == "Staff Handbook 2026" for s in reply["sources"])
    # and the restricted document is still restricted after an unrelated edit
    client.patch(f"/documents/{world['salary']}", headers=admin, json={"classification": "Restricted"})
    reply = client.post("/rag/query", headers=emma, json={"question": "salary of the employees"}).json()
    assert not any(s["title"] == "Salary Report" for s in reply["sources"])


# ---------- analytics ranges + profile rename ----------

def test_analytics_ranges(client, login):
    emma, admin = login("emma@acme.test"), login("admin@acme.test")
    client.post("/rag/query", headers=emma, json={"question": "work from home policy"})
    client.post("/rag/query", headers=emma, json={"question": "salary of the employees"})

    week = client.get("/admin/analytics/summary", headers=admin).json()
    assert week["range"] == "7d" and week["bucket_days"] == 1 and len(week["activity"]) == 7

    month = client.get("/admin/analytics/summary?range=1m", headers=admin).json()
    assert len(month["activity"]) == 30 and month["bucket_days"] == 1
    assert sum(b["queries"] for b in month["activity"]) == 2
    assert month["activity"][-1]["queries"] == 2

    quarter = client.get("/admin/analytics/summary?range=3m", headers=admin).json()
    assert len(quarter["activity"]) == 13 and quarter["bucket_days"] == 7
    assert sum(b["queries"] for b in quarter["activity"]) == 2  # nothing lost when bucketed weekly
    assert quarter["activity"][-1]["queries"] == 2  # today falls in the last weekly bucket

    # "today" is independent of the range, so the dashboard stat card is right for all of them
    for data in (week, month, quarter):
        assert data["today"]["queries"] == 2
        assert data["today"]["security_events"] >= 1

    assert client.get("/admin/analytics/summary?range=1y", headers=admin).status_code == 422


def test_rename_self(client, login):
    emma = login("emma@acme.test")
    ok = client.patch("/auth/me", headers=emma, json={"full_name": "  Emma   J.  Employee "})
    assert ok.status_code == 200
    assert ok.json()["full_name"] == "Emma J. Employee"  # trimmed, inner spaces collapsed
    assert ok.json()["role"] == "Employee" and ok.json()["tenant_name"] == "Acme Industries"
    assert client.get("/auth/me", headers=emma).json()["full_name"] == "Emma J. Employee"

    assert client.patch("/auth/me", headers=emma, json={"full_name": "   "}).status_code == 422
    assert client.patch("/auth/me", headers=emma, json={"full_name": ""}).status_code == 422
    assert client.patch("/auth/me", headers=emma, json={"full_name": "x" * 256}).status_code == 422

    logs = client.get("/admin/audit", headers=login("admin@acme.test")).json()
    assert any(l["action"] == "profile_updated" and "Emma Employee -> Emma J. Employee" in l["details"] for l in logs)
    # renames show up wherever names are resolved
    users = client.get("/admin/users", headers=login("admin@acme.test")).json()
    assert any(u["full_name"] == "Emma J. Employee" for u in users)


def test_rename_cannot_change_role_or_email(client, login):
    emma = login("emma@acme.test")
    client.patch("/auth/me", headers=emma, json={"full_name": "Emma", "role": "Admin", "email": "x@y.z"})
    me = client.get("/auth/me", headers=emma).json()
    assert me["role"] == "Employee" and me["email"] == "emma@acme.test"


def test_rename_requires_login(client):
    assert client.patch("/auth/me", json={"full_name": "Hacker"}).status_code in (401, 403)


# ================= streaming answers =================
import asyncio
import json
from datetime import datetime, timedelta

from app.db import SessionLocal
from app.models.chat import Chat, ChatMessage
from app.models.temporary_access import TemporaryAccess
from app.rag import routes as rag_routes


def sse(response):
    events = []
    for block in response.text.strip().split("\n\n"):
        lines = block.split("\n")
        events.append((lines[0][len("event: "):], json.loads(lines[1][len("data: "):])))
    return events


def test_stream_sends_meta_then_tokens_then_done_and_saves_the_chat(client, login, llm_calls):
    headers = login("emma@acme.test")
    response = client.post("/rag/query/stream", headers=headers, json={"question": "What is the work from home policy?"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = sse(response)

    names = [name for name, _ in events]
    assert names[0] == "meta" and names[-1] == "done"
    assert names.count("token") >= 5  # arrives in pieces, not as one block
    meta = events[0][1]
    assert meta["restricted"] is None and meta["sources"][0]["file_name"] == "Employee_Handbook.pdf"
    streamed = "".join(data["t"] for name, data in events if name == "token")
    assert streamed == events[-1][1]["answer"]
    assert len(llm_calls) == 1

    chat = client.get(f"/chats/{meta['chat_id']}", headers=headers).json()
    assert [m["role"] for m in chat["messages"]] == ["user", "assistant"]
    assert chat["messages"][1]["content"] == streamed
    assert chat["messages"][1]["sources"][0]["title"] == "Employee Handbook"

    # a follow-up continues the same chat
    again = sse(client.post("/rag/query/stream", headers=headers, json={"question": "How many leave days?", "chat_id": meta["chat_id"]}))
    assert again[0][1]["chat_id"] == meta["chat_id"]
    assert len(client.get(f"/chats/{meta['chat_id']}", headers=headers).json()["messages"]) == 4

    logs = client.get("/admin/audit", headers=login("admin@acme.test")).json()
    assert any(l["action"] == "rag_query" and "documents=" in l["details"] for l in logs)


def test_stream_restricted_never_reaches_the_model(client, login, llm_calls):
    headers = login("emma@acme.test")
    events = sse(client.post("/rag/query/stream", headers=headers, json={"question": "What is the salary of the employees in the company?"}))
    assert [n for n, _ in events] == ["meta", "done"]
    assert events[0][1]["restricted"]["title"] == "Salary Report"
    assert events[0][1]["sources"] == []
    assert llm_calls == []
    assert "80000" not in json.dumps(events)
    chat = client.get(f"/chats/{events[0][1]['chat_id']}", headers=headers).json()
    assert chat["messages"][1]["restricted"]["required_roles"] == ["Manager"]


def test_stream_respects_chat_ownership_and_login(client, login):
    chat_id = sse(client.post("/rag/query/stream", headers=login("emma@acme.test"), json={"question": "work from home policy"}))[0][1]["chat_id"]
    assert client.post("/rag/query/stream", headers=login("eli@acme.test"), json={"question": "hi", "chat_id": chat_id}).status_code == 404
    assert client.post("/rag/query/stream", json={"question": "hi"}).status_code in (401, 403)


def test_stream_failure_before_any_text_leaves_no_trace(client, login):
    headers = login("emma@acme.test")
    events = sse(client.post("/rag/query/stream", headers=headers, json={"question": "boom-early work from home policy"}))
    assert [n for n, _ in events] == ["meta", "error"]
    assert "unavailable" in events[1][1]["message"]
    assert client.get("/chats", headers=headers).json() == []  # question rolled back, no empty chat


def test_stream_failure_midway_keeps_what_was_written(client, login):
    headers = login("emma@acme.test")
    events = sse(client.post("/rag/query/stream", headers=headers, json={"question": "boom-late work from home policy"}))
    names = [n for n, _ in events]
    assert names.count("token") == 3 and names[-1] == "error"
    chat = client.get(f"/chats/{events[0][1]['chat_id']}", headers=headers).json()
    assert chat["messages"][1]["content"].endswith(rag_routes.STOPPED_MARK)


def _manual_turn(user_id, question="tell me about leave"):
    with SessionLocal() as db:
        chat = Chat(user_id=user_id, tenant_id="acme", title=question, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        db.add(chat)
        db.flush()
        message = ChatMessage(chat_id=chat.id, role="user", content=question, created_at=datetime.utcnow())
        db.add(message)
        db.commit()
        return rag_routes.StreamTurn(
            chat_id=chat.id, user_message_id=message.id, new_chat=True, user_id=user_id, tenant_id="acme",
            question=question, context="Document: Handbook\nContent: " + "leave policy details " * 30,
        )


def _saved(chat_id):
    with SessionLocal() as db:
        return [(m.role, m.content) for m in db.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).order_by(ChatMessage.id)]


def test_stopping_mid_answer_saves_the_partial_text(world):
    turn = _manual_turn(world["employee"])

    async def run():
        gen = rag_routes.answer_events(turn)
        await gen.__anext__()          # meta
        await gen.__anext__()          # first piece
        await gen.__anext__()          # second piece
        await gen.aclose()             # what a disconnect (Stop button) does

    asyncio.run(run())
    saved = _saved(turn.chat_id)
    assert [role for role, _ in saved] == ["user", "assistant"]
    assert saved[1][1].startswith("From")
    assert saved[1][1].endswith(rag_routes.STOPPED_MARK)
    assert len(saved[1][1]) < 200  # only what had streamed, not the whole answer


def test_stopping_before_any_text_saves_only_the_marker(world):
    turn = _manual_turn(world["employee"])

    async def run():
        gen = rag_routes.answer_events(turn)
        await gen.__anext__()          # meta only
        await gen.aclose()

    asyncio.run(run())
    assert _saved(turn.chat_id)[1] == ("assistant", rag_routes.STOPPED_MARK.strip())


def test_deleting_a_chat_while_it_streams_does_not_crash(world):
    turn = _manual_turn(world["employee"])
    with SessionLocal() as db:
        db.delete(db.get(Chat, turn.chat_id))
        db.commit()

    async def run():
        gen = rag_routes.answer_events(turn)
        await gen.__anext__()
        await gen.aclose()

    asyncio.run(run())  # must not raise


# ================= personal analytics =================

def test_my_analytics_is_personal_and_differs_from_the_admin_view(client, login):
    emma, eli, admin = login("emma@acme.test"), login("eli@acme.test"), login("admin@acme.test")
    client.post("/rag/query", headers=emma, json={"question": "work from home policy"})
    client.post("/rag/query", headers=emma, json={"question": "leave policy"})
    client.post("/rag/query", headers=eli, json={"question": "work from home policy"})

    mine = client.get("/me/analytics", headers=emma).json()
    assert mine["scope"] == "me" and mine["range"] == "7d" and len(mine["activity"]) == 7
    assert mine["today"]["queries"] == 2 and mine["totals"]["questions"] == 2
    assert mine["totals"]["documents"] == 1 and mine["totals"]["chats"] == 2
    assert mine["totals"]["requests_pending"] == 0

    company = client.get("/admin/analytics/summary", headers=admin).json()
    assert company["today"]["queries"] == 3          # everyone
    assert eli_total(client, eli) == 1               # Eli sees only her own

    month = client.get("/me/analytics?range=1m", headers=emma).json()
    assert len(month["activity"]) == 30 and sum(b["queries"] for b in month["activity"]) == 2
    quarter = client.get("/me/analytics?range=3m", headers=emma).json()
    assert len(quarter["activity"]) == 13 and quarter["bucket_days"] == 7
    assert client.get("/me/analytics?range=1y", headers=emma).status_code == 422
    assert client.get("/me/analytics").status_code in (401, 403)


def eli_total(client, headers):
    return client.get("/me/analytics", headers=headers).json()["totals"]["questions"]


def test_my_analytics_counts_requests_and_refusals(client, login, world):
    emma = login("emma@acme.test")
    client.post("/rag/query", headers=emma, json={"question": "salary of the employees"})  # refused -> security event
    client.post(f"/documents/{world['salary']}/access-request", headers=emma, json={})
    mine = client.get("/me/analytics", headers=emma).json()
    assert mine["totals"]["requests_pending"] == 1
    assert mine["today"]["security_events"] >= 1


# ================= approve with options (temporary access) =================

def _request_salary(client, login, world):
    emma, admin = login("emma@acme.test"), login("admin@acme.test")
    client.post(f"/documents/{world['salary']}/access-request", headers=emma, json={"reason": "Budget"})
    request_id = client.get("/admin/access-requests", headers=admin).json()[0]["id"]
    return emma, admin, request_id


def _ask_salary(client, emma):
    return client.post("/rag/query", headers=emma, json={"question": "What is the salary of the employees in the company?"}).json()


def test_approve_without_a_body_is_still_permanent(client, login, world):
    emma, admin, rid = _request_salary(client, login, world)
    done = client.post(f"/admin/access-requests/{rid}/approve", headers=admin)
    assert done.status_code == 200 and done.json()["expires_at"] is None
    perms = client.get(f"/documents/{world['salary']}/permissions", headers=admin).json()
    assert any(p["user_id"] == world["employee"] for p in perms)
    assert client.get("/admin/security/temporary-access", headers=admin).json() == []
    assert _ask_salary(client, emma)["restricted"] is None


def test_approve_for_a_duration_grants_temporary_access_only(client, login, world):
    emma, admin, rid = _request_salary(client, login, world)
    done = client.post(f"/admin/access-requests/{rid}/approve", headers=admin, json={"duration_hours": 2})
    assert done.status_code == 200 and done.json()["expires_at"] is not None

    # no permanent grant was created ...
    perms = client.get(f"/documents/{world['salary']}/permissions", headers=admin).json()
    assert not any(p["user_id"] == world["employee"] for p in perms)
    # ... a temporary one was, and it works right away
    grants = client.get("/admin/security/temporary-access", headers=admin).json()
    assert len(grants) == 1 and grants[0]["user_id"] == world["employee"]
    reply = _ask_salary(client, emma)
    assert reply["restricted"] is None and any(s["title"] == "Salary Report" for s in reply["sources"])

    # both sides can see that it is temporary
    mine = client.get("/me/access-requests", headers=emma).json()[0]
    assert mine["status"] == "approved" and mine["access_expires_at"] is not None and mine["decided_by"] == "Jane Admin"
    listed = client.get("/admin/access-requests?status=approved", headers=admin).json()[0]
    assert listed["access_expires_at"] is not None and listed["decided_by"] == "Jane Admin"
    logs = client.get("/admin/audit", headers=admin).json()
    assert any(l["action"] == "access_request_approved" and "expires_at=" in l["details"] for l in logs)


def test_temporary_approval_stops_working_after_it_expires(client, login, world):
    emma, admin, rid = _request_salary(client, login, world)
    client.post(f"/admin/access-requests/{rid}/approve", headers=admin, json={"duration_hours": 1})
    assert _ask_salary(client, emma)["restricted"] is None

    with SessionLocal() as db:  # time passes
        for grant in db.query(TemporaryAccess).all():
            grant.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()

    # The index still lists her until it is next synced; the database check must stop her anyway.
    reply = _ask_salary(client, emma)
    assert not any(s["title"] == "Salary Report" for s in reply["sources"])
    assert reply["restricted"]["title"] == "Salary Report"
    assert "Salary Report" not in [d["title"] for d in client.get("/documents", headers=emma).json()]
    assert client.get(f"/documents/{world['salary']}", headers=emma).status_code == 403
    assert client.get("/admin/security/temporary-access", headers=admin).json() == []


def test_approve_with_a_custom_expiry(client, login, world):
    emma, admin, rid = _request_salary(client, login, world)
    when = (datetime.utcnow() + timedelta(days=3)).isoformat() + "Z"
    done = client.post(f"/admin/access-requests/{rid}/approve", headers=admin, json={"expires_at": when})
    assert done.status_code == 200 and done.json()["expires_at"].startswith(when[:13])


def test_approve_rejects_bad_options(client, login, world):
    emma, admin, rid = _request_salary(client, login, world)
    url = f"/admin/access-requests/{rid}/approve"
    assert client.post(url, headers=admin, json={"duration_hours": 0}).status_code == 422
    assert client.post(url, headers=admin, json={"duration_hours": 24 * 90 + 1}).status_code == 422
    both = {"duration_hours": 2, "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat()}
    assert client.post(url, headers=admin, json=both).status_code == 422
    past = {"expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()}
    assert client.post(url, headers=admin, json=past).status_code == 400
    far = {"expires_at": (datetime.utcnow() + timedelta(days=400)).isoformat()}
    assert client.post(url, headers=admin, json=far).status_code == 400
    # nothing was granted by the failed attempts, and the request is still pending
    assert client.get("/admin/security/temporary-access", headers=admin).json() == []
    assert client.get("/admin/access-requests", headers=admin).json()[0]["status"] == "pending"
    assert client.post(url, headers=emma, json={"duration_hours": 1}).status_code == 403  # admins only
    assert client.post(url, headers=admin, json={"duration_hours": 1}).status_code == 200
    assert client.post(url, headers=admin, json={"duration_hours": 1}).status_code == 409  # already decided


# ================= security events: seen / unseen =================

def test_opening_security_page_marks_events_seen(client, login):
    emma, admin = login("emma@acme.test"), login("admin@acme.test")
    client.post("/rag/query", headers=emma, json={"question": "salary of the employees"})
    before = client.get("/admin/analytics/summary", headers=admin).json()["totals"]["open_security_events"]
    assert before >= 1

    done = client.post("/admin/security/events/acknowledge", headers=admin)
    assert done.status_code == 200 and done.json()["acknowledged"] == before
    assert client.get("/admin/analytics/summary", headers=admin).json()["totals"]["open_security_events"] == 0
    events = client.get("/admin/security/events", headers=admin).json()
    assert events and all(e["status"] == "seen" for e in events)  # still listed, just not "new"

    assert client.post("/admin/security/events/acknowledge", headers=admin).json()["acknowledged"] == 0  # idempotent
    logs = client.get("/admin/audit", headers=admin).json()
    assert any(l["action"] == "security_events_reviewed" and f"count={before}" in l["details"] for l in logs)

    client.post("/rag/query", headers=emma, json={"question": "what is the salary of the employees in the company?"})
    # a repeat of the same event within the dedupe window is not new; something different is
    client.get(f"/documents/{1 + 1}", headers=emma)
    assert client.get("/admin/analytics/summary", headers=admin).json()["totals"]["open_security_events"] >= 1


def test_acknowledging_is_limited_to_your_own_tenant_and_to_admins(client, login):
    from app.security.events import create_security_event

    with SessionLocal() as db:
        create_security_event(db, "unauthorized_document_access", "high", tenant_id="globex", details="other tenant")
    assert client.post("/admin/security/events/acknowledge", headers=login("emma@acme.test")).status_code == 403
    client.post("/admin/security/events/acknowledge", headers=login("admin@acme.test"))
    globex = client.get("/admin/analytics/summary", headers=login("root@globex.test")).json()
    assert globex["totals"]["open_security_events"] == 1  # untouched by another tenant's admin
