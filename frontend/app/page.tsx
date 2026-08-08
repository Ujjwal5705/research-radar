"use client";

import { useEffect, useState } from "react";
import { listPapers, ApiError } from "@/lib/api";
import type { PaginatedPapers } from "@/lib/types";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { SearchFilters } from "@/components/SearchFilters";
import { PaperCard } from "@/components/PaperCard";
import { Pagination } from "@/components/Pagination";

interface RawFilters {
  q: string;
  year: string;
  topic: string;
  author: string;
}

const EMPTY_FILTERS: RawFilters = { q: "", year: "", topic: "", author: "" };

export default function SearchPage() {
  const [rawFilters, setRawFilters] = useState<RawFilters>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PaginatedPapers | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  const debouncedFilters = useDebouncedValue(rawFilters, 400);

  // Any real filter change should reset back to page 1 - otherwise you can
  // get stuck on "page 5" of a search that now only has 2 pages of results.
  useEffect(() => {
    setPage(1);
  }, [debouncedFilters.q, debouncedFilters.year, debouncedFilters.topic, debouncedFilters.author]);

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);

    listPapers(
      {
        q: debouncedFilters.q || undefined,
        year: debouncedFilters.year ? Number(debouncedFilters.year) : undefined,
        topic: debouncedFilters.topic || undefined,
        author: debouncedFilters.author || undefined,
        page,
        page_size: 20,
      },
      controller.signal
    )
      .then((result) => setData(result))
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      })
      .finally(() => setIsLoading(false));

    return () => controller.abort();
  }, [debouncedFilters, page, retryKey]);

  return (
    <main className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
      <header className="mb-8">
        <h1 className="font-serif text-3xl text-ink">Research Radar</h1>
        <p className="mt-1 text-ink-muted">
          Search recent machine learning and robotics papers.
        </p>
      </header>

      <SearchFilters values={rawFilters} onChange={setRawFilters} />

      <div className="mt-8">
        {error && (
          <div className="rounded-lg border border-error-soft bg-error-soft px-4 py-3 text-sm text-error">
            <p className="font-medium">Couldn&apos;t load results</p>
            <p className="mt-0.5">{error}</p>
            <button
              onClick={() => setRetryKey((k) => k + 1)}
              className="mt-2 rounded-md border border-error px-3 py-1 text-xs font-medium hover:bg-error hover:text-white"
            >
              Try again
            </button>
          </div>
        )}

        {!error && isLoading && !data && (
          <ul className="space-y-3" aria-busy="true" aria-label="Loading results">
            {Array.from({ length: 5 }).map((_, i) => (
              <li
                key={i}
                className="h-24 animate-pulse rounded-lg border border-border bg-paper-raised"
              />
            ))}
          </ul>
        )}

        {!error && data && data.results.length === 0 && (
          <div className="rounded-lg border border-dashed border-border px-4 py-12 text-center">
            <p className="text-ink">No papers match your search.</p>
            <p className="mt-1 text-sm text-ink-muted">
              Try a different keyword or clear your filters.
            </p>
          </div>
        )}

        {!error && data && data.results.length > 0 && (
          <div className={isLoading ? "opacity-60 transition-opacity" : "transition-opacity"}>
            <p className="mb-3 text-sm text-ink-muted">
              {data.total} paper{data.total === 1 ? "" : "s"} found
            </p>
            <ul className="space-y-3">
              {data.results.map((paper) => (
                <li key={paper.id}>
                  <PaperCard paper={paper} />
                </li>
              ))}
            </ul>
            <Pagination page={data.page} totalPages={data.total_pages} onPageChange={setPage} />
          </div>
        )}
      </div>
    </main>
  );
}