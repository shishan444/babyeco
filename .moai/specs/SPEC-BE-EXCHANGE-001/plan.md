# SPEC-BE-EXCHANGE-001: Exchange Center API

## Overview

Implement the reward management and redemption API for the exchange center functionality.

**Business Context**: The Exchange Center API manages reward items configured by parents and handles redemption requests from children, including timer-based rewards.

**Target Users**:
- Primary: Child app (redemption)
- Secondary: Parent app (reward configuration)

---

## Technical Constraints

### Framework and Versions
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0
- PostgreSQL 15+
- Background task processing for timers

### Dependencies
- SPEC-BE-AUTH-001 (Authentication API)
- SPEC-BE-POINT-001 (Point System API)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall return only rewards accessible to the requesting child.

```
Given a reward list request from a child
When processed
Then only rewards from their family are returned
And only enabled rewards are included
```

**UR-002**: The system shall validate reward configuration before saving.

```
Given a reward creation/update request
When processed
Then name is required and within limits
And cost is positive
And type-specific fields are validated
```

**UR-003**: The system shall maintain accurate stock counts for quantity rewards.

```
Given a quantity-type reward
When redemption occurs
Then stock is decremented atomically
And redemption fails if stock is zero
```

### Event-Driven Requirements

**EDR-001**: When a parent creates a reward, the system shall add it to the family's exchange center.

```
Given a valid reward creation request
When processed
Then the reward is created with all configuration
And appears in children's exchange center
```

**EDR-002**: When a child redeems a one-time reward, the system shall deduct points and record redemption.

```
Given a valid one-time redemption
When processed
Then points are deducted from child's balance
And a redemption record is created
And parent is notified
```

**EDR-003**: When a child redeems a timer reward, the system shall start a timer session.

```
Given a valid timer redemption
When processed
Then points are deducted
And a timer session is created with start time
And the timer status is "running"
And parent is notified
```

**EDR-004**: When a timer expires, the system shall mark it complete and notify.

```
Given an active timer session
When the duration elapses
Then the timer is marked complete
And child and parent are notified
```

**EDR-005**: When a child pins a reward, the system shall update their pinned goal.

```
Given a pin request
When processed
Then the previous pin (if any) is removed
And the new reward is pinned
```

### State-Driven Requirements

**SDR-001**: While a timer is running, the system shall prevent new timer redemptions.

```
Given a child has an active timer
When they try to redeem another timer reward
Then the request is rejected
And an error indicates active timer exists
```

**SDR-002**: While a reward is out of stock, the system shall prevent redemption.

```
Given a quantity reward has stock = 0
When redemption is attempted
Then the request is rejected
And "Out of stock" error is returned
```

**SDR-003**: While a reward is disabled, the system shall hide it from children.

```
Given a reward is disabled
When a child views the exchange center
Then the reward is not included
```

### Optional Requirements

**OR-001**: The system MAY support reward scheduling (available during certain times).

```
Given a reward with time restrictions
When current time is outside window
Then the reward shows as unavailable
```

**OR-002**: The system MAY support reward cooldown periods.

```
Given a reward with cooldown
When recently redeemed
Then redemption is blocked until cooldown expires
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT allow redemption with insufficient points.

```
Given a child lacks sufficient points
When redemption is attempted
Then the request is rejected before any deduction
```

**UBR-002**: The system shall NOT allow concurrent timer activations.

```
Given simultaneous timer redemption requests
When processed
Then only one succeeds
And others are rejected
```

---

## Technical Solution

### API Endpoints

```yaml
# Reward Management (Parent)
POST /api/v1/rewards
  Headers: Authorization: Bearer {token}
  Request: RewardCreateRequest
  Response: Reward

GET /api/v1/rewards
  Headers: Authorization: Bearer {token}
  Query: type?, enabled?
  Response: [Reward]

GET /api/v1/rewards/{reward_id}
  Headers: Authorization: Bearer {token}
  Response: Reward

PUT /api/v1/rewards/{reward_id}
  Headers: Authorization: Bearer {token}
  Request: RewardUpdateRequest
  Response: Reward

DELETE /api/v1/rewards/{reward_id}
  Headers: Authorization: Bearer {token}
  Response: { success: true }

PATCH /api/v1/rewards/{reward_id}/toggle
  Headers: Authorization: Bearer {token}
  Request: { enabled: bool }
  Response: Reward

