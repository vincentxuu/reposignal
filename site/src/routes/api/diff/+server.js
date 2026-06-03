import { json } from '@sveltejs/kit';
import { loadRuntimeAnalysis } from '$lib/server/data.server.js';
import { diffRepos, findRepo } from '$lib/server/tools.server.js';

export async function GET({ url, platform }) {
  const analysis = await loadRuntimeAnalysis(platform);
  const left = findRepo(analysis, url.searchParams.get('left'));
  const right = findRepo(analysis, url.searchParams.get('right'));
  const diff = diffRepos(left, right);
  return json(diff || { error: 'repo_not_found' }, { status: diff ? 200 : 404 });
}
