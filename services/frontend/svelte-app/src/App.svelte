<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import Login from '$lib/Login.svelte';
  import Register from '$lib/Register.svelte';
  import Dashboard from '$lib/Dashboard.svelte';
  import PasswordResetRequest from '$lib/PasswordResetRequest.svelte';
  import PasswordResetConfirm from '$lib/PasswordResetConfirm.svelte';
  import VerifyEmail from '$lib/VerifyEmail.svelte';
  import Flash from '$lib/Flash.svelte';

  let isAuthenticated = $state(false);
  let checkingAuth = $state(true);
  let currentPage = $state('login');

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

  function navigateTo(page) {
    if (page === 'login' || page === 'register' || page === 'reset-request') {
      const url = new URL(window.location);
      url.search = '';
      window.history.replaceState({}, '', url);
    }
    currentPage = page;
  }

  function handleAuthChanged(e) {
    isAuthenticated = e.detail.authenticated;
    if (e.detail.authenticated) {
      checkAuth();
    }
  }

  onMount(() => {
    const params = new URLSearchParams(window.location.search);

    if (params.get('uid') && params.get('token')) {
      currentPage = 'reset-confirm';
    } else if (params.get('key')) {
      currentPage = 'verify-email';
    }

    checkAuth();

    window.addEventListener('auth-changed', handleAuthChanged);
    return () => window.removeEventListener('auth-changed', handleAuthChanged);
  });
</script>

<Flash />

{#if checkingAuth}
  <div class="loading-screen">
    <div class="spinner"></div>
  </div>
{:else if isAuthenticated}
  <Dashboard />
{:else if currentPage === 'register'}
  <Register onNavigate={navigateTo} />
{:else if currentPage === 'reset-request'}
  <PasswordResetRequest onNavigate={navigateTo} />
{:else if currentPage === 'reset-confirm'}
  <PasswordResetConfirm onNavigate={navigateTo} />
{:else if currentPage === 'verify-email'}
  <VerifyEmail onNavigate={navigateTo} />
{:else}
  <Login onNavigate={navigateTo} />
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
