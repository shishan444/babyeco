# SPEC-BE-ENTERTAIN-001: Entertainment Content API

## Overview

Implement the content management and reading tracking API for the entertainment module.

**Business Context**: The Entertainment API manages educational content for children and tracks reading progress. Content completion triggers AI-generated questions for point bonuses.

**Target Users**:
- Primary: Child app (content consumption)
- Secondary: Admin/Content management (content upload)

---

## Technical Constraints

### Framework and Versions
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0
- PostgreSQL 15+
- File storage (S3/local)

### Dependencies
- SPEC-BE-AUTH-001 (Authentication API)
- SPEC-BE-POINT-001 (Point System API)
- SPEC-BE-AI-001 (AI Q&A API)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall return only age-appropriate content.

```
Given a content list request from a child
When processed
Then only content matching child's age range is returned
And inappropriate content is filtered
```

**UR-002**: The system shall track reading progress per child.

```
Given a child reads content
When progress updates occur
Then progress is stored per child-content pair
And progress can be resumed later
```

**UR-003**: The system shall prevent duplicate point earning from same content.

```
Given a child has already earned points from content
When they complete it again
Then no additional points are awarded
And the content shows as "completed"
```

### Event-Driven Requirements

**EDR-001**: When content is accessed, the system shall check unlock status.

```
Given a child tries to read content
When access is requested
Then free content is always accessible
And premium content requires unlock
```

**EDR-002**: When content is unlocked, the system shall deduct points.

```
Given a child unlocks premium content
When unlock is processed
Then point cost is deducted
And content becomes accessible
And unlock is recorded
```

**EDR-003**: When content is completed, the system shall prepare questions.

```
Given a child finishes reading content
When completion is recorded
Then AI-generated questions are prepared
And the question session is available
```

**EDR-004**: When questions are answered correctly, the system shall award points.

```
Given a child answers questions
When answers are submitted
Then correct answers earn bonus points
And a summary is returned
```

### State-Driven Requirements

**SDR-001**: While content is being read, the system shall save progress periodically.

```
Given a child is reading content
When they scroll through
Then progress is auto-saved every 30 seconds
And position is tracked
```

**SDR-002**: While questions are being answered, the system shall track progress.

```
Given a question session is active
When answers are submitted
Then progress through questions is tracked
And score is accumulated
```

### Optional Requirements

**OR-001**: The system MAY support multiple content categories.

```
Given content exists in categories
When browsing
Then content can be filtered by category
```

**OR-002**: The system MAY support content recommendations.

```
Given a child has reading history
When viewing content
Then recommended content may be shown
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT allow access to content without proper unlock.

```
Given premium content is locked
When access attempted
Then request is rejected
And unlock prompt is shown
```

---

## Technical Solution

### API Endpoints

```yaml
# Content Browsing (Child)
GET /api/v1/child/content
  Headers: Authorization: Bearer {token}
  Query: category?, type?
  Response: [Content]

GET /api/v1/child/content/{content_id}
  Headers: Authorization: Bearer {token}
  Response: Content

# Content Unlock
POST /api/v1/child/content/{content_id}/unlock
  Headers: Authorization: Bearer {token}
  Response: { success: true, content: Content }

# Reading Progress
GET /api/v1/child/content/{content_id}/progress
  Headers: Authorization: Bearer {token}
  Response: ReadingProgress

PUT /api/v1/child/content/{content_id}/progress
  Headers: Authorization: Bearer {token}
  Request: { progress: int, position: int }
  Response: ReadingProgress

POST /api/v1/child/content/{content_id}/complete
  Headers: Authorization: Bearer {token}
  Response: { questions_available: bool }

# Question Session
GET /api/v1/child/content/{content_id}/questions
  Headers: Authorization: Bearer {token}
  Response: [Question]

POST /api/v1/child/content/{content_id}/questions/submit
  Headers: Authorization: Bearer {token}
  Request: { answers: [{ question_id, answer }] }
  Response: QuestionResult

# Content Management (Admin/Internal)
POST /internal/v1/content
  Request: ContentCreateRequest
  Response: Content

PUT /internal/v1/content/{content_id}
  Request: ContentUpdateRequest
  Response: Content

