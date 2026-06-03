import { json } from '@sveltejs/kit';
import { generateWorkflow } from '$lib/server/tools.server.js';

export function GET({ url }) {
  const stack = url.searchParams.get('stack') || 'python';
  return json({ stack, workflow: generateWorkflow(stack) });
}
