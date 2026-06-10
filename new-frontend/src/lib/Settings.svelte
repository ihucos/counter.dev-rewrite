<script lang="ts">
  /**
   * Settings modal - manage hosts/sites, view tracking info, change password,
   * configure timezone, hide_hosts preference, delete account, and logout.
   */
  import { api, TRACKER_URL } from './api.js';
  import type { UserData, HostData } from './api.js';

  let {
    user = null,
    hosts = [] as HostData[]
  }: { user: UserData | null; hosts: HostData[] } = $props();

  let open = $state(false);
  let newSiteName = $state('');
  let addError = $state('');
  let adding = $state(false);
  let copySuccess = $state(false);

  // Password change
  let oldPwd = $state('');
  let newPwd1 = $state('');
  let newPwd2 = $state('');
  let pwdError = $state('');
  let pwdSuccess = $state('');
  let changingPwd = $state(false);

  // Timezone
  let selectedTimezone = $state(0);
  let timezoneSaved = $state(false);
  let savingTimezone = $state(false);

  // Hide hosts preference
  let hideHostsPref = $state(false);
  let hidingHostsSaving = $state(false);

  // Delete account
  let deleteMode = $state<'hidden' | 'request' | 'confirm'>('hidden');
  let deleteConfirmUsername = $state('');
  let deleteError = $state('');
  let deleting = $state(false);
  let deleteDone = $state(false);

  const TIMEZONES = [
    { offset: -12, label: '[UTC-12:00] United States Minor Outlying Islands' },
    { offset: -11, label: '[UTC-11:00] United States Minor Outlying Islands' },
    { offset: -10, label: '[UTC-10:00] Honolulu' },
    { offset: -9, label: '[UTC-09:00] Anchorage' },
    { offset: -8, label: '[UTC-08:00] Los Angeles, Vancouver, Tijuana' },
    { offset: -7, label: '[UTC-07:00] Denver, Edmonton, Ciudad Ju\u00e1rez' },
    { offset: -6, label: '[UTC-06:00] Mexico City, Chicago, Guatemala City' },
    { offset: -5, label: '[UTC-05:00] New York, Toronto, Bogot\u00e1' },
    { offset: -4, label: '[UTC-04:00] Santiago, Santo Domingo, Manaus' },
    { offset: -3, label: '[UTC-03:00] S\u00e3o Paulo, Buenos Aires, Montevideo' },
    { offset: -2, label: '[UTC-02:00] Fernando de Noronha' },
    { offset: -1, label: '[UTC-01:00] Cape Verde, Azores islands' },
    { offset: 0, label: '[UTC+00:00] London, Dublin, Lisbon' },
    { offset: 1, label: '[UTC+01:00] Berlin, Rome, Paris' },
    { offset: 2, label: '[UTC+02:00] Cairo, Johannesburg, Khartoum' },
    { offset: 3, label: '[UTC+03:00] Moscow, Istanbul, Riyadh' },
    { offset: 4, label: '[UTC+04:00] Dubai, Baku, Tbilisi' },
    { offset: 5, label: '[UTC+05:00] Karachi, Tashkent, Yekaterinburg' },
    { offset: 6, label: '[UTC+06:00] Dhaka, Almaty, Omsk' },
    { offset: 7, label: '[UTC+07:00] Jakarta, Ho Chi Minh City, Bangkok' },
    { offset: 8, label: '[UTC+08:00] Shanghai, Taipei, Kuala Lumpur' },
    { offset: 9, label: '[UTC+09:00] Tokyo, Seoul, Pyongyang, Ambon' },
    { offset: 10, label: '[UTC+10:00] Sydney, Port Moresby, Vladivostok' },
    { offset: 11, label: '[UTC+11:00] Noum\u00e9a, Magadan' },
    { offset: 12, label: '[UTC+12:00] Auckland, Suva, Petropavlovsk-Kamchatsky' },
    { offset: 13, label: '[UTC+13:00] Phoenix Islands, Samoa' },
    { offset: 14, label: '[UTC+14:00] Line Islands' },
  ];

  function flash(msg: string, type: string = 'info'): void {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message: msg, type } }));
  }

  let trackingCode = $derived.by(() => {
    if (!user) return '';
    const uuid = user.uuid || 'YOUR_UUID';
    const utcoffset = user.timezone ?? 0;
    return `<script src="${TRACKER_URL}" data-id="${uuid}" data-utcoffset="${utcoffset}"><\/script>`;
  });

  function openSettings(): void {
    selectedTimezone = user?.timezone != null ? Number(user.timezone) : 0;
    hideHostsPref = user?.hide_hosts ?? false;
    timezoneSaved = false;
    resetPasswordState();
    resetDeleteState();
    open = true;
  }

  function closeSettings(): void {
    open = false;
    copySuccess = false;
    newSiteName = '';
    addError = '';
    resetPasswordState();
    resetDeleteState();
  }

  function resetPasswordState(): void {
    oldPwd = '';
    newPwd1 = '';
    newPwd2 = '';
    pwdError = '';
    pwdSuccess = '';
    changingPwd = false;
  }

  function resetDeleteState(): void {
    deleteMode = 'hidden';
    deleteConfirmUsername = '';
    deleteError = '';
    deleting = false;
    deleteDone = false;
  }

  async function copyTrackingCode(): Promise<void> {
    const code = trackingCode;
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      copySuccess = true;
      flash('Tracking code copied!', 'success');
      setTimeout(() => copySuccess = false, 2000);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = code;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      copySuccess = true;
      flash('Tracking code copied!', 'success');
      setTimeout(() => copySuccess = false, 2000);
    }
  }

  async function addSite(): Promise<void> {
    const name = newSiteName.trim();
    if (!name) return;
    addError = '';
    adding = true;
    try {
      const host = await api.createHost({ name });
      if (host) hosts.push(host);
      newSiteName = '';
      flash(`Added "${name}"`, 'success');
    } catch (e) {
      addError = (e as Error).message || 'Failed to add.';
    } finally {
      adding = false;
    }
  }

  async function deleteHost(host: HostData): Promise<void> {
    if (!confirm(`Delete "${host.name}" permanently?`)) return;
    try {
      await api.deleteHost(host.id);
      const idx = hosts.indexOf(host);
      if (idx !== -1) hosts.splice(idx, 1);
      flash(`Deleted "${host.name}"`, 'success');
    } catch {
      flash('Failed to delete.', 'error');
    }
  }

  async function toggleHide(host: HostData): Promise<void> {
    try {
      const updated = await api.updateHost(host.id, { hide: !host.hide });
      if (updated) host.hide = updated.hide;
    } catch {
      flash('Failed to update.', 'error');
    }
  }

  async function changePassword(): Promise<void> {
    pwdError = '';
    pwdSuccess = '';
    if (!oldPwd) { pwdError = 'Current password is required.'; return; }
    if (!newPwd1) { pwdError = 'New password is required.'; return; }
    if (newPwd1.length < 6) { pwdError = 'New password must be at least 6 characters.'; return; }
    if (newPwd1 !== newPwd2) { pwdError = 'Passwords do not match.'; return; }

    changingPwd = true;
    try {
      await api.changePassword({
        old_password: oldPwd,
        new_password1: newPwd1,
        new_password2: newPwd2,
      });
      pwdSuccess = 'Password changed successfully.';
      flash('Password changed!', 'success');
      oldPwd = ''; newPwd1 = ''; newPwd2 = '';
    } catch (e) {
      pwdError = (e as Error).message || 'Failed to change password.';
    } finally {
      changingPwd = false;
    }
  }

  async function saveTimezone(): Promise<void> {
    savingTimezone = true;
    timezoneSaved = false;
    try {
      await api.updateUser({ timezone: String(selectedTimezone) });
      if (user) user.timezone = String(selectedTimezone);
      timezoneSaved = true;
      flash('Timezone saved!', 'success');
      setTimeout(() => { timezoneSaved = false; }, 2500);
    } catch (e) {
      flash('Failed to save timezone', 'error');
    } finally {
      savingTimezone = false;
    }
  }

  async function toggleHideHosts(): Promise<void> {
    const newVal = !hideHostsPref;
    hidingHostsSaving = true;
    try {
      await api.updateUser({ hide_hosts: newVal });
      if (user) user.hide_hosts = newVal;
      hideHostsPref = newVal;
      flash(`Hidden websites will ${newVal ? 'now' : 'no longer'} be filtered out.`, 'info');
    } catch (e) {
      flash('Failed to update preference', 'error');
    } finally {
      hidingHostsSaving = false;
    }
  }

  /**
   * Delete account flow:
   *   1. User clicks "Delete account" -> deleteMode = 'request'
   *   2. User types their username to confirm -> deleteMode = 'confirm'
   *   3. API call is made to delete the account
   */
  function initiateDelete(): void {
    resetDeleteState();
    deleteMode = 'request';
  }

  function confirmDelete(): void {
    if (!user) return;
    if (deleteConfirmUsername.trim() !== user.username) {
      deleteError = 'Username does not match. Please type your exact username to confirm.';
      return;
    }
    deleteError = '';
    deleteMode = 'confirm';
    performDelete();
  }

  async function performDelete(): Promise<void> {
    if (!user) return;
    deleting = true;
    deleteError = '';
    try {
      await api.deleteUser(user.username);
      deleteDone = true;
      flash('Account deleted. We\'re sorry to see you go!', 'info');
      // Redirect to home after a brief delay
      setTimeout(() => {
        window.location.href = '/';
      }, 2000);
    } catch (e) {
      deleteError = (e as Error).message || 'Failed to delete account. Please try again or contact support.';
      deleteMode = 'request';
    } finally {
      deleting = false;
    }
  }

  async function handleLogout(): Promise<void> {
    try {
      await api.logout();
    } catch { /* ignore */ }
    window.location.href = '/';
  }
