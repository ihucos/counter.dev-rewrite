/**
 * API client for the counter.dev Django backend.
 * Uses session-based authentication (CSRF token from cookie).
 *
 * API Endpoints (Django URL configuration):
 *   /api/auth/login/              - POST  (dj_rest_auth)
 *   /api/auth/logout/             - POST  (dj_rest_auth)
 *   /api/auth/user/               - GET, PATCH (dj_rest_auth UserDetailsView)
 *   /api/auth/password/change/    - POST  (dj_rest_auth PasswordChangeView)
 *   /api/auth/password/reset/     - POST  (dj_rest_auth PasswordResetView)
 *   /api/auth/password/reset/confirm/ - POST  (dj_rest_auth PasswordResetConfirmView)
 *   /api/auth/registration/       - POST  (dj_rest_auth.registration)
 *   /api/auth/registration/verify-email/ - POST  (dj_rest_auth.registration)
 *   /api/core/hosts/              - GET, POST (DRF ViewSet)
 *   /api/core/hosts/:id/          - GET, PATCH, DELETE (DRF ViewSet)
 *   /api/core/query/?site=X&...   - GET   (custom view)
 */

const API_BASE = '/api';

const TRACKER_URL = import.meta.env.VITE_TRACKER_URL || 'https://cdn.counter.dev/script.js';

function getCsrfToken() {
  const name = 'csrftoken';
  const value = '; ' + document.cookie;
  const parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

async function request(method, path, body) {
  const headers = { 'Content-Type': 'application/json' };

  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    headers['X-CSRFToken'] = getCsrfToken();
  }

  const options = { method, headers, credentials: 'include' };
  if (body != null) {
    options.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(API_BASE + path, options);
  } catch (fetchError) {
    const error = new Error('Network error: unable to reach the server');
    error.status = 0;
    error.data = {};
    throw error;
  }

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = {};
    }
    const msg = errorData.detail
      || (errorData.non_field_errors && errorData.non_field_errors[0])
      || (typeof errorData === 'string' ? errorData : null)
      || errorData.name
      || 'Request failed (HTTP ' + response.status + ')';
    const error = new Error(msg);
    error.status = response.status;
    error.data = errorData;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

const api = {
  login: (username, password) =>
    request('POST', '/auth/login/', { username, password }),

  logout: () =>
    request('POST', '/auth/logout/'),

  register: (data) =>
    request('POST', '/auth/registration/', data),

  getUser: () =>
    request('GET', '/auth/user/'),

  updateUser: (data) =>
    request('PATCH', '/auth/user/', data),

  changePassword: (data) =>
    request('POST', '/auth/password/change/', data),

  /** Request a password reset email */
  requestPasswordReset: (data) =>
    request('POST', '/auth/password/reset/', data),

  /** Confirm a password reset with token */
  confirmPasswordReset: (data) =>
    request('POST', '/auth/password/reset/confirm/', data),

  getHosts: () =>
    request('GET', '/core/hosts/'),

  getHost: (id) =>
    request('GET', '/core/hosts/' + id + '/'),

  createHost: (name) =>
    request('POST', '/core/hosts/', { name }),

  updateHost: (id, data) =>
    request('PATCH', '/core/hosts/' + id + '/', data),

  deleteHost: (id) =>
    request('DELETE', '/core/hosts/' + id + '/'),

  query: (site, startDate, endDate) => {
    const params = new URLSearchParams();
    params.set('site', site);
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    const qs = params.toString();
    return request('GET', '/core/query/' + (qs ? '?' + qs : ''));
  },
};

export { api, TRACKER_URL };
