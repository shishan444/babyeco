# SPEC-BE-TASK-001: Task System API

## Overview

Implement the task management API for creating, assigning, and managing tasks with check-in workflow.

**Business Context**: Tasks are the primary way children earn points. Parents create and assign tasks, children check in when complete, and parents approve to award points.

**Target Users**:
- Primary: Parent app (task management)
- Secondary: Child app (task viewing and check-in)

---

## Technical Constraints

### Framework and Versions
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0
- PostgreSQL 15+
- Background task processing (Celery/ARQ)

### Dependencies
- SPEC-BE-AUTH-001 (Authentication API)
- SPEC-BE-POINT-001 (Point System API)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall return only tasks accessible to the requesting user.

```
Given a task list request
When a parent requests
Then only their family's tasks are returned
When a child requests
Then only tasks assigned to them are returned
```

**UR-002**: The system shall validate task configuration before saving.

```
Given a task creation/update request
When the request is processed
Then title is required and within length limits
And point value is within allowed range
And at least one assignee is specified
```

**UR-003**: The system shall calculate task deadlines based on configuration.

```
Given a task with time window
When the task is active for the day
Then the deadline is calculated correctly
And overdue status is determined accurately
```

### Event-Driven Requirements

**EDR-001**: When a parent creates a task, the system shall assign it to specified children.

```
Given a valid task creation request
When processed
Then the task is created with all configuration
And assigned to the specified children
And appropriate notifications are triggered
```

**EDR-002**: When a child checks in a task, the system shall create a pending approval.

```
Given a child submits a check-in
When the check-in is processed
Then a check-in record is created with pending status
And the parent is notified
And the task status shows "awaiting_approval"
```

**EDR-003**: When a parent approves a check-in, the system shall award points.

```
Given a parent approves a check-in
When approval is processed
Then points are awarded to the child
And the check-in status changes to approved
And the child is notified
And any streak bonus is calculated and awarded
```

**EDR-004**: When a parent rejects a check-in, the system shall notify without points.

```
Given a parent rejects a check-in
When rejection is processed
Then no points are awarded
And the check-in status changes to rejected
And the child is notified with reason (if provided)
```

**EDR-005**: When a task deadline passes without check-in, the system shall mark it missed.

```
Given a task has a deadline
When the deadline passes without check-in
Then the task instance is marked as missed
And streak may be affected
```

### State-Driven Requirements

**SDR-001**: While a task is recurring, the system shall generate daily instances.

```
Given a daily/weekly task
When a new day begins
Then task instances are generated for applicable days
And each instance tracks its own completion state
```

**SDR-002**: While a check-in is pending, the system shall prevent duplicate check-ins.

```
Given a pending check-in exists
When a child tries to check in again
Then the request is rejected
And an appropriate error message is returned
```

### Optional Requirements

**OR-001**: The system MAY support task templates.

```
Given task templates exist
When a parent creates from template
Then the template values are pre-filled
And the parent can customize before saving
```

**OR-002**: The system MAY support photo proof requirements.

```
Given a task requires photo proof
When a child checks in
Then a photo must be attached
And the photo is stored and linked to the check-in
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT allow points to be awarded without approval.

```
Given any check-in
When the status is pending
Then no points are awarded
Until explicit parent approval
```

---

## Technical Solution

### API Endpoints

```yaml
# Task Management (Parent)
POST /api/v1/tasks
  Headers: Authorization: Bearer {token}
  Request: TaskCreateRequest
  Response: Task

GET /api/v1/tasks
  Headers: Authorization: Bearer {token}
  Query: assignee_id?, type?, status?, date?
  Response: [Task]

GET /api/v1/tasks/{task_id}
  Headers: Authorization: Bearer {token}
  Response: Task

PUT /api/v1/tasks/{task_id}
  Headers: Authorization: Bearer {token}
  Request: TaskUpdateRequest
  Response: Task

DELETE /api/v1/tasks/{task_id}
  Headers: Authorization: Bearer {token}
  Response: { success: true }

# Task Viewing (Child)
GET /api/v1/child/tasks
  Headers: Authorization: Bearer {token}
  Query: date?, status?
  Response: [TaskInstance]

GET /api/v1/child/tasks/{task_instance_id}
  Headers: Authorization: Bearer {token}
  Response: TaskInstance

# Check-in Flow
POST /api/v1/child/tasks/{task_instance_id}/checkin
  Headers: Authorization: Bearer {token}
  Request: { photo_url?, note? }
  Response: CheckIn

# Approval Flow (Parent)
GET /api/v1/approvals
  Headers: Authorization: Bearer {token}
  Response: [CheckIn]

POST /api/v1/approvals/{checkin_id}/approve
  Headers: Authorization: Bearer {token}
  Response: { points_awarded, check_in }

POST /api/v1/approvals/{checkin_id}/reject
  Headers: Authorization: Bearer {token}
  Request: { reason? }
  Response: { check_in }
