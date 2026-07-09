import { EmptyState } from "@/components/EmptyState";

export function ComingSoon({ area, task }: { area: string; task: number }) {
  return (
    <EmptyState
      title={`${area} is on the way`}
      detail={`This page ships with Task ${task} of the roadmap.`}
    />
  );
}
