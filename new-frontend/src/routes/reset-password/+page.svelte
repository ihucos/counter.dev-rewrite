<script lang="ts">
  import { api } from '$lib/api.js';

  let email = $state('');
  let error = $state('');
  let loading = $state(false);
  let done = $state(false);

  async function handleReset(): Promise<void> {
    error = '';
    if (!email.trim()) { error = 'Please enter your email.'; return; }
    loading = true;
    try {
      await api.requestPasswordReset(email);
      done = true;
    } catch (e) {
      error = (e as Error).message || 'Request failed.';
    } finally {
      loading = false;
    }
  }
</script>

<div class="page">
  <div class="card">
    <div class="logo"></div>
    <h1>Reset Password</h1>

    {#if done}
      <div class="success">
        If an account with that email exists, we've sent password reset instructions.
      </div>
      <a href="/" class="btn-primary" style="display:block;text-align:center;">Back to Sign In</a>
    {:else}
      <p class="desc">Enter your email and we'll send you a reset link.</p>
      <form onsubmit={(e: Event) => { e.preventDefault(); handleReset(); }}>
        {#if error}<div class="error">{error}</div>{/if}
        <label>
          Email
          <input type="email" bind:value={email} placeholder="Your email" required disabled={loading} />
        </label>
        <button type="submit" class="btn-primary" disabled={loading}>
          {loading ? 'Sending...' : 'Send Reset Link'}
        </button>
      </form>
      <p class="footer-text">
        <a href="/" class="link-btn">Back to Sign In</a>
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
  h1 { margin: 0 0 12px; font-size: 24px; color: #1a1a2e; }
  .desc { font-size: 14px; color: #666; margin-bottom: 24px; }
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
  .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
  .error {
    background: #fee; color: #c0392b; padding: 12px; border-radius: 8px;
    margin-bottom: 16px; font-size: 14px;
  }
  .success {
    background: #d4edda; color: #155724; padding: 16px; border-radius: 8px;
    margin-bottom: 24px; font-size: 14px; line-height: 1.5;
  }
  .footer-text { margin-top: 24px; text-align: center; font-size: 14px; color: #666; }
  .link-btn {
    background: none; border: none; color: #4361ee; cursor: pointer;
    font-size: 14px; padding: 0; font-family: inherit;
  }
  .link-btn:hover { text-decoration: underline; }
</style>