DELETE /internal/v1/content/{content_id}
  Response: { success: true }
```

### Data Models

```python
# models/content.py
class Content(Base):
    __tablename__ = "content"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None]
    cover_image_url: Mapped[str | None]
    content_url: Mapped[str]  # URL to actual content
    content_type: Mapped[str]  # ebook, video, game
    category: Mapped[str]  # story, science, nature, etc.
    age_min: Mapped[int] = mapped_column(SmallInteger)
    age_max: Mapped[int] = mapped_column(SmallInteger)
    point_cost: Mapped[int] = mapped_column(default=0)  # 0 = free
    point_reward: Mapped[int]  # Points for completing + questions
    reading_time_minutes: Mapped[int]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime]

class ContentUnlock(Base):
    __tablename__ = "content_unlocks"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    content_id: Mapped[UUID] = mapped_column(ForeignKey("content.id"))
    unlocked_at: Mapped[datetime] = mapped_column(default=utcnow)

class ReadingProgress(Base):
    __tablename__ = "reading_progress"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    content_id: Mapped[UUID] = mapped_column(ForeignKey("content.id"))
    progress: Mapped[int] = mapped_column(default=0)  # 0-100
    position: Mapped[int] = mapped_column(default=0)  # Scroll position
    started_at: Mapped[datetime]
    last_read_at: Mapped[datetime]
    completed: Mapped[bool] = mapped_column(default=False)
    completed_at: Mapped[datetime | None]
    points_earned: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
        UniqueConstraint('child_id', 'content_id'),
    )

class ContentQuestion(Base):
    __tablename__ = "content_questions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    content_id: Mapped[UUID] = mapped_column(ForeignKey("content.id"))
    question: Mapped[str]
    question_type: Mapped[str]  # multiple_choice, short_answer
    options: Mapped[list[str] | None]  # For multiple choice
    correct_answer: Mapped[str]
    hint: Mapped[str]
    points: Mapped[int]
    order: Mapped[int]

class QuestionSession(Base):
    __tablename__ = "question_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    content_id: Mapped[UUID] = mapped_column(ForeignKey("content.id"))
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    completed_at: Mapped[datetime | None]
    total_questions: Mapped[int]
    correct_answers: Mapped[int]
    points_earned: Mapped[int]

class QuestionAnswer(Base):
    __tablename__ = "question_answers"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("question_sessions.id"))
    question_id: Mapped[UUID] = mapped_column(ForeignKey("content_questions.id"))
    answer: Mapped[str]
    is_correct: Mapped[bool]
    answered_at: Mapped[datetime] = mapped_column(default=utcnow)
```

### Response Schemas

```python
# schemas/content.py
class ContentResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    cover_image_url: str | None
    content_type: str
    category: str
    age_range: tuple[int, int]
    point_cost: int
    point_reward: int
    reading_time_minutes: int
    is_unlocked: bool
    progress: int | None
    completed: bool

class ReadingProgressResponse(BaseModel):
    content_id: UUID
    progress: int
    position: int
    completed: bool
    can_earn_points: bool

class QuestionResponse(BaseModel):
    id: UUID
    question: str
    question_type: str
    options: list[str] | None
    points: int
    order: int

class QuestionResultResponse(BaseModel):
    correct_count: int
    total_questions: int
    points_earned: int
    answers: list[AnswerResult]
