# SPEC-DESIGN-003: Design System Specification

## Overview

Create a comprehensive design system that serves as the single source of truth for both Child and Parent applications.

**Business Context**: A unified design system ensures consistency across applications, accelerates development, and maintains brand integrity. It provides reusable components, tokens, and guidelines for the entire BabyEco product family.

**Target Users**:
- Primary: Frontend developers implementing UI
- Secondary: Designers creating new screens
- Tertiary: QA engineers testing UI consistency

---

## Design Philosophy

### Core Principles

| Principle | Application |
|-----------|-------------|
| Consistency | Same patterns across child/parent apps |
| Scalability | Easy to extend for new features |
| Accessibility | WCAG 2.1 AA as baseline |
| Performance | Optimized for mobile-first |
| Maintainability | Clear naming, documentation |

### Token-First Approach

All design decisions are expressed as tokens:
- Color tokens
- Typography tokens
- Spacing tokens
- Shadow tokens
- Animation tokens

---

## Design Tokens

### Color System

#### Brand Colors

```css
/* Primary Brand */
--brand-primary: #FF6B6B;
--brand-primary-light: #FF8B8B;
--brand-primary-dark: #E55555;

/* Secondary Brand */
--brand-secondary: #4ECDC4;
--brand-secondary-light: #6ED9D2;
--brand-secondary-dark: #3CB8AF;
```

#### Semantic Colors

```css
/* Success */
--semantic-success: #10B981;
--semantic-success-light: #D1FAE5;
--semantic-success-dark: #059669;

/* Warning */
--semantic-warning: #F59E0B;
--semantic-warning-light: #FEF3C7;
--semantic-warning-dark: #D97706;

/* Error */
--semantic-error: #EF4444;
--semantic-error-light: #FEE2E2;
--semantic-error-dark: #DC2626;

/* Info */
--semantic-info: #3B82F6;
--semantic-info-light: #DBEAFE;
--semantic-info-dark: #2563EB;
```

#### Neutral Colors

```css
/* Gray Scale */
--gray-50: #F9FAFB;
--gray-100: #F3F4F6;
--gray-200: #E5E7EB;
--gray-300: #D1D5DB;
--gray-400: #9CA3AF;
--gray-500: #6B7280;
--gray-600: #4B5563;
--gray-700: #374151;
--gray-800: #1F2937;
--gray-900: #111827;
```

#### App-Specific Palettes

```css
/* Child App Palette */
--child-bg-primary: #FFF9F0;
--child-bg-secondary: #FFFFFF;
--child-surface: #FFFFFF;
--child-text-primary: #2D3436;
--child-text-secondary: #636E72;

/* Parent App Palette */
--parent-bg-primary: #F9FAFB;
--parent-bg-secondary: #FFFFFF;
--parent-surface: #FFFFFF;
--parent-text-primary: #111827;
--parent-text-secondary: #6B7280;
```

---

### Typography System

#### Font Families

```css
/* Display Font (Headlines) */
--font-display: 'Nunito', -apple-system, BlinkMacSystemFont, sans-serif;

/* Body Font */
--font-body: 'Nunito', -apple-system, BlinkMacSystemFont, sans-serif;

/* Monospace (Code/Data) */
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

#### Font Size Scale

```css
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 2rem;      /* 32px */
--text-4xl: 2.5rem;    /* 40px */
```

#### Font Weight Scale

```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
--font-extrabold: 800;
```

#### Line Height Scale

```css
--leading-none: 1;
--leading-tight: 1.25;
--leading-snug: 1.375;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
--leading-loose: 2;
```

---

### Spacing System

#### Base Unit: 4px

```css
--space-0: 0;
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
--space-24: 6rem;     /* 96px */
```

---

### Border Radius System

```css
--radius-none: 0;
--radius-sm: 0.25rem;    /* 4px */
--radius-md: 0.5rem;     /* 8px */
--radius-lg: 0.75rem;    /* 12px */
--radius-xl: 1rem;       /* 16px */
--radius-2xl: 1.5rem;    /* 24px */
--radius-full: 9999px;   /* Pill shape */
```

---

### Shadow System

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
--shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
```