```

### Data Models

```python
# models/task.py
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id"))
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None]
    points: Mapped[int] = mapped_column(SmallInteger)
    type: Mapped[str] = mapped_column(String(20))  # daily, weekly, one-time, family
    requires_photo: Mapped[bool] = mapped_column(default=False)
    streak_bonus: Mapped[int | None]  # Bonus points per streak day
    is_active: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("parents.id"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime]

class TaskConfig(Base):
    """Configuration for recurring tasks"""
    __tablename__ = "task_configs"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"))
    # For daily tasks
    deadline_time: Mapped[time | None]  # e.g., 18:00
    # For weekly tasks
    days_of_week: Mapped[list[int] | None]  # [0,1,2,3,4,5,6]

class TaskAssignment(Base):
    __tablename__ = "task_assignments"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"))
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    assigned_at: Mapped[datetime] = mapped_column(default=utcnow)

class TaskInstance(Base):
    """Generated instance for a specific date"""
    __tablename__ = "task_instances"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"))
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    date: Mapped[date]
    deadline: Mapped[datetime | None]
    status: Mapped[str]  # pending, awaiting_approval, approved, rejected, missed
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

class CheckIn(Base):
    __tablename__ = "check_ins"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    task_instance_id: Mapped[UUID] = mapped_column(ForeignKey("task_instances.id"))
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    photo_url: Mapped[str | None]
    note: Mapped[str | None]
    checked_in_at: Mapped[datetime] = mapped_column(default=utcnow)
    status: Mapped[str]  # pending, approved, rejected
    reviewed_by: Mapped[UUID | None]
    reviewed_at: Mapped[datetime | None]
    rejection_reason: Mapped[str | None]
    points_awarded: Mapped[int | None]
```

### Request/Response Models

```python
# schemas/task.py
class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    points: int = Field(..., ge=1, le=100)
    type: Literal["daily", "weekly", "one-time", "family"]
    assignee_ids: list[UUID]
    deadline_time: time | None = None
    days_of_week: list[int] | None = None  # 0-6
    requires_photo: bool = False
    streak_bonus: int | None = Field(None, ge=1, le=20)

class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    points: int
    type: str
    assignees: list[ChildBrief]
    deadline_time: time | None
    days_of_week: list[int] | None
    requires_photo: bool
    streak_bonus: int | None
    is_active: bool
    created_at: datetime

class TaskInstanceResponse(BaseModel):
    id: UUID
    task: TaskBrief
    date: date
    deadline: datetime | None
    status: str
    check_in: CheckInBrief | None
```

### Business Logic

```python
# services/task_service.py
class TaskService:
    async def create_task(self, family_id: UUID, data: TaskCreateRequest) -> Task:
        # Validate assignees belong to family
        # Create task
        # Create assignments
        # Create config if recurring
        # Generate instances if applicable
        # Send notifications
        pass

    async def check_in(self, task_instance_id: UUID, child_id: UUID,
                       photo_url: str | None, note: str | None) -> CheckIn:
        # Validate task instance is pending
        # Validate no existing pending check-in
        # Create check-in record
        # Update task instance status
        # Notify parent
        pass

    async def approve_check_in(self, check_in_id: UUID, parent_id: UUID) -> CheckIn:
        # Validate check-in is pending
        # Validate parent owns the task
        # Calculate points (base + streak bonus)
        # Award points via point service
        # Update check-in status
        # Notify child
        # Update streak if applicable
        pass
```

### Background Jobs

```python
# Background tasks
- generate_daily_task_instances: Run at midnight to create task instances
- mark_overdue_tasks: Run every 15 min to mark missed tasks
- cleanup_old_instances: Run daily to archive old task instances
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-BE-AUTH-001 | Upstream | Pending | Auth context |
| SPEC-BE-POINT-001 | Parallel | Pending | Point awarding |
| PostgreSQL | Database | Required | Data storage |
| Notification Service | Service | Required | Push notifications |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Duplicate check-ins | Medium | Medium | Unique constraint, idempotent API |
| Missed task detection | Low | Low | Background job with retry |
| Notification delivery | Medium | Low | Queue with retry logic |
| Timezone handling | Medium | Medium | Store in UTC, display in local |

---

## Acceptance Criteria

### Task CRUD
- [ ] Given valid data, when task created, then task and assignments exist
- [ ] Given task exists, when updated, then changes saved
- [ ] Given task exists, when deleted, then removed (soft delete)

### Task Assignment
- [ ] Given assignees specified, when task created, then all assigned
- [ ] Given assignee not in family, when task created, then rejected

### Check-in Flow
- [ ] Given pending task, when check-in submitted, then pending approval created
- [ ] Given photo required, when check-in without photo, then rejected
- [ ] Given existing pending check-in, when duplicate check-in, then rejected

### Approval Flow
- [ ] Given pending check-in, when approved, then points awarded
- [ ] Given pending check-in, when rejected, then no points
- [ ] Given streak active, when approved, then bonus calculated

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-TASK-001 | Upstream | Child task frontend |
| SPEC-FE-PARENT-001 | Upstream | Parent task management |
| SPEC-BE-POINT-001 | Downstream | Point awarding |
| SPEC-BE-REPORT-001 | Downstream | Task statistics |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
