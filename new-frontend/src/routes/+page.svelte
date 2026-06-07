<script>
  import { goto } from '$app/navigation';
  import { api } from '$lib/api.js';

  let username = $state('');
  let password = $state('');
  let error = $state('');
  let loading = $state(false);
  let showPassword = $state(false);

  function flash(msg, type = 'info') {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message: msg, type } }));
  }

  async function handleLogin() {
    error = '';
    if (!username.trim() || !password) {
      error = 'Please fill in all fields.';
      return;
    }
    loading = true;
    try {
      await api.login(username, password);
      flash('Welcome back!', 'success');
      goto('/dashboard');
    } catch (e) {
      error = e.message || 'Login failed.';
    } finally {
      loading = false;
    }
  }

  // Redirect to dashboard if already authenticated
  $effect(() => {
    api.getUser().then(() => {
      goto('/dashboard');
    }).catch(() => {
      // not authenticated, stay on login
    });
  });
</script>

<div class="page">
  <div class="card">
    <div class="logo"></div>
    <h1>Sign In</h1>

    <form onsubmit={(e) => { e.preventDefault(); handleLogin(); }}>
      {#if error}
        <div class="error">{error}</div>
      {/if}

      <label>
        Username
        <input type="text" bind:value={username} placeholder="Your username" required disabled={loading} />
      </label>

      <label>
        Password
        <div class="pw-wrap">
          <input
            type={showPassword ? 'text' : 'password'}
            bind:value={password}
            placeholder="Your password"
            required
            disabled={loading}
          />
          <button type="button" class="toggle" onclick={() => showPassword = !showPassword}>
            {showPassword ? '🙈' : '👁️'}
          </button>
        </div>
      </label>

      <button type="submit" class="btn-primary" disabled={loading}>
        {loading ? 'Signing in...' : 'Sign In'}
      </button>

      <div class="links">
        <a href="/reset-password" class="link-btn">Forgot password?</a>
      </div>
    </form>

    <p class="footer-text">
      Don't have an account?
      <a href="/register" class="link-btn">Sign Up</a>
    </p>
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
    border: 1px solid #ddd; border-radius: 8px; font-size: 16px;
  }
  input:focus { outline: none; border-color: #4361ee; box-shadow: 0 0 0 3px rgba(67,97,238,0.15); }
  .pw-wrap { position: relative; margin-top: 6px; }
  .pw-wrap input { margin-top: 0; padding-right: 44px; }
  .toggle {
    position: absolute; right: 4px; top: 50%; transform: translateY(-50%);
    background: none; border: none; cursor: pointer; font-size: 18px; padding: 8px;
  }
  .btn-primary {
    background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none;
    padding: 12px 24px; border-radius: 8px; font-size: 16px; cursor: pointer;
    width: 100%; margin-top: 8px; font-weight: 600; transition: transform 0.1s;
  }
  .btn-primary:hover { transform: translateY(-1px); }
  .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
  .error {
    background: #fee; color: #c0392b; padding: 12px; border-radius: 8px;
    margin-bottom: 16px; font-size: 14px;
  }
  .links { text-align: center; margin-top: 12px; }
  .footer-text { margin-top: 24px; text-align: center; font-size: 14px; color: #666; }
  .link-btn {
    background: none; border: none; color: #4361ee; cursor: pointer;
    font-size: 14px; padding: 0; font-family: inherit;
  }
  .link-btn:hover { text-decoration: underline; }
</style>
