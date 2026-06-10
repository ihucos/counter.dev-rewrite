<script lang="ts">
  import { page } from '$app/state';
  import { api } from '$lib/api.js';

  let loading = $state(true);
  let error = $state('');
  let errorDetail = $state('');
  let success = $state(false);
  let alreadyVerified = $state(false);

  function flash(msg: string, type: string = 'info'): void {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message: msg, type } }));
  }

  $effect(() => {
    const key = page.url.searchParams.get('key');
    if (!key) {
      error = 'No verification key found in the URL.';
      errorDetail = 'The verification link you clicked is missing the required key parameter. Please check that the full URL was copied correctly.';
      loading = false;
      return;
    }

    api.verifyEmail(key)
      .then(() => {
        success = true;
        flash('Email verified successfully!', 'success');
      })
      .catch((e: unknown) => {
        const err = e as { status?: number; message?: string; data?: Record<string, unknown> };

        // Check for "already verified" in the response detail
        if (err.data && typeof err.data.detail === 'string') {
          const detail = (err.data.detail as string).toLowerCase();
          if (detail.includes('already verified')) {
            alreadyVerified = true;
            flash('Your email was already verified.', 'info');
            return;
          }
        }

        // Check for "already verified" in the error message too
        if (err.message && err.message.toLowerCase().includes('already verified')) {
          alreadyVerified = true;
          flash('Your email was already verified.', 'info');
          return;
        }

        error = err.message || 'Verification failed.';
        errorDetail = 'The verification link may have expired or is invalid. Please try registering again or contact support.';
      })
      .finally(() => {
        loading = false;
      });
  });
</script>

<div class="page">
  <div class="card">
    <div class="logo"></div>
    <h1>Email Verification</h1>

    {#if loading}
      <p class="loading-text">Verifying your email...</p>
      <div class="spinner"></div>
    {:else if success}
      <div class="success">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <span>Email verified successfully!</span>
      </div>
      <p class="info-text">Your account is now fully activated. You can sign in to access the dashboard.</p>
      <a href="/" class="btn-primary" style="display:block;text-align:center;">Go to Sign In</a>
    {:else if alreadyVerified}
      <div class="info">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
        </svg>
        <span>Your email was already verified.</span>
      </div>
      <p class="info-text">No further action is needed. You can sign in to access the dashboard.</p>
      <a href="/" class="btn-primary" style="display:block;text-align:center;">Go to Sign In</a>
    {:else}
      <div class="error">{error}</div>
      {#if errorDetail}
        <p class="error-detail">{errorDetail}</p>
      {/if}
      <a href="/" class="btn-primary" style="display:block;text-align:center;">Back to Sign In</a>
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
    max-width: 420px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); text-align: center;
  }
  .logo {
    width: 48px; height: 48px; background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 12px; margin: 0 auto 24px;
  }
  h1 { margin: 0 0 24px; font-size: 24px; color: #1a1a2e; }
  .loading-text {
    color: #666;
    font-size: 14px;
    margin-bottom: 16px;
  }
  .spinner {
    width: 32px; height: 32px; border: 3px solid #e0e0e0; border-top-color: #4361ee;
    border-radius: 50%; animation: spin 0.7s linear infinite; margin: 0 auto 24px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .info-text {
    font-size: 13px;
    color: #666;
    margin-bottom: 20px;
    line-height: 1.5;
  }
  .btn-primary {
    background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none;
    padding: 12px 24px; border-radius: 8px; font-size: 16px; cursor: pointer;
    width: 100%; font-weight: 600; display: block; text-decoration: none;
  }
  .btn-primary:hover { transform: translateY(-1px); }
  .error {
    display: flex; align-items: center; gap: 10px;
    background: #fee; color: #c0392b; padding: 12px 16px; border-radius: 8px;
    margin-bottom: 8px; font-size: 14px; text-align: left;
  }
  .error-detail {
    font-size: 13px;
    color: #888;
    margin-bottom: 20px;
    line-height: 1.5;
  }
  .success {
    display: flex; align-items: center; justify-content: center; gap: 10px;
    background: #d4edda; color: #155724; padding: 16px; border-radius: 8px;
    margin-bottom: 16px; font-size: 14px;
  }
  .success svg { width: 24px; height: 24px; flex-shrink: 0; }
  .info {
    display: flex; align-items: center; justify-content: center; gap: 10px;
    background: #e8f4fd; color: #0c5460; padding: 16px; border-radius: 8px;
    margin-bottom: 16px; font-size: 14px;
  }
  .info svg { width: 24px; height: 24px; flex-shrink: 0; }
</style>
