# SPEC-BE-AI-001: AI Q&A API

## Overview

Implement the AI-powered question and answer API for the child chat interface.

**Business Context**: The AI Q&A API provides safe, age-appropriate responses to children's questions. All content is filtered and concerning topics trigger parent notifications.

**Target Users**:
- Primary: Child app (chat interface)
- Secondary: Entertainment module (content questions)

---

## Technical Constraints

### Framework and Versions
- FastAPI (Python 3.11+)
- OpenAI API / Anthropic Claude API
- Redis for response caching
- Streaming response support

### Dependencies
- SPEC-BE-AUTH-001 (Authentication API)
- Notification Service

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall validate all inputs before processing.

```
Given an AI question request
When received
Then input is sanitized
And length limits are enforced
And appropriate context is attached
```

**UR-002**: The system shall filter all AI responses for age appropriateness.

```
Given an AI response
When generated
Then content passes through safety filters
And inappropriate content is blocked or modified
And response is suitable for child's age
```

**UR-003**: The system shall enforce daily question limits.

```
Given a child asks questions
When daily limit is checked
Then count is compared against configured limit
And requests over limit are rejected
```

### Event-Driven Requirements

**EDR-001**: When a question is received, the system shall generate an age-appropriate response.

```
Given a valid question from a child
When processed
Then context includes child's age
And response is tailored for comprehension level
And streaming response begins within 2 seconds
```

**EDR-002**: When content is flagged as concerning, the system shall notify parents.

```
Given question or response triggers content flag
When flag is detected
Then conversation continues normally for child
And parent notification is queued
And flag is logged with context
```

**EDR-003**: When an out-of-scope question is asked, the system shall redirect politely.

```
Given a question outside appropriate scope
When detected
Then a friendly refusal response is generated
And appropriate topic suggestions are provided
```

**EDR-004**: When content questions are requested, the system shall generate context-aware questions.

```
Given content ID for question generation
When requested
Then AI generates questions based on content
And questions are age-appropriate
And correct answers are determined
```

### State-Driven Requirements

**SDR-001**: While a response is streaming, the system shall maintain connection.

```
Given a streaming response is in progress
When chunks are generated
Then they are sent immediately
And connection is kept alive
And errors are handled gracefully
```

**SDR-002**: While daily limit is reached, the system shall block further questions.

```
Given daily limit is exhausted
When a new question is asked
Then request is rejected
And limit reset time is provided
```

### Optional Requirements

**OR-001**: The system MAY cache common responses.

```
Given a repeated question
When cache exists
Then cached response is returned
And no AI call is needed
```

**OR-002**: The system MAY support conversation context.

```
Given ongoing conversation
When new question is asked
Then previous context is included
And follow-up questions are contextual
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT return unfiltered AI responses.

```
Given any AI response
When generated
Then it passes through all safety layers
And raw AI output is never directly exposed
```

**UBR-002**: The system shall NOT store conversations indefinitely.

```
Given conversation history
When retention period expires
Then history is deleted
And retention is configurable
```

---

## Technical Solution

### API Endpoints

```yaml
# Chat Interface (Child)
POST /api/v1/child/ai/chat
  Headers: Authorization: Bearer {token}
  Request: { message: str, conversation_id?: UUID }
  Response: StreamingResponse

POST /api/v1/child/ai/chat/stream
  Headers: Authorization: Bearer {token}
  Request: { message: str, conversation_id?: UUID }
  Response: text/event-stream

GET /api/v1/child/ai/conversations
  Headers: Authorization: Bearer {token}
  Response: [Conversation]

GET /api/v1/child/ai/conversations/{conversation_id}
  Headers: Authorization: Bearer {token}
  Response: Conversation

DELETE /api/v1/child/ai/conversations/{conversation_id}
  Headers: Authorization: Bearer {token}
  Response: { success: true }

