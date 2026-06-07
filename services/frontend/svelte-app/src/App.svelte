<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import Login from '$lib/Login.svelte';
  import Dashboard from '$lib/Dashboard.svelte';

  let isAuthenticated = $state(false);
  let checkingAuth = $state(true);

  async function checkAuth() {
    try {
      await api.getUser();
      isAuthenticated = true;
    } catch {
      isAuthenticated = false;
    } finally {
      checkingAuth = false;
    }
  }

  onMount(() => {
    checkAuth();

    // Listen for auth changes (login/logout)
    const handler = (e) => {
      isAuthenticated = e.detail.authenticated;
      if (e.detail.authenticated) {
        // Re-check auth state to ensure fresh CSRF tokens
        checkAuth();
      }
    };
    window.addEventListener('auth-changed', handler);
    return () => window.removeEventListener('auth-changed', handler);
  });
</script>

{#if checkingAuth}
  <div class="loading-screen">
    <div class="spinner"></div>
  </div>
{:else if isAuthenticated}
  <Dashboard />
{:else}
  <Login />
{/if}

<style>
  .loading-screen {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #f5f5f5;
  }
  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid #e5e7eb;
    border-top-color: #2563eb;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>
