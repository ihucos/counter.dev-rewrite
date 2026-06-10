<script lang="ts">
  /**
   * MetricsPanel - displays a bar chart panel for metrics data.
   * Matches the old design with optional SVG icon support.
   *
   * Props:
   *   title: string - the panel heading
   *   icon: string (optional) - SVG path content for the icon (24x24 viewBox)
   *   data: Record<string, number> - the key-value pairs to display
   *   sortAndLimit: boolean (default true) - whether to sort descending and limit to 15
   *   valueTotal: number | null (optional) - total for percentage calc; if null, computed from data
   */
  let {
    title = '',
    icon = '',
    data = {} as Record<string, number>,
    sortAndLimit = true,
    valueTotal = null as number | null,
  }: {
    title: string;
    icon?: string;
    data: Record<string, number>;
    sortAndLimit?: boolean;
    valueTotal?: number | null;
  } = $props();

  let entries = $derived.by(() => {
    const entries = Object.entries(data);
    if (!sortAndLimit) return entries;
    return entries.sort((a, b) => b[1] - a[1]).slice(0, 15);
  });

  let total = $derived(valueTotal ?? Object.values(data).reduce((a, b) => a + b, 0));

  function n(x: number | null | undefined): string {
    if (x == null) return '0';
    return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }

  function pct(value: number): number {
    if (!total) return 0;
    const p = Math.round((value / total) * 100);
    return p === 0 && value > 0 ? 0.5 : p;
  }

  function pctLabel(value: number): string {
    if (!total) return '0%';
    const p = Math.round((value / total) * 100);
    if (p === 0 && value > 0) return '<1%';
    return p + '%';
  }

  function hasData(): boolean {
    return Object.keys(data).length > 0;
  }
</script>

{#if hasData()}
  <div class="panel">
    <div class="headline">
      {#if icon}
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html icon}</svg>
      {/if}
      <h3>{title}</h3>
    </div>
    <div class="list">
      {#each entries as [item, count]}
        <div class="row">
          <div class="bar" style="width: {pct(count)}%"></div>
          <div class="inner">
            <span class="label">{item}</span>
            <span class="value">{n(count)}</span>
            <span class="pct">{pctLabel(count)}</span>
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}

<style>
  .panel {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  .headline {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
  }
  .headline h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 700;
    color: #333;
  }
  .headline svg {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }
  .list {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .row {
    position: relative;
    display: flex;
    align-items: center;
    height: 36px;
    padding: 0 12px;
    border-radius: 18px;
    overflow: hidden;
  }
  .bar {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    background: #e7f6ff;
    border-radius: 18px;
    transition: width 0.3s ease;
    min-width: 4px;
  }
  .inner {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    width: 100%;
    gap: 8px;
  }
  .label {
    flex: 1;
    font-size: 13px;
    color: #444;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .value {
    font-size: 13px;
    font-weight: 600;
    color: #111;
    white-space: nowrap;
  }
  .pct {
    font-size: 11px;
    color: #888;
    width: 36px;
    text-align: right;
    flex-shrink: 0;
  }
</style>
