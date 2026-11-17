# Feature Development Workflow

## 1. Feature lifecycle

1. Problem statement and evidence.
2. User story and measurable outcome.
3. Scope and non-goals.
4. UX flow and states.
5. Data model and API contract.
6. Security/privacy review.
7. Implementation plan and test plan.
8. Development behind feature flag if needed.
9. QA and acceptance review.
10. Documentation and release notes.
11. Production monitoring and feedback.

## 2. Required feature ticket template

```markdown
## Problem
Who experiences what problem, and what evidence supports it?

## User story
As a [user], I want [capability], so that [outcome].

## Scope
- Included:
- Excluded:

## Acceptance criteria
- Given / When / Then:

## Data and API impact
- Tables:
- Endpoints:
- Events/jobs:

## Security and privacy
- Tenant scope:
- Permissions:
- Sensitive data:

## UX states
- Loading:
- Empty:
- Error:
- Partial:
- Success:

## Tests
- Unit:
- Integration:
- Contract:
- Security:

## Rollout and rollback
- Feature flag:
- Migration:
- Monitoring:
```

## 3. Definition of Ready

A feature is ready to start when:
- The user problem is clear.
- Acceptance criteria are testable.
- Required data and permissions are understood.
- Design covers key states.
- Dependencies and assumptions are identified.
- Financial rule changes have an owner and expected test fixtures.

## 4. Definition of Done

A feature is done when:
- Acceptance criteria pass.
- Tests cover expected and adverse paths.
- Tenant isolation and role checks are implemented.
- Errors are safe and actionable.
- Logs/metrics are available without exposing sensitive payloads.
- Documentation and API contracts are updated.
- Accessibility checks pass for user-facing flows.
- Feature is reviewed and deployable with a rollback path.

## 5. Financial feature special controls

- Add independent expected-result fixtures.
- Use decimal arithmetic.
- Document sign convention and rounding.
- Persist calculation/ruleset version.
- Include traceability to original source rows.
- Add regression tests for refunds, split settlements, fees, duplicates and date boundaries.
- Require human review when match confidence is insufficient.

## 6. Pull request rules

- Keep PRs small and single-purpose.
- Include screenshots for meaningful UI changes.
- Include migration notes where schema changes.
- Never include real customer data in tests or screenshots.
- Require reviewer approval for authorization and reconciliation changes.
