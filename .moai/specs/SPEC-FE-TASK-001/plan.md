# SPEC-FE-TASK-001: Child Task System

## Overview

Implement the task management and completion interface for the child-facing application, including task list, detail view, and check-in functionality.

**Business Context**: The task system is the core of BabyEco's behavioral incentive economy. Children view assigned tasks, mark them complete, and earn points upon parent approval.

**Target Users**:
- Primary: Children aged 6-12 completing tasks
- Secondary: Parents assigning and approving tasks

---

## Technical Constraints

### Framework and Versions
- Next.js 22.x with App Router
- React 19.x
- Zustand for state management
- React Query for data fetching
- Framer Motion / GSAP for animations

### Dependencies
- SPEC-DESIGN-001 (Child App Design)
- SPEC-DESIGN-003 (Design System)
- SPEC-FE-AUTH-002 (Child Auth Module)
- SPEC-BE-TASK-001 (Backend Task API)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall display today's tasks on the home dashboard.

```
Given a child is on the home dashboard
When the screen loads
Then their assigned tasks for today are displayed
And each task shows title, points, and completion status
```

**UR-002**: The system shall categorize tasks by type (Daily, Weekly, One-time, Family).

```
Given a child views their task list
When the list is displayed
Then tasks are grouped by category
And filter pills allow filtering by type
```

**UR-003**: The system shall display time windows for time-sensitive tasks.

```
Given a task has a time window
When the task card is displayed
Then the deadline time is shown (e.g., "Do by 6:00 PM")
And the task is highlighted when approaching deadline
```

### Event-Driven Requirements

**EDR-001**: When a child taps "I Did It!" on a task, the system shall prompt for confirmation.

```
Given a child views a pending task
When they tap "I Did It!"
Then a confirmation modal appears
And the modal shows task name and points to earn
```

**EDR-002**: When a child confirms task completion, the system shall submit a check-in request.

```
Given a child has confirmed task completion
When the check-in is submitted
Then the task status changes to "Awaiting Approval"
And the parent is notified
And a celebration animation plays
```

**EDR-003**: When a task requires photo proof, the system shall prompt for camera access.

```
Given a task requires photo verification
When the child taps "I Did It!"
Then a camera interface opens
And they can capture a photo
And attach it to the check-in
```

**EDR-004**: When a task is approved, the system shall update points and show celebration.

```
Given a child has a pending approval
When the parent approves the check-in
Then the child sees a point gain animation
And the task shows "Completed" status
And the celebration animation plays
```

**EDR-005**: When a task deadline passes without completion, the system shall mark it as missed.

```
Given a task has a deadline
When the deadline passes without check-in
Then the task shows "Missed" status
And the task is visually distinguished (red accent)
```

### State-Driven Requirements

**SDR-001**: While tasks are loading, the system shall display skeleton cards.

```
Given a child opens the task list
When tasks are being fetched
Then skeleton cards are displayed
And a subtle loading animation plays
```

**SDR-002**: While a task is awaiting approval, the system shall display "Waiting for parent" status.

```
Given a child has checked in on a task
When the check-in is pending approval
Then the task card shows "Waiting for parent" badge
And the check-in button is disabled
```

**SDR-003**: While there are no tasks assigned, the system shall display an empty state.

```
Given a child has no tasks assigned
When they view the task list
Then a friendly empty state is shown
And a message like "No tasks yet! Ask your parent to add some." displays
```

### Optional Requirements

**OR-001**: The system MAY allow children to add notes to check-ins.

```
Given a child is checking in a task
When they want to add details
Then a text input is available for notes
And the note is attached to the check-in
```

**OR-002**: The system MAY support streak bonuses display.

```
Given a recurring task has a streak
When the child views the task
Then the current streak is displayed
And bonus points for streak are shown
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT allow check-ins on already completed tasks.

```
Given a task is already completed
When the child views the task
Then the check-in button is not visible
And "Done!" badge is shown instead
```

**UBR-002**: The system shall NOT allow check-ins after the deadline has passed.

```
Given a task deadline has passed
When the child views the task
Then the check-in button is disabled
And "Missed" status is shown
```

**UBR-003**: The system shall NOT show tasks assigned to other children.

```
Given multiple children in a family
When a child views their task list
Then only their assigned tasks are visible
And siblings' tasks are not shown
```

---

## Technical Solution

### Component Structure

```
src/
├── app/
│   └── (child)/
│       └── (authenticated)/
│           ├── tasks/
│           │   ├── page.tsx
│           │   └── [taskId]/
│           │       └── page.tsx
│           └── components/
│               └── TaskCard.tsx
├── components/
│   ├── tasks/
│   │   ├── TaskList.tsx
│   │   ├── TaskCard.tsx
│   │   ├── TaskDetail.tsx
│   │   ├── TaskFilters.tsx
│   │   ├── CheckInButton.tsx
│   │   ├── CheckInModal.tsx
│   │   ├── PhotoCapture.tsx
│   │   ├── TaskCelebration.tsx
│   │   ├── TaskStatusBadge.tsx
│   │   └── EmptyTaskState.tsx
│   └── ui/
│       └── (design system components)
├── lib/
│   ├── tasks/
│   │   ├── task-client.ts
│   │   ├── task-utils.ts
│   │   └── task-animations.ts
│   └── hooks/
│       ├── useTasks.ts
│       ├── useTaskDetail.ts
│       └── useCheckIn.ts
└── stores/
    └── task-store.ts
