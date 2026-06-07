<script>
  import { onMount } from 'svelte';
  import { api } from './lib/api.js';
  import Login from './lib/Login.svelte';
  import Register from './lib/Register.svelte';
  import Dashboard from './lib/Dashboard.svelte';
  import PasswordResetRequest from './lib/PasswordResetRequest.svelte';
  import PasswordResetConfirm from './lib/PasswordResetConfirm.svelte';
  import VerifyEmail from './lib/VerifyEmail.svelte';
  import Flash from './lib/Flash.svelte';
  import './app.css';

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
    currentPage = page;
  }

  function handleAuthChanged(e) {
    isAuthenticated = e.detail.authenticated;
    if (!e.detail.authenticated) {
      currentPage = 'login';
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
  <Register {navigateTo} />
{:else if currentPage === 'reset-request'}
  <PasswordResetRequest {navigateTo} />
{:else if currentPage === 'reset-confirm'}
  <PasswordResetConfirm {navigateTo} />
{:else if currentPage === 'verify-email'}
  <VerifyEmail {navigateTo} />
{:else}
  <Login {navigateTo} />
{/if}

<style>
  .loading-screen {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #f0f2f5;
  }
  .spinner {
    width: 36px;
    height: 36px;
    border: 3px solid #e0e0e0;
    border-top-color: #4361ee;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
