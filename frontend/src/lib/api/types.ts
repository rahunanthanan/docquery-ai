import { z } from "zod";

export const userSchema = z.object({
  id: z.string(),
  email: z.string(),
  fullName: z.string(),
  role: z.enum(["user", "reviewer", "admin"]),
  isActive: z.boolean(),
});

export type ApiUser = z.infer<typeof userSchema>;
export type Role = ApiUser["role"];

export const tokenResponseSchema = z.object({
  accessToken: z.string(),
  tokenType: z.literal("bearer"),
  expiresIn: z.number(),
  user: userSchema,
});

export type TokenResponse = z.infer<typeof tokenResponseSchema>;