```

### Task Card Component

```tsx
// TaskCard.tsx
interface TaskCardProps {
  task: Task;
  onCheckIn: (task: Task) => void;
  onViewDetail: (task: Task) => void;
}

interface Task {
  id: string;
  title: string;
  description?: string;
  points: number;
  type: 'daily' | 'weekly' | 'one-time' | 'family';
  status: 'pending' | 'awaiting_approval' | 'approved' | 'rejected' | 'missed';
  deadline?: Date;
  requiresPhoto: boolean;
  streak?: number;
}

// Visual states:
// - pending: Full color, check-in button visible
// - awaiting_approval: Yellow accent, "Waiting for parent" badge
// - approved: Green accent, "Done!" badge
// - rejected: Gray, can retry
// - missed: Red accent, "Missed" badge
```

### State Management

```typescript
// task-store.ts
interface TaskState {
  tasks: Task[];
  isLoading: boolean;
  error: string | null;
  selectedFilter: TaskFilter;

  // Actions
  fetchTasks: () => Promise<void>;
  checkIn: (taskId: string, photo?: string, note?: string) => Promise<void>;
  setFilter: (filter: TaskFilter) => void;
}

type TaskFilter = 'all' | 'daily' | 'weekly' | 'one-time' | 'family';
```

### Check-in Flow

```typescript
// useCheckIn.ts
export function useCheckIn() {
  const checkIn = async (taskId: string, options: CheckInOptions) => {
    // 1. Show confirmation modal
    // 2. If photo required, capture photo
    // 3. Submit to API
    // 4. On success:
    //    - Play celebration animation
    //    - Update local state optimistically
    //    - Show success toast
    // 5. On error:
    //    - Revert optimistic update
    //    - Show error message
  };

  return { checkIn, isCheckingIn };
}
```

### Animation Specifications

```typescript
// task-animations.ts
export const taskAnimations = {
  // Card entrance
  cardEnter: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, x: -100 },
  },

  // Check-in celebration
  celebration: {
    confetti: {
      particleCount: 50,
      spread: 70,
      origin: { y: 0.6 },
    },
    pointAnimation: {
      initial: { opacity: 1, y: 0, scale: 1 },
      animate: { opacity: 0, y: -50, scale: 1.5 },
      duration: 1000,
    },
  },

  // Status change
  statusChange: {
    duration: 300,
    easing: 'ease-out',
  },
};
```

### Real-time Updates

```typescript
// Task updates via WebSocket or polling
// Option 1: WebSocket for real-time approval notifications
// Option 2: Polling every 30 seconds
// MVP: Use polling for simplicity

export function useTaskUpdates() {
  useEffect(() => {
    const interval = setInterval(() => {
      refetchTasks();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, []);
}
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-DESIGN-001 | Design | Completed | Task card designs |
| SPEC-DESIGN-003 | Design | Completed | Design system |
| SPEC-FE-AUTH-002 | Auth | Pending | Child session |
| SPEC-BE-TASK-001 | API | Pending | Task endpoints |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Check-in without doing task | Medium | High | Parent approval gate |
| Task list performance | Low | Low | Pagination, virtualization |
| Animation lag on older devices | Medium | Medium | Reduce motion option |
| Photo upload failures | Medium | Medium | Retry logic, local caching |

---

## Acceptance Criteria

### Task Display
- [ ] Given tasks exist, when list loads, then all tasks display correctly
- [ ] Given filter selected, when applied, then only filtered tasks show
- [ ] Given time-sensitive task, when displayed, then deadline shows

### Check-in Flow
- [ ] Given pending task, when "I Did It!" tapped, then confirmation modal shows
- [ ] Given confirmation, when submitted, then status changes to awaiting
- [ ] Given photo required, when check-in, then camera interface opens

### Status Updates
- [ ] Given approval received, when task updates, then celebration plays
- [ ] Given deadline passed, when task viewed, then missed status shows

### Empty/Error States
- [ ] Given no tasks, when list viewed, then empty state shows
- [ ] Given fetch error, when occurs, then error state with retry shows

### Accessibility
- [ ] All task cards are keyboard accessible
- [ ] Status changes are announced
- [ ] Animations respect prefers-reduced-motion

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-DESIGN-001 | Upstream | UI design reference |
| SPEC-FE-AUTH-002 | Upstream | Child authentication |
| SPEC-FE-POINT-001 | Downstream | Points awarded from tasks |
| SPEC-BE-TASK-001 | Parallel | Backend task API |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
