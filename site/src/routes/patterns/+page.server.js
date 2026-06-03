import { loadAnalysis } from '$lib/server/data.server.js';

export const prerender = true;

export function load() {
  return { analysis: loadAnalysis() };
}
