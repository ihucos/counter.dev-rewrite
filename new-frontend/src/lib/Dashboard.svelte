<script>
  import { onMount } from 'svelte';
  import { api } from './api.js';
  import Settings from './Settings.svelte';
  import MetricsPanel from './MetricsPanel.svelte';

  let user = $state(null);
  let hosts = $state([]);
  let selectedHost = $state(null);
  let queryData = $state(null);
  let loading = $state(true);
  let queryLoading = $state(false);
  let error = $state('');
  let range = $state('last7');

  function today() { return new Date().toISOString().slice(0, 10); }
  function daysAgo(n) { const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10); }

  let startDate = $state(daysAgo(7));
  let endDate = $state(today());

  const RANGES = [
    { key: 'today', label: 'Today', days: 0 },
    { key: 'yesterday', label: 'Yesterday', days: 1, from: 1, to: 1 },
    { key: 'last7', label: 'Last 7 days', days: 7 },
    { key: 'last30', label: 'Last 30 days', days: 30 },
    { key: 'all', label: 'All time', days: null },
  ];

  function flash(msg, type = 'info') {
    window.dispatchEvent(new CustomEvent('flash', { detail: { message: msg, type } }));
  }

  function selectRange(r) {
    range = r.key;
    if (r.days === null) { startDate = ''; endDate = ''; }
    else if (r.days === 0) { startDate = today(); endDate = today(); }
    else if (r.from !== undefined) { startDate = daysAgo(r.from); endDate = daysAgo(r.to); }
    else { startDate = daysAgo(r.days); endDate = today(); }
    loadData();
  }

  async function loadData() {
    if (!selectedHost) return;
    queryLoading = true;
    try {
      queryData = await api.query(selectedHost.name, startDate || undefined, endDate || undefined);
    } catch (e) {
      queryData = null;
      flash('Failed to load data: ' + e.message, 'error');
    } finally {
      queryLoading = false;
    }
  }

  function selectHost(host) {
    selectedHost = host;
    loadData();
  }

  function n(v) {
    if (v == null) return '0';
    return v.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }

  function catTotal(cat) {
    if (!queryData || !queryData[cat]) return 0;
    return Object.values(queryData[cat]).reduce((a, b) => a + b, 0);
  }

  function logout() {
    api.logout().catch(() => {});
    window.dispatchEvent(new CustomEvent('auth-changed', { detail: { authenticated: false } }));
  }

  onMount(async () => {
    try {
      user = await api.getUser();
      hosts = await api.getHosts();
      if (hosts.length > 0) {
        selectedHost = hosts[0];
        queryData = await api.query(selectedHost.name, startDate || undefined, endDate || undefined);
      }
    } catch (e) {
      error = e.message || 'Failed to load.';
    } finally {
      loading = false;
    }
  });
</script>

