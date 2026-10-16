"""Substantive corpus expansions and additional evaluation documents."""

CORPUS_SUPPLEMENTS = {
    "Information Security Policy": """\
Operational controls
Managers approve access against current duties rather than job title alone.
System owners review privileged accounts each quarter and ordinary access annually.
Production secrets are retrieved from the approved secret manager at runtime.
Security Operations records incident severity, containment owner, and next review time.
Information owners identify customer-specific handling terms before data is indexed.
Users report suspected credential exposure through the incident channel immediately.
Review evidence
The annual review samples access approvals, exception expiries, and change records.
Material policy exceptions include compensating control evidence and a named reviewer.
Control gaps receive an owner, due date, and risk acceptance or remediation decision.
""",
    "Access Control Policy": """\
Decision and review controls
Authorization uses the authenticated identity and authoritative tenant membership.
User-specific and role-based grants are scoped to the individual document resource.
Administrators cannot use a role in one tenant to cross another tenant boundary.
Grant changes update the authoritative record before retrieval metadata is synchronized.
The application rechecks current permission after vector search and before disclosure.
Access reviews compare active grants with current business need and document ownership.
Denied requests disclose neither document contents nor neighboring resource identifiers.
Reviewers retain approval, change, and revocation evidence with timestamps.
""",
    "Employee Access Management Standard": """\
Operational checks
Managers submit role changes with the affected employee and effective date.
IAM reconciles new-hire and termination notices against the authoritative roster.
Provisioners verify tenant membership independently of user-supplied request fields.
Moved employees lose obsolete grants before unrelated new access is added.
Leaver processing includes active sessions and document-specific temporary grants.
Service credentials are reviewed separately from the employee's personal account.
Evidence includes the approved request, granted role, completion time, and reviewer.
""",
    "Data Classification and Handling Standard": """\
Handling decision examples
An internal process note remains in an approved company workspace.
A confidential customer report is available only to named authorized recipients.
Restricted credentials are removed rather than embedded in a searchable document.
Changing a label does not alter the tenant or document permission record.
Before indexing, the owner confirms audience, source quality, and retention category.
Derived text chunks inherit the source document's access boundary.
The owner documents a reclassification decision and informs downstream custodians.
""",
    "Incident Response Playbook": """\
Operational decision points
The incident commander assigns a severity, evidence custodian, and communication lead.
Containment actions preserve forensic evidence unless immediate safety requires otherwise.
Credential compromise triggers account restriction and supported session revocation.
Suspected cross-tenant disclosure is escalated as a confidentiality incident.
Recovery is accepted only after owners validate service behavior and access boundaries.
External notification decisions are made by the authorized Legal and Privacy contacts.
Each corrective action has an owner, risk statement, due date, and closure evidence.
""",
    "Document Retention and Disposal Schedule": """\
Operational disposal controls
The records owner identifies the governing retention category before ingestion.
Legal holds suspend scheduled disposal only for the records in the hold scope.
Deletion covers the source object, extracted text, and derived vector points.
The operator records which systems were checked and any inaccessible replica.
Immutable backup copies expire under the documented backup lifecycle.
A deletion receipt must distinguish completed system deletion from backup aging.
Restores reapply current retention and access policy before users can retrieve content.
""",
    "Remote Work Security Standard": """\
Remote-work operating checks
Users connect through approved identity controls and do not share active sessions.
The endpoint reports supported encryption and current security updates.
Sensitive information is not copied to an unmanaged personal device for convenience.
Users verify the recipient and classification before screen sharing or printing.
Lost devices are reported promptly so administrators can revoke access where supported.
Public networks require the approved protected connection before sensitive work.
Managers review exceptions for device ownership, scope, and an explicit expiry.
""",
    "Acceptable Use Standard": """\
Permitted testing and handling
Security testing requires written authorization, defined targets, and a time window.
A test account does not authorize access to another tenant's real customer data.
Users report suspected exposure rather than downloading additional material to confirm it.
Automation must respect service limits and must not bypass access-control checks.
Public demonstrations use synthetic or specifically approved information.
Access credentials remain personal and may not be shared with coworkers.
Violations are referred to the responsible manager and Security for documented review.
""",
    "AI Use and Governance Standard": """\
Operational safeguards
Use-case owners document model provider, data flow, intended audience, and limitations.
Retrieved documents are evidence to evaluate, never authority to change system rules.
The application supplies only context authorized for the current authenticated user.
Generated content is reviewed before it drives a consequential operational decision.
Evaluation questions and references are checked for secrets and unnecessary identifiers.
Model or prompt changes trigger a targeted regression evaluation and security review.
Evaluation scores are recorded with dataset, retrieval settings, and evaluator model.
""",
    "Temporary Access Management Standard": """\
Lifecycle evidence
The grant record identifies one tenant-scoped user, document, purpose, and expiry.
The approver is distinct from the requester when separation of duties is required.
Expiry checks use the current decision time and do not depend on scheduled cleanup.
Revocation removes the authoritative grant before the vector ACL is refreshed.
The post-retrieval authorization check denies stale vector metadata after expiry.
An extension creates a new approved time window rather than silently prolonging access.
Audit evidence records grant, expiry, early revoke, and synchronization outcome.
""",
    "Data Privacy Standard": """\
Privacy review procedure
The owner records purpose, categories, recipients, provider, region, and retention.
Only fields needed for the approved purpose enter prompts or evaluation artifacts.
Support exports use masked identifiers and exclude authentication secrets.
Deletion requests are coordinated with legal holds and derived-index disposal.
Cross-tenant content is never a permitted source for answering another tenant.
Privacy reviews changes in audience or model provider before production use.
Unintended disclosure is routed to incident response for impact assessment.
""",
    "Authentication and Password Standard": """\
Identity assurance checks
Token validation checks signature, expiry, and the corresponding active database user.
The application does not treat a token's tenant claim as a substitute for membership.
Administrative account creation is tenant-scoped and does not return password hashes.
Authentication failures use non-disclosing responses and are monitored for abuse.
Users report suspected token exposure so supported sessions can be revoked.
Password reset and account recovery require an approved identity-verification path.
Privileged access receives stronger authentication where the deployment supports it.
""",
    "Security Monitoring and Audit Standard": """\
Review workflow
An audit record explains a sensitive action; a security event describes a threat signal.
Each record uses the available actor, tenant, target, outcome, and timestamp fields.
Repeated denials are reviewed for user error, scanning, or attempted boundary crossing.
Log access is limited to responders with a documented operational need.
Investigators preserve the relevant event identifiers before changing retention state.
Audit records exclude bearer tokens, password material, and full restricted document text.
Control owners document telemetry gaps rather than interpreting missing events as success.
""",
    "RAGVault Security Architecture": """\
Enforcement boundaries
JWT authentication identifies an active user before protected routes execute.
The user's database-backed tenant and role are passed to the retrieval component.
Qdrant filters tenant and user or role ACL metadata before returning candidate chunks.
The authoritative permission service checks each returned document again.
Only authorized results are formatted into the LLM context and source list.
Permission revocation synchronizes vector metadata after the database change.
Audit records and security events are separate evidence for sensitive actions and denials.
""",
    "RAGVault Engineering Architecture": """\
Implementation and operational notes
The API validates question length and retrieval limits before embedding a query.
Chunk identifiers are stable per document and chunk index for vector replacement.
Ingestion stores tenant, classification, document identity, and ACL payload fields.
Permission synchronization updates payloads without regenerating document embeddings.
The document loader rejects unsupported extensions and malformed PDF or DOCX files.
The RAGAS runner saves each metric atomically and skips valid saved scores on resume.
The v2 evaluation selects a dedicated evaluator model without changing the product LLM.
""",
    "Employee Access Lifecycle Guide": """\
Operational exceptions and evidence
An urgent joiner request still identifies a manager, tenant, role, and expiry if temporary.
Identity Operations records the source of the employment-status instruction.
The application owner validates that the new role exposes only required screens and data.
Mover validation confirms that obsolete access was removed before closure.
Leaver evidence includes account disablement and supported session revocation outcomes.
Records transfer names the receiving custodian and does not make the recipient an owner by default.
Quarterly certification records reviewer, decision, and remediation for stale entitlements.
""",
    "Employee Records Handling Standard": """\
Operational safeguards
Payroll, accommodation, and investigation records use narrower audiences than general HR files.
Managers receive only records necessary for their assigned responsibilities.
Exports identify the recipient, purpose, and authorized transfer method.
AI evaluation uses synthetic personnel examples unless real data is explicitly approved.
Corrections are routed to the system of record owner rather than copied into side files.
Temporary review access names the individual reviewer and an expiry.
People Operations verifies access removal when a case owner changes roles or leaves.
""",
    "RAGVault Product Overview": """\
User-visible boundaries
The interface presents documents and sources returned by the authorized API response.
The frontend is not the security boundary; every operation is authorized by the backend.
A missing source does not imply that a user may request another tenant's content.
Administrators manage users and documents only within their own tenant scope.
Access requests record an intended resource and require authorized review before grant.
Audit and security panels display records returned by protected administrative endpoints.
Product availability and model responses depend on the configured deployment services.
""",
}

