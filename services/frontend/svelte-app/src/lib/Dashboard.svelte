<script>
  import { api } from '$lib/api.js';
  import { onMount } from 'svelte';

  let hosts = $state([]);
  let selectedHost = $state(null);
  let queryData = $state(null);
  let loading = $state(true);
  let queryLoading = $state(false);
  let error = $state('');
  let user = $state(null);

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

  onMount(async () => {
    try {
      user = await api.getUser();
      hosts = await api.getHosts();
      if (hosts.length > 0) {
        selectedHost = hosts[0].name;
        await loadQueryData();
      }
    } catch (e) {
      error = e.message || 'Failed to load data';
    } finally {
      loading = false;
    }
  });

  async function loadQueryData() {
    if (!selectedHost) return;
    queryLoading = true;
    queryData = null;
    try {
      queryData = await api.query(
        selectedHost,
        startDate || undefined,
        endDate || undefined
      );
    } catch (e) {
      console.error('Query failed', e);
      queryData = null;
    } finally {
      queryLoading = false;
    }
  }

  function selectRange(r) {
    range = r.key;
    if (r.days === null) {
      // All time: omit date filters entirely
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

  function selectHost(name) {
    selectedHost = name;
    loadQueryData();
  }

  /** Sum all values in a category object */
  function categoryTotal(category) {
    if (!queryData || !queryData[category]) return 0;
    return Object.values(queryData[category]).reduce((a, b) => a + b, 0);
  }

  function numberFormat(x) {
    if (x == null) return '0';
    return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }

  function getSortedEntries(category) {
    if (!queryData || !queryData[category]) return [];
    return Object.entries(queryData[category])
      .sort((a, b) => b[1] - a[1])
      .slice(0, 12);
  }

  function hasData(dim) {
    return queryData && queryData[dim] && Object.keys(queryData[dim]).length > 0;
  }

  function percentRepr(value, total) {
    if (!total) return 0;
    const pct = Math.round((value / total) * 100);
    if (pct === 0 && value > 0) return 0.5;
    return pct;
  }

  function percentLabel(value, total) {
    if (!total) return '0%';
    const pct = Math.round((value / total) * 100);
    if (pct === 0 && value > 0) return '<1%';
    return pct + '%';
  }

  async function handleLogout() {
    try {
      await api.logout();
      window.dispatchEvent(new CustomEvent('auth-changed', { detail: { authenticated: false } }));
    } catch (e) {
      console.error('Logout failed', e);
    }
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
        <button onclick={handleLogout} class="btn-logout">Sign out</button>
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
        <div class="site-selector">
          {#each hosts as host (host.id)}
            <button
              class="chip"
              class:active={selectedHost === host.name}
              onclick={() => selectHost(host.name)}
            >
              {host.name}
            </button>
          {/each}
        </div>
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
      </div>
    </section>

    <main class="content">
      {#if queryLoading}
        <div class="loading-indicator">Loading data...</div>
      {:else if queryData && Object.keys(queryData).length > 0}
        <!-- Summary Cards -->
        <section class="summary-cards">
          <div class="card">
            <div class="card-label">Pageviews</div>
            <div class="card-value">{numberFormat(categoryTotal('pageview'))}</div>
          </div>
          <div class="card">
            <div class="card-label">Referrers</div>
            <div class="card-value">{numberFormat(categoryTotal('ref'))}</div>
          </div>
          <div class="card">
            <div class="card-label">Countries</div>
            <div class="card-value">{numberFormat(categoryTotal('country'))}</div>
          </div>
          <div class="card">
            <div class="card-label">Browsers</div>
            <div class="card-value">{numberFormat(categoryTotal('browser'))}</div>
          </div>
        </section>

        <!-- Pages & Referrers -->
        <section class="metrics-grid">
          {#if hasData('pageview')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="3" width="18" height="18" rx="2" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M3 9H21" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M9 21V9" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <h3>Pages</h3>
            </div>
            <div class="metrics-list">
              {#each getSortedEntries('pageview') as [item, count]}
                <div class="bar-row">
                  <div class="bar-fill" style="width: {percentRepr(count, categoryTotal('pageview'))}%"></div>
                  <div class="bar-row-inner">
                    <span class="bar-label">{item}</span>
                    <span class="bar-value">{numberFormat(count)}</span>
                    <span class="bar-pct">{percentLabel(count, categoryTotal('pageview'))}</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {/if}

          {#if hasData('ref')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 3V21H21" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M18 17V9" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M13 17V5" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M8 17V11" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <h3>Referrers</h3>
            </div>
            <div class="metrics-list">
              {#each getSortedEntries('ref') as [item, count]}
                <div class="bar-row">
                  <div class="bar-fill" style="width: {percentRepr(count, categoryTotal('ref'))}%"></div>
                  <div class="bar-row-inner">
                    <span class="bar-label">{item}</span>
                    <span class="bar-value">{numberFormat(count)}</span>
                    <span class="bar-pct">{percentLabel(count, categoryTotal('ref'))}</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {/if}
        </section>

        <!-- Countries & Browsers -->
        <section class="metrics-grid">
          {#if hasData('country')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 12H22" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 2C15 2 18 5.5 18 12C18 18.5 15 22 12 22C9 22 6 18.5 6 12C6 5.5 9 2 12 2Z" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <h3>Countries</h3>
            </div>
            <div class="metrics-list">
              {#each getSortedEntries('country') as [item, count]}
                <div class="bar-row">
                  <div class="bar-fill" style="width: {percentRepr(count, categoryTotal('country'))}%"></div>
                  <div class="bar-row-inner">
                    <span class="bar-label">{item}</span>
                    <span class="bar-value">{numberFormat(count)}</span>
                    <span class="bar-pct">{percentLabel(count, categoryTotal('country'))}</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {/if}

          {#if hasData('browser')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="3" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <h3>Browsers</h3>
            </div>
            <div class="metrics-list">
              {#each getSortedEntries('browser') as [item, count]}
                <div class="bar-row">
                  <div class="bar-fill" style="width: {percentRepr(count, categoryTotal('browser'))}%"></div>
                  <div class="bar-row-inner">
                    <span class="bar-label">{item}</span>
                    <span class="bar-value">{numberFormat(count)}</span>
                    <span class="bar-pct">{percentLabel(count, categoryTotal('browser'))}</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {/if}
        </section>

        <!-- OS & Device -->
        <section class="metrics-grid">
          {#if hasData('platform')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="4" y="2" width="16" height="20" rx="2" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M9 22H15" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 17V19" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <h3>Operating Systems</h3>
            </div>
            <div class="metrics-list">
              {#each getSortedEntries('platform') as [item, count]}
                <div class="bar-row">
                  <div class="bar-fill" style="width: {percentRepr(count, categoryTotal('platform'))}%"></div>
                  <div class="bar-row-inner">
                    <span class="bar-label">{item}</span>
                    <span class="bar-value">{numberFormat(count)}</span>
                    <span class="bar-pct">{percentLabel(count, categoryTotal('platform'))}</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {/if}

          {#if hasData('device')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 4H20V16H4V4Z" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M8 20H16" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 16V20" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <h3>Devices</h3>
            </div>
            <div class="metrics-list">
              {#each getSortedEntries('device') as [item, count]}
                <div class="bar-row">
                  <div class="bar-fill" style="width: {percentRepr(count, categoryTotal('device'))}%"></div>
                  <div class="bar-row-inner">
                    <span class="bar-label">{item}</span>
                    <span class="bar-value">{numberFormat(count)}</span>
                    <span class="bar-pct">{percentLabel(count, categoryTotal('device'))}</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
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
  .navbar { background: white; border-bottom: 1px solid #e5e7eb; padding: 12px 0; }
  .navbar .content { display: flex; justify-content: space-between; align-items: center; }
  .logotype { width: 28px; height: 28px; background: #2563eb; border-radius: 6px; display: block; }
  .nav-right { display: flex; align-items: center; gap: 12px; }
  .user-name { font-size: 14px; color: #666; }
  .btn-logout { background: none; border: 1px solid #ddd; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px; }
  .btn-logout:hover { background: #f9fafb; }

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

  .toolbar { background: white; border-bottom: 1px solid #e5e7eb; padding: 12px 0; }
  .toolbar-inner { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
  .site-selector, .range-selector { display: flex; gap: 6px; flex-wrap: wrap; }
  .chip { background: #f3f4f6; border: 1px solid #e5e7eb; padding: 6px 14px; border-radius: 20px; font-size: 13px; cursor: pointer; color: #555; transition: all 0.15s; }
  .chip:hover { background: #e5e7eb; }
  .chip.active { background: #2563eb; color: white; border-color: #2563eb; }

  .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-top: 24px; }
  .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  .card-label { font-size: 13px; color: #888; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
  .card-value { font-size: 28px; font-weight: 700; font-family: 'Nunito Sans', sans-serif; color: #111; }

  .metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px; }

  .metrics-panel { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }

  .metrics-headline { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
  .metrics-headline h3 { font-size: 16px; font-family: 'Nunito Sans', sans-serif; font-weight: 700; color: #333; margin: 0; }
  .metrics-headline svg { width: 20px; height: 20px; flex-shrink: 0; }

  .metrics-list { display: flex; flex-direction: column; gap: 2px; }

  .bar-row { position: relative; display: flex; align-items: center; height: 36px; padding: 0 12px; border-radius: 18px; overflow: hidden; }
  .bar-fill { position: absolute; left: 0; top: 0; height: 100%; background: #e7f6ff; border-radius: 18px; transition: width 0.3s ease; min-width: 4px; }
  .bar-row-inner { position: relative; z-index: 1; display: flex; align-items: center; width: 100%; gap: 8px; }
  .bar-label { flex: 1; font-size: 13px; color: #444; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .bar-value { font-size: 13px; font-weight: 600; color: #111; white-space: nowrap; }
  .bar-pct { font-size: 11px; color: #888; width: 36px; text-align: right; flex-shrink: 0; }

  @media (max-width: 768px) {
    .metrics-grid { grid-template-columns: 1fr; }
  }
</style>
