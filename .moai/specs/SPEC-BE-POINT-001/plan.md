# SPEC-BE-POINT-001: Point System API

## Overview

Implement the point balance and transaction management API for tracking earned and spent points.

**Business Context**: Points are the currency of BabyEco. This API manages point balances, transactions, and provides history for reporting.

**Target Users**:
- Primary: Task/Exchange systems (internal)
- Secondary: Frontend applications (balance display, history)

---

## Technical Constraints

### Framework and Versions
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0
- PostgreSQL 15+
- Transactional integrity required

### Dependencies
- SPEC-BE-AUTH-001 (Authentication API)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall maintain accurate point balances per child.

```
Given any point transaction
When processed
Then the child's balance reflects all earned minus spent
And the balance is always non-negative
```

**UR-002**: The system shall record all point transactions with full audit trail.

```
Given any point change
When a transaction is created
Then the transaction includes source, amount, timestamp
And linked entity (task/exchange) is recorded
```

**UR-003**: The system shall prevent negative balances.

```
Given a spend transaction
When the amount exceeds current balance
Then the transaction is rejected
And an appropriate error is returned
```

### Event-Driven Requirements

**EDR-001**: When points are earned, the system shall create an earning transaction.

```
Given a task approval
When points are awarded
Then an "earn" transaction is created
And the child's balance increases
And the transaction links to the check-in
```

**EDR-002**: When points are spent, the system shall create a spending transaction.

```
Given a reward redemption
When points are deducted
Then a "spend" transaction is created
And the child's balance decreases
And the transaction links to the exchange
```

**EDR-003**: When points are frozen, the system shall reserve without deducting.

```
Given a pending exchange requires point hold
When frozen
Then points are marked as unavailable
And appear as "frozen" in balance
And can be unfrozen or spent
```

**EDR-004**: When points are manually adjusted, the system shall create an adjustment record.

```
Given a parent adjusts points
When adjustment is processed
Then an "adjustment" transaction is created
And reason is recorded
And parent who made adjustment is logged
```

### State-Driven Requirements

**SDR-001**: While calculating available balance, frozen points shall be excluded.

```
Given a child has frozen points
When available balance is queried
Then only non-frozen points are included
And frozen amount is shown separately
```

**SDR-002**: While transaction history is requested, results shall be paginated.

```
Given a transaction history request
When large history exists
Then results are paginated
And sorted by most recent first
```

### Optional Requirements

**OR-001**: The system MAY support point expiration.

```
Given points with expiration configured
When expiration date passes
Then expired points are removed
And an expiration transaction is created
```

**OR-002**: The system MAY support point categories/types.

```
Given different point types exist
When transactions are created
Then point type is tracked
And types may have different expiration rules
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT allow balance inconsistencies.

```
Given any operation
When completed
Then sum of transactions equals current balance
And no orphan transactions exist
```

**UBR-002**: The system shall NOT allow concurrent modification conflicts.

```
Given simultaneous balance updates
When processed
Then transaction isolation prevents conflicts
And final balance is consistent
```

---

## Technical Solution

### API Endpoints

```yaml
# Balance (Child)
GET /api/v1/child/points/balance
  Headers: Authorization: Bearer {token}
  Response: { balance, frozen, available, total_earned, total_spent }

# Transaction History
GET /api/v1/child/points/transactions
  Headers: Authorization: Bearer {token}
  Query: type?, start_date?, end_date?, page?, page_size?
  Response: PaginatedResponse[Transaction]

# Internal Service Endpoints (not exposed to frontend)
POST /internal/v1/points/earn
  Request: { child_id, amount, source_type, source_id, description? }
  Response: Transaction

POST /internal/v1/points/spend
  Request: { child_id, amount, source_type, source_id, description? }
  Response: Transaction

POST /internal/v1/points/freeze
  Request: { child_id, amount, source_type, source_id }
  Response: { freeze_id }

POST /internal/v1/points/unfreeze
  Request: { freeze_id }
  Response: { success: true }

POST /internal/v1/points/adjust
  Request: { child_id, amount, reason, adjusted_by }
  Response: Transaction

# Parent Endpoints
POST /api/v1/children/{child_id}/points/adjust
  Headers: Authorization: Bearer {token}
  Request: { amount, reason }
  Response: Transaction

GET /api/v1/children/{child_id}/points/balance
  Headers: Authorization: Bearer {token}
  Response: PointBalance

GET /api/v1/children/{child_id}/points/transactions
  Headers: Authorization: Bearer {token}
  Query: type?, start_date?, end_date?, page?, page_size?
  Response: PaginatedResponse[Transaction]
```

### Data Models

```python
# models/point.py
class PointBalance(Base):
    __tablename__ = "point_balances"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"), unique=True)
    balance: Mapped[int] = mapped_column(default=0)
    frozen: Mapped[int] = mapped_column(default=0)
    total_earned: Mapped[int] = mapped_column(default=0)
    total_spent: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

