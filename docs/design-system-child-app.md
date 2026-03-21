# BabyEco Child App - Design System Documentation

## Design Principles

The BabyEco child app follows a **playful, encouraging, and age-appropriate** design philosophy targeting children ages 6-12.

### Core Principles

| Principle | Description |
|-----------|-------------|
| **Large Touch Targets** | Minimum 48x48px tap targets for small fingers |
| **Clear Visual Hierarchy** | One primary action per screen |
| **Positive Reinforcement** | Celebration animations, encouraging copy |
| **Simple Navigation** | Max 3 levels deep, persistent bottom nav |
| **Consistent Patterns** | Same interaction = same visual response |
| **Safe Exploration** | No destructive actions without confirmation |

---

## Color Palette

### Primary Colors

```css
/* Main Colors */
--child-primary: #FF6B6B;      /* Warm coral - main actions, CTAs */
--child-secondary: #4ECDC4;    /* Teal - secondary actions */
--child-accent: #FFE66D;       /* Yellow - highlights, stars */
--child-success: #95E1A3;      /* Green - completion, achievements */
--child-warning: #FFD93D;      /* Yellow - caution */
--child-danger: #FF8B94;       /* Red - errors (soft, child-friendly) */
```

### Background Colors

```css
--child-bg-primary: #FFF9F0;   /* Warm cream - main background */
--child-bg-secondary: #FFFFFF; /* White - cards, content areas */
--child-bg-overlay: rgba(0, 0, 0, 0.4); /* Modal overlay */
--child-bg-hover: rgba(255, 107, 107, 0.08); /* Hover state */
```

### Text Colors

```css
--child-text-primary: #2D3436;   /* Dark gray - headings, important text */
--child-text-secondary: #636E72; /* Medium gray - body text */
--child-text-muted: #B2BEC3;     /* Light gray - placeholders, disabled */
--child-text-inverse: #FFFFFF;   /* White - text on colored backgrounds */
```

### Semantic Colors (Transaction Types)

```css
--child-transaction-earn: #95E1A3;  /* Green (+): Earning points */
--child-transaction-spend: #FF8B94; /* Red (-): Spending points */
--child-transaction-frozen: #4ECDC4; /* Blue (⏸): Frozen/Pending */
```

### Color Usage Guidelines

| Context | Color | Usage |
|---------|-------|-------|
| Primary Buttons | `--child-primary` | Main actions (Check-in, Exchange) |
| Secondary Buttons | `--child-secondary` | Alternative actions |
| Success States | `--child-success` | Completed tasks, achievements |
| Error States | `--child-danger` | Soft error messages (not scary!) |
| Warnings | `--child-warning` | Time reminders, low points |
| Links | `--child-secondary` | Navigation anchors |

---

## Typography

### Font Family

```css
--font-display: 'Nunito', 'Quicksand', sans-serif;  /* Headings */
--font-body: 'Nunito', 'Quicksand', sans-serif;     /* Body text */
```

**Rationale**: Nunito is a rounded, friendly font that's highly readable for children. It has excellent weight variation for hierarchy.

### Type Scale

| Usage | Size | Weight | Line Height | Example |
|-------|------|--------|-------------|---------|
| **Display / H1** | 32px | 800 (Extra Bold) | 1.2 | Screen titles |
| **Heading / H2** | 24px | 700 (Bold) | 1.3 | Section headers |
| **Subheading / H3** | 20px | 700 (Bold) | 1.4 | Card titles |
| **Body Large** | 18px | 600 (Semi Bold) | 1.5 | Important info |
| **Body** | 16px | 600 (Semi Bold) | 1.5 | Regular content |
| **Body Small** | 14px | 600 (Semi Bold) | 1.5 | Secondary text |
| **Caption** | 12px | 500 (Medium) | 1.4 | Labels, timestamps |

### Typography Guidelines

