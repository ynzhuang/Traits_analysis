/**
 * Types for the agreement-review UI.
 *
 * These describe the JSON the Flask backend in `webui/backend/app.py`
 * actually returns — the shapes were read off live responses from
 * `/api/trials/<nct_id>` and `/api/trials/<nct_id>/comparison` against the
 * sample data, and cross-checked against how the components consume them.
 *
 * Fields the UI does not read are typed loosely on purpose: the backend
 * passes analysis JSON through largely untouched, and over-specifying it here
 * would break the build every time the analysis schema gains a field.
 */

/** A single extracted trait, as produced by criteria decomposition. */
export interface Trait {
  trait: string;
  category: string;
  value: string;
  source_text?: string;
  original_trait_phrase?: string;
  original_value_phrase?: string;
}

/** One eligibility criterion and the traits decomposed out of it. */
export interface Criterion {
  type: string;
  original_text: string;
  logic?: string;
  traits: Trait[];
}

/** A trial and its decomposed criteria. */
export interface Trial {
  trial_id: string;
  criteria: Criterion[];
  title?: string;
  nct_number?: string;
  phase?: string;
  status?: string;
  sponsor?: string;
  condition?: string;
}

/**
 * One reviewer's decomposition output, keyed by trial id.
 *
 * The backend returns a file per reviewer whose top level is a map of
 * trial id to that trial's decomposition, hence the indexing in
 * `decompositions[reviewer]?.[trialId]`.
 */
export type ReviewerDecomposition = Record<string, Trial>;

/**
 * Agreement on one trait across reviewers.
 *
 * `trait_signature` is the `trait|category|value` triple the analysis uses to
 * decide whether two reviewers extracted "the same" trait; the comparison
 * table splits it on `|` to render its three parts.
 */
export interface TraitLevelAgreement {
  trait_signature: string;
  fleiss_kappa: number;
  present_instances: number;
  total_possible_instances: number;
  consensus_method: string;
  trait?: string;
  category?: string;
  value?: string;
}

/** Agreement on one criterion across reviewers. */
export interface CriterionLevelAgreement {
  criterion_text?: string;
  fleiss_kappa?: number;
  total_traits?: number;
}

/** Headline numbers shown in the consensus panel. */
export interface OverallAgreement {
  /** Not emitted by the current analysis schema — may be undefined. */
  overall_fleiss_kappa?: number;
  /** Not emitted by the current analysis schema — may be undefined. */
  average_trait_kappa?: number;
  /** Not emitted by the current analysis schema — may be undefined. */
  average_criterion_kappa?: number;
  total_traits: number;
  total_reviewers: number;
  total_criteria?: number;
  agreement_distribution?: AgreementDistribution;
}

/** How traits are spread across the agreement bands. */
export interface AgreementDistribution {
  high_agreement?: number;
  moderate_agreement?: number;
  low_agreement?: number;
  [band: string]: number | undefined;
}

export interface AgreementSummary {
  overall: OverallAgreement;
  /**
   * Optional: the analysis schema currently shipped does not emit per-trait
   * agreement, so consumers must handle its absence. See webui/README.md.
   */
  trait_level?: TraitLevelAgreement[];
  criterion_level?: CriterionLevelAgreement[];
}

/** Provenance for an analysis run. */
export interface AnalysisMetadata {
  analysis_timestamp?: string;
  total_reviewers?: number;
  total_trials?: number;
  total_criteria?: number;
  reviewer_identifiers?: string[];
}

/** Consistency scores reported alongside kappa. */
export interface QualityMetrics {
  trait_extraction_consistency?: number;
  category_assignment_consistency?: number;
  value_specification_consistency?: number;
  granularity_consistency?: number;
}

/** The full agreement analysis document for a trial. */
export interface AgreementAnalysis {
  agreement_summary: AgreementSummary;
  analysis_metadata?: AnalysisMetadata;
  quality_metrics?: QualityMetrics;
  semantic_normalization_log?: unknown[];
  trials?: unknown[];
}

/** The payload behind `/api/trials/<nct_id>/comparison`. */
export interface CriteriaComparison {
  trial: Trial;
  reviewers: string[];
  decompositions: Record<string, ReviewerDecomposition>;
  agreement: AgreementAnalysis;
}
