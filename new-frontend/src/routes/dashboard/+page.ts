/**
 * Dashboard page load function.
 *
 * This runs on both server-side and client-side and can be used
 * to preload data before the page component renders.
 *
 * Since the app uses session-based authentication and SSR is disabled,
 * this primarily helps with setting up page metadata and any
 * client-side data prefetching hints.
 *
 * Auth protection is handled at two levels:
 * 1. Server-side: hooks.server.ts checks session cookies on protected routes
 * 2. Client-side: +layout.ts checks session cookie on navigation
 */
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
  return {
    // The dashboard component handles all data loading via the API client.
    // This load function is intentionally minimal to avoid duplicating
    // the auth checks that happen in the component.
    title: 'Dashboard - Counter Analytics',
  };
};
