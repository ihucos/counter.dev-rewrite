<script>
  import { enhance } from '$app/forms';
  import TimeRangeSelector from '$lib/components/TimeRangeSelector.svelte';
  import DomainSelector from '$lib/components/DomainSelector.svelte';
  import QueryResult from '$lib/components/QueryResult.svelte';

  let { data } = $props();
  let hosts = data.hosts || [];

  let timeRange = $state('24h');
  let domain = $state('');
  let queryResult = $state(null);
  let loading = $state(false);
  let error = $state(null);

  async function runQuery() {
    loading = true;
    error = null;
    queryResult = null;

    try {
      const formData = new FormData();
      formData.append('timeRange', timeRange);
      formData.append('domain', domain);

      const response = await fetch('/dashboard', {
        method: 'POST',
        body: formData,
      });

      const json = await response.json();
      if (json.success) {
        queryResult = json.result;
      } else {
        error = json.error || 'Query failed';
      }
    } catch (err) {
      error = err.message || 'Network error';
    } finally {
      loading = false;
    }
  }
</script>

<div class="dashboard">
  <h1>Dashboard</h1>
  
  <div class="controls">
    <div class="control-group">
      <label for="timeRange">Time Range</label>
      <TimeRangeSelector id="timeRange" bind:value={timeRange} />
    </div>
    <div class="control-group">
      <label for="domain">Domain</label>
      <DomainSelector id="domain" {hosts} bind:value={domain} />
    </div>
    <button class="btn-primary" onclick={runQuery} disabled={loading}>
      {loading ? 'Running...' : 'Run Query'}
    </button>
  </div>

  <QueryResult data={queryResult} {loading} {error} />
</div>

<style>
  .dashboard {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }
  h1 {
    margin-bottom: 1.5rem;
  }
  .controls {
    display: flex;
    gap: 1rem;
    align-items: flex-end;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
  }
  .control-group {
    flex: 1;
    min-width: 150px;
  }
  .control-group label {
    display: block;
    margin-bottom: 0.25rem;
    font-weight: 500;
    font-size: 0.875rem;
    color: var(--color-text-muted);
  }
</style>