# SPEC-FE-ENTERTAIN-001: Entertainment Module

## Overview

Implement the entertainment content browsing and reading interface for the child-facing application, including eBooks and AI-generated questions.

**Business Context**: The Entertainment module provides educational and engaging content for children. After reading, children answer AI-generated questions to earn bonus points, combining entertainment with learning.

**Target Users**:
- Primary: Children aged 6-12 consuming content
- Secondary: Parents monitoring content consumption

---

## Technical Constraints

### Framework and Versions
- Next.js 22.x with App Router
- React 19.x
- Zustand for state management
- Reading progress persistence
- AI question integration

### Dependencies
- SPEC-DESIGN-001 (Child App Design)
- SPEC-DESIGN-003 (Design System)
- SPEC-FE-AUTH-002 (Child Auth Module)
- SPEC-BE-ENTERTAIN-001 (Backend Entertainment API)
- SPEC-BE-AI-001 (Backend AI Q&A API)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall display available content in a gallery format.

```
Given a child opens the Entertainment Hub
When the screen loads
Then content items are displayed in a grid
And each item shows cover image, title, and point reward
```

**UR-002**: The system shall indicate content unlock status.

```
Given a child views content items
When the gallery loads
Then each item shows its unlock status
And free content has no cost badge
And premium content shows point cost
```

**UR-003**: The system shall display reading progress for started content.

```
Given a child has started reading content
When they view the content gallery
Then progress percentage is shown on the item
And they can resume from where they left off
```

### Event-Driven Requirements

**EDR-001**: When a child taps a content item, the system shall open the reader view.

```
Given a child taps a content item
When the item is accessible (free or unlocked)
Then the reading view opens
And displays content with appropriate formatting
And shows progress indicator
```

**EDR-002**: When a child completes reading, the system shall prompt for questions.

```
Given a child finishes reading content
When they reach the end
Then a "Ready for questions?" prompt appears
And shows potential point reward for answering
```

**EDR-003**: When a child answers questions correctly, the system shall award points.

```
Given a child answers AI-generated questions
When they submit answers
Then correct answers earn bonus points
And a summary shows points earned
And celebration animation plays
```

**EDR-004**: When a child unlocks premium content, the system shall deduct points.

```
Given a child taps locked premium content
When they confirm unlock
Then the point cost is deducted
And content becomes accessible
And reading view opens
```

### State-Driven Requirements

**SDR-001**: While reading, the system shall track progress automatically.

```
Given a child is reading content
When they scroll through the content
Then reading progress is tracked
And progress is saved periodically
And resumes on return
```

**SDR-002**: While answering questions, the system shall provide hints after failed attempts.

```
Given a child struggles with a question
When they answer incorrectly twice
Then a hint is offered
And the hint doesn't reveal the full answer
```

**SDR-003**: While content is loading, the system shall display skeleton cards.

```
Given a child opens the Entertainment Hub
When content is being fetched
Then skeleton cards are displayed
And animate to real cards when loaded
```

### Optional Requirements

**OR-001**: The system MAY support adjustable text size in reader.

```
Given a child is reading content
When they access settings
Then text size can be adjusted
And preference is saved for future reading
```

**OR-002**: The system MAY support bookmarking.

```
Given a child is reading content
When they tap bookmark
Then current position is saved
And bookmark icon appears
```

**OR-003**: The system MAY support reading history.

```
Given a child wants to revisit content
When they view history
Then previously read items are listed
And can be re-read without re-earning points
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT allow point earning from same content twice.

```
Given a child has already earned points from content
When they re-read it
Then no additional points are awarded
And the content shows "Completed" status
```

**UBR-002**: The system shall NOT show inappropriate content.

```
Given content is filtered by age appropriateness
When a child browses
Then only age-appropriate content is visible
And content filtering is enforced
```

---

## Technical Solution

### Component Structure

```
src/
├── app/
│   └── (child)/
│       └── (authenticated)/
│           └── entertainment/
│               ├── page.tsx
│               └── [contentId]/
│                   ├── read/
│                   │   └── page.tsx
│                   └── questions/
│                       └── page.tsx
├── components/
│   ├── entertainment/
│   │   ├── EntertainmentHub.tsx
│   │   ├── ContentGrid.tsx
│   │   ├── ContentCard.tsx
│   │   ├── ReaderView.tsx
│   │   ├── ReadingProgress.tsx
│   │   ├── QuestionScreen.tsx
│   │   ├── QuestionCard.tsx
│   │   ├── HintDisplay.tsx
│   │   ├── AnswerResult.tsx
│   │   ├── PointsSummary.tsx
│   │   ├── TextSizeControl.tsx
│   │   └── BookmarkButton.tsx
│   └── ui/
│       └── (design system components)
├── lib/
│   ├── entertainment/
│   │   ├── entertainment-client.ts
│   │   ├── reading-tracker.ts
│   │   └── content-utils.ts
│   └── hooks/
│       ├── useContent.ts
│       ├── useReader.ts
│       └── useQuestions.ts
└── stores/
    └── entertainment-store.ts
```

### Content Card Component

```tsx
// ContentCard.tsx
interface ContentCardProps {
  content: Content;
  onPress: () => void;
}

interface Content {
  id: string;
  title: string;
  description?: string;
  coverImage: string;
  type: 'ebook' | 'video' | 'game'; // MVP: ebook only
  pointCost: number; // 0 for free
  pointReward: number; // Points for completing + questions
  readingTime: number; // Minutes
  category: string;
  ageRange: [number, number]; // e.g., [6, 9]
  progress?: number; // 0-100
  completed: boolean;
}

