"use client";

/**
 * §3.2 UsageChart (Recharts): stacked token bars per day or per user.
 * Palette validated with the dataviz six-check script against the app's
 * light surface: prompt #0d9264, completion #2563eb (CVD ΔE 90).
 */

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Usage } from "@/lib/api/admin";

const PROMPT_COLOR = "#0d9264";
const COMPLETION_COLOR = "#2563eb";
const SURFACE = "#f7f8f6";
const INK_MUTED = "#5c6a63";

export function UsageChart({ usage }: { usage: Usage }) {
  return (
    <div className="usage-chart" role="img" aria-label="Token usage chart">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={usage.rows} barCategoryGap="35%">
          <CartesianGrid vertical={false} stroke="#dde3df" />
          <XAxis
            dataKey="key"
            tick={{ fill: INK_MUTED, fontSize: 12 }}
            axisLine={{ stroke: "#dde3df" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: INK_MUTED, fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={60}
          />
          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
            contentStyle={{
              borderRadius: 8,
              border: "1px solid #dde3df",
              fontSize: 13,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 13 }} />
          <Bar
            dataKey="promptTokens"
            name="Prompt tokens"
            stackId="tokens"
            fill={PROMPT_COLOR}
            stroke={SURFACE}
            strokeWidth={2}
          />
          <Bar
            dataKey="completionTokens"
            name="Completion tokens"
            stackId="tokens"
            fill={COMPLETION_COLOR}
            stroke={SURFACE}
            strokeWidth={2}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