CORPUS_SUPPLEMENT_ADDENDA = {
    "Access Control Policy": """\
Reviewers sample both allowed and denied resource decisions.
Role changes trigger a review of inherited document grants.
Evidence is linked to the exact resource and tenant.
""",
    "Employee Access Management Standard": """\
Managers certify active access against current duties.
Expired temporary grants are not renewed automatically.
IAM records the completion time for each lifecycle change.
""",
    "Data Classification and Handling Standard": """\
Owners review classification when the source or audience changes.
Derived chunks retain the source document's handling boundary.
Misclassified material is quarantined until the owner decides.
""",
    "Incident Response Playbook": """\
Responders avoid copying restricted evidence into broad channels.
Containment decisions record expected service and customer impact.
The incident owner confirms each corrective action is closed.
""",
    "Document Retention and Disposal Schedule": """\
Owners re-check holds immediately before scheduled disposal.
Deletion evidence names the source and every derived store checked.
Restored data receives the current retention and permission rules.
""",
    "Remote Work Security Standard": """\
Users lock unattended devices before leaving a work area.
Support requests exclude screenshots containing restricted records.
Managers review any approved unmanaged-device exception.
""",
    "Acceptable Use Standard": """\
Testing output is stored only in the approved evidence location.
Users do not probe resources outside the written test scope.
Suspected accidental access is reported without further browsing.
""",
    "AI Use and Governance Standard": """\
Reviewers distinguish retrieved evidence from model-generated wording.
Dataset changes are recorded separately from model changes.
Security approval is required before changing authorization behavior.
Prompt changes are reviewed for disclosure and injection effects.
The use-case owner records the intended human review boundary.
""",
    "Data Privacy Standard": """\
The owner documents whether derived text remains personal data.
Evaluation results avoid direct identifiers unless approved.
Deletion and correction requests are tracked to a disposition.
""",
    "Authentication and Password Standard": """\
Shared credentials are prohibited unless an approved exception exists.
Token-bearing requests use the protected transport configured by deployment.
Inactive accounts are disabled through the authoritative identity record.
""",
    "Security Monitoring and Audit Standard": """\
Reviewers verify that denial events do not include protected text.
Sensitive audit access is limited to authorized investigation roles.
Retention follows the approved evidence and privacy schedule.
""",
    "RAGVault Security Architecture": """\
The model has no authority to approve a permission or change a grant.
A failed authorization check removes the candidate from secure context.
Source metadata is returned only for authorized retrieved results.
""",
    "RAGVault Engineering Architecture": """\
Evaluation artifacts are kept separate from production model configuration.
The runner never substitutes a missing score with a default value.
ACL changes are validated using both retrieval and authorization evidence.
""",
    "Employee Records Handling Standard": """\
An approved transfer records the recipient and business purpose.
General role membership does not expose sensitive case files.
Auditors sample removals after employee role changes.
The record owner verifies the retention category before export.
Disclosures are logged with the recipient and approved purpose.
""",
    "RAGVault Product Overview": """\
The API remains authoritative when client state or UI controls are stale.
Unavailable model output does not change document authorization.
Users can distinguish an answer from its listed source records.
""",
}
for _title, _addendum in CORPUS_SUPPLEMENT_ADDENDA.items():
    CORPUS_SUPPLEMENTS[_title] += _addendum


