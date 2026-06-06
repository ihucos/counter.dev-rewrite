import { fail, redirect } from '@sveltejs/kit';
import { api } from '$lib/api.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals }) {
  if (!locals.user) {
    throw redirect(303, '/');
  }

  try {
    const hosts = await api.get('/api/core/hosts/');
    return { hosts };
  } catch (error) {
    return { hosts: [] };
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  submit_query: async ({ request }) => {
    const data = await request.formData();
    const timeRange = data.get('timeRange') || '24h';
    const domain = data.get('domain') || '';

    try {
      const queryUrl = `/api/core/query/?timeRange=${timeRange}${domain ? `&domain=${domain}` : ''}`;
      const result = await api.get(queryUrl);
      return { success: true, result };
    } catch (error) {
      return fail(400, { error: error.message || 'Query failed' });
    }
  },

  update_account: async ({ request, locals }) => {
    const data = await request.formData();
    const timezone = parseInt(data.get('timezone')) || 0;
    const hideHosts = data.get('hide_hosts') === 'true';
    const prefs = JSON.parse(data.get('prefs') || '{}');

    try {
      await api.patch('/api/auth/user/', {
        timezone,
        prefs,
        hide_hosts: hideHosts,
      });
      return { success: true };
    } catch (error) {
      return fail(400, { error: error.message || 'Update failed' });
    }
  },

  delete_account: async ({ locals }) => {
    try {
      await api.delete('/api/auth/user/');
    } catch (error) {
      return fail(400, { error: error.message || 'Delete failed' });
    }
    throw redirect(303, '/');
  },
};--- a/src/routes/dashboard/+page.svelte
