/**
 * Server-side hooks for the Counter SvelteKit app.
 *
 * These hooks run on every request to the server.
 * Since the app uses session-based auth (cookies), the server can check
 * for authentication by forwarding requests to the Django backend.
 *
 * Protected routes (dashboard, setup) need to verify the user has a valid
 * session cookie. If not, redirect to the login page.
 */

import type { Handle } from '@sveltejs/kit';

/** Route definitions - which paths require authentication */
const PROTECTED_ROUTES = ['/dashboard', '/setup'];

/** Routes that should redirect to dashboard if already authenticated */
const AUTH_ROUTES = ['/', '/register', '/reset-password', '/verify-email'];

/**
 * Check if the user has a valid session by calling the Django /api/auth/user/ endpoint.
 * We use the `fetch` API on the server side with the forwarded cookies.
 */
async function isAuthenticated(request: Request): Promise<boolean> {
  try {
    const apiUrl = new URL(request.url);
    const origin = `${apiUrl.protocol}//${apiUrl.host}`;
    const response = await fetch(`${origin}/api/auth/user/`, {
      method: 'GET',
      headers: {
        'Cookie': request.headers.get('cookie') || '',
        'Content-Type': 'application/json',
      },
    });
    return response.ok;
  } catch {
    return false;
  }
}

export const handle: Handle = async ({ event, resolve }) => {
  const pathname = event.url.pathname;

  // Check if this is a protected route
  const needsAuth = PROTECTED_ROUTES.some(route => pathname.startsWith(route));

  if (needsAuth) {
    const authenticated = await isAuthenticated(event.request);
    if (!authenticated) {
      // Redirect to login page
      return new Response(null, {
        status: 302,
        headers: {
          location: '/',
        },
      });
    }
  }

  // If user is on an auth-only route (login, register) but already logged in,
  // redirect to dashboard. But only for exact matches to avoid loops.
  if (pathname === '/') {
    const authenticated = await isAuthenticated(event.request);
    if (authenticated) {
      return new Response(null, {
        status: 302,
        headers: {
          location: '/dashboard',
        },
      });
    }
  }

  return resolve(event);
};
