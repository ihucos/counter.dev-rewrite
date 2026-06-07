<script>
  import { api } from '$lib/api.js';

  let username = '';
  let password = '';
  let error = '';
  let loading = false;

  async function handleLogin() {
    error = '';
    loading = true;
    try {
      await api.login(username, password);
      // Dispatch custom event so App.svelte can react
      window.dispatchEvent(new CustomEvent('auth-changed', { detail: { authenticated: true } }));
    } catch (e) {
      error = e.message || 'Login failed';
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
        />
      </label>

      <label>
        Password
        <input
          type="password"
          bind:value={password}
          placeholder="Your password"
          required
          disabled={loading}
        />
      </label>

      <button type="submit" class="btn-primary full" disabled={loading}>
        {loading ? 'Signing in...' : 'Sign in'}
      </button>
    </form>

    <p class="signup-link">
      Don't have an account? <a href="/welcome.html?sign-up">Sign up</a>
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
  .signup-link {
    margin-top: 24px;
    text-align: center;
    font-size: 14px;
    color: #666;
  }
  .signup-link a {
    color: #2563eb;
    text-decoration: none;
  }
</style>
