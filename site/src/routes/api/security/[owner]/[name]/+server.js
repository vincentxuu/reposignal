import { json } from '@sveltejs/kit';
import { loadRuntimeAnalysis } from '$lib/server/data.server.js';

export async function GET({ params, platform }) {
  const analysis = await loadRuntimeAnalysis(platform);
  const repo = `${params.owner}/${params.name}`;
  const score = (analysis.security_posture?.scores || []).find((item) => item.repo === repo);
  return json(score || { repo, error: 'not_found' }, { status: score ? 200 : 404 });
}
