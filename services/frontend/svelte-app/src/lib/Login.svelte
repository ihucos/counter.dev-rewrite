<script>
  import { api } from '$lib/api.js';

  let { onNavigate } = $props();

  let username = $state('');
  let password = $state('');
  let error = $state('');
  let loading = $state(false);
  let showPassword = $state(false);

  function flash(message, type = 'info') {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message, type } }));
  }

  function validateForm() {
    if (!username.trim()) {
      return 'Please enter your username.';
    }
    if (!password) {
      return 'Please enter your password.';
    }
    return null;
  }

  async function handleLogin() {
    error = '';

    const validationError = validateForm();
    if (validationError) {
      error = validationError;
      return;
    }

    loading = true;
    try {
      await api.login(username, password);
      flash('Welcome back!', 'success');
      window.dispatchEvent(new CustomEvent('auth-changed', { detail: { authenticated: true } }));
    } catch (e) {
      if (e.status === 400) {
        error = e.message || 'Invalid username or password.';
      } else if (e.status === 403) {
        error = 'Account not verified. Please check your email for a verification link.';
      } else {
        error = e.message || 'Login failed. Please try again.';
      }
    } finally {
      loading = false;
    }
  }
</script>

<div class="login-page">
  <div class="login-card">
    <div class="logotype"></div>
    <h1>Sign in to Counter</h1>

    <form onsubmit={(e) => { e.preventDefault(); handleLogin(); }}>
      {#if error}
        <div class="error-message">{error}</div>
      {/if}

      <label>
        Username
        <input
          type="text"
          bind:value={username}
          placeholder="Your username"
          required
          disabled={loading}
          autocomplete="username"
        />
      </label>

      <label>
        Password
        <div class="password-wrapper">
          <input
            type={showPassword ? 'text' : 'password'}
            bind:value={password}
            placeholder="Your password"
            required
            disabled={loading}
            autocomplete="current-password"
          />
          <button
            type="button"
            class="toggle-password"
            onclick={() => showPassword = !showPassword}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            tabindex="-1"
          >
            {#if showPassword}
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            {:else}
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            {/if}
          </button>
        </div>
      </label>

      <button type="submit" class="btn-primary full" disabled={loading}>
        {loading ? 'Signing in...' : 'Sign in'}
      </button>

      <div class="forgot-password">
        <button class="link-btn" onclick={() => onNavigate('reset-request')}>Forgot password?</button>
      </div>
    </form>

    <p class="signup-link">
      Don't have an account?
      <button class="link-btn" onclick={() => onNavigate('register')}>Sign up</button>
    </p>
  </div>
</div>

<style>
  .login-page {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #f5f5f5;
  }
  .login-card {
    background: white;
    border-radius: 8px;
    padding: 40px;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
  .logotype {
    width: 32px;
    height: 32px;
    background: #2563eb;
    border-radius: 8px;
    margin-bottom: 24px;
  }
  h1 {
    font-size: 24px;
    margin-bottom: 24px;
    font-family: 'Nunito Sans', sans-serif;
  }
  label {
    display: block;
    margin-bottom: 16px;
    font-size: 14px;
    color: #666;
  }
  input {
    display: block;
    width: 100%;
    padding: 10px 12px;
    margin-top: 6px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 16px;
    box-sizing: border-box;
  }
  input:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.2);
  }
  .password-wrapper {
    position: relative;
    display: block;
    margin-top: 6px;
  }
  .password-wrapper input {
    margin-top: 0;
    padding-right: 44px;
  }
  .toggle-password {
    position: absolute;
    right: 4px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    padding: 8px;
    cursor: pointer;
    color: #999;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 0;
  }
  .toggle-password:hover {
    color: #666;
  }
  .btn-primary {
    background: #2563eb;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    font-size: 16px;
    cursor: pointer;
    width: 100%;
    margin-top: 8px;
  }
  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .btn-primary:hover:not(:disabled) {
    background: #1d4ed8;
  }
  .full {
    width: 100%;
  }
  .error-message {
    background: #fef2f2;
    color: #dc2626;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 16px;
    font-size: 14px;
  }
  .forgot-password {
    text-align: center;
    margin-top: 12px;
  }
  .signup-link {
    margin-top: 24px;
    text-align: center;
    font-size: 14px;
    color: #666;
  }
  .link-btn {
    background: none;
    border: none;
    color: #2563eb;
    text-decoration: none;
    cursor: pointer;
    font-size: 14px;
    padding: 0;
    font-family: inherit;
  }
  .link-btn:hover {
    text-decoration: underline;
  }
</style>