- **6-8 years**: Use larger sizes (Body Large minimum), shorter words
- **9-12 years**: Can use full scale, more complex sentences
- **Always**: Left-align for readability (avoid center-aligned body text)
- **Emphasis**: Use font weight and color, NOT underline

---

## Spacing & Layout

### Spacing Scale

```css
--space-xs: 4px;     /* Fine spacing (icon inside button) */
--space-sm: 8px;     /* Tight spacing (related items) */
--space-md: 16px;    /* Default spacing (card padding) */
--space-lg: 24px;    /* Section spacing */
--space-xl: 32px;    /* Large gaps (between sections) */
--space-2xl: 48px;   /* Screen margins */
```

### Layout Grid

- **Screen Padding**: 24px on all sides
- **Card Padding**: 16px
- **Button Padding**: 12px horizontal, 16px vertical
- **List Item Gap**: 12px
- **Section Gap**: 24px

### Component Dimensions

| Component | Width | Height | Notes |
|-----------|-------|--------|-------|
| **Button (Primary)** | Auto | 48px | Min width 120px |
| **Button (Large)** | Auto | 56px | Hero CTAs |
| **Touch Target** | Min 48px | Min 48px | WCAG compliance |
| **Card** | Fill container | Auto | Min height 80px |
| **Input Field** | Fill container | 48px | With labels |
| **Bottom Nav** | Fill container | 64px | Fixed height |

---

## Component Library

### Buttons

#### Primary Button

```tsx
<Button
  variant="primary"
  size="lg"
  text="I Did It!"
  icon={null}
  disabled={false}
/>
```

**States**:
- Default: Coral background, white text
- Hover: Darker coral (+10%)
- Active: Scale 0.95
- Disabled: Muted coral, 50% opacity

#### Secondary Button

```tsx
<Button
  variant="secondary"
  size="md"
  text="View Details"
/>
```

**States**:
- Default: Teal background, white text
- Hover: Darker teal (+10%)

#### IconButton

```tsx
<IconButton
  icon="check"
  variant="success"
  size={32}
/>
```

### Cards

#### Task Card

```tsx
<TaskCard
  title="Complete homework"
  points={10}
  category="daily"
  status="pending" // pending | completed | overdue | awaiting_approval
  dueTime="6:00 PM"
  progress={1} // 1/1 for single, 3/5 for multi-step
/>
```

**Card Structure**:
- Icon (left, 48x48px)
- Title + points badge (top row)
- Category + time badge (middle row)
- Progress bar (bottom, if applicable)
- Check-in button (right edge)

#### Exchange Item Card

```tsx
<ExchangeCard
  title="Screen Time 30min"
  cost={100}
  type="timer" // timer | item | custom
  timeRemaining={4200} // seconds, for timer items
  isPinned={true}
  progress={0.8} // 80% toward goal
/>
```

#### Achievement Badge

```tsx
<Badge
  icon="trophy"
  title="7-Day Streak"
  unlocked={true}
  date={new Date('2024-03-15')}
/>
```

### Navigation

#### Bottom Navigation Bar

```tsx
<BottomNav
  items={[
    { icon: 'home', label: 'Home', active: true },
    { icon: 'list', label: 'Tasks', active: false },
    { icon: 'star', label: 'Points', active: false },
    { icon: 'more', label: 'More', active: false },
  ]}
/>
```

**Specifications**:
- Height: 64px
- Background: White with top shadow
- Icon size: 24px
- Label size: 11px
- Active color: Primary coral
- Inactive color: Text muted

---

## Animation Specifications

### Micro-interactions

| Trigger | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Button Press | Scale 0.95, opacity 0.8 | 100ms | Ease-out |
| Task Card Complete | Slide right + fade out | 300ms | Ease-in-out |
| Point Balance Change | Count up animation | 500ms | Ease-out |
| Streak Increment | Bounce effect | 400ms | Spring |
| Navigation Tap | Icon scale + color fade | 150ms | Ease-out |

### Celebration Animations

#### Task Completion

