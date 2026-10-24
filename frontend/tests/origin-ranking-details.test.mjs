import assert from 'node:assert/strict';
import test from 'node:test';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

import { OriginCandidateRankingDetails, formatCandidateRating, capDisplayedOriginShortlist } from '../src/components/OriginCandidateRankingDetails.mjs';

const candidate = {
  overall_match_score: 87,
  category_relevance_score: 91,
  interest_match_score: 88,
  comfort_suitability_score: 74,
  duration_suitability_score: 82,
  destination_quality_score: 90,
  explanation: 'AI explanation.',
  match_reasons: ['Matches your wildlife interest in verified places.'],
  tradeoffs: ['The estimate leaves less budget remaining.'],
  why_visit: 'Verified listings include Ooty Lake.',
  trip_fit: 'This matches the Nature category for your trip.',
  practical_note: 'Check current routes before planning a day trip.',
};

test('AI results render score dimensions, reasons, tradeoffs, and score caveat', () => {
  const html = renderToStaticMarkup(React.createElement(OriginCandidateRankingDetails, {
    candidate, rankingSource: 'ai', expanded: true,
  }));
  assert.match(html, /AI Match Score: 87\/100/);
  assert.match(html, /Category: 91\/100/);
  assert.match(html, /Matches your wildlife interest/);
  assert.match(html, /Tradeoffs:/);
  assert.match(html, /not objective measurements or probabilities/);
});

test('fallback results render an explanation and no invented AI score', () => {
  const fallbackCandidate = {
    ...candidate,
    overall_match_score: null,
    match_reasons: [],
    tradeoffs: [],
    explanation: 'Estimated total remains within the budget.',
  };
  const html = renderToStaticMarkup(React.createElement(OriginCandidateRankingDetails, {
    candidate: fallbackCandidate, rankingSource: 'fallback', expanded: true,
  }));
  assert.match(html, /Why visit:/);
  assert.match(html, /Verified listings include Ooty Lake/);
  assert.doesNotMatch(html, /AI Match Score/);
  assert.doesNotMatch(html, /Category:/);
});

test('destination cards render grounded travel guidance and only supplied Google review counts', () => {
  const html = renderToStaticMarkup(React.createElement(OriginCandidateRankingDetails, {
    candidate, rankingSource: 'ai', expanded: false,
  }));
  assert.match(html, /Why visit:/);
  assert.match(html, /Verified listings include Ooty Lake/);
  assert.match(html, /Why it fits this trip:/);
  assert.match(html, /This matches the Nature category/);
  assert.match(html, /Practical consideration:/);
  assert.match(html, /Check current routes/);
  assert.equal(formatCandidateRating(4.5, 2341), '4.5/5 · 2,341 reviews');
  assert.equal(formatCandidateRating(null, 2341), 'Rating unavailable');
});

test('destination cards render at most the backend shortlist cap', () => {
  const candidates = Array.from({ length: 14 }, (_, index) => ({ destination_id: String(index) }));
  assert.equal(capDisplayedOriginShortlist(candidates).length, 8);
  assert.deepEqual(capDisplayedOriginShortlist(candidates.slice(0, 4)), candidates.slice(0, 4));
});
