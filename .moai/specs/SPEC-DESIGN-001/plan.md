# SPEC-DESIGN-001: Child App Prototype Design

## Overview

Create comprehensive UI/UX prototype for the child-facing application (ages 6-12). This is the foundation of BabyEco's Design-First approach.

**Business Context**: The child app is the primary interface for children to interact with the behavioral incentive economy system. It must be engaging, easy to use, and appropriate for the cognitive development of 6-12 year olds.

**Target Users**:
- Primary: Children 6-12 years old
- Secondary: Parents (approving designs)

---

## Design Philosophy

### Age-Appropriate Design Principles

| Principle | Application |
|-----------|-------------|
| Large Touch Targets | Minimum 48px tap targets |
| Clear Visual Hierarchy | One primary action per screen |
| Positive Reinforcement | Celebration animations, encouraging copy |
| Simple Navigation | Max 3 levels deep, persistent nav bar |
| Consistent Patterns | Same interaction = same visual response |
| Safe Exploration | No destructive actions without confirmation |

### Cognitive Development Considerations

**Ages 6-8 (Early)**:
- Literal interpretation, needs explicit instructions
- Shorter attention span, break tasks into steps
- Visual over text-heavy
- Immediate feedback essential

**Ages 9-12 (Late)**:
- Can handle more complex flows
- Starting to appreciate status/achievements
- Can read longer text
- Peer comparison becomes relevant

---

## User Flow Overview

### Core User Journeys

```
1. First-Time User
   Welcome → Enter Invite Code → Profile Created → First Task Tutorial

2. Daily Usage
   Home → View Tasks → Complete Task → Check-in → Celebrate → View Points

3. Exchange Flow
   Home → Exchange Center → Browse Items → Pin Goal → Earn Points → Exchange

4. Entertainment Flow
   Home → Entertainment → Choose Content → Unlock/Read → Answer Questions → Earn Points
```

---

## Screen Specifications

### 1. Welcome Screen

**Purpose**: First impression and brand introduction

**Elements**:
- Logo animation (playful bounce)
- Welcome message in child-friendly language
- "Let's Go!" CTA button
- Background with subtle animation (floating shapes)

**Interaction**:
- Tap CTA → Navigate to invite code input
- Animation: Logo bounces in, shapes float gently

**Copy Guidelines**:
- Title: "Welcome to BabyEco!"
- Subtitle: "Your adventure starts here"
- CTA: "Let's Go!"

---

### 2. Device Binding Screen

**Purpose**: Enter invite code to bind device to profile

**Elements**:
- 6-character code input (individual boxes)
- "Confirm" button (disabled until 6 chars entered)
- "Need Help?" link (opens help modal)
- Progress indicator

**Input Behavior**:
- Auto-advance to next box on input
- Backspace moves to previous box
- Visual feedback on each character

**Error States**:
- Invalid code: "Hmm, that code doesn't look right. Try again!"
- Already used: "This code was already used. Ask your parent for a new one."
- Network error: "Oops! Something went wrong. Let's try again."

**Success Transition**:
- Confetti celebration
- "Yay! You're all set!"
- Auto-navigate to home after 2 seconds

---

### 3. Home Dashboard

**Purpose**: Central hub for daily activities

**Layout**:
```
┌─────────────────────────────┐
│  Header                     │
│  ┌───────────────────────┐  │
│  │ Avatar  Name  Age     │  │
│  │        Points: XXX    │  │
│  └───────────────────────┘  │
│                              │
│  Today's Tasks              │
│  ┌───────────────────────┐  │
│  │ Task Card 1           │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │ Task Card 2           │  │
│  └───────────────────────┘  │
│                              │
│  Quick Stats                │
│  ┌─────┐ ┌─────┐ ┌─────┐   │
│  │ 🔥  │ │ ⭐  │ │ 🎯  │   │
│  │ 5   │ │ 120 │ │ 80% │   │
│  │day  │ │pts  │ │goal │   │
│  └─────┘ └─────┘ └─────┘   │
│                              │
│  Bottom Navigation          │
│  [Home][Tasks][Points][More]│
└─────────────────────────────┘
```

**Elements**:
- Profile summary (avatar, name, age)
- Current point balance (with animation on change)
- Today's task cards (swipeable)
- Quick stats (streak, total points, goal progress)
- Bottom navigation bar

**Animations**:
- Task cards slide in on load
- Point balance animates when changed
- Streak fire has subtle flicker animation

---

### 4. Task List Screen

**Purpose**: View all tasks with filtering

**Elements**:
- Category filter pills (Daily, Weekly, One-time, Family)
- Task cards grouped by category
- Completion status indicator
- Points badge on each card

