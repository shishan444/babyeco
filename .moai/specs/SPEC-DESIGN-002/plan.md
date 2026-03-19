# SPEC-DESIGN-002: Parent App Prototype Design

## Overview

Create comprehensive UI/UX prototype for the parent-facing application. This is the control center for managing children's behavioral incentive economy.

**Business Context**: The parent app is the primary interface for parents to configure tasks, manage rewards, approve check-ins, and monitor their children's progress. It must be efficient, trustworthy, and provide clear oversight.

**Target Users**:
- Primary: Parents of children aged 6-12
- Secondary: Guardians, caregivers

---

## Design Philosophy

### Parent-Centric Design Principles

| Principle | Application |
|-----------|-------------|
| Information Density | More data per screen, efficient scanning |
| Quick Actions | One-tap approvals, batch operations |
| Clear Status | Visual hierarchy for pending items |
| Trust Indicators | Confirmation dialogs, audit trails |
| Flexible Configuration | Customizable task/reward parameters |

### Parent Mental Model

**Core Needs**:
- Quick overview of children's status
- Easy task and reward management
- Timely notifications for approvals
- Progress insights and trends
- Control over child's digital experience

---

## User Flow Overview

### Core User Journeys

```
1. First-Time User
   Welcome → Create Family → Add Child → Configure Initial Tasks → Dashboard

2. Daily Usage
   Dashboard → View Pending Check-ins → Approve/Reject → View Progress

3. Task Management
   Dashboard → Task Center → Add/Edit Task → Configure Points → Save

4. Reward Configuration
   Dashboard → Reward Store → Add Item → Set Cost/Timer → Publish

5. Progress Monitoring
   Dashboard → Growth Report → Select Child → View Analytics → Export
```

---

## Screen Specifications

### 1. Welcome Screen

**Purpose**: Onboard new parents to the system

**Elements**:
- Logo with professional styling
- Value proposition headlines
- "Create Family" and "Join Existing" CTAs
- Brief feature highlights

**Copy Guidelines**:
- Title: "Build Better Habits Together"
- Subtitle: "The smart way to motivate your children"
- CTAs: "Create My Family" / "Have an invite?"

---

### 2. Family Setup Screen

**Purpose**: Create family account and initial configuration

**Elements**:
- Family name input
- Parent profile form (name, email, phone)
- Child addition form
- Invite code generation display
- Setup progress indicator

**Flow**:
1. Enter family name
2. Create parent account
3. Add child(ren) with basic info
4. Generate and display invite codes
5. Setup complete celebration

---

### 3. Parent Dashboard

**Purpose**: Central hub for daily management

**Layout**:
```
┌─────────────────────────────────────────────┐
│  Header                                     │
│  ┌─────────────────────────────────────────┐│
│  │ Family: Smith Family          [Settings]││
│  └─────────────────────────────────────────┘│
│                                              │
│  Pending Approvals (3)              [View All]│
│  ┌─────────────────────────────────────────┐│
│  │ Emma completed "Clean Room"  +15pts [✓][✗]│
│  └─────────────────────────────────────────┘│
│                                              │
│  Children Overview                          │
│  ┌────────────┐ ┌────────────┐              │
│  │ 👧 Emma    │ │ 👦 Jake    │              │
│  │ 340 pts    │ │ 220 pts    │              │
│  │ 85% done   │ │ 72% done   │              │
│  └────────────┘ └────────────┘              │
│                                              │
│  Quick Actions                              │
│  [+ Add Task] [+ Add Reward] [+ View Report]│
│                                              │
│  Bottom Navigation                          │
│  [Home][Tasks][Rewards][Reports][Settings]  │
└─────────────────────────────────────────────┘
```

**Elements**:
- Family name and quick settings
- Pending approvals queue with quick actions
- Children overview cards
- Quick action buttons
- Bottom navigation bar

---

### 4. Child Detail Screen

**Purpose**: View and manage individual child

**Elements**:
- Child profile header (avatar, name, age)
- Current point balance
- Streak status
- Weekly completion chart
- Active goals
- Recent activity log
- Quick actions (edit profile, view full report)

**Activity Log Entry**:
```
┌─────────────────────────────────────────────┐
│ ✓ Completed homework              +10 pts  │
│   Today, 4:30 PM                            │
├─────────────────────────────────────────────┤
│ 🎁 Redeemed screen time           -50 pts  │
│   Yesterday, 7:00 PM                        │
└─────────────────────────────────────────────┘
```

---

### 5. Task Management Screen

**Purpose**: Create and manage tasks

**Elements**:
- Task list with filters (by child, by type, by status)
- Add task FAB
- Task cards with edit/delete actions
- Batch operation toolbar

