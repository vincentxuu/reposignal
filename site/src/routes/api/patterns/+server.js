import { json } from '@sveltejs/kit';
import { loadRuntimeAnalysis } from '$lib/server/data.server.js';

export async function GET({ platform, url }) {
  const analysis = await loadRuntimeAnalysis(platform);
  const category = url.searchParams.get('category');
  let patterns = analysis.pattern_detection?.patterns || [];
  if (category) {
    patterns = patterns.filter((pattern) => pattern.category === category);
  }
  return json({ patterns });
}
