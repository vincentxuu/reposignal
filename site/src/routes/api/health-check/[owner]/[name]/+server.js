import { json } from '@sveltejs/kit';
import { loadRuntimeAnalysis } from '$lib/server/data.server.js';
import { copilotRecommendations, findRepo } from '$lib/server/tools.server.js';

export async function GET({ params, platform }) {
  const analysis = await loadRuntimeAnalysis(platform);
  const repoName = `${params.owner}/${params.name}`;
  const repo = findRepo(analysis, repoName);
  const security = (analysis.security_posture?.scores || []).find((item) => item.repo === repoName);
  if (repo) {
    return json({
      repo: repoName,
      source: 'snapshot',
      maturity_pct: repo.maturity_pct,
      workflow_count: repo.workflow_count,
      security_score: security?.score,
      recommendations: copilotRecommendations(repo, security)
    });
  }
  const live = await liveHealthCheck(params.owner, params.name, platform?.env?.GITHUB_TOKEN);
  return json(live, { status: live.error ? 404 : 200 });
}

async function liveHealthCheck(owner, name, token) {
  const repo = `${owner}/${name}`;
  const headers = { accept: 'application/vnd.github+json', 'user-agent': 'reposignal-health-check' };
  if (token) headers.authorization = `Bearer ${token}`;
  const list = await fetch(`https://api.github.com/repos/${owner}/${name}/contents/.github/workflows`, {
    headers
  });
  if (list.status === 404) {
    return { repo, source: 'live', error: 'no_workflows_found' };
  }
  if (!list.ok) {
    return { repo, source: 'live', error: `github_status_${list.status}` };
  }
  const files = (await list.json()).filter((item) => item.type === 'file' && /\.ya?ml$/.test(item.name));
  const workflows = [];
  for (const file of files.slice(0, 30)) {
    const raw = await fetch(file.download_url);
    const text = raw.ok ? await raw.text() : '';
    workflows.push(analyzeWorkflowText(file.name, text));
  }
  const hasPermissions = workflows.filter((workflow) => workflow.has_permissions).length;
  const securityTools = [...new Set(workflows.flatMap((workflow) => workflow.security_tools))];
  const recommendations = [];
  if (hasPermissions < workflows.length) recommendations.push('Add explicit `permissions:` to every workflow.');
  if (!securityTools.length) recommendations.push('Add CodeQL, Trivy, Semgrep, Gitleaks, Scorecard, or another scanner.');
  if (!workflows.some((workflow) => workflow.has_matrix)) recommendations.push('Add matrix testing for supported platforms or runtime versions.');
  return {
    repo,
    source: 'live',
    workflow_count: workflows.length,
    permissions_coverage_pct: workflows.length ? Math.round(hasPermissions / workflows.length * 100) : 0,
    security_tools: securityTools,
    patterns: {
      matrix: workflows.some((workflow) => workflow.has_matrix),
      ai_review: workflows.some((workflow) => workflow.has_ai_review),
      security_scan: securityTools.length > 0
    },
    recommendations
  };
}

function analyzeWorkflowText(name, text) {
  const actions = [...text.matchAll(/uses:\s*([^\s#]+)/g)].map((match) => match[1].split('@')[0]);
  const securityTools = actions.filter((action) => /trivy|snyk|grype|codeql|semgrep|gitleaks|scorecard|gosec/i.test(action));
  return {
    name,
    has_matrix: /strategy:\s*[\s\S]*matrix:/i.test(text),
    has_permissions: /^permissions:/m.test(text),
    has_ai_review: /claude|copilot|coderabbit|ai[-_ ]?review/i.test(text),
    security_tools: securityTools
  };
}
