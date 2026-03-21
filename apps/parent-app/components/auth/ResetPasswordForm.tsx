// @MX:NOTE: [Reset password form with strength indicator and validation]
// @MX:SPEC: [SPEC-FE-AUTH-001 - Password reset completion flow]

"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { Loading } from "@/components/ui/Loading";
import { PasswordStrength } from "@/components/auth/PasswordStrength";
import { resetPasswordSchema } from "@/lib/validations/auth";
import type { ResetPasswordData } from "@/types/auth";

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

/**
 * Reset password form component
 * Allows users to set a new password using a reset token
 */
export function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [isLoading, setIsLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      token,
      password: "",
      confirmPassword: "",
    },
  });

  const password = watch("password");

  const onSubmit = async (data: ResetPasswordFormData) => {
    setSubmitError(null);
    setIsLoading(true);
    try {
      const { authClient } = await import("@/lib/api/authClient");
      await authClient.resetPassword(data);
      setSuccess(true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to reset password";
      setSubmitError(message);
      setError("root", { type: "manual", message });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Card className="p-8 max-w-md mx-auto">
        <Loading />
      </Card>
    );
  }

  if (success) {
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
          <h2 className="text-2xl font-bold mb-4">Password Reset Successful</h2>
          <p className="text-gray-600 mb-6">
            Your password has been successfully reset. You can now login with your new password.
          </p>
          <Button
            type="button"
            className="w-full"
            onClick={() => router.push("/login")}
          >
            Go to Login
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-8 max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-2 text-center">Reset Password</h2>
      <p className="text-gray-600 text-center mb-6 text-sm">
        Enter your new password below.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <input type="hidden" {...register("token")} value={token} />

        <div>
          <Input
            type="password"
            label="New Password"
            placeholder="Enter new password"
            error={errors.password?.message}
            {...register("password")}
            disabled={isSubmitting}
            autoComplete="new-password"
            required
          />
          <div className="mt-2">
            <PasswordStrength password={password} />
          </div>
        </div>

        <Input
          type="password"
          label="Confirm New Password"
          placeholder="Confirm new password"
          error={errors.confirmPassword?.message}
          {...register("confirmPassword")}
          disabled={isSubmitting}
          autoComplete="new-password"
          required
        />

        {submitError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{submitError}</p>
          </div>
        )}

        <Button type="submit" className="w-full" loading={isSubmitting}>
          Reset Password
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
