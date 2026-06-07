<script>
  import { onMount } from 'svelte';
  import { api } from './api.js';
  let { navigateTo } = $props();

  let loading = $state(true);
  let error = $state('');
  let success = $state(false);
  let alreadyVerified = $state(false);

  onMount(async () => {
    const params = new URLSearchParams(window.location.search);
    const key = params.get('key');
    if (!key) {
      error = 'No verification key found in the URL.';
      loading = false;
      return;
    }
    try {
      await api.verifyEmail(key);
      success = true;
    } catch (e) {
      if (e.data?.detail?.toLowerCase().includes('already verified')) {
        alreadyVerified = true;
      } else {
        error = e.message || 'Verification failed.';
      }
    } finally {
      loading = false;
    }
  });
</script>

<div class="page">
  <div class="card">
    <div class="logo"></div>
    <h1>Email Verification</h1>

    {#if loading}
      <p>Verifying your email...</p>
      <div class="spinner"></div>
    {:else if success || alreadyVerified}
      <div class="success">
        {success ? 'Email verified successfully!' : 'Email was already verified.'}
      </div>
      <button class="btn-primary" onclick={() => navigateTo('login')}>Go to Sign In</button>
    {:else}
      <div class="error">{error}</div>
      <button class="btn-primary" onclick={() => navigateTo('login')}>Back to Sign In</button>
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
    max-width: 400px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); text-align: center;
  }
  .logo {
    width: 48px; height: 48px; background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 12px; margin: 0 auto 24px;
  }
  h1 { margin: 0 0 24px; font-size: 24px; color: #1a1a2e; }
  .spinner {
    width: 32px; height: 32px; border: 3px solid #e0e0e0; border-top-color: #4361ee;
    border-radius: 50%; animation: spin 0.7s linear infinite; margin: 16px auto;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .btn-primary {
    background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none;
    padding: 12px 24px; border-radius: 8px; font-size: 16px; cursor: pointer;
    width: 100%; font-weight: 600;
  }
  .error {
    background: #fee; color: #c0392b; padding: 12px; border-radius: 8px;
    margin-bottom: 16px; font-size: 14px;
  }
  .success {
    background: #d4edda; color: #155724; padding: 16px; border-radius: 8px;
    margin-bottom: 24px; font-size: 14px;
  }
</style>
