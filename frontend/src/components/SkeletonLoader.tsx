interface Props {
  lines?: number;
}

export function SkeletonLoader({ lines = 3 }: Props) {
  return (
    <div className="skeleton" aria-busy="true" aria-label="Loading">
      {Array.from({ length: lines }, (_, i) => (
        <div key={i} className="skeleton-line" />
      ))}
    </div>
  );
}
