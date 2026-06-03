import { json } from '@sveltejs/kit';
import { aiReviewerKit } from '$lib/server/tools.server.js';

export function GET() {
  return json({ workflow: aiReviewerKit() });
}
