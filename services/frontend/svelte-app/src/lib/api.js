/**
 * API client for the counter.dev Django backend.
 * Uses session-based authentication (CSRF token from cookie).
 */

const API_BASE = '/api';

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
      || 'Request failed (HTTP ' + response.status + ')';
    const error = new Error(msg);
    error.status = response.status;
    error.data = errorData;
    throw error;
  }

  // Handle 204 No Content
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

  getHosts: () =>
    request('GET', '/core/hosts/'),

  updateHost: (id, data) =>
    request('PATCH', '/core/hosts/' + id + '/', data),

  query: (site, startDate, endDate) => {
    const params = new URLSearchParams();
    params.set('site', site);
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    const qs = params.toString();
    return request('GET', '/core/query/' + (qs ? '?' + qs : ''));
  },
};

export { api };
