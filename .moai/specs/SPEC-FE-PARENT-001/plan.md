# SPEC-FE-PARENT-001: Parent Core Features

## Overview

Implement the core management features for the parent-facing application, including dashboard, task management, reward configuration, and approval queue.

**Business Context**: Parents need comprehensive tools to manage their family's behavioral incentive system. This module provides the control center for all parent operations.

**Target Users**:
- Primary: Parents managing family accounts
- Secondary: Guardians, caregivers

---

## Technical Constraints

### Framework and Versions
- Next.js 22.x with App Router
- React 19.x
- Zustand for state management
- React Query for data fetching
- Recharts for analytics charts

### Dependencies
- SPEC-DESIGN-002 (Parent App Design)
- SPEC-DESIGN-003 (Design System)
- SPEC-FE-AUTH-001 (Parent Auth Module)
- SPEC-BE-TASK-001 (Backend Task API)
- SPEC-BE-POINT-001 (Backend Point API)
- SPEC-BE-EXCHANGE-001 (Backend Exchange API)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall display a dashboard with family overview.

```
Given a parent logs in
When the dashboard loads
Then all children are displayed with quick stats
And pending approvals count is shown
And quick action buttons are visible
```

**UR-002**: The system shall display pending approvals prominently.

```
Given there are pending check-ins
When the parent views the dashboard
Then pending approvals are listed with quick approve/reject actions
And each item shows child name, task, and timestamp
```

**UR-003**: The system shall organize tasks by assignment and type.

```
Given a parent views task management
When the task list loads
Then tasks are grouped by type (Daily, Weekly, etc.)
And filter by child assignment is available
```

### Event-Driven Requirements

**EDR-001**: When a parent approves a check-in, the system shall award points and notify the child.

```
Given a parent reviews a pending check-in
When they tap "Approve"
Then points are awarded to the child
And a notification is sent to the child's device
And the item is removed from pending queue
```

**EDR-002**: When a parent rejects a check-in, the system shall notify the child without points.

```
Given a parent reviews a pending check-in
When they tap "Reject"
Then no points are awarded
And an optional reason can be provided
And the child is notified
```

**EDR-003**: When a parent creates a task, the system shall assign it to selected children.

```
Given a parent fills the task creation form
When they save the task
Then the task is created and assigned
And it appears in assigned children's task lists
```

**EDR-004**: When a parent creates a reward, the system shall add it to the exchange center.

```
Given a parent configures a reward
When they save it
Then the reward appears in the exchange center
And is visible to assigned children
```

**EDR-005**: When a parent adjusts a child's points, the system shall log the adjustment.

```
Given a parent manually adjusts points
When the adjustment is saved
Then the child's balance is updated
And an audit log entry is created
And the child is notified
```

### State-Driven Requirements

**SDR-001**: While there are no pending approvals, the system shall show empty state.

```
Given no pending check-ins exist
When parent views dashboard
Then "All caught up!" empty state is displayed
And quick actions remain accessible
```

**SDR-002**: While a child has an active timer, the system shall show timer status.

```
Given a child has redeemed a timer reward
When parent views child detail
Then the active timer status is displayed
And remaining time is visible
```

**SDR-003**: While data is loading, the system shall show skeleton states.

```
Given data is being fetched
When parent views any screen
Then appropriate skeleton components are shown
And content animates in when loaded
```

### Optional Requirements

**OR-001**: The system MAY support batch approval of check-ins.

```
Given multiple pending approvals
When parent selects multiple items
Then a "Approve All" action is available
And confirms before batch processing
```

**OR-002**: The system MAY support auto-approval after time threshold.

```
Given auto-approval is configured
When a check-in is pending longer than threshold
Then it is automatically approved
And parent is notified of auto-approval
```

**OR-003**: The system MAY support task templates.

```
Given parent wants to create similar tasks
When they use a template
Then pre-filled task form opens
And they can customize before saving
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT allow assigning tasks to children not in the family.

```
Given a parent creates a task
When they select assignees
Then only their own children are listed
And other family's children are not accessible
```

**UBR-002**: The system shall NOT allow negative point adjustments below zero.

```
Given a parent adjusts points
When they try to deduct more than balance
Then the action is blocked
And an error message is shown
```

---

## Technical Solution

### Component Structure

```
src/
├── app/
│   └── (parent)/
│       └── (authenticated)/
│           ├── dashboard/
│           │   └── page.tsx
│           ├── tasks/
│           │   ├── page.tsx
│           │   ├── new/
│           │   │   └── page.tsx
│           │   └── [taskId]/
│           │       └── page.tsx
│           ├── rewards/
│           │   ├── page.tsx
│           │   ├── new/
│           │   │   └── page.tsx
│           │   └── [rewardId]/
│           │       └── page.tsx
│           ├── approvals/
│           │   └── page.tsx
│           └── children/
│               └── [childId]/
│                   └── page.tsx
├── components/
│   ├── parent/
│   │   ├── Dashboard.tsx
│   │   ├── ChildOverviewCard.tsx
│   │   ├── PendingApprovals.tsx
│   │   ├── ApprovalCard.tsx
│   │   ├── QuickActions.tsx
│   │   ├── TaskManager.tsx
│   │   ├── TaskForm.tsx
│   │   ├── RewardManager.tsx
│   │   ├── RewardForm.tsx
│   │   ├── ChildDetail.tsx
│   │   ├── PointAdjustment.tsx
│   │   └── FamilySettings.tsx
│   └── ui/
│       └── (design system components)
├── lib/
│   ├── parent/
│   │   ├── parent-client.ts
│   │   ├── task-config.ts
│   │   └── reward-config.ts
│   └── hooks/
│       ├── useApprovals.ts
│       ├── useTaskManagement.ts
│       ├── useRewardManagement.ts
│       └── useChildManagement.ts
└── stores/
    └── parent-store.ts
