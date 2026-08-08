import Link from "next/link";
import type { PaperSummary } from "@/lib/types";

export function PaperCard({ paper }: { paper: PaperSummary }) {
  const authorLine =
    paper.authors.length === 0
      ? "Authors unknown"
      : paper.authors.length <= 3
        ? paper.authors.join(", ")
        : `${paper.authors.slice(0, 3).join(", ")} +${paper.authors.length - 3} more`;

  return (
    <Link
      href={`/papers/${paper.id}`}
      className="block rounded-lg border border-border bg-paper-raised p-5 transition hover:border-accent hover:shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      <h2 className="font-serif text-lg leading-snug text-ink">{paper.title}</h2>
      <p className="mt-1.5 text-sm text-ink-muted">{authorLine}</p>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        {paper.publication_year && (
          <span className="rounded-full border border-border px-2 py-0.5 text-ink-muted">
            {paper.publication_year}
          </span>
        )}
        <span className="rounded-full border border-border px-2 py-0.5 text-ink-muted">
          {paper.citation_count} {paper.citation_count === 1 ? "citation" : "citations"}
        </span>
        {paper.topics.map((topic) => (
          <span
            key={topic}
            className="rounded-full bg-accent-soft px-2 py-0.5 text-accent"
          >
            {topic}
          </span>
        ))}
      </div>
    </Link>
  );
}