# Question Generation (Internal)
POST /internal/v1/ai/generate-questions
  Request: { content_id: UUID, content_text: str, age_range: [int, int], count: int }
  Response: [GeneratedQuestion]

# Content Flag Review (Parent)
GET /api/v1/ai/flags
  Headers: Authorization: Bearer {token}
  Query: child_id?, status?, start_date?, end_date?
  Response: [ContentFlag]

PATCH /api/v1/ai/flags/{flag_id}
  Headers: Authorization: Bearer {token}
  Request: { status: str, notes?: str }
  Response: ContentFlag
```

### Data Models

```python
# models/ai.py
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    ended_at: Mapped[datetime | None]
    message_count: Mapped[int] = mapped_column(default=0)

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str]  # user, assistant
    content: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

class ContentFlag(Base):
    __tablename__ = "content_flags"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"))
    message_id: Mapped[UUID] = mapped_column(ForeignKey("messages.id"))
    flag_type: Mapped[str]  # emotional, inappropriate, safety
    severity: Mapped[str]  # low, medium, high
    context: Mapped[str]  # The flagged content
    reason: Mapped[str]  # AI explanation
    status: Mapped[str]  # pending, reviewed, dismissed
    reviewed_by: Mapped[UUID | None]
    reviewed_at: Mapped[datetime | None]
    notes: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

class DailyUsage(Base):
    __tablename__ = "daily_usage"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    date: Mapped[date]
    question_count: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        UniqueConstraint('child_id', 'date'),
    )
```

### AI Client Implementation

```python
# services/ai_service.py
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