**Task Card Design**:
```
┌─────────────────────────────────────┐
│ 📚  Complete homework               │
│     +10 points  •  Daily task       │
│                                      │
│     [────────────────░]  1/1 done   │
│                                      │
│     ⏰ Do by 6:00 PM                │
└─────────────────────────────────────┘
```

**States**:
- Pending: Full color, check-in button visible
- Completed: Muted, checkmark, "Done!" badge
- Overdue: Red accent, "Missed" badge
- Awaiting Approval: Yellow accent, "Waiting for parent" badge

---

### 5. Task Detail Screen

**Purpose**: View task details and check-in

**Elements**:
- Task title and description
- Points to earn
- Time window (if applicable)
- Instructions (parent-provided)
- "I Did It!" check-in button
- Streak bonus indicator

**Check-in Flow**:
1. User taps "I Did It!"
2. Confirmation modal appears
3. User confirms
4. Success celebration (confetti + sound)
5. Point gain animation
6. Auto-return to task list after 3 seconds

**Celebration Animation**:
- Confetti burst from button
- Points float up: "+10"
- Sound effect (optional, respects settings)
- Character mascot cheers (optional)

---

### 6. Point Overview Screen

**Purpose**: View point balance and history

**Elements**:
- Large point balance display (animated)
- Current goal progress bar
- Quick stats (earned this week, spent this week)
- Transaction history list

**Transaction Card**:
```
┌─────────────────────────────────────┐
│ 💚 Completed homework        +10    │
│    Today, 4:30 PM                   │
├─────────────────────────────────────┤
│ 🎁 Redeemed screen time      -50    │
│    Yesterday, 7:00 PM              │
└─────────────────────────────────────┘
```

**Color Coding**:
- Green (+): Earning
- Red (-): Spending
- Blue (⏸): Frozen (pending exchange)

---

### 7. Exchange Center Screen

**Purpose**: Browse and redeem rewards

**Layout**:
```
┌─────────────────────────────┐
│  My Goal (Pinned Item)     │
│  ┌───────────────────────┐  │
│  │ 🎮 Screen Time 30min  │  │
│  │ [────────────░] 80%   │  │
│  │ 120/150 points        │  │
│  └───────────────────────┘  │
│                              │
│  Available Rewards          │
│  ┌───────┐ ┌───────┐       │
│  │ Item1 │ │ Item2 │       │
│  └───────┘ └───────┘       │
│  ┌───────┐ ┌───────┐       │
│  │ Item3 │ │ Item4 │       │
│  └───────┘ └───────┘       │
│                              │
│  My Wishlist                │
│  (Items I want that aren't  │
│   available yet)            │
└─────────────────────────────┘
```

**Item Card Design**:
```
┌───────────────────┐
│      [Image]      │
│                   │
│  Movie Night      │
│  🎟 200 points    │
│                   │
│  [Pin as Goal]    │
└───────────────────┘
```

**Timer Item (Time-based)**:
```
┌───────────────────┐
│      [Image]      │
│                   │
│  Screen Time 1hr  │
│  🎟 100 points    │
│                   │
│  ⏱ 7:00:00 left   │
│  [Start Timer]    │
└───────────────────┘
```

---

### 8. Entertainment Hub Screen

**Purpose**: Access entertainment content

**Elements**:
- Category tabs (eBooks, Games, Videos - MVP: eBooks only)
- Content gallery (grid or carousel)
- Unlock status on each item
- Point cost/gain indicator

**Content Card**:
```
┌───────────────────┐
│   [Book Cover]    │
│                   │
│  Adventure Story  │
│  📖 Read & Earn   │
│  +20 points       │
└───────────────────┘
```

**Unlock States**:
- Free: No cost badge
- Paid: Cost badge with points
- Earn: "+" badge for reading rewards
- Locked: Lock icon, tap to unlock

---

### 9. Reading Module Screen

**Purpose**: Read content and answer AI questions

**Reading View**:
- Clean, distraction-free text
- Adjustable font size
- Progress indicator
- "Done Reading" button

**Q&A Interface**:
```
┌─────────────────────────────────────┐
│  🤖 Great reading! Let's talk about │
│     what you learned.              │
│                                      │
│  Question 1 of 3                    │
│  "What was the main character's    │
│   name?"                            │
│                                      │
│  ┌─────────────────────────────┐   │
│  │ Type your answer here...    │   │
│  └─────────────────────────────┘   │
│                                      │
│  [I don't know 💭]                   │
│                                      │
│           [Submit Answer]            │
└─────────────────────────────────────┘
```

**Hint Mode** (after 2 "I don't know"):
```
💡 Hint: The character's name starts
   with "A" and they love adventure...
```