---

### Animation System

#### Duration Scale

```css
--duration-75: 75ms;
--duration-100: 100ms;
--duration-150: 150ms;
--duration-200: 200ms;
--duration-300: 300ms;
--duration-500: 500ms;
--duration-700: 700ms;
--duration-1000: 1000ms;
```

#### Easing Functions

```css
--ease-linear: linear;
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
--ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
```

#### Animation Presets

```css
/* Fade In */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide Up */
@keyframes slideUp {
  from { transform: translateY(16px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Scale In */
@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

/* Bounce */
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

/* Pulse */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Confetti Burst */
@keyframes confetti {
  0% { transform: translateY(0) rotate(0deg); opacity: 1; }
  100% { transform: translateY(-100px) rotate(720deg); opacity: 0; }
}
```

---

## Component Library

### Button Component

```tsx
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
  size: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  children: React.ReactNode;
}

// Variants
// Primary: Filled with brand color
// Secondary: Outlined with brand color
// Ghost: Transparent with brand color text
// Danger: Filled with error color
// Success: Filled with success color

// Sizes
// sm: 32px height, 14px font
// md: 40px height, 16px font
// lg: 48px height, 18px font
```

### Card Component

```tsx
interface CardProps {
  variant: 'elevated' | 'outlined' | 'filled';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  clickable?: boolean;
  children: React.ReactNode;
}

// Variants
// Elevated: Shadow, white background
// Outlined: Border, no shadow
// Filled: Gray background, no border/shadow
```

### Input Component

```tsx
interface InputProps {
  type: 'text' | 'email' | 'password' | 'number' | 'tel';
  size: 'sm' | 'md' | 'lg';
  label?: string;
  placeholder?: string;
  helperText?: string;
  error?: string;
  disabled?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

// States
// Default: Gray border
// Focus: Brand color border, focus ring
// Error: Error color border, error message
// Disabled: Muted appearance, no interaction
```

### Modal Component

```tsx
interface ModalProps {
  size: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  title?: string;
  closable?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  footer?: React.ReactNode;
  children: React.ReactNode;
}

// Sizes
// sm: 400px max-width
// md: 560px max-width
// lg: 720px max-width
// xl: 960px max-width
// full: 100vw/100vh
```

### Toast Component

```tsx
interface ToastProps {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  position: 'top' | 'bottom';
}

// Auto-dismiss after duration (default: 4000ms)
// Swipe to dismiss
// Stacks from position
```

### Avatar Component

```tsx
interface AvatarProps {
  size: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  src?: string;
  name: string;
  status?: 'online' | 'offline' | 'busy';
  badge?: string | number;
}

// Sizes
// xs: 24px
// sm: 32px
// md: 40px
// lg: 56px
// xl: 80px

// Fallback: Initials from name
// Status dot: Bottom-right corner
```

### Badge Component

```tsx
interface BadgeProps {
  variant: 'solid' | 'soft' | 'outlined';
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

// Variants
// Solid: Filled background
// Soft: Light background, dark text
// Outlined: Border only
```

### Progress Component

```tsx
interface ProgressProps {
  value: number;
  max: number;
  size: 'sm' | 'md' | 'lg';
  color: 'primary' | 'secondary' | 'success' | 'warning';
  showLabel?: boolean;
  animated?: boolean;
}
```

### Skeleton Component

```tsx
interface SkeletonProps {
  variant: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
}
```

---

## Icon System

### Icon Library

Use Lucide Icons as base library with custom icons for brand-specific needs.

### Icon Sizes

```css
--icon-xs: 12px;
--icon-sm: 16px;
--icon-md: 20px;
--icon-lg: 24px;
--icon-xl: 32px;
```

