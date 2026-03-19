# SPEC-PERF-001: Performance Optimization

## Overview

Define performance optimization strategy and benchmarks for BabyEco applications.

**Business Context**: Performance directly impacts user experience, especially for children with shorter attention spans. This SPEC establishes benchmarks and optimization strategies.

**Target Users**:
- Primary: Development team
- Secondary: DevOps team

---

## Technical Constraints

### Framework and Versions
- Next.js 22.x with App Router
- React 19.x
- FastAPI (Python 3.11+)
- PostgreSQL 15+
- Redis 7+

### Dependencies
- All SPECs implemented

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: All API endpoints shall respond within defined time limits.

```
Given an API request
When processed
Then response time is within benchmark
And slow responses are logged
```

**UR-002**: All pages shall load within defined time limits.

```
Given a page navigation
When loading
Then initial render completes within benchmark
And time to interactive meets benchmark
```

**UR-003**: Animations shall maintain 60fps.

```
Given an animation is playing
When rendering
Then frame rate stays at or above 60fps
And jank is minimal
```

### Event-Driven Requirements

**EDR-001**: When a slow query is detected, the system shall log and alert.

```
Given a query exceeds threshold
When detected
Then query is logged with details
And developers are alerted
```

**EDR-002**: When bundle size exceeds limit, the build shall warn.

```
Given a bundle exceeds size limit
When build completes
Then warning is displayed
And breakdown is provided
```

**EDR-003**: When cache is stale, the system shall invalidate appropriately.

```
Given cached data is outdated
When accessed
Then fresh data is fetched
And cache is updated
```

### State-Driven Requirements

**SDR-001**: While under load, the system shall maintain responsiveness.

```
Given high traffic load
When requests increase
Then response times stay acceptable
And no requests timeout
```

**SDR-002**: While offline, the system shall serve cached content.

```
Given network is unavailable
When user interacts
Then cached content is shown
And offline indicator displays
```

---

## Performance Benchmarks

### Frontend

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| First Contentful Paint (FCP) | < 1.5s | > 3s |
| Largest Contentful Paint (LCP) | < 2.5s | > 4s |
| Time to Interactive (TTI) | < 3.5s | > 7s |
| Cumulative Layout Shift (CLS) | < 0.1 | > 0.25 |
| First Input Delay (FID) | < 100ms | > 300ms |
| Bundle Size (Initial) | < 150KB | > 300KB |
| Bundle Size (Lazy) | < 500KB total | > 1MB |

### Backend

| Endpoint Type | Target P50 | Target P95 | Target P99 |
|--------------|------------|------------|------------|
| Auth endpoints | 100ms | 300ms | 500ms |
| Read queries (simple) | 50ms | 150ms | 300ms |
| Read queries (complex) | 200ms | 500ms | 1000ms |
| Write operations | 100ms | 300ms | 500ms |
| AI endpoints | 2000ms | 5000ms | 10000ms |
| Report generation | 500ms | 2000ms | 5000ms |

### Database

| Metric | Target |
|--------|--------|
| Query time (indexed) | < 10ms |
| Query time (complex) | < 100ms |
| Connection pool usage | < 80% |
| Index hit ratio | > 95% |

---

## Technical Solution

### Frontend Optimizations

```typescript
// Code splitting strategy
// app/(child)/layout.tsx
const TaskModule = lazy(() => import('./tasks'));
const ExchangeModule = lazy(() => import('./exchange'));
const EntertainmentModule = lazy(() => import('./entertainment'));

// Image optimization
// components/optimized-image.tsx
import Image from 'next/image';

export function OptimizedImage({ src, alt, width, height }) {
  return (
    <Image
      src={src}
      alt={alt}
      width={width}
      height={height}
      loading="lazy"
      placeholder="blur"
      blurDataURL={generateBlurDataURL(width, height)}
    />
  );
}

// Virtualized list for long lists
import { VirtualList } from '@tanstack/react-virtual';

export function TaskList({ tasks }) {
  const rowVirtualizer = useVirtualizer({
    count: tasks.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // Item height
  });

  return (
    <div ref={parentRef} className="h-screen overflow-auto">
      <div style={{ height: rowVirtualizer.getTotalSize() }}>
        {rowVirtualizer.getVirtualItems().map((virtualRow) => (
          <TaskCard
            key={virtualRow.key}
            task={tasks[virtualRow.index]}
            style={{
              position: 'absolute',
              transform: `translateY(${virtualRow.start}px)`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

// Debounced search
function useDebouncedSearch(delay = 300) {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, delay);

  return { query, setQuery, debouncedQuery };
}

// Memoized expensive components
const TaskCard = memo(function TaskCard({ task, onCheckIn }) {
  // Component implementation
});

// Animation performance
// Use will-change sparingly
.animated-element {
  will-change: transform, opacity;
}

// Use transform instead of top/left
.card-enter {
  transform: translateY(20px);
  opacity: 0;
}
.card-enter-active {
  transform: translateY(0);
  opacity: 1;
  transition: transform 300ms, opacity 300ms;
}
```

