const upcoming = [
  { area: "Documents", detail: "Upload PDFs and text files for indexing" },
  { area: "Q&A", detail: "Ask questions, get answers with citations" },
  { area: "Review", detail: "Approve, flag or reject AI answers" },
  { area: "Audit", detail: "Trace every action in an append-only log" },
];

export default function Home() {
  return (
    <main
      style={{
        maxWidth: 640,
        margin: "0 auto",
        padding: "6rem 1.5rem",
      }}
    >
      <p
        style={{
          color: "var(--accent)",
          fontSize: 13,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          margin: 0,
        }}
      >
        Scaffold running — Task 1
      </p>
      <h1 style={{ fontSize: 40, lineHeight: 1.1, margin: "0.5rem 0 1rem" }}>
        DocQuery AI
      </h1>
      <p style={{ color: "var(--muted)", fontSize: 17, marginBottom: "2.5rem" }}>
        A RAG document Q&amp;A assistant with human-in-the-loop review and a
        full audit trail. The stack is wired; features arrive task by task.
      </p>
      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {upcoming.map((item) => (
          <li
            key={item.area}
            style={{
              display: "flex",
              gap: "1rem",
              padding: "0.85rem 0",
              borderTop: "1px solid var(--line)",
            }}
          >
            <span style={{ fontWeight: 600, minWidth: 110 }}>{item.area}</span>
            <span style={{ color: "var(--muted)" }}>{item.detail}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
