import { loadAnalysis } from '$lib/server/data.server.js';

export const prerender = true;

export function entries() {
  return (loadAnalysis().pattern_detection?.patterns || []).map((pattern) => ({ slug: pattern.slug }));
}

export function load({ params }) {
  const analysis = loadAnalysis();
  const pattern = (analysis.pattern_detection?.patterns || []).find((item) => item.slug === params.slug);
  return { pattern };
}
