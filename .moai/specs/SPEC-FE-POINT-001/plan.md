# SPEC-FE-POINT-001: Child Point System

## Overview

Implement the point balance and transaction history interface for the child-facing application.

**Business Context**: Points are the currency of BabyEco's incentive system. Children earn points from tasks and spend them on rewards. This module provides visibility into their point balance and history.

**Target Users**:
- Primary: Children aged 6-12 tracking their points
- Secondary: Parents monitoring point activity

---

## Technical Constraints

### Framework and Versions
- Next.js 22.x with App Router
- React 19.x
- Zustand for state management
- Framer Motion for animations
- Recharts for charts (optional)

### Dependencies
- SPEC-DESIGN-001 (Child App Design)
- SPEC-DESIGN-003 (Design System)
- SPEC-FE-AUTH-002 (Child Auth Module)
- SPEC-BE-POINT-001 (Backend Point API)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall display the current point balance prominently on the point overview screen.

```
Given a child is on the point overview screen
When the screen loads
Then their current point balance is displayed in large, animated numbers
And the balance updates with animation when changed
```

**UR-002**: The system shall display goal progress if a reward is pinned.

```
Given a child has pinned a reward goal
When they view the point overview
Then a progress bar shows progress toward the goal
And current points vs required points are displayed
```

**UR-003**: The system shall display transaction history with color-coded entries.

```
Given a child has point transactions
When they view the history list
Then earning transactions are green (+)
And spending transactions are red (-)
And frozen points are blue (pending exchange)
```

### Event-Driven Requirements

**EDR-001**: When points are earned, the system shall animate the balance increase.

```
Given a child earns points
When the transaction completes
Then the balance animates upward
And a "+X" indicator floats up and fades
And optional sound effect plays
```

**EDR-002**: When points are spent, the system shall animate the balance decrease.

```
Given a child spends points
When the exchange completes
Then the balance animates downward
And a "-X" indicator shows
```

**EDR-003**: When a transaction is tapped, the system shall show transaction details.

```
Given a child views their transaction history
When they tap a transaction entry
Then a detail modal opens
And shows date, time, type, and related item/task
```

**EDR-004**: When the point history is scrolled, the system shall load more entries (pagination).

```
Given a child has many transactions
When they scroll to the bottom of the list
Then more transactions are loaded
And a loading indicator shows while fetching
```

### State-Driven Requirements

**SDR-001**: While points are loading, the system shall display a skeleton.

```
Given a child opens the point overview
When points are being fetched
Then a skeleton placeholder shows
And the actual balance animates in when loaded
```

**SDR-002**: While the balance is insufficient for a pinned goal, the system shall show progress percentage.

```
Given a child has pinned a goal
When current points < required points
Then the progress bar shows percentage complete
And the remaining points needed are displayed
```

**SDR-003**: While the balance is sufficient for a pinned goal, the system shall highlight "Ready to redeem".

```
Given a child has pinned a goal
When current points >= required points
Then "Ready to redeem!" is prominently displayed
And the progress bar shows 100%
And a CTA to redeem is highlighted
```

### Optional Requirements

**OR-001**: The system MAY display weekly/monthly earning summaries.

```
Given a child views point overview
When they scroll down
Then summary cards show "This week" and "This month" totals
And comparison to previous period is shown
```

**OR-002**: The system MAY display a mini chart of earning trends.

```
Given a child has point history
When viewing point overview
Then a simple line chart shows 7-day earning trend
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT allow negative point balances.

```
Given a child tries to spend points
When the cost exceeds their balance
Then the action is blocked
And "Not enough points!" message shows
```

**UBR-002**: The system shall NOT show other children's point balances.

```
Given multiple children in a family
When a child views their points
Then only their own balance is visible
And siblings' balances are not accessible
```

---

## Technical Solution

### Component Structure

```
src/
├── app/
│   └── (child)/
│       └── (authenticated)/
│           └── points/
│               ├── page.tsx
│               └── [transactionId]/
│                   └── page.tsx
├── components/
│   ├── points/
│   │   ├── PointBalance.tsx
│   │   ├── GoalProgress.tsx
│   │   ├── TransactionList.tsx
│   │   ├── TransactionCard.tsx
│   │   ├── TransactionDetail.tsx
│   │   ├── PointSummary.tsx
│   │   ├── EarningTrend.tsx
│   │   └── BalanceAnimation.tsx
│   └── ui/
│       └── (design system components)
├── lib/
│   ├── points/
│   │   ├── point-client.ts
│   │   ├── point-utils.ts
│   │   └── point-animations.ts
│   └── hooks/
│       ├── usePoints.ts
│       ├── useTransactions.ts
│       └── usePointGoal.ts
└── stores/
    └── point-store.ts
