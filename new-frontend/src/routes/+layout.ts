/**
 * Layout configuration for the Counter app.
 *
 * SSR is disabled because the app uses session-based authentication
 * with Django, and we rely on client-side routing for the SPA-like experience.
 *
 * Auth protection is handled at two levels:
 * 1. Server-side: hooks.server.ts checks session cookies on protected routes
 * 2. Client-side: individual pages check auth state on mount as a fallback
 */
export const ssr = false;

/**
 * Client-side navigation guard.
 * This runs on every client-side navigation to check if the user has a valid session.
 * If not, they're redirected to the login page.
 *
 * Protected routes are defined here for cases where the server-side hook
 * might not fire (e.g., direct client-side navigation without a full page load).
 */
import { goto } from '$app/navigation';
import { browser } from '$app/environment';

/** Routes that require authentication */
const protectedRoutes = ['/dashboard', '/setup'];

/**
 * Check if the current path is protected and redirect if not authenticated.
 * This runs on the client side after navigation.
 */
export async function load({ url }: { url: URL }) {
  if (!browser) return {};

  const pathname = url.pathname;

  // Only check protected routes
  const isProtected = protectedRoutes.some(route => pathname.startsWith(route));
  if (!isProtected) return {};

  try {
    // Quick check: does the session cookie exist?
    const hasSessionCookie = document.cookie.includes('sessionid');
    if (!hasSessionCookie) {
      goto('/');
      return {};
    }
  } catch {
    goto('/');
  }

  return {};
}
