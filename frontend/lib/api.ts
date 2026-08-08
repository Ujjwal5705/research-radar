import type { PaginatedPapers, PaperDetail, SearchFilters, SummaryResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    // Network-level failure (backend down, CORS, DNS, etc.) - no HTTP
    // response at all, so we can't read a status code or detail message.
    throw new ApiError(0, "Could not reach the server. Is the API running?");
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // response wasn't JSON - fall back to statusText
    }
    throw new ApiError(res.status, detail);
  }

  return res.json() as Promise<T>;
}

function buildQuery(filters: SearchFilters): string {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.year !== undefined) params.set("year", String(filters.year));
  if (filters.topic) params.set("topic", filters.topic);
  if (filters.author) params.set("author", filters.author);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.page_size ?? 20));
  return params.toString();
}

export function listPapers(filters: SearchFilters, signal?: AbortSignal): Promise<PaginatedPapers> {
  return request<PaginatedPapers>(`/papers?${buildQuery(filters)}`, { signal });
}

export function getPaper(id: number | string): Promise<PaperDetail> {
  return request<PaperDetail>(`/papers/${id}`);
}

export function summarizePaper(id: number | string): Promise<SummaryResponse> {
  return request<SummaryResponse>(`/papers/${id}/summarize`, { method: "POST" });
}