// Card states:
// - Free: No cost badge
// - Premium (locked): Cost badge with points
// - Premium (unlocked): "Unlocked" badge
// - In progress: Progress bar
// - Completed: Checkmark badge
```

### Reader View Component

```tsx
// ReaderView.tsx
interface ReaderViewProps {
  content: Content;
  onComplete: () => void;
  onProgress: (progress: number) => void;
}

// Features:
// - Clean, distraction-free reading area
// - Adjustable text size (3 sizes)
// - Progress bar at top
// - "Done Reading" button
// - Auto-save progress every 30 seconds
// - Scroll position tracking
```

### Question Screen Component

```tsx
// QuestionScreen.tsx
interface QuestionScreenProps {
  contentId: string;
  questions: Question[];
  onComplete: (correctCount: number, totalPoints: number) => void;
}

interface Question {
  id: string;
  question: string;
  type: 'multiple_choice' | 'short_answer';
  options?: string[]; // For multiple choice
  correctAnswer: string;
  hint: string;
  points: number;
}

// Flow:
// 1. Show question with input
// 2. User submits answer
// 3. Show correct/incorrect feedback
// 4. After 2 wrong: show hint
// 5. Move to next question
// 6. After all: show summary
```

### State Management

```typescript
// entertainment-store.ts
interface EntertainmentState {
  content: Content[];
  readingProgress: Map<string, number>; // contentId -> progress
  bookmarks: string[]; // contentIds
  currentReading: string | null;
  currentQuestions: Question[];
  questionIndex: number;
  correctAnswers: number;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchContent: () => Promise<void>;
  startReading: (contentId: string) => void;
  updateProgress: (contentId: string, progress: number) => void;
  completeReading: (contentId: string) => Promise<Question[]>;
  submitAnswer: (questionId: string, answer: string) => Promise<boolean>;
  finishQuestions: () => void;
}
```

### Reading Progress Tracking

```typescript
// reading-tracker.ts
export function useReadingTracker(contentId: string) {
  const [progress, setProgress] = useState(0);
  const { updateProgress } = useEntertainmentStore();

  useEffect(() => {
    // Calculate progress based on scroll position
    const handleScroll = () => {
      const scrollElement = document.getElementById('reader-content');
      if (!scrollElement) return;

      const scrollTop = scrollElement.scrollTop;
      const scrollHeight = scrollElement.scrollHeight;
      const clientHeight = scrollElement.clientHeight;

      const newProgress = Math.min(
        100,
        Math.round((scrollTop / (scrollHeight - clientHeight)) * 100)
      );

      setProgress(newProgress);
    };

    // Save progress periodically
    const saveInterval = setInterval(() => {
      updateProgress(contentId, progress);
      localStorage.setItem(`reading-progress-${contentId}`, String(progress));
    }, 30000); // 30 seconds

    return () => {
      clearInterval(saveInterval);
      updateProgress(contentId, progress);
    };
  }, [contentId, progress]);

  return { progress };
}
```

### Question Flow

```typescript
// useQuestions.ts
export function useQuestions(contentId: string) {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [wrongAttempts, setWrongAttempts] = useState(0);
  const [showHint, setShowHint] = useState(false);

  const currentQuestion = questions[currentIndex];

  const submitAnswer = async (answer: string): Promise<AnswerResult> => {
    const isCorrect = answer.toLowerCase().trim() ===
                      currentQuestion.correctAnswer.toLowerCase().trim();

    if (isCorrect) {
      // Move to next question
      setCurrentIndex((prev) => prev + 1);
      setWrongAttempts(0);
      setShowHint(false);
      return { isCorrect: true, points: currentQuestion.points };
    } else {
      setWrongAttempts((prev) => prev + 1);
      if (wrongAttempts >= 1) {
        setShowHint(true);
      }
      return { isCorrect: false, hint: showHint ? currentQuestion.hint : null };
    }
  };

  return {
    currentQuestion,
    currentIndex,
    totalQuestions: questions.length,
    showHint,
    submitAnswer,
    isComplete: currentIndex >= questions.length,
  };
}
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-DESIGN-001 | Design | Completed | Entertainment UI designs |
| SPEC-DESIGN-003 | Design | Completed | Design system |
| SPEC-FE-AUTH-002 | Auth | Pending | Child session |
| SPEC-BE-ENTERTAIN-001 | API | Pending | Content endpoints |
| SPEC-BE-AI-001 | API | Pending | AI question generation |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Content loading performance | Medium | Medium | Lazy loading, pagination |
| Question difficulty mismatch | Medium | Medium | AI tuning, age-appropriate filters |
| Reading progress loss | Low | Medium | Local storage backup |
| Content appropriateness | High | Low | Content moderation, age filtering |

---

## Acceptance Criteria

### Content Gallery
- [ ] Given content exists, when page loads, then grid displays correctly
- [ ] Given content types, when browsing, then status badges show
- [ ] Given progress exists, when viewing, then progress bars display

### Reading Experience
- [ ] Given content started, when reading, then progress tracks
- [ ] Given reading complete, when finished, then question prompt shows
- [ ] Given text size changed, when adjusted, then preference saves

### Question System
- [ ] Given questions generated, when displayed, then format correct
- [ ] Given wrong answer, when submitted, then feedback shows
- [ ] Given hint needed, when triggered, then hint displays
- [ ] Given all answered, when complete, then summary shows

### Point Earning
- [ ] Given correct answer, when submitted, then points awarded
- [ ] Given content complete, when finished, then celebration plays

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-POINT-001 | Downstream | Awarded points |
| SPEC-FE-AI-001 | Downstream | AI Q&A interface |
| SPEC-BE-ENTERTAIN-001 | Parallel | Backend content API |
| SPEC-BE-AI-001 | Parallel | Backend AI API |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