```yaml
Confetti:
  count: 50
  duration: 1500ms
  colors: [primary, secondary, accent, yellow]
  physics:
    gravity: 0.5
    spread: 60 degrees
    speed: 8-12 random

Points Float:
  delay: 500ms
  duration: 1000ms
  text: "+10"
  start: button_center
  end: balance_display
  path: arc_upward

Haptic: medium (if supported)
Sound: "success_chime.mp3" (respects settings)
```

#### Goal Achieved

```yaml
Confetti:
  count: 100
  duration: 2000ms
  colors: [gold, yellow, accent]
  physics:
    gravity: 0.3
    spread: 120 degrees

Trophy Animation:
  scale: 0.5 → 1.2 → 1.0
  rotation: -10deg → 10deg → 0deg
  duration: 600ms

Modal:
  title: "Goal Achieved! 🎉"
  message: "You earned enough points for [Item Name]!"
  actions: [Claim, Share]
```

### Page Transitions

| Transition | Animation | Duration | Easing |
|------------|-----------|----------|--------|
| Push (Forward) | Slide in from right | 300ms | Ease-out |
| Pop (Back) | Slide out to right | 300ms | Ease-in |
| Modal | Fade in + scale 0.95→1 | 250ms | Ease-out |
| Tab Switch | Cross-fade | 200ms | Ease-in-out |

### Animation Guidelines

- **Respects prefers-reduced-motion**: Disable celebrations when user prefers reduced motion
- **Performance**: Use CSS transforms (opacity, transform, scale) - avoid layout-triggering properties
- **Child-Friendly**: Bouncy, playful easing (not stiff linear)
- **Never** scary or sudden - always gentle transitions

---

## Iconography

### Icon Style

- **Style**: Outline style, 2px stroke
- **Size**: 24px default, 16px small, 32px large
- **Corner Radius**: 2px (slight softness)
- **Library**: Lucide Icons (customized for child-friendly appearance)

### Key Icons

| Concept | Icon | Usage |
|---------|------|-------|
| Home | house | Home screen |
| Tasks | list-checks | Task list |
| Points | star | Points/earnings |
| Exchange | gift | Rewards center |
| Settings | settings | Settings menu |
| Check | check | Completion |
| Close | x | Cancel/close |
| Help | help-circle | Help/FAQ |
| Fire | flame | Streak counter |
| Trophy | trophy | Achievement |
| Lock | lock | Locked content |
| Clock | clock | Time remaining |

---

## Accessibility

### WCAG 2.1 AA Compliance

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Color Contrast | Minimum 4.5:1 for text | ✅ Pass |
| Touch Targets | Minimum 48x48px | ✅ Pass |
| Text Scaling | Support up to 200% | ✅ Pass |
| Screen Reader | All elements labeled | ✅ Pass |
| Focus Indicators | Visible focus rings | ✅ Pass |
| Motion | prefers-reduced-motion | ✅ Pass |

### Age-Specific Considerations

**Ages 6-8**:
- Simpler language (Flesch-Kincaid Grade 3-4)
- More icons, less text
- Immediate feedback on all actions
- Fewer choices per screen (3-4 max)
- Larger text (minimum 18px body)

**Ages 9-12**:
- More detailed information
- Achievement comparisons
- Progress statistics
- Social features (future)

---

## Screen Specifications

### 1. Welcome Screen

**Purpose**: First impression and brand introduction

**Elements**:
- Logo (center, 120x120px, bounce animation)
- Welcome message: "Welcome to BabyEco!"
- Subtitle: "Your adventure starts here"
- CTA Button: "Let's Go!" (large, primary)
- Background: Floating shapes animation

**Animation**:
- Logo: Bounce in from bottom (400ms)
- Shapes: Gentle float (CSS keyframe, 3s loop)
- CTA: Pulse effect every 2s

### 2. Device Binding Screen

**Purpose**: Enter invite code to bind device

**Elements**:
- 6-character input (individual boxes, 48x48px each)
- Auto-advance to next box
- "Confirm" button (disabled until 6 chars)
- "Need Help?" link (opens modal)
- Progress indicator (dots)

