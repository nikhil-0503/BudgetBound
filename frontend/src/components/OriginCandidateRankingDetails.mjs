import React from 'react';

const h = React.createElement;

export function formatCandidateRating(rating, reviewCount, ratingScale = 5) {
  if (rating == null) return 'Rating unavailable';
  return `${rating}/${ratingScale}${reviewCount == null ? '' : ` · ${Number(reviewCount).toLocaleString()} ratings`}`;
}

export function capDisplayedOriginShortlist(candidates) {
  return Array.isArray(candidates) ? candidates.slice(0, 8) : [];
}

export function OriginCandidateRankingDetails({ candidate, rankingSource, expanded }) {
  const hasAiScore = rankingSource === 'ai' && candidate.overall_match_score != null;
  const dimensions = [
    ['Category', candidate.category_relevance_score],
    ['Interests', candidate.interest_match_score],
    ['Comfort', candidate.comfort_suitability_score],
    ['Duration', candidate.duration_suitability_score],
    ['Quality', candidate.destination_quality_score],
  ];

  return h(React.Fragment, null,
    h('section', { className: 'space-y-1 text-xs text-paper-600 dark:text-paper-300' },
      candidate.why_visit && h('p', null, h('strong', null, 'Why visit: '), candidate.why_visit),
      candidate.trip_fit && h('p', null, h('strong', null, 'Why it fits this trip: '), candidate.trip_fit),
      candidate.practical_note && h('p', null, h('strong', null, 'Practical consideration: '), candidate.practical_note)),
    hasAiScore && h('div', { className: 'rounded-lg border px-2.5 py-1 text-[10px] font-bold uppercase' },
      `AI Match Score: ${candidate.overall_match_score}/100`),
    expanded && h('div', { className: 'space-y-2 text-xs text-paper-600 dark:text-paper-300' },
      !candidate.match_reasons?.length && !candidate.why_visit && h('p', null, candidate.explanation),
      hasAiScore && h('div', { className: 'flex flex-wrap gap-2' }, dimensions.map(([label, score]) =>
        h('span', { key: label, className: 'rounded-full bg-paper-100 px-2 py-1 text-[10px] dark:bg-paper-900' }, `${label}: ${score}/100`))),
      candidate.match_reasons?.length > 0 && h('ul', { className: 'list-disc pl-4' }, candidate.match_reasons.map((reason, index) =>
        h('li', { key: `${index}-${reason}` }, reason))),
      candidate.tradeoffs?.length > 0 && h('p', null,
        h('strong', null, 'Tradeoffs: '), candidate.tradeoffs.join(' · ')),
      hasAiScore && h('p', { className: 'text-[10px] text-paper-400' },
        'AI match scores are model judgments, not objective measurements or probabilities. Cost feasibility is checked separately.'),
    ),
  );
}
