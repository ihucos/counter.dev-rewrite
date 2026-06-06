<script>
  import { page } from '$app/state';
  import { enhance } from '$app/forms';

  let tab = $derived(page.url.searchParams.get('tab') || 'login');
  let forgotPassword = $state(false);
  let forgotEmail = $state('');
</script>

<div class="welcome">
  <div class="card">
    <h1>Analytics Dashboard</h1>
    <p class="subtitle">Sign in to access your analytics</p>
    
    <div class="tabs">
      <a href="/?tab=login" class="tab" class:active={tab === 'login'}>Log In</a>
      <a href="/?tab=signup" class="tab" class:active={tab === 'signup'}>Sign Up</a>
    </div>

    {#if tab === 'login'}
      <form method="POST" action="?/login" use:enhance>
        <label>
          Username or Email
          <input type="text" name="username" required />
        </label>
        <label>
          Password
          <input type="password" name="password" required />
        </label>
        <button type="submit" class="btn-primary btn-full">Log In</button>
        <button type="button" class="btn-link" onclick={() => forgotPassword = !forgotPassword}>
          Forgot password?
        </button>
        
        {#if forgotPassword}
          <div class="forgot-password">
            <form method="POST" action="?/forgot_password" use:enhance>
              <label>
                Email
                <input type="email" name="email" bind:value={forgotEmail} required />
              </label>
              <button type="submit" class="btn-secondary btn-full">Reset Password</button>
            </form>
          </div>
        {/if}
      </form>
    {:else}
      <form method="POST" action="?/register" use:enhance>
        <label>
          Username
          <input type="text" name="username" required />
        </label>
        <label>
          Email
          <input type="email" name="email" required />
        </label>
        <label>
          Password
          <input type="password" name="password1" required />
        </label>
        <label>
          Confirm Password
          <input type="password" name="password2" required />
        </label>
        <button type="submit" class="btn-primary btn-full">Create Account</button>
      </form>
    {/if}
  </div>
</div>

<style>
  .welcome {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 140px);
  }
  .card {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: 2rem;
    width: 100%;
    max-width: 400px;
    box-shadow: var(--shadow);
  }
  h1 {
    text-align: center;
    margin-bottom: 0.5rem;
  }
  .subtitle {
    text-align: center;
    color: var(--color-text-muted);
    margin-bottom: 1.5rem;
  }
  .tabs {
    display: flex;
    margin-bottom: 1.5rem;
    border-bottom: 2px solid var(--color-border);
  }
  .tab {
    flex: 1;
    text-align: center;
    padding: 0.5rem;
    color: var(--color-text-muted);
    text-decoration: none;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
  }
  .tab.active {
    color: var(--color-primary);
    border-bottom-color: var(--color-primary);
  }
  label {
    display: block;
    margin-bottom: 0.75rem;
  }
  .btn-full {
    width: 100%;
    margin-top: 0.5rem;
  }
  .btn-link {
    background: none;
    border: none;
    color: var(--color-primary);
    padding: 0;
    margin-top: 0.5rem;
    display: inline-block;
  }
  .btn-link:hover {
    text-decoration: underline;
  }
  .forgot-password {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--color-border);
  }
</style>--- a/src/routes/api/core/query/+server.js