```

### Service Implementation

```python
# services/content_service.py
class ContentService:
    def __init__(self, db: AsyncSession, point_service: PointService):
        self.db = db
        self.point_service = point_service

    async def get_content_for_child(
        self, child_id: UUID, child_age: int
    ) -> list[Content]:
        # Get content matching age range
        result = await self.db.execute(
            select(Content)
            .where(Content.is_active == True)
            .where(Content.age_min <= child_age)
            .where(Content.age_max >= child_age)
            .order_by(Content.created_at.desc())
        )
        contents = result.scalars().all()

        # Enrich with unlock/progress status
        for content in contents:
            content.is_unlocked = await self._is_unlocked(child_id, content.id)
            content.progress = await self._get_progress(child_id, content.id)

        return contents

    async def unlock_content(
        self, child_id: UUID, content_id: UUID
    ) -> ContentUnlock:
        async with self.db.begin():
            content = await self._get_content(content_id)

            if content.point_cost == 0:
                raise ContentFreeError()  # Free content doesn't need unlock

            if await self._is_unlocked(child_id, content_id):
                raise AlreadyUnlockedError()

            # Deduct points
            await self.point_service.spend(
                child_id=child_id,
                amount=content.point_cost,
                source_type="content_unlock",
                source_id=content_id,
            )

            # Create unlock record
            unlock = ContentUnlock(
                child_id=child_id,
                content_id=content_id,
            )
            self.db.add(unlock)
            await self.db.commit()

        return unlock

    async def complete_reading(
        self, child_id: UUID, content_id: UUID
    ) -> dict:
        async with self.db.begin():
            progress = await self._get_or_create_progress(child_id, content_id)

            if progress.completed:
                return {"questions_available": False, "already_completed": True}

            progress.completed = True
            progress.completed_at = datetime.utcnow()
            await self.db.commit()

        # Check if questions available
        questions = await self._get_questions(content_id)
        return {"questions_available": len(questions) > 0}

    async def submit_answers(
        self, child_id: UUID, content_id: UUID, answers: list[dict]
    ) -> QuestionResultResponse:
        async with self.db.begin():
            # Check if already earned points
            progress = await self._get_progress(child_id, content_id)
            if progress.points_earned:
                raise PointsAlreadyEarnedError()

            # Create session
            questions = await self._get_questions(content_id)
            session = QuestionSession(
                child_id=child_id,
                content_id=content_id,
                total_questions=len(questions),
            )
            self.db.add(session)
            await self.db.flush()

            # Grade answers
            correct_count = 0
            total_points = 0
            answer_results = []

            for answer in answers:
                question = next(
                    (q for q in questions if q.id == answer["question_id"]), None
                )
                if not question:
                    continue

                is_correct = self._check_answer(question, answer["answer"])

                if is_correct:
                    correct_count += 1
                    total_points += question.points

                answer_record = QuestionAnswer(
                    session_id=session.id,
                    question_id=question.id,
                    answer=answer["answer"],
                    is_correct=is_correct,
                )
                self.db.add(answer_record)
                answer_results.append({
                    "question_id": question.id,
                    "is_correct": is_correct,
                })

            # Update session
            session.correct_answers = correct_count
            session.points_earned = total_points
            session.completed_at = datetime.utcnow()

            # Award points
            if total_points > 0:
                await self.point_service.earn(
                    child_id=child_id,
                    amount=total_points,
                    source_type="content_questions",
                    source_id=session.id,
                )
                progress.points_earned = True

            await self.db.commit()

        return QuestionResultResponse(
            correct_count=correct_count,
            total_questions=len(questions),
            points_earned=total_points,
            answers=answer_results,
        )
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-BE-AUTH-001 | Upstream | Pending | Auth context |
| SPEC-BE-POINT-001 | Upstream | Pending | Point awarding |
| SPEC-BE-AI-001 | Parallel | Pending | Question generation |
| File Storage | Service | Required | Content storage |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Content delivery performance | Medium | Medium | CDN, lazy loading |
| Question quality | Medium | Medium | AI tuning, manual review |
| Answer grading accuracy | Medium | Low | Flexible matching, manual review |

---

## Acceptance Criteria

### Content Access
- [ ] Given child age, when browsing, then only age-appropriate content shown
- [ ] Given free content, when accessed, then available immediately
- [ ] Given premium content, when unlocked, then points deducted

### Reading Progress
- [ ] Given reading started, when progress updated, then saved correctly
- [ ] Given reading complete, when marked, then questions available
- [ ] Given previous progress, when resuming, then position restored

### Question System
- [ ] Given questions exist, when session starts, then all questions available
- [ ] Given correct answer, when submitted, then points awarded
- [ ] Given already earned points, when submitting, then rejected

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-ENTERTAIN-001 | Upstream | Frontend display |
| SPEC-BE-AI-001 | Parallel | Question generation |
| SPEC-BE-POINT-001 | Downstream | Point awarding |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
