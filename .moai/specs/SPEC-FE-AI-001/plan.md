# SPEC-FE-AI-001: AI Q&A Interface

## Overview

Implement the AI-powered question and answer interface for the child-facing application, enabling children to ask questions and receive age-appropriate responses.

**Business Context**: The AI Q&A feature allows children to satisfy their curiosity safely. All responses are age-appropriate, and concerning content triggers parent notification.

**Target Users**:
- Primary: Children aged 6-12 asking questions
- Secondary: Parents monitoring AI interactions

---

## Technical Constraints

### Framework and Versions
- Next.js 22.x with App Router
- React 19.x
- Zustand for state management
- Streaming responses for AI

### Dependencies
- SPEC-DESIGN-001 (Child App Design)
- SPEC-DESIGN-003 (Design System)
- SPEC-FE-AUTH-002 (Child Auth Module)
- SPEC-BE-AI-001 (Backend AI API)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall display a chat interface with message history.

```
Given a child opens the AI Q&A screen
When the screen loads
Then a chat interface is displayed
And previous messages (if any) are shown
And a message input is at the bottom
```

**UR-002**: The system shall display quick question suggestions.

```
Given a child views the AI chat
When the conversation is empty or idle
Then suggested questions are displayed
And tapping a suggestion sends it as a question
```

**UR-003**: The system shall show a child-friendly AI avatar.

```
Given the AI is responding
When the response appears
Then a friendly AI avatar is displayed
And the avatar animates while "thinking"
```

### Event-Driven Requirements

**EDR-001**: When a child sends a question, the system shall stream the AI response.

```
Given a child types and sends a question
When the message is sent
Then a typing indicator appears
And the response streams in character by character
And the avatar animates during response
```

**EDR-002**: When a response is complete, the system shall offer follow-up suggestions.

```
Given an AI response is complete
When the response finishes
Then follow-up question suggestions appear
And the child can tap to ask follow-ups
```

**EDR-003**: When content is flagged as concerning, the system shall notify parents.

```
Given a child's question or the AI's response is flagged
When the flag is triggered
Then the conversation continues normally for the child
And a notification is sent to the parent
And the flagged content is logged
```

**EDR-004**: When a child asks an out-of-scope question, the system shall redirect politely.

```
Given a child asks something outside appropriate scope
When the AI detects this
Then a friendly refusal message is shown
And suggestions for appropriate topics are offered
```

### State-Driven Requirements

**SDR-001**: While the AI is responding, the system shall disable the input.

```
Given the AI is generating a response
When the child tries to send another message
Then the input is disabled
And a "Please wait..." indicator shows
```

**SDR-002**: While offline, the system shall show cached responses if available.

```
Given the device is offline
When the child views the AI chat
Then cached conversation is visible
And new messages cannot be sent
And "You're offline" indicator shows
```

**SDR-003**: While the daily question limit is reached, the system shall show limit message.

```
Given daily question limit is reached
When the child tries to ask more
Then a friendly limit message shows
And the limit resets message displays
And parent can adjust limit
```

### Optional Requirements

**OR-001**: The system MAY support voice input.

```
Given a device supports voice input
When the child taps the microphone
Then voice recording starts
And speech is converted to text
And the question is sent
```

**OR-002**: The system MAY support text-to-speech for responses.

```
Given a child prefers audio
When they tap the speaker icon
Then the AI response is read aloud
And playback controls are available
```

**OR-003**: The system MAY support conversation export for parents.

```
Given a parent wants to review conversations
When they access the parent app
Then they can view AI chat history
And can export conversations
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT allow unfiltered AI responses.

```
Given any question is asked
When the AI generates a response
Then the response passes through content filters
And inappropriate content is blocked or modified
```

**UBR-002**: The system shall NOT store conversations indefinitely.

```
Given conversations exist
When retention period passes
Then old conversations are deleted
And retention is configurable by parent
```

---

## Technical Solution

### Component Structure

```
src/
├── app/
│   └── (child)/
│       └── (authenticated)/
│           └── ai-chat/
│               └── page.tsx
├── components/
│   ├── ai-chat/
│   │   ├── ChatInterface.tsx
│   │   ├── MessageList.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── UserMessage.tsx
│   │   ├── AIMessage.tsx
│   │   ├── AIAvatar.tsx
│   │   ├── TypingIndicator.tsx
│   │   ├── ChatInput.tsx
│   │   ├── QuickSuggestions.tsx
│   │   ├── VoiceInput.tsx
│   │   ├── TextToSpeech.tsx
│   │   └── LimitWarning.tsx
│   └── ui/
│       └── (design system components)
├── lib/
│   ├── ai-chat/
│   │   ├── ai-client.ts
│   │   ├── content-filter.ts
│   │   └── suggestions.ts
│   └── hooks/
│       ├── useChat.ts
│       ├── useStreamingResponse.ts
│       └── useVoiceInput.ts
└── stores/
    └── chat-store.ts
