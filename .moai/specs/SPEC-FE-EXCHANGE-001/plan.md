# SPEC-FE-EXCHANGE-001: Child Exchange Center

## Overview

Implement the reward browsing and redemption interface for the child-facing application.

**Business Context**: The Exchange Center is where children spend their earned points on rewards configured by parents. This is the core "spending" side of the incentive economy.

**Target Users**:
- Primary: Children aged 6-12 redeeming rewards
- Secondary: Parents configuring available rewards

---

## Technical Constraints

### Framework and Versions
- Next.js 22.x with App Router
- React 19.x
- Zustand for state management
- Framer Motion for animations
- Timer/Countdown components

### Dependencies
- SPEC-DESIGN-001 (Child App Design)
- SPEC-DESIGN-003 (Design System)
- SPEC-FE-AUTH-002 (Child Auth Module)
- SPEC-FE-POINT-001 (Point System)
- SPEC-BE-EXCHANGE-001 (Backend Exchange API)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall display available rewards in a grid layout.

```
Given a child opens the Exchange Center
When the screen loads
Then available rewards are displayed in a card grid
And each card shows image, name, and point cost
```

**UR-002**: The system shall display the pinned goal prominently at the top.

```
Given a child has pinned a reward
When they view the Exchange Center
Then their pinned goal appears at the top
And a progress bar shows completion percentage
```

**UR-003**: The system shall display point balance in the header.

```
Given a child is in the Exchange Center
When they look at the header
Then their current point balance is visible
And they can see if they have enough for items
```

### Event-Driven Requirements

**EDR-001**: When a child pins a reward as goal, the system shall update the pinned display.

```
Given a child views a reward
When they tap "Pin as Goal"
Then the reward appears in the pinned section
And the previous goal (if any) is replaced
And a confirmation animation plays
```

**EDR-002**: When a child redeems a one-time reward, the system shall deduct points and show confirmation.

```
Given a child has enough points for a one-time reward
When they tap "Redeem" and confirm
Then points are deducted
And a success confirmation shows
And parent is notified of the redemption
```

**EDR-003**: When a child redeems a timer-based reward, the system shall start a countdown timer.

```
Given a child has enough points for a timer reward
When they tap "Start Timer" and confirm
Then points are deducted
And a countdown timer begins
And the timer is visible in the UI
```

**EDR-004**: When a timer expires, the system shall notify the child and parent.

```
Given a timer reward is active
When the timer reaches zero
Then an alert plays (sound + visual)
And the activity should end
And parent is notified
```

**EDR-005**: When a reward is out of stock, the system shall show "Out of Stock" status.

```
Given a quantity-based reward has no stock
When the child views the reward
Then "Out of Stock" badge is displayed
And the redeem button is disabled
```

### State-Driven Requirements

**SDR-001**: While points are insufficient, the system shall disable redeem and show deficit.

```
Given a child views a reward they can't afford
When the cost > balance
Then the redeem button is disabled or shows "X more points needed"
And the card has a subtle gray overlay
```

**SDR-002**: While a timer is active, the system shall display the remaining time.

```
Given a timer reward is in progress
When the child views the Exchange Center
Then the active timer is prominently displayed
And shows HH:MM:SS remaining
And can be expanded to full-screen timer
```

**SDR-003**: While rewards are loading, the system shall display skeleton cards.

```
Given a child opens the Exchange Center
When rewards are being fetched
Then skeleton cards are displayed in a grid
And animate to real cards when loaded
```

### Optional Requirements

**OR-001**: The system MAY support a wishlist for unavailable rewards.

```
Given a reward is out of stock or too expensive
When the child taps "Add to Wishlist"
Then the reward is added to their wishlist
And parent can see wishlist items
```

**OR-002**: The system MAY show a preview of redemption confirmation.

```
Given a child is about to redeem
When they tap redeem
Then a preview card shows what they'll get
And the point deduction is clearly shown
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT allow redemption with insufficient points.

```
Given a child tries to redeem without enough points
When they attempt the action
Then the action is blocked
And "Not enough points" message shows
```

**UBR-002**: The system shall NOT allow multiple simultaneous timers.

```
Given a timer is already running
When the child tries to start another
Then the action is blocked
And "Finish your current activity first" message shows
```

---

## Technical Solution

### Component Structure

```
src/
├── app/
│   └── (child)/
│       └── (authenticated)/
│           └── exchange/
│               ├── page.tsx
│               └── timer/
│                   └── page.tsx
├── components/
│   ├── exchange/
│   │   ├── ExchangeCenter.tsx
│   │   ├── PinnedGoal.tsx
│   │   ├── RewardGrid.tsx
│   │   ├── RewardCard.tsx
│   │   ├── RewardDetail.tsx
│   │   ├── RedeemModal.tsx
│   │   ├── TimerDisplay.tsx
│   │   ├── TimerFullscreen.tsx
│   │   ├── TimerAlert.tsx
│   │   ├── WishlistSection.tsx
│   │   └── InsufficientPoints.tsx
│   └── ui/
│       └── (design system components)
├── lib/
│   ├── exchange/
│   │   ├── exchange-client.ts
│   │   ├── timer-utils.ts
│   │   └── exchange-animations.ts
│   └── hooks/
│       ├── useRewards.ts
│       ├── useRedemption.ts
│       ├── useTimer.ts
│       └── useWishlist.ts
└── stores/
    └── exchange-store.ts
