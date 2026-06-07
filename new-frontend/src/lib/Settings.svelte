<script lang="ts">
  /**
   * Settings modal - manage hosts/sites, view tracking info, change password.
   */
  import { api } from './api.js';
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

  function flash(msg: string, type: string = 'info'): void {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message: msg, type } }));
  }

  async function copyTrackingCode(): Promise<void> {
    const uuid = user?.uuid || 'YOUR_UUID';
    const code = `<script src="https://cdn.counter.dev/script.js" data-id="${uuid}" data-utcoffset="${user?.timezone ?? 0}"><\/script>`;
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
    if (!oldPwd || !newPwd1 || newPwd1 !== newPwd2) {
      pwdError = 'Check your inputs.';
      return;
    }
    changingPwd = true;
    try {
      await api.changePassword({
        old_password: oldPwd,
        new_password1: newPwd1,
        new_password2: newPwd2,
      });
      pwdSuccess = 'Password changed!';
      flash('Password changed!', 'success');
      oldPwd = ''; newPwd1 = ''; newPwd2 = '';
    } catch (e) {
      pwdError = (e as Error).message || 'Failed.';
    } finally {
      changingPwd = false;
    }
  }
</script>

<button class="icon-btn" onclick={() => open = true} aria-label="Settings">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
  </svg>
</button>

{#if open}
  <div class="overlay" onclick={() => open = false}></div>
  <div class="modal">
    <div class="header">
      <h2>Settings</h2>
      <button class="close-btn" onclick={() => open = false}>×</button>
    </div>
    <div class="body">
      <!-- Add site -->
      <section>
        <h3>Add Website</h3>
        <form class="inline-form" onsubmit={(e: Event) => { e.preventDefault(); addSite(); }}>
          <input type="text" bind:value={newSiteName} placeholder="e.g. example.com" disabled={adding} />
          <button type="submit" class="btn" disabled={adding || !newSiteName.trim()}>
            {adding ? '...' : 'Add'}
          </button>
        </form>
        {#if addError}<div class="error-msg">{addError}</div>{/if}
      </section>

      <!-- Tracking code -->
      <section>
        <h3>Tracking Code</h3>
        <p class="desc">Add this to your site's &lt;head&gt;:</p>
        <button class="btn" onclick={copyTrackingCode}>{copySuccess ? 'Copied!' : 'Copy Code'}</button>
      </section>

      <!-- Hosts list -->
      <section>
        <h3>Websites</h3>
        {#each hosts as h}
          <div class="host-row">
            <span>{h.name}</span>
            <div class="actions">
              <button class="small-btn" onclick={() => toggleHide(h)}>{h.hide ? 'Show' : 'Hide'}</button>
              <button class="small-btn danger" onclick={() => deleteHost(h)}>Delete</button>
            </div>
          </div>
        {/each}
      </section>

      <!-- Change password -->
      <section>
        <h3>Change Password</h3>
        {#if pwdError}<div class="error-msg">{pwdError}</div>{/if}
        {#if pwdSuccess}<div class="success-msg">{pwdSuccess}</div>{/if}
        <div class="pwd-form">
          <input type="password" bind:value={oldPwd} placeholder="Current password" disabled={changingPwd} />
          <input type="password" bind:value={newPwd1} placeholder="New password" disabled={changingPwd} />
          <input type="password" bind:value={newPwd2} placeholder="Confirm new password" disabled={changingPwd} />
          <button class="btn" onclick={changePassword} disabled={changingPwd || !oldPwd || !newPwd1 || !newPwd2}>
            {changingPwd ? 'Changing...' : 'Change Password'}
          </button>
        </div>
      </section>

      <!-- User info -->
      {#if user}
        <section>
          <h3>Account</h3>
          <div class="user-info">
            <div>Username: {user.username}</div>
            <div>Email: {user.email}</div>
          </div>
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
    background: white; border-radius: 16px; width: 90%; max-width: 480px;
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
  section h3 { margin: 0 0 8px; font-size: 15px; color: #333; }
  .desc { font-size: 13px; color: #888; margin-bottom: 8px; }
  .inline-form { display: flex; gap: 8px; }
  input {
    flex: 1; padding: 10px 12px; border: 1px solid #ddd;
    border-radius: 8px; font-size: 14px;
  }
  input:focus { outline: none; border-color: #4361ee; box-shadow: 0 0 0 3px rgba(67,97,238,0.15); }
  .btn {
    background: #4361ee; color: white; border: none; padding: 10px 20px;
    border-radius: 8px; font-size: 14px; cursor: pointer; font-weight: 600;
  }
  .btn:hover { background: #3651d9; }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .host-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 12px; background: #f9fafb; border-radius: 8px;
    border: 1px solid #eee; margin-bottom: 6px; font-size: 14px;
  }
  .actions { display: flex; gap: 6px; }
  .small-btn {
    padding: 4px 10px; border-radius: 6px; font-size: 12px;
    border: 1px solid #ddd; background: white; cursor: pointer;
  }
  .small-btn:hover { background: #f5f5f5; }
  .small-btn.danger { color: #c0392b; border-color: #f5c6cb; }
  .small-btn.danger:hover { background: #fee; }
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
    font-size: 14px; color: #555; line-height: 1.8;
  }
</style>
