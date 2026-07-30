# Phase 28: Functional Frontend Interaction Audit

All visible Review Spine controls are now connected to typed API calls or deliberate local UI state.

## Interaction checklist

| Surface | Control | Behavior |
| --- | --- | --- |
| Reviews | Search | Filters repository, PR number, author, and title; persists as `q` in the URL |
| Reviews | Status/severity/repository/author filters | Combine together and persist as URL parameters |
| Reviews | Sort | Supports newest, oldest, severity, confidence, and finding count |
| Reviews | Filters / clear | Opens the filter region and clears all active filters |
| Reviews | Review row | Navigates to the matching review workspace |
| Reviews | Connect repository | Navigates to settings |
| Review workspace | Changed file | Updates the active file and diff heading |
| Review workspace | Changes/Summary/Checks | Switches the visible workspace panel |
| Review workspace | Finding | Selects the finding and highlights its affected line |
| Review workspace | Resolve | Persists finding state through FastAPI and updates open counts |
| Review workspace | Dismiss | Requires a reason and persists dismissal |
| Review workspace | Comment | Opens a composer and persists the comment |
| Review workspace | Approve / dismiss all | Requires confirmation/reason and persists review decision |
| Review workspace | Copy link | Copies the current URL |
| Review workspace | Open on GitHub | Opens the repository pull-request URL in a new tab |
| HITL queue | Approve / reject / escalate | Requires a reason, persists the decision, and removes completed item |
| Settings | Minimum severity | Edits and validates the review threshold |
| Settings | Ignored paths | Adds, removes, and persists patterns |
| Settings | Notifications | Toggles and persists notification preference |
| Settings | Save | Shows saving, success, validation, and API error states |
| Trace | Event row | Selects an event and displays details |
| Economics | Usage/budget | Loads typed data from the backend with empty and error states |

## API surface

- `GET /reviews`
- `GET /reviews/{review_id}`
- `POST /reviews/{review_id}/findings/{finding_id}/resolve`
- `POST /reviews/{review_id}/findings/{finding_id}/dismiss`
- `POST /reviews/{review_id}/decision`
- `POST /reviews/{review_id}/comments`
- `GET /reviews/{review_id}/trace`
- `GET/PUT /reviews/settings/current`
- Existing `/hitl/*` and `/economics/*` endpoints remain available.

## Verification

- Frontend lint: passed with ESLint CLI configuration.
- Frontend production build and type checking: passed.
- Backend tests: 75 passed, 1 skipped.
- Browser checks: dashboard filtering and URL state, review navigation, finding dismissal with reason, comment submission, resolve action, settings save, HITL approval, trace selection, and console errors.
- Docker Compose backend and frontend services rebuilt and running locally.