### Custom Icons Required

| Icon Name | Usage |
|-----------|-------|
| points-star | Point display |
| task-check | Task completion |
| streak-fire | Streak indicator |
| gift-box | Exchange center |
| timer-clock | Timer-based rewards |
| growth-chart | Growth dashboard |
| parent-child | Family management |

---

## Layout Patterns

### Grid System

```css
/* 12-column grid */
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

.grid {
  display: grid;
  gap: var(--space-4);
}

.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.grid-cols-6 { grid-template-columns: repeat(6, minmax(0, 1fr)); }
.grid-cols-12 { grid-template-columns: repeat(12, minmax(0, 1fr)); }
```

### Responsive Breakpoints

```css
/* Mobile First */
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;
```

### Common Layout Patterns

#### Page Layout

```tsx
<Page>
  <Header />
  <Main>
    <Content />
  </Main>
  <Navigation />
</Page>
```

#### List Layout

```tsx
<List>
  <ListItem />
  <ListItem />
  <ListItem />
</List>
```

#### Card Grid

```tsx
<CardGrid columns={3}>
  <Card />
  <Card />
  <Card />
</CardGrid>
```

---

## Accessibility Guidelines

### Focus Management

```css
/* Focus Ring */
*:focus-visible {
  outline: 2px solid var(--brand-primary);
  outline-offset: 2px;
}
```

### Color Contrast

- All text must meet WCAG AA (4.5:1 for normal text, 3:1 for large text)
- Interactive elements must have 3:1 contrast ratio
- Never rely on color alone to convey information

### Touch Targets

- Minimum 44x44px for all interactive elements
- Minimum 8px spacing between touch targets

### Motion Preferences

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## File Structure

```
design-system/
├── tokens/
│   ├── colors.css
│   ├── typography.css
│   ├── spacing.css
│   ├── shadows.css
│   └── animations.css
├── components/
│   ├── Button/
│   ├── Card/
│   ├── Input/
│   ├── Modal/
│   ├── Toast/
│   ├── Avatar/
│   ├── Badge/
│   ├── Progress/
│   └── Skeleton/
├── patterns/
│   ├── layouts/
│   └── compositions/
└── icons/
    ├── lucide/
    └── custom/
```

---

## Deliverables

### Design Tokens
- [ ] CSS custom properties file
- [ ] Tailwind config extension
- [ ] JSON export for other platforms

### Components
- [ ] All components implemented in React
- [ ] Storybook documentation
- [ ] Unit tests for all components
- [ ] Accessibility tests

### Documentation
- [ ] Usage guidelines
- [ ] Code examples
- [ ] Do's and Don'ts
- [ ] Contribution guidelines

---

## Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| SPEC-DESIGN-001 | Completed | Child app colors |
| SPEC-DESIGN-002 | Completed | Parent app colors |
| Tailwind CSS | Required | v3.4+ |
| shadcn/ui | Required | Base component library |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Token inconsistency | High | Medium | Automated token validation |
| Component sprawl | Medium | Medium | Strict contribution guidelines |
| Accessibility gaps | High | Low | Automated a11y testing |

---

## Acceptance Criteria

### Token Coverage
- [ ] All color tokens defined
- [ ] All typography tokens defined
- [ ] All spacing tokens defined
- [ ] All animation tokens defined

### Component Coverage
- [ ] 10+ base components implemented
- [ ] All variants covered
- [ ] All states covered
- [ ] Responsive behavior verified

### Documentation
- [ ] Storybook deployed
- [ ] Usage guidelines complete
- [ ] Accessibility guidelines complete

### Testing
- [ ] 100% component test coverage
- [ ] Visual regression tests
- [ ] Accessibility tests passing

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-DESIGN-001 | Upstream | Child app design requirements |
| SPEC-DESIGN-002 | Upstream | Parent app design requirements |
| All FE SPECs | Downstream | Consumes design system |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
