# BabyEco SPEC Overview

## Project Summary

**Project Name**: BabyEco - Children's Behavioral Incentive Economy System
**Description**: A point-based economy system where parents set rules and children participate autonomously, using gamification to replace coercive discipline and cultivate children's self-discipline and goal management skills.
**Architecture**: Dual mobile apps (Parent + Child) + Backend API
**Development Approach**: Design-First + Frontend-First

---

## Development Philosophy

### Design-First Approach

All development starts with UI/UX prototype design:

1. **Prototype Design Phase**: Create wireframes, user flows, and interaction patterns before any code
2. **Design System**: Establish visual language, component library, and animation standards
3. **Frontend Implementation**: Build UI based on approved prototypes with mock data
4. **Backend API Development**: Design APIs based on frontend data requirements
5. **Integration**: Connect frontend to real backend APIs

### Why Frontend-First?

| Benefit | Description |
|---------|-------------|
| User Validation | Validate UX with real prototypes before backend investment |
| Clear Contracts | Frontend mock data defines the API contracts |
| Parallel Work | Designers and frontend developers can work independently |
| Faster Iteration | UI changes don't require backend modifications |

---

## SPEC Priority Matrix

### Phase 1: Prototype Design (Design-First)

| Priority | SPEC ID | Title | Effort |
|----------|---------|-------|--------|
| P0 | SPEC-DESIGN-001 | Child App Prototype Design | L |
| P0 | SPEC-DESIGN-002 | Parent App Prototype Design | L |
| P0 | SPEC-DESIGN-003 | Design System Specification | M |

### Phase 2: Frontend Implementation (Frontend-First)

| Priority | SPEC ID | Title | App | Effort |
|----------|---------|-------|-----|--------|
| P0 | SPEC-FE-AUTH-001 | Parent Authentication Module | Parent | M |
| P0 | SPEC-FE-AUTH-002 | Child Authentication Module | Child | M |
| P0 | SPEC-FE-TASK-001 | Task System UI | Child | L |
| P0 | SPEC-FE-POINT-001 | Point System UI | Child | M |
| P0 | SPEC-FE-EXCHANGE-001 | Exchange Center UI | Child | M |
| P0 | SPEC-FE-PARENT-001 | Parent Core Features | Parent | L |
| P1 | SPEC-FE-GROWTH-001 | Growth Dashboard | Child | M |
| P1 | SPEC-FE-ENTERTAIN-001 | Entertainment Module | Child | L |
| P1 | SPEC-FE-AI-001 | AI Q&A Interface | Child | M |

### Phase 3: Backend API Development (API-First Design)

| Priority | SPEC ID | Title | Effort |
|----------|---------|-------|--------|
| P0 | SPEC-BE-AUTH-001 | Authentication & Account API | M |
| P0 | SPEC-BE-TASK-001 | Task System API | L |
| P0 | SPEC-BE-POINT-001 | Point System API | L |
| P0 | SPEC-BE-EXCHANGE-001 | Exchange Center API | M |
| P1 | SPEC-BE-ENTERTAIN-001 | Entertainment Content API | L |
| P1 | SPEC-BE-AI-001 | AI Q&A API | M |
| P1 | SPEC-BE-REPORT-001 | Report & Analytics API | M |

### Phase 4: Integration & Optimization

| Priority | SPEC ID | Title | Effort |
|----------|---------|-------|--------|
| P0 | SPEC-INTEGRATION-001 | Frontend-Backend Integration | L |
| P0 | SPEC-ONBOARD-001 | Onboarding Flow | M |
| P1 | SPEC-PERF-001 | Performance Optimization | M |

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────┐
│                  PHASE 1: Prototype Design                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   SPEC-DESIGN-001 ─────┬─────────────────────────────────────────┐  │
│   (Child App)          │                                         │  │
│                        │                                         │  │
│   SPEC-DESIGN-002 ─────┼─────────────────────────────────────────┤  │
│   (Parent App)         │                                         │  │
│                        │                                         │  │
│   SPEC-DESIGN-003 ─────┴─────────────────────────────────────────┘  │
│   (Design System)                                                   │
│                                                                      │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
              ┌────────────────────────┴────────────────────────┐
              │                                                  │
