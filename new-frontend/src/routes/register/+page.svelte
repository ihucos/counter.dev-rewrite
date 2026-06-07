<script>
  import { goto } from '$app/navigation';
  import { api } from '$lib/api.js';

  let username = $state('');
  let email = $state('');
  let password1 = $state('');
  let password2 = $state('');
  let error = $state('');
  let loading = $state(false);
  let done = $state(false);

  function flash(msg, type = 'info') {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message: msg, type } }));
  }

  function utcOffset() {
    return Math.round((-1 * new Date().getTimezoneOffset()) / 60);
  }

  async function handleRegister() {
    error = '';
    if (!username.trim() || !password1 || !password2) {
      error = 'Please fill in required fields.';
      return;
    }
    if (password1 !== password2) {
      error = 'Passwords do not match.';
      return;
    }
    loading = true;
    try {
      await api.register({
        username: username.trim(),
        email: email.trim() || undefined,
        password1,
        password2,
        timezone: utcOffset(),
      });
      done = true;
      flash('Account created! Check your email for verification.', 'success');
    } catch (e) {
      error = e.message || 'Registration failed.';
    } finally {
      loading = false;
    }
  }
</script>

<div class="page">
  <div class="card">
    <div class="logo"></div>
    <h1>{done ? 'Check Your Email' : 'Create Account'}</h1>

    {#if done}
      <div class="success">
        <p>Your account has been created.</p>
        {#if email}
          <p>We sent a verification link to <strong>{email}</strong>.</p>
        {:else}
          <p>Your account is ready. Add an email later in settings for password recovery.</p>
        {/if}
      </div>
      <a href="/" class="btn-primary" style="display:block;text-align:center;">Go to Sign In</a>
    {:else}
      <form onsubmit={(e) => { e.preventDefault(); handleRegister(); }}>
        {#if error}<div class="error">{error}</div>{/if}

        <label>
          Username *
          <input type="text" bind:value={username} placeholder="Choose a username" required disabled={loading} />
        </label>
        <label>
          Email
          <input type="email" bind:value={email} placeholder="Your email (optional)" disabled={loading} />
        </label>
        <label>
          Password *
          <input type="password" bind:value={password1} placeholder="Min. 6 characters" required disabled={loading} />
        </label>
        <label>
          Confirm Password *
          <input type="password" bind:value={password2} placeholder="Repeat password" required disabled={loading} />
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
    border: 1px solid #ddd; border-radius: 8px; font-size: 16px;
  }
  input:focus { outline: none; border-color: #4361ee; box-shadow: 0 0 0 3px rgba(67,97,238,0.15); }
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
  .footer-text { margin-top: 24px; text-align: center; font-size: 14px; color: #666; }
  .link-btn {
    background: none; border: none; color: #4361ee; cursor: pointer;
    font-size: 14px; padding: 0; font-family: inherit;
  }
  .link-btn:hover { text-decoration: underline; }
</style>
