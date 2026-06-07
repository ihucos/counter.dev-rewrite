<script>
  import { api } from '$lib/api.js';

  let { onNavigate } = $props();

  let username = $state('');
  let email = $state('');
  let password1 = $state('');
  let password2 = $state('');
  let error = $state('');
  let loading = $state(false);
  let registrationComplete = $state(false);
  let fieldErrors = $state({});

  function flash(message, type = 'info') {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message, type } }));
  }

  function getUTCOffset() {
    return Math.round((-1 * new Date().getTimezoneOffset()) / 60);
  }

  function validateForm() {
    const errors = {};

    if (!username.trim()) {
      errors.username = 'Username is required';
    } else if (username.trim().length < 2) {
      errors.username = 'Username must be at least 2 characters';
    } else if (!/^[a-zA-Z0-9_]+$/.test(username.trim())) {
      errors.username = 'Username can only contain letters, numbers, and underscores';
    }

    if (email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      errors.email = 'Please enter a valid email address';
    }

    if (!password1) {
      errors.password1 = 'Password is required';
    } else if (password1.length < 6) {
      errors.password1 = 'Password must be at least 6 characters';
    }

    if (password1 !== password2) {
      errors.password2 = 'Passwords do not match';
    }

    return errors;
  }

  async function handleRegister() {
    error = '';
    fieldErrors = {};

    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length > 0) {
      fieldErrors = validationErrors;
      return;
    }

    loading = true;
    try {
      const result = await api.register({
        username: username.trim(),
        email: email.trim() || undefined,
        password1,
        password2,
        timezone: getUTCOffset(),
      });

      if (result && result.user) {
        flash('Account created! Welcome to Counter.', 'success');
        window.dispatchEvent(new CustomEvent('auth-changed', { detail: { authenticated: true } }));
      } else {
        registrationComplete = true;
        flash('Account created! Please check your email to verify your account.', 'success');
      }
    } catch (e) {
      error = e.message || 'Registration failed';

      if (e.data && typeof e.data === 'object') {
        const fieldMap = {};
        for (const [field, errors] of Object.entries(e.data)) {
          if (Array.isArray(errors)) {
            fieldMap[field] = errors.join(', ');
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

  function clearFieldError(field) {
    fieldErrors = { ...fieldErrors, [field]: undefined };
  }
</script>

<div class="register-page">
  <div class="register-card">
    <div class="logotype"></div>

    {#if registrationComplete}
      <h1>Check Your Email</h1>
      <div class="success-message">
        <p>Your account has been created successfully.</p>
        {#if email}
          <p>We sent a verification link to <strong>{email}</strong>. Please check your inbox and click the link to activate your account.</p>
        {:else}
          <p>Since you didn't provide an email, your account is ready to use. You can add an email later in your settings.</p>
        {/if}
      </div>
      <p class="login-link">
        <button class="link-btn" onclick={() => onNavigate('login')}>Go to sign in</button>
      </p>
    {:else}
      <h1>Sign up to Counter</h1>

      <form onsubmit={(e) => { e.preventDefault(); handleRegister(); }}>
        {#if error}
          <div class="error-message">{error}</div>
        {/if}

        <label>
          Username
          <input
            type="text"
            bind:value={username}
            placeholder="Choose a username"
            required
            disabled={loading}
            class:input-error={fieldErrors.username}
            oninput={() => clearFieldError('username')}
          />
          {#if fieldErrors.username}
            <span class="field-error">{fieldErrors.username}</span>
          {/if}
        </label>

        <label>
          Email
          <input
            type="email"
            bind:value={email}
            placeholder="Your email (optional)"
            disabled={loading}
            class:input-error={fieldErrors.email}
            oninput={() => clearFieldError('email')}
          />
          {#if fieldErrors.email}
            <span class="field-error">{fieldErrors.email}</span>
          {:else}
            <span class="field-hint">Required for password reset and account notifications</span>
          {/if}
        </label>

        <label>
          Password
          <input
            type="password"
            bind:value={password1}
            placeholder="Choose a password (min. 6 characters)"
            required
            disabled={loading}
            class:input-error={fieldErrors.password1}
            oninput={() => clearFieldError('password1')}
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
            placeholder="Repeat password"
            required
            disabled={loading}
            class:input-error={fieldErrors.password2}
            oninput={() => clearFieldError('password2')}
          />
          {#if fieldErrors.password2}
            <span class="field-error">{fieldErrors.password2}</span>
          {/if}
        </label>

        <button type="submit" class="btn-primary full" disabled={loading}>
          {loading ? 'Creating account...' : 'Create account'}
        </button>
      </form>

      <p class="login-link">
        Already have an account?
        <button class="link-btn" onclick={() => onNavigate('login')}>Sign in</button>
      </p>
    {/if}
  </div>
</div>

<style>
  .register-page {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #f5f5f5;
  }
  .register-card {
    background: white;
    border-radius: 8px;
    padding: 40px;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
  .logotype {
    width: 32px;
    height: 32px;
    background: #2563eb;
    border-radius: 8px;
    margin-bottom: 24px;
  }
  h1 {
    font-size: 24px;
    margin-bottom: 24px;
    font-family: 'Nunito Sans', sans-serif;
  }
  label {
    display: block;
    margin-bottom: 16px;
    font-size: 14px;
    color: #666;
  }
  input {
    display: block;
    width: 100%;
    padding: 10px 12px;
    margin-top: 6px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 16px;
    box-sizing: border-box;
    transition: border-color 0.15s;
  }
  input:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.2);
  }
  input.input-error {
    border-color: #dc2626;
  }
  input.input-error:focus {
    box-shadow: 0 0 0 2px rgba(220,38,38,0.2);
  }
  .field-error {
    display: block;
    margin-top: 4px;
    font-size: 12px;
    color: #dc2626;
  }
  .field-hint {
    display: block;
    margin-top: 4px;
    font-size: 11px;
    color: #999;
  }
  .btn-primary {
    background: #2563eb;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    font-size: 16px;
    cursor: pointer;
    width: 100%;
    margin-top: 8px;
  }
  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .btn-primary:hover:not(:disabled) {
    background: #1d4ed8;
  }
  .full {
    width: 100%;
  }
  .error-message {
    background: #fef2f2;
    color: #dc2626;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 16px;
    font-size: 14px;
  }
  .success-message {
    background: #d1fae5;
    color: #065f46;
    padding: 16px;
    border-radius: 6px;
    margin-bottom: 24px;
    font-size: 14px;
    line-height: 1.6;
  }
  .success-message strong {
    color: #065f46;
  }
  .login-link {
    margin-top: 24px;
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
</style>