---

### 10. AI Q&A Chat Screen

**Purpose**: Ask questions to AI assistant

**Elements**:
- Chat interface with message bubbles
- Quick question suggestions
- Typing indicator
- Child-friendly AI avatar

**Chat Layout**:
```
┌─────────────────────────────────────┐
│                                      │
│  🤖 Hi! I'm Eco, your learning      │
│     buddy. What would you like to   │
│     know?                           │
│                                      │
│  ┌────────────┐                     │
│  │ Why is sky │                     │
│  │ blue?      │                     │
│  └────────────┘                     │
│                                      │
│  🤖 Great question! The sky looks   │
│     blue because...                 │
│                                      │
│  [─────────────────────────────]   │
│  [Type your question...]     [Send] │
└─────────────────────────────────────┘
```

**Safety Features**:
- All responses are age-appropriate
- Emotional content triggers parent notification
- Out-of-scope questions get friendly refusal

---

### 11. Growth Dashboard Screen

**Purpose**: View achievements and progress

**Elements**:
- Total points earned (all time)
- Current streak
- Task completion rate (weekly/monthly)
- Achievement badges
- Milestone timeline

**Achievement Badge**:
```
┌───────────────────┐
│       🏆          │
│   7-Day Streak    │
│   Unlocked!       │
│   March 15, 2024  │
└───────────────────┘
```

---

### 12. Settings Screen

**Purpose**: Manage preferences (limited for children)

**Elements**:
- Profile view/edit
- Sound on/off toggle
- Notification preferences
- Help & FAQ
- "Ask Parent for Help" button

---

## Animation Specifications

### Micro-interactions

| Element | Trigger | Animation | Duration |
|---------|---------|-----------|----------|
| Button | Press | Scale down 0.95, opacity 0.8 | 100ms |
| Task Card | Complete | Slide right, fade out | 300ms |
| Point Balance | Change | Number increment, scale pulse | 500ms |
| Streak Counter | Increment | Fire emoji bounce | 400ms |
| Navigation | Tap | Icon scale, color change | 150ms |

### Celebration Animations

**Task Completion**:
- Confetti burst (50 particles, 1.5s)
- Points float up and fade (0.5s delay, 1s duration)
- Haptic feedback (if supported)
- Sound effect (optional)

**Goal Achieved**:
- Bigger confetti burst (100 particles, 2s)
- Trophy animation
- "Goal Achieved!" modal
- Share card generation option

### Page Transitions

| Transition | Animation | Duration |
|------------|-----------|----------|
| Push | Slide in from right | 300ms |
| Pop | Slide out to right | 300ms |
| Modal | Fade in + scale from 0.95 | 250ms |
| Tab | Cross-fade | 200ms |

---

## Color Palette (Child App)

### Primary Colors

```css
--child-primary: #FF6B6B;      /* Warm coral - main actions */
--child-secondary: #4ECDC4;    /* Teal - secondary actions */
--child-accent: #FFE66D;       /* Yellow - highlights */
--child-success: #95E1A3;      /* Green - completion */
--child-warning: #FFD93D;      /* Yellow - caution */
--child-danger: #FF8B94;       /* Red - errors (soft) */
```

### Background Colors

```css
--child-bg-primary: #FFF9F0;   /* Warm cream */
--child-bg-secondary: #FFFFFF; /* White cards */
--child-bg-overlay: rgba(0, 0, 0, 0.4); /* Modal overlay */
```

### Text Colors

```css
--child-text-primary: #2D3436;   /* Dark gray */
--child-text-secondary: #636E72; /* Medium gray */
--child-text-muted: #B2BEC3;     /* Light gray */
--child-text-inverse: #FFFFFF;   /* White */
```

---

## Typography

### Font Family

```css
--font-display: 'Nunito', sans-serif;  /* Headings */
--font-body: 'Nunito', sans-serif;      /* Body text */
```

### Type Scale

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| Heading 1 | 32px | 800 | 1.2 |
| Heading 2 | 24px | 700 | 1.3 |
| Heading 3 | 20px | 700 | 1.4 |
| Body Large | 18px | 600 | 1.5 |
| Body | 16px | 600 | 1.5 |
| Body Small | 14px | 600 | 1.5 |
| Caption | 12px | 500 | 1.4 |

---

## Component Library

### Button Variants

```tsx
// Primary Button
<Button variant="primary" size="lg">
  I Did It!
</Button>

// Secondary Button
<Button variant="secondary" size="md">
  View Details
</Button>

// Icon Button
<IconButton icon="check" variant="success" />

// Disabled State
<Button disabled>Waiting...</Button>
```

### Card Components