┌─────────────▼──────────────────────────────────────────────────▼─────┐
│                  PHASE 2: Frontend Implementation                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   SPEC-FE-AUTH-001 ──────────────────┐                              │
│   (Parent Auth)                      │                              │
│                                      │                              │
│   SPEC-FE-AUTH-002 ──────────────────┤                              │
│   (Child Auth)                       │                              │
│                                      │                              │
│   SPEC-FE-TASK-001 ──────────────────┤     SPEC-FE-PARENT-001      │
│   (Task UI)                          │     (Parent Core)           │
│                                      │                              │
│   SPEC-FE-POINT-001 ─────────────────┤                              │
│   (Point UI)                         │                              │
│                                      │                              │
│   SPEC-FE-EXCHANGE-001 ──────────────┘                              │
│   (Exchange UI)                                                     │
│                                                                      │
│   SPEC-FE-GROWTH-001 ──────┬─────────────────────────────────────── │
│   (Growth Dashboard)       │                                        │
│                            │     SPEC-FE-ENTERTAIN-001             │
│   SPEC-FE-AI-001 ──────────┴─────────────────────────────────────── │
│   (AI Q&A)                  (Entertainment)                        │
│                                                                      │
└──────────────────────────────────────┬───────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────┐
│                  PHASE 3: Backend API Development                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   SPEC-BE-AUTH-001 ──────────────────┐                              │
│   (Auth API)                         │                              │
│                                      │                              │
│   SPEC-BE-TASK-001 ──────────────────┤                              │
│   (Task API)                         │                              │
│                                      │                              │
│   SPEC-BE-POINT-001 ─────────────────┤                              │
│   (Point API)                        │                              │
│                                      │                              │
│   SPEC-BE-EXCHANGE-001 ──────────────┤                              │
│   (Exchange API)                     │                              │
│                                      │                              │
│   SPEC-BE-ENTERTAIN-001 ─────────────┤                              │
│   (Entertainment API)                │                              │
│                                      │                              │
│   SPEC-BE-AI-001 ────────────────────┤                              │
│   (AI Q&A API)                       │                              │
│                                      │                              │
│   SPEC-BE-REPORT-001 ────────────────┘                              │
│   (Report API)                                                      │
│                                                                      │
└──────────────────────────────────────┬───────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────┐
│                  PHASE 4: Integration & Optimization                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   SPEC-INTEGRATION-001 ──────────────┐                              │
│   (Frontend-Backend Integration)     │                              │
│                                      │                              │
│   SPEC-ONBOARD-001 ──────────────────┤                              │
│   (Onboarding Flow)                  │                              │
│                                      │                              │
│   SPEC-PERF-001 ─────────────────────┘                              │
│   (Performance Optimization)                                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Detailed SPEC Descriptions

### Phase 1: Prototype Design (Weeks 1-3)

#### SPEC-DESIGN-001: Child App Prototype Design

**Status**: Planned
**Dependencies**: None
**Description**: Create comprehensive UI/UX prototype for the child-facing application.

**Deliverables**:
- User flow diagrams for all child-facing features
- Wireframes for core screens (home, tasks, points, exchange, entertainment)
- Interaction patterns and micro-animations
- Touch gesture specifications for 6-12 age group
- Accessibility considerations for cognitive development

**Key Screens**:
1. Welcome & Device Binding
2. Home Dashboard (Task Overview)
3. Task Detail & Check-in
4. Point Balance & History
5. Exchange Center & Wishlist
6. Entertainment Hub
7. Reading Module & Q&A
8. Growth Dashboard
9. AI Q&A Chat
10. Settings & Profile

---

#### SPEC-DESIGN-002: Parent App Prototype Design

**Status**: Planned
**Dependencies**: None (parallel with SPEC-DESIGN-001)
**Description**: Create comprehensive UI/UX prototype for the parent-facing application.

**Deliverables**:
- User flow diagrams for parent management features
- Wireframes for core screens (dashboard, tasks, children, reports)
- Approval workflow interfaces
- Monitoring and alert designs
- Efficient workflows for busy parents

**Key Screens**:
1. Registration & Login
2. Child Profile Management
3. Task Management (CRUD)
4. Point Model Configuration
5. Approval Center (unified pending items)
6. Exchange Item Management
7. Entertainment Content Upload
8. Reports & Analytics
9. Notification Settings
10. Growth Dashboard Mirror View

---

#### SPEC-DESIGN-003: Design System Specification

**Status**: Planned
**Dependencies**: SPEC-DESIGN-001, SPEC-DESIGN-002
**Description**: Establish the unified design system for both apps.

**Deliverables**:
- Color palette (warm/vibrant for child, clean/efficient for parent)
- Typography scale with accessibility considerations
- Component library specifications (shadcn/ui + Radix UI)
- Animation guidelines (GSAP + Framer Motion)
- Icon set and illustration style
- Spacing and layout grid
- Accessibility guidelines for 6-12 cognitive range

