<script lang="ts">
  import { goto } from '$app/navigation';
  import { api } from '$lib/api.js';

  let username = $state('');
  let email = $state('');
  let password1 = $state('');
  let password2 = $state('');
  let error = $state('');
  let fieldErrors = $state<Record<string, string>>({});
  let loading = $state(false);
  let done = $state(false);

  function flash(msg: string, type: string = 'info'): void {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message: msg, type } }));
  }

  function utcOffset(): number {
    return Math.round((-1 * new Date().getTimezoneOffset()) / 60);
  }

  function validateForm(): Record<string, string> {
    const errs: Record<string, string> = {};

    if (!username.trim()) {
      errs.username = 'Username is required';
    } else if (username.trim().length < 2) {
      errs.username = 'Username must be at least 2 characters';
    } else if (!/^[a-zA-Z0-9_]+$/.test(username.trim())) {
      errs.username = 'Username can only contain letters, numbers, and underscores';
    }

    if (email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      errs.email = 'Please enter a valid email address';
    }

    if (!password1) {
      errs.password1 = 'Password is required';
    } else if (password1.length < 6) {
      errs.password1 = 'Password must be at least 6 characters';
    }

    if (password1 !== password2) {
      errs.password2 = 'Passwords do not match';
    }

    return errs;
  }

  function clearFieldError(field: string): void {
    if (fieldErrors[field]) {
      const updated = { ...fieldErrors };
      delete updated[field];
      fieldErrors = updated;
    }
  }

  async function handleRegister(): Promise<void> {
    error = '';
    fieldErrors = {};

    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length > 0) {
      fieldErrors = validationErrors;
      return;
    }

    loading = true;
    try {
      const result = await api.register({
        username: username.trim(),
        email: email.trim() || undefined,
        password1,
        password2,
        timezone: utcOffset(),
      });

      done = true;

      if (result && result.user) {
        flash('Account created! Welcome to Counter.', 'success');
        setTimeout(() => goto('/setup'), 1000);
      } else {
        flash('Account created! Please check your email to verify.', 'success');
        setTimeout(() => goto('/setup'), 1200);
      }
    } catch (e) {
      const apiErr = e as { status?: number; message?: string; data?: Record<string, unknown> };
      error = apiErr.message || 'Registration failed.';

      // Map per-field errors from the API response (e.g. username taken, invalid email)
      if (apiErr.data && typeof apiErr.data === 'object') {
        const fieldMap: Record<string, string> = {};
        for (const [field, errs] of Object.entries(apiErr.data)) {
          if (Array.isArray(errs)) {
            fieldMap[field] = errs.join(', ');
          }
        }
        if (Object.keys(fieldMap).length > 0) {
          fieldErrors = fieldMap;
        }
      }
    } finally {
      loading = false;
    }
  }
</script>

