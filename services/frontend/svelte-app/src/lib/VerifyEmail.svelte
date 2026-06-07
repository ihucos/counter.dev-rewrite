<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';

  let { onNavigate } = $props();

  let verificationKey = $state('');
  let loading = $state(true);
  let error = $state('');
  let success = $state(false);
  let alreadyVerified = $state(false);

  function flash(message, type = 'info') {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message, type } }));
  }

  onMount(async () => {
    const params = new URLSearchParams(window.location.search);
    const key = params.get('key');

    if (!key) {
      loading = false;
      error = 'No verification key provided. The link in your email should contain a verification key.';
      return;
    }

    verificationKey = key;

    try {
      const result = await api.verifyEmail({ key });
      success = true;
      flash('Email verified successfully! Your account is now active.', 'success');
    } catch (e) {
      if (e.status === 400) {
        const data = e.data || {};
        if (data.detail && data.detail.toLowerCase().includes('already verified')) {
          alreadyVerified = true;
          flash('Your email was already verified.', 'info');
        } else {
          error = e.message || 'Failed to verify email. The link may have expired.';
          flash(e.message || 'Verification failed', 'error');
        }
      } else {
        error = e.message || 'Failed to verify email. Please try again.';
        flash(e.message || 'Verification failed', 'error');
      }
    } finally {
      loading = false;
    }
  });
</script>

<div class="verify-page">
  <div class="verify-card">
    <div class="logotype"></div>
    <h1>Email Verification</h1>

    {#if loading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Verifying your email address...</p>
      </div>
    {:else if success || alreadyVerified}
      <div class="success-message">
        {#if success}
          Your email has been verified successfully. You can now use all features of your account.
        {:else}
          Your email was already verified. No further action is needed.
        {/if}
      </div>
      <p class="action-link">
        <button class="link-btn" onclick={() => onNavigate('login')}>Go to sign in</button>
      </p>
    {:else}
      <div class="error-message">
        {error}
      </div>
      <p class="action-link">
        <button class="link-btn" onclick={() => onNavigate('login')}>Back to sign in</button>
      </p>
      <p class="description small">
        If the link has expired, you can request a new verification email from your account settings after signing in.
      </p>
    {/if}
  </div>
</div>

<style>
  .verify-page {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #f5f5f5;
  }
  .verify-card {
    background: white;
    border-radius: 8px;
    padding: 40px;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    text-align: center;
  }
  .logotype {
    width: 32px;
    height: 32px;
    background: #2563eb;
    border-radius: 8px;
    margin: 0 auto 24px;
  }
  h1 {
    font-size: 24px;
    margin-bottom: 24px;
    font-family: 'Nunito Sans', sans-serif;
  }
  .loading-state {
    padding: 20px 0;
  }
  .loading-state p {
    color: #666;
    font-size: 14px;
    margin-top: 16px;
  }
  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid #e5e7eb;
    border-top-color: #2563eb;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin: 0 auto;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  .error-message {
    background: #fef2f2;
    color: #dc2626;
    padding: 16px;
    border-radius: 6px;
    margin-bottom: 16px;
    font-size: 14px;
    line-height: 1.5;
    text-align: left;
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
  .action-link {
    margin-top: 16px;
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
  .description.small {
    font-size: 12px;
    color: #999;
    line-height: 1.5;
    margin-top: 16px;
  }
</style>