</script>

<button class="icon-btn" onclick={openSettings} aria-label="Settings">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
  </svg>
</button>

{#if open}
  <div class="overlay" onclick={closeSettings} role="presentation"></div>
  <div class="modal" role="dialog" aria-label="Settings">
    <div class="header">
      <h2>Settings</h2>
      <button class="close-btn" onclick={closeSettings}>&times;</button>
    </div>
    <div class="body">
      <!-- Add site -->
      <section>
        <h3>Add Website</h3>
        <p class="desc">Add a new website to track.</p>
        <form class="inline-form" onsubmit={(e: Event) => { e.preventDefault(); addSite(); }}>
          <input type="text" bind:value={newSiteName} placeholder="e.g. example.com" disabled={adding} />
          <button type="submit" class="btn" disabled={adding || !newSiteName.trim()}>
            {adding ? 'Adding...' : 'Add'}
          </button>
        </form>
        {#if addError}<div class="error-msg">{addError}</div>{/if}
      </section>

      <!-- Tracking code -->
      <section>
        <h3>Tracking Code</h3>
        <p class="desc">Add this script to the <code>&lt;head&gt;</code> of your site:</p>
        <div class="code-row">
          <code class="code-display">{trackingCode || '<!-- Log in to see your tracking code -->'}</code>
          <button class="btn" onclick={copyTrackingCode} disabled={!trackingCode}>{copySuccess ? 'Copied!' : 'Copy Code'}</button>
        </div>
      </section>

      <!-- Hosts list -->
      <section>
        <h3>Websites</h3>
        <p class="desc">Toggle visibility or remove tracked websites.</p>
        {#each hosts as h}
          <div class="host-row">
            <span class="host-name">{h.name}</span>
            <div class="actions">
              <button class="small-btn" class:active={!h.hide} onclick={() => toggleHide(h)}>{h.hide ? 'Hidden' : 'Visible'}</button>
              <button class="small-btn danger" onclick={() => deleteHost(h)}>Delete</button>
            </div>
          </div>
        {/each}
      </section>

      <!-- Timezone -->
      <section>
        <h3>Timezone</h3>
        <p class="desc">Set your timezone for accurate tracking configuration.</p>
        <div class="timezone-row">
          <select class="select" bind:value={selectedTimezone}>
            {#each TIMEZONES as tz}
              <option value={tz.offset}>{tz.label}</option>
            {/each}
          </select>
          <button class="btn" onclick={saveTimezone} disabled={savingTimezone || selectedTimezone === Number(user?.timezone ?? 0)}>
            {savingTimezone ? 'Saving...' : timezoneSaved ? 'Saved!' : 'Save'}
          </button>
        </div>
      </section>

      <!-- Hide hosts preference -->
      <section>
        <h3>Preferences</h3>
        <p class="desc">Customize your dashboard experience.</p>
        <label class="toggle-row">
          <span class="toggle-label">
            Hide inactive websites
            <span class="toggle-hint">When enabled, hidden websites won't appear in the dashboard site selector.</span>
          </span>
          <button
            class="toggle-switch"
            class:active={hideHostsPref}
            onclick={toggleHideHosts}
            disabled={hidingHostsSaving}
            role="switch"
            aria-checked={hideHostsPref}
          >
            <span class="toggle-knob"></span>
          </button>
        </label>
      </section>

      <!-- Change password -->
      <section>
        <h3>Change Password</h3>
        <p class="desc">Update your account password.</p>
        {#if pwdError}<div class="error-msg">{pwdError}</div>{/if}
        {#if pwdSuccess}<div class="success-msg">{pwdSuccess}</div>{/if}
        <div class="pwd-form">
          <input type="password" bind:value={oldPwd} placeholder="Current password" disabled={changingPwd} />
          <input type="password" bind:value={newPwd1} placeholder="New password (min. 6 chars)" disabled={changingPwd} />
          <input type="password" bind:value={newPwd2} placeholder="Confirm new password" disabled={changingPwd} />
          <button class="btn" onclick={changePassword} disabled={changingPwd || !oldPwd || !newPwd1 || !newPwd2}>
            {changingPwd ? 'Changing...' : 'Change Password'}
          </button>
        </div>
      </section>

      <!-- Account info + Delete account -->
      {#if user}
        <section>
          <h3>Account</h3>
          <div class="user-info">
            <div><strong>Username:</strong> {user.username}</div>
            <div><strong>Email:</strong> {user.email || '(not set)'}</div>
            {#if user.uuid}
              <div><strong>Tracking ID:</strong> <code class="uuid-text">{user.uuid}</code></div>
            {/if}
          </div>

          <!-- Delete account -->
          {#if !deleteDone}
            <div class="delete-section">
              <h4 class="delete-title">Delete Account</h4>
              <div class="danger-box">
                {#if deleteMode === 'hidden'}
                  <div class="delete-prompt">
                    <div class="danger-message">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="alert-icon">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                        <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                      </svg>
                      <span>Deleting your account removes all data you've collected!</span>
                    </div>
                    <button class="btn-danger" onclick={initiateDelete}>Delete account</button>
                  </div>
                {:else if deleteMode === 'request'}
                  <div class="delete-confirm-form">
                    {#if deleteError}
                      <div class="error-msg">{deleteError}</div>
                    {/if}
                    <div class="confirm-row">
                      <input
                        type="text"
                        bind:value={deleteConfirmUsername}
                        placeholder="Type your username ({user.username}) to confirm"
                        disabled={deleting}
                        class="confirm-input"
                      />
                      <button
                        class="btn-danger"
                        onclick={confirmDelete}
                        disabled={deleting || !deleteConfirmUsername.trim()}
                      >
                        {deleting ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
                    <button class="btn-cancel" onclick={resetDeleteState}>Cancel</button>
                  </div>
                {:else if deleteMode === 'confirm' && deleting}
                  <div class="delete-progress">
                    <div class="spinner-small"></div>
                    <span>Deleting your account...</span>
                  </div>
                {/if}
              </div>
            </div>
          {:else}
            <div class="delete-success">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <span>Account deleted. Redirecting...</span>
            </div>
          {/if}

          <button class="btn-logout" onclick={handleLogout}>Sign Out</button>
        </section>
      {/if}
    </div>
  </div>
{/if}

<style>
  .icon-btn {
    background: none; border: 1px solid #e0e0e0; padding: 8px;
    border-radius: 8px; cursor: pointer; color: #666; display: flex;
    align-items: center; line-height: 0;
  }
  .icon-btn:hover { background: #f5f5f5; }
  .overlay {
    position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 999;
  }
  .modal {
    position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
    background: white; border-radius: 16px; width: 90%; max-width: 520px;
    max-height: 85vh; overflow-y: auto; z-index: 1000;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  }
  .header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 20px 24px 0;
  }
  .header h2 { margin: 0; font-size: 20px; }
  .close-btn {
    background: none; border: none; font-size: 28px; cursor: pointer;
    color: #888; padding: 0; line-height: 1;
  }
  .close-btn:hover { color: #333; }
  .body { padding: 16px 24px 24px; }
  section { margin-top: 20px; }
  section:first-child { margin-top: 0; }
  section h3 { margin: 0 0 4px; font-size: 15px; color: #333; }
  .desc { font-size: 13px; color: #888; margin-bottom: 8px; }
  .desc code { background: #f3f4f6; padding: 1px 4px; border-radius: 3px; font-size: 12px; }
  .inline-form { display: flex; gap: 8px; }
  input, .select {
    flex: 1; padding: 10px 12px; border: 1px solid #ddd;
    border-radius: 8px; font-size: 14px;
  }
  input:focus, .select:focus { outline: none; border-color: #4361ee; box-shadow: 0 0 0 3px rgba(67,97,238,0.15); }
  .select { background: white; cursor: pointer; }
  .btn {
    background: #4361ee; color: white; border: none; padding: 10px 20px;
    border-radius: 8px; font-size: 14px; cursor: pointer; font-weight: 600;
    white-space: nowrap;
  }
  .btn:hover { background: #3651d9; }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .code-row { display: flex; gap: 8px; align-items: flex-start; }
  .code-display {
    flex: 1; padding: 10px 12px; background: #f9fafb; border: 1px solid #eee;
    border-radius: 8px; font-size: 12px; font-family: monospace;
    word-break: break-all; color: #333; line-height: 1.5;
  }
  .host-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 12px; background: #f9fafb; border-radius: 8px;
    border: 1px solid #eee; margin-bottom: 6px; font-size: 14px;
  }
  .host-name { font-weight: 500; color: #333; }
  .actions { display: flex; gap: 6px; }
  .small-btn {
    padding: 4px 10px; border-radius: 6px; font-size: 12px;
    border: 1px solid #ddd; background: white; cursor: pointer;
  }
  .small-btn:hover { background: #f5f5f5; }
  .small-btn.active { background: #d1fae5; color: #065f46; border-color: #a7f3d0; }
  .small-btn.danger { color: #c0392b; border-color: #f5c6cb; }
  .small-btn.danger:hover { background: #fee; }
  .timezone-row { display: flex; gap: 8px; align-items: flex-start; }
  .pwd-form { display: flex; flex-direction: column; gap: 8px; }
  .error-msg {
    padding: 8px 12px; background: #fee; color: #c0392b;
    border-radius: 8px; font-size: 13px; margin-bottom: 8px;
  }
  .success-msg {
    padding: 8px 12px; background: #d4edda; color: #155724;
    border-radius: 8px; font-size: 13px; margin-bottom: 8px;
  }
  .user-info {
    font-size: 14px; color: #555; line-height: 1.8; margin-bottom: 12px;
  }
  .user-info strong { color: #333; }
  .uuid-text {
    font-size: 12px; background: #f3f4f6; padding: 2px 6px;
    border-radius: 4px; color: #666;
  }
  .toggle-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 14px; background: #f9fafb; border-radius: 8px;
    border: 1px solid #eee; cursor: pointer;
  }
  .toggle-label {
    display: flex; flex-direction: column; gap: 2px;
    font-size: 14px; font-weight: 500; color: #333;
  }
  .toggle-hint { font-size: 12px; font-weight: 400; color: #888; }
  .toggle-switch {
    position: relative; width: 44px; height: 24px;
    background: #d1d5db; border: none; border-radius: 12px;
    cursor: pointer; transition: background 0.2s;
    flex-shrink: 0; padding: 0;
  }
  .toggle-switch.active { background: #4361ee; }
  .toggle-switch:disabled { opacity: 0.5; cursor: not-allowed; }
  .toggle-knob {
    position: absolute; top: 2px; left: 2px; width: 20px; height: 20px;
    background: white; border-radius: 50%; transition: transform 0.2s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }
  .toggle-switch.active .toggle-knob { transform: translateX(20px); }
  .btn-logout {
    background: none; border: 1px solid #e5e7eb; padding: 8px 20px;
    border-radius: 8px; cursor: pointer; font-size: 14px; color: #dc2626;
    margin-top: 16px;
  }
  .btn-logout:hover { background: #fef2f2; border-color: #fca5a5; }

  /* Delete account styles */
  .delete-section { margin-top: 16px; }
  .delete-title {
    font-size: 13px; font-weight: 700; color: #dc2626;
    margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.5px;
  }
  .danger-box {
    background: linear-gradient(135deg, #fef2f2 0%, #fef2f2 100%);
    border: 1px solid #fecaca;
    border-radius: 12px;
    padding: 16px;
  }
  .delete-prompt { display: flex; flex-direction: column; gap: 12px; }
  .danger-message {
    display: flex; align-items: center; gap: 10px;
    font-size: 13px; color: #991b1b; line-height: 1.5;
  }
  .alert-icon { width: 20px; height: 20px; flex-shrink: 0; color: #dc2626; }
  .btn-danger {
    background: #dc2626; color: white; border: none;
    padding: 8px 20px; border-radius: 8px; font-size: 14px;
    font-weight: 600; cursor: pointer; align-self: flex-start;
    transition: background 0.15s;
  }
  .btn-danger:hover { background: #b91c1c; }
  .btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
  .delete-confirm-form { display: flex; flex-direction: column; gap: 8px; }
  .confirm-row { display: flex; gap: 8px; align-items: stretch; }
  .confirm-input {
    flex: 1; padding: 8px 12px; border: 1px solid #fecaca;
    border-radius: 8px; font-size: 13px; background: white;
  }
  .confirm-input:focus {
    outline: none; border-color: #dc2626; box-shadow: 0 0 0 3px rgba(220,38,38,0.15);
  }
  .btn-cancel {
    background: none; border: 1px solid #ddd; padding: 6px 14px;
    border-radius: 6px; font-size: 12px; cursor: pointer; color: #666;
    align-self: flex-start;
  }
  .btn-cancel:hover { background: #f5f5f5; }
  .delete-progress {
    display: flex; align-items: center; gap: 10px;
    font-size: 13px; color: #991b1b;
  }
  .spinner-small {
    width: 16px; height: 16px; border: 2px solid #fecaca;
    border-top-color: #dc2626; border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .delete-success {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 12px; background: #d4edda; color: #155724;
    border-radius: 8px; font-size: 13px; margin-top: 8px;
  }
</style>