<div class="page">
  <div class="card">
    <div class="logo"></div>
    <h1>{done ? 'Account Created!' : 'Create Account'}</h1>

    {#if done}
      <div class="success">
        <p>Your account has been created successfully.</p>
        {#if email}
          <p>We sent a verification link to <strong>{email}</strong>. Please check your inbox and click the link to activate your account.</p>
        {:else}
          <p>Since you didn't provide an email, your account is ready to use. You can add an email later in settings for account recovery.</p>
        {/if}
        <p class="redirect-hint">Redirecting to setup...</p>
      </div>
    {:else}
      <form onsubmit={(e: Event) => { e.preventDefault(); handleRegister(); }}>
        {#if error && Object.keys(fieldErrors).length === 0}
          <div class="error">{error}</div>
        {/if}

        <label>
          Username *
          <input
            type="text"
            bind:value={username}
            placeholder="Choose a username"
            required
            disabled={loading}
            class:input-error={!!fieldErrors.username}
            oninput={() => clearFieldError('username')}
            autocomplete="username"
          />
          {#if fieldErrors.username}
            <span class="field-error">{fieldErrors.username}</span>
          {/if}
        </label>

        <label>
          Email
          <input
            type="email"
            bind:value={email}
            placeholder="Your email (optional)"
            disabled={loading}
            class:input-error={!!fieldErrors.email}
            oninput={() => clearFieldError('email')}
            autocomplete="email"
          />
          {#if fieldErrors.email}
            <span class="field-error">{fieldErrors.email}</span>
          {:else}
            <span class="field-hint">Required for password reset and account notifications</span>
          {/if}
        </label>

        <label>
          Password *
          <input
            type="password"
            bind:value={password1}
            placeholder="Choose a password (min. 6 characters)"
            required
            disabled={loading}
            class:input-error={!!fieldErrors.password1}
            oninput={() => clearFieldError('password1')}
            autocomplete="new-password"
          />
          {#if fieldErrors.password1}
            <span class="field-error">{fieldErrors.password1}</span>
          {/if}
        </label>

        <label>
          Confirm Password *
          <input
            type="password"
            bind:value={password2}
            placeholder="Repeat password"
            required
            disabled={loading}
            class:input-error={!!fieldErrors.password2}
            oninput={() => clearFieldError('password2')}
            autocomplete="new-password"
          />
          {#if fieldErrors.password2}
            <span class="field-error">{fieldErrors.password2}</span>
          {/if}
        </label>

        <button type="submit" class="btn-primary" disabled={loading}>
          {loading ? 'Creating account...' : 'Create Account'}
        </button>
      </form>

      <p class="footer-text">
        Already have an account?
        <a href="/" class="link-btn">Sign In</a>
      </p>
    {/if}
  </div>
</div>

<style>
  .page {
    display: flex; justify-content: center; align-items: center; min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  .card {
    background: white; border-radius: 16px; padding: 40px; width: 100%;
    max-width: 400px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);
  }
  .logo {
    width: 48px; height: 48px; background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 12px; margin-bottom: 24px;
  }
  h1 { margin: 0 0 24px; font-size: 24px; color: #1a1a2e; }
  label { display: block; margin-bottom: 16px; font-size: 14px; color: #666; }
  input {
    display: block; width: 100%; padding: 10px 12px; margin-top: 6px;
    border: 1px solid #ddd; border-radius: 8px; font-size: 16px; box-sizing: border-box;
    transition: border-color 0.15s;
  }
  input:focus { outline: none; border-color: #4361ee; box-shadow: 0 0 0 3px rgba(67,97,238,0.15); }
  input.input-error { border-color: #dc2626; }
  input.input-error:focus { box-shadow: 0 0 0 3px rgba(220,38,38,0.2); }
  .field-error {
    display: block; margin-top: 4px; font-size: 12px; color: #dc2626;
  }
  .field-hint {
    display: block; margin-top: 4px; font-size: 11px; color: #999;
  }
  .btn-primary {
    background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none;
    padding: 12px 24px; border-radius: 8px; font-size: 16px; cursor: pointer;
    width: 100%; margin-top: 8px; font-weight: 600;
  }
  .btn-primary:hover { transform: translateY(-1px); }
  .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
  .error {
    background: #fee; color: #c0392b; padding: 12px; border-radius: 8px;
    margin-bottom: 16px; font-size: 14px;
  }
  .success {
    background: #d4edda; color: #155724; padding: 16px; border-radius: 8px;
    margin-bottom: 24px; font-size: 14px; line-height: 1.6;
  }
  .redirect-hint {
    font-size: 12px;
    color: #888;
    margin-top: 8px;
    animation: pulse 1.5s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  .footer-text { margin-top: 24px; text-align: center; font-size: 14px; color: #666; }
  .link-btn {
    background: none; border: none; color: #4361ee; cursor: pointer;
    font-size: 14px; padding: 0; font-family: inherit;
  }
  .link-btn:hover { text-decoration: underline; }
</style>
