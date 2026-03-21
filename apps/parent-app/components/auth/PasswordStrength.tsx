// @MX:NOTE: [Password strength indicator with visual feedback]
// @MX:SPEC: [SPEC-FE-AUTH-001 - Password strength requirements validation]

"use client";

import { useMemo } from "react";

interface PasswordStrengthProps {
  password: string;
}

interface StrengthLevel {
  label: string;
  color: string;
  width: string;
}

/**
 * Calculate password strength based on multiple criteria
 * Returns strength level from 0-4
 */
function calculateStrength(password: string): number {
  if (!password) return 0;

  let strength = 0;

  // Length check
  if (password.length >= 8) strength++;
  if (password.length >= 12) strength++;

  // Character variety
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
  if (/\d/.test(password)) strength++;
  if (/[^a-zA-Z0-9]/.test(password)) strength++;

  return Math.min(strength, 4);
}

/**
 * Get strength level configuration
 */
function getStrengthLevel(strength: number): StrengthLevel {
  const levels: Record<number, StrengthLevel> = {
    0: { label: "Weak", color: "bg-red-500", width: "25%" },
    1: { label: "Fair", color: "bg-orange-500", width: "50%" },
    2: { label: "Good", color: "bg-yellow-500", width: "75%" },
    3: { label: "Strong", color: "bg-green-500", width: "100%" },
    4: { label: "Very Strong", color: "bg-green-600", width: "100%" },
  };

  return levels[strength as keyof typeof levels] || levels[0];
}

/**
 * Password strength indicator component
 * Provides visual feedback on password security
 */
export function PasswordStrength({ password }: PasswordStrengthProps) {
  const strength = useMemo(() => calculateStrength(password), [password]);
  const level = useMemo(() => getStrengthLevel(strength), [strength]);

  if (!password) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-600">Password strength:</span>
        <span className={`font-medium ${
          strength <= 1 ? "text-red-600" :
          strength === 2 ? "text-yellow-600" :
          "text-green-600"
        }`}>
          {level.label}
        </span>
      </div>

      {/* Strength bar */}
      <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${level.color}`}
          style={{ width: level.width }}
          role="progressbar"
          aria-valuenow={strength}
          aria-valuemin={0}
          aria-valuemax={4}
          aria-label={`Password strength: ${level.label}`}
        />
      </div>

      {/* Requirements checklist */}
      <div className="space-y-1 text-xs text-gray-600">
        <p className="font-medium mb-1">Password requirements:</p>
        <ul className="space-y-1">
          <li className={password.length >= 8 ? "text-green-600" : "text-gray-400"}>
            {password.length >= 8 ? "✓" : "○"} At least 8 characters
          </li>
          <li className={/[A-Za-z]/.test(password) ? "text-green-600" : "text-gray-400"}>
            {/[A-Za-z]/.test(password) ? "✓" : "○"} Contains letters
          </li>
          <li className={/\d/.test(password) ? "text-green-600" : "text-gray-400"}>
            {/\d/.test(password) ? "✓" : "○"} Contains numbers
          </li>
          <li className={/[^a-zA-Z0-9]/.test(password) ? "text-green-600" : "text-gray-400"}>
            {/[^a-zA-Z0-9]/.test(password) ? "✓" : "○"} Special characters (optional)
          </li>
        </ul>
      </div>
    </div>
  );
}
