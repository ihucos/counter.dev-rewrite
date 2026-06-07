<script>
  /**
   * A bar chart showing visits over time (date range).
   *
   * Props:
   *   dateData: Record<string, number> - the raw date -> count mapping
   *   startDate: string - start date (YYYY-MM-DD), for filling gaps
   *   endDate: string - end date (YYYY-MM-DD), for filling gaps
   */
  let { dateData = {}, startDate = '', endDate = '' } = $props();

  const CHART_ICON = '<path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/>';

  /**
   * Fill in missing dates between start and end so the time-series chart
   * has a contiguous range.
   */
  function fillDateRange(dates, start, end) {
    const filled = {};
    const s = start ? new Date(start) : new Date(Object.keys(dates).sort()[0]);
    const e = end ? new Date(end) : new Date();
    const cur = new Date(s);
    while (cur <= e) {
      const key = cur.toISOString().slice(0, 10);
      filled[key] = dates[key] || 0;
      cur.setDate(cur.getDate() + 1);
    }
    return filled;
  }

  let dateEntries = $derived.by(() => {
    if (Object.keys(dateData).length === 0) return [];
    const filled = fillDateRange(dateData, startDate, endDate);
    return Object.entries(filled).sort((a, b) => a[0].localeCompare(b[0]));
  });

  let maxVal = $derived.by(() => {
    if (dateEntries.length === 0) return 0;
    return Math.max(...dateEntries.map(([, v]) => v), 1);
  });

  /** Format a YYYY-MM-DD date to a short label (e.g. "Jan 5") */
  function shortDate(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  function numberFormat(x) {
    if (x == null) return '0';
    return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }

  function hasData() {
    return Object.keys(dateData).length > 0;
  }
</script>

{#if hasData()}
  <div class="chart-panel">
    <div class="metrics-headline">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html CHART_ICON}</svg>
      <h3>Visits over Time</h3>
    </div>
    <div class="chart-container">
      {#each dateEntries as [dateStr, count]}
        {@const barHeight = maxVal > 0 ? Math.max((count / maxVal) * 120, 2) : 2}
        <div class="chart-bar-wrapper" title="{dateStr}: {numberFormat(count)} visits">
          <div class="chart-bar" style="height: {barHeight}px;"></div>
          <span class="chart-label">{shortDate(dateStr)}</span>
        </div>
      {/each}
    </div>
  </div>
{/if}

<style>
  .chart-panel {
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
  .chart-container {
    display: flex;
    align-items: flex-end;
    gap: 3px;
    height: 160px;
    padding-top: 10px;
    overflow-x: auto;
  }
  .chart-bar-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1 0 auto;
    min-width: 28px;
  }
  .chart-bar {
    width: 100%;
    max-width: 32px;
    background: linear-gradient(180deg, #2563eb 0%, #60a5fa 100%);
    border-radius: 3px 3px 0 0;
    transition: height 0.3s ease;
    min-height: 2px;
  }
  .chart-bar-wrapper:hover .chart-bar {
    background: linear-gradient(180deg, #1d4ed8 0%, #3b82f6 100%);
  }
  .chart-label {
    font-size: 9px;
    color: #999;
    margin-top: 4px;
    white-space: nowrap;
    transform: rotate(-30deg);
    transform-origin: left center;
  }
</style>
