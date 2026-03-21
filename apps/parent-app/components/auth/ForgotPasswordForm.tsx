// @MX:NOTE: [Forgot password form with email validation and API integration]
// @MX:SPEC: [SPEC-FE-AUTH-001 - Password reset request flow]

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuthStore } from "@/stores/authStore";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { Loading } from "@/components/ui/Loading";
import { forgotPasswordSchema } from "@/lib/validations/auth";
import type { ForgotPasswordData } from "@/types/auth";

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

/**
 * Forgot password form component
 * Allows users to request a password reset link via email
 */
export function ForgotPasswordForm() {
  const router = useRouter();
  const { isLoading } = useAuthStore();
  const [submitted, setSubmitted] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: "",
    },
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setSubmitError(null);
    try {
      // Import authClient dynamically to avoid SSR issues
      const { authClient } = await import("@/lib/api/authClient");
      await authClient.forgotPassword(data);
      setSubmitted(true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to send reset email";
      setSubmitError(message);
      setError("root", { type: "manual", message });
    }
  };

  if (isLoading) {
    return (
      <Card className="p-8 max-w-md mx-auto">
        <Loading />
      </Card>
    );
  }

  if (submitted) {
    return (
      <Card className="p-8 max-w-md mx-auto">
        <div className="text-center">
          <div className="mb-4 text-green-600">
            <svg
              className="mx-auto h-12 w-12"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold mb-4">Check Your Email</h2>
          <p className="text-gray-600 mb-6">
            If an account exists with the email you provided, a password reset link has been sent.
            Please check your inbox and follow the instructions.
          </p>
          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={() => router.push("/login")}
          >
            Back to Login
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-8 max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-2 text-center">Forgot Password</h2>
      <p className="text-gray-600 text-center mb-6 text-sm">
        Enter your email address and we'll send you a link to reset your password.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          type="email"
          label="Email Address"
          placeholder="parent@example.com"
          error={errors.email?.message}
          {...register("email")}
          disabled={isSubmitting}
          autoComplete="email"
          required
        />

        {submitError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{submitError}</p>
          </div>
        )}

        <Button type="submit" className="w-full" loading={isSubmitting}>
          Send Reset Link
        </Button>

        <div className="text-center text-sm text-gray-600">
          Remember your password?{" "}
          <button
            type="button"
            className="text-parent-primary hover:underline font-medium"
            onClick={() => router.push("/login")}
          >
            Sign In
          </button>
        </div>
      </form>
    </Card>
  );
}
