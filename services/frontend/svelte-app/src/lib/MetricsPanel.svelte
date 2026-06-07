<script>
  /**
   * Displays a panel with a title, icon, and a list of bar rows for metrics data.
   *
   * Props:
   *   title: string - the panel heading
   *   icon: string - SVG path content for the icon (24x24 viewBox)
   *   data: Record<string, number> - the key-value pairs to display
   *   sortAndLimit: boolean (default true) - whether to sort descending and limit to 15
   *   valueTotal: number | null (optional) - total for percentage calc; if null, computed from data
   */
  let { title = '', icon = '', data = {}, sortAndLimit = true, valueTotal = null } = $props();

  let entries = $derived.by(() => {
    const entries = Object.entries(data);
    if (!sortAndLimit) return entries;
    return entries.sort((a, b) => b[1] - a[1]).slice(0, 15);
  });

  let total = $derived(valueTotal ?? Object.values(data).reduce((a, b) => a + b, 0));

  function numberFormat(x) {
    if (x == null) return '0';
    return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }

  function percentRepr(value, totalVal) {
    if (!totalVal) return 0;
    const pct = Math.round((value / totalVal) * 100);
    if (pct === 0 && value > 0) return 0.5;
    return pct;
  }

  function percentLabel(value, totalVal) {
    if (!totalVal) return '0%';
    const pct = Math.round((value / totalVal) * 100);
    if (pct === 0 && value > 0) return '<1%';
    return pct + '%';
  }

  function hasData() {
    return Object.keys(data).length > 0;
  }
</script>

{#if hasData()}
  <div class="metrics-panel">
    <div class="metrics-headline">
      {#if icon}
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html icon}</svg>
      {/if}
      <h3>{title}</h3>
    </div>
    <div class="metrics-list">
      {#each entries as [item, count]}
        <div class="bar-row">
          <div class="bar-fill" style="width: {percentRepr(count, total)}%"></div>
          <div class="bar-row-inner">
            <span class="bar-label">{item}</span>
            <span class="bar-value">{numberFormat(count)}</span>
            <span class="bar-pct">{percentLabel(count, total)}</span>
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}

<style>
  .metrics-panel {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }

  .metrics-headline {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
  }
  .metrics-headline h3 {
    font-size: 16px;
    font-family: 'Nunito Sans', sans-serif;
    font-weight: 700;
    color: #333;
    margin: 0;
  }
  .metrics-headline svg {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }

  .metrics-list {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .bar-row {
    position: relative;
    display: flex;
    align-items: center;
    height: 36px;
    padding: 0 12px;
    border-radius: 18px;
    overflow: hidden;
  }
  .bar-fill {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    background: #e7f6ff;
    border-radius: 18px;
    transition: width 0.3s ease;
    min-width: 4px;
  }
  .bar-row-inner {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    width: 100%;
    gap: 8px;
  }
  .bar-label {
    flex: 1;
    font-size: 13px;
    color: #444;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .bar-value {
    font-size: 13px;
    font-weight: 600;
    color: #111;
    white-space: nowrap;
  }
  .bar-pct {
    font-size: 11px;
    color: #888;
    width: 36px;
    text-align: right;
    flex-shrink: 0;
  }
</style>