```

### Reward Card Component

```tsx
// RewardCard.tsx
interface RewardCardProps {
  reward: Reward;
  balance: number;
  onPin: () => void;
  onRedeem: () => void;
  onViewDetail: () => void;
}

interface Reward {
  id: string;
  name: string;
  description?: string;
  imageUrl?: string;
  type: 'one-time' | 'timer' | 'quantity';
  cost: number;
  duration?: number; // For timer type (minutes)
  stock?: number; // For quantity type
  isPinned: boolean;
}

// Card states:
// - Affordable: Full color, redeem button active
// - Unaffordable: Muted, "X more points" shown
// - Out of stock: Disabled, stock indicator
// - Pinned: Highlighted border, star icon
```

### Timer Component

```tsx
// TimerDisplay.tsx
interface TimerDisplayProps {
  duration: number; // Total minutes
  remaining: number; // Remaining seconds
  isPaused: boolean;
  onPause: () => void;
  onResume: () => void;
  onExpand: () => void;
}

// Features:
// - HH:MM:SS display
// - Circular progress indicator
// - Pause/Resume controls
// - Fullscreen expand
// - Warning colors at 5 min, 1 min remaining
```

### State Management

```typescript
// exchange-store.ts
interface ExchangeState {
  rewards: Reward[];
  pinnedGoal: PinnedGoal | null;
  activeTimer: ActiveTimer | null;
  wishlist: string[]; // Reward IDs
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchRewards: () => Promise<void>;
  pinReward: (rewardId: string) => Promise<void>;
  redeemReward: (rewardId: string) => Promise<void>;
  startTimer: (rewardId: string) => Promise<void>;
  pauseTimer: () => void;
  resumeTimer: () => void;
  addToWishlist: (rewardId: string) => void;
  removeFromWishlist: (rewardId: string) => void;
}

interface ActiveTimer {
  rewardId: string;
  rewardName: string;
  duration: number; // Total seconds
  remaining: number; // Remaining seconds
  startedAt: Date;
  isPaused: boolean;
}
```

### Timer Logic

```typescript
// timer-utils.ts
export function useTimerManager() {
  const [activeTimer, setActiveTimer] = useState<ActiveTimer | null>(null);

  // Persist timer state to localStorage for recovery
  useEffect(() => {
    if (activeTimer) {
      localStorage.setItem('activeTimer', JSON.stringify(activeTimer));
    } else {
      localStorage.removeItem('activeTimer');
    }
  }, [activeTimer]);

  // Countdown tick
  useEffect(() => {
    if (!activeTimer || activeTimer.isPaused) return;

    const interval = setInterval(() => {
      setActiveTimer((prev) => {
        if (!prev || prev.remaining <= 1) {
          handleTimerComplete();
          return null;
        }
        return { ...prev, remaining: prev.remaining - 1 };
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [activeTimer?.isPaused]);

  const handleTimerComplete = () => {
    // Play alert
    // Notify parent
    // Show completion screen
  };

  return { activeTimer, startTimer, pauseTimer, resumeTimer };
}
```

### Redemption Flow

```typescript
// useRedemption.ts
export function useRedemption() {
  const redeem = async (reward: Reward) => {
    // 1. Show confirmation modal
    // 2. On confirm:
    //    a. Check balance again
    //    b. Call API to redeem
    //    c. On success:
    //       - Update local balance
    //       - If timer: start timer
    //       - If quantity: decrement stock
    //       - Show success celebration
    //    d. On error:
    //       - Show error message
    //       - Allow retry
  };

  return { redeem, isRedeeming };
}
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-DESIGN-001 | Design | Completed | Exchange UI designs |
| SPEC-DESIGN-003 | Design | Completed | Design system |
| SPEC-FE-POINT-001 | Upstream | Pending | Point balance |
| SPEC-BE-EXCHANGE-001 | API | Pending | Exchange endpoints |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Timer tampering | Medium | Medium | Server-side validation, secure timer |
| Race conditions on stock | Medium | Low | Optimistic locking on backend |
| Timer state loss on refresh | High | Medium | LocalStorage persistence |
| Notification delivery | Medium | Low | Multiple notification channels |

---

## Acceptance Criteria

### Reward Display
- [ ] Given rewards exist, when page loads, then grid displays correctly
- [ ] Given pinned goal, when viewing, then goal section shows at top
- [ ] Given point balance, when viewing, then header shows balance

### Redemption Flow
- [ ] Given sufficient points, when redeem clicked, then confirmation shows
- [ ] Given confirmed redemption, when processed, then points deducted
- [ ] Given insufficient points, when redeem attempted, then blocked with message

### Timer Features
- [ ] Given timer redemption, when started, then countdown begins
- [ ] Given active timer, when paused, then timer stops
- [ ] Given timer complete, when finished, then alert plays

### Stock Management
- [ ] Given quantity reward, when redeemed, then stock decrements
- [ ] Given out of stock, when viewing, then disabled state shows

### Edge Cases
- [ ] Given no rewards, when page loads, then empty state shows
- [ ] Given timer active on refresh, when app loads, then timer restores

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-POINT-001 | Upstream | Uses point balance |
| SPEC-BE-EXCHANGE-001 | Parallel | Backend exchange API |
| SPEC-FE-PARENT-001 | Upstream | Parent configures rewards |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