# Exchange Center (Child)
GET /api/v1/child/rewards
  Headers: Authorization: Bearer {token}
  Response: [Reward]

POST /api/v1/child/rewards/{reward_id}/redeem
  Headers: Authorization: Bearer {token}
  Response: Redemption

POST /api/v1/child/rewards/{reward_id}/pin
  Headers: Authorization: Bearer {token}
  Response: { success: true, pinned_reward: Reward }

DELETE /api/v1/child/rewards/pin
  Headers: Authorization: Bearer {token}
  Response: { success: true }

# Timer Management
GET /api/v1/child/timers/active
  Headers: Authorization: Bearer {token}
  Response: TimerSession | null

POST /api/v1/child/timers/{timer_id}/pause
  Headers: Authorization: Bearer {token}
  Response: TimerSession

POST /api/v1/child/timers/{timer_id}/resume
  Headers: Authorization: Bearer {token}
  Response: TimerSession

# Parent Timer Monitoring
GET /api/v1/children/{child_id}/timers/active
  Headers: Authorization: Bearer {token}
  Response: TimerSession | null
```

### Data Models

```python
# models/exchange.py
class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None]
    image_url: Mapped[str | None]
    type: Mapped[str]  # one-time, timer, quantity
    cost: Mapped[int] = mapped_column(SmallInteger)

    # Timer-specific
    duration_minutes: Mapped[int | None]

    # Quantity-specific
    stock: Mapped[int | None]
    initial_stock: Mapped[int | None]

    enabled: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("parents.id"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime]

class Redemption(Base):
    __tablename__ = "redemptions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    reward_id: Mapped[UUID] = mapped_column(ForeignKey("rewards.id"))
    points_spent: Mapped[int]
    type: Mapped[str]  # one-time, timer, quantity
    status: Mapped[str]  # completed, active, cancelled
    redeemed_at: Mapped[datetime] = mapped_column(default=utcnow)

    # For timer redemptions
    timer_session_id: Mapped[UUID | None]

class TimerSession(Base):
    __tablename__ = "timer_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    redemption_id: Mapped[UUID] = mapped_column(ForeignKey("redemptions.id"))
    reward_id: Mapped[UUID] = mapped_column(ForeignKey("rewards.id"))
    duration_seconds: Mapped[int]
    started_at: Mapped[datetime]
    paused_at: Mapped[datetime | None]
    resumed_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    status: Mapped[str]  # running, paused, completed, cancelled
    remaining_seconds: Mapped[int]  # Calculated or stored

class PinnedReward(Base):
    __tablename__ = "pinned_rewards"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"), unique=True)
    reward_id: Mapped[UUID] = mapped_column(ForeignKey("rewards.id"))
    pinned_at: Mapped[datetime] = mapped_column(default=utcnow)
```

### Request/Response Schemas

```python
# schemas/exchange.py
class RewardCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    image_url: str | None = None
    type: Literal["one-time", "timer", "quantity"]
    cost: int = Field(..., ge=1, le=10000)
    duration_minutes: int | None = Field(None, ge=1, le=480)  # Max 8 hours
    stock: int | None = Field(None, ge=0)

    @validator('duration_minutes', always=True)
    def validate_timer(cls, v, values):
        if values.get('type') == 'timer' and v is None:
            raise ValueError('duration_minutes required for timer type')
        return v

    @validator('stock', always=True)
    def validate_quantity(cls, v, values):
        if values.get('type') == 'quantity' and v is None:
            raise ValueError('stock required for quantity type')
        return v

class RewardResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    image_url: str | None
    type: str
    cost: int
    duration_minutes: int | None
    stock: int | None
    enabled: bool
    created_at: datetime

class RedemptionResponse(BaseModel):
    id: UUID
    reward: RewardBrief
    points_spent: int
    type: str
    status: str
    redeemed_at: datetime
    timer_session: TimerSessionBrief | None

class TimerSessionResponse(BaseModel):
    id: UUID
    reward: RewardBrief
    duration_seconds: int
    remaining_seconds: int
    started_at: datetime
    status: str
    is_paused: bool