**Design Tokens**:
```yaml
# Child App Colors
child_primary: "#FF6B6B"    # Warm coral
child_secondary: "#4ECDC4"  # Teal accent
child_success: "#95E1A3"    # Achievement green
child_background: "#FFF9F0" # Warm cream

# Parent App Colors
parent_primary: "#5B6B8C"   # Professional blue-gray
parent_secondary: "#8B5CF6" # Purple accent
parent_success: "#10B981"   # Success green
parent_background: "#F8FAFC" # Clean white

# Animation
duration_fast: "150ms"
duration_normal: "300ms"
duration_slow: "500ms"
easing_default: "cubic-bezier(0.4, 0, 0.2, 1)"
```

---

### Phase 2: Frontend Implementation (Weeks 4-10)

#### SPEC-FE-AUTH-001: Parent Authentication Module

**Status**: Planned
**Dependencies**: SPEC-DESIGN-002, SPEC-DESIGN-003
**Description**: Implement parent registration, login, and profile management UI.

**Key Components**:
- Registration form with validation
- Login form with error handling
- Profile editing interface
- Password reset flow (UI only, mock data)
- Token management in Zustand store

**Technical Stack**:
- Next.js 22 App Router
- React Hook Form + Zod validation
- Zustand for auth state
- Secure token storage

---

#### SPEC-FE-AUTH-002: Child Authentication Module

**Status**: Planned
**Dependencies**: SPEC-DESIGN-001, SPEC-DESIGN-003
**Description**: Implement child device binding and authentication UI.

**Key Components**:
- Welcome screen with brand introduction
- Invite code input with validation
- Device binding confirmation
- Profile display after binding
- Child-friendly error messages

**Age-Appropriate Design**:
- Large touch targets (min 48px)
- Clear visual feedback
- Simple, encouraging copy
- Progress indication for async operations

---

#### SPEC-FE-TASK-001: Task System UI

**Status**: Planned
**Dependencies**: SPEC-DESIGN-001, SPEC-DESIGN-003
**Description**: Implement the complete task management interface for children.

**Key Features**:
- Task list with categories and filters
- Task detail view with instructions
- Check-in button with confirmation
- Streak counter with celebration animation
- Task completion celebration (confetti, sounds)
- Task history view

**Animation Requirements**:
- Task card entrance animations
- Check-in button micro-interactions
- Celebration effects (GSAP + Framer Motion)
- Smooth list transitions

---

#### SPEC-FE-POINT-001: Point System UI

**Status**: Planned
**Dependencies**: SPEC-DESIGN-001, SPEC-DESIGN-003
**Description**: Implement point balance and transaction history UI.

**Key Features**:
- Animated point balance display
- Earning vs spending visualization
- Transaction history list
- Point health indicator
- Achievement notifications

**Visual Feedback**:
- Point gain animation (number increment)
- Point deduction warning
- Progress toward goals
- Milestone celebration

---

#### SPEC-FE-EXCHANGE-001: Exchange Center UI

**Status**: Planned
**Dependencies**: SPEC-DESIGN-001, SPEC-DESIGN-003
**Description**: Implement the exchange center and wishlist interface.

**Key Features**:
- Exchange item gallery
- Wishlist submission form
- Pinned goal with progress bar
- Timer display for time-based benefits
- Fulfillment status tracking
- Exchange history

**Interaction Patterns**:
- Item card hover/tap states
- Wishlist form validation
- Progress bar animation
- Timer countdown display

---

#### SPEC-FE-PARENT-001: Parent Core Features

**Status**: Planned
**Dependencies**: SPEC-DESIGN-002, SPEC-DESIGN-003
**Description**: Implement parent-facing management features.

**Key Features**:
- Child profile CRUD
- Task management (create, edit, delete)
- Point model configuration
- Unified approval center
- Deduction interface
- Completion rate monitoring
- Notification settings

**UX Priorities**:
- Efficient workflows for busy parents
- Batch operations where possible
- Clear status indicators
- Quick actions on dashboard

---

#### SPEC-FE-GROWTH-001: Growth Dashboard

**Status**: Planned
**Dependencies**: SPEC-DESIGN-001, SPEC-DESIGN-003
**Description**: Implement the child-facing growth dashboard.

**Key Features**:
- Point overview (balance + total)
- Current goal progress
- Task completion statistics
- Transaction history
- Milestone timeline
- Share cards for achievements

---

#### SPEC-FE-ENTERTAIN-001: Entertainment Module