**Task Card Design**:
```
┌─────────────────────────────────────────────┐
│ 📚 Complete homework                        │
│ Assigned to: Emma, Jake                     │
│ +10 points • Daily • Due by 6:00 PM         │
│                                              │
│ [Edit] [Duplicate] [Delete]                 │
└─────────────────────────────────────────────┘
```

**Task Types**:
- Daily: Recurring every day
- Weekly: Recurring on specific days
- One-time: Single completion
- Family: Shared among siblings

---

### 6. Task Creation Modal

**Purpose**: Configure new or existing task

**Elements**:
- Task title input
- Description textarea
- Point value slider/input
- Task type selector
- Assign to children (multi-select)
- Time window configuration
- Recurrence settings
- Photo proof toggle
- Save/Cancel buttons

**Validation**:
- Title required (max 100 chars)
- Point value 1-100
- At least one child assigned

---

### 7. Reward Management Screen

**Purpose**: Configure exchange items

**Elements**:
- Reward categories (Timer, One-time, Quantity)
- Add reward FAB
- Reward cards with stock indicators
- Quick enable/disable toggle

**Reward Card Design**:
```
┌─────────────────────────────────────────────┐
│ 🎮 Screen Time 30min                        │
│ 100 points • Timer type                     │
│ Stock: Unlimited                            │
│                                              │
│ [Edit] [Disable] [View Usage]               │
└─────────────────────────────────────────────┘
```

**Reward Types**:
- Timer: Time-based (screen time, game time)
- One-time: Single use (movie night, outing)
- Quantity: Limited stock (toys, treats)

---

### 8. Approval Queue Screen

**Purpose**: Review and process pending check-ins

**Elements**:
- Pending items count badge
- Filter by child
- Sort by time (newest/oldest)
- Quick approve all button (with confirmation)
- Individual approval cards

**Approval Card**:
```
┌─────────────────────────────────────────────┐
│ Emma checked in:                            │
│ "Cleaned my room" 📸 [View Photo]           │
│                                              │
│ Task: Clean bedroom                         │
│ Points: +15                                 │
│ Time: 5 minutes ago                         │
│                                              │
│ [Approve] [Reject] [Ask for Proof]          │
└─────────────────────────────────────────────┘
```

**Actions**:
- Approve: Award points, notify child
- Reject: No points, optional reason
- Ask for Proof: Request additional evidence

---

### 9. Growth Report Screen

**Purpose**: View analytics and trends

**Elements**:
- Child selector
- Date range picker
- Key metrics cards
- Trend charts
- Export button

**Metrics Cards**:
```
┌───────────┐ ┌───────────┐ ┌───────────┐
│ Tasks     │ │ Points    │ │ Streak    │
│ Completed │ │ Earned    │ │ Days      │
│           │ │           │ │           │
│    45     │ │   450     │ │    7      │
│  ↑ 12%    │ │  ↑ 8%     │ │  Best!    │
└───────────┘ └───────────┘ └───────────┘
```

**Charts**:
- Daily task completion trend (7/30 days)
- Point earning vs spending trend
- Category breakdown (pie chart)
- Weekly comparison

---

### 10. Settings Screen

**Purpose**: Configure family and account settings

**Elements**:
- Family profile section
- Member management
- Notification preferences
- Approval settings
- AI content settings
- Help & support
- Account security

**Sections**:
```
┌─────────────────────────────────────────────┐
│ Family Settings                             │
│ ├─ Family Name                              │
│ ├─ Invite Codes                             │
│ └─ Timezone                                 │
│                                              │
│ Children                                    │
│ ├─ Emma (Manage)                            │
│ └─ Jake (Manage)                            │
│                                              │
│ Approval Settings                           │
│ ├─ Auto-approve after: [Off/1hr/6hr]       │
│ ├─ Require photo for tasks over: [pts]     │
│ └─ Notification: [Push/Email/Both]          │
│                                              │
│ AI Settings                                 │
│ ├─ Content filtering: [Strict/Moderate]    │
│ └─ Daily question limit: [5/10/Unlimited]  │
└─────────────────────────────────────────────┘
```

---

### 11. Child Profile Management

**Purpose**: Configure individual child settings

**Elements**:
- Basic info (name, birthdate, avatar)
- Device binding status
- Point adjustment (manual add/deduct)
- Task assignments
- Reward restrictions
- Daily limits

---

## Color Palette (Parent App)

### Primary Colors

```css
--parent-primary: #4F46E5;      /* Indigo - main actions */
--parent-secondary: #7C3AED;    /* Purple - secondary actions */
--parent-accent: #10B981;       /* Green - success/approval */
--parent-warning: #F59E0B;      /* Amber - attention */
--parent-danger: #EF4444;       /* Red - reject/delete */
```

