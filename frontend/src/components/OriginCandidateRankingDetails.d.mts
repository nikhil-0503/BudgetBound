import type { ReactElement } from 'react';

export function formatCandidateRating(rating: number | null, reviewCount: number | null, ratingScale?: number | null): string;
export function capDisplayedOriginShortlist<T>(candidates: T[]): T[];

export function OriginCandidateRankingDetails(props: {
  candidate: {
    overall_match_score: number | null;
    category_relevance_score: number | null;
    interest_match_score: number | null;
    comfort_suitability_score: number | null;
    duration_suitability_score: number | null;
    destination_quality_score: number | null;
    explanation: string;
    match_reasons: string[];
    tradeoffs: string[];
    why_visit?: string;
    trip_fit?: string;
    practical_note?: string | null;
  };
  rankingSource: 'ai' | 'fallback' | 'not_applicable';
  expanded: boolean;
}): ReactElement;
