<script>
  import { onMount } from 'svelte';
  import { getUser } from '$lib/api.js';
  import Login from '$lib/Login.svelte';
  import Dashboard from '$lib/Dashboard.svelte';

  let isAuthenticated = $state(false);
  let checkingAuth = $state(true);

  onMount(async () => {
    // Check if user is already authenticated
    try {
      await getUser();
      isAuthenticated = true;
    } catch {
      isAuthenticated = false;
    } finally {
      checkingAuth = false;
    }

    // Listen for auth changes (login/logout)
    window.addEventListener('auth-changed', (e) => {
      isAuthenticated = e.detail.authenticated;
    });
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
