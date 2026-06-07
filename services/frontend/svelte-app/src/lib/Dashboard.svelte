<script>
  import { api } from '$lib/api.js';
  import { onMount, onDestroy } from 'svelte';
  import Settings from '$lib/Settings.svelte';
  import MetricsPanel from '$lib/MetricsPanel.svelte';
  import TimeSeriesChart from '$lib/TimeSeriesChart.svelte';
  import DownloadCSV from '$lib/DownloadCSV.svelte';
  import ConnectionStatus from '$lib/ConnectionStatus.svelte';
  import RecentVisits from '$lib/RecentVisits.svelte';

  let hosts = $state([]);
  let selectedHostId = $state(null);
  let selectedHostName = $derived.by(() => {
    if (!selectedHostId) return null;
    const h = hosts.find(h => h.id === selectedHostId);
    return h ? h.name : null;
  });
  let queryData = $state(null);
  let loading = $state(true);
  let queryLoading = $state(false);
  let error = $state('');
  let user = $state(null);
  let connectionStatus = $state('checking');
  let lastRefresh = $state(null);
  let visitLogs = $state([]);
  let logsLoading = $state(false);

  const REFRESH_INTERVAL_MS = 15000;
  let refreshTimer = null;

  function flash(message, type = 'info') {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message, type } }));
  }

  function today() {
    const d = new Date();
    return d.toISOString().slice(0, 10);
  }
  function daysAgo(n) {
    const d = new Date();
    d.setDate(d.getDate() - n);
    return d.toISOString().slice(0, 10);
  }

  let range = $state('last7');
  let startDate = $state(daysAgo(7));
  let endDate = $state(today());

  const RANGES = [
    { key: 'today', label: 'Today', days: 0 },
    { key: 'yesterday', label: 'Yesterday', days: 1, from: 1, to: 1 },
    { key: 'last7', label: 'Last 7 days', days: 7 },
    { key: 'last30', label: 'Last 30 days', days: 30 },
    { key: 'all', label: 'All time', days: null },
  ];

  function startAutoRefresh() {
    stopAutoRefresh();
    refreshTimer = setInterval(() => {
      if (selectedHostName) {
        loadQueryData(true);
        loadVisitLogs(true);
      }
    }, REFRESH_INTERVAL_MS);
  }

  function stopAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }

  async function checkConnection() {
    connectionStatus = 'connecting';
    try {
      await api.getHosts();
      connectionStatus = 'connected';
    } catch {
      connectionStatus = 'disconnected';
    }
  }

  onMount(async () => {
    checkConnection();
    try {
      user = await api.getUser();
      hosts = await api.getHosts();
      if (hosts.length > 0) {
        selectedHostId = hosts[0].id;
        await Promise.all([
          loadQueryData(),
          loadVisitLogs(),
        ]);
      }
      connectionStatus = 'connected';
      startAutoRefresh();
    } catch (e) {
      error = e.message || 'Failed to load data';
      connectionStatus = 'disconnected';
    } finally {
      loading = false;
    }
  });

  onDestroy(() => {
    stopAutoRefresh();
  });

  async function loadQueryData(silent = false) {
    if (!selectedHostName) return;
    if (!silent) queryLoading = true;
    try {
      queryData = await api.query(
        selectedHostName,
        startDate || undefined,
        endDate || undefined
      );
      lastRefresh = new Date();
      connectionStatus = 'connected';
    } catch (e) {
      console.error('Query failed', e);
      if (!silent) {
        queryData = null;
        connectionStatus = 'disconnected';
      }
    } finally {
      if (!silent) queryLoading = false;
    }
  }

  async function loadVisitLogs(silent = false) {
    if (!selectedHostName) return;
    if (!silent) logsLoading = true;
    try {
      const response = await api.getVisitLogs(selectedHostName, 50);
      visitLogs = response.logs || [];
      if (response.sites_with_logs && response.sites_with_logs.length > 0) {
        connectionStatus = 'connected';
      }
    } catch (e) {
      console.error('Failed to load visit logs', e);
      if (!silent) {
        visitLogs = [];
      }
    } finally {
      if (!silent) logsLoading = false;
    }
  }

  function selectRange(r) {
    range = r.key;
    if (r.days === null) {
      startDate = '';
      endDate = '';
    } else if (r.days === 0) {
      startDate = today();
      endDate = today();
    } else if (r.from !== undefined) {
      startDate = daysAgo(r.from);
      endDate = daysAgo(r.to);
    } else {
      startDate = daysAgo(r.days);
      endDate = today();
    }
    loadQueryData();
  }

  function selectHost(id) {
    selectedHostId = id;
    Promise.all([
      loadQueryData(),
      loadVisitLogs(),
    ]);
  }

  function categoryTotal(category) {
    if (!queryData || !queryData[category]) return 0;
    return Object.values(queryData[category]).reduce((a, b) => a + b, 0);
  }

  let totalVisits = $derived(categoryTotal('date'));

  function numberFormat(x) {
    if (x == null) return '0';
    return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }

  function handleAuthChanged(event) {
    if (!event.detail.authenticated) {
      window.dispatchEvent(new CustomEvent('auth-changed', { detail: { authenticated: false } }));
    }
  }

  function formatRefreshTime(date) {
    if (!date) return '';
    return date.toLocaleTimeString();
  }

  const ICONS = {
    page: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
    loc: '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    ref: '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17V11"/>',
    country: '<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    browser: '<circle cx="12" cy="12" r="3"/><path d="M12 21a9 9 0 0 0 9-9"/><path d="M12 3a9 9 0 0 0-9 9"/><circle cx="12" cy="12" r="9"/>',
    platform: '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22h6"/><path d="M12 17v2"/>',
    device: '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 22h8"/>',
    lang: '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>',
    screen: '<path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>',
    hour: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    weekday: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>',
    chart: '<path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/>',
  };

  const HOUR_LABELS = {
    0: '12 a.m.', 1: '1 a.m.', 2: '2 a.m.', 3: '3 a.m.',
    4: '4 a.m.', 5: '5 a.m.', 6: '6 a.m.', 7: '7 a.m.',
    8: '8 a.m.', 9: '9 a.m.', 10: '10 a.m.', 11: '11 a.m.',
    12: '12 noon', 13: '1 p.m.', 14: '2 p.m.', 15: '3 p.m.',
    16: '4 p.m.', 17: '5 p.m.', 18: '6 p.m.', 19: '7 p.m.',
    20: '8 p.m.', 21: '9 p.m.', 22: '10 p.m.', 23: '11 p.m.',
  };

  function getNormalizedHours(hours) {
    if (!hours) return {};
    const pad = Object.fromEntries([...Array(24).keys()].map(i => [HOUR_LABELS[i], 0]));
    const formatted = Object.fromEntries(
      Object.entries(hours).map(([k, v]) => [HOUR_LABELS[k] || k, v])
    );
    return { ...pad, ...formatted };
  }

  const WEEKDAY_LABELS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  function getNormalizedWeekdays(weekdayData) {
    if (!weekdayData) return {};
    return Object.fromEntries(
      WEEKDAY_LABELS.map((label, idx) => [label, weekdayData[String(idx)] || 0])
    );
  }
