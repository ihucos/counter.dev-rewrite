/**
 * API client for the Django REST backend.
 * Uses session-based authentication (CSRF token from cookie).
 */

export interface ApiError extends Error {
  status: number;
  data?: Record<string, unknown>;
}

export interface UserData {
  pk: number;
  email: string;
  username: string;
  uuid: string;
  timezone: string;
  hide_hosts: boolean;
  prefs: Record<string, unknown>;
}

export interface HostData {
  id: number;
  name: string;
  host: string;
  hide: boolean;
  user: number;
}

export interface QueryResult {
  [category: string]: Record<string, number>;
}

export interface VisitLogEntry {
  timestamp: string;
  date: string;
  time: string;
  country: string;
  referrer: string;
  device: string;
  platform: string;
  site: string;
  extra: string;
}

export interface VisitLogsResponse {
  logs: VisitLogEntry[];
  sites_with_logs: string[];
}

interface AuthResponse { key?: string; user?: UserData; }
interface LoginData { username: string; password: string; }
interface RegisterData { username: string; email?: string; password1: string; password2: string; timezone?: number; }
interface VerifyEmailData { key: string; }
interface ResendEmailData { email: string; }
interface ChangePasswordData { old_password: string; new_password1: string; new_password2: string; }
interface RequestPasswordResetData { email: string; }
interface ConfirmPasswordResetData { uid: string; token: string; new_password1: string; new_password2: string; }
interface UpdateUserData { username?: string; email?: string; timezone?: string; hide_hosts?: boolean; prefs?: Record<string, unknown>; }
interface CreateHostData { name: string; host?: string; }
interface UpdateHostData { name?: string; host?: string; hide?: boolean; }

const API_BASE = '/api';

function getCsrfToken(): string {
  const name = 'csrftoken';
  const value = '; ' + document.cookie;
  const parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop()?.split(';').shift() || '';
  return '';
}

function parseError(errorData: unknown, status: number): string {
  if (!errorData || typeof errorData !== 'object') {
    return `Request failed (HTTP ${status})`;
  }
  const data = errorData as Record<string, unknown>;
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.non_field_errors) && data.non_field_errors.length > 0) {
    return data.non_field_errors[0] as string;
  }
  const messages: string[] = [];
  for (const [field, errors] of Object.entries(data)) {
    if (Array.isArray(errors)) {
      const label = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ');
      messages.push(`${label}: ${errors.join(', ')}`);
    } else if (typeof errors === 'string') {
      messages.push(errors);
    }
  }
  return messages.length > 0 ? messages.join('; ') : `Request failed (HTTP ${status})`;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T | null> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    headers['X-CSRFToken'] = getCsrfToken();
  }
  const options: RequestInit = { method, headers, credentials: 'include' };
  if (body != null) options.body = JSON.stringify(body);

  let response: Response;
  try {
    response = await fetch(API_BASE + path, options);
  } catch {
    const err = new Error('Network error: unable to reach the server') as ApiError;
    err.status = 0;
    throw err;
  }

  if (!response.ok) {
    let data: unknown;
    try { data = await response.json(); } catch { data = {}; }
    const msg = parseError(data, response.status);
    const err = new Error(msg) as ApiError;
    err.status = response.status;
    err.data = data as Record<string, unknown>;
    throw err;
  }

  if (response.status === 204) return null;
  const text = await response.text();
  if (!text) return null;
  try { return JSON.parse(text) as T; } catch { return text as unknown as T; }
}

function buildUrl(path: string, params?: Record<string, string | undefined>): string {
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
  login: (username: string, password: string): Promise<AuthResponse | null> =>
    request<AuthResponse>('POST', '/auth/login/', { username, password } as LoginData),

  logout: (): Promise<null> =>
    request<null>('POST', '/auth/logout/'),

  register: (data: RegisterData): Promise<AuthResponse | null> =>
    request<AuthResponse>('POST', '/auth/registration/', data),

  verifyEmail: (key: string): Promise<unknown | null> =>
    request<unknown>('POST', '/auth/registration/verify-email/', { key } as VerifyEmailData),

  resendVerificationEmail: (email: string): Promise<unknown | null> =>
    request<unknown>('POST', '/auth/registration/resend-email/', { email } as ResendEmailData),

  getUser: (): Promise<UserData | null> =>
    request<UserData>('GET', '/auth/user/'),

  updateUser: (data: UpdateUserData): Promise<UserData | null> =>
    request<UserData>('PATCH', '/auth/user/', data),

  changePassword: (data: ChangePasswordData): Promise<unknown | null> =>
    request<unknown>('POST', '/auth/password/change/', data),

  requestPasswordReset: (email: string): Promise<unknown | null> =>
    request<unknown>('POST', '/auth/password/reset/', { email } as RequestPasswordResetData),

  confirmPasswordReset: (data: ConfirmPasswordResetData): Promise<unknown | null> =>
    request<unknown>('POST', '/auth/password/reset/confirm/', data),

  // Hosts
  getHosts: (): Promise<HostData[] | null> =>
    request<HostData[]>('GET', '/core/hosts/'),

  getHost: (id: number): Promise<HostData | null> =>
    request<HostData>('GET', `/core/hosts/${id}/`),

  createHost: (data: CreateHostData): Promise<HostData | null> =>
    request<HostData>('POST', '/core/hosts/', data),

  updateHost: (id: number, data: UpdateHostData): Promise<HostData | null> =>
    request<HostData>('PATCH', `/core/hosts/${id}/`, data),

  deleteHost: (id: number): Promise<null> =>
    request<null>('DELETE', `/core/hosts/${id}/`),

  // Query
  query: (site: string, startDate?: string, endDate?: string): Promise<QueryResult | null> =>
    request<QueryResult>('GET', buildUrl('/core/query/', {
      site,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    } as Record<string, string | undefined>)),

  // Visit logs (from Redis)
  getVisitLogs: (site?: string, limit?: number): Promise<VisitLogsResponse | null> =>
    request<VisitLogsResponse>('GET', buildUrl('/core/logs/', {
      site: site || undefined,
      limit: limit ? String(limit) : undefined,
    } as Record<string, string | undefined>)),
};

export type {
  LoginData, RegisterData, CreateHostData, UpdateHostData,
  UpdateUserData, ChangePasswordData, RequestPasswordResetData, ConfirmPasswordResetData
};
