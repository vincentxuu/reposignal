import { loadAnalysis } from '$lib/server/data.server.js';

export const prerender = true;

export function load() {
  const analysis = loadAnalysis();
  return {
    repos: (analysis.repo_summaries || []).map((repo) => repo.repo).sort()
  };
}
