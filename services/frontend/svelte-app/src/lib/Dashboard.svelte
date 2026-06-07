<script>
  import { api } from '$lib/api.js';
  import { onMount } from 'svelte';
  import Settings from '$lib/Settings.svelte';

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
        selectedHostId = hosts[0].id;
        await loadQueryData();
      }
    } catch (e) {
      error = e.message || 'Failed to load data';
    } finally {
      loading = false;
    }
  });

  async function loadQueryData() {
    if (!selectedHostName) return;
    queryLoading = true;
    queryData = null;
    try {
      queryData = await api.query(
        selectedHostName,
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
      .slice(0, 15);
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

  /** Forward logout event to App.svelte via window custom event */
  function handleAuthChanged(event) {
    if (!event.detail.authenticated) {
      window.dispatchEvent(new CustomEvent('auth-changed', { detail: { authenticated: false } }));
    }
  }

  // Time helpers
  const HOUR_LABELS = {
    0: '12 a.m.', 1: '1 a.m.', 2: '2 a.m.', 3: '3 a.m.',
    4: '4 a.m.', 5: '5 a.m.', 6: '6 a.m.', 7: '7 a.m.',
    8: '8 a.m.', 9: '9 a.m.', 10: '10 a.m.', 11: '11 a.m.',
    12: '12 noon', 13: '1 p.m.', 14: '2 p.m.', 15: '3 p.m.',
    16: '4 p.m.', 17: '5 p.m.', 18: '6 p.m.', 19: '7 p.m.',
    20: '8 p.m.', 21: '9 p.m.', 22: '10 p.m.', 23: '11 p.m.',
  };

  function getNormalizedHours(hours) {
    if (!hours) return [];
    const pad = Object.fromEntries([...Array(24).keys()].map(i => [HOUR_LABELS[i], 0]));
    const formatted = Object.fromEntries(
      Object.entries(hours).map(([k, v]) => [HOUR_LABELS[k] || k, v])
    );
    const merged = { ...pad, ...formatted };
    return Object.entries(merged);
  }

  const WEEKDAY_LABELS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  function getNormalizedWeekdays(weekdayData) {
    if (!weekdayData) return [];
    return WEEKDAY_LABELS.map((label, idx) => {
      const key = String(idx);
      return [label, weekdayData[key] || 0];
    });
  }

  // Icon paths helper
  const ICONS = {
    page: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
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
</script>

<div class="dashboard">
  <nav class="navbar">
    <div class="content">
      <a href="/" class="logotype" aria-label="Counter home"></a>
      <div class="nav-right">
        {#if user}
          <span class="user-name">{user.username}</span>
        {/if}
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
        <section class="summary-cards">
          <div class="card">
            <div class="card-label">Pageviews</div>
            <div class="card-value">{numberFormat(categoryTotal('page'))}</div>
          </div>
          <div class="card">
            <div class="card-label">Visitors</div>
            <div class="card-value">{numberFormat(categoryTotal('visitor'))}</div>
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

        <section class="metrics-grid">
          {#if hasData('page')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html ICONS.page}</svg>
              <h3>Pages</h3>
            </div>
            <div class="metrics-list">
              {#each getSortedEntries('page') as [item, count]}
                <div class="bar-row">
                  <div class="bar-fill" style="width: {percentRepr(count, categoryTotal('page'))}%"></div>
                  <div class="bar-row-inner">
                    <span class="bar-label">{item}</span>
                    <span class="bar-value">{numberFormat(count)}</span>
                    <span class="bar-pct">{percentLabel(count, categoryTotal('page'))}</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {/if}

          {#if hasData('ref')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html ICONS.ref}</svg>
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

        <section class="metrics-grid">
          {#if hasData('country')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html ICONS.country}</svg>
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
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html ICONS.browser}</svg>
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

        <section class="metrics-grid">
          {#if hasData('platform')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html ICONS.platform}</svg>
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
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html ICONS.device}</svg>
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

        <section class="metrics-grid">
          {#if hasData('lang')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html ICONS.lang}</svg>
              <h3>Languages</h3>
            </div>
            <div class="metrics-list">
              {#each getSortedEntries('lang') as [item, count]}
                <div class="bar-row">
                  <div class="bar-fill" style="width: {percentRepr(count, categoryTotal('lang'))}%"></div>
                  <div class="bar-row-inner">
                    <span class="bar-label">{item}</span>
                    <span class="bar-value">{numberFormat(count)}</span>
                    <span class="bar-pct">{percentLabel(count, categoryTotal('lang'))}</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {/if}

          {#if hasData('screen')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html ICONS.screen}</svg>
              <h3>Screens</h3>
            </div>
            <div class="metrics-list">
              {#each getSortedEntries('screen') as [item, count]}
                <div class="bar-row">
                  <div class="bar-fill" style="width: {percentRepr(count, categoryTotal('screen'))}%"></div>
                  <div class="bar-row-inner">
                    <span class="bar-label">{item}</span>
                    <span class="bar-value">{numberFormat(count)}</span>
                    <span class="bar-pct">{percentLabel(count, categoryTotal('screen'))}</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {/if}
        </section>

        <section class="metrics-grid">
          {#if hasData('hour')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html ICONS.hour}</svg>
              <h3>Hour</h3>
            </div>
            <div class="metrics-list">
              {#each getNormalizedHours(queryData.hour) as [label, count]}
                <div class="bar-row">
                  <div class="bar-fill" style="width: {percentRepr(count, categoryTotal('hour'))}%"></div>
                  <div class="bar-row-inner">
                    <span class="bar-label">{label}</span>
                    <span class="bar-value">{numberFormat(count)}</span>
                    <span class="bar-pct">{percentLabel(count, categoryTotal('hour'))}</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {/if}

          {#if hasData('weekday')}
          <div class="metrics-panel">
            <div class="metrics-headline">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html ICONS.weekday}</svg>
              <h3>Day of Week</h3>
            </div>
            <div class="metrics-list">
              {#each getNormalizedWeekdays(queryData.weekday) as [label, count]}
                <div class="bar-row">
                  <div class="bar-fill" style="width: {percentRepr(count, categoryTotal('weekday'))}%"></div>
                  <div class="bar-row-inner">
                    <span class="bar-label">{label}</span>
                    <span class="bar-value">{numberFormat(count)}</span>
                    <span class="bar-pct">{percentLabel(count, categoryTotal('weekday'))}</span>
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

  .toolbar { background: white; border-bottom: 1px solid #e5e7eb; padding: 12px 0; position: sticky; top: 53px; z-index: 99; }
  .toolbar-inner { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
  .site-selector, .range-selector { display: flex; gap: 6px; flex-wrap: wrap; }
  .chip { background: #f3f4f6; border: 1px solid #e5e7eb; padding: 6px 14px; border-radius: 20px; font-size: 13px; cursor: pointer; color: #555; transition: all 0.15s; }
  .chip:hover { background: #e5e7eb; }
  .chip.active { background: #2563eb; color: white; border-color: #2563eb; }

  .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-top: 24px; }
  .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  .card-label { font-size: 13px; color: #888; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
  .card-value { font-size: 28px; font-weight: 700; font-family: 'Nunito Sans', sans-serif; color: #111; }

  .metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px; margin-bottom: 24px; }

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
    .toolbar-inner { flex-direction: column; }
  }
</style>
