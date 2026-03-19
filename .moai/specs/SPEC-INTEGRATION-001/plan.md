# SPEC-INTEGRATION-001: Frontend-Backend Integration Testing

## Overview

Define integration testing strategy and test cases for BabyEco's frontend-backend communication.

**Business Context**: Integration tests verify that frontend applications correctly communicate with backend APIs, ensuring data flows correctly and edge cases are handled.

**Target Users**:
- Primary: Development team
- Secondary: QA engineers

---

## Technical Constraints

### Framework and Versions
- Playwright for E2E testing
- Vitest for integration tests
- MSW (Mock Service Worker) for API mocking

### Dependencies
- All FE SPECs completed
- All BE SPECs completed

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: All API endpoints shall have corresponding integration tests.

```
Given an API endpoint exists
When integration tests are written
Then request/response is verified
And error cases are covered
```

**UR-002**: All user flows shall have E2E test coverage.

```
Given a critical user flow exists
When E2E tests are written
Then the complete flow is tested
And assertions verify expected outcomes
```

**UR-003**: Tests shall run in CI/CD pipeline.

```
Given code is pushed
When CI runs
Then all integration tests execute
And failures block deployment
```

### Event-Driven Requirements

**EDR-001**: When authentication fails, tests shall verify proper error handling.

```
Given invalid credentials
When login attempted
Then frontend displays error
And no session is created
```

**EDR-002**: When API returns error, tests shall verify error state UI.

```
Given API returns 500
When frontend receives response
Then error state is displayed
And retry option is available
```

**EDR-003**: When network is offline, tests shall verify offline behavior.

```
Given network is disconnected
When user interacts
Then offline indicator shows
And cached data is used where possible
```

### State-Driven Requirements

**SDR-001**: While tests are running, test data shall be isolated.

```
Given integration tests execute
When tests run
Then test database is used
And data is cleaned between tests
```

**SDR-002**: While E2E tests run, browser contexts shall be isolated.

```
Given E2E tests execute
When browser sessions run
Then each test has clean state
And no cross-test contamination
```

---

## Technical Solution

### Test Categories

```yaml
Integration Tests:
  - API contract tests
  - Authentication flow
  - Task management flow
  - Point system flow
  - Exchange flow
  - Entertainment flow
  - AI chat flow
  - Report generation

E2E Tests:
  - Parent registration and setup
  - Child device binding
  - Complete task flow (create -> assign -> check-in -> approve)
  - Point earning and spending
  - Reward redemption (including timer)
  - Content reading and questions
  - AI Q&A interaction

Performance Tests:
  - API response time benchmarks
  - Concurrent user simulation
  - Load testing critical endpoints
```

### Test Structure

```
tests/
├── integration/
│   ├── auth/
│   │   ├── parent-auth.test.ts
│   │   └── child-auth.test.ts
│   ├── tasks/
│   │   ├── task-crud.test.ts
│   │   ├── check-in-flow.test.ts
│   │   └── approval-flow.test.ts
│   ├── points/
│   │   ├── balance.test.ts
│   │   └── transactions.test.ts
│   ├── exchange/
│   │   ├── rewards.test.ts
│   │   ├── redemption.test.ts
│   │   └── timer.test.ts
│   ├── entertainment/
│   │   ├── content.test.ts
│   │   └── questions.test.ts
│   ├── ai/
│   │   ├── chat.test.ts
│   │   └── content-filter.test.ts
│   └── reports/
│       ├── growth.test.ts
│       └── exports.test.ts
├── e2e/
│   ├── parent/
│   │   ├── registration.spec.ts
│   │   ├── family-setup.spec.ts
│   │   ├── task-management.spec.ts
│   │   └── approvals.spec.ts
│   ├── child/
│   │   ├── device-binding.spec.ts
│   │   ├── task-completion.spec.ts
│   │   ├── point-tracking.spec.ts
│   │   ├── reward-redemption.spec.ts
│   │   ├── content-reading.spec.ts
│   │   └── ai-chat.spec.ts
│   └── flows/
│       ├── complete-task-cycle.spec.ts
│       ├── point-earn-spend.spec.ts
│       └── family-onboarding.spec.ts
└── performance/
    ├── api-benchmarks.test.ts
    └── load-testing.test.ts
```

