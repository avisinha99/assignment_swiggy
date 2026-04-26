# Demo Walkthrough

Use Swagger at `/docs` and follow this exact sequence.

## 1) Create Project
`POST /api/projects`

```json
{
  "key": "DEMO",
  "name": "Demo Project"
}
```

Copy `project_id` from the response.

## 2) Create Issues (Epic -> Story -> Sub-task)
`POST /api/projects/{project_id}/issues` (Epic)

```json
{
  "type": "epic",
  "title": "Auth revamp",
  "description": "Top level epic",
  "priority": "high",
  "labels": ["auth", "backend"]
}
```

`POST /api/projects/{project_id}/issues` (Story under Epic)

```json
{
  "type": "story",
  "title": "OAuth login",
  "description": "Implement OAuth flow",
  "priority": "high",
  "story_points": 5,
  "parent_id": "<EPIC_ID>",
  "labels": ["auth"]
}
```

`POST /api/projects/{project_id}/issues` (Sub-task under Story)

```json
{
  "type": "sub_task",
  "title": "Add callback handler",
  "priority": "medium",
  "parent_id": "<STORY_ID>"
}
```

## 3) Board State
`GET /api/projects/{project_id}/board`

## 4) Workflow Validation
Attempt invalid transition:
`POST /api/issues/{issue_id}/transitions`

```json
{ "to_status": "done" }
```

Expected: `422` with allowed transitions.

Then valid transitions in order:
- `{ "to_status": "in_progress" }`
- `{ "to_status": "in_review" }`
- `{ "to_status": "done" }`

## 5) Sprint Flow
Create sprint:
`POST /api/projects/{project_id}/sprints`

```json
{
  "name": "Sprint 1",
  "start_date": "2026-04-25",
  "end_date": "2026-05-08"
}
```

Start sprint:
`POST /api/sprints/{sprint_id}/start`

Move issue to sprint:
`PATCH /api/issues/{issue_id}`

```json
{ "sprint_id": "<SPRINT_ID>" }
```

Complete sprint (no carry-over):
`POST /api/sprints/{sprint_id}/complete`

```json
{
  "carry_over_issue_ids": [],
  "carry_over_to_sprint_id": null
}
```

## 6) Comments, Mentions, Notifications
Add a comment with mention:
`POST /api/issues/{issue_id}/comments`

```json
{
  "body": "Please review @jane@demo.com"
}
```

Check Jane's notifications:
`GET /api/notifications?user_email=jane@demo.com&limit=50`

## 7) Watchers
- `POST /api/issues/{issue_id}/watch`
- `POST /api/issues/{issue_id}/unwatch`

## 8) Activity Feed (Audit Trail)
`GET /api/projects/{project_id}/activity?limit=50`

## 9) Search + Filtering
- `GET /api/search?limit=50`
- `GET /api/search?status=in_progress&limit=50`
- `GET /api/search?priority=high&limit=50`

## 10) WebSocket Realtime Demo
Run websocket test client:

```bash
python ws_test.py
```

Then create/update/transition an issue from Swagger and observe streamed events (`issue_created`, `issue_updated`, `issue_moved`, `comment_added`) in the websocket terminal.