class Transaction(Base):
    __tablename__ = "point_transactions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"), index=True)
    type: Mapped[str]  # earn, spend, freeze, unfreeze, adjustment, expiration
    amount: Mapped[int]  # Positive for earn/unfreeze, negative for spend/freeze
    balance_after: Mapped[int]  # Balance after this transaction
    source_type: Mapped[str]  # check_in, exchange, manual, system
    source_id: Mapped[UUID | None]
    description: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)

    # For freeze transactions
    freeze_id: Mapped[UUID | None]  # Links freeze/unfreeze/spend

class PointFreeze(Base):
    __tablename__ = "point_freezes"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    amount: Mapped[int]
    source_type: Mapped[str]
    source_id: Mapped[UUID | None]
    status: Mapped[str]  # active, spent, released
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    released_at: Mapped[datetime | None]
```

### Service Implementation

```python
# services/point_service.py
class PointService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(self, child_id: UUID) -> PointBalance:
        result = await self.db.execute(
            select(PointBalance).where(PointBalance.child_id == child_id)
        )
        balance = result.scalar_one_or_none()
        if not balance:
            # Create initial balance
            balance = PointBalance(child_id=child_id)
            self.db.add(balance)
            await self.db.commit()
        return balance

    async def earn(
        self, child_id: UUID, amount: int, source_type: str,
        source_id: UUID | None = None, description: str | None = None
    ) -> Transaction:
        async with self.db.begin():
            # Lock balance row
            balance = await self._lock_balance(child_id)

            # Update balance
            balance.balance += amount
            balance.total_earned += amount

            # Create transaction
            transaction = Transaction(
                child_id=child_id,
                type="earn",
                amount=amount,
                balance_after=balance.balance,
                source_type=source_type,
                source_id=source_id,
                description=description,
            )
            self.db.add(transaction)
            await self.db.commit()

        return transaction

    async def spend(
        self, child_id: UUID, amount: int, source_type: str,
        source_id: UUID | None = None, description: str | None = None
    ) -> Transaction:
        async with self.db.begin():
            balance = await self._lock_balance(child_id)

            # Check available balance
            available = balance.balance - balance.frozen
            if available < amount:
                raise InsufficientPointsError(
                    f"Available: {available}, Required: {amount}"
                )

            # Update balance
            balance.balance -= amount
            balance.total_spent += amount

            transaction = Transaction(
                child_id=child_id,
                type="spend",
                amount=-amount,
                balance_after=balance.balance,
                source_type=source_type,
                source_id=source_id,
                description=description,
            )
            self.db.add(transaction)
            await self.db.commit()

        return transaction

    async def freeze(self, child_id: UUID, amount: int, source_type: str,
                     source_id: UUID | None = None) -> PointFreeze:
        async with self.db.begin():
            balance = await self._lock_balance(child_id)

            available = balance.balance - balance.frozen
            if available < amount:
                raise InsufficientPointsError()

            balance.frozen += amount

            freeze = PointFreeze(
                child_id=child_id,
                amount=amount,
                source_type=source_type,
                source_id=source_id,
                status="active",
            )
            self.db.add(freeze)

            # Create freeze transaction
            transaction = Transaction(
                child_id=child_id,
                type="freeze",
                amount=-amount,
                balance_after=balance.balance,
                source_type=source_type,
                source_id=source_id,
            )
            self.db.add(transaction)
            await self.db.commit()

        return freeze

    async def _lock_balance(self, child_id: UUID) -> PointBalance:
        """Lock balance row for transaction"""
        result = await self.db.execute(
            select(PointBalance)
            .where(PointBalance.child_id == child_id)
            .with_for_update()
        )
        return result.scalar_one()
```

### Response Schemas

```python
# schemas/point.py
class PointBalanceResponse(BaseModel):
    balance: int
    frozen: int
    available: int
    total_earned: int
    total_spent: int

class TransactionResponse(BaseModel):
    id: UUID
    type: str
    amount: int
    balance_after: int
    source_type: str
    source_id: UUID | None
    description: str | None
    created_at: datetime

class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-BE-AUTH-001 | Upstream | Pending | Auth context |
| PostgreSQL | Database | Required | ACID transactions |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Race conditions | High | Medium | Row-level locking, transactions |
| Balance drift | High | Low | Reconciliation job, constraints |
| Performance at scale | Medium | Low | Indexing, caching |

---

## Acceptance Criteria

### Balance Management
- [ ] Given valid child, when balance queried, then accurate balance returned
- [ ] Given earn transaction, when processed, then balance increases
- [ ] Given spend transaction, when processed, then balance decreases
- [ ] Given insufficient balance, when spend attempted, then rejected

### Transaction Recording
- [ ] Given any transaction, when processed, then audit trail created
- [ ] Given history request, when queried, then paginated results returned
- [ ] Given date filter, when applied, then correct range returned

### Freezing
- [ ] Given freeze request, when processed, then points frozen
- [ ] Given unfreeze request, when processed, then points released
- [ ] Given frozen points, when available queried, then excluded

### Adjustments
- [ ] Given parent adjustment, when processed, then balance updated
- [ ] Given adjustment, when recorded, then reason logged

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-BE-TASK-001 | Upstream | Earns points from tasks |
| SPEC-BE-EXCHANGE-001 | Upstream | Spends points on rewards |
| SPEC-FE-POINT-001 | Downstream | Frontend display |
| SPEC-BE-REPORT-001 | Downstream | Point statistics |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
