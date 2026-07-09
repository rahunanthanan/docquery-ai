/** §6: zod mirrors of the backend validation rules — UX only, never trusted. */

import { z } from "zod";

export const loginFormSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
});

export const registerFormSchema = z.object({
  fullName: z
    .string()
    .trim()
    .min(1, "Enter your name.")
    .max(100, "Name must be at most 100 characters."),
  email: z.string().email("Enter a valid email address."),
  password: z
    .string()
    .min(10, "Password must be at least 10 characters.")
    .regex(/[A-Za-z]/, "Password must contain at least one letter.")
    .regex(/\d/, "Password must contain at least one number."),
});

export type LoginForm = z.infer<typeof loginFormSchema>;
export type RegisterForm = z.infer<typeof registerFormSchema>;
