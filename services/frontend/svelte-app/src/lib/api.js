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
  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(API_BASE + path, options);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const msg = errorData.detail || (errorData.non_field_errors && errorData.non_field_errors[0]) || 'HTTP ' + response.status;
    const error = new Error(msg);
    error.status = response.status;
    error.data = errorData;
    throw error;
  }

  const text = await response.text();
  return text ? JSON.parse(text) : null;
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
    var params = '?site=' + encodeURIComponent(site);
    if (startDate) params += '&start_date=' + encodeURIComponent(startDate);
    if (endDate) params += '&end_date=' + encodeURIComponent(endDate);
    return request('GET', '/core/query/' + params);
  },
};

export { api };
