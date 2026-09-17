/**
 * Client for the Flask backend in `webui/backend/app.py`.
 *
 * One method per route that backend exposes. The base URL is configurable
 * because the backend and this app run on different ports in development
 * (Flask on 5000, Next on 3000); set NEXT_PUBLIC_API_BASE_URL to point at a
 * deployed backend.
 */

import type {
  AgreementAnalysis,
  CriteriaComparison,
  ReviewerDecomposition,
  Trial,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5000";

/** Raised for any non-2xx response, carrying the status for the caller. */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string, options?: { cause?: unknown }) {
    super(message, options);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
  } catch (cause) {
    // A transport failure is the common case in development — the backend
    // simply is not running. Say so, rather than surfacing "Failed to fetch".
    throw new ApiError(
      0,
      `Could not reach the API at ${API_BASE_URL}. Is the Flask backend running?`,
      { cause },
    );
  }

  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      detail = typeof body?.error === "string" ? `: ${body.error}` : "";
    } catch {
      // Error bodies are not guaranteed to be JSON; the status alone will do.
    }
    throw new ApiError(
      response.status,
      `Request to ${path} failed with ${response.status}${detail}`,
    );
  }

  return (await response.json()) as T;
}

export const apiClient = {
  /** GET /api/health */
  getHealth: () => request<{ status: string }>("/api/health"),

  /** GET /api/reviewers — the reviewer identifiers available in the corpus. */
  getReviewers: () => request<string[]>("/api/reviewers"),

  /** GET /api/trials — the trial ids available. */
  getTrials: () => request<string[]>("/api/trials"),

  /** GET /api/trials/:nctId */
  getTrial: (nctId: string) =>
    request<Trial>(`/api/trials/${encodeURIComponent(nctId)}`),

  /** GET /api/trials/:nctId/decompositions/:reviewer */
  getReviewerDecomposition: (nctId: string, reviewer: string) =>
    request<ReviewerDecomposition>(
      `/api/trials/${encodeURIComponent(nctId)}/decompositions/${encodeURIComponent(reviewer)}`,
    ),

  /** GET /api/trials/:nctId/agreement */
  getAgreementAnalysis: (nctId: string) =>
    request<AgreementAnalysis>(
      `/api/trials/${encodeURIComponent(nctId)}/agreement`,
    ),

  /**
   * GET /api/trials/:nctId/comparison
   *
   * The one the main page uses: trial, reviewers, every reviewer's
   * decomposition, and the agreement analysis, in a single round trip.
   */
  getCriteriaComparison: (nctId: string) =>
    request<CriteriaComparison>(
      `/api/trials/${encodeURIComponent(nctId)}/comparison`,
    ),
};
