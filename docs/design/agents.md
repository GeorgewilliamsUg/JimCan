### Implementer

Translates approved design into the application while preserving contracts and constraints.

### Reviewer

Checks correctness, completeness, consistency, accessibility, permissions, and scope.

### QA agent

Runs tests, visual checks, responsive checks, browser checks, and regression checks.

### Product owner

Approves business rules, priorities, trade-offs, open decisions, and release readiness.

One agent may perform more than one role only when the task is low risk. A high-impact change should receive an independent review.

## 18. Mandatory review checklist before approval

Before approving a change, the reviewer should confirm:

- [ ] The requested scope is clear.
- [ ] No unapproved files are changed.
- [ ] Existing user work is preserved.
- [ ] The design matches the source of truth.
- [ ] No requirements were invented.
- [ ] Permissions and data exposure are considered.
- [ ] Normal and exceptional states are covered.
- [ ] Responsive and accessibility behaviour is covered.
- [ ] Tests or evidence are appropriate.
- [ ] The change is reversible or its consequence is understood.
- [ ] Open questions are recorded.

## 19. Completion evidence

Every completed task report must include:

```text
Outcome:

Changed files:

Unchanged but reviewed:

Evidence:
- [test or check]
- [test or check]

Assumptions:

Open questions:

Risks:

Next approval needed:
```

Do not report only “done”.

## 20. Failure and blocking behaviour

If an agent cannot proceed safely:

1. Stop before mutation.
2. State the exact blocker.
3. Show the evidence.
4. Explain the decision required.
5. Offer one or more safe options.
6. Do not continue by silently choosing a high-impact assumption.

Examples of legitimate blockers:

- A missing permission rule changes who can see financial records.
- Two approved documents define different invoice numbering rules.
- A requested deletion has unknown consumers.
- The backend response shape is not available.
- A design change would require a new dependency or deployment change.

## 21. Change log requirement

Any change to this document must record:

- Date
- Author or agent
- Reason
- Sections changed
- Approval status

This document should evolve with the project, but agents must not weaken its permission or evidence requirements without explicit product-owner approval.

## 22. Final agent definition of done

An agent task is complete only when:

- The requested outcome is delivered or the blocker is clearly documented.
- The scope did not expand silently.
- All changes were approved at the correct permission level.
- No hallucinated facts or unverified claims remain.
- Relevant documents and decisions are updated.
- Appropriate tests or review evidence exist.
- Remaining risks and open questions are visible.
- The final report is concise, exact, and honest.
