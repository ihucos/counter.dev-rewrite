<script lang="ts">
  /**
   * VerifyEmail component that handles email verification via a URL key.
   * Can be used standalone or as part of a route page.
   *
   * Props:
   *   key: string - the verification key from the URL query param
   *   onVerified: () => void - callback after successful verification
   *   onError: (msg: string) => void - callback on error
   */
  import { api } from '$lib/api.js';

  let {
    key = '',
    onVerified = () => {},
    onError = (_msg: string) => {},
  }: {
    key: string;
    onVerified?: () => void;
    onError?: (msg: string) => void;
  } = $props();

  let loading = $state(true);
  let error = $state('');
  let success = $state(false);
  let alreadyVerified = $state(false);
  let done = $state(false);

  function flash(msg: string, type: string = 'info'): void {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message: msg, type } }));
  }

  $effect(() => {
    if (!key || done) return;

    loading = true;
    api.verifyEmail(key)
      .then(() => {
        success = true;
        flash('Email verified successfully!', 'success');
        onVerified();
      })
      .catch((e: unknown) => {
        const err = e as { status?: number; data?: Record<string, unknown>; message?: string };
        if (err.status === 400) {
          const data = err.data || {};
          const detail = typeof data.detail === 'string' ? data.detail.toLowerCase() : '';
          if (detail.includes('already verified')) {
            alreadyVerified = true;
            flash('Your email was already verified.', 'info');
          } else {
            error = err.message || 'Failed to verify email. The link may have expired.';
            onError(error);
          }
        } else {
          error = err.message || 'Failed to verify email. Please try again.';
          onError(error);
        }
      })
      .finally(() => {
        loading = false;
        done = true;
      });
  });
</script>

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
{:else}
  <div class="error-message">{error}</div>
{/if}

<style>
  .loading-state {
    text-align: center;
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
  .success-message {
    background: #d4edda;
    color: #155724;
    padding: 16px;
    border-radius: 8px;
    font-size: 14px;
    line-height: 1.5;
  }
  .error-message {
    background: #fee;
    color: #c0392b;
    padding: 16px;
    border-radius: 8px;
    font-size: 14px;
    line-height: 1.5;
  }
</style>
