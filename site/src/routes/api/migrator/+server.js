import { json } from '@sveltejs/kit';
import { migrateWorkflow } from '$lib/server/tools.server.js';

export function GET({ url }) {
  return json(migrateWorkflow(url.searchParams.get('from') || 'gitlab', url.searchParams.get('to') || 'github'));
}