```

### Service Implementation

```python
# services/exchange_service.py
class ExchangeService:
    def __init__(self, db: AsyncSession, point_service: PointService):
        self.db = db
        self.point_service = point_service

    async def redeem(self, child_id: UUID, reward_id: UUID) -> Redemption:
        async with self.db.begin():
            # Get reward with lock
            reward = await self._get_reward_for_update(reward_id)

            # Validate
            if not reward.enabled:
                raise RewardDisabledError()
            if reward.type == 'quantity' and reward.stock <= 0:
                raise OutOfStockError()

            # Check for active timer
            if reward.type == 'timer':
                active = await self._get_active_timer(child_id)
                if active:
                    raise ActiveTimerExistsError()

            # Deduct points
            await self.point_service.spend(
                child_id=child_id,
                amount=reward.cost,
                source_type="redemption",
                source_id=reward_id,
            )

            # Update stock if quantity
            if reward.type == 'quantity':
                reward.stock -= 1

            # Create redemption
            redemption = Redemption(
                child_id=child_id,
                reward_id=reward_id,
                points_spent=reward.cost,
                type=reward.type,
                status="active" if reward.type == "timer" else "completed",
            )
            self.db.add(redemption)
            await self.db.flush()

            # Create timer session if needed
            if reward.type == 'timer':
                timer = TimerSession(
                    child_id=child_id,
                    redemption_id=redemption.id,
                    reward_id=reward_id,
                    duration_seconds=reward.duration_minutes * 60,
                    started_at=datetime.utcnow(),
                    status="running",
                    remaining_seconds=reward.duration_minutes * 60,
                )
                self.db.add(timer)
                redemption.timer_session_id = timer.id

            await self.db.commit()

        return redemption

    async def pause_timer(self, timer_id: UUID, child_id: UUID) -> TimerSession:
        async with self.db.begin():
            timer = await self._get_timer_for_update(timer_id, child_id)

            if timer.status != "running":
                raise InvalidTimerStateError()

            timer.status = "paused"
            timer.paused_at = datetime.utcnow()
            await self.db.commit()

        return timer

    async def complete_timer(self, timer_id: UUID) -> TimerSession:
        """Called by background job when timer expires"""
        async with self.db.begin():
            timer = await self._get_timer_for_update(timer_id)

            timer.status = "completed"
            timer.completed_at = datetime.utcnow()
            timer.remaining_seconds = 0

            # Update redemption status
            await self.db.execute(
                update(Redemption)
                .where(Redemption.timer_session_id == timer_id)
                .values(status="completed")
            )

            await self.db.commit()

        # Send notifications
        await self._send_timer_complete_notifications(timer)

        return timer
```

### Background Jobs

```python
# Background tasks
- monitor_active_timers: Check every 10 seconds for expired timers
- send_timer_warnings: Send warnings at 5 min and 1 min remaining
- cleanup_completed_timers: Archive old timer sessions
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-BE-AUTH-001 | Upstream | Pending | Auth context |
| SPEC-BE-POINT-001 | Upstream | Pending | Point deduction |
| PostgreSQL | Database | Required | ACID transactions |
| Notification Service | Service | Required | Push notifications |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Stock race conditions | High | Medium | Row-level locking |
| Timer drift | Low | Low | Server-side time tracking |
| Point deduction failure | High | Low | Transaction rollback |
| Multiple timer redemption | Medium | Medium | Unique constraint, locking |

---

## Acceptance Criteria

### Reward Management
- [ ] Given valid reward, when created, then stored correctly
- [ ] Given reward exists, when disabled, then hidden from children
- [ ] Given quantity reward, when redeemed, then stock decremented

### Redemption Flow
- [ ] Given sufficient points, when redeemed, then points deducted
- [ ] Given insufficient points, when redeemed, then rejected
- [ ] Given out of stock, when redeemed, then rejected

### Timer Management
- [ ] Given timer redemption, when processed, then timer starts
- [ ] Given active timer, when new timer attempted, then rejected
- [ ] Given timer running, when paused, then timer stops
- [ ] Given timer complete, when expired, then notifications sent

### Pinning
- [ ] Given pin request, when processed, then goal updated
- [ ] Given previous pin, when new pin, then replaced

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-EXCHANGE-001 | Upstream | Child exchange frontend |
| SPEC-FE-PARENT-001 | Upstream | Parent reward management |
| SPEC-BE-POINT-001 | Upstream | Point deduction |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
