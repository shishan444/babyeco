# SPEC-FE-GROWTH-001: Growth Dashboard

## Overview

Implement the growth tracking and achievement interface for the child-facing application, displaying progress, streaks, and milestones.

**Business Context**: The Growth Dashboard motivates children by visualizing their progress over time. It shows achievements, streaks, and provides a sense of accomplishment.

**Target Users**:
- Primary: Children aged 6-12 viewing their progress
- Secondary: Parents reviewing child development

---

## Technical Constraints

### Framework and Versions
- Next.js 22.x with App Router
- React 19.x
- Zustand for state management
- Recharts for data visualization
- Framer Motion for animations

### Dependencies
- SPEC-DESIGN-001 (Child App Design)
- SPEC-DESIGN-003 (Design System)
- SPEC-FE-AUTH-002 (Child Auth Module)
- SPEC-BE-REPORT-001 (Backend Report API)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall display total points earned (all time).

```
Given a child opens the Growth Dashboard
When the screen loads
Then their all-time earned points are displayed prominently
And the number has a celebratory animation
```

**UR-002**: The system shall display current streak status.

```
Given a child views the Growth Dashboard
When the screen loads
Then their current streak (consecutive days with tasks) is displayed
And a fire emoji animates for active streaks
```

**UR-003**: The system shall display task completion rate.

```
Given a child views the Growth Dashboard
When the completion rate section loads
Then weekly and monthly completion percentages are shown
And visual indicators show improvement or decline
```

### Event-Driven Requirements

**EDR-001**: When a child unlocks a new achievement, the system shall display an unlock animation.

```
Given a child earns a new achievement
When the condition is met
Then an unlock animation plays
And the new badge appears in the collection
And a celebration modal shows the achievement details
```

**EDR-002**: When a child taps an achievement badge, the system shall show details.

```
Given a child views their achievement collection
When they tap a badge
Then a detail modal opens
And shows achievement name, description, and unlock date
```

**EDR-003**: When a child reaches a milestone, the system shall celebrate with special animation.

```
Given a child reaches a milestone (e.g., 1000 points)
When the milestone is achieved
Then a special celebration animation plays
And a milestone card is added to their timeline
```

### State-Driven Requirements

**SDR-001**: While no achievements are unlocked, the system shall show locked badges.

```
Given a child has no achievements yet
When they view the achievement section
Then locked badges are displayed in gray
And the unlock conditions are shown
```

**SDR-002**: While on a streak, the system shall animate the streak counter.

```
Given a child has an active streak (>= 3 days)
When viewing the streak display
Then the fire emoji has a subtle flicker animation
And the streak number is highlighted
```

**SDR-003**: While the streak is broken, the system shall show encouragement.

```
Given a child's streak was broken
When viewing the streak display
Then a "Keep going!" message is shown
And the streak counter resets to 0
```

### Optional Requirements

**OR-001**: The system MAY display a milestone timeline.

```
Given a child has reached milestones
When viewing the Growth Dashboard
Then a timeline shows past milestones
And upcoming milestones are previewed
```

**OR-002**: The system MAY display weekly activity charts.

```
Given a child has activity data
When viewing the Growth Dashboard
Then a bar chart shows daily task completions
And the current week is highlighted
```

**OR-003**: The system MAY support sharing achievement cards.

```
Given a child unlocks an achievement
When they view the achievement
Then a "Share" option is available
And generates a shareable image card
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT show other children's achievements.

```
Given multiple children in a family
When a child views their Growth Dashboard
Then only their own achievements are visible
```

**UBR-002**: The system shall NOT allow manual editing of achievement status.

```
Given a child views achievements
When they interact with badges
Then badges cannot be manually unlocked
And only system-earned achievements are shown
```

---

## Technical Solution

### Component Structure

```
src/
├── app/
│   └── (child)/
│       └── (authenticated)/
│           └── growth/
│               └── page.tsx
├── components/
│   ├── growth/
│   │   ├── GrowthDashboard.tsx
│   │   ├── TotalPoints.tsx
│   │   ├── StreakDisplay.tsx
│   │   ├── CompletionRate.tsx
│   │   ├── AchievementGrid.tsx
│   │   ├── AchievementBadge.tsx
│   │   ├── AchievementDetail.tsx
│   │   ├── AchievementUnlock.tsx
│   │   ├── MilestoneTimeline.tsx
│   │   ├── WeeklyChart.tsx
│   │   └── ShareableCard.tsx
│   └── ui/
│       └── (design system components)
├── lib/
│   ├── growth/
│   │   ├── growth-client.ts
│   │   ├── achievement-utils.ts
│   │   └── milestone-utils.ts
│   └── hooks/
│       ├── useGrowthData.ts
│       ├── useAchievements.ts
│       └── useStreak.ts
└── stores/
    └── growth-store.ts
```

### Achievement Badge Component

```tsx
// AchievementBadge.tsx
interface AchievementBadgeProps {
  achievement: Achievement;
  isUnlocked: boolean;
  onPress: () => void;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string; // Emoji or icon name
  category: 'streak' | 'points' | 'tasks' | 'special';
  requirement: {
    type: string;
    value: number;
  };
  unlockedAt?: Date;
}

