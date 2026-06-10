<script lang="ts">
  import { goto } from '$app/navigation';
  import { api, TRACKER_URL } from '$lib/api.js';
  import type { UserData, HostData } from '$lib/api.js';

  let user = $state<UserData | null>(null);
  let hosts = $state<HostData[]>([]);
  let loading = $state(true);
  let copySuccess = $state(false);

  /** Polling for first visit detection */
  let firstVisitLoading = $state(false);
  let firstVisitDetected = $state(false);
  let firstVisitError = $state('');
  let pollTimer: ReturnType<typeof setInterval> | null = null;
  let dashboardNavigating = $state(false);

  function flash(msg: string, type: string = 'info'): void {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message: msg, type } }));
  }

  function getUTCOffset(): number {
    return Math.round((-1 * new Date().getTimezoneOffset()) / 60);
  }

  function getTrackingCode(): string {
    if (!user) return '';
    const uuid = user.uuid;
    const utcoffset = user.timezone != null ? Number(user.timezone) : getUTCOffset();
    return `<script src="${TRACKER_URL}" data-id="${uuid}" data-utcoffset="${utcoffset}"><\/script>`;
  }

  async function copyCode(): Promise<void> {
    const code = getTrackingCode();
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      copySuccess = true;
      flash('Tracking code copied!', 'success');
      setTimeout(() => { copySuccess = false; }, 2000);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = code;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      copySuccess = true;
      flash('Tracking code copied!', 'success');
      setTimeout(() => { copySuccess = false; }, 2000);
    }
  }

  /**
   * Poll the query endpoint for the first host to detect
   * when the first visit arrives. Polls every 5 seconds,
   * stops when data is found or navigates away.
   */
  function startPolling(): void {
    if (hosts.length === 0) return;
    if (pollTimer) return;

    const hostName = hosts[0].name;

    // Immediate check
    pollOnce(hostName);

    pollTimer = setInterval(() => {
      pollOnce(hostName);
    }, 5000);
  }

  async function pollOnce(hostName: string): Promise<void> {
    firstVisitLoading = true;
    firstVisitError = '';

    try {
      // Query recent data (last 7 days) to see if any visits arrived
      const data = await api.query(hostName, undefined, undefined);

      if (data) {
        // Check if we have any data at all
        const hasData = Object.values(data).some((category) => {
          return category && typeof category === 'object' && Object.keys(category).length > 0;
        });

        if (hasData) {
          // First visit detected! Navigate to dashboard
          firstVisitDetected = true;
          flash('First visit detected! Redirecting to dashboard...', 'success');
          stopPolling();
          dashboardNavigating = true;

          setTimeout(() => {
            goto('/dashboard');
          }, 1200);
        }
      }
    } catch (e) {
      firstVisitError = (e as Error).message || 'Poll failed';
      // Don't stop polling on transient errors
    } finally {
      firstVisitLoading = false;
    }
  }

  function stopPolling(): void {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function goToDashboard(): void {
    stopPolling();
    goto('/dashboard');
  }

  // Check authentication and load user data, then start polling
  $effect(() => {
    api.getUser().then(async (u) => {
      user = u;
      const h = await api.getHosts();
      hosts = h ?? [];

      if (hosts.length > 0) {
        // Check immediately if data already exists (redirect straight away)
        try {
          const data = await api.query(hosts[0].name, undefined, undefined);
          if (data && Object.keys(data).length > 0 && Object.values(data).some((v) => Object.keys(v).length > 0)) {
            goto('/dashboard');
            return;
          }
        } catch {
          // No data yet - will poll
        }

        // Start polling for first visit
        startPolling();
      }
    }).catch(() => {
      // Not logged in, redirect to login
      goto('/');
    }).finally(() => {
      loading = false;
    });

    // Cleanup on component destroy
    return () => {
      stopPolling();
    };
  });
</script>

<div class="page">
  {#if loading}
    <div class="loading-screen">
      <div class="spinner"></div>
    </div>
  {:else if user}
    <section class="tracking">
      <div class="content">
        <div class="tracking-illustration">
          <svg width="350" height="495" viewBox="0 0 350 495" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <rect x="25" y="95" width="300" height="280" rx="16" fill="#E8F0FE"/>
            <rect x="45" y="115" width="260" height="40" rx="6" fill="#2563EB" opacity="0.15"/>
            <circle cx="65" cy="135" r="8" fill="#2563EB" opacity="0.3"/>
            <rect x="85" y="129" width="60" height="12" rx="3" fill="#2563EB" opacity="0.4"/>
            <rect x="155" y="129" width="40" height="12" rx="3" fill="#2563EB" opacity="0.2"/>
            <rect x="45" y="175" width="260" height="8" rx="4" fill="#2563EB" opacity="0.1"/>
            <rect x="45" y="195" width="200" height="16" rx="4" fill="#2563EB" opacity="0.12"/>
            <rect x="45" y="225" width="260" height="80" rx="8" fill="#2563EB" opacity="0.08"/>
            <rect x="65" y="245" width="80" height="12" rx="3" fill="#2563EB" opacity="0.3"/>
            <rect x="65" y="265" width="140" height="12" rx="3" fill="#2563EB" opacity="0.15"/>
            <rect x="65" y="285" width="100" height="12" rx="3" fill="#2563EB" opacity="0.2"/>
            <circle cx="215" cy="251" r="30" fill="#2563EB" opacity="0.15"/>
            <circle cx="215" cy="251" r="16" fill="#2563EB" opacity="0.25"/>
            <rect x="45" y="325" width="260" height="8" rx="4" fill="#2563EB" opacity="0.1"/>
            <rect x="45" y="345" width="120" height="16" rx="4" fill="#2563EB" opacity="0.12"/>
            <path d="M175 400 L150 420 L200 420 Z" fill="#2563EB" opacity="0.15"/>
            <rect x="100" y="420" width="150" height="6" rx="3" fill="#2563EB" opacity="0.08"/>
            <rect x="130" y="435" width="90" height="6" rx="3" fill="#2563EB" opacity="0.05"/>
            <circle cx="175" cy="445" r="15" fill="none" stroke="#2563EB" stroke-width="3" opacity="0.3"/>
            <path d="M175 448 L175 455" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" opacity="0.3"/>
            <path d="M175 440 L175 443" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" opacity="0.3"/>
            <path d="M168 445 L172 445" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" opacity="0.3"/>
            <path d="M178 445 L182 445" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" opacity="0.3"/>
          </svg>
        </div>
        <div class="tracking-card">
          <div class="welcome">
            <h1>
              Hi, <span class="username">{user.username}</span>!
            </h1>
          </div>

          <div class="step">
            <div class="step-number">1</div>
            <div>
              <h2>Tracking Code</h2>
              <p>This JavaScript snippet collects visitor statistics. Add it to all HTML pages you want to track.</p>
            </div>
          </div>

          <div class="code-section">
            <div class="code-input-wrap">
              <input
                type="text"
                class="code-input"
                value={getTrackingCode()}
                readonly
                onfocus={(e) => (e.target as HTMLInputElement).select()}
              />
              <button class="btn-copy" onclick={copyCode}>
                {copySuccess ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <span class="hint">Inside the <strong>&lt;head&gt;</strong> section</span>
          </div>

          <div class="step">
            <div class="step-number">2</div>
            <div>
              <h2>Visit a site with the tracking code</h2>
              <p>Open a page that includes the tracking code to see your first visit appear.</p>
            </div>
          </div>

          {#if dashboardNavigating}
            <!-- First visit detected - navigating to dashboard -->
            <div class="waiting detected">
              <svg class="check-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <span>First visit detected! Redirecting to dashboard...</span>
            </div>
          {:else}
            <!-- Waiting for first visit with live polling -->
            <div class="waiting">
              <svg class="loader-svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5">
                <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
              </svg>
              <span>Waiting for first visit...</span>
              {#if firstVisitLoading}
                <span class="polling-hint">checking...</span>
              {/if}
            </div>
          {/if}

          <div class="actions">
            <button class="btn-primary" onclick={goToDashboard} disabled={dashboardNavigating}>
              Go to Dashboard
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
              </svg>
            </button>
          </div>

          <p class="support">
            Got stuck? Disable any tracking blocker,
            <a href="/dashboard">reload the page</a>, or
            <a href="mailto:hey@counter.dev">ask for support.</a>
          </p>
        </div>
      </div>
    </section>
  {/if}
</div>

<style>
  .page { min-height: 100vh; background: #f5f7fa; }
  .loading-screen { display: flex; justify-content: center; align-items: center; min-height: 60vh; }
  .spinner { width: 32px; height: 32px; border: 3px solid #e5e7eb; border-top-color: #2563eb; border-radius: 50%; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .tracking .content {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    gap: 48px;
    max-width: 1060px;
    margin: 0 auto;
    padding: 80px 24px 24px;
  }

  .tracking-illustration {
    flex-shrink: 0;
    width: 350px;
  }
  .tracking-illustration svg {
    width: 100%;
    height: auto;
  }

  .tracking-card {
    flex: 1;
    max-width: 600px;
    background: white;
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  }

  .welcome h1 {
    font-size: 28px;
    font-weight: 700;
    color: #111;
    margin: 0 0 32px;
  }
  .username {
    color: #2563eb;
  }

  .step {
    display: flex;
    gap: 16px;
    align-items: flex-start;
    margin-bottom: 24px;
  }
  .step-number {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #2563eb;
    color: white;
    font-size: 16px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .step h2 {
    font-size: 18px;
    font-weight: 600;
    color: #1a1a2e;
    margin: 0 0 6px;
  }
  .step p {
    font-size: 14px;
    color: #666;
    margin: 0;
    line-height: 1.5;
  }

  .code-section {
    margin: 0 0 32px 48px;
  }
  .code-input-wrap {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
  }
  .code-input {
    flex: 1;
    padding: 12px 14px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    font-size: 13px;
    font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
    background: #f9fafb;
    color: #333;
    word-break: break-all;
  }
  .code-input:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
  }
  .btn-copy {
    background: #2563eb;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.15s;
  }
  .btn-copy:hover { background: #1d4ed8; }
  .btn-copy:active { background: #1e40af; }
  .hint {
    font-size: 13px;
    color: #888;
  }
  .hint strong {
    color: #555;
    font-weight: 600;
  }

  .waiting {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0 0 32px 48px;
    padding: 12px 16px;
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 500;
    color: #0369a1;
  }
  .waiting.detected {
    background: #d4edda;
    border-color: #c3e6cb;
    color: #155724;
  }
  .loader-svg {
    animation: rotate 2s linear infinite;
    flex-shrink: 0;
  }
  @keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  .check-icon {
    flex-shrink: 0;
  }
  .polling-hint {
    font-size: 11px;
    color: #7dd3fc;
    font-weight: 400;
    animation: pulse 1.5s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  .actions {
    margin-left: 48px;
    margin-bottom: 24px;
  }
  .btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border: none;
    padding: 12px 28px;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.1s, box-shadow 0.1s;
  }
  .btn-primary:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102,126,234,0.4);
  }
  .btn-primary:active:not(:disabled) { transform: translateY(0); }
  .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
  .btn-primary svg { width: 18px; height: 18px; }

  .support {
    margin-left: 48px;
    font-size: 13px;
    color: #888;
  }
  .support a {
    color: #2563eb;
    text-decoration: underline;
  }

  @media (max-width: 900px) {
    .tracking .content {
      flex-direction: column;
      align-items: center;
      padding: 24px 16px;
    }
    .tracking-illustration { display: none; }
    .tracking-card {
      max-width: 100%;
      padding: 24px;
      box-shadow: none;
      background: transparent;
    }
    .welcome h1 { font-size: 24px; }
    .code-section, .waiting, .actions, .support {
      margin-left: 0;
    }
    .code-input-wrap { flex-direction: column; }
    .code-input { font-size: 12px; }
  }
</style>
