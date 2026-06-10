<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/state';
  import { api } from '$lib/api.js';

  let uid = $state('');
  let token = $state('');
  let password1 = $state('');
  let password2 = $state('');
  let error = $state('');
  let fieldErrors = $state<Record<string, string>>({});
  let loading = $state(false);
  let done = $state(false);

  // Read query params from the URL on mount
  $effect(() => {
    const params = page.url.searchParams;
    uid = params.get('uid') || '';
    token = params.get('token') || '';
  });

  function flash(msg: string, type: string = 'info'): void {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message: msg, type } }));
  }

  function validateForm(): Record<string, string> {
    const errs: Record<string, string> = {};

    if (!password1) {
      errs.password1 = 'New password is required';
    } else if (password1.length < 6) {
      errs.password1 = 'Password must be at least 6 characters';
    }

    if (password1 !== password2) {
      errs.password2 = 'Passwords do not match';
    }

    return errs;
  }

  async function handleConfirm(): Promise<void> {
    error = '';
    fieldErrors = {};

    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length > 0) {
      fieldErrors = validationErrors;
      return;
    }

    loading = true;
    try {
      await api.confirmPasswordReset({
        uid,
        token,
        new_password1: password1,
        new_password2: password2,
      });
      done = true;
      flash('Password reset successfully! You can now sign in.', 'success');
      // Redirect to login after a short delay
      setTimeout(() => goto('/'), 2000);
    } catch (e: unknown) {
      const err = e as { status?: number; message?: string; data?: Record<string, unknown> };
      error = err.message || 'Failed to reset password. The link may have expired.';

      // Check for field-level errors in API response
      if (err.data && typeof err.data === 'object') {
        const fieldMap: Record<string, string> = {};
        for (const [field, errs] of Object.entries(err.data)) {
          if (Array.isArray(errs)) {
            fieldMap[field] = errs.join(', ');
          }
        }
        if (Object.keys(fieldMap).length > 0) {
          fieldErrors = fieldMap;
        }
      }
    } finally {
      loading = false;
    }
  }
</script>

<div class="page">
  <div class="card">
    <div class="logo"></div>
    <h1>Set New Password</h1>

    {#if done}
      <div class="success">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <span>Password reset successfully! Redirecting to sign in...</span>
      </div>
    {:else if !uid || !token}
      <div class="error">Invalid or missing reset link. Please request a new password reset.</div>
      <a href="/reset-password" class="btn-primary" style="display:block;text-align:center;">Request New Reset</a>
    {:else}
      <p class="desc">Enter your new password below.</p>

      <form onsubmit={(e: Event) => { e.preventDefault(); handleConfirm(); }}>
        {#if error && Object.keys(fieldErrors).length === 0}
          <div class="error">{error}</div>
        {/if}

        <label>
          New Password
          <input
            type="password"
            bind:value={password1}
            placeholder="Min. 6 characters"
            required
            disabled={loading}
            class:input-error={!!fieldErrors.password1}
            autocomplete="new-password"
          />
          {#if fieldErrors.password1}
            <span class="field-error">{fieldErrors.password1}</span>
          {/if}
        </label>

        <label>
          Confirm Password
          <input
            type="password"
            bind:value={password2}
            placeholder="Repeat your new password"
            required
            disabled={loading}
            class:input-error={!!fieldErrors.password2}
            autocomplete="new-password"
          />
          {#if fieldErrors.password2}
            <span class="field-error">{fieldErrors.password2}</span>
          {/if}
        </label>

        <button type="submit" class="btn-primary" disabled={loading || !password1 || !password2}>
          {loading ? 'Resetting...' : 'Reset Password'}
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
    transition: border-color 0.15s;
  }
  input:focus { outline: none; border-color: #4361ee; box-shadow: 0 0 0 3px rgba(67,97,238,0.15); }
  input.input-error { border-color: #dc2626; }
  input.input-error:focus { box-shadow: 0 0 0 3px rgba(220,38,38,0.2); }
  .field-error {
    display: block; margin-top: 4px; font-size: 12px; color: #dc2626;
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
  .success {
    display: flex; align-items: center; gap: 10px;
    background: #d4edda; color: #155724; padding: 16px; border-radius: 8px;
    margin-bottom: 24px; font-size: 14px; line-height: 1.5;
  }
  .success svg { width: 24px; height: 24px; flex-shrink: 0; }
  .footer-text { margin-top: 24px; text-align: center; font-size: 14px; color: #666; }
  .link-btn {
    background: none; border: none; color: #4361ee; cursor: pointer;
    font-size: 14px; padding: 0; font-family: inherit;
  }
  .link-btn:hover { text-decoration: underline; }
</style>
