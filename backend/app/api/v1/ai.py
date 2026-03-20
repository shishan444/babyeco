"""AI chat and question generation API endpoints."""

import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_child
from app.core.database import get_db
from app.models.child_profile import ChildProfile
from app.schemas.ai import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionResponse,
    ContentFlagResponse,
    ContentFlagUpdate,
    ConversationResponse,
    DailyUsageResponse,
)
from app.services.ai_service import (
    AIService,
    ChatService,
    ContentFilter,
    DailyUsageService,
    SafetyFilterService,
)

router = APIRouter()


def get_ai_service() -> AIService:
    """Get AI service instance."""
    return AIService()


def get_content_filter() -> ContentFilter:
    """Get content filter instance."""
    return ContentFilter()


@router.post("/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageCreate,
    current_child: Annotated[ChildProfile, Depends(get_current_child)],
    db: Annotated[AsyncSession, Depends(get_db)],
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    content_filter: Annotated[ContentFilter, Depends(get_content_filter)],
):
    """Send a chat message and get AI response.

    @MX:NOTE
    Non-streaming endpoint for simple chat interactions.
    """
    # Check daily limit
    usage_service = DailyUsageService(db)
    if not await usage_service.can_ask_question(current_child.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily question limit reached. Please try again tomorrow.",
        )

    # Filter input
    input_result = content_filter.check_input(request.content)
    if input_result.should_notify_parent:
        # Log content flag for parent review
        pass

    # Get or create session
    chat_service = ChatService(db)
    session = await chat_service.get_or_create_session(
        current_child.id,
        request.conversation_id,
    )

    # Get conversation history
    history = await chat_service.get_conversation_history(session.id)

    # Generate response (collect all chunks)
    full_response = ""
    async for chunk in ai_service.generate_response(
        request.content, current_child.age, history
    ):
        full_response += chunk

    # Filter output
    output_result = content_filter.check_output(full_response)
    if output_result.should_notify_parent:
        # Log for parent notification
        pass

    # Save messages
    await chat_service.save_message(session.id, "user", request.content)
    await chat_service.save_message(session.id, "assistant", full_response)

    return ChatMessageResponse(
        id=UUID("00000000-0000-0000-000000000001"),
        role="assistant",
        content=full_response,
        created_at=datetime.utcnow(),
    )


@router.post("/chat/stream")
async def stream_chat(
    request: ChatMessageCreate,
    current_child: Annotated[ChildProfile, Depends(get_current_child)],
    db: Annotated[AsyncSession, Depends(get_db)],
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    content_filter: Annotated[ContentFilter, Depends(get_content_filter)],
):
    """Stream AI chat response.

    @MX:NOTE
    Streaming endpoint for real-time chat display.
    """
    # Check daily limit
    usage_service = DailyUsageService(db)
    if not await usage_service.can_ask_question(current_child.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily question limit reached.",
        )

    # Filter input
    input_result = content_filter.check_input(request.content)
    if input_result.should_notify_parent:
        # Log content flag for parent review
        pass

    # Check for redirect
    should_redirect, suggestion = content_filter.should_redirect(request.content)
    if should_redirect:
        redirect_msg = f"I'd love to help you learn about {suggestion} instead! What would you like to know about that?"
        return StreamingResponse(
            iter([f"data: {json.dumps({'chunk': redirect_msg})}\n\n"]),
            media_type="text/event-stream",
        )

    # Get or create session
    chat_service = ChatService(db)
    session = await chat_service.get_or_create_session(
        current_child.id,
        request.conversation_id
    )

    # Get conversation history
    history = await chat_service.get_conversation_history(session.id)

    # Stream response
    async def generate():
        full_response = ""
        async for chunk in ai_service.generate_response(
            request.content, current_child.age, history
        ):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        # Filter output
        output_result = content_filter.check_output(full_response)
        if output_result.should_notify_parent:
            # Log for parent notification
            pass

        # Save messages
        await chat_service.save_message(session.id, "user", request.content)
        await chat_service.save_message(session.id, "assistant", full_response)

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations", response_model=list[ChatSessionResponse])
async def list_conversations(
    current_child: Annotated[ChildProfile, Depends(get_current_child)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all conversations for the child."""
    chat_service = ChatService(db)
    sessions = await chat_service.get_child_sessions(current_child.id)
    return sessions


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_child: Annotated[ChildProfile, Depends(get_current_child)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific conversation with messages."""
    chat_service = ChatService(db)
    session = await chat_service.get_or_create_session(
        current_child.id,
        conversation_id,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    if session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not active"
        )

    if session.child_id != current_child.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your session"
        )

    # Get messages
    messages = await chat_service.get_conversation_history(session.id)

    return ConversationResponse(
        session=session,
        messages=messages,
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID,
    current_child: Annotated[ChildProfile, Depends(get_current_child)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a conversation."""
    chat_service = ChatService(db)
    await chat_service.end_session(conversation_id)
    return None


@router.get("/usage", response_model=DailyUsageResponse)
async def get_daily_usage(
    current_child: Annotated[ChildProfile, Depends(get_current_child)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get today's AI usage for a child."""
    usage_service = DailyUsageService(db)
    return await usage_service.get_usage(current_child.id)


@router.get("/flags", response_model=list[ContentFlagResponse])
async def list_content_flags(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all content flags for parent review."""
    safety_service = SafetyFilterService(db)
    flags = await safety_service.get_pending_flags()
    return [
        ContentFlagResponse(
            id=flag.id,
            child_id=flag.message.session.child_id,
            conversation_id=flag.message.session_id,
            message_id=flag.message_id,
            flag_type=flag.filter_type,
            severity="medium",
            context=flag.message.content,
            reason=flag.reason,
            status="pending",
            reviewed_at=flag.reviewed_at,
            notes=None,
            created_at=flag.created_at,
        )
        for flag in flags
    ]


@router.patch("/flags/{flag_id}", response_model=ContentFlagResponse)
async def update_content_flag(
    flag_id: UUID,
    update: ContentFlagUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a content flag status."""
    # Implementation would update the flag in the database
    return None  # Placeholder
