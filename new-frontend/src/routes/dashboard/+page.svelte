<script lang="ts">
  import { goto } from '$app/navigation';
  import { api } from '$lib/api.js';
  import type { UserData, HostData } from '$lib/api.js';
  import type { VisitLogEntry } from '$lib/api.js';
  import type { DumpPayload } from '$lib/live.js';
  import { getLiveStream } from '$lib/live.js';
  import Settings from '$lib/Settings.svelte';
  import MetricsPanel from '$lib/MetricsPanel.svelte';
  import ConnectionStatus from '$lib/ConnectionStatus.svelte';
  import TimeSeriesChart from '$lib/TimeSeriesChart.svelte';
  import DownloadCSV from '$lib/DownloadCSV.svelte';
  import TrafficSources from '$lib/TrafficSources.svelte';
  import TimeSection from '$lib/TimeSection.svelte';
  import SourcesCountries from '$lib/SourcesCountries.svelte';
  import RecentVisits from '$lib/RecentVisits.svelte';
  import Pwyw from '$lib/Pwyw.svelte';

  let user = $state<UserData | null>(null);
  let hosts = $state<HostData[]>([]);
  let selectedHostId = $state<number | null>(null);

  /**
   * Visible hosts: apply hide_hosts preference filtering.
   * If the user has hide_hosts enabled, only show hosts where hide === false.
   * Otherwise show all hosts.
   */
  let visibleHosts = $derived.by(() => {
    if (!user?.hide_hosts) return hosts;
    return hosts.filter(h => !h.hide);
  });

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

  // PWYW metrics
  let pwywTotalDaysTracked = $state(0);
  let pwywAverageDailyHits = $state(0);

  const REFRESH_INTERVAL_MS = 15000;
  let refreshTimer: ReturnType<typeof setInterval> | null = null;
  // Tracks whether the current queryData came from a properly filtered
  // API query (true) vs. from the live stream's "all" bucket (false).
  // When true, incoming SSE dump events should NOT overwrite queryData
  // (except for the "today" and "yesterday" ranges, where the SSE data
  // is accurate).
  let dataFromApiQuery = $state(false);

  /**
   * SVG icon paths for each MetricsPanel (matching old design).
   * Each is a 24x24 viewBox SVG path content.
   */
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
  };

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

  /**
   * Compute PWYW metrics by querying all hosts with all-time data.
   */
  async function computePwywMetrics(): Promise<void> {
    if (!hosts || hosts.length === 0) return;

    let maxDaysTracked = 0;
    let totalLast7Hits = 0;
    let hostsWithData = 0;

    for (const host of hosts) {
      try {
        const allData = await api.query(host.name, undefined, undefined);
        if (!allData) continue;

        const dateData = allData['date'];
        if (!dateData || Object.keys(dateData).length === 0) continue;

        hostsWithData++;

        const numDays = Object.keys(dateData).length;
        if (numDays > maxDaysTracked) maxDaysTracked = numDays;

        const sortedDates = Object.keys(dateData).sort().reverse();
        const recent7 = sortedDates.slice(0, 7);
        for (const d of recent7) {
          totalLast7Hits += dateData[d] || 0;
        }
      } catch {
        // Skip hosts that error
      }
    }

    pwywTotalDaysTracked = maxDaysTracked;
    pwywAverageDailyHits = hostsWithData > 0 ? Math.round(totalLast7Hits / 7) : 0;
  }

  /**
   * Start the auto-refresh timer.
   *
   * Always refreshes visit logs. Query data is refreshed via the timer
   * only if SSE is not connected. SSE provides real-time data for
   * "today" and "yesterday" ranges; for other ranges, the timer calls
   * the API query with proper date filtering.
   */
  function startAutoRefresh(): void {
    stopAutoRefresh();
    refreshTimer = setInterval(() => {
      if (selectedHostName) {
        loadVisitLogs(true);
        // Always refresh query data so date-filtered views stay accurate.
        // This also ensures "last7", "last30", and "all" ranges get
        // properly filtered data from the API.
        loadQueryData(true);
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

  /**
   * Handle incoming live data from the SSE/polling stream.
   *
   * For "today" and "yesterday" ranges, the SSE payload's `day` and
   * `yesterday` buckets are accurate and can overwrite queryData.
   *
   * For other ranges ("last7", "last30", "all"), the SSE payload only
   * has the `all` bucket, which may not reflect the selected range.
   * In these cases, we only update queryData from the SSE payload when
   * the current data hasn't come from a properly filtered API query
   * (i.e., on initial load or after a range switch before the API
   * query completes).
   */
  function handleLiveDump(payload: DumpPayload): void {
    if (!selectedHostName) return;
    const siteData = payload.sites[selectedHostName];
    if (!siteData) return;

    // Update recent logs from live data immediately
    if (siteData.logs && siteData.logs.length > 0) {
      visitLogs = siteData.logs;
    }

    // Decide whether to update queryData from SSE data.
    // For "today" and "yesterday", the SSE data is range-accurate.
    // For other ranges, only apply SSE data if we don't already have
    // properly filtered data from the API query.
    const shouldApplySseData =
      range === 'today' ||
      range === 'yesterday' ||
      !dataFromApiQuery;

    if (shouldApplySseData) {
      let sseData: Record<string, Record<string, number>> | null = null;
      if (range === 'today') {
        sseData = siteData.visits.day ?? null;
      } else if (range === 'yesterday') {
        sseData = siteData.visits.yesterday ?? null;
      } else {
        sseData = siteData.visits.all ?? null;
      }

      if (sseData && Object.keys(sseData).length > 0) {
        queryData = sseData;
      }
    }

    connectionStatus = 'connected';
    lastRefresh = new Date();
  }

  function handleLiveConnected(): void {
    connectionStatus = 'connected';
  }

  function handleLiveDisconnected(): void {
    connectionStatus = 'disconnected';
  }

  function handleLiveError(): void {
    // Don't immediately disconnect on error - the live stream will fall back to polling
  }

  /**
   * Initialize the live stream for real-time data.
   * Returns a cleanup function that unsubscribes and stops the stream.
   */
  function initLiveStream(): (() => void) | undefined {
    if (!hosts.length) return;

    const stream = getLiveStream();
    stream.setHosts(hosts);

    const unsub = stream.subscribe((event) => {
      switch (event.type) {
        case 'dump':
          handleLiveDump(event.data as DumpPayload);
          break;
        case 'connected':
          handleLiveConnected();
          break;
        case 'disconnected':
          handleLiveDisconnected();
          break;
        case 'error':
          handleLiveError();
          break;
        case 'nouser':
          goto('/');
          break;
      }
    });

    stream.start();

    // Return cleanup function to be called on component destroy
    return () => {
      unsub();
      stream.stop();
    };
  }

  async function loadQueryData(silent = false): Promise<void> {
    if (!selectedHostName) return;
    if (!silent) queryLoading = true;
    try {
      queryData = await api.query(selectedHostName, startDate || undefined, endDate || undefined);
      dataFromApiQuery = true;
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
    // Reset the flag so SSE data can fill in until the API query completes
    dataFromApiQuery = false;
    loadQueryData();
  }

  function selectHost(id: number): void {
    selectedHostId = id;
    dataFromApiQuery = false;
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

  // Initialize on mount and clean up on destroy
  $effect(() => {
    checkConnection();

    let liveCleanup: (() => void) | undefined;

    api.getUser().then(async (u) => {
      user = u;
      const h = await api.getHosts();
      hosts = h ?? [];
      // Initialize live stream with hosts data and store cleanup
      liveCleanup = initLiveStream();

      // Select first visible host
      const targetHosts = u?.hide_hosts ? (h ?? []).filter(host => !host.hide) : (h ?? []);
      if (targetHosts.length > 0) {
        selectedHostId = targetHosts[0].id;
        await Promise.all([loadQueryData(), loadVisitLogs()]);
        computePwywMetrics();
      }
      connectionStatus = 'connected';
      startAutoRefresh();
    }).catch(() => {
      goto('/');
    }).finally(() => {
      loading = false;
    });

    return () => {
      stopAutoRefresh();
      if (liveCleanup) {
        liveCleanup();
      }
    };
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
            {#each visibleHosts as host (host.id)}
              <button class="chip" class:active={selectedHostId === host.id} onclick={() => selectHost(host.id)}>
                {host.name}
              </button>
            {/each}
            {#if visibleHosts.length === 0}
              <span class="no-visible-hosts">No visible websites. Check your Settings.</span>
            {/if}
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
      {:else if selectedHostName && queryData && Object.keys(queryData).length > 0}
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

        <!-- Traffic sources -->
        <TrafficSources queryData={queryData ?? {}} />

        <!-- Visit chart over time -->
        <section class="chart-section">
          <TimeSeriesChart
            dateData={queryData['date'] ?? {}}
            {startDate}
            {endDate}
          />
        </section>

        <!-- Pages and Page Paths with icons -->
        <section class="metrics-grid">
          <MetricsPanel title="Pages" icon={ICONS.page} data={queryData['page'] ?? {}} />
          <MetricsPanel title="Page Paths" icon={ICONS.loc} data={queryData['loc'] ?? {}} />
        </section>

        <!-- Sources & Countries -->
        <section class="sources-countries-section">
          <SourcesCountries
            refData={queryData['ref'] ?? {}}
            countryData={queryData['country'] ?? {}}
          />
        </section>

        <!-- Browsers and Operating Systems with icons -->
        <section class="metrics-grid">
          <MetricsPanel title="Browsers" icon={ICONS.browser} data={queryData['browser'] ?? {}} />
          <MetricsPanel title="Operating Systems" icon={ICONS.platform} data={queryData['platform'] ?? {}} />
        </section>

        <!-- Devices and Languages with icons -->
        <section class="metrics-grid">
          <MetricsPanel title="Devices" icon={ICONS.device} data={queryData['device'] ?? {}} />
          <MetricsPanel title="Languages" icon={ICONS.lang} data={queryData['lang'] ?? {}} />
        </section>

        <!-- Screens with icon + Time section -->
        <section class="metrics-grid">
          <MetricsPanel title="Screens" icon={ICONS.screen} data={queryData['screen'] ?? {}} />
          <TimeSection
            hourData={queryData['hour'] ?? {}}
            weekdayData={queryData['weekday'] ?? {}}
          />
        </section>

        <!-- Recent visits -->
        <section class="recent-visits-section">
          {#if logsLoading}
            <div class="loading-indicator">Loading recent visits...</div>
          {:else}
            <RecentVisits logs={visitLogs} hostName={selectedHostName ?? ''} />
          {/if}
        </section>

        <!-- Pay What You Want -->
        {#if user}
          <Pwyw
            totalDaysTracked={pwywTotalDaysTracked}
            averageDailyHits={pwywAverageDailyHits}
            userId={user.pk}
            isSubscribed={false}
          />
        {/if}
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
  .no-visible-hosts { font-size: 13px; color: #999; padding: 6px 0; }

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
