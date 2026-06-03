import { json } from '@sveltejs/kit';
import { loadRuntimeAnalysis } from '$lib/server/data.server.js';
import { copilotRecommendations, findRepo } from '$lib/server/tools.server.js';

export async function GET({ url, platform }) {
  const analysis = await loadRuntimeAnalysis(platform);
  const repoName = url.searchParams.get('repo');
  const repo = findRepo(analysis, repoName);
  const security = (analysis.security_posture?.scores || []).find((item) => item.repo === repoName);
  return json({ repo: repoName, recommendations: copilotRecommendations(repo, security) });
}