### Background Colors

```css
--parent-bg-primary: #F9FAFB;   /* Light gray */
--parent-bg-secondary: #FFFFFF; /* White cards */
--parent-bg-overlay: rgba(0, 0, 0, 0.5); /* Modal overlay */
```

### Text Colors

```css
--parent-text-primary: #111827;   /* Near black */
--parent-text-secondary: #6B7280; /* Medium gray */
--parent-text-muted: #9CA3AF;     /* Light gray */
--parent-text-inverse: #FFFFFF;   /* White */
```

---

## Typography

### Font Family

```css
--font-display: 'Inter', sans-serif;  /* Headings */
--font-body: 'Inter', sans-serif;      /* Body text */
```

### Type Scale

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| Heading 1 | 28px | 700 | 1.2 |
| Heading 2 | 22px | 600 | 1.3 |
| Heading 3 | 18px | 600 | 1.4 |
| Body Large | 16px | 500 | 1.5 |
| Body | 14px | 400 | 1.5 |
| Body Small | 13px | 400 | 1.5 |
| Caption | 12px | 500 | 1.4 |

---

## Component Library

### Button Variants

```tsx
// Primary Button
<Button variant="primary" size="md">
  Save Changes
</Button>

// Approval Button
<Button variant="success" size="sm">
  Approve
</Button>

// Danger Button
<Button variant="danger" size="sm">
  Reject
</Button>

// Ghost Button
<Button variant="ghost" size="md">
  Cancel
</Button>
```

### Card Components

```tsx
// Child Card
<ChildCard
  name="Emma"
  points={340}
  completionRate={85}
  onClick={() => navigate('/child/emma')}
/>

// Task Card
<TaskCard
  title="Complete homework"
  points={10}
  assignees={['Emma', 'Jake']}
  onEdit={handleEdit}
  onDelete={handleDelete}
/>

// Approval Card
<ApprovalCard
  childName="Emma"
  taskName="Clean bedroom"
  points={15}
  timestamp={Date.now()}
  photoUrl="/photo.jpg"
  onApprove={handleApprove}
  onReject={handleReject}
/>
```

---

## Accessibility Guidelines

### WCAG 2.1 AA Compliance

| Requirement | Implementation |
|-------------|----------------|
| Color Contrast | Minimum 4.5:1 for text |
| Touch Targets | Minimum 44x44px |
| Text Scaling | Support up to 200% |
| Screen Reader | All elements labeled |
| Focus Indicators | Visible focus rings |
| Motion | Respect prefers-reduced-motion |

---

## Responsive Design

### Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 640px | Single column |
| Tablet | 640-1024px | Two column |
| Desktop | > 1024px | Multi-column with sidebar |

### Mobile Optimizations

- Bottom navigation for easy thumb access
- Swipe actions on cards (approve/reject)
- Pull-to-refresh on lists
- Collapsible sections

---

## Prototyping Deliverables

### Wireframes
- [ ] All 11 core screens
- [ ] Error states
- [ ] Loading states
- [ ] Empty states

### High-Fidelity Designs
- [ ] All screens in final colors
- [ ] All component states
- [ ] Responsive layouts

### Interaction Specifications
- [ ] Micro-interactions documented
- [ ] Page transitions defined
- [ ] Loading animations

### Developer Handoff
- [ ] Design tokens JSON
- [ ] Asset exports
- [ ] Accessibility notes

---

## Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| SPEC-DESIGN-001 | Completed | Shared design system |
| SPEC-DESIGN-003 | Parallel | Design system规范 |
| Figma license | Required | Design tool |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Information overload | Medium | Medium | Progressive disclosure, clear hierarchy |
| Mobile-first vs Desktop | Medium | Low | Responsive design from start |
| Approval bottleneck | High | Medium | Auto-approve option, batch actions |

---

## Acceptance Criteria

### Design Quality
- [ ] All 11 core screens designed
- [ ] Consistent design language
- [ ] WCAG 2.1 AA accessibility compliance
- [ ] Responsive layouts for mobile/tablet/desktop

### User Validation
- [ ] User testing with 5+ parents completed
- [ ] Task completion rate >= 90%
- [ ] No critical usability issues

### Developer Handoff
- [ ] Figma file organized and shared
- [ ] Design tokens exported
- [ ] Component states defined

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-DESIGN-001 | Parallel | Child app design |
| SPEC-DESIGN-003 | Downstream | Design system based on both apps |
| SPEC-FE-AUTH-001 | Downstream | Implements parent auth UI |
| SPEC-FE-PARENT-001 | Downstream | Implements parent features |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
