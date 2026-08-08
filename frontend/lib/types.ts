export interface PaperSummary {
  id: number;
  title: string;
  publication_year: number | null;
  citation_count: number;
  authors: string[];
  topics: string[];
}

export interface Author {
  id: number;
  name: string;
}

export interface Topic {
  name: string;
  score: number;
}

export interface PaperDetail {
  id: number;
  openalex_id: string;
  title: string;
  abstract: string | null;
  publication_year: number | null;
  doi: string | null;
  citation_count: number;
  authors: Author[];
  topics: Topic[];
}

export interface PaginatedPapers {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: PaperSummary[];
}

export interface SummaryResponse {
  summary: string;
}

export interface SearchFilters {
  q?: string;
  year?: number;
  topic?: string;
  author?: string;
  page?: number;
  page_size?: number;
}