### Test Fixtures

```typescript
// fixtures/auth.ts
export const testFixtures = {
  parentUser: {
    email: 'test-parent@example.com',
    password: 'TestPassword123!',
    name: 'Test Parent',
    familyName: 'Test Family',
  },

  childUser: {
    name: 'Test Child',
    birthDate: '2015-01-01',
  },

  inviteCode: 'ABC123',
};

// fixtures/tasks.ts
export const taskFixtures = {
  dailyTask: {
    title: 'Test Daily Task',
    points: 10,
    type: 'daily',
    assigneeIds: [],
  },

  weeklyTask: {
    title: 'Test Weekly Task',
    points: 20,
    type: 'weekly',
    daysOfWeek: [1, 2, 3, 4, 5], // Mon-Fri
  },
};

// fixtures/rewards.ts
export const rewardFixtures = {
  oneTimeReward: {
    name: 'Test Reward',
    cost: 50,
    type: 'one-time',
  },

  timerReward: {
    name: 'Screen Time 30min',
    cost: 100,
    type: 'timer',
    durationMinutes: 30,
  },
};
```

### Integration Test Examples

```typescript
// integration/tasks/check-in-flow.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { createTestClient } from '../helpers/client';
import { setupTestDatabase, cleanupTestDatabase } from '../helpers/db';

describe('Task Check-in Flow', () => {
  let parentClient: TestClient;
  let childClient: TestClient;
  let childId: string;
  let taskId: string;

  beforeEach(async () => {
    await setupTestDatabase();

    // Create parent and child
    const { parent, child, tokens } = await createTestFamily();
    parentClient = createTestClient(tokens.parent);
    childClient = createTestClient(tokens.child);
    childId = child.id;

    // Create a task
    const task = await parentClient.post('/api/v1/tasks', {
      title: 'Test Task',
      points: 10,
      type: 'daily',
      assigneeIds: [childId],
    });
    taskId = task.body.id;
  });

  afterEach(async () => {
    await cleanupTestDatabase();
  });

  it('should allow child to check in on task', async () => {
    // Get task instances for today
    const instances = await childClient.get('/api/v1/child/tasks');
    const instance = instances.body.find((i) => i.task.id === taskId);

    expect(instance).toBeDefined();
    expect(instance.status).toBe('pending');

    // Check in
    const checkIn = await childClient.post(
      `/api/v1/child/tasks/${instance.id}/checkin`,
      {}
    );

    expect(checkIn.status).toBe(201);
    expect(checkIn.body.status).toBe('pending'); // Awaiting approval
  });

  it('should prevent duplicate check-ins', async () => {
    const instances = await childClient.get('/api/v1/child/tasks');
    const instance = instances.body.find((i) => i.task.id === taskId);

    // First check-in
    await childClient.post(`/api/v1/child/tasks/${instance.id}/checkin`, {});

    // Second check-in should fail
    const result = await childClient.post(
      `/api/v1/child/tasks/${instance.id}/checkin`,
      {}
    );

    expect(result.status).toBe(400);
    expect(result.body.error).toContain('already checked in');
  });

  it('should award points when parent approves', async () => {
    // Child checks in
    const instances = await childClient.get('/api/v1/child/tasks');
    const instance = instances.body.find((i) => i.task.id === taskId);
    const checkIn = await childClient.post(
      `/api/v1/child/tasks/${instance.id}/checkin`,
      {}
    );

    // Get initial balance
    const beforeBalance = await childClient.get('/api/v1/child/points/balance');

    // Parent approves
    const approval = await parentClient.post(
      `/api/v1/approvals/${checkIn.body.id}/approve`
    );

    expect(approval.status).toBe(200);
    expect(approval.body.points_awarded).toBe(10);

    // Check balance increased
    const afterBalance = await childClient.get('/api/v1/child/points/balance');
    expect(afterBalance.body.balance).toBe(beforeBalance.body.balance + 10);
  });
});
```