</script>

<div class="dashboard">
  <nav class="navbar">
    <div class="content">
      <a href="/" class="logotype" aria-label="Counter home"></a>
      <div class="nav-right">
        {#if user}
          <span class="user-name">{user.username}</span>
        {/if}
        <ConnectionStatus status={connectionStatus} />
        <Settings
          {hosts}
          {selectedHostName}
          {user}
          onauthChanged={handleAuthChanged}
        />
      </div>
    </div>
  </nav>

  {#if loading}
    <div class="loading-screen">
      <div class="spinner"></div>
    </div>
  {:else if error}
    <main class="content">
      <div class="error-banner">Error: {error}</div>
    </main>
  {:else if hosts.length === 0}
    <main class="content">
      <div class="empty-state">
        <h2>Welcome to Counter</h2>
        <p>Add a tracking code to your website to get started.</p>
        <p class="small">Your tracking code will be shown here once you have a site set up.</p>
      </div>
    </main>
  {:else}
    <section class="toolbar">
      <div class="content toolbar-inner">
        <div class="toolbar-left">
          <div class="site-selector">
            {#each hosts as host (host.id)}
              <button
                class="chip"
                class:active={selectedHostId === host.id}
                onclick={() => selectHost(host.id)}
              >
                {host.name}
              </button>
            {/each}
          </div>
        </div>
        <div class="toolbar-right">
          <div class="range-selector">
            {#each RANGES as r}
              <button
                class="chip"
                class:active={range === r.key}
                onclick={() => selectRange(r)}
              >
                {r.label}
              </button>
            {/each}
          </div>
          <DownloadCSV
            data={queryData ?? {}}
            hostName={selectedHostName ?? 'unknown'}
            {startDate}
            {endDate}
          />
        </div>
      </div>
    </section>

    <main class="content">
      {#if queryLoading}
        <div class="loading-indicator">Loading data...</div>
      {:else if queryData && Object.keys(queryData).length > 0}
        <div class="refresh-indicator">
          {#if lastRefresh}
            <span class="refresh-time">Last updated: {formatRefreshTime(lastRefresh)}</span>
          {/if}
          <span class="refresh-badge">Auto-refreshing</span>
        </div>

        <section class="summary-cards">
          <div class="card">
            <div class="card-label">Pageviews</div>
            <div class="card-value">{numberFormat(categoryTotal('page'))}</div>
          </div>
          <div class="card">
            <div class="card-label">Visits</div>
            <div class="card-value">{numberFormat(totalVisits)}</div>
          </div>
          <div class="card">
            <div class="card-label">Referrers</div>
            <div class="card-value">{numberFormat(categoryTotal('ref'))}</div>
          </div>
          <div class="card">
            <div class="card-label">Countries</div>
            <div class="card-value">{numberFormat(categoryTotal('country'))}</div>
          </div>
        </section>

        <section class="chart-section">
          <TimeSeriesChart
            dateData={queryData['date'] ?? {}}
            {startDate}
            {endDate}
          />
        </section>

        <section class="metrics-grid">
          <MetricsPanel title="Pages" icon={ICONS.page} data={queryData['page'] ?? {}} />
          <MetricsPanel title="Page Paths" icon={ICONS.loc} data={queryData['loc'] ?? {}} />
        </section>

        <section class="metrics-grid">
          <MetricsPanel title="Referrers" icon={ICONS.ref} data={queryData['ref'] ?? {}} />
          <MetricsPanel title="Countries" icon={ICONS.country} data={queryData['country'] ?? {}} />
        </section>

        <section class="metrics-grid">
          <MetricsPanel title="Browsers" icon={ICONS.browser} data={queryData['browser'] ?? {}} />
          <MetricsPanel title="Operating Systems" icon={ICONS.platform} data={queryData['platform'] ?? {}} />
        </section>

        <section class="metrics-grid">
          <MetricsPanel title="Devices" icon={ICONS.device} data={queryData['device'] ?? {}} />
          <MetricsPanel title="Languages" icon={ICONS.lang} data={queryData['lang'] ?? {}} />
        </section>

        <section class="metrics-grid">
          <MetricsPanel title="Screens" icon={ICONS.screen} data={queryData['screen'] ?? {}} />
          <MetricsPanel title="Hour" icon={ICONS.hour} data={getNormalizedHours(queryData['hour'])} />
        </section>

        <section class="metrics-grid">
          <MetricsPanel title="Day of Week" icon={ICONS.weekday} data={getNormalizedWeekdays(queryData['weekday'])} />
          <div></div>
        </section>

        <!-- Recent visits section: shows live log entries from Redis -->
        <section class="recent-visits-section">
          {#if logsLoading}
            <div class="loading-indicator">Loading recent visits...</div>
          {:else}
            <RecentVisits logs={visitLogs} hostName={selectedHostName ?? ''} />
          {/if}
        </section>
      {:else if !queryLoading}
        <div class="empty-data">No data available for this period.</div>
      {/if}
    </main>
  {/if}
</div>

<style>
  .dashboard { min-height: 100vh; background: #f5f5f5; }
  .navbar { background: white; border-bottom: 1px solid #e5e7eb; padding: 12px 0; position: sticky; top: 0; z-index: 100; }
  .navbar .content { display: flex; justify-content: space-between; align-items: center; }
  .logotype { width: 28px; height: 28px; background: #2563eb; border-radius: 6px; display: block; }
  .nav-right { display: flex; align-items: center; gap: 8px; }
  .user-name { font-size: 14px; color: #666; }

  .content { max-width: 1060px; margin: 0 auto; padding: 0 24px; }
  .loading-screen { display: flex; justify-content: center; align-items: center; min-height: 60vh; }
  .spinner { width: 32px; height: 32px; border: 3px solid #e5e7eb; border-top-color: #2563eb; border-radius: 50%; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading-indicator { text-align: center; padding: 40px; color: #666; font-size: 16px; }
  .error-banner { background: #fef2f2; color: #dc2626; padding: 16px; border-radius: 8px; margin-top: 24px; }
  .empty-state { text-align: center; padding: 80px 24px; }
  .empty-state h2 { font-family: 'Nunito Sans', sans-serif; font-size: 28px; margin-bottom: 12px; }
  .empty-state p { color: #666; font-size: 16px; }
  .empty-state .small { font-size: 14px; color: #999; }
  .empty-data { text-align: center; padding: 60px 24px; color: #666; font-size: 16px; }

  .refresh-indicator {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 20px;
    margin-bottom: 4px;
  }
  .refresh-time {
    font-size: 11px;
    color: #999;
  }
  .refresh-badge {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 2px 8px;
    border-radius: 8px;
    background: #d1fae5;
    color: #065f46;
    font-weight: 600;
  }

  .toolbar { background: white; border-bottom: 1px solid #e5e7eb; padding: 12px 0; position: sticky; top: 53px; z-index: 99; }
  .toolbar-inner { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; align-items: center; }
  .toolbar-left, .toolbar-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .site-selector, .range-selector { display: flex; gap: 6px; flex-wrap: wrap; }
  .chip { background: #f3f4f6; border: 1px solid #e5e7eb; padding: 6px 14px; border-radius: 20px; font-size: 13px; cursor: pointer; color: #555; transition: all 0.15s; }
  .chip:hover { background: #e5e7eb; }
  .chip.active { background: #2563eb; color: white; border-color: #2563eb; }

  .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-top: 24px; }
  .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  .card-label { font-size: 13px; color: #888; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
  .card-value { font-size: 28px; font-weight: 700; font-family: 'Nunito Sans', sans-serif; color: #111; }

  .chart-section { margin-top: 24px; }

  .metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px; margin-bottom: 24px; }

  .recent-visits-section {
    margin-top: 24px;
    margin-bottom: 48px;
  }

  @media (max-width: 768px) {
    .metrics-grid { grid-template-columns: 1fr; }
    .toolbar-inner { flex-direction: column; align-items: stretch; }
    .toolbar-right { justify-content: space-between; }
  }
</style>
