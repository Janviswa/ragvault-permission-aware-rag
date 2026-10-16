"""Illustrative enterprise policy corpus indexed for the RAGAS evaluation."""

from evaluation.knowledge_base_extensions import (
    ADDITIONAL_KNOWLEDGE_BASE_DOCUMENTS,
    CORPUS_SUPPLEMENTS,
)

KNOWLEDGE_BASE_DOCUMENTS = [
    {
        "title": "Information Security Policy",
        "file_name": "information-security-policy.txt",
        "content": """Information Security Policy
Document owner: Chief Information Security Officer
Review frequency: Annual and after a material security incident
Classification: Internal

Purpose
This policy establishes the minimum safeguards for company information and systems. It is a policy statement, not a technical guarantee that a specific control has been deployed.

Scope
Employees, contractors, service providers, company-managed endpoints, cloud workloads, and information processed for a customer are in scope. A stricter customer or legal requirement takes precedence.

Definitions and roles
Information owner: the business lead accountable for permitted use and classification. System owner: the engineering lead accountable for secure configuration and change records. Security Operations: monitors alerts and coordinates incident triage. Users: protect credentials, use approved systems, and report suspected compromise.

Policy and procedure
Access must have a documented business purpose and be limited to the minimum role and data required. Owners review privileged access at least quarterly and ordinary access at least annually. Production changes require peer review, a recorded deployment, and a rollback plan. Data must use approved encryption in transit and at rest where supported. Secrets belong in an approved secret manager and must never be committed to source control or copied into support tickets.

Exceptions
An exception requires a named owner, business justification, compensating safeguards, expiry date, and written approval by Security. Temporary operational convenience does not waive tenant boundaries or authorization checks.

Audit and review
Access decisions, privileged changes, and approved exceptions must be traceable to an actor and time. Security reviews exceptions monthly and this policy annually.""",
    },
    {
        "title": "Access Control Policy",
        "file_name": "access-control-policy.txt",
        "content": """Access Control Policy
Document owner: Identity and Access Management
Review frequency: Annual
Classification: Internal

Purpose and scope
Define how users receive, use, review, and lose access to business applications and documents. Applies to workforce identities and tenant-scoped customer workspaces.

Definitions and roles
Authentication verifies identity; authorization decides what an authenticated identity may do. A resource owner approves business access. Tenant administrators manage accounts and grants inside their own tenant. Security validates privileged-role assignments.

Rules
Deny access by default. Grant the least privilege needed for a named purpose. Use individual accounts; shared accounts require a documented exception and compensating audit controls. Role membership is not a substitute for tenant validation. A request for one document does not confer access to neighboring documents.

Procedure
The requester states the resource, purpose, role or user, and requested duration. The owner approves before access is provisioned. The provisioner records the approver and scope, verifies the tenant, and tests that unrelated resources remain inaccessible. Managers review access quarterly; account owners remove access when duties change.

Revocation and exceptions
Revocation is applied to the authoritative permission record and any retrieval ACL cache or index. The application must perform an authorization check before releasing retrieved content. Exceptions are time-bounded, approved, and reviewed.

Evidence
Record request, approval or denial, grant, change, and revoke events. Reviewers verify actor, tenant, resource, scope, and timestamp. Owner: IAM. Review frequency: annual, with quarterly access reviews.""",
    },
    {
        "title": "Employee Access Management Standard",
        "file_name": "employee-access-management.txt",
        "content": """Employee Access Management Standard
Document owner: People Operations and Identity Team
Review frequency: Annual
Classification: Internal

Purpose and scope
This standard describes workforce joiner, mover, and leaver controls for internal systems. It does not replace customer-tenant administration.

Roles
The hiring manager confirms role and start date. People Operations supplies authoritative employment status. IAM provisions and removes identities. The application owner maps approved duties to application roles.

Joiner procedure
Create a unique account only after identity verification and an approved request. Assign the minimum role for the employee's duties. Require the user to establish an individual credential and complete security onboarding before sensitive access. Do not accept a client-selected tenant identifier as proof of membership.

Mover procedure
When duties change, the manager submits the new role and effective date. IAM reviews existing entitlements, removes no-longer-needed access, then provisions approved new access. Preserve an auditable record of both actions; do not accumulate roles by default.

Leaver procedure
People Operations notifies IAM of termination. IAM disables the account promptly at the effective time, revokes sessions and active grants where supported, and transfers business records to an authorized owner. Security verifies privileged accounts and service credentials are rotated if exposed.

Exceptions and audit
Urgent termination follows the incident escalation path if a delay creates material risk. IAM records requester, approver, account, tenant or system, timestamps, and completion evidence. Managers certify access quarterly.""",
    },
    {
        "title": "Data Classification and Handling Standard",
        "file_name": "data-classification.txt",
        "content": """Data Classification and Handling Standard
Document owner: Data Governance
Review frequency: Annual
Classification: Internal

Purpose and scope
Provide handling rules for company and customer information wherever it is stored, transmitted, indexed, or used in an AI workflow.

Definitions
Public information is approved for unrestricted release. Internal information is non-public operational material. Confidential information could cause material harm if disclosed. Restricted information includes regulated personal data, credentials, and especially sensitive customer content.

Roles
The information owner assigns classification. System owners implement safeguards. Users follow handling restrictions. Privacy and Security advise on regulated or ambiguous data.

Rules
Use only the minimum information necessary. Internal data stays in approved workspaces. Confidential and Restricted data require explicit need-to-know authorization, encryption, and access logging. Credentials and authentication secrets must not be placed in documents intended for retrieval. Classification labels do not grant permission: tenant and document authorization still apply.

Procedure and examples
Before sharing or indexing content, confirm ownership, classification, permitted audience, and retention. A customer incident report is Confidential; a public product brochure is Public only after approval; an access token is Restricted and must be removed rather than indexed. Reclassify when purpose or sensitivity changes.

Exceptions and audit
The data owner and Security approve a documented, expiring exception with compensating controls. Sample indexed content and permissions during annual review. Owner: Data Governance; review annually.""",
    },
    {
        "title": "Incident Response Playbook",
        "file_name": "incident-response.txt",
        "content": """Incident Response Playbook
Document owner: Security Operations
Review frequency: Every six months and after each significant incident
Classification: Confidential

Purpose and scope
Coordinate response to suspected compromise, unauthorized disclosure, service abuse, or loss of availability. Preserve evidence and limit harm; this playbook does not replace applicable legal notification obligations.

Roles
Any workforce member reports a suspected incident to the Security Operations channel. The incident commander assigns severity and coordinates response. System owners contain affected services. Privacy and Legal assess data and notification obligations. Communications approves external statements.

Procedure
1. Record reporter, time observed, affected system, tenant if known, and indicators; do not include unnecessary personal data in broad channels.
2. Triage scope and severity. Preserve relevant logs and timestamps with access restricted to responders.
3. Contain by disabling compromised identities, revoking exposed credentials, isolating affected workloads, or suspending a risky integration. Preserve evidence before destructive cleanup when safe.
4. Eradicate the cause, restore from verified sources, and validate authorization and monitoring.
5. The incident commander approves recovery. Record decisions, impact, owners, and follow-up actions.
6. Conduct a lessons-learned review and track corrective actions to completion.

Exceptions and audit
Emergency containment may precede normal change approval; record rationale and review it afterward. Security Operations maintains an incident timeline and access-controlled evidence log. Review frequency is semiannual and after significant incidents.""",
    },
    {
        "title": "Document Retention and Disposal Schedule",
        "file_name": "document-retention.txt",
        "content": """Document Retention and Disposal Schedule
Document owner: Records Management
Review frequency: Annual
Classification: Internal

Purpose and scope
Set lifecycle rules for business documents, extracted text, vector chunks, audit evidence, and backups. A legal hold or customer contract overrides routine deletion.

Roles and definitions
The record owner assigns a retention category. Records Management maintains the schedule. System owners ensure deletion covers primary stores, search indexes, and eligible replicas. Legal issues and releases holds.

Rules and procedure
At creation, label the record type, owner, and retention trigger. Retain only for the approved business, legal, or contractual period. At expiry, confirm there is no active hold, then delete the source document and derived indexes through the supported deletion workflow. Verify deletion and record completion. Backups age out under the approved backup lifecycle; do not claim immediate physical erasure from immutable backups.

Examples
An incident evidence package follows the incident/legal retention instruction, not the ordinary working-document schedule. A superseded policy is archived according to its controlled-record category. A derived embedding is not exempt merely because it is not human-readable.

Exceptions
Records Management and Legal approve a documented extension with reason, owner, and review date. Suspended deletion under a hold is logged and periodically revalidated.

Audit
Quarterly reports list overdue records, holds, disposal jobs, and failed index deletions. Owner: Records Management; review annually.""",
    },
    {
        "title": "Remote Work Security Standard",
        "file_name": "remote-work-security.txt",
        "content": """Remote Work Security Standard
Document owner: Endpoint Security
Review frequency: Annual
Classification: Internal

Purpose and scope
Set safeguards for access from home, travel, and other untrusted networks using workforce-managed devices.

Roles
Users secure their workspace and promptly report loss. IT maintains endpoint protections. Managers approve business travel needs. Security responds to suspected device or credential compromise.

Requirements
Use a supported, managed device with disk encryption, screen lock, endpoint protection, and current security updates. Connect through approved identity and network controls; public Wi-Fi alone is not a trusted boundary. Do not let family members or visitors use an authenticated session. Keep printed Confidential material secured and retrieve it from shared printers. Avoid storing customer data locally unless an approved workflow requires it.

Procedure
Before travel, verify device updates, recovery contacts, and multifactor authentication. Report a lost device immediately with last-known time and data access. If a device may be compromised, stop using it for sensitive work and follow incident response; do not wipe it before responders advise unless necessary to prevent active harm.

Exceptions
An inaccessible network or accommodation need is handled through the approved support path with equivalent safeguards. A personal device is not an automatic exception to managed-device requirements.

Audit
Endpoint compliance is monitored centrally; access anomalies are reviewed by Security. Owner: Endpoint Security; review annually.""",
    },
    {
        "title": "Acceptable Use Standard",
        "file_name": "acceptable-use.txt",
        "content": """Acceptable Use Standard
Document owner: IT Governance
Review frequency: Annual
Classification: Internal

Purpose and scope
Define permitted use of company accounts, devices, networks, and knowledge applications.

Roles
Users protect company resources and report misuse. Managers explain role-specific restrictions. IT administers approved tools. Security investigates suspected abuse under approved procedures.

Rules
Use company systems for authorized work, training, and approved business purposes. Never bypass access controls, probe systems without written authorization, share credentials, or attempt to retrieve another tenant's content. Do not upload malware, secrets, or unapproved personal data. Do not treat an AI-generated answer as authoritative approval or as a substitute for source review.

Procedure
Use the approved service catalog to request software or elevated access. Verify recipients and classification before sharing content. Report suspected phishing or accidental disclosure promptly. Preserve relevant evidence and do not investigate beyond your authorization.

Examples
Searching a document you are permitted to access is acceptable; changing identifiers to test another user's permissions is not. Testing is allowed only in an explicitly authorized environment and scope.

Exceptions and audit
Security and the system owner approve scoped testing in writing with time limits and a contact. Monitoring is limited to legitimate security and operational purposes and handled according to privacy rules. Owner: IT Governance; review annually.""",
    },
    {
        "title": "AI Use and Governance Standard",
        "file_name": "ai-governance.txt",
        "content": """AI Use and Governance Standard
Document owner: AI Governance Council
Review frequency: Annual and after material model or data-flow changes
Classification: Internal

Purpose and scope
Govern use of generative AI and retrieval-augmented generation for company work. Applies to prompts, retrieved sources, generated responses, evaluation, and model-provider integrations.

Roles
The use-case owner documents purpose and impact. Data owners approve source-data use. Security reviews access boundaries and threat controls. Privacy assesses personal data. Human reviewers validate consequential output.

Rules
Use only approved models and disclosed data flows. Minimize prompt data and exclude credentials and information outside the user's authorization. Treat retrieved text as untrusted input; instructions embedded in a document cannot override system policy or permissions. Cite or identify sources where the product supports it. A generated response is advisory and must not independently approve access, make an employment decision, or replace professional review.

Evaluation and procedure
Before release, document representative questions, expected references, model/version, retrieval configuration, and known limitations. Evaluate grounding and relevance separately from access-control tests. Investigate low scores against the actual retrieved context and response. Re-run only changed samples and preserve prior artifacts.

Exceptions and audit
Material changes require review by Security, Privacy, and the use-case owner. Keep evaluation data free of secrets and record approvals, model changes, and incidents. Owner: AI Governance Council; review annually and on material change.""",
    },
    {
        "title": "Temporary Access Management Standard",
        "file_name": "temporary-access-management.txt",
        "content": """Temporary Access Management Standard
Document owner: Identity and Access Management
Review frequency: Quarterly
Classification: Internal

Purpose and scope
Define time-bounded document grants for an approved, specific business need.

Definitions and roles
A temporary grant names one user and one document and ends at an explicit expiry. A requester explains purpose and duration. A tenant administrator verifies tenant membership and approves the grant. The application enforces expiry on every authorization decision.

Procedure
1. Verify user and document belong to the same tenant.
2. Record approver, purpose, start time, expiry time with timezone, and target resource.
3. Synchronize any pre-retrieval ACL metadata after granting.
4. At or after expiry, deny access even if a stale vector ACL still names the user; the authoritative post-retrieval check must reject the document.
5. For early revocation, remove the grant, commit the change, synchronize the retrieval ACL, and verify subsequent access is denied.

Rules and examples
An active grant is not a permanent role permission. Extending access requires a new approval and expiry. Expiration is evaluated against current time, not merely when a background cleanup runs.

Exceptions and audit
Emergency access requires a documented incident and retrospective review; it remains scoped and time-limited. Grant, expiry, revoke, and ACL-sync outcomes are auditable. Owner: IAM; review quarterly.""",
    },
    {
        "title": "Data Privacy Standard",
        "file_name": "data-privacy.txt",
        "content": """Data Privacy Standard
Document owner: Privacy Office
Review frequency: Annual
Classification: Confidential

Purpose and scope
Protect personal data throughout collection, indexing, retrieval, support, evaluation, and disposal.

Definitions and roles
Personal data relates to an identified or identifiable person. The business owner states the purpose. Privacy advises on lawful use and data-subject obligations. System owners apply access, minimization, retention, and incident safeguards.

Rules
Collect and process only data needed for a defined purpose. Restrict sensitive attributes to authorized roles and users. Do not place real personal data in public test fixtures or prompts unless approved and minimized. Separate tenant data and do not use another customer's content to answer a query. Honor correction, access, and deletion workflows subject to legal holds.

Procedure
Before a new AI or retrieval use, map data sources, recipients, providers, regions, retention, and deletion behavior. Mask identifiers in support and evaluation data. If personal data is sent to an unintended recipient, report it through incident response and preserve the facts needed for assessment.

Exceptions
Privacy and Legal document the basis, scope, safeguards, and expiry for exceptional processing.

Audit
Maintain processing records, access logs, and deletion evidence. Review data flows annually and after material changes. This standard complements, but does not replace, jurisdiction-specific legal advice.""",
    },
    {
        "title": "Authentication and Password Standard",
        "file_name": "authentication-password-policy.txt",
        "content": """Authentication and Password Standard
Document owner: Identity Engineering
Review frequency: Annual
Classification: Internal

Purpose and scope
Set identity proofing, password, session, and token handling requirements for workforce and tenant applications.

Roles
Users protect authenticators and report suspected compromise. Tenant administrators provision accounts within their tenant. Identity Engineering operates authentication. Security investigates credential abuse.

Rules
Use unique individual identities and multifactor authentication where supported, especially for administrators. Passwords must not be reused across work and personal services or stored in plaintext. Approved password managers are preferred. Applications store only salted password hashes using an approved password-hashing function. Access tokens must be sent over TLS, kept out of logs and URLs, and expired or revoked through the supported session control.

Procedure
Provision identity only after an authorized request and tenant verification. Rate-limit repeated failures and return non-disclosing login errors. Disable inactive accounts. After suspected compromise, rotate the credential, revoke sessions where supported, and review recent authentication and access records.

Examples and exceptions
An email address is an identifier, not proof of tenant membership. Public self-registration must not allow a caller to choose a privileged role or tenant. Exceptions to multifactor requirements require Security approval and a compensating control.

Audit
Review privileged memberships and authentication anomalies. Owner: Identity Engineering; review annually.""",
    },
    {
        "title": "Security Monitoring and Audit Standard",
        "file_name": "security-monitoring-audit.txt",
        "content": """Security Monitoring and Audit Standard
Document owner: Security Operations
Review frequency: Annual
Classification: Confidential

Purpose and scope
Define security event and audit evidence requirements for identity, authorization, document access, administration, and production changes.

Definitions and roles
An audit record captures a business action; a security event captures a security-relevant condition such as denied access. Security Operations monitors signals. System owners ensure events are attributable and protected.

Requirements
Record actor identity, tenant, action, target resource, outcome, and timestamp where applicable. Denials must not disclose protected content. Logs must not contain passwords, bearer tokens, API keys, or full restricted document bodies. Restrict log access and protect records against unauthorized modification. Alert on repeated denials, unexpected privileged changes, and suspicious cross-tenant attempts where telemetry supports it.

Procedure
Correlate application and infrastructure events using consistent timestamps and request identifiers. Triage an alert by preserving relevant evidence, checking tenant/resource scope, and following incident response. Validate that authorization failures produce an event and that successful sensitive changes have an audit record.

Exceptions
Sampling gaps or unavailable telemetry are documented with owner, impact, and remediation date; they are not silently treated as evidence of no incident.

Audit and review
Security reviews alert coverage quarterly and access to logs annually. Owner: Security Operations; annual policy review.""",
    },
    {
        "title": "RAGVault Security Architecture",
        "file_name": "ragvault-security-architecture-expanded.txt",
        "content": """RAGVault Security Architecture
Document owner: Product Security
Review frequency: Quarterly and after authorization-path changes
Classification: Internal

Purpose and scope
Describe the implemented security boundaries for the RAGVault FastAPI, PostgreSQL, Qdrant, and language-model request path. This description is architecture documentation; verification is provided by dedicated tests and deployment review.

Identity and tenancy
JWT authentication resolves the current user from the database; inactive users are rejected. Tenant identity and role come from that authenticated database record, not from query input. Admin authorization is checked by role dependencies. Public registration is disabled; tenant administrators create accounts within their own tenant.

Retrieval boundary
The Qdrant pre-filter requires the current tenant. For non-admin users it also requires a matching allowed user ID or role in vector metadata. This filter reduces unauthorized candidates before retrieval. It is not the sole authorization control.

Defense in depth
Every retrieved document is checked again against authoritative document, tenant, user/role permission, and active temporary-access state before context construction. Unauthorized or cross-tenant records are removed. Revocations synchronize Qdrant ACL metadata; the post-retrieval check remains necessary if metadata is stale. Only authorized text reaches the language model. Sources are built from the authorized result set.

Audit and threats
Sensitive operations create audit records; unauthorized access creates security events. Prompt-injection detection treats document instructions as untrusted and does not grant them authority. Tests cover token rejection, role checks, tenant isolation, IDOR, expiry/revoke, pre-filter shape, post-retrieval filtering, and no unauthorized LLM context.

Limitations and review
RAG quality scores do not establish authorization correctness. Security test coverage is not proof against all threats. Product Security reviews access paths, tenant filters, vector payload synchronization, and context construction quarterly.""",
    },
    {
        "title": "RAGVault Engineering Architecture",
        "file_name": "ragvault-engineering-architecture-expanded.txt",
        "content": """RAGVault Engineering Architecture
Document owner: Platform Engineering
Review frequency: Quarterly
Classification: Internal

Purpose and scope
Describe the RAGVault request and ingestion pipeline for engineers maintaining the service.

Components
FastAPI exposes authentication, document, permission, administration, and RAG routes. PostgreSQL stores users, tenant IDs, document content, permissions, temporary grants, access requests, audit logs, and security events. Qdrant stores embedded text chunks and metadata. The frontend calls the API through its configured public API URL. The configured language model generates an answer only after secure context construction.

Ingestion
Supported uploads are TXT, PDF, and DOCX. The loader extracts text; chunk_text currently uses 500-character chunks with 50-character overlap. Embeddings are 384-dimensional. Each Qdrant payload includes document ID, chunk index, tenant ID, classification, title, file name, text, allowed user IDs, and allowed roles. Permission synchronization updates ACL metadata without regenerating embeddings.

Query path
The production RAG route requests secure context with the pipeline's default limit of five. The RAGAS evaluation runner also defaults to five retrieved chunks. Qdrant applies tenant and user/role filters before returning candidates. The pipeline then validates each candidate using database authorization before context assembly. The LLM receives only the filtered context, and the route records a query audit event.

Operations and failure modes
Document updates require re-ingestion; permission changes require ACL synchronization. Expired or revoked access must fail the database check even if vector metadata is stale. Monitor PostgreSQL, Qdrant, model-provider errors, ingestion failures, and audit persistence.

Exceptions and audit
Do not bypass authorization to improve retrieval scores. Changes to chunking, top-k, model, or permission filters require review and a recorded evaluation. Owner: Platform Engineering; review quarterly.""",
    },
    {
        "title": "Vendor Security Assessment Guide",
        "file_name": "vendor-security-assessment.pdf",
        "format": "pdf",
        "content": """Vendor Security Assessment Guide
Document owner: Third-Party Risk
Review frequency: Annual
Classification: Internal

Purpose
This guide explains how procurement and Security assess a vendor before sensitive information or production connectivity is approved.

Scope and definitions
A vendor is an external service provider processing company or customer information. A critical vendor can affect confidentiality, integrity, availability, or a regulated business process. A security questionnaire is evidence to review, not a substitute for verification.

Roles
The business sponsor documents purpose, data, integrations, and business dependency. Procurement confirms contractual terms and subprocessors. Security reviews access controls, encryption, incident handling, vulnerability management, and independent assurance. Privacy reviews personal-data flows. Legal approves contract language.

Assessment procedure
1. Classify proposed data and identify tenant or customer boundaries.
2. Request current assurance artifacts, incident-notification terms, data location, retention/deletion commitments, and a subprocessor list.
3. Scope requested API credentials to the minimum resources; require individual administrative identities and multifactor authentication where supported.
4. Verify encryption, backup, change management, access review, and tested recovery evidence against the proposed service tier.
5. Record gaps, compensating controls, accountable owners, approval, and reassessment date before production data is shared.

Rules and exceptions
No vendor receives credentials or Restricted data before written approval. A time-limited pilot uses synthetic or minimized data unless an exception is approved. Exceptions require Security, Privacy, and business-owner approval and an expiry.

Audit and review
Retain the assessment, decision, contract, and remediation evidence in the controlled vendor record. Reassess critical vendors annually and after a material incident or service change.""",
    },
    {
        "title": "Employee Access Lifecycle Guide",
        "file_name": "employee-access-lifecycle.docx",
        "format": "docx",
        "content": """Employee Access Lifecycle Guide
Document owner: Identity Operations
Review frequency: Annual
Classification: Internal

Purpose
Provide operational instructions for provisioning, changing, and removing employee application access.

Scope and definitions
This guide covers workforce accounts in company-managed applications. A joiner is a newly authorized worker; a mover changes duties; a leaver's employment ends. Customer tenant accounts remain under the tenant administrator's authority.

Roles
The manager verifies the business need and requested role. People Operations confirms identity and employment status. Identity Operations provisions or disables the account. The application owner confirms role mappings and reviews exceptional access.

Joiner steps
Confirm an approved ticket, verified identity, start date, manager, and tenant. Create an individual account, assign the least-privilege role, and require the user to complete authentication setup. Do not accept tenant ID or role claims supplied by the applicant as approval evidence.

Mover steps
Obtain the new manager-approved duties and effective date. Review current access, remove grants no longer needed, then add the approved role. Verify that the change did not expand access to unrelated tenants or documents.

Leaver steps
Use the authoritative termination time. Disable the account, revoke sessions and temporary grants where supported, and transfer business records to an authorized owner. Confirm completion and notify the manager. Escalate a high-risk termination to Security for coordinated containment.

Exceptions and audit
Urgent access is still approved, scoped, and time-limited. Record requester, approver, account, target system, role, effective time, and completion. Identity Operations reconciles leaver notifications daily and managers certify access quarterly.""",
    },
    {
        "title": "Employee Records Handling Standard",
        "file_name": "employee-records-handling.txt",
        "content": """Employee Records Handling Standard
Document owner: People Operations
Review frequency: Annual and after a material privacy or legal change
Classification: Confidential

Purpose and scope
Establish safeguards for personnel, payroll, benefits, performance, accommodation, and employee-relations records. Applies to People Operations, managers, approved processors, and systems storing employee records.

Definitions and roles
Employee record: information collected or created for an employment purpose. Record owner: the People Operations lead responsible for purpose and retention category. People Operations: approves operational access. Privacy and Legal: advise on sensitive processing, disclosure, and holds. System owners: enforce tenant, role, and document permissions.

Rules
Access is limited to named staff with a documented job need; general employee or manager roles do not automatically permit access to all HR files. Keep health, investigation, payroll, and identity-verification records separate from general personnel notes where supported. Do not place employee secrets or unnecessary identifiers in an AI prompt, shared support request, or broadly searchable knowledge collection. A document's Confidential label is not an access grant.

Procedure
Before creating or importing a record, identify its owner, purpose, audience, classification, and retention category. Verify the tenant and specific record permissions. Share only the minimum excerpt needed. Correct inaccurate information through the controlled record owner. On a role change or departure, promptly remove access and transfer records only to an authorized custodian.

Retention, exceptions, and audit
Follow the approved Document Retention Schedule and suspend disposal only for an active legal hold. Any broader or emergency access requires owner approval, written purpose, narrow scope, expiry, and retrospective review. Log access changes and disclosures. People Operations reviews HR entitlements quarterly and this standard annually.""",
    },
    {
        "title": "RAGVault Product Overview",
        "file_name": "ragvault-product-overview.txt",
        "content": """RAGVault Product Overview
Document owner: Product Management
Review frequency: Quarterly
Classification: Internal

Purpose and scope
RAGVault is a permission-aware retrieval-augmented generation application for searching approved enterprise documents. This overview describes the current product boundaries and is not a promise that every deployment has identical configuration.

Components and definitions
The Next.js frontend presents authentication, document management, access requests, administration, and question-and-answer screens. FastAPI provides the API. PostgreSQL stores users, tenant identifiers, source documents, grants, access requests, and audit records. Qdrant stores embedded chunks and retrieval metadata. The configured language model drafts answers from authorized retrieved context.

Roles and workflow
An administrator provisions tenant accounts and manages documents and grants. A user signs in, submits a question, and receives an answer with source documents where authorized results exist. Administrators can review access requests and security/audit views. A product administrator's authority remains inside the administrator's tenant.

Document lifecycle
Administrators can upload TXT, PDF, and DOCX sources. The service extracts text, divides it into chunks, creates embeddings, and indexes them with tenant and ACL metadata. Permission-aware retrieval applies filters before vector search and a second authoritative authorization check before model context construction. Updates and deletions must use the supported document workflow so stored text and vectors remain consistent.

Security and limitations
The model is not an identity provider, access approver, or source of authorization decisions. Retrieved content is untrusted and cannot override system instructions. Answers may be incomplete or incorrect; users should inspect cited sources. RAGAS measures answer and retrieval quality, not authorization security. Tenant isolation, access revocation, and leakage prevention require dedicated security tests.

Exceptions and audit
Use only approved tenant content and models. Product changes to indexing, retrieval, context construction, or permissions require engineering and security review. Sensitive administration and question activity are recorded where the API audit path supports it. Owner: Product Management; review quarterly.""",
    },
    {
        "title": "RAGVault Security Test Inventory",
        "file_name": "security-test-inventory.txt",
        "source_path": "knowledge_base_files/security-test-inventory.txt",
        "content": "",
    },
]

for _document in KNOWLEDGE_BASE_DOCUMENTS:
    _supplement = CORPUS_SUPPLEMENTS.get(_document["title"])
    if _supplement:
        _document["supplement"] = _supplement

KNOWLEDGE_BASE_DOCUMENTS.extend(ADDITIONAL_KNOWLEDGE_BASE_DOCUMENTS)
