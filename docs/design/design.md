- Loading, empty, error, permission, and offline behaviour
- Keyboard and screen-reader notes
- Data fields and formatting rules
- Acceptance criteria
- Screenshot evidence

Development rules:

- Do not add raw hex values to templates.
- Do not create a one-off component without adding it to the style guide or recording why it is intentionally local.
- Do not hide a dead control behind styling.
- Do not use client-only behaviour when a normal page load is required.
- Do not treat visual similarity as complete without state and accessibility review.

---

## 22. Design review checklist

### Product clarity

- [ ] The page has one primary purpose.
- [ ] The primary action is obvious.
- [ ] The current project, client, or document context is visible.
- [ ] Status and next action are understandable.

### Visual design

- [ ] Tokens are used consistently.
- [ ] Text hierarchy is clear.
- [ ] Spacing follows the system.
- [ ] Contrast passes the approved targets.
- [ ] Numeric data aligns correctly.
- [ ] The page is not visually overloaded.

### Interaction

- [ ] All controls work.
- [ ] Loading and saving are visible.
- [ ] Destructive actions explain consequences.
- [ ] Empty and error states are actionable.
- [ ] Back, refresh, direct URL, and failed request behaviour are considered.

### Responsive behaviour

- [ ] 360 px reviewed.
- [ ] 390 px reviewed.
- [ ] 768 px reviewed.
- [ ] 1024 px reviewed.
- [ ] 1440 px reviewed.
- [ ] No unintended horizontal scrolling.
- [ ] Sticky elements respect safe areas and the keyboard.

### Accessibility

- [ ] Landmarks and heading structure are correct.
- [ ] Keyboard path is complete.
- [ ] Focus is visible and restored after overlays.
- [ ] Fields have labels and useful errors.
- [ ] Dynamic updates are announced appropriately.
- [ ] Colour is not the only signal.
- [ ] Touch targets are at least 44 px where applicable.
- [ ] Reduced motion is respected.

### Evidence

- [ ] 390 px screenshot captured.
- [ ] 1440 px screenshot captured.
- [ ] Automated tests pass.
- [ ] Representative user task completed.
- [ ] Decision log and style guide updated.

---

## 23. Open design decisions

These items must be resolved before the related phase is considered complete:

1. Final Jimcan logo, brand colours, and approved font family.
2. Exact KPI definitions and dashboard calculation windows.
3. Role and permission matrix.
4. Two-factor authentication scope.
5. Supported browsers, phones, and screen readers.
6. BOQ calculation, versioning, locking, and concurrency rules.
7. Tax rates, rounding, filing, and period-locking rules.
8. Invoice numbering and adjustment/void rules.
9. Supported offline actions and conflict strategy.
10. Public enquiry privacy, retention, and spam-protection rules.
11. Approved document templates and paper sizes.
12. Search scope and ranking behaviour.
13. Analytics and privacy requirements.

Each decision must record its owner, date, reasoning, affected screens, and implementation impact.

## 24. Design definition of done

A screen or feature is design-complete only when:

- Its purpose and primary action are clear.
- Its normal, loading, empty, error, permission, offline, and locked states are defined where relevant.
- Desktop and mobile layouts are specified.
- Components use approved tokens.
- Accessibility behaviour is documented.
- Copy is final enough to test layout and meaning.
- The data contract is known.
- Acceptance criteria are testable.
- The style guide and decision log are updated.
- A representative user can complete the intended task.
