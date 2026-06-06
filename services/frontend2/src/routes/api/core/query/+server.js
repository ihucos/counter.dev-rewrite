import { json } from '@sveltejs/kit';
import { api } from '$lib/api.js';

/** @type {import('./$types').RequestHandler} */
export async function GET({ url, cookies }) {
  const timeRange = url.searchParams.get('timeRange') || '24h';
  const domain = url.searchParams.get('domain') || '';

  try {
    const queryUrl = `/api/core/query/?timeRange=${timeRange}${domain ? `&domain=${domain}` : ''}`;
    const data = await api.get(queryUrl);
    return json(data);
  } catch (error) {
    return json({ error: error.message }, { status: 500 });
  }
}
