<script>
  import { api, TRACKER_URL } from '$lib/api.js';

  let { hosts, selectedHostName, user, onauthChanged } = $props();

  let showSettings = $state(false);

  let hostForTracking = $state(null);
  let trackingCode = $derived.by(() => {
    if (!user || !hostForTracking) return '';
    const uuid = user.uuid;
    const utcoffset = user.timezone ?? 0;
    return `<script src="${TRACKER_URL}" data-id="${uuid}" data-utcoffset="${utcoffset}"><\/script>`;
  });
  let copySuccess = $state(false);

  let newSiteName = $state('');
  let addSiteError = $state('');
  let addingSite = $state(false);

  // Password change state
  let currentPassword = $state('');
  let newPassword = $state('');
  let repeatNewPassword = $state('');
  let passwordError = $state('');
  let passwordSuccess = $state('');
  let changingPassword = $state(false);

  // Timezone editing state
  let selectedTimezone = $state(0);
  let timezoneSaved = $state(false);
  let savingTimezone = $state(false);

  // Hide hosts preference state
  let hideHostsPref = $state(false);
  let hidingHostsSaving = $state(false);

  const TIMEZONES = [
    { offset: -12, label: '[UTC-12:00] United States Minor Outlying Islands' },
    { offset: -11, label: '[UTC-11:00] United States Minor Outlying Islands' },
    { offset: -10, label: '[UTC-10:00] Honolulu' },
    { offset: -9, label: '[UTC-09:00] Anchorage' },
    { offset: -8, label: '[UTC-08:00] Los Angeles, Vancouver, Tijuana' },
    { offset: -7, label: '[UTC-07:00] Denver, Edmonton, Ciudad Juárez' },
    { offset: -6, label: '[UTC-06:00] Mexico City, Chicago, Guatemala City' },
    { offset: -5, label: '[UTC-05:00] New York, Toronto, Bogotá' },
    { offset: -4, label: '[UTC-04:00] Santiago, Santo Domingo, Manaus' },
    { offset: -3, label: '[UTC-03:00] São Paulo, Buenos Aires, Montevideo' },
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
    { offset: 11, label: '[UTC+11:00] Nouméa, Magadan' },
    { offset: 12, label: '[UTC+12:00] Auckland, Suva, Petropavlovsk-Kamchatsky' },
    { offset: 13, label: '[UTC+13:00] Phoenix Islands, Samoa' },
    { offset: 14, label: '[UTC+14:00] Line Islands' },
  ];

  function openSettings(hostName) {
    hostForTracking = hostName;
    selectedTimezone = user?.timezone ?? 0;
    hideHostsPref = user?.hide_hosts ?? false;
    resetPasswordState();
    timezoneSaved = false;
    showSettings = true;
  }

  function closeSettings() {
    showSettings = false;
    hostForTracking = null;
    copySuccess = false;
    newSiteName = '';
    addSiteError = '';
    resetPasswordState();
  }

  function resetPasswordState() {
    currentPassword = '';
    newPassword = '';
    repeatNewPassword = '';
    passwordError = '';
    passwordSuccess = '';
    changingPassword = false;
  }

  async function copyTrackingCode() {
    try {
      await navigator.clipboard.writeText(trackingCode);
      copySuccess = true;
      setTimeout(() => { copySuccess = false; }, 2000);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = trackingCode;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      copySuccess = true;
      setTimeout(() => { copySuccess = false; }, 2000);
    }
  }

  async function toggleHostVisibility(host) {
    try {
      await api.updateHost(host.id, { hide: !host.hide });
      host.hide = !host.hide;
    } catch (e) {
      console.error('Failed to update host visibility', e);
    }
  }

  async function handleAddSite() {
    const trimmed = newSiteName.trim();
    if (!trimmed) return;
    addSiteError = '';
    addingSite = true;
    try {
      const newHost = await api.createHost(trimmed);
      hosts.push(newHost);
      hostForTracking = newHost.name;
      newSiteName = '';
    } catch (e) {
      addSiteError = e.message || 'Failed to add website';
    } finally {
      addingSite = false;
    }
  }

  async function handleDeleteHost(host) {
    if (!confirm(`Delete "${host.name}"? This will permanently remove all tracking data.`)) {
      return;
    }
    try {
      await api.deleteHost(host.id);
      const idx = hosts.indexOf(host);
      if (idx !== -1) hosts.splice(idx, 1);
      if (hostForTracking === host.name) {
        hostForTracking = hosts.length > 0 ? hosts[0].name : null;
      }
    } catch (e) {
      console.error('Failed to delete host', e);
    }
  }

  async function handleChangePassword() {
    passwordError = '';
    passwordSuccess = '';

    if (!currentPassword) {
      passwordError = 'Current password is required.';
      return;
    }
    if (!newPassword) {
      passwordError = 'New password is required.';
      return;
    }
    if (newPassword.length < 6) {
      passwordError = 'New password must be at least 6 characters.';
      return;
    }
    if (newPassword !== repeatNewPassword) {
      passwordError = 'New passwords do not match.';
      return;
    }

    changingPassword = true;
    try {
      await api.changePassword({
        old_password: currentPassword,
        new_password1: newPassword,
        new_password2: repeatNewPassword,
      });
      passwordSuccess = 'Password changed successfully.';
      currentPassword = '';
      newPassword = '';
      repeatNewPassword = '';
    } catch (e) {
      passwordError = e.message || 'Failed to change password.';
    } finally {
      changingPassword = false;
    }
  }

  async function handleSaveTimezone() {
    savingTimezone = true;
    timezoneSaved = false;
    try {
      const updated = await api.updateUser({ timezone: selectedTimezone });
      if (user) {
        user.timezone = updated.timezone ?? selectedTimezone;
      }
      timezoneSaved = true;
      setTimeout(() => { timezoneSaved = false; }, 2500);
    } catch (e) {
      console.error('Failed to save timezone', e);
    } finally {
      savingTimezone = false;
    }
  }

  async function handleToggleHideHosts() {
    const newValue = !hideHostsPref;
    hidingHostsSaving = true;
    try {
      const updated = await api.updateUser({ hide_hosts: newValue });
      if (user) {
        user.hide_hosts = updated.hide_hosts ?? newValue;
      }
      hideHostsPref = user?.hide_hosts ?? newValue;
    } catch (e) {
      console.error('Failed to update hide_hosts preference', e);
    } finally {
      hidingHostsSaving = false;
    }
  }

  async function handleLogout() {
    try {
      await api.logout();
      onauthChanged({ authenticated: false });
    } catch (e) {
      console.error('Logout failed', e);
    }
  }
