import { loadAnalysis, loadRepoSources } from '$lib/server/data.server.js';

export const prerender = true;

export function entries() {
  return (loadAnalysis().repo_summaries || []).map((repo) => {
    const [owner, name] = repo.repo.split('/');
    return { owner, name };
  });
}

export function load({ params }) {
  const repoName = `${params.owner}/${params.name}`;
  const analysis = loadAnalysis();
  const repo = (analysis.repo_summaries || []).find((item) => item.repo === repoName);
  const security = (analysis.security_posture?.scores || []).find((item) => item.repo === repoName);
  const sources = repo ? loadRepoSources(params.owner, params.name) : {};
  return { repo, security, sources };
}