### E2E Test Examples

```typescript
// e2e/flows/complete-task-cycle.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Complete Task Cycle', () => {
  test('parent creates task, child completes, parent approves', async ({
    browser,
  }) => {
    // Create isolated contexts
    const parentContext = await browser.newContext();
    const childContext = await browser.newContext();
    const parentPage = await parentContext.newPage();
    const childPage = await childContext.newPage();

    // Parent: Login
    await parentPage.goto('/login');
    await parentPage.fill('[name="email"]', 'parent@test.com');
    await parentPage.fill('[name="password"]', 'password');
    await parentPage.click('button[type="submit"]');
    await expect(parentPage).toHaveURL('/dashboard');

    // Parent: Create task
    await parentPage.click('text=Add Task');
    await parentPage.fill('[name="title"]', 'Complete homework');
    await parentPage.fill('[name="points"]', '15');
    await parentPage.click('button:has-text("Save")');
    await expect(parentPage.locator('text=Complete homework')).toBeVisible();

    // Child: Login (via device binding simulation)
    await childPage.goto('/welcome');
    await childPage.click('text=Let\'s Go!');
    // ... device binding flow ...

    // Child: View task
    await childPage.click('text=Tasks');
    await expect(childPage.locator('text=Complete homework')).toBeVisible();

    // Child: Check in
    await childPage.click('text=Complete homework');
    await childPage.click('button:has-text("I Did It!")');
    await childPage.click('button:has-text("Confirm")');
    await expect(
      childPage.locator('text=Waiting for parent')
    ).toBeVisible();

    // Parent: Approve
    await parentPage.reload();
    await parentPage.click('text=Approve');
    await expect(parentPage.locator('text=Approved')).toBeVisible();

    // Child: See points awarded
    await childPage.reload();
    await expect(childPage.locator('text=+15')).toBeVisible();

    await parentContext.close();
    await childContext.close();
  });
});
```

### API Mock Setup

```typescript
// mocks/handlers.ts
import { rest } from 'msw';

export const handlers = [
  // Auth handlers
  rest.post('/api/v1/auth/login', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        user: { id: '1', email: 'test@test.com' },
        access_token: 'test-token',
        refresh_token: 'test-refresh',
      })
    );
  }),

  // Task handlers
  rest.get('/api/v1/child/tasks', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        {
          id: '1',
          task: { id: '1', title: 'Test Task', points: 10 },
          status: 'pending',
        },
      ])
    );
  }),

  // Error simulation
  rest.get('/api/v1/error', (req, res, ctx) => {
    return res(ctx.status(500), ctx.json({ error: 'Server error' }));
  }),
];
```

---

## Test Coverage Requirements

| Category | Minimum Coverage |
|----------|-----------------|
| API Contracts | 100% |
| Critical User Flows | 100% |
| Error Handling | 80% |
| Edge Cases | 70% |

---

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run test:integration
      - uses: codecov/codecov-action@v3

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx playwright install
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| All FE SPECs | Upstream | Pending | Frontend implementations |
| All BE SPECs | Upstream | Pending | Backend implementations |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Flaky tests | Medium | Medium | Retry logic, proper waits |
| Slow test execution | Medium | Medium | Parallelization, selective runs |
| Test data pollution | High | Low | Isolated databases, cleanup |

---

## Acceptance Criteria

### Integration Tests
- [ ] All API endpoints have contract tests
- [ ] Error handling is tested
- [ ] Authentication flows are tested
- [ ] Rate limiting is tested

### E2E Tests
- [ ] Critical user flows are covered
- [ ] Multi-user scenarios are tested
- [ ] Offline behavior is tested
- [ ] Responsive design is tested

### CI/CD
- [ ] Tests run on every push
- [ ] Test failures block deployment
- [ ] Coverage reports are generated
- [ ] Performance benchmarks are tracked

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| All FE SPECs | Validates | Tests frontend implementations |
| All BE SPECs | Validates | Tests backend implementations |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