def _make_document(
    title: str,
    file_name: str,
    owner: str,
    purpose: str,
    scope: str,
    roles: tuple[str, ...],
    rules: tuple[str, ...],
    procedures: tuple[str, ...],
    examples: tuple[str, ...],
    exceptions: tuple[str, ...],
    audit: tuple[str, ...],
    *,
    format_name: str | None = None,
    legacy_file_names: tuple[str, ...] = (),
) -> dict[str, str]:
    sections = (
        (title, f"Document owner: {owner}", "Review frequency: Annual", "Classification: Internal"),
        ("Purpose", purpose),
        ("Scope", scope),
        (
            "Definitions",
            "Control owner: the role accountable for implementation and evidence.",
            "Exception: a documented, approved, and time-bounded deviation.",
        ),
        ("Roles and responsibilities", *roles),
        ("Mandatory rules", *rules),
        ("Operating procedure", *procedures),
        ("Examples", *examples),
        ("Exceptions", *exceptions),
        ("Audit evidence and review", *audit),
    )
    content = "\n\n".join("\n".join(section) for section in sections)
    document = {
        "title": title,
        "file_name": file_name,
        "content": content,
    }
    if format_name:
        document["format"] = format_name
    if legacy_file_names:
        document["legacy_file_names"] = list(legacy_file_names)
    return document


