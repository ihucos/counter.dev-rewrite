import { fail, redirect } from '@sveltejs/kit';
import { api } from '$lib/api.js';

/** @type {import('./$types').Actions} */
export const actions = {
  login: async ({ request, cookies }) => {
    const data = await request.formData();
    const username = data.get('username');
    const password = data.get('password');

    if (!username || !password) {
      return fail(400, { error: 'Username and password are required' });
    }

    try {
      const response = await api.post('/api/auth/login/', {
        username,
        password,
      });
      
      // Session cookie is set by Django
      cookies.set('sessionid', response.sessionid, {
        path: '/',
        httpOnly: true,
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
      });
    } catch (error) {
      return fail(401, { error: error.message || 'Invalid credentials' });
    }

    throw redirect(303, '/dashboard');
  },

  register: async ({ request, cookies }) => {
    const data = await request.formData();
    const username = data.get('username');
    const email = data.get('email');
    const password1 = data.get('password1');
    const password2 = data.get('password2');

    if (!username || !email || !password1 || !password2) {
      return fail(400, { error: 'All fields are required' });
    }

    if (password1 !== password2) {
      return fail(400, { error: 'Passwords do not match' });
    }

    try {
      const response = await api.post('/api/auth/registration/', {
        username,
        email,
        password1,
        password2,
        timezone: 0,
        prefs: {},
        hide_hosts: false,
      });

      // Set session cookie
      cookies.set('sessionid', response.sessionid, {
        path: '/',
        httpOnly: true,
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
      });
    } catch (error) {
      return fail(400, { error: error.message || 'Registration failed' });
    }

    throw redirect(303, '/dashboard');
  },

  logout: async ({ cookies }) => {
    try {
      await api.post('/api/auth/logout/');
    } catch (error) {
      console.error('Logout error:', error);
    }

    cookies.delete('sessionid', { path: '/' });
    throw redirect(303, '/');
  },

  forgot_password: async ({ request }) => {
    const data = await request.formData();
    const email = data.get('email');

    if (!email) {
      return fail(400, { error: 'Email is required' });
    }

    try {
      await api.post('/api/auth/password/reset/', { email });
      return { success: true };
    } catch (error) {
      return fail(400, { error: error.message || 'Password reset failed' });
    }
  },
};--- a/src/routes/+page.svelte