**Status**: Planned
**Dependencies**: SPEC-DESIGN-001, SPEC-DESIGN-003
**Description**: Implement entertainment content and reading module UI.

**Key Features**:
- Content gallery with categories
- Content player (eBook viewer)
- Reading module with AI Q&A
- Progress tracking
- Point spending/earning display

**Reading Module Specifics**:
- Socratic dialogue interface
- Hint mode activation
- Score display after completion
- Single reading report view

---

#### SPEC-FE-AI-001: AI Q&A Interface

**Status**: Planned
**Dependencies**: SPEC-DESIGN-001, SPEC-DESIGN-003
**Description**: Implement the AI Q&A chat interface.

**Key Features**:
- Chat interface with message bubbles
- Quick question suggestions
- Typing indicator
- Message history
- Child-friendly AI responses

---

### Phase 3: Backend API Development (Weeks 11-16)

#### SPEC-BE-AUTH-001: Authentication & Account API

**Status**: Planned
**Dependencies**: Phase 2 frontend implementations (API contracts defined by mock data)
**Description**: Implement authentication and account management APIs.

**Endpoints**:
- POST `/api/v1/auth/register` - Parent registration
- POST `/api/v1/auth/login` - Parent login
- POST `/api/v1/auth/logout` - Logout
- POST `/api/v1/auth/refresh` - Token refresh
- POST `/api/v1/children` - Child profile CRUD
- POST `/api/v1/child/bind` - Device binding

**Technical Stack**:
- FastAPI (Python)
- SQLAlchemy 2.0
- JWT authentication (RS256)
- bcrypt password hashing
- PostgreSQL database

---

#### SPEC-BE-TASK-001: Task System API

**Status**: Planned
**Dependencies**: SPEC-BE-AUTH-001
**Description**: Implement task management APIs.

**Endpoints**:
- GET/POST/PATCH/DELETE `/api/v1/tasks`
- POST `/api/v1/tasks/{id}/checkin`
- PATCH `/api/v1/checkins/{id}/approve`
- GET `/api/v1/tasks/stats`

---

#### SPEC-BE-POINT-001: Point System API

**Status**: Planned
**Dependencies**: SPEC-BE-AUTH-001, SPEC-BE-TASK-001
**Description**: Implement point account and transaction APIs.

**Endpoints**:
- GET `/api/v1/points/balance`
- GET `/api/v1/points/history`
- POST `/api/v1/points/deduct`

---

#### SPEC-BE-EXCHANGE-001: Exchange Center API

**Status**: Planned
**Dependencies**: SPEC-BE-AUTH-001, SPEC-BE-POINT-001
**Description**: Implement exchange center APIs.

**Endpoints**:
- GET/POST `/api/v1/exchanges`
- POST `/api/v1/wishlist`
- PATCH `/api/v1/exchanges/{id}/fulfill`

---

#### SPEC-BE-ENTERTAIN-001: Entertainment Content API

**Status**: Planned
**Dependencies**: SPEC-BE-AUTH-001, SPEC-BE-POINT-001
**Description**: Implement entertainment and reading module APIs.

**Endpoints**:
- GET `/api/v1/content`
- POST `/api/v1/content/{id}/unlock`
- POST `/api/v1/reading/{id}/qa`
- POST `/api/v1/reading/{id}/complete`

---

#### SPEC-BE-AI-001: AI Q&A API

**Status**: Planned
**Dependencies**: SPEC-BE-AUTH-001
**Description**: Implement AI Q&A APIs.

**Endpoints**:
- POST `/api/v1/ai/chat`
- GET `/api/v1/ai/history`

---

#### SPEC-BE-REPORT-001: Report & Analytics API

**Status**: Planned
**Dependencies**: All core backend SPECs
**Description**: Implement reporting and analytics APIs.

**Endpoints**:
- GET `/api/v1/reports/weekly`
- GET `/api/v1/reports/monthly`
- GET `/api/v1/reports/growth`

---

### Phase 4: Integration & Optimization (Weeks 17-20)

#### SPEC-INTEGRATION-001: Frontend-Backend Integration

**Status**: Planned
**Dependencies**: All Phase 2 & Phase 3 SPECs
**Description**: Connect frontend implementations to real backend APIs.

**Tasks**:
- Replace mock data with API calls
- Implement error handling
- Add loading states
- Configure API client
- Test end-to-end flows

---

#### SPEC-ONBOARD-001: Onboarding Flow

**Status**: Planned
**Dependencies**: SPEC-INTEGRATION-001
**Description**: Implement the 5-step cold start onboarding flow.

