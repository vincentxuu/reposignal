import { json } from '@sveltejs/kit';
import { loadRuntimeAnalysis } from '$lib/server/data.server.js';
import { flakySignals } from '$lib/server/tools.server.js';

export async function GET({ platform }) {
  return json(flakySignals(await loadRuntimeAnalysis(platform)));
}