```

### Message Components

```tsx
// MessageBubble.tsx
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  isFlagged?: boolean;
}

// UserMessage.tsx - Child's messages
// - Right-aligned
// - Primary color background
// - Text in inverse color

// AIMessage.tsx - AI responses
// - Left-aligned
// - Light background
// - AI avatar on left
// - Streaming animation for in-progress
```

### Chat Input Component

```tsx
// ChatInput.tsx
interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
}

// Features:
// - Text input with send button
// - Voice input button (optional)
// - Character counter
// - Disabled state with visual feedback
// - Enter to send
```

### Quick Suggestions Component

```tsx
// QuickSuggestions.tsx
interface QuickSuggestionsProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
}

// Default suggestions:
const DEFAULT_SUGGESTIONS = [
  "Why is the sky blue?",
  "How do plants grow?",
  "What makes rain?",
  "Tell me a fun fact!",
];

// Context-aware suggestions after responses
```

### State Management

```typescript
// chat-store.ts
interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  isOffline: boolean;
  dailyLimit: {
    used: number;
    max: number;
    resetsAt: Date;
  };
  suggestions: string[];
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchHistory: () => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  appendStreamChunk: (chunk: string) => void;
  completeStream: () => void;
  selectSuggestion: (suggestion: string) => void;
  checkLimit: () => Promise<void>;
}
```

### Streaming Response Handler

```typescript
// useStreamingResponse.ts
export function useStreamingResponse() {
  const { appendStreamChunk, completeStream } = useChatStore();

  const streamResponse = async (question: string) => {
    const response = await fetch('/api/v1/ai/chat/stream', {
      method: 'POST',
      body: JSON.stringify({ question }),
      headers: { 'Content-Type': 'application/json' },
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      appendStreamChunk(chunk);
    }

    completeStream();
  };

  return { streamResponse };
}
```

### Content Filtering

```typescript
// content-filter.ts
export function filterContent(content: string): FilterResult {
  // Client-side pre-filter (backend does full filtering)
  const blockedPatterns = [
    // Patterns for inappropriate content
  ];

  for (const pattern of blockedPatterns) {
    if (pattern.test(content)) {
      return {
        isSafe: false,
        reason: 'Content flagged for review',
        shouldNotifyParent: true,
      };
    }
  }

  return { isSafe: true };
}
```

### AI Avatar Animation

```tsx
// AIAvatar.tsx
interface AIAvatarProps {
  isThinking: boolean;
  size?: 'sm' | 'md' | 'lg';
}

// Animations:
// - Idle: Subtle breathing/floating
// - Thinking: Pulsing glow, eyes following
// - Speaking: Mouth animation (optional)

const avatarAnimations = {
  idle: {
    y: [0, -5, 0],
    transition: { duration: 2, repeat: Infinity },
  },
  thinking: {
    scale: [1, 1.1, 1],
    transition: { duration: 0.5, repeat: Infinity },
  },
};
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-DESIGN-001 | Design | Completed | AI chat UI designs |
| SPEC-DESIGN-003 | Design | Completed | Design system |
| SPEC-FE-AUTH-002 | Auth | Pending | Child session |
| SPEC-BE-AI-001 | API | Pending | AI endpoints |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| AI hallucination | High | Medium | Strict prompting, content filters |
| Response latency | Medium | Medium | Streaming responses, caching |
| Inappropriate content | High | Low | Multi-layer content filtering |
| Daily limit abuse | Low | Medium | Server-side enforcement |

---

## Acceptance Criteria

### Chat Interface
- [ ] Given valid session, when page loads, then chat displays
- [ ] Given history exists, when loading, then messages show
- [ ] Given suggestions configured, when idle, then suggestions show

### Message Flow
- [ ] Given question sent, when processing, then typing indicator shows
- [ ] Given response streaming, when receiving, then text appears progressively
- [ ] Given response complete, when finished, then follow-ups show

### Safety Features
- [ ] Given concerning content, when detected, then parent notified
- [ ] Given out-of-scope, when detected, then redirect shown
- [ ] Given limit reached, when trying to send, then limit message shows

### Optional Features
- [ ] Given voice input, when tapped, then recording starts
- [ ] Given TTS enabled, when tapped, then response is read

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-ENTERTAIN-001 | Upstream | Question integration from content |
| SPEC-BE-AI-001 | Parallel | Backend AI API |
| SPEC-FE-PARENT-001 | Downstream | Parent notification for flags |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
