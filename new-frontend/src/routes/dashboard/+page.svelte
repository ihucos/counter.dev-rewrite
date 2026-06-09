<script lang="ts">
  import { goto } from '$app/navigation';
  import { api } from '$lib/api.js';
  import type { UserData, HostData } from '$lib/api.js';
  import type { VisitLogEntry } from '$lib/api.js';
  import Settings from '$lib/Settings.svelte';
  import MetricsPanel from '$lib/MetricsPanel.svelte';
  import ConnectionStatus from '$lib/ConnectionStatus.svelte';
  import TimeSeriesChart from '$lib/TimeSeriesChart.svelte';
  import DownloadCSV from '$lib/DownloadCSV.svelte';
  import TrafficSources from '$lib/TrafficSources.svelte';
  import TimeSection from '$lib/TimeSection.svelte';
  import SourcesCountries from '$lib/SourcesCountries.svelte';
  import RecentVisits from '$lib/RecentVisits.svelte';

  let user = $state<UserData | null>(null);
  let hosts = $state<HostData[]>([]);
  let selectedHostId = $state<number | null>(null);
  let selectedHostName = $derived.by(() => {
    if (!selectedHostId) return null;
    const h = hosts.find(h => h.id === selectedHostId);
    return h ? h.name : null;
  });
  let queryData = $state<Record<string, Record<string, number>> | null>(null);
  let loading = $state(true);
  let queryLoading = $state(false);
  let error = $state('');
  let connectionStatus = $state('checking');
  let lastRefresh = $state<Date | null>(null);
  let visitLogs = $state<VisitLogEntry[]>([]);
  let logsLoading = $state(false);

  const REFRESH_INTERVAL_MS = 15000;
  let refreshTimer: ReturnType<typeof setInterval> | null = null;

  function flash(msg: string, type: string = 'info'): void {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message: msg, type } }));
  }

  function today(): string { return new Date().toISOString().slice(0, 10); }
  function daysAgo(n: number): string { const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10); }

  let range = $state('last7');
  let startDate = $state(daysAgo(7));
  let endDate = $state(today());

  const RANGES = [
    { key: 'today', label: 'Today', days: 0 },
    { key: 'yesterday', label: 'Yesterday', days: 1, from: 1, to: 1 },
    { key: 'last7', label: 'Last 7 days', days: 7 },
    { key: 'last30', label: 'Last 30 days', days: 30 },
    { key: 'all', label: 'All time', days: null as number | null },
  ];

  function startAutoRefresh(): void {
    stopAutoRefresh();
    refreshTimer = setInterval(() => {
      if (selectedHostName) {
        loadQueryData(true);
        loadVisitLogs(true);
      }
    }, REFRESH_INTERVAL_MS);
  }

  function stopAutoRefresh(): void {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }

  async function checkConnection(): Promise<void> {
    connectionStatus = 'connecting';
    try {
      await api.getHosts();
      connectionStatus = 'connected';
    } catch {
      connectionStatus = 'disconnected';
    }
  }

  async function loadQueryData(silent = false): Promise<void> {
    if (!selectedHostName) return;
    if (!silent) queryLoading = true;
    try {
      queryData = await api.query(selectedHostName, startDate || undefined, endDate || undefined);
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

  async function loadVisitLogs(silent = false): Promise<void> {
    if (!selectedHostName) return;
    if (!silent) logsLoading = true;
    try {
      const response = await api.getVisitLogs(selectedHostName, 50);
      visitLogs = response?.logs || [];
      if (response?.sites_with_logs && response.sites_with_logs.length > 0) {
        connectionStatus = 'connected';
      }
    } catch (e) {
      console.error('Failed to load visit logs', e);
      if (!silent) visitLogs = [];
    } finally {
      if (!silent) logsLoading = false;
    }
  }

  function selectRange(r: { key: string; days: number | null; from?: number; to?: number }): void {
    range = r.key;
    if (r.days === null) { startDate = ''; endDate = ''; }
    else if (r.days === 0) { startDate = today(); endDate = today(); }
    else if (r.from !== undefined) { startDate = daysAgo(r.from); endDate = daysAgo(r.to); }
    else { startDate = daysAgo(r.days); endDate = today(); }
    loadQueryData();
  }

  function selectHost(id: number): void {
    selectedHostId = id;
    Promise.all([loadQueryData(), loadVisitLogs()]);
  }

  function categoryTotal(category: string): number {
    if (!queryData || !queryData[category]) return 0;
    return Object.values(queryData[category]).reduce((a: number, b: number) => a + b, 0);
  }

  let totalVisits = $derived(categoryTotal('date'));

  function n(x: number | null | undefined): string {
    if (x == null) return '0';
    return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }

  function formatRefreshTime(date: Date): string {
    return date.toLocaleTimeString();
  }

  async function logout(): Promise<void> {
    try { await api.logout(); } catch { /* ignore */ }
    goto('/');
  }

  // Initialize on mount
  $effect(() => {
    checkConnection();
    api.getUser().then(async (u) => {
      user = u;
      const h = await api.getHosts();
      hosts = h ?? [];
      if (hosts.length > 0) {
        selectedHostId = hosts[0].id;
        await Promise.all([loadQueryData(), loadVisitLogs()]);
      }
      connectionStatus = 'connected';
      startAutoRefresh();
    }).catch(() => {
      goto('/');
    }).finally(() => {
      loading = false;
    });

    return () => { stopAutoRefresh(); };
  });
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
        <Settings {user} {hosts} />
        <button class="btn-outline" onclick={logout}>Sign Out</button>
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
        <p class="small">Your tracking code will be shown in Settings once you have a site set up.</p>
      </div>
    </main>
  {:else}
    <section class="toolbar">
      <div class="content toolbar-inner">
        <div class="toolbar-left">
          <div class="site-selector">
            {#each hosts as host (host.id)}
              <button class="chip" class:active={selectedHostId === host.id} onclick={() => selectHost(host.id)}>
                {host.name}
              </button>
            {/each}
          </div>
        </div>
        <div class="toolbar-right">
          <div class="range-selector">
            {#each RANGES as r}
              <button class="chip" class:active={range === r.key} onclick={() => selectRange(r)}>
                {r.label}
              </button>
            {/each}
          </div>
          {#if queryData}
            <DownloadCSV data={queryData ?? {}} hostName={selectedHostName ?? 'unknown'} {startDate} {endDate} />
          {/if}
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

        <!-- Summary cards -->
        <section class="summary-cards">
          <div class="card">
            <div class="card-label">Pageviews</div>
            <div class="card-value">{n(categoryTotal('page'))}</div>
          </div>
          <div class="card">
            <div class="card-label">Visits</div>
            <div class="card-value">{n(totalVisits)}</div>
          </div>
          <div class="card">
            <div class="card-label">Referrers</div>
            <div class="card-value">{n(categoryTotal('ref'))}</div>
          </div>
          <div class="card">
            <div class="card-label">Countries</div>
            <div class="card-value">{n(categoryTotal('country'))}</div>
          </div>
        </section>

        <!-- Traffic sources: visits, search engines, social, direct -->
        <TrafficSources queryData={queryData ?? {}} />

        <!-- Visit chart over time -->
        <section class="chart-section">
          <TimeSeriesChart
            dateData={queryData['date'] ?? {}}
            {startDate}
            {endDate}
          />
        </section>

        <!-- Metrics: pages, page paths -->
        <section class="metrics-grid">
          <MetricsPanel title="Pages" data={queryData['page'] ?? {}} />
          <MetricsPanel title="Page Paths" data={queryData['loc'] ?? {}} />
        </section>

        <!-- Sources & Countries - enhanced panel -->
        <section class="sources-countries-section">
          <SourcesCountries
            refData={queryData['ref'] ?? {}}
            countryData={queryData['country'] ?? {}}
          />
        </section>

        <!-- Metrics: browsers, operating systems -->
        <section class="metrics-grid">
          <MetricsPanel title="Browsers" data={queryData['browser'] ?? {}} />
          <MetricsPanel title="Operating Systems" data={queryData['platform'] ?? {}} />
        </section>

        <!-- Metrics: devices, languages -->
        <section class="metrics-grid">
          <MetricsPanel title="Devices" data={queryData['device'] ?? {}} />
          <MetricsPanel title="Languages" data={queryData['lang'] ?? {}} />
        </section>

        <!-- Metrics: screens + time section with tabs -->
        <section class="metrics-grid">
          <MetricsPanel title="Screens" data={queryData['screen'] ?? {}} />
          <TimeSection
            hourData={queryData['hour'] ?? {}}
            weekdayData={queryData['weekday'] ?? {}}
          />
        </section>

        <!-- Recent visits section -->
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
  .btn-outline { background: none; border: 1px solid #ddd; padding: 6px 14px; border-radius: 8px; cursor: pointer; font-size: 13px; color: #666; }
  .btn-outline:hover { background: #f5f5f5; }

  .content { max-width: 1060px; margin: 0 auto; padding: 0 24px; }
  .loading-screen { display: flex; justify-content: center; align-items: center; min-height: 60vh; }
  .spinner { width: 32px; height: 32px; border: 3px solid #e5e7eb; border-top-color: #2563eb; border-radius: 50%; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading-indicator { text-align: center; padding: 40px; color: #666; font-size: 16px; }
  .error-banner { background: #fef2f2; color: #dc2626; padding: 16px; border-radius: 8px; margin-top: 24px; }
  .empty-state { text-align: center; padding: 80px 24px; }
  .empty-state h2 { font-size: 28px; margin-bottom: 12px; }
  .empty-state p { color: #666; font-size: 16px; }
  .empty-state .small { font-size: 14px; color: #999; }
  .empty-data { text-align: center; padding: 60px 24px; color: #666; font-size: 16px; }

  .refresh-indicator { display: flex; align-items: center; justify-content: flex-end; gap: 10px; margin-top: 20px; margin-bottom: 4px; }
  .refresh-time { font-size: 11px; color: #999; }
  .refresh-badge { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; padding: 2px 8px; border-radius: 8px; background: #d1fae5; color: #065f46; font-weight: 600; }

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
  .card-value { font-size: 28px; font-weight: 700; color: #111; }

  .chart-section { margin-top: 24px; }
  .metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px; margin-bottom: 24px; }
  .sources-countries-section { margin-top: 24px; margin-bottom: 24px; }
  .recent-visits-section { margin-top: 24px; margin-bottom: 48px; }

  @media (max-width: 768px) {
    .metrics-grid { grid-template-columns: 1fr; }
    .toolbar-inner { flex-direction: column; align-items: stretch; }
    .toolbar-right { justify-content: space-between; }
  }
</style>
