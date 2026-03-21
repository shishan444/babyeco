// @MX:NOTE: [Registration form integrated with react-hook-form and Zod validation]
// @MX:SPEC: [SPEC-FE-AUTH-001 - User registration with real-time validation and password strength]

"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuthStore } from "@/stores/authStore";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { Loading } from "@/components/ui/Loading";
import { PasswordStrength } from "@/components/auth/PasswordStrength";
import { registerSchema } from "@/lib/validations/auth";
import type { RegisterData } from "@/types/auth";

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const router = useRouter();
  const { register: registerUser, isLoading, error, clearError } = useAuthStore();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      familyName: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  const password = watch("password");

  const onSubmit = async (data: RegisterData) => {
    clearError();
    await registerUser(data);
    if (useAuthStore.getState().isAuthenticated) {
      router.push("/dashboard");
    }
  };

  if (isLoading) {
    return (
      <Card className="p-8 max-w-md mx-auto">
        <Loading />
      </Card>
    );
  }

  return (
    <Card className="p-8 max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-6 text-center">Create Family Account</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          type="text"
          label="Family Name"
          placeholder="Smith Family"
          error={errors.familyName?.message}
          {...register("familyName")}
          disabled={isSubmitting}
          autoComplete="organization"
          required
        />

        <Input
          type="email"
          label="Email"
          placeholder="parent@example.com"
          error={errors.email?.message}
          {...register("email")}
          disabled={isSubmitting}
          autoComplete="email"
          required
        />

        <div>
          <Input
            type="password"
            label="Password"
            placeholder="•••••••••"
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
          label="Confirm Password"
          placeholder="•••••••••"
          error={errors.confirmPassword?.message}
          {...register("confirmPassword")}
          disabled={isSubmitting}
          autoComplete="new-password"
          required
        />

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <Button type="submit" className="w-full" loading={isSubmitting}>
          Create Account
        </Button>

        <div className="text-center text-sm text-gray-600">
          Already have an account?{" "}
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
