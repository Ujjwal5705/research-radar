interface FilterValues {
  q: string;
  year: string;
  topic: string;
  author: string;
}

interface SearchFiltersProps {
  values: FilterValues;
  onChange: (values: FilterValues) => void;
}

// Hardcoded to the two topics this corpus was ingested with (see
// backend/ingestion/ingest_openalex.py). If more topics were ever added,
// this would become a values fetched from the API instead.
const TOPIC_OPTIONS = ["machine learning", "robotics"];

export function SearchFilters({ values, onChange }: SearchFiltersProps) {
  return (
    <div className="space-y-3">
      <label htmlFor="search" className="sr-only">
        Search papers
      </label>
      <input
        id="search"
        type="search"
        placeholder="Search by title or abstract..."
        value={values.q}
        onChange={(e) => onChange({ ...values, q: e.target.value })}
        className="w-full rounded-lg border border-border bg-paper-raised px-4 py-3 text-ink placeholder:text-ink-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
      />

      <div className="flex flex-wrap gap-3">
        <select
          aria-label="Filter by topic"
          value={values.topic}
          onChange={(e) => onChange({ ...values, topic: e.target.value })}
          className="rounded-md border border-border bg-paper-raised px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        >
          <option value="">All topics</option>
          {TOPIC_OPTIONS.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>

        <input
          type="number"
          aria-label="Filter by year"
          placeholder="Year"
          value={values.year}
          onChange={(e) => onChange({ ...values, year: e.target.value })}
          className="w-28 rounded-md border border-border bg-paper-raised px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />

        <input
          type="text"
          aria-label="Filter by author"
          placeholder="Author name"
          value={values.author}
          onChange={(e) => onChange({ ...values, author: e.target.value })}
          className="flex-1 min-w-40 rounded-md border border-border bg-paper-raised px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />

        {(values.q || values.year || values.topic || values.author) && (
          <button
            onClick={() => onChange({ q: "", year: "", topic: "", author: "" })}
            className="rounded-md px-3 py-2 text-sm text-accent hover:underline"
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}