class AIService:
    def __init__(self, settings: Settings):
        self.openai = AsyncOpenAI(api=settings.openai_api_key)
        self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.ai_model  # "gpt-4" or "claude-3"

    async def generate_response(
        self,
        message: str,
        child_age: int,
        conversation_history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        # Build system prompt based on age
        system_prompt = self._build_system_prompt(child_age)

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": message})

        # Stream response
        if self.model.startswith("gpt"):
            async for chunk in self._stream_openai(messages):
                yield chunk
        else:
            async for chunk in self._stream_anthropic(messages):
                yield chunk

    def _build_system_prompt(self, child_age: int) -> str:
        base = """You are Eco, a friendly AI learning buddy for children.
Your responses must be:
- Age-appropriate and easy to understand
- Educational and encouraging
- Safe and positive
- Concise (max 200 words)

If asked about inappropriate topics, politely redirect to learning topics."""

        if child_age <= 8:
            base += "\n\nUse simple words, short sentences, and fun examples."
        else:
            base += "\n\nYou can use more complex explanations but keep them engaging."

        return base

    async def _stream_openai(
        self, messages: list[dict]
    ) -> AsyncGenerator[str, None]:
        response = await self.openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            stream=True,
            max_tokens=300,
            temperature=0.7,
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_content_questions(
        self,
        content_text: str,
        age_range: tuple[int, int],
        count: int = 3,
    ) -> list[dict]:
        prompt = f"""Based on the following content, generate {count} age-appropriate
questions for children aged {age_range[0]}-{age_range[1]}.

Content:
{content_text[:2000]}

For each question, provide:
1. The question text
2. Type (multiple_choice or short_answer)
3. Options (for multiple choice, 4 options)
4. The correct answer
5. A hint for struggling children

Format as JSON array."""

        response = await self.openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        return json.loads(response.choices[0].message.content)["questions"]
```

### Content Filtering

```python
# services/content_filter.py
class ContentFilter:
    """Multi-layer content filtering for child safety"""

    def __init__(self):
        # Patterns to detect concerning content
        self.emotional_patterns = [
            r"\b(hurt myself|kill myself|want to die)\b",
            r"\b(sad|depressed|alone)\b.*\b(all the time|forever)\b",
        ]
        self.safety_patterns = [
            r"\b(address|phone number|where I live)\b",
            r"\b(meet|meet up)\b.*\b(stranger|online)\b",
        ]
        self.inappropriate_patterns = [
            # Patterns for age-inappropriate topics
        ]

    def check_input(self, content: str) -> FilterResult:
        """Check user input before sending to AI"""
        flags = []

        for pattern in self.emotional_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                flags.append(("emotional", "medium"))

        for pattern in self.safety_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                flags.append(("safety", "high"))

        return FilterResult(
            is_safe=len(flags) == 0,
            flags=flags,
            should_notify_parent=len(flags) > 0,
        )

    def check_output(self, content: str) -> FilterResult:
        """Check AI output before returning to child"""
        # Check for any problematic content
        # Modify or block if necessary
        pass

    def should_redirect(self, content: str) -> tuple[bool, str | None]:
        """Check if question is out of scope"""
        out_of_scope = [
            "medical advice",
            "legal advice",
            "financial advice",
            "mature topics",
        ]
        # Return (should_redirect, suggested_topic)
        pass
```

### Streaming Endpoint

```python
# routers/ai.py
from fastapi.responses import StreamingResponse

@router.post("/child/ai/chat/stream")
async def stream_chat(
    request: ChatRequest,
    current_child: Child = Depends(get_current_child),
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
    content_filter: ContentFilter = Depends(get_content_filter),
):
    # Check daily limit
    usage = await check_daily_usage(db, current_child.id)
    if usage.question_count >= current_child.daily_question_limit:
        raise DailyLimitExceededError()

    # Filter input
    input_result = content_filter.check_input(request.message)
    if input_result.should_notify_parent:
        await create_content_flag(
            db, current_child.id, request.message, input_result.flags
        )

    # Check for redirect
    should_redirect, suggestion = content_filter.should_redirect(request.message)
    if should_redirect:
        return StreamingResponse(
            iter([f"I'd love to help you learn about {suggestion} instead! "
                  f"What would you like to know about that?"]),
            media_type="text/event-stream",
        )

    # Get conversation history
    history = await get_conversation_history(db, request.conversation_id)

    # Stream response
    async def generate():
        full_response = ""
        async for chunk in ai_service.generate_response(
            request.message, current_child.age, history
        ):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        # Filter output
        output_result = content_filter.check_output(full_response)
        if output_result.should_notify_parent:
            await create_content_flag(
                db, current_child.id, full_response, output_result.flags, is_response=True
            )

        # Save conversation
        await save_message(db, request.conversation_id, "user", request.message)
        await save_message(db, request.conversation_id, "assistant", full_response)

        # Update usage
        await increment_daily_usage(db, current_child.id)

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-BE-AUTH-001 | Upstream | Pending | Auth context |
| OpenAI/Anthropic API | External | Required | AI model access |
| Redis | Cache | Required | Response caching |
| Notification Service | Service | Required | Parent alerts |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| AI hallucination | High | Medium | Strict prompting, output filtering |
| API rate limits | Medium | Medium | Caching, fallback models |
| Latency | Medium | Low | Streaming, caching |
| Inappropriate content | High | Low | Multi-layer filtering |

---

## Acceptance Criteria

### Chat Interface
- [ ] Given valid question, when asked, then streaming response returns
- [ ] Given concerning input, when detected, then parent notified
- [ ] Given out-of-scope, when detected, then redirect shown

### Content Filtering
- [ ] Given inappropriate input, when checked, then flagged
- [ ] Given inappropriate output, when checked, then modified/blocked
- [ ] Given safety issue, when detected, then high-priority alert

### Question Generation
- [ ] Given content, when questions generated, then age-appropriate
- [ ] Given questions, when answers checked, then accurate

### Rate Limiting
- [ ] Given daily limit, when reached, then blocked
- [ ] Given limit reset, when new day, then counter resets

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-AI-001 | Upstream | Frontend chat UI |
| SPEC-BE-ENTERTAIN-001 | Upstream | Content question generation |
| SPEC-FE-PARENT-001 | Downstream | Flag review interface |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
