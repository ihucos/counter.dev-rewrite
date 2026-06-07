<script>
  import { api } from '$lib/api.js';

  let { onNavigate } = $props();

  let username = $state('');
  let email = $state('');
  let password1 = $state('');
  let password2 = $state('');
  let error = $state('');
  let loading = $state(false);
  let success = $state(false);

  function getUTCOffset() {
    return Math.round((-1 * new Date().getTimezoneOffset()) / 60);
  }

  async function handleRegister() {
    error = '';
    loading = true;
    try {
      await api.register({
        username,
        email,
        password1,
        password2,
        timezone: getUTCOffset(),
      });
      // Registration success - dispatch auth event so App.svelte transitions
      window.dispatchEvent(new CustomEvent('auth-changed', { detail: { authenticated: true } }));
    } catch (e) {
      error = e.message || 'Registration failed';
      if (e.data && typeof e.data === 'object') {
        // Join all field errors into a single message
        const msgs = [];
        for (const [field, errors] of Object.entries(e.data)) {
          if (Array.isArray(errors)) {
            msgs.push(`${field}: ${errors.join(', ')}`);
          }
        }
        if (msgs.length > 0) {
          error = msgs.join('; ');
        }
      }
    } finally {
      loading = false;
    }
  }
</script>

<div class="register-page">
  <div class="register-card">
    <div class="logotype"></div>
    <h1>Sign up to Counter</h1>

    <form onsubmit={(e) => { e.preventDefault(); handleRegister(); }}>
      {#if error}
        <div class="error-message">{error}</div>
      {/if}

      <label>
        Username
        <input
          type="text"
          bind:value={username}
          placeholder="Choose a username"
          required
          disabled={loading}
        />
      </label>

      <label>
        Email
        <input
          type="email"
          bind:value={email}
          placeholder="Your email (optional)"
          disabled={loading}
        />
      </label>

      <label>
        Password
        <input
          type="password"
          bind:value={password1}
          placeholder="Choose a password"
          required
          disabled={loading}
        />
      </label>

      <label>
        Confirm Password
        <input
          type="password"
          bind:value={password2}
          placeholder="Repeat password"
          required
          disabled={loading}
        />
      </label>

      <button type="submit" class="btn-primary full" disabled={loading}>
        {loading ? 'Creating account...' : 'Create account'}
      </button>
    </form>

    <p class="login-link">
      Already have an account?
      <button class="link-btn" onclick={() => onNavigate('login')}>Sign in</button>
    </p>
  </div>
</div>

<style>
  .register-page {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #f5f5f5;
  }
  .register-card {
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
  .login-link {
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