ADDITIONAL_KNOWLEDGE_BASE_DOCUMENTS = [
    _make_document(
        "Document Ingestion and Source Validation Standard",
        "document-ingestion-source-validation.txt",
        "Content Platform Engineering",
        "Define safe intake and validation for business documents entering a searchable knowledge collection.",
        "Applies to TXT, PDF, and DOCX uploads and their extracted text, chunks, embeddings, and source metadata.",
        ("The uploader confirms ownership and permitted use.", "The document owner approves audience and classification.", "Platform Engineering maintains parsers and ingestion evidence."),
        ("Supported extensions are checked before parsing.", "Malformed or empty extraction is rejected instead of indexed.", "The stored source remains associated with its tenant and document identity.", "Extracted content is treated as untrusted data.", "Ingestion never grants access that the source permission record does not grant."),
        ("Record uploader, tenant, source name, and classification.", "Extract text using the format-specific loader and inspect extraction errors.", "Chunk content with the configured overlap and generate normalized embeddings.", "Attach document and ACL metadata to each vector point.", "Verify source count and vector count after ingestion or replacement."),
        ("A scanned image with no extractable text requires an approved OCR path.", "A DOCX with tables is checked for extraction limitations before operational use."),
        ("A parser exception blocks indexing and is escalated with the source identifier.", "A retry is recorded and does not create duplicate points for the same chunk."),
        ("Retain extraction outcome, parser version, and ingestion timestamp.", "Review malformed-file and duplicate-source rates quarterly."),
        legacy_file_names=("upload_test.txt",),
    ),
    _make_document(
        "Business Continuity and Recovery Plan",
        "business-continuity-recovery-plan.pdf",
        "Business Resilience",
        "Coordinate service recovery while preserving tenant and authorization boundaries.",
        "Covers RAGVault API, PostgreSQL, Qdrant, document storage, identity dependencies, and operator communications.",
        ("The incident commander sets recovery priorities.", "Service owners restore components and verify health.", "Security validates access controls before user traffic resumes."),
        ("Recovery objectives are approved by service owners.", "Backups are protected separately from production credentials.", "A restored vector index must match the source tenant and ACL metadata.", "Failover does not bypass authentication or authorization.", "Unverified content is not exposed during degraded operation."),
        ("Declare the incident and assign a recovery lead.", "Restore database state from the approved recovery point.", "Restore or rebuild vectors from authorized source records.", "Run health, tenant-filter, and permission checks in a restricted environment.", "Resume traffic after security and business owners accept evidence."),
        ("If Qdrant is rebuilt, re-ingest through the tenant-aware document workflow.", "If the API is unavailable, users receive a service notice rather than an alternate unsecured export."),
        ("Emergency access is time-limited and logged.", "A recovery exception names the approver and compensating monitoring."),
        ("Record recovery point, component versions, verification results, and downtime.", "Run a tabletop exercise annually and track corrective actions."),
        format_name="pdf",
        legacy_file_names=("upload_test.pdf",),
    ),
    _make_document(
        "Change Management Standard",
        "change-management-standard.docx",
        "Engineering Operations",
        "Ensure production changes are reviewed, attributable, and recoverable.",
        "Applies to application code, infrastructure, database schema, prompts, retrieval configuration, and permission logic.",
        ("The change owner documents intended behavior.", "A peer reviews implementation and test evidence.", "Operations coordinates release and rollback."),
        ("Changes use version-controlled source.", "Security-sensitive changes include authorization regression tests.", "Database changes include compatibility and recovery considerations.", "Prompt changes do not weaken the authorized-context boundary.", "Emergency changes receive retrospective review."),
        ("Describe scope, risk, dependencies, and rollback.", "Run focused tests and required suite checks.", "Obtain required peer and security approval.", "Deploy using the approved pipeline and monitor health.", "Close with test, deployment, and rollback evidence."),
        ("A retrieval top-k experiment stays in evaluation unless production approval is granted.", "A permission change is tested against allowed and denied cases."),
        ("Emergency changes identify an incident, owner, time limit, and reviewer.", "A failed deployment triggers rollback or documented containment."),
        ("Retain reviewer, commit, build, deployment, and outcome identifiers.", "Review failed changes and emergency releases monthly."),
        format_name="docx",
        legacy_file_names=("upload_test.docx",),
    ),
    _make_document(
        "Secure Software Development Standard",
        "secure-software-development-standard.txt",
        "Application Security",
        "Integrate security requirements throughout design, implementation, review, and release.",
        "Applies to backend APIs, frontend code, evaluation utilities, infrastructure definitions, and dependencies.",
        ("Developers own secure implementation.", "Reviewers examine trust boundaries and failure handling.", "Security advises on high-risk design changes."),
        ("Validate untrusted input at API boundaries.", "Use parameterized database access and typed schemas.", "Keep credentials in deployment secrets, never source.", "Require authorization on the server for every protected operation.", "Do not return internal exception details to users."),
        ("Document data flows and trust boundaries.", "Add tests for allowed, denied, and malformed requests.", "Review dependencies and configuration changes.", "Run static checks and the focused test suite.", "Record residual risk before release."),
        ("A UI-hidden admin button still requires backend authorization.", "A validation error omits passwords and tokens from its response."),
        ("A security exception has an owner, compensating control, and expiry.", "Critical unresolved findings block release."),
        ("Keep review and test evidence with the change.", "Reassess controls after material architecture changes."),
    ),
    _make_document(
        "API Security Standard",
        "api-security-standard.txt",
        "API Platform",
        "Protect API identities, resources, inputs, and responses against unauthorized use.",
        "Covers browser-facing and service-facing HTTP endpoints and uploaded content.",
        ("API owners define resource authorization.", "Identity services issue and validate credentials.", "Operators monitor abuse and errors."),
        ("Authenticate protected requests.", "Authorize using server-side tenant and resource records.", "Validate lengths, ranges, types, and file formats.", "Rate limits and body-size limits protect service capacity.", "Responses exclude tokens, hashes, and inaccessible resource contents."),
        ("Map endpoint to required role and tenant scope.", "Validate request schemas before database writes.", "Apply object-level checks to every identifier.", "Return stable 401, 403, 404, and 422 behavior as appropriate.", "Audit sensitive mutations without storing secrets."),
        ("An unknown document ID cannot be used to probe a neighboring tenant.", "An oversized RAG question is rejected before retrieval."),
        ("A versioned compatibility exception is bounded and monitored.", "Unsupported methods remain unavailable."),
        ("Review route authorization and validation tests each release.", "Monitor repeated failures and anomalous object access."),
    ),
    _make_document(
        "Cloud Security Configuration Baseline",
        "cloud-security-configuration-baseline.txt",
        "Cloud Platform Security",
        "Set minimum safeguards for deployed application and data services.",
        "Applies to container workloads, managed data services, networking, secrets, and observability.",
        ("Platform owners maintain deployment settings.", "Security reviews exposed interfaces.", "Service owners classify stored data."),
        ("Expose only required service ports.", "Use separate credentials for application dependencies.", "Keep development and production data separated.", "Encrypt traffic and storage where the platform supports it.", "Use health checks and least-privilege runtime identities."),
        ("Review network paths before deployment.", "Load secrets from protected runtime configuration.", "Patch base images and pinned dependencies.", "Verify backup and restore controls.", "Record service ownership and escalation contacts."),
        ("A local compose network is not assumed to be production-hardened.", "A health endpoint reports dependency status without returning credentials."),
        ("Temporary public exposure requires documented risk approval and expiry.", "Emergency credentials are rotated after the incident."),
        ("Review configuration drift and access logs.", "Reassess the baseline annually and after cloud changes."),
    ),
    _make_document(
        "Cryptographic Key Management Standard",
        "cryptographic-key-management-standard.txt",
        "Security Engineering",
        "Protect cryptographic keys used to secure data, communications, and service identities.",
        "Applies to encryption keys, signing keys, API credentials, and certificates used by company services.",
        ("Key custodians control lifecycle operations.", "Service owners request scoped key use.", "Security approves exceptional access."),
        ("Do not store keys in source control or retrieved documents.", "Limit key access to service identities and approved operators.", "Separate key material from encrypted data.", "Rotate keys after exposure or policy-defined lifecycle events.", "Log administrative key operations."),
        ("Inventory key owner, purpose, scope, and rotation date.", "Provision keys through the approved secret or key manager.", "Restrict permissions to required cryptographic actions.", "Test rotation and dependent service recovery.", "Revoke and replace compromised key material."),
        ("A model provider key is a runtime secret and is not an evaluator result.", "A signing key is not reused as a database password."),
        ("Break-glass access is approved, time-bounded, and reviewed.", "Unavailable key management blocks sensitive processing."),
        ("Retain rotation and revocation records without logging key values.", "Review key inventory quarterly."),
    ),
    _make_document(
        "Vulnerability Management Standard",
        "vulnerability-management-standard.txt",
        "Product Security",
        "Identify, prioritize, remediate, and verify security vulnerabilities.",
        "Covers application code, dependencies, container images, APIs, and deployed infrastructure.",
        ("Asset owners remediate findings.", "Security triages severity and exploitability.", "Release owners verify closure."),
        ("Track each finding to an owner and due date.", "Prioritize reachable and data-impacting weaknesses.", "Do not suppress a finding solely to meet a deadline.", "Test fixes against regression cases.", "Document accepted residual risk with an expiry."),
        ("Record affected component and evidence.", "Assess severity and exposure.", "Patch or mitigate through a reviewed change.", "Run focused tests and verify the fixed path.", "Close only when evidence supports remediation."),
        ("A dependency update includes compatibility tests.", "A public endpoint with object-ID access receives IDOR review."),
        ("A deadline exception names compensating controls and risk owner.", "An actively exploited issue follows incident response."),
        ("Report open aging and exceptions to the accountable owner.", "Review remediation trends monthly."),
    ),
    _make_document(
        "Backup and Restore Standard",
        "backup-and-restore-standard.txt",
        "Infrastructure Reliability",
        "Ensure recoverable data copies are protected and restoration is verifiable.",
        "Applies to relational records, uploaded sources, configuration, and derived vector indexes.",
        ("Data owners classify backup content.", "Operators run and test backups.", "Security reviews restore exposure."),
        ("Restrict backup access independently from production access.", "Protect backup transfer and storage.", "Define retention and deletion behavior.", "Do not claim immediate erasure from immutable backup media.", "Restore derived indexes only with current ACL state."),
        ("Identify source of truth and recovery point.", "Restore into a controlled environment.", "Reapply tenant and document authorization metadata.", "Validate counts, integrity, and access boundaries.", "Record acceptance before production use."),
        ("A Qdrant rebuild may regenerate vectors from authorized source documents.", "A retained backup expires under its documented lifecycle."),
        ("A legal hold changes disposal only within the recorded scope.", "Emergency restore is monitored and reviewed."),
        ("Record restore date, operator, source, and test results.", "Exercise recovery at the approved frequency."),
    ),
    _make_document(
        "Network Security Standard",
        "network-security-standard.txt",
        "Network Engineering",
        "Reduce unauthorized network reachability and protect service-to-service communication.",
        "Applies to API ingress, database and vector-store paths, administrative access, and outbound integrations.",
        ("Network owners define trust zones.", "Service owners request flows.", "Security reviews exceptions."),
        ("Expose only documented listeners.", "Keep databases off public ingress unless explicitly approved.", "Restrict outbound paths to required dependencies.", "Use protected transport for sensitive traffic.", "Monitor administrative and anomalous connections."),
        ("Inventory source, destination, port, owner, and purpose.", "Approve and implement the narrowest rule.", "Test expected connectivity and denied paths.", "Remove expired rules.", "Review changes against tenant and service boundaries."),
        ("A Docker service name resolves inside the compose network, not as an authorization control.", "A public health route returns status only."),
        ("Emergency access has a source restriction and expiry.", "Unnecessary open ports are removed."),
        ("Retain network change approvals and flow evidence.", "Review exposed services quarterly."),
    ),
    _make_document(
        "Secrets Management Standard",
        "secrets-management-standard.txt",
        "Platform Security",
        "Prevent credentials and tokens from being exposed through code, logs, documents, or evaluation artifacts.",
        "Applies to application secrets, database passwords, signing material, and provider API keys.",
        ("Secret owners define rotation.", "Service operators provision runtime access.", "Users report suspected exposure."),
        ("Never commit secrets or include them in URLs.", "Do not log bearer tokens, password hashes, or provider keys.", "Use individual or workload-scoped credentials.", "Limit access to the service and operators that need it.", "Rotate after exposure and remove stale credentials."),
        ("Provision through protected deployment settings.", "Verify the secret is absent from build output and response bodies.", "Restrict runtime environment access.", "Rotate and redeploy using approved procedure.", "Review logs and source history after suspected leakage."),
        ("A redacted validation error reports field location but not secret content.", "A test fixture uses a nonproduction placeholder."),
        ("Break-glass retrieval records custodian and expiry.", "Exposed credentials trigger incident response."),
        ("Audit secret lifecycle events without recording values.", "Review privileged secret access quarterly."),
    ),
    _make_document(
        "Data Quality and Provenance Standard",
        "data-quality-provenance-standard.txt",
        "Knowledge Operations",
        "Ensure searchable content is attributable, current, and suitable for its intended audience.",
        "Applies to uploaded documents, extracted text, generated evaluation corpus, and derived chunks.",
        ("Content owners confirm source accuracy.", "Knowledge operators maintain metadata.", "Reviewers assess stale or conflicting sources."),
        ("Every indexed source has an owner and unique identity.", "Preserve source provenance during extraction and chunking.", "Do not represent illustrative policy as adopted company policy.", "Resolve conflicting versions before broad indexing.", "Remove duplicates without dropping permission history."),
        ("Check source title, date, audience, and classification.", "Compare extracted text with the original where format risks exist.", "Record superseded status and replacement reference.", "Review duplicate titles and filenames.", "Re-ingest through the authorized workflow after approval."),
        ("A PDF extraction is checked for missing pages.", "A revised policy is not presented beside a stale copy without a version label."),
        ("Unverified content remains quarantined from production retrieval.", "A source exception has an owner and expiry."),
        ("Retain source checksum or version evidence where supported.", "Review stale-source reports quarterly."),
    ),
    _make_document(
        "Customer Data Isolation Standard",
        "customer-data-isolation-standard.txt",
        "Tenant Platform Engineering",
        "Prevent customer data from crossing tenant boundaries during storage, retrieval, administration, and response.",
        "Applies to source documents, vector payloads, application queries, grants, and support workflows.",
        ("Tenant owners approve membership.", "API services enforce tenant scope.", "Security reviews cross-tenant events."),
        ("Derive tenant identity from the authenticated server-side user.", "Filter vector retrieval by tenant before returning candidates.", "Check tenant and current permission after retrieval.", "Do not trust client-supplied tenant IDs.", "Do not expose unauthorized text to the LLM or response."),
        ("Create tenant-scoped records and vector metadata.", "Propagate authenticated identity into retrieval.", "Test same-tenant allowed and cross-tenant denied cases.", "Revoke access in the database and synchronize ACL metadata.", "Audit denials without disclosing protected contents."),
        ("An administrator can administer only their own tenant.", "A matching user ID in a different tenant does not grant access."),
        ("Support access is explicitly approved, scoped, and logged.", "No operational exception may authorize cross-tenant disclosure."),
        ("Review tenant identifiers through query and document lifecycle tests.", "Escalate unexpected cross-tenant results immediately."),
    ),
    _make_document(
        "Service Account and Workload Identity Standard",
        "service-account-workload-identity-standard.txt",
        "Identity Engineering",
        "Constrain non-human identities to a documented service purpose and lifecycle.",
        "Applies to backend services, scheduled jobs, ingestion workers, and deployment automation.",
        ("Service owners request workload access.", "Identity Engineering provisions identities.", "Operators remove unused credentials."),
        ("Use a dedicated identity per service where feasible.", "Grant minimum database and vector operations.", "Do not reuse an employee token as a service credential.", "Rotate credentials and certificates on schedule or compromise.", "Separate development, test, and production identities."),
        ("Record owner, environment, dependencies, and expiry.", "Approve scopes before provisioning.", "Store credentials in protected runtime configuration.", "Monitor service use and privilege changes.", "Disable and remove identities when the workload retires."),
        ("A RAGAS runner uses evaluation credentials and does not change the production LLM.", "A deployment role cannot grant user document permissions."),
        ("Temporary broad scope requires explicit approval and expiry.", "A missing owner is grounds to disable or reassign the identity."),
        ("Review service identity inventory quarterly.", "Audit provisioning and decommission evidence."),
    ),
    _make_document(
        "AI Model Change and Evaluation Standard",
        "ai-model-change-evaluation-standard.txt",
        "AI Governance and Platform Engineering",
        "Control changes to model, prompt, retrieval settings, and evaluation methodology.",
        "Applies to RAG answer generation, RAGAS evaluators, datasets, references, and indexed evaluation sources.",
        ("Model owners document provider and version.", "Evaluation owners preserve datasets and score provenance.", "Security validates that production authorization remains outside the model."),
        ("Do not mix evaluator models within a reported comparison set.", "Preserve completed scores and original baselines.", "Record model identity with each newly evaluated metric.", "Do not alter references or scores to manufacture a pass.", "Keep RAG quality claims separate from security assurance."),
        ("Freeze question, reference, corpus, and retrieval configuration.", "Select one evaluator model for a result set.", "Run missing cases sequentially and save each metric atomically.", "Investigate low scores using retrieved context and source evidence.", "Report changed evaluation inputs and comparison limitations."),
        ("A model change creates a separately labeled result artifact.", "An evaluator override never changes the production model setting."),
        ("Rate-limit failures pause evaluation rather than creating placeholder values.", "Changed inputs require explicit rescore and preserve prior snapshots."),
        ("Archive model, RAGAS version, settings, and coverage.", "Review metric status and failures before publishing a report."),
    ),
]
