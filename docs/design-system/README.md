# BabyEco Design System

Unified design system for BabyEco Child and Parent applications.

**Version**: 1.0.0
**Last Updated**: 2026-03-21

---

## Overview

The BabyEco Design System provides a unified set of design tokens, components, and guidelines for both the Child and Parent applications. It ensures consistency across the product family while respecting the unique needs of each audience.

### Key Principles

| Principle | Description |
|-----------|-------------|
| **Consistency** | Shared patterns across Child and Parent apps |
| **Age-Appropriate** | Child-friendly UI, professional parent experience |
| **Accessibility** | WCAG 2.1 AA compliance baseline |
| **Performance** | Mobile-first, optimized animations |
| **Scalability** | Easy to extend for new features |

---

## Quick Start

### Installation

```bash
# Copy tokens to your project
cp docs/design-system/tokens.css src/styles/tokens.css

# Import in your main stylesheet
@import './tokens.css';
```

### Using with Tailwind CSS

```javascript
// tailwind.config.js
const babyecoTokens = require('./docs/design-system/tailwind.config.js');

module.exports = {
  ...babyecoTokens,
  // Add your project-specific overrides
};
```

### Using Design Tokens in CSS

```css
.my-button {
  background-color: var(--child-primary);
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-lg);
  font-size: var(--child-text-base);
  font-weight: var(--font-semibold);
}
```

---

## App Comparison

