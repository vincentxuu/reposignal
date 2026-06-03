import { loadAnalysis } from '$lib/server/data.server.js';

export const prerender = true;

export function load() {
  const analysis = loadAnalysis();
  const scoreByRepo = new Map(
    (analysis.security_posture?.scores || []).map((s) => [s.repo, s.score])
  );
  const repos = (analysis.repo_summaries || []).map((r) => ({
    repo: r.repo,
    workflow_count: r.workflow_count,
    maturity_pct: r.maturity_pct,
    security_score: scoreByRepo.get(r.repo) ?? null,
    pattern_count: r.pattern_count,
    has_matrix: r.has_matrix,
    has_permissions: r.has_permissions,
    has_ai_review: r.has_ai_review,
    has_security_scan: r.has_security_scan,
    has_cache: r.has_cache
  }));
  return { repos };
}