```tsx
// Task Card
<TaskCard
  title="Complete homework"
  points={10}
  category="daily"
  status="pending"
  onCheckIn={handleCheckIn}
/>

// Exchange Item Card
<ExchangeCard
  title="Screen Time 30min"
  cost={100}
  type="timer"
  onPin={handlePin}
/>

// Achievement Badge
<Badge
  icon="trophy"
  title="7-Day Streak"
  unlocked={true}
/>
```

---

## Accessibility Guidelines

### WCAG 2.1 AA Compliance

| Requirement | Implementation |
|-------------|----------------|
| Color Contrast | Minimum 4.5:1 for text |
| Touch Targets | Minimum 48x48px |
| Text Scaling | Support up to 200% |
| Screen Reader | All elements labeled |
| Focus Indicators | Visible focus rings |
| Motion | Respect prefers-reduced-motion |

### Age-Specific Considerations

**6-8 years**:
- Simpler language
- More icons, less text
- Immediate feedback
- Fewer choices per screen

**9-12 years**:
- More detailed information
- Achievement comparisons
- Progress statistics
- Social features (future)

---

## Prototyping Tools

### Recommended Tools

| Phase | Tool | Purpose |
|-------|------|---------|
| Wireframes | Figma | Low-fidelity layout |
| High-fidelity | Figma | Final visual design |
| Interactions | Figma Prototype | Click-through flows |
| Animation | Lottie/GSAP | Motion specifications |

### Deliverable Formats

1. **Figma File**: Complete design system and all screens
2. **Prototype Link**: Interactive click-through for user testing
3. **Asset Export**: Icons, illustrations in SVG/PNG
4. **Animation Specs**: Lottie JSON files for complex animations
5. **Design Tokens**: JSON file for developer handoff

---

## Deliverables Checklist

### Wireframes
- [ ] All 12 core screens
- [ ] Error states for each screen
- [ ] Loading states
- [ ] Empty states

### High-Fidelity Designs
- [ ] All screens in final colors
- [ ] All component states
- [ ] Responsive considerations (if applicable)

### Interaction Specifications
- [ ] All micro-interactions documented
- [ ] Page transitions defined
- [ ] Celebration animations specified

### Design System
- [ ] Color palette
- [ ] Typography scale
- [ ] Component library
- [ ] Spacing grid
- [ ] Animation timing

### Developer Handoff
- [ ] Design tokens JSON
- [ ] Asset exports
- [ ] Animation specs
- [ ] Accessibility notes

---

## User Testing Plan

### Testing Phases

| Phase | Participants | Method | Focus |
|-------|--------------|--------|-------|
| 1. Wireframes | 5 children | Think-aloud | Flow comprehension |
| 2. Hi-Fi Prototype | 10 children | Task-based | Usability |
| 3. Animation Review | 5 children | Observation | Engagement |

### Key Metrics

- Task completion rate
- Time to complete key tasks
- Error rate
- Satisfaction (smile sheet)
- Engagement indicators

---

## Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| Design tool license | Required | Figma |
| User testing participants | Required | 6-12 year olds with parent consent |
| Animation software | Required | After Effects / Lottie |

---

## Timeline

| Week | Milestone |
|------|-----------|
| 1 | User research, personas, user flows |
| 2 | Wireframes for all screens |
| 3 | High-fidelity designs |
| 4 | Interactive prototype, user testing |
| 5 | Design system documentation, handoff |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Children don't understand UI | High | Medium | Early user testing, iterative design |
| Animations too distracting | Medium | Low | Balance engagement with usability |
| Accessibility gaps | High | Medium | WCAG checklist, testing with diverse users |
| Design-dev handoff gaps | Medium | Medium | Detailed specs, design tokens, regular syncs |

---

## Acceptance Criteria

### Design Quality
- [ ] All 12 core screens designed
- [ ] Consistent design language across all screens
- [ ] WCAG 2.1 AA accessibility compliance
- [ ] Age-appropriate language and visuals

### User Validation
- [ ] User testing with 10+ children completed
- [ ] Task completion rate >= 80%
- [ ] No critical usability issues remaining

### Developer Handoff
- [ ] Figma file organized and shared
- [ ] Design tokens exported
- [ ] Animation specs documented
- [ ] Component states defined

### Documentation
- [ ] Design system documentation complete
- [ ] Interaction patterns documented
- [ ] Accessibility guidelines documented

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-DESIGN-002 | Parallel | Parent app design (shared design system) |
| SPEC-DESIGN-003 | Downstream | Design system based on these designs |
| SPEC-FE-AUTH-002 | Downstream | Implements child auth UI |
| SPEC-FE-TASK-001 | Downstream | Implements task system UI |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
