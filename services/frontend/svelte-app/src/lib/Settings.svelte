<script>
  import { api } from '$lib/api.js';

  let { hosts, selectedHostName, user } = $props();

  /** Emit auth change (logout) */
  let emit = $emit();

  let showSettings = $state(false);

  // Tracking code display
  let hostForTracking = $state(null);
  let trackingCode = $derived.by(() => {
    if (!user || !hostForTracking) return '';
    const uuid = user.uuid;
    const utcoffset = user.timezone ?? 0;
    return `<script src="https://cdn.counter.dev/script.js" data-id="${uuid}" data-utcoffset="${utcoffset}"><\/script>`;
  });
  let copySuccess = $state(false);

  function openSettings(hostName) {
    hostForTracking = hostName;
    showSettings = true;
  }

  function closeSettings() {
    showSettings = false;
    hostForTracking = null;
    copySuccess = false;
  }

  async function copyTrackingCode() {
    try {
      await navigator.clipboard.writeText(trackingCode);
      copySuccess = true;
      setTimeout(() => { copySuccess = false; }, 2000);
    } catch {
      // Fallback
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

  async function handleLogout() {
    try {
      await api.logout();
      emit('authChanged', { authenticated: false });
    } catch (e) {
      console.error('Logout failed', e);
    }
  }
</script>

<!-- Settings button -->
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
  <!-- Overlay -->
  <div class="overlay" onclick={closeSettings} role="presentation"></div>

  <!-- Modal -->
  <div class="settings-modal" role="dialog" aria-label="Settings">
    <div class="modal-header">
      <h2>Settings</h2>
      <button class="btn-close" onclick={closeSettings} aria-label="Close">&times;</button>
    </div>
    <div class="modal-body">
      <!-- Tracking Code Section -->
      <div class="section">
        <h3>Tracking Code</h3>
        <p class="section-desc">
          Add this script to the <code>&lt;head&gt;</code> section of your website.
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

      <!-- Hosts Section -->
      <div class="section">
        <h3>Websites</h3>
        <p class="section-desc">Toggle visibility of your tracked websites.</p>
        <div class="hosts-list">
          {#each hosts as host (host.id)}
            <div class="host-row">
              <span class="host-name">{host.name}</span>
              <button
                class="toggle-btn"
                class:visible={!host.hide}
                class:hidden={host.hide}
                onclick={() => toggleHostVisibility(host)}
                aria-label="{host.hide ? 'Show' : 'Hide'} {host.name}"
              >
                {host.hide ? 'Hidden' : 'Visible'}
              </button>
            </div>
          {/each}
        </div>
      </div>

      <!-- Account Section -->
      <div class="section">
        <h3>Account</h3>
        {#if user}
          <div class="user-info">
            <span class="user-detail"><strong>Username:</strong> {user.username}</span>
            <span class="user-detail"><strong>Email:</strong> {user.email}</span>
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
