import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/features/auth/AuthContext";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { errorMessage } from "@/lib/api/errorMessage";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(1, "Password is required."),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (values: LoginFormValues) => {
    setFormError(null);
    try {
      await login(values);
      const redirectTo = (location.state as { from?: string } | null)?.from ?? "/";
      navigate(redirectTo, { replace: true });
    } catch (error) {
      setFormError(errorMessage(error, "Could not log in. Check your email and password."));
    }
  };

  return (
    <div className="flex min-h-dvh items-center justify-center px-4">
      <Card className="w-full max-w-sm p-6">
        <h1 className="mb-1 font-heading text-2xl font-bold text-primary">GlobeTrotter</h1>
        <p className="mb-6 text-sm text-ink/60">Log in to plan trips, save places, and join the chat.</p>

        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-xs font-medium text-ink/70">
            Email
            <input
              type="email"
              autoComplete="email"
              {...register("email")}
              className="rounded-lg border border-border bg-canvas px-3 py-2.5 text-sm"
            />
            {errors.email ? <span className="text-coral">{errors.email.message}</span> : null}
          </label>
          <label className="flex flex-col gap-1 text-xs font-medium text-ink/70">
            Password
            <input
              type="password"
              autoComplete="current-password"
              {...register("password")}
              className="rounded-lg border border-border bg-canvas px-3 py-2.5 text-sm"
            />
            {errors.password ? <span className="text-coral">{errors.password.message}</span> : null}
          </label>
          {formError ? <p className="text-xs text-coral">{formError}</p> : null}
          <Button type="submit" disabled={isSubmitting} className="mt-2">
            Log in
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-ink/60">
          New here?{" "}
          <Link to="/register" className="font-semibold text-primary underline underline-offset-2">
            Create an account
          </Link>
        </p>
      </Card>
    </div>
  );
}