<div class="dashboard">
  <nav class="nav">
    <div class="nav-inner">
      <span class="brand">API Dashboard</span>
      <div class="nav-right">
        {#if user}<span class="user">{user.username}</span>{/if}
        <Settings {user} {hosts} />
        <button class="btn-outline" onclick={logout}>Sign Out</button>
      </div>
    </div>
  </nav>

  {#if loading}
    <div class="loading"><div class="spinner"></div></div>
  {:else if error}
    <div class="error-banner">{error}</div>
  {:else if hosts.length === 0}
    <div class="empty">
      <h2>Welcome!</h2>
      <p>Add a website in Settings to get started.</p>
    </div>
  {:else}
    <div class="toolbar">
      <div class="toolbar-inner">
        <div class="site-list">
          {#each hosts as h}
            <button class="chip" class:active={selectedHost?.id === h.id} onclick={() => selectHost(h)}>
              {h.name}
            </button>
          {/each}
        </div>
        <div class="range-list">
          {#each RANGES as r}
            <button class="chip" class:active={range === r.key} onclick={() => selectRange(r)}>{r.label}</button>
          {/each}
        </div>
      </div>
    </div>

    <main class="content">
      {#if queryLoading}
        <div class="loading">Loading data...</div>
      {:else if queryData && Object.keys(queryData).length > 0}
        <div class="cards">
          <div class="card"><div class="label">Pageviews</div><div class="value">{n(catTotal('page'))}</div></div>
          <div class="card"><div class="label">Visits</div><div class="value">{n(catTotal('date'))}</div></div>
          <div class="card"><div class="label">Referrers</div><div class="value">{n(catTotal('ref'))}</div></div>
          <div class="card"><div class="label">Countries</div><div class="value">{n(catTotal('country'))}</div></div>
        </div>

        <div class="grid">
          <MetricsPanel title="Pages" data={queryData['page'] ?? {}} />
          <MetricsPanel title="Paths" data={queryData['loc'] ?? {}} />
        </div>
        <div class="grid">
          <MetricsPanel title="Referrers" data={queryData['ref'] ?? {}} />
          <MetricsPanel title="Countries" data={queryData['country'] ?? {}} />
        </div>
        <div class="grid">
          <MetricsPanel title="Browsers" data={queryData['browser'] ?? {}} />
          <MetricsPanel title="Operating Systems" data={queryData['platform'] ?? {}} />
        </div>
        <div class="grid">
          <MetricsPanel title="Devices" data={queryData['device'] ?? {}} />
          <MetricsPanel title="Languages" data={queryData['lang'] ?? {}} />
        </div>
        <div class="grid">
          <MetricsPanel title="Screens" data={queryData['screen'] ?? {}} />
          <MetricsPanel title="Hours" data={queryData['hour'] ?? {}} />
        </div>
      {:else if !queryLoading}
        <div class="empty">No data for this period.</div>
      {/if}
    </main>
  {/if}
</div>

<style>
  .dashboard { min-height: 100vh; background: #f0f2f5; }
  .nav {
    background: white; border-bottom: 1px solid #e0e0e0;
    padding: 12px 0; position: sticky; top: 0; z-index: 100;
  }
  .nav-inner {
    max-width: 1100px; margin: 0 auto; padding: 0 24px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .brand { font-weight: 700; font-size: 16px; color: #4361ee; }
  .nav-right { display: flex; align-items: center; gap: 8px; }
  .user { font-size: 14px; color: #666; }
  .btn-outline {
    background: none; border: 1px solid #ddd; padding: 6px 14px;
    border-radius: 8px; cursor: pointer; font-size: 13px; color: #666;
  }
  .btn-outline:hover { background: #f5f5f5; }
  .loading { text-align: center; padding: 60px; color: #888; }
  .spinner {
    width: 32px; height: 32px; border: 3px solid #e0e0e0;
    border-top-color: #4361ee; border-radius: 50%;
    animation: spin 0.7s linear infinite; margin: 0 auto 12px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .error-banner {
    max-width: 1100px; margin: 24px auto; padding: 16px;
    background: #fee; color: #c0392b; border-radius: 8px;
  }
  .empty { text-align: center; padding: 80px 24px; color: #888; }
  .empty h2 { margin: 0 0 8px; color: #333; }

  .toolbar {
    background: white; border-bottom: 1px solid #e0e0e0;
    padding: 12px 0; position: sticky; top: 53px; z-index: 99;
  }
  .toolbar-inner {
    max-width: 1100px; margin: 0 auto; padding: 0 24px;
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;
  }
  .site-list, .range-list { display: flex; gap: 6px; flex-wrap: wrap; }
  .chip {
    background: #f5f5f5; border: 1px solid #e0e0e0; padding: 6px 14px;
    border-radius: 20px; font-size: 13px; cursor: pointer; color: #555;
  }
  .chip:hover { background: #eee; }
  .chip.active { background: #4361ee; color: white; border-color: #4361ee; }

  .content { max-width: 1100px; margin: 0 auto; padding: 24px; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .card {
    background: white; border-radius: 12px; padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  .label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
  .value { font-size: 28px; font-weight: 700; color: #1a1a2e; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
  @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
</style>
