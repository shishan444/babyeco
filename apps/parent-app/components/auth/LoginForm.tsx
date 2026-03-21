// @MX:NOTE: [Login form integrated with react-hook-form and Zod validation]
// @MX:SPEC: [SPEC-FE-AUTH-001 - User authentication with real-time validation]

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
import { loginSchema } from "@/lib/validations/auth";
import type { LoginCredentials } from "@/types/auth";

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const router = useRouter();
  const { login, isLoading, error, clearError } = useAuthStore();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    clearError();
    await login(data);
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
      <h2 className="text-2xl font-bold mb-6 text-center">Parent Login</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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

        <Input
          type="password"
          label="Password"
          placeholder="•••••••••"
          error={errors.password?.message}
          {...register("password")}
          disabled={isSubmitting}
          autoComplete="current-password"
          required
        />

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <Button type="submit" className="w-full" loading={isSubmitting}>
          Sign In
        </Button>

        <div className="text-center">
          <button
            type="button"
            className="text-sm text-parent-primary hover:underline"
            onClick={() => router.push("/forgot-password")}
          >
            Forgot Password?
          </button>
        </div>

        <div className="text-center text-sm text-gray-600">
          Don't have an account?{" "}
          <button
            type="button"
            className="text-parent-primary hover:underline"
            onClick={() => router.push("/register")}
          >
            Register
          </button>
        </div>
      </form>
    </Card>
  );
}
