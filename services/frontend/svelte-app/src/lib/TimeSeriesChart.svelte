<script>
  let { dateData = {}, startDate = '', endDate = '' } = $props();

  const CHART_ICON = '<path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 4-6"/>';

  function fillDateRange(dates, start, end) {
    const filled = {};
    const s = start ? new Date(start + 'T00:00:00') : new Date(Object.keys(dates).sort()[0]);
    const e = end ? new Date(end + 'T00:00:00') : new Date();
    const cur = new Date(s);
    while (cur <= e) {
      const key = cur.toISOString().slice(0, 10);
      filled[key] = dates[key] || 0;
      cur.setDate(cur.getDate() + 1);
    }
    return filled;
  }

  function groupEntries(entries) {
    if (entries.length <= 31) {
      return entries.map(([dateStr, count]) => {
        const d = new Date(dateStr + 'T00:00:00');
        const label = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        return { label, count, dateStr };
      });
    }

    const weeks = {};
    for (const [dateStr, count] of entries) {
      const d = new Date(dateStr + 'T00:00:00');
      const day = d.getDay();
      const diff = d.getDate() - day + (day === 0 ? -6 : 1);
      const monday = new Date(d);
      monday.setDate(diff);
      const weekKey = monday.toISOString().slice(0, 10);
      weeks[weekKey] = (weeks[weekKey] || 0) + count;
    }
    let weekEntries = Object.entries(weeks).sort((a, b) => a[0].localeCompare(b[0]));

    if (weekEntries.length <= 16) {
      return weekEntries.map(([dateStr, count]) => {
        const label = 'CW' + getWeekNumber(new Date(dateStr + 'T00:00:00'));
        return { label, count, dateStr };
      });
    }

    const months = {};
    for (const [dateStr, count] of entries) {
      const monthKey = dateStr.slice(0, 7);
      months[monthKey] = (months[monthKey] || 0) + count;
    }
    let monthEntries = Object.entries(months).sort((a, b) => a[0].localeCompare(b[0]));

    if (monthEntries.length <= 32) {
      return monthEntries.map(([dateStr, count]) => {
        const d = new Date(dateStr + '-01T00:00:00');
        const label = d.toLocaleDateString('en-US', { month: 'short' });
        return { label, count, dateStr };
      });
    }

    const years = {};
    for (const [dateStr, count] of entries) {
      const yearKey = dateStr.slice(0, 4);
      years[yearKey] = (years[yearKey] || 0) + count;
    }
    return Object.entries(years).sort((a, b) => a[0].localeCompare(b[0]))
      .map(([year, count]) => ({ label: year, count, dateStr: year }));
  }

  function getWeekNumber(d) {
    d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
  }

  let chartData = $derived.by(() => {
    if (Object.keys(dateData).length === 0) return [];
    const filled = fillDateRange(dateData, startDate, endDate);
    const sorted = Object.entries(filled).sort((a, b) => a[0].localeCompare(b[0]));
    return groupEntries(sorted);
  });

  let maxVal = $derived.by(() => {
    if (chartData.length === 0) return 0;
    return Math.max(...chartData.map(d => d.count), 1);
  });

  function numberFormat(x) {
    if (x == null) return '0';
    return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }

  function hasData() {
    return Object.keys(dateData).length > 0;
  }

  let labelInterval = $derived.by(() => {
    if (chartData.length <= 15) return 1;
    if (chartData.length <= 30) return 2;
    if (chartData.length <= 60) return 4;
    return Math.ceil(chartData.length / 15);
  });
</script>

{#if hasData()}
  <div class="chart-panel">
    <div class="metrics-headline">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html CHART_ICON}</svg>
      <h3>Visits over Time</h3>
      <span class="chart-total">{numberFormat(chartData.reduce((sum, d) => sum + d.count, 0))} total</span>
    </div>
    <div class="chart-container">
      {#each chartData as { label, count, dateStr }, i}
        {@const barHeight = maxVal > 0 ? Math.max((count / maxVal) * 120, 2) : 2}
        <div class="chart-bar-wrapper" title="{dateStr}: {numberFormat(count)} visits">
          <div class="chart-bar" style="height: {barHeight}px;" class:chart-bar-zero={count === 0}></div>
          <span class="chart-label" class:chart-label-hidden={i % labelInterval !== 0}>{label}</span>
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
  .chart-total {
    font-size: 12px;
    color: #888;
    margin-left: auto;
  }
  .chart-container {
    display: flex;
    align-items: flex-end;
    gap: 3px;
    height: 160px;
    padding-top: 10px;
    overflow-x: auto;
    scrollbar-width: thin;
  }
  .chart-container::-webkit-scrollbar {
    height: 4px;
  }
  .chart-container::-webkit-scrollbar-track {
    background: transparent;
  }
  .chart-container::-webkit-scrollbar-thumb {
    background: #ddd;
    border-radius: 2px;
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
  .chart-bar-zero {
    background: #e5e7eb;
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
  }
  .chart-label-hidden {
    visibility: hidden;
  }
</style>