// Visual states:
// - Unlocked: Full color, glow effect
// - Locked: Grayscale, lock icon overlay
// - New: "NEW" badge, sparkle animation
```

### Streak Display Component

```tsx
// StreakDisplay.tsx
interface StreakDisplayProps {
  currentStreak: number;
  longestStreak: number;
  lastActiveDate: Date;
}

// Features:
// - Large fire emoji with flicker animation (streak >= 3)
// - Current streak number
// - "Best streak" comparison
// - Encouragement message if streak broken
```

### Achievement Types

```typescript
// achievement-utils.ts
export const ACHIEVEMENT_DEFINITIONS: Achievement[] = [
  // Streak achievements
  { id: 'streak-3', name: '3-Day Streak', icon: '🔥', requirement: { type: 'streak', value: 3 } },
  { id: 'streak-7', name: 'Week Warrior', icon: '⚡', requirement: { type: 'streak', value: 7 } },
  { id: 'streak-30', name: 'Monthly Master', icon: '👑', requirement: { type: 'streak', value: 30 } },

  // Point achievements
  { id: 'points-100', name: 'Century Club', icon: '💯', requirement: { type: 'total_points', value: 100 } },
  { id: 'points-500', name: 'Point Collector', icon: '💎', requirement: { type: 'total_points', value: 500 } },
  { id: 'points-1000', name: 'Point Master', icon: '🏆', requirement: { type: 'total_points', value: 1000 } },

  // Task achievements
  { id: 'tasks-10', name: 'Task Starter', icon: '⭐', requirement: { type: 'tasks_completed', value: 10 } },
  { id: 'tasks-50', name: 'Task Champion', icon: '🌟', requirement: { type: 'tasks_completed', value: 50 } },
  { id: 'tasks-100', name: 'Task Legend', icon: '💫', requirement: { type: 'tasks_completed', value: 100 } },

  // Special achievements
  { id: 'first-exchange', name: 'First Reward', icon: '🎁', requirement: { type: 'first_exchange', value: 1 } },
  { id: 'perfect-week', name: 'Perfect Week', icon: '🎯', requirement: { type: 'perfect_week', value: 1 } },
];
```

### State Management

```typescript
// growth-store.ts
interface GrowthState {
  totalPointsEarned: number;
  currentStreak: number;
  longestStreak: number;
  completionRate: {
    weekly: number;
    monthly: number;
  };
  achievements: Achievement[];
  milestones: Milestone[];
  weeklyData: DailyData[];
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchGrowthData: () => Promise<void>;
  checkAchievements: () => Promise<void>;
}
```

### Milestone System

```typescript
// milestone-utils.ts
export const MILESTONE_THRESHOLDS = [
  { type: 'points', value: 100, title: '100 Points Club', reward: null },
  { type: 'points', value: 500, title: '500 Points Milestone', reward: null },
  { type: 'points', value: 1000, title: '1000 Points Champion', reward: null },
  { type: 'tasks', value: 50, title: '50 Tasks Completed', reward: null },
  { type: 'tasks', value: 100, title: '100 Tasks Milestone', reward: null },
  { type: 'streak', value: 7, title: '7-Day Streak!', reward: null },
  { type: 'streak', value: 30, title: '30-Day Streak Master', reward: null },
];

export function checkMilestones(currentStats: Stats, previousStats: Stats): Milestone[] {
  const newMilestones: Milestone[] = [];

  for (const threshold of MILESTONE_THRESHOLDS) {
    const current = currentStats[threshold.type];
    const previous = previousStats[threshold.type];

    if (current >= threshold.value && previous < threshold.value) {
      newMilestones.push({
        ...threshold,
        achievedAt: new Date(),
      });
    }
  }

  return newMilestones;
}
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-DESIGN-001 | Design | Completed | Growth UI designs |
| SPEC-DESIGN-003 | Design | Completed | Design system |
| SPEC-FE-AUTH-002 | Auth | Pending | Child session |
| SPEC-BE-REPORT-001 | API | Pending | Report endpoints |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Chart performance on mobile | Low | Low | Optimize rendering, limit data points |
| Achievement farming | Low | Medium | Backend validation of achievement criteria |
| Demotivation from low stats | Medium | Medium | Positive framing, focus on progress |

---

## Acceptance Criteria

### Dashboard Display
- [ ] Given valid session, when page loads, then all stats display correctly
- [ ] Given streak active, when viewing, then animation plays
- [ ] Given achievements exist, when viewing, then badges show

### Achievement System
- [ ] Given criteria met, when checked, then achievement unlocks
- [ ] Given achievement unlocked, when viewed, then celebration plays
- [ ] Given badge tapped, when opened, then detail modal shows

### Milestones
- [ ] Given milestone reached, when detected, then celebration plays
- [ ] Given milestones history, when viewed, then timeline shows

### Charts
- [ ] Given weekly data, when viewed, then chart renders correctly
- [ ] Given no data, when viewed, then empty state shows

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-TASK-001 | Upstream | Provides task completion data |
| SPEC-FE-POINT-001 | Upstream | Provides point history |
| SPEC-BE-REPORT-001 | Parallel | Backend report API |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
