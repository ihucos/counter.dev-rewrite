<script>
  /**
   * MetricsPanel - displays a bar chart panel for metrics data.
   * Props:
   *   title: string
   *   data: Record<string, number>
   */
  let { title = '', data = {} } = $props();

  let entries = $derived(
    Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 15)
  );

  let total = $derived(Object.values(data).reduce((a, b) => a + b, 0));

  function n(x) {
    if (x == null) return '0';
    return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }

  function pct(value) {
    if (!total) return 0;
    const p = Math.round((value / total) * 100);
    return p === 0 && value > 0 ? 1 : p;
  }

  function hasData() {
    return Object.keys(data).length > 0;
  }
</script>

{#if hasData()}
  <div class="panel">
    <h3 class="title">{title}</h3>
    <div class="list">
      {#each entries as [item, count]}
        <div class="row">
          <div class="bar" style="width: {pct(count)}%"></div>
          <div class="inner">
            <span class="label">{item}</span>
            <span class="value">{n(count)}</span>
            <span class="pct">{pct(count)}%</span>
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}

<style>
  .panel {
    background: white; border-radius: 12px; padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  .title {
    margin: 0 0 16px; font-size: 15px; font-weight: 700; color: #333;
  }
  .list { display: flex; flex-direction: column; gap: 2px; }
  .row {
    position: relative; display: flex; align-items: center;
    height: 34px; padding: 0 12px; border-radius: 17px; overflow: hidden;
  }
  .bar {
    position: absolute; left: 0; top: 0; height: 100%;
    background: #e8f0fe; border-radius: 17px; transition: width 0.3s ease;
    min-width: 4px;
  }
  .inner {
    position: relative; z-index: 1; display: flex;
    align-items: center; width: 100%; gap: 8px;
  }
  .label {
    flex: 1; font-size: 13px; color: #444; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
  }
  .value { font-size: 13px; font-weight: 600; color: #111; white-space: nowrap; }
  .pct { font-size: 11px; color: #888; width: 36px; text-align: right; flex-shrink: 0; }
</style>
