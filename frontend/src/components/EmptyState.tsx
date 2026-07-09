interface Props {
  title: string;
  detail?: string;
  action?: React.ReactNode;
}

export function EmptyState({ title, detail, action }: Props) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      {detail ? <p className="muted">{detail}</p> : null}
      {action}
    </div>
  );
}
