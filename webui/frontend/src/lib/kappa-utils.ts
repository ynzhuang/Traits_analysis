/**
 * Presentation helpers for Fleiss' kappa.
 *
 * Bands follow Landis & Koch (1977), the same interpretation the Python
 * analysis reports against. Keeping the thresholds in one place matters:
 * `ConsensusPanel` groups traits at 0.6 and 0.4, and those cut points have to
 * mean the same thing as the labels shown beside them.
 */

export type KappaInterpretation =
  | "unknown"
  | "poor"
  | "slight"
  | "fair"
  | "moderate"
  | "substantial"
  | "almost-perfect";

export interface KappaScore {
  /** The raw coefficient, clamped to the valid [-1, 1] range. */
  value: number;
  interpretation: KappaInterpretation;
  /** Tailwind classes for the badge that renders this score. */
  color: string;
}

const LABELS: Record<KappaInterpretation, string> = {
  unknown: "No data",
  poor: "Poor",
  slight: "Slight",
  fair: "Fair",
  moderate: "Moderate",
  substantial: "Substantial",
  "almost-perfect": "Almost Perfect",
};

const COLORS: Record<KappaInterpretation, string> = {
  unknown: "border-gray-300 bg-gray-50 text-gray-500",
  poor: "border-red-300 bg-red-50 text-red-700",
  slight: "border-red-200 bg-red-50 text-red-600",
  fair: "border-amber-300 bg-amber-50 text-amber-700",
  moderate: "border-yellow-300 bg-yellow-50 text-yellow-700",
  substantial: "border-green-300 bg-green-50 text-green-700",
  "almost-perfect": "border-emerald-400 bg-emerald-50 text-emerald-700",
};

/**
 * Classify a coefficient into its Landis & Koch band.
 *
 * Kappa below zero means agreement worse than chance, which is a real result
 * rather than an error, so it gets its own band instead of being clamped to
 * "slight".
 */
export function interpretKappa(value: number | null | undefined): KappaInterpretation {
  // A coefficient the analysis did not report is not the same as a
  // coefficient of zero. Rendering a missing value as "0.000 / Poor" would
  // assert an agreement result that was never computed.
  if (value == null || !Number.isFinite(value)) return "unknown";
  if (value < 0) return "poor";
  if (value <= 0.2) return "slight";
  if (value <= 0.4) return "fair";
  if (value <= 0.6) return "moderate";
  if (value <= 0.8) return "substantial";
  return "almost-perfect";
}

/** Build the display object the badges consume. */
export function createKappaScore(value: number | null | undefined): KappaScore {
  if (value == null || !Number.isFinite(value)) {
    return { value: NaN, interpretation: "unknown", color: COLORS.unknown };
  }
  const safe = Math.max(-1, Math.min(1, value));
  const interpretation = interpretKappa(safe);
  return { value: safe, interpretation, color: COLORS[interpretation] };
}

/**
 * Format a coefficient for display.
 *
 * Three decimals, because the difference between 0.665 and 0.667 is the
 * difference between two Landis & Koch bands at the margin. A non-finite
 * input renders as an em dash rather than "NaN".
 */
export function formatKappa(value: number | null | undefined, precision = 3): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return value.toFixed(precision);
}

/** The human-readable label for a band. */
export function getKappaLabel(interpretation: KappaInterpretation): string {
  return LABELS[interpretation] ?? "Unknown";
}