### Backend Optimizations

```python
# Database query optimization
# services/task_service.py
class TaskService:
    async def get_tasks_with_assignees(self, family_id: UUID) -> list[Task]:
        # Use eager loading to avoid N+1
        result = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.assignees),
                selectinload(Task.config),
            )
            .where(Task.family_id == family_id)
            .where(Task.is_active == True)
        )
        return result.scalars().all()

# Index creation
# migrations/add_performance_indexes.py
def upgrade():
    # Task queries
    op.create_index('idx_tasks_family_active', 'tasks', ['family_id', 'is_active'])
    op.create_index('idx_task_instances_child_date', 'task_instances', ['child_id', 'date'])
    op.create_index('idx_check_ins_status', 'check_ins', ['status', 'created_at'])

    # Point queries
    op.create_index('idx_transactions_child_date', 'point_transactions', ['child_id', 'created_at'])

    # Full-text search for content
    op.execute("""
        CREATE INDEX idx_content_search ON content
        USING gin(to_tsvector('english', title || ' ' || description))
    """)

# Caching strategy
# cache/decorators.py
from functools import wraps
from redis import Redis

def cached(key_template: str, ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = key_template.format(*args, **kwargs)
            cached = await redis.get(cache_key)

            if cached:
                return json.loads(cached)

            result = await func(*args, **kwargs)
            await redis.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

# Usage
@cached('user:{0}:profile', ttl=600)
async def get_user_profile(user_id: UUID) -> dict:
    # ...

# Connection pooling
# config/database.py
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Query batching
# GraphQL or custom batching for multiple related queries
@router.post('/api/v1/batch')
async def batch_request(requests: list[BatchRequest]):
    results = await asyncio.gather(*[
        process_single_request(req) for req in requests
    ])
    return results
```

### Monitoring

```typescript
// Performance monitoring
// lib/monitoring.ts
export function reportWebVitals(metric: NextWebVitalsMetric) {
  // Send to analytics
  if (metric.value > getThreshold(metric.name)) {
    // Alert on slow metrics
    sendToSentry({
      type: 'performance',
      metric: metric.name,
      value: metric.value,
      page: window.location.pathname,
    });
  }
}

// Custom performance marks
export function measureRender(componentName: string) {
  const start = performance.now();
  return () => {
    const duration = performance.now() - start;
    if (duration > 16) { // More than one frame
      console.warn(`${componentName} render took ${duration.toFixed(2)}ms`);
    }
  };
}
```

```python
# Backend monitoring
# middleware/performance.py
import time
from prometheus_client import Histogram

REQUEST_LATENCY = Histogram(
    'request_latency_seconds',
    'Request latency',
    ['method', 'endpoint', 'status']
)

@app.middleware('http')
async def add_timing_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).observe(duration)

    # Log slow requests
    if duration > 1.0:
        logger.warning(
            f"Slow request: {request.method} {request.url.path} "
            f"took {duration:.2f}s"
        )

    return response
```

---

## Bundle Analysis

```javascript
// next.config.js
module.exports = {
  // Bundle analyzer
  experimental: {
    bundlePagesRouterDependencies: true,
  },

  // Compression
  compress: true,

  // Headers for caching
  async headers() {
    return [
      {
        source: '/:all*(svg|jpg|png|woff|woff2)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },
};
```

---

## Load Testing

```yaml
# load-tests/locustfile.py
from locust import HttpUser, task, between

class ParentUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_dashboard(self):
        self.client.get('/api/v1/dashboard')

    @task(2)
    def view_approvals(self):
        self.client.get('/api/v1/approvals')

    @task(1)
    def approve_task(self):
        self.client.post('/api/v1/approvals/test-id/approve')

class ChildUser(HttpUser):
    wait_time = between(2, 5)

    @task(5)
    def view_tasks(self):
        self.client.get('/api/v1/child/tasks')

    @task(2)
    def view_points(self):
        self.client.get('/api/v1/child/points/balance')

    @task(1)
    def check_in_task(self):
        self.client.post('/api/v1/child/tasks/test-id/checkin')
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| All SPECs | Upstream | Pending | Complete implementation |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Third-party API latency | High | Medium | Timeouts, fallbacks |
| Database bloat | Medium | Low | Regular maintenance, archiving |
| Memory leaks | Medium | Low | Monitoring, profiling |

---

## Acceptance Criteria

### Frontend Performance
- [ ] FCP < 1.5s on 3G connection
- [ ] LCP < 2.5s on 3G connection
- [ ] TTI < 3.5s on 3G connection
- [ ] CLS < 0.1
- [ ] Bundle size < 150KB initial

### Backend Performance
- [ ] All endpoints respond within P95 target
- [ ] Database queries < 100ms average
- [ ] Cache hit ratio > 90%
- [ ] No connection pool exhaustion under load

### Monitoring
- [ ] Web vitals reported
- [ ] Slow queries logged
- [ ] Alerts configured for threshold violations

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| All SPECs | Applies to | Performance requirements for all |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