| Aspect | Child App | Parent App |
|--------|-----------|------------|
| **Primary Color** | Coral (#FF6B6B) | Indigo (#4F46E5) |
| **Secondary Color** | Teal (#4ECDC4) | Purple (#7C3AED) |
| **Font** | Nunito (Playful) | Nunito (Professional) |
| **Touch Targets** | 48px minimum | 44px minimum |
| **Text Size** | Larger (16-32px) | Standard (14-24px) |
| **Shadows** | Softer | Standard |
| **Animations** | Bouncy, playful | Smooth, subtle |
| **Information Density** | Lower | Higher |

---

## Design Tokens

### Colors

#### Child App Colors

```css
/* Primary - Coral */
--child-primary: #FF6B6B;
--child-primary-light: #FF8B8B;
--child-primary-dark: #E55555;

/* Secondary - Teal */
--child-secondary: #4ECDC4;
--child-secondary-light: #6ED9D2;
--child-secondary-dark: #3CB8AF;

/* Accents */
--child-accent: #FFE66D;      /* Yellow */
--child-success: #95E1A3;     /* Green */
--child-warning: #FFD93D;     /* Yellow */
--child-danger: #FF8B94;      /* Soft Red */
```

#### Parent App Colors

```css
/* Primary - Indigo */
--parent-primary: #4F46E5;
--parent-primary-light: #6366F1;
--parent-primary-dark: #4338CA;

/* Secondary - Purple */
--parent-secondary: #7C3AED;
--parent-secondary-light: #8B5CF6;
--parent-secondary-dark: #6D28D9;
```

#### Semantic Colors (Shared)

```css
--semantic-success: #10B981;
--semantic-warning: #F59E0B;
--semantic-error: #EF4444;
--semantic-info: #3B82F6;
```

### Typography

#### Font Families

```css
--font-display: 'Nunito', sans-serif;  /* Headings */
--font-body: 'Nunito', sans-serif;     /* Body text */
--font-mono: 'JetBrains Mono', monospace; /* Code */
```

#### Font Sizes

| Token | Child | Parent | Usage |
|-------|-------|--------|-------|
| `*-text-xs` | 12px | 12px | Captions, labels |
| `*-text-sm` | 14px | 14px | Secondary text |
| `*-text-base` | 16px | 16px | Body text |
| `*-text-lg` | 18px | 18px | Emphasized text |
| `*-text-xl` | 20px | 20px | Subheadings |
| `*-text-2xl` | 24px | 24px | Headings |
| `*-text-3xl` | 32px | 32px | Display |
| `*-text-4xl` | 40px | 40px | Hero titles |

### Spacing

All spacing is based on a 4px base unit.

```css
--space-1: 4px;    /* Fine spacing */
--space-2: 8px;    /* Tight spacing */
--space-3: 12px;   /* Compact */
--space-4: 16px;   /* Default */
--space-6: 24px;   /* Section spacing */
--space-8: 32px;   /* Large gaps */
--space-12: 48px;  /* Screen margins */
```

### Border Radius

```css
--radius-sm: 4px;   /* Small elements */
--radius-md: 8px;   /* Cards, buttons */
--radius-lg: 12px;  /* Large cards */
--radius-xl: 16px;  /* Modals */
--radius-full: 9999px; /* Pills, circles */
```

### Shadows

```css
/* Standard Shadows */
--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

/* Child App - Softer */
--child-shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
--child-shadow-md: 0 4px 8px rgba(0, 0, 0, 0.08);
--child-shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.1);
```

### Animation

```css
/* Durations */
--duration-100: 100ms;  /* Micro-interactions */
--duration-200: 200ms;  /* Default transitions */
--duration-300: 300ms;  /* Page transitions */
--duration-500: 500ms;  /* Complex animations */

/* Easing */
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
--ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
```

---

## Component Guidelines

### Button Component

#### Variants

| Variant | Usage | Child App | Parent App |
|---------|-------|-----------|------------|
| Primary | Main actions | Coral fill | Indigo fill |
| Secondary | Alt actions | Teal fill | Purple fill |
| Ghost | Tertiary | Coral outline | Indigo outline |
| Danger | Destructive | Soft red | Red |
| Success | Confirmation | Green | Green |

#### Sizes

| Size | Child | Parent |
|------|-------|--------|
| sm | 36px | 32px |
| md | 48px | 40px |
| lg | 56px | 48px |

#### Example

```tsx
<Button variant="primary" size="lg" fullWidth>
  Complete Task
</Button>
```

### Card Component

#### Variants

- **Elevated**: Shadow, white background (default)
- **Outlined**: Border, no shadow
- **Filled**: Gray background, no border

#### Example

```tsx
<Card variant="elevated" padding="md" hoverable>
  <CardHeader>
    <Avatar src="/avatar.png" size="md" />
    <Title>Task Name</Title>
  </CardHeader>
  <CardContent>
    <p>Task description here</p>
  </CardContent>
</Card>
```

### Input Component

#### States

- **Default**: Gray border
- **Focus**: Brand color border, focus ring
- **Error**: Red border, error message
- **Disabled**: Muted appearance

#### Example

```tsx
<Input
  type="text"
  label="Child Name"
  placeholder="Enter name"
  error={errors.name}
  helperText="Must be 2-20 characters"
/>
```

---

## Animation Patterns

### Micro-interactions

| Trigger | Animation | Duration |
|---------|-----------|----------|
| Button Press | Scale 0.95 | 100ms |
| Hover | Subtle lift | 200ms |
| Focus | Color fade | 150ms |

### Page Transitions

| Transition | Animation | Duration |
|------------|-----------|----------|
| Push (Forward) | Slide in from right | 300ms |
| Pop (Back) | Slide out to right | 300ms |
| Modal | Fade in + scale | 250ms |

### Child App Celebrations

```css
/* Confetti Burst */
@keyframes confetti {
  0% { transform: translateY(0) rotate(0deg); opacity: 1; }
  100% { transform: translateY(-100px) rotate(720deg); opacity: 0; }
}

/* Points Float */
@keyframes pointsFloat {
  0% { transform: translateY(0) scale(1); opacity: 1; }
  50% { transform: translateY(-30px) scale(1.2); opacity: 1; }
  100% { transform: translateY(-60px) scale(0.8); opacity: 0; }
}
```

---

## Icon System

### Icon Library

Use [Lucide Icons](https://lucide.dev/) as the base library.

### Icon Sizes

```css
--icon-xs: 12px;
--icon-sm: 16px;
--icon-md: 20px;
--icon-lg: 24px;
--icon-xl: 32px;
```

### Common Icons

| Concept | Icon | Usage |
|---------|------|-------|
| Home | `house` | Home screen |
| Tasks | `list-checks` | Task list |
| Points | `star` | Points display |
| Settings | `settings` | Settings menu |
| Check | `check` | Completion |
| Close | `x` | Cancel/close |
| Help | `help-circle` | Help/FAQ |

---

## Accessibility

### WCAG 2.1 AA Compliance

- **Color Contrast**: Minimum 4.5:1 for text
- **Touch Targets**: Minimum 44x44px
- **Focus Indicators**: Visible focus rings
- **Screen Readers**: Proper ARIA labels
- **Motion**: Respects `prefers-reduced-motion`

### Focus Management

```css
*:focus-visible {
  outline: 2px solid var(--child-primary);
  outline-offset: 2px;
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Responsive Breakpoints

```css
--breakpoint-xs: 480px;
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;
```

### Mobile-First Approach

```css
/* Default: Mobile styles */
.container { padding: var(--space-4); }

/* Tablet and up */
@media (min-width: 768px) {
  .container { padding: var(--space-8); }
}

/* Desktop and up */
@media (min-width: 1024px) {
  .container { max-width: 1280px; margin: 0 auto; }
}
```

---

## File Structure

```
docs/design-system/
├── README.md           # This file
├── tokens.css          # CSS custom properties
├── tailwind.config.js  # Tailwind CSS configuration
├── tokens.json         # JSON export for cross-platform
└── components/         # Component documentation (future)
```

---

## Best Practices

### DO's

- Use design tokens for all styling decisions
- Follow the established color hierarchy
- Respect touch target minimums
- Test with screen readers
- Provide alt text for images
- Use semantic HTML

### DON'Ts

- Don't hardcode colors or sizes
- Don't create custom shadows without checking tokens
- Don't use color alone to convey information
- Don't skip accessibility attributes
- Don't ignore reduced motion preferences
- Don't create components that don't scale

---

## Migration Guide

### Migrating from Hardcoded Styles

**Before:**
```css
.my-element {
  background-color: #FF6B6B;
  padding: 16px;
  border-radius: 12px;
}
```

**After:**
```css
.my-element {
  background-color: var(--child-primary);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
}
```

### Tailwind Class Migration

**Before:**
```html
<div class="bg-[#FF6B6B] p-4 rounded-xl">
```

**After:**
```html
<div class="bg-child-primary p-4 rounded-xl">
```

---

## Contributing

When contributing to the design system:

1. **Token Changes**: Update all three formats (CSS, Tailwind, JSON)
2. **New Components**: Document with props and examples
3. **Breaking Changes**: Bump major version
4. **Additions**: Bump minor version
5. **Documentation**: Keep README in sync

---

## Changelog

### Version 1.0.0 (2026-03-21)

**Added:**
- Initial design system release
- Child app color palette
- Parent app color palette
- Typography scale
- Spacing system
- Shadow definitions
- Animation tokens
- Tailwind CSS configuration
- JSON export for cross-platform

---

## Resources

- **Child App Design**: See `docs/design-system-child-app.md`
- **Parent App Design**: See `.moai/specs/SPEC-DESIGN-002/plan.md`
- **Design Tokens JSON**: `docs/design-system/tokens.json`
- **Tailwind Config**: `docs/design-system/tailwind.config.js`

---

**Maintained by**: BabyEco Design Team
**License**: Internal Use Only