</script>
<button
  class="btn-icon"
  onclick={() => openSettings(selectedHostName)}
  aria-label="Settings"
  disabled={!selectedHostName}
>
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="currentColor" stroke-width="2"/>
  </svg>
</button>

{#if showSettings}
  <div class="overlay" onclick={closeSettings} role="presentation"></div>

  <div class="settings-modal" role="dialog" aria-label="Settings">
    <div class="modal-header">
      <h2>Settings</h2>
      <button class="btn-close" onclick={closeSettings} aria-label="Close">&times;</button>
    </div>
    <div class="modal-body">
      <div class="section">
        <h3>Add Website</h3>
        <p class="section-desc">Add a new website to track.</p>
        <form class="add-site-form" onsubmit={(e) => { e.preventDefault(); handleAddSite(); }}>
          <input
            type="text"
            bind:value={newSiteName}
            placeholder="e.g. example.com"
            class="add-site-input"
            disabled={addingSite}
          />
          <button type="submit" class="btn-primary-sm" disabled={addingSite || !newSiteName.trim()}>
            {addingSite ? 'Adding...' : 'Add'}
          </button>
        </form>
        {#if addSiteError}
          <div class="add-site-error">{addSiteError}</div>
        {/if}
      </div>

      {#if hostForTracking}
      <div class="section">
        <h3>Tracking Code</h3>
        <p class="section-desc">
          Add this script to the <code>&lt;head&gt;</code> section of <strong>{hostForTracking}</strong>.
        </p>
        <div class="tracking-code-box">
          <input
            type="text"
            class="code-input"
            value={trackingCode}
            readonly
            onclick={(e) => e.target.select()}
          />
          <button class="btn-copy" onclick={copyTrackingCode}>
            {copySuccess ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>
      {/if}

      <div class="section">
        <h3>Websites</h3>
        <p class="section-desc">Toggle visibility or remove tracked websites.</p>
        <div class="hosts-list">
          {#each hosts as host (host.id)}
            <div class="host-row">
              <span class="host-name">{host.name}</span>
              <div class="host-actions">
                <button
                  class="toggle-btn"
                  class:visible={!host.hide}
                  class:hidden={host.hide}
                  onclick={() => toggleHostVisibility(host)}
                  aria-label="{host.hide ? 'Show' : 'Hide'} {host.name}"
                >
                  {host.hide ? 'Hidden' : 'Visible'}
                </button>
                <button
                  class="btn-delete"
                  onclick={() => handleDeleteHost(host)}
                  aria-label="Delete {host.name}"
                  title="Delete this website and all its data"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  </svg>
                </button>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <div class="section">
        <h3>Timezone</h3>
        <p class="section-desc">Set your timezone for accurate tracking code configuration.</p>
        <div class="timezone-form">
          <select class="timezone-select" bind:value={selectedTimezone}>
            {#each TIMEZONES as tz}
              <option value={tz.offset}>{tz.label}</option>
            {/each}
          </select>
          <button
            class="btn-primary-sm"
            onclick={handleSaveTimezone}
            disabled={savingTimezone || selectedTimezone === (user?.timezone ?? 0)}
          >
            {savingTimezone ? 'Saving...' : timezoneSaved ? 'Saved!' : 'Save'}
          </button>
        </div>
      </div>

      <div class="section">
        <h3>Preferences</h3>
        <p class="section-desc">Customize your dashboard experience.</p>
        <label class="toggle-row">
          <span class="toggle-label">
            Hide inactive websites
            <span class="toggle-hint">When enabled, hidden websites won't appear in the dashboard site selector.</span>
          </span>
          <button
            class="toggle-switch"
            class:active={hideHostsPref}
            onclick={handleToggleHideHosts}
            disabled={hidingHostsSaving}
            aria-label="Toggle hide inactive websites"
            role="switch"
            aria-checked={hideHostsPref}
          >
            <span class="toggle-knob"></span>
          </button>
        </label>
      </div>

      <div class="section">
        <h3>Change Password</h3>
        <p class="section-desc">Update your account password.</p>
        <form class="password-form" onsubmit={(e) => { e.preventDefault(); handleChangePassword(); }}>
          {#if passwordError}
            <div class="form-error">{passwordError}</div>
          {/if}
          {#if passwordSuccess}
            <div class="form-success">{passwordSuccess}</div>
          {/if}
          <label class="form-label">
            Current Password
            <input
              type="password"
              bind:value={currentPassword}
              placeholder="Current password"
              class="form-input"
              disabled={changingPassword}
            />
          </label>
          <label class="form-label">
            New Password
            <input
              type="password"
              bind:value={newPassword}
              placeholder="New password (min. 6 characters)"
              class="form-input"
              disabled={changingPassword}
            />
          </label>
          <label class="form-label">
            Repeat New Password
            <input
              type="password"
              bind:value={repeatNewPassword}
              placeholder="Repeat new password"
              class="form-input"
              disabled={changingPassword}
            />
          </label>
          <button type="submit" class="btn-primary-sm" disabled={changingPassword || !currentPassword || !newPassword || !repeatNewPassword}>
            {changingPassword ? 'Changing...' : 'Change Password'}
          </button>
        </form>
      </div>

      <div class="section">
        <h3>Account</h3>
        {#if user}
          <div class="user-info">
            <span class="user-detail"><strong>Username:</strong> {user.username}</span>
            <span class="user-detail"><strong>Email:</strong> {user.email}</span>
            {#if user.uuid}
              <span class="user-detail"><strong>Tracking ID:</strong> {user.uuid}</span>
            {/if}
          </div>
        {/if}
        <button class="btn-logout" onclick={handleLogout}>Sign out</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .btn-icon {
    background: none;
    border: 1px solid #e5e7eb;
    padding: 8px;
    border-radius: 6px;
    cursor: pointer;
    color: #666;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 0;
  }
  .btn-icon:hover:not(:disabled) {
    background: #f9fafb;
    color: #333;
  }
  .btn-icon:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.4);
    z-index: 999;
  }

  .settings-modal {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    border-radius: 12px;
    width: 90%;
    max-width: 520px;
    max-height: 85vh;
    overflow-y: auto;
    z-index: 1000;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px 0;
  }
  .modal-header h2 {
    margin: 0;
    font-size: 20px;
    font-family: 'Nunito Sans', sans-serif;
  }
  .btn-close {
    background: none;
    border: none;
    font-size: 28px;
    cursor: pointer;
    color: #888;
    padding: 0;
    line-height: 1;
  }
  .btn-close:hover {
    color: #333;
  }

  .modal-body {
    padding: 16px 24px 24px;
  }

  .section {
    margin-top: 20px;
  }
  .section:first-child {
    margin-top: 0;
  }
  .section h3 {
    margin: 0 0 4px;
    font-size: 16px;
    font-family: 'Nunito Sans', sans-serif;
    color: #333;
  }
  .section-desc {
    margin: 0 0 12px;
    font-size: 13px;
    color: #888;
  }
  .section-desc code {
    background: #f3f4f6;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 12px;
  }

  .add-site-form {
    display: flex;
    gap: 8px;
  }
  .add-site-input {
    flex: 1;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 14px;
  }
  .add-site-input:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.2);
  }
  .btn-primary-sm {
    background: #2563eb;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-size: 14px;
    cursor: pointer;
    white-space: nowrap;
    font-weight: 600;
  }
  .btn-primary-sm:hover {
    background: #1d4ed8;
  }
  .btn-primary-sm:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .add-site-error {
    margin-top: 8px;
    padding: 8px 12px;
    background: #fef2f2;
    color: #dc2626;
    border-radius: 6px;
    font-size: 13px;
  }

  .tracking-code-box {
    display: flex;
    gap: 8px;
  }
  .code-input {
    flex: 1;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 13px;
    font-family: monospace;
    background: #f9fafb;
    color: #333;
  }
  .code-input:focus {
    outline: none;
    border-color: #2563eb;
  }
  .btn-copy {
    background: #2563eb;
    color: white;
    border: none;
    padding: 10px 18px;
    border-radius: 6px;
    font-size: 14px;
    cursor: pointer;
    white-space: nowrap;
  }
  .btn-copy:hover {
    background: #1d4ed8;
  }

  .hosts-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .host-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    background: #f9fafb;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
  }
  .host-name {
    font-size: 14px;
    font-weight: 500;
    color: #333;
  }
  .host-actions {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .toggle-btn {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    border: none;
    cursor: pointer;
    transition: all 0.15s;
  }
  .toggle-btn.visible {
    background: #d1fae5;
    color: #065f46;
  }
  .toggle-btn.hidden {
    background: #f3f4f6;
    color: #6b7280;
  }
  .toggle-btn:hover {
    opacity: 0.8;
  }
  .btn-delete {
    background: none;
    border: 1px solid transparent;
    padding: 4px;
    border-radius: 4px;
    cursor: pointer;
    color: #9ca3af;
    display: flex;
    align-items: center;
    line-height: 0;
    transition: all 0.15s;
  }
  .btn-delete:hover {
    color: #dc2626;
    background: #fef2f2;
    border-color: #fca5a5;
  }

  .timezone-form {
    display: flex;
    gap: 8px;
    align-items: flex-start;
  }
  .timezone-select {
    flex: 1;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 14px;
    background: white;
    color: #333;
    cursor: pointer;
  }
  .timezone-select:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.2);
  }

  .toggle-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 14px;
    background: #f9fafb;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    cursor: pointer;
  }
  .toggle-label {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 14px;
    font-weight: 500;
    color: #333;
  }
  .toggle-hint {
    font-size: 12px;
    font-weight: 400;
    color: #888;
  }
  .toggle-switch {
    position: relative;
    width: 44px;
    height: 24px;
    background: #d1d5db;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    transition: background 0.2s;
    flex-shrink: 0;
    padding: 0;
  }
  .toggle-switch.active {
    background: #2563eb;
  }
  .toggle-switch:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .toggle-knob {
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    transition: transform 0.2s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }
  .toggle-switch.active .toggle-knob {
    transform: translateX(20px);
  }

  .password-form {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .form-label {
    display: block;
    font-size: 13px;
    color: #666;
  }
  .form-input {
    display: block;
    width: 100%;
    padding: 10px 12px;
    margin-top: 4px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 14px;
    box-sizing: border-box;
  }
  .form-input:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.2);
  }
  .form-error {
    padding: 8px 12px;
    background: #fef2f2;
    color: #dc2626;
    border-radius: 6px;
    font-size: 13px;
  }
  .form-success {
    padding: 8px 12px;
    background: #d1fae5;
    color: #065f46;
    border-radius: 6px;
    font-size: 13px;
  }

  .user-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 12px;
    font-size: 14px;
    color: #555;
  }
  .user-detail strong {
    color: #333;
  }

  .btn-logout {
    background: none;
    border: 1px solid #e5e7eb;
    padding: 8px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    color: #dc2626;
  }
  .btn-logout:hover {
    background: #fef2f2;
    border-color: #fca5a5;
  }
</style>
