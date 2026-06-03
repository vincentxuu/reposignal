import { loadAnalysis, loadConfigBatch } from '$lib/server/data.server.js';

export const prerender = true;

export function load() {
  return {
    analysis: loadAnalysis(),
    batch2: loadConfigBatch('batch2'),
    batch3: loadConfigBatch('batch3')
  };
}