```

### Dashboard Component

```tsx
// Dashboard.tsx
interface DashboardProps {
  family: Family;
  children: Child[];
  pendingApprovals: Approval[];
}

// Sections:
// 1. Header with family name
// 2. Pending approvals queue (top priority)
// 3. Children overview cards (grid)
// 4. Quick actions toolbar
// 5. Recent activity feed (optional)
```

### Task Form Component

```tsx
// TaskForm.tsx
interface TaskFormProps {
  task?: Task; // For editing
  children: Child[];
  onSave: (task: TaskData) => Promise<void>;
  onCancel: () => void;
}

interface TaskData {
  title: string;
  description?: string;
  points: number;
  type: 'daily' | 'weekly' | 'one-time' | 'family';
  assigneeIds: string[];
  timeWindow?: {
    enabled: boolean;
    deadline?: string; // HH:MM format
    days?: number[]; // 0-6 for weekly
  };
  requiresPhoto: boolean;
  streakBonus?: number;
}

// Form fields:
// - Title input (required)
// - Description textarea
// - Points slider (1-100)
// - Type selector
// - Assignee multi-select
// - Time window configuration
// - Photo proof toggle
// - Streak bonus input (optional)
```

### Reward Form Component

```tsx
// RewardForm.tsx
interface RewardFormProps {
  reward?: Reward; // For editing
  onSave: (reward: RewardData) => Promise<void>;
  onCancel: () => void;
}

interface RewardData {
  name: string;
  description?: string;
  imageUrl?: string;
  type: 'one-time' | 'timer' | 'quantity';
  cost: number;
  duration?: number; // Minutes for timer type
  stock?: number; // For quantity type
  enabled: boolean;
}

// Form fields:
// - Name input (required)
// - Description textarea
// - Image upload
// - Type selector
// - Cost input
// - Duration input (timer type)
// - Stock input (quantity type)
// - Enable/Disable toggle
```

### State Management

```typescript
// parent-store.ts
interface ParentState {
  family: Family | null;
  children: Child[];
  tasks: Task[];
  rewards: Reward[];
  pendingApprovals: Approval[];
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchDashboard: () => Promise<void>;
  approveCheckIn: (checkInId: string) => Promise<void>;
  rejectCheckIn: (checkInId: string, reason?: string) => Promise<void>;
  createTask: (task: TaskData) => Promise<void>;
  updateTask: (taskId: string, task: TaskData) => Promise<void>;
  deleteTask: (taskId: string) => Promise<void>;
  createReward: (reward: RewardData) => Promise<void>;
  updateReward: (rewardId: string, reward: RewardData) => Promise<void>;
  deleteReward: (rewardId: string) => Promise<void>;
  adjustChildPoints: (childId: string, amount: number, reason: string) => Promise<void>;
}
```

### Real-time Updates

```typescript
// Listen for new check-ins requiring approval
export function useApprovalNotifications() {
  const { addApproval } = useParentStore();

  useEffect(() => {
    // Option 1: WebSocket for instant notifications
    // Option 2: Polling every 30 seconds
    // MVP: Polling

    const pollApprovals = async () => {
      const newApprovals = await fetchPendingApprovals();
      // Compare with current state and update
    };

    const interval = setInterval(pollApprovals, 30000);
    return () => clearInterval(interval);
  }, []);
}
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-DESIGN-002 | Design | Completed | Parent app UI |
| SPEC-DESIGN-003 | Design | Completed | Design system |
| SPEC-FE-AUTH-001 | Auth | Pending | Parent session |
| SPEC-BE-TASK-001 | API | Pending | Task endpoints |
| SPEC-BE-EXCHANGE-001 | API | Pending | Reward endpoints |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Approval bottleneck | High | Medium | Auto-approval, batch actions |
| Configuration complexity | Medium | Medium | Progressive disclosure, templates |
| Data consistency | High | Low | Optimistic updates with rollback |
| Notification delivery | Medium | Low | Multiple channels |

---

## Acceptance Criteria

### Dashboard
- [ ] Given valid session, when dashboard loads, then all sections display
- [ ] Given pending approvals, when viewing, then queue shows all items
- [ ] Given children exist, when viewing, then overview cards show

### Approval Flow
- [ ] Given pending item, when approved, then child receives points
- [ ] Given pending item, when rejected, then child notified
- [ ] Given batch selection, when approved all, then all processed

### Task Management
- [ ] Given task form, when saved, then task created and assigned
- [ ] Given task exists, when edited, then changes saved
- [ ] Given task exists, when deleted, then removed from all lists

### Reward Management
- [ ] Given reward form, when saved, then reward added to exchange
- [ ] Given reward exists, when disabled, then hidden from children
- [ ] Given timer reward, when created, then duration configurable

### Child Management
- [ ] Given child selected, when points adjusted, then balance updates
- [ ] Given child detail viewed, when stats shown, then accurate data

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-AUTH-001 | Upstream | Parent authentication |
| SPEC-FE-TASK-001 | Downstream | Child task display |
| SPEC-FE-EXCHANGE-001 | Downstream | Child reward display |
| SPEC-BE-TASK-001 | Parallel | Backend task API |
| SPEC-BE-EXCHANGE-001 | Parallel | Backend reward API |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