**Flow Steps**:
1. Create child profile (name/age/avatar)
2. Select 3 age-appropriate task templates
3. Review default point model
4. Generate invite code, child binds device
5. Child completes first task check-in

---

#### SPEC-PERF-001: Performance Optimization

**Status**: Planned
**Dependencies**: SPEC-INTEGRATION-001
**Description**: Optimize application performance.

**Focus Areas**:
- Bundle size optimization
- Image optimization
- API response caching
- Animation performance
- Loading time reduction

---

## Migration from Old Structure

### Old vs New Comparison

| Aspect | Old Structure | New Structure |
|--------|--------------|---------------|
| Start Point | Backend infrastructure | UI/UX prototype design |
| Development Order | Backend first, then frontend | Frontend first, then backend |
| API Design | Backend-driven | Frontend-driven (mock data defines contracts) |
| Validation | Late (after backend ready) | Early (prototype testing) |
| Parallel Work | Limited | Design, frontend, backend can overlap |

### SPEC ID Mapping

| Old SPEC ID | New SPEC ID(s) | Notes |
|-------------|----------------|-------|
| SPEC-AUTH-001 | SPEC-DESIGN-001/002 → SPEC-FE-AUTH-001/002 → SPEC-BE-AUTH-001 | Split into design, frontend, backend |
| SPEC-DB-001 | Merged into SPEC-BE-AUTH-001 | Database design part of backend API |
| SPEC-TASK-001 | SPEC-FE-TASK-001 → SPEC-BE-TASK-001 | Frontend before backend |
| SPEC-POINT-001 | SPEC-FE-POINT-001 → SPEC-BE-POINT-001 | Frontend before backend |
| SPEC-EXCHANGE-001 | SPEC-FE-EXCHANGE-001 → SPEC-BE-EXCHANGE-001 | Frontend before backend |
| SPEC-ENTERTAIN-001 | SPEC-FE-ENTERTAIN-001 → SPEC-BE-ENTERTAIN-001 | Frontend before backend |
| SPEC-GROWTH-001 | SPEC-FE-GROWTH-001 | Primarily frontend, uses existing APIs |
| SPEC-AI-001 | SPEC-FE-AI-001 → SPEC-BE-AI-001 | Frontend before backend |
| SPEC-ONBOARD-001 | SPEC-ONBOARD-001 (Phase 4) | Moved to integration phase |
| SPEC-PARENT-001 | SPEC-FE-PARENT-001 | Primarily frontend |
| (New) | SPEC-DESIGN-001/002/003 | Design phase SPECs |
| (New) | SPEC-INTEGRATION-001 | Integration phase SPEC |
| (New) | SPEC-PERF-001 | Performance optimization SPEC |
| (New) | SPEC-BE-REPORT-001 | Backend report API SPEC |

### Dependency Changes

**Old Dependency Chain**:
```
AUTH → DB → TASK → POINT → EXCHANGE → Extensions
```

**New Dependency Chain**:
```
Design → Frontend (parallel) → Backend (parallel) → Integration
```

The new structure allows:
- Designers to work on prototypes while developers prepare
- Frontend developers to build with mock data
- Backend developers to implement APIs based on frontend contracts
- Final integration connects everything together

---

## Technical Stack Reference

| Layer | Technology |
|-------|------------|
| Frontend Framework | Next.js 22 (App Router) |
| Styling | Tailwind CSS + CSS Variables |
| UI Components | shadcn/ui + Radix UI |
| Animation | GSAP 3 + Framer Motion + React Spring |
| State Management | Zustand |
| Form Handling | React Hook Form + Zod |
| Backend Framework | FastAPI (Python) |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL (production) / SQLite (development) |
| Authentication | JWT (RS256) |
| Password Hashing | bcrypt |

---

## Risk Assessment

| Risk Area | Risk | Mitigation |
|-----------|------|------------|
| Design-Dev Alignment | Designs don't translate to code | Regular design reviews, component-first approach |
| Mock Data Accuracy | Mock data doesn't match real API | Define contracts early, validate in integration phase |
| Scope Creep | Too many features in prototype | Stick to MVP scope, defer nice-to-haves |
| Animation Performance | Over-engineered animations | Profile early, use will-change, test on low-end devices |
| Accessibility | 6-12 age range needs vary | Test with age-appropriate users, provide modes |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-03-19 | Initial SPEC breakdown (backend-first) |
| 2.0 | 2024-03-19 | Restructured to Design-First + Frontend-First approach |

---

**Maintained by**: BabyEco Development Team
**Last Updated**: 2024-03-19
