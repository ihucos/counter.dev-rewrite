<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';

  let { onNavigate } = $props();

  // Parse the reset token, uid from URL query params
  let uid = $state('');
  let token = $state('');
  let newPassword1 = $state('');
  let newPassword2 = $state('');
  let error = $state('');
  let loading = $state(false);
  let success = $state(false);
  let parsed = $state(false);

  onMount(() => {
    const params = new URLSearchParams(window.location.search);
    uid = params.get('uid') || '';
    token = params.get('token') || '';
    parsed = true;
  });

  async function handleConfirmReset() {
    error = '';
    loading = true;
    try {
      // dj_rest_auth PasswordResetConfirmView expects uid, token, new_password1, new_password2
      await api.confirmPasswordReset({
        uid,
        token,
        new_password1: newPassword1,
        new_password2: newPassword2,
      });
      success = true;
    } catch (e) {
      error = e.message || 'Failed to reset password';
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

<div class="confirm-page">
  <div class="confirm-card">
    <div class="logotype"></div>
    <h1>Set New Password</h1>

    {#if !parsed}
      <div class="loading-message">Loading...</div>
    {:else if success}
      <div class="success-message">
        Your password has been reset successfully.
      </div>
      <p class="back-link">
        <button class="link-btn" onclick={() => onNavigate('login')}>Sign in with your new password</button>
      </p>
    {:else if !uid || !token}
      <div class="error-message">
        Invalid or missing reset link. Please request a new password reset.
      </div>
      <p class="back-link">
        <button class="link-btn" onclick={() => onNavigate('login')}>Back to sign in</button>
      </p>
    {:else}
      <p class="description">Choose a new password for your account.</p>

      <form onsubmit={(e) => { e.preventDefault(); handleConfirmReset(); }}>
        {#if error}
          <div class="error-message">{error}</div>
        {/if}

        <label>
          New Password
          <input
            type="password"
            bind:value={newPassword1}
            placeholder="New password (min. 6 characters)"
            required
            disabled={loading}
          />
        </label>

        <label>
          Confirm New Password
          <input
            type="password"
            bind:value={newPassword2}
            placeholder="Repeat new password"
            required
            disabled={loading}
          />
        </label>

        <button type="submit" class="btn-primary full" disabled={loading || !newPassword1 || !newPassword2}>
          {loading ? 'Resetting...' : 'Reset password'}
        </button>
      </form>

      <p class="back-link">
        <button class="link-btn" onclick={() => onNavigate('login')}>Back to sign in</button>
      </p>
    {/if}
  </div>
</div>

<style>
  .confirm-page {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #f5f5f5;
  }
  .confirm-card {
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
  .loading-message {
    text-align: center;
    padding: 40px 0;
    color: #666;
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
