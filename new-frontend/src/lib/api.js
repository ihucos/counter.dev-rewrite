/**
 * API client for the Django REST backend.
 * Uses session-based authentication (CSRF token from cookie).
 *
 * Endpoints:
 *   POST   /api/auth/login/
 *   POST   /api/auth/logout/
 *   GET    /api/auth/user/
 *   PATCH  /api/auth/user/
 *   POST   /api/auth/password/change/
 *   POST   /api/auth/password/reset/
 *   POST   /api/auth/password/reset/confirm/
 *   POST   /api/auth/registration/
 *   POST   /api/auth/registration/verify-email/
 *   POST   /api/auth/registration/resend-email/
 *   GET    /api/core/hosts/
 *   GET    /api/core/hosts/{id}/
 *   POST   /api/core/hosts/
 *   PUT    /api/core/hosts/{id}/
 *   PATCH  /api/core/hosts/{id}/
 *   DELETE /api/core/hosts/{id}/
 *   GET    /api/core/query/
 */

const API_BASE = '/api';

function getCsrfToken() {
  const name = 'csrftoken';
  const value = '; ' + document.cookie;
  const parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

function parseError(errorData, status) {
  if (!errorData || typeof errorData !== 'object') {
    return `Request failed (HTTP ${status})`;
  }
  if (typeof errorData.detail === 'string') return errorData.detail;
  if (Array.isArray(errorData.non_field_errors) && errorData.non_field_errors.length > 0) {
    return errorData.non_field_errors[0];
  }
  const messages = [];
  for (const [field, errors] of Object.entries(errorData)) {
    if (Array.isArray(errors)) {
      const label = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ');
      messages.push(`${label}: ${errors.join(', ')}`);
    } else if (typeof errors === 'string') {
      messages.push(errors);
    }
  }
  return messages.length > 0 ? messages.join('; ') : `Request failed (HTTP ${status})`;
}

async function request(method, path, body) {
  const headers = { 'Content-Type': 'application/json' };
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    headers['X-CSRFToken'] = getCsrfToken();
  }
  const options = { method, headers, credentials: 'include' };
  if (body != null) options.body = JSON.stringify(body);

  let response;
  try {
    response = await fetch(API_BASE + path, options);
  } catch {
    const err = new Error('Network error: unable to reach the server');
    err.status = 0;
    throw err;
  }

  if (!response.ok) {
    let data;
    try { data = await response.json(); } catch { data = {}; }
    const msg = parseError(data, response.status);
    const err = new Error(msg);
    err.status = response.status;
    err.data = data;
    throw err;
  }

  if (response.status === 204) return null;
  const text = await response.text();
  if (!text) return null;
  try { return JSON.parse(text); } catch { return text; }
}

function buildUrl(path, params) {
  if (!params) return path;
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v != null) qs.set(k, v);
  }
  const str = qs.toString();
  return str ? path + '?' + str : path;
}

export const api = {
  // Auth
  login: (username, password) =>
    request('POST', '/auth/login/', { username, password }),

  logout: () =>
    request('POST', '/auth/logout/'),

  register: (data) =>
    request('POST', '/auth/registration/', data),

  verifyEmail: (key) =>
    request('POST', '/auth/registration/verify-email/', { key }),

  resendVerificationEmail: (email) =>
    request('POST', '/auth/registration/resend-email/', { email }),

  getUser: () =>
    request('GET', '/auth/user/'),

  updateUser: (data) =>
    request('PATCH', '/auth/user/', data),

  changePassword: (data) =>
    request('POST', '/auth/password/change/', data),

  requestPasswordReset: (email) =>
    request('POST', '/auth/password/reset/', { email }),

  confirmPasswordReset: (data) =>
    request('POST', '/auth/password/reset/confirm/', data),

  // Hosts
  getHosts: () =>
    request('GET', '/core/hosts/'),

  getHost: (id) =>
    request('GET', `/core/hosts/${id}/`),

  createHost: (data) =>
    request('POST', '/core/hosts/', data),

  updateHost: (id, data) =>
    request('PATCH', `/core/hosts/${id}/`, data),

  deleteHost: (id) =>
    request('DELETE', `/core/hosts/${id}/`),

  // Query
  query: (site, startDate, endDate) =>
    request('GET', buildUrl('/core/query/', {
      site,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    })),
}