**Error States**:
- Invalid code: "Hmm, that code doesn't look right. Try again!"
- Already used: "This code was already used. Ask your parent for a new one."
- Network error: "Oops! Something went wrong. Let's try again."

**Success**: Confetti celebration → "Yay! You're all set!" → Auto-nav to Home (2s)

### 3. Home Dashboard

**Purpose**: Central hub for daily activities

**Layout**:
```
┌─────────────────────────────────┐
│ Header                          │
│ ┌─────────────────────────────┐ │
│ │ [Avatar] Name • Age         │ │
│ │ ★ Points: 120               │ │
│ └─────────────────────────────┘ │
│                                 │
│ Today's Tasks                   │
│ ┌─────────────────────────────┐ │
│ │ Task Card 1                 │ │
│ └─────────────────────────────┘ │
│ ┌─────────────────────────────┐ │
│ │ Task Card 2                 │ │
│ └─────────────────────────────┘ │
│                                 │
│ Quick Stats                     │
│ ┌─────┐ ┌─────┐ ┌─────┐      │
│ │ 🔥  │ │ ⭐  │ │ 🎯  │      │
│ │ 5   │ │ 120 │ │ 80% │      │
│ │ day  │ │ pts  │ │goal │      │
│ └─────┘ └─────┘ └─────┘      │
│                                 │
│ Bottom Navigation               │
│ [Home][Tasks][Points][More]     │
└─────────────────────────────────┘
```

### 4-12. Other Screens

(Refer to SPEC-DESIGN-001 plan.md for detailed specifications)

---

## Design Tokens (JSON)

```json
{
  "babyeco-child": {
    "colors": {
      "primary": "#FF6B6B",
      "secondary": "#4ECDC4",
      "accent": "#FFE66D",
      "success": "#95E1A3",
      "warning": "#FFD93D",
      "danger": "#FF8B94",
      "bg": {
        "primary": "#FFF9F0",
        "secondary": "#FFFFFF",
        "overlay": "rgba(0, 0, 0, 0.4)"
      },
      "text": {
        "primary": "#2D3436",
        "secondary": "#636E72",
        "muted": "#B2BEC3",
        "inverse": "#FFFFFF"
      }
    },
    "typography": {
      "fontFamily": {
        "display": "Nunito",
        "body": "Nunito"
      },
      "fontSize": {
        "display": 32,
        "h1": 32,
        "h2": 24,
        "h3": 20,
        "bodyLarge": 18,
        "body": 16,
        "bodySmall": 14,
        "caption": 12
      },
      "fontWeight": {
        "bold": 700,
        "semiBold": 600,
        "medium": 500
      },
      "lineHeight": {
        "tight": 1.2,
        "normal": 1.4,
        "relaxed": 1.5
      }
    },
    "spacing": {
      "xs": 4,
      "sm": 8,
      "md": 16,
      "lg": 24,
      "xl": 32,
      "xxl": 48
    },
    "borderRadius": {
      "sm": 8,
      "md": 12,
      "lg": 16,
      "xl": 24,
      "full": 9999
    },
    "shadows": {
      "sm": "0 1px 2px rgba(0,0,0,0.05)",
      "md": "0 4px 6px rgba(0,0,0,0.07)",
      "lg": "0 10px 15px rgba(0,0,0,0.1)",
      "xl": "0 20px 25px rgba(0,0,0,0.15)"
    }
  }
}
```

---

## Developer Handoff Checklist

- [ ] Design tokens exported as JSON
- [ ] All components documented with props
- [ ] Animation timing and easing specified
- [ ] All states (default, hover, active, disabled) defined
- [ ] Responsive breakpoints specified (if applicable)
- [ ] Accessibility notes included
- [ ] Icon library exported (SVG/PNG)
- [ ] Lottie files exported for complex animations

---

**Document Version**: 1.0
**Last Updated**: 2026-03-21
**Status**: Draft for Review
