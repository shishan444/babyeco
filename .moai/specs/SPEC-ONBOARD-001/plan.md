# SPEC-ONBOARD-001: Onboarding Flow

## Overview

Implement the first-time user onboarding experience for both parent and child applications.

**Business Context**: A smooth onboarding experience is critical for user retention. This module guides new users through setup and introduces key features.

**Target Users**:
- Primary: New parents setting up their family
- Secondary: New children binding their device

---

## Technical Constraints

### Framework and Versions
- Next.js 22.x with App Router
- React 19.x
- Framer Motion for animations
- Local storage for progress persistence

### Dependencies
- SPEC-FE-AUTH-001 (Parent Auth)
- SPEC-FE-AUTH-002 (Child Auth)
- SPEC-FE-PARENT-001 (Parent Features)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall display a step-by-step onboarding wizard.

```
Given a new user starts onboarding
When the process begins
Then a clear progress indicator is shown
And steps can be navigated forward/backward
```

**UR-002**: The system shall save onboarding progress.

```
Given a user is in onboarding
When they leave and return
Then progress is restored
And they can continue from where they left
```

**UR-003**: The system shall allow skipping non-essential steps.

```
Given an optional onboarding step
When skip is clicked
Then the step is marked complete
And the user proceeds to next step
```

### Event-Driven Requirements

**EDR-001**: When a parent completes family setup, the system shall show success celebration.

```
Given a parent completes all required steps
When setup is finished
Then a celebration animation plays
And the dashboard is introduced
And first task suggestions are shown
```

**EDR-002**: When a child binds their device, the system shall show welcome tutorial.

```
Given a child successfully binds device
When binding completes
Then a welcome animation plays
And key features are highlighted
And first task is introduced
```

**EDR-003**: When onboarding is skipped, the system shall offer to resume later.

```
Given onboarding is incomplete
When user tries to skip
Then a "Resume later" option is shown
And progress is saved
```

### State-Driven Requirements

**SDR-001**: While onboarding is incomplete, the system shall show resume prompt.

```
Given onboarding was started but not completed
When user logs in
Then resume prompt is displayed
And user can continue or skip
```

**SDR-002**: While showing feature highlights, the system shall use tooltips.

```
Given a feature is being introduced
When highlighting occurs
Then a tooltip points to the feature
And a brief description is provided
And dismissal is easy
```

---

## Technical Solution

### Component Structure

```
src/
├── components/
│   ├── onboarding/
│   │   ├── OnboardingWizard.tsx
│   │   ├── ProgressBar.tsx
│   │   ├── WelcomeStep.tsx
│   │   ├── FamilySetupStep.tsx
│   │   ├── ChildAddStep.tsx
│   │   ├── TaskSetupStep.tsx
│   │   ├── RewardSetupStep.tsx
│   │   ├── CompletionStep.tsx
│   │   ├── FeatureHighlight.tsx
│   │   ├── Tooltip.tsx
│   │   ├── TutorialOverlay.tsx
│   │   └── SkipButton.tsx
│   └── ui/
└── hooks/
    └── useOnboarding.ts
```

### Parent Onboarding Flow

```typescript
// Parent onboarding steps
const PARENT_ONBOARDING_STEPS = [
  {
    id: 'welcome',
    title: 'Welcome to BabyEco',
    description: 'Let\'s set up your family',
    component: WelcomeStep,
    required: true,
  },
  {
    id: 'family',
    title: 'Create Your Family',
    description: 'Enter your family details',
    component: FamilySetupStep,
    required: true,
  },
  {
    id: 'children',
    title: 'Add Children',
    description: 'Add your children to get started',
    component: ChildAddStep,
    required: true,
  },
  {
    id: 'first-task',
    title: 'Create Your First Task',
    description: 'Set up a task for your children',
    component: TaskSetupStep,
    required: false,
    skipLabel: 'I\'ll do this later',
  },
  {
    id: 'first-reward',
    title: 'Add a Reward',
    description: 'Create an exciting reward',
    component: RewardSetupStep,
    required: false,
    skipLabel: 'I\'ll do this later',
  },
  {
    id: 'complete',
    title: 'You\'re All Set!',
    description: 'Start your journey',
    component: CompletionStep,
    required: true,
  },
];
```

### Child Onboarding Flow

```typescript
// Child onboarding steps
const CHILD_ONBOARDING_STEPS = [
  {
    id: 'welcome',
    title: 'Hi There!',
    description: 'Let\'s get you started',
    animation: 'wave',
  },
  {
    id: 'code',
    title: 'Enter Your Code',
    description: 'Ask your parent for the code',
    component: CodeInputStep,
  },
  {
    id: 'profile',
    title: 'That\'s You!',
    description: 'Your profile is ready',
    component: ProfileConfirmStep,
  },
  {
    id: 'tour',
    title: 'Let\'s Look Around',
    description: 'Quick tour of your app',
    component: AppTourStep,
  },
  {
    id: 'first-task',
    title: 'Your First Task',
    description: 'Ready to earn points?',
    component: FirstTaskStep,
  },
];
```

