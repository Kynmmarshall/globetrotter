import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/features/auth/AuthContext";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { errorMessage } from "@/lib/api/errorMessage";

const registerSchema = z.object({
  display_name: z.string().min(1, "Display name is required.").max(80),
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(8, "Password must be at least 8 characters."),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({ resolver: zodResolver(registerSchema) });

  const onSubmit = async (values: RegisterFormValues) => {
    setFormError(null);
    try {
      await registerUser(values);
      navigate("/", { replace: true });
    } catch (error) {
      setFormError(errorMessage(error, "Could not create your account."));
    }
  };

  return (
    <div className="flex min-h-dvh items-center justify-center px-4">
      <Card className="w-full max-w-sm p-6">
        <h1 className="mb-1 font-heading text-2xl font-bold text-primary">Join GlobeTrotter</h1>
        <p className="mb-6 text-sm text-ink/60">Create an account to save places and plan your trips.</p>

        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-xs font-medium text-ink/70">
            Display name
            <input {...register("display_name")} className="rounded-lg border border-border bg-canvas px-3 py-2.5 text-sm" />
            {errors.display_name ? <span className="text-coral">{errors.display_name.message}</span> : null}
          </label>
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
              autoComplete="new-password"
              {...register("password")}
              className="rounded-lg border border-border bg-canvas px-3 py-2.5 text-sm"
            />
            {errors.password ? <span className="text-coral">{errors.password.message}</span> : null}
          </label>
          {formError ? <p className="text-xs text-coral">{formError}</p> : null}
          <Button type="submit" disabled={isSubmitting} className="mt-2">
            Create account
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-ink/60">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-primary underline underline-offset-2">
            Log in
          </Link>
        </p>
      </Card>
    </div>
  );
}
