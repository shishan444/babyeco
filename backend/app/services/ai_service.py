"""AI service for chat and question generation."""

import json
import re
from collections.abc import AsyncGenerator
from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai import ChatMessage, ChatSession, SafetyFilterResult

if TYPE_CHECKING:
    pass


class ContentFilterResult:
    """Result of content filtering."""

    def __init__(
        self,
        is_safe: bool = True,
        flags: list[tuple[str, str]] | None = None,
        should_notify_parent: bool = False,
    ):
        self.is_safe = is_safe
        self.flags = flags or []
        self.should_notify_parent = should_notify_parent


class AIService:
    """Service for AI-powered chat and question generation.

    @MX:ANCHOR
    Core AI service handling chat and content generation.
    Integrates with OpenAI/Anthropic APIs.
    """

    def __init__(self):
        # Initialize OpenAI client
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.AI_MODEL or "gpt-4"

    async def generate_response(
        self,
        message: str,
        child_age: int,
        conversation_history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Generate AI response for child's question.

        @MX:NOTE
        Streams response chunks for real-time display.
        Uses age-appropriate prompts.
        """
        if not self.openai:
            # Fallback response when API not configured
            yield "抱歉，我现在无法回答。请稍后再试。"
            return

        system_prompt = self._build_system_prompt(child_age)

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": message})

        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                max_tokens=300,
                temperature=0.7,
            )

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception:
            yield "抱歉，我遇到了一些问题。请稍后再试。"

    def _build_system_prompt(self, child_age: int) -> str:
        """Build age-appropriate system prompt.

        @MX:NOTE
        Tailors prompt complexity to child's age.
        """
        base = """你是Eco，一个友善的AI学习伙伴，专门陪伴孩子们学习和探索。

你的回答必须：
- 适合儿童的年龄和理解能力
- 有教育意义且鼓励好奇心
- 安全和积极
- 简洁（最多200字）

如果被问到不适合的话题，请礼貌地引导到学习相关的话题。"""

        if child_age <= 8:
            base += "\n\n请使用简单的词语、短句子和有趣的例子。"
        else:
            base += "\n\n可以使用更复杂的解释，但要保持有趣和吸引人。"

        return base

    async def generate_content_questions(
        self,
        content_text: str,
        age_range: tuple[int, int],
        count: int = 3,
    ) -> list[dict]:
        """Generate questions based on content.

        @MX:NOTE
        Creates age-appropriate questions for content review.
        """
        if not self.openai:
            return []

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

Format as JSON array with keys: question_text, question_type, options, correct_answer, hint"""

        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("questions", [])

        except Exception:
            return []


class ContentFilter:
    """Multi-layer content filtering for child safety.

    @MX:ANCHOR
    Safety filtering service for AI interactions.
    Detects concerning content and triggers notifications.
    """

    def __init__(self):
        # Patterns for emotional distress
        self.emotional_patterns = [
            r"\b(hurt myself|kill myself|want to die|don't want to live)\b",
            r"\b(sad|depressed|alone)\b.*\b(all the time|forever|always)\b",
        ]

        # Patterns for safety concerns
        self.safety_patterns = [
            r"\b(address|phone number|where I live|my location)\b",
            r"\b(meet|meet up|meeting)\b.*\b(stranger|someone online|internet)\b",
            r"\b(secret|don't tell|keep it secret)\b.*\b(adult|grown-up)\b",
        ]

        # Patterns for inappropriate topics
        self.inappropriate_patterns = [
            # Add patterns for age-inappropriate topics
        ]

    def check_input(self, content: str) -> ContentFilterResult:
        """Check user input before sending to AI.

        @MX:NOTE
        Returns filter result with flags and notification status.
        """
        flags = []

        for pattern in self.emotional_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                flags.append(("emotional", "high"))

        for pattern in self.safety_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                flags.append(("safety", "high"))

        return ContentFilterResult(
            is_safe=len(flags) == 0,
            flags=flags,
            should_notify_parent=len(flags) > 0,
        )

    def check_output(self, content: str) -> ContentFilterResult:
        """Check AI output before returning to child.

        @MX:NOTE
        Validates response for safety and appropriateness.
        """
        # Basic checks for problematic output
        flags = []

        # Check for any leaked sensitive information
        if re.search(r"\b\d{3}-\d{3}-\d{4}\b", content):  # Phone numbers
            flags.append(("safety", "medium"))

        return ContentFilterResult(
            is_safe=len(flags) == 0,
            flags=flags,
            should_notify_parent=len(flags) > 0,
        )

    def should_redirect(self, content: str) -> tuple[bool, str | None]:
        """Check if question is out of scope.

        @MX:NOTE
        Returns redirect status and suggested topic.
        """
        out_of_scope_keywords = [
            "medical advice",
            "legal advice",
            "financial advice",
            "投资",
            "股票",
            "医疗诊断",
            "法律建议",
        ]

        for keyword in out_of_scope_keywords:
            if keyword.lower() in content.lower():
                return (True, "有趣的科学知识")

        return (False, None)


class ChatService:
    """Service for managing chat sessions and messages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, child_id: UUID) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(
            child_id=child_id,
            status="active",
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_or_create_session(
        self,
        child_id: UUID,
        session_id: UUID | None = None,
    ) -> ChatSession:
        """Get existing session or create new one."""
        if session_id:
            result = await self.db.execute(
                select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.child_id == child_id,
                    ChatSession.status == "active",
                )
            )
            session = result.scalar_one_or_none()
            if session:
                return session

        return await self.create_session(child_id)

    async def save_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        token_count: int | None = None,
    ) -> ChatMessage:
        """Save a chat message."""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            token_count=token_count,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_conversation_history(
        self,
        session_id: UUID,
        limit: int = 10,
    ) -> list[dict]:
        """Get conversation history for context."""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()

        return [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(messages)
        ]

    async def get_child_sessions(
        self,
        child_id: UUID,
        limit: int = 20,
    ) -> list[ChatSession]:
        """Get chat sessions for a child."""
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.child_id == child_id)
            .order_by(ChatSession.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def end_session(self, session_id: UUID) -> None:
        """End a chat session."""
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.ended_at = datetime.utcnow()
            session.status = "ended"
            await self.db.commit()


class DailyUsageService:
    """Service for tracking daily AI usage limits."""

    DAILY_LIMIT = 50  # Default daily question limit

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_usage(self, child_id: UUID) -> dict:
        """Get today's usage for a child."""
        today = date.today()

        # Count today's messages
        result = await self.db.execute(
            select(func.count(ChatMessage.id))
            .join(ChatSession)
            .where(
                ChatSession.child_id == child_id,
                func.date(ChatMessage.created_at) == today,
                ChatMessage.role == "user",
            )
        )
        count = result.scalar() or 0

        return {
            "child_id": str(child_id),
            "date": today.isoformat(),
            "question_count": count,
            "limit": self.DAILY_LIMIT,
            "remaining": max(0, self.DAILY_LIMIT - count),
        }

    async def can_ask_question(self, child_id: UUID) -> bool:
        """Check if child can ask more questions today."""
        usage = await self.get_usage(child_id)
        return usage["remaining"] > 0


class SafetyFilterService:
    """Service for managing safety filter results."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_flag(
        self,
        message_id: UUID,
        filter_type: str,
        flagged: bool,
        reason: str | None = None,
    ) -> SafetyFilterResult:
        """Create a safety filter result record."""
        result = SafetyFilterResult(
            message_id=message_id,
            filter_type=filter_type,
            flagged=flagged,
            reason=reason,
        )
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)
        return result

    async def get_pending_flags(
        self,
        child_id: UUID | None = None,
    ) -> list[SafetyFilterResult]:
        """Get pending safety filter results for review."""
        query = select(SafetyFilterResult).where(
            SafetyFilterResult.reviewed_at.is_(None)
        )

        if child_id:
            query = query.join(ChatMessage).join(ChatSession).where(
                ChatSession.child_id == child_id
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())