### Onboarding Hook

```typescript
// hooks/useOnboarding.ts
export function useOnboarding(type: 'parent' | 'child') {
  const steps = type === 'parent' ? PARENT_ONBOARDING_STEPS : CHILD_ONBOARDING_STEPS;
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());

  // Load saved progress
  useEffect(() => {
    const saved = localStorage.getItem(`onboarding-${type}`);
    if (saved) {
      const progress = JSON.parse(saved);
      setCurrentStep(progress.currentStep);
      setCompletedSteps(new Set(progress.completedSteps));
    }
  }, [type]);

  // Save progress
  const saveProgress = useCallback(() => {
    localStorage.setItem(
      `onboarding-${type}`,
      JSON.stringify({
        currentStep,
        completedSteps: Array.from(completedSteps),
      })
    );
  }, [type, currentStep, completedSteps]);

  const nextStep = useCallback(() => {
    const step = steps[currentStep];
    setCompletedSteps((prev) => new Set([...prev, step.id]));

    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
      saveProgress();
    }
  }, [currentStep, steps, saveProgress]);

  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [currentStep]);

  const skipStep = useCallback(() => {
    // Mark as skipped but not completed
    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
      saveProgress();
    }
  }, [currentStep, steps.length, saveProgress]);

  const completeOnboarding = useCallback(() => {
    localStorage.removeItem(`onboarding-${type}`);
    // Mark onboarding as completed in user profile
  }, [type]);

  return {
    currentStep,
    step: steps[currentStep],
    progress: (currentStep + 1) / steps.length,
    isFirstStep: currentStep === 0,
    isLastStep: currentStep === steps.length - 1,
    completedSteps,
    nextStep,
    prevStep,
    skipStep,
    completeOnboarding,
  };
}
```

### Feature Highlight Component

```tsx
// components/onboarding/FeatureHighlight.tsx
interface FeatureHighlightProps {
  targetRef: React.RefObject<HTMLElement>;
  title: string;
  description: string;
  position: 'top' | 'bottom' | 'left' | 'right';
  onNext: () => void;
  onSkip?: () => void;
}

export function FeatureHighlight({
  targetRef,
  title,
  description,
  position,
  onNext,
  onSkip,
}: FeatureHighlightProps) {
  const [coords, setCoords] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (targetRef.current) {
      const rect = targetRef.current.getBoundingClientRect();
      setCoords({
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
      });
    }
  }, [targetRef]);

  return (
    <div className="fixed inset-0 z-50">
      {/* Overlay with spotlight */}
      <div className="absolute inset-0 bg-black/50">
        {/* Spotlight cutout */}
        <div
          className="absolute"
          style={{
            left: coords.x - 50,
            top: coords.y - 50,
            width: 100,
            height: 100,
            borderRadius: '50%',
            boxShadow: '0 0 0 9999px rgba(0,0,0,0.5)',
          }}
        />
      </div>

      {/* Tooltip */}
      <Tooltip
        targetCoords={coords}
        position={position}
        title={title}
        description={description}
        onNext={onNext}
        onSkip={onSkip}
      />
    </div>
  );
}
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-FE-AUTH-001 | Upstream | Pending | Parent auth |
| SPEC-FE-AUTH-002 | Upstream | Pending | Child auth |
| SPEC-FE-PARENT-001 | Upstream | Pending | Parent features |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Users skip onboarding | Medium | High | Resume prompts, in-app tips |
| Onboarding too long | High | Medium | Allow skipping, make optional |
| Progress loss | Low | Low | Local storage + server sync |

---

## Acceptance Criteria

### Parent Onboarding
- [ ] Given new parent, when starting, then wizard begins
- [ ] Given step completed, when proceeding, then progress saved
- [ ] Given all required steps done, when finishing, then dashboard shown
- [ ] Given onboarding incomplete, when returning, then resume prompt shows

### Child Onboarding
- [ ] Given new child, when starting, then welcome shows
- [ ] Given code entered, when valid, then profile confirmed
- [ ] Given tour started, when highlighting, then tooltips work
- [ ] Given tour complete, when finished, then first task shown

### Progress Persistence
- [ ] Given progress exists, when returning, then restored correctly
- [ ] Given onboarding complete, when done, then progress cleared
- [ ] Given skip clicked, when non-required, then proceeds

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-AUTH-001 | Upstream | Parent auth flow |
| SPEC-FE-AUTH-002 | Upstream | Child device binding |
| SPEC-FE-PARENT-001 | Downstream | First task/reward creation |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