```

### Point Balance Component

```tsx
// PointBalance.tsx
interface PointBalanceProps {
  balance: number;
  animateOnChange?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

// Behavior:
// - Large, prominent number display
// - Animated counting effect on value change
// - Sparkle/shine effect on significant gains
// - Subtle glow effect
```

### Transaction Card Component

```tsx
// TransactionCard.tsx
interface TransactionCardProps {
  transaction: Transaction;
  onPress: () => void;
}

interface Transaction {
  id: string;
  type: 'earn' | 'spend' | 'frozen' | 'unfrozen';
  amount: number;
  description: string;
  relatedId?: string; // Task ID or Exchange ID
  relatedType?: 'task' | 'exchange';
  timestamp: Date;
}

// Color coding:
// earn: Green (#95E1A3), + prefix
// spend: Red (#FF8B94), - prefix
// frozen: Blue (#4ECDC4), pause icon
// unfrozen: Blue (#4ECDC4), + prefix
```

### State Management

```typescript
// point-store.ts
interface PointState {
  balance: number;
  goal: PinnedGoal | null;
  transactions: Transaction[];
  summary: PointSummary | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchBalance: () => Promise<void>;
  fetchTransactions: (page?: number) => Promise<void>;
  fetchSummary: () => Promise<void>;
  updateBalance: (newBalance: number) => void; // Called from external events
}

interface PinnedGoal {
  rewardId: string;
  rewardName: string;
  rewardImage?: string;
  requiredPoints: number;
}

interface PointSummary {
  earnedThisWeek: number;
  spentThisWeek: number;
  earnedThisMonth: number;
  spentThisMonth: number;
  weekOverWeekChange: number;
}
```

### Balance Animation

```typescript
// point-animations.ts
export const balanceAnimations = {
  // Count up/down animation
  countChange: {
    duration: 500,
    easing: 'easeOut',
  },

  // Float up indicator
  floatIndicator: {
    initial: { opacity: 1, y: 0, scale: 1 },
    animate: { opacity: 0, y: -40, scale: 1.2 },
    duration: 1000,
  },

  // Sparkle effect for large gains
  sparkle: {
    count: 8,
    spread: 60,
    colors: ['#FFE66D', '#FF6B6B', '#4ECDC4'],
  },

  // Pulse effect
  pulse: {
    scale: [1, 1.05, 1],
    duration: 300,
  },
};
```

### Real-time Balance Updates

```typescript
// Listen for balance changes from other parts of the app
// (task completion, exchange, etc.)

export function usePointSync() {
  const { updateBalance, fetchBalance } = usePointStore();

  useEffect(() => {
    // Subscribe to point change events
    const unsubscribe = eventBus.subscribe('points:changed', (newBalance) => {
      updateBalance(newBalance);
    });

    // Also poll periodically as backup
    const interval = setInterval(fetchBalance, 60000); // 1 minute

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, []);
}
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-DESIGN-001 | Design | Completed | Point UI designs |
| SPEC-DESIGN-003 | Design | Completed | Design system |
| SPEC-FE-AUTH-002 | Auth | Pending | Child session |
| SPEC-BE-POINT-001 | API | Pending | Point endpoints |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Balance sync issues | High | Medium | Optimistic updates + server reconciliation |
| Animation performance | Low | Low | Reduce motion option, optimize animations |
| Long transaction lists | Medium | Low | Pagination, virtualization |

---

## Acceptance Criteria

### Balance Display
- [ ] Given valid session, when page loads, then balance displays correctly
- [ ] Given balance change, when updated, then animation plays
- [ ] Given pinned goal, when viewing, then progress shows

### Transaction History
- [ ] Given transactions exist, when list loads, then all entries show
- [ ] Given transaction tapped, when opened, then detail modal shows
- [ ] Given many transactions, when scrolling, then pagination works

### Visual Feedback
- [ ] Given points earned, when added, then positive animation plays
- [ ] Given points spent, when deducted, then negative animation shows
- [ ] Given goal reached, when met, then celebration shows

### Edge Cases
- [ ] Given no transactions, when list viewed, then empty state shows
- [ ] Given fetch error, when occurs, then error state with retry shows

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-TASK-001 | Upstream | Earns points from tasks |
| SPEC-FE-EXCHANGE-001 | Upstream/Downstream | Spends points on rewards |
| SPEC-BE-POINT-001 | Parallel | Backend point API |
| SPEC-FE-GROWTH-001 | Downstream | Uses point history for reports |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
