<script>
  import { api } from '$lib/api.js';

  let { onNavigate } = $props();

  let email = $state('');
  let error = $state('');
  let loading = $state(false);
  let success = $state(false);

  function flash(message, type = 'info') {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message, type } }));
  }

  async function handleRequestReset() {
    error = '';
    loading = true;
    try {
      // dj_rest_auth PasswordResetView expects 'email' field
      await api.requestPasswordReset({ email });
      success = true;
      flash('Password reset email sent if account exists.', 'success');
    } catch (e) {
      error = e.message || 'Request failed';
      if (e.data && typeof e.data === 'object') {
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

<div class="reset-page">
  <div class="reset-card">
    <div class="logotype"></div>
    <h1>Reset Password</h1>

    {#if success}
      <div class="success-message">
        If an account with that email address exists, we have sent password reset instructions. Please check your email.
      </div>
      <p class="back-link">
        <button class="link-btn" onclick={() => onNavigate('login')}>Back to sign in</button>
      </p>
    {:else}
      <p class="description">Enter the email address associated with your account and we'll send you a link to reset your password.</p>

      <form onsubmit={(e) => { e.preventDefault(); handleRequestReset(); }}>
        {#if error}
          <div class="error-message">{error}</div>
        {/if}

        <label>
          Email
          <input
            type="email"
            bind:value={email}
            placeholder="Your email address"
            required
            disabled={loading}
          />
        </label>

        <button type="submit" class="btn-primary full" disabled={loading}>
          {loading ? 'Sending...' : 'Send reset link'}
        </button>
      </form>

      <p class="back-link">
        <button class="link-btn" onclick={() => onNavigate('login')}>Back to sign in</button>
      </p>
    {/if}
  </div>
</div>

<style>
  .reset-page {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #f5f5f5;
  }
  .reset-card {
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
    margin-bottom: 12px;
    font-family: 'Nunito Sans', sans-serif;
  }
  .description {
    font-size: 14px;
    color: #666;
    margin-bottom: 24px;
    line-height: 1.5;
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
  .success-message {
    background: #d1fae5;
    color: #065f46;
    padding: 16px;
    border-radius: 6px;
    margin-bottom: 24px;
    font-size: 14px;
    line-height: 1.5;
  }
  .back-link {
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
