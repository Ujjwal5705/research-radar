interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-4 py-6">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="rounded-md border border-border px-3 py-1.5 text-sm text-ink transition hover:border-accent disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-border"
      >
        Previous
      </button>
      <span className="text-sm text-ink-muted">
        Page {page} of {totalPages}
      </span>
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="rounded-md border border-border px-3 py-1.5 text-sm text-ink transition hover:border-accent disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-border"
      >
        Next
      </button>
    </div>
  );
}