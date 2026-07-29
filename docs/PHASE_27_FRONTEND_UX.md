# Phase 27: Human-Crafted Frontend UX

Review Spine's frontend now treats review work as a focused engineering workflow rather than a generic dashboard.

## Product decisions

- The review desk leads with work that needs a developer's judgment: open reviews, reviews awaiting action, unresolved findings, and completed reviews.
- The review workspace uses three stable areas on desktop: changed files, code context, and findings. On smaller screens, the file list becomes horizontally scrollable and findings stack beneath the diff.
- AI output is framed as a finding with severity, evidence location, confidence, agent source, and a suggested next step. It is never presented as an unquestionable defect.
- Review decisions are visible state changes. Approve, dismiss, and resolve actions update the summary status immediately in the client UI.
- Search and status filtering are local, fast, and preserve the page layout while the queue changes.

## Visual system

- Neutral gray background and white work surfaces keep code and severity signals legible.
- Teal is reserved for primary actions and completed/healthy states. Amber marks human attention. Red marks high-severity risk. Blue is used for informational affordances.
- Borders and spacing provide hierarchy; cards are limited to metrics and framed tools.
- Typography uses a system UI stack for product copy and a monospace stack for file paths and code.
- Controls use 6px radii and Lucide icons, with semantic labels and visible focus states.

## Verification

- `npm run build` passes.
- `python -m pytest` passes: 73 passed, 1 skipped.
- Docker Compose frontend image rebuilt and recreated successfully.
- Live checks passed at `http://localhost:3000/reviews` and `http://localhost:3000/reviews/review-1`.
- Visual checks covered the desktop review desk, desktop review workspace, and a 390px mobile review desk viewport.
