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
 *   /api/auth/registration/       - POST  (dj_rest_auth.registration RegisterView)
 *   /api/auth/registration/verify-email/ - POST  (dj_rest_auth.registration VerifyEmailView)
 *   /api/core/hosts/              - GET, POST (DRF ViewSet)
 *   /api/core/hosts/:id/          - GET, PATCH, DELETE (DRF ViewSet)
 *   /api/core/query/?site=X&...   - GET   (custom query view)
 *   /api/core/logs/?site=X&...    - GET   (custom view, visit logs from Redis)
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

function parseErrorData(errorData, status) {
  if (!errorData || typeof errorData !== 'object') {
    return 'Request failed (HTTP ' + status + ')';
  }
  if (typeof errorData.detail === 'string') {
    return errorData.detail;
  }
  if (Array.isArray(errorData.non_field_errors) && errorData.non_field_errors.length > 0) {
    return errorData.non_field_errors[0];
  }
  const messages = [];
  for (const [field, errors] of Object.entries(errorData)) {
    if (Array.isArray(errors)) {
      const displayField = field.replace(/_/g, ' ');
      const label = displayField.charAt(0).toUpperCase() + displayField.slice(1);
      messages.push(label + ': ' + errors.join(', '));
    } else if (typeof errors === 'string') {
      messages.push(errors);
    }
  }
  if (messages.length > 0) {
    return messages.join('; ');
  }
  return 'Request failed (HTTP ' + status + ')';
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
    const msg = parseErrorData(errorData, response.status);
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

function buildUrl(path, params) {
  if (!params) return path;
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value != null) {
      qs.set(key, value);
    }
  }
  const qsStr = qs.toString();
  return qsStr ? path + '?' + qsStr : path;
}

const api = {
  login: (username, password) =>
    request('POST', '/auth/login/', { username, password }),

  logout: () =>
    request('POST', '/auth/logout/'),

  register: (data) =>
    request('POST', '/auth/registration/', data),

  verifyEmail: (data) =>
    request('POST', '/auth/registration/verify-email/', data),

  getUser: () =>
    request('GET', '/auth/user/'),

  updateUser: (data) =>
    request('PATCH', '/auth/user/', data),

  changePassword: (data) =>
    request('POST', '/auth/password/change/', data),

  requestPasswordReset: (data) =>
    request('POST', '/auth/password/reset/', data),

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
    return request('GET', buildUrl('/core/query/', {
      site,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    }));
  },

  getVisitLogs: (site, limit = 30) => {
    return request('GET', buildUrl('/core/logs/', {
      site: site || undefined,
      limit: String(limit),
    }));
  },
};

export { api, TRACKER_URL };
