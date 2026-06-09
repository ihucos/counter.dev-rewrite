<script lang="ts">
  /**
   * Time Section Component
   * Shows hour-by-hour, day-of-week, and time-of-day breakdowns with tab switching.
   *
   * Props:
   *   hourData: Record<string, number> - hourly counts (keys: 0-23)
   *   weekdayData: Record<string, number> - weekday counts (keys: 0-6, 0=Sunday)
   */
  let {
    hourData = {} as Record<string, number>,
    weekdayData = {} as Record<string, number>
  }: {
    hourData: Record<string, number>;
    weekdayData: Record<string, number>;
  } = $props();

  let activeTab = $state('hour');

  const HOUR_LABELS: Record<number, string> = {
    0: '12 a.m.', 1: '1 a.m.', 2: '2 a.m.', 3: '3 a.m.',
    4: '4 a.m.', 5: '5 a.m.', 6: '6 a.m.', 7: '7 a.m.',
    8: '8 a.m.', 9: '9 a.m.', 10: '10 a.m.', 11: '11 a.m.',
    12: '12 noon', 13: '1 p.m.', 14: '2 p.m.', 15: '3 p.m.',
    16: '4 p.m.', 17: '5 p.m.', 18: '6 p.m.', 19: '7 p.m.',
    20: '8 p.m.', 21: '9 p.m.', 22: '10 p.m.', 23: '11 p.m.',
  };

  const WEEKDAY_LABELS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  function n(x: number | null | undefined): string {
    if (x == null) return '0';
    return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ',');
  }

  let normalizedHours = $derived.by(() => {
    const pad: Record<number, number> = {};
    for (let i = 0; i < 24; i++) pad[i] = 0;
    const data = { ...pad };
    for (const [k, v] of Object.entries(hourData || {})) {
      data[Number(k)] = v as number;
    }
    return data;
  });

  let hourEntries = $derived.by(() => {
    return Object.entries(normalizedHours).map(([hour, count]) => ({
      hour: Number(hour),
      label: HOUR_LABELS[Number(hour)] || `${hour}:00`,
      count: count as number,
    }));
  });

  let maxHourCount = $derived(Math.max(...hourEntries.map(e => e.count), 1));

  let normalizedWeekdays = $derived.by(() => {
    const pad: Record<number, number> = {};
    WEEKDAY_LABELS.forEach((_, idx) => { pad[idx] = 0; });
    const data = { ...pad };
    for (const [k, v] of Object.entries(weekdayData || {})) {
      data[Number(k)] = v as number;
    }
    return data;
  });

  let weekdayEntries = $derived.by(() => {
    return Object.entries(normalizedWeekdays).map(([idx, count]) => ({
      idx: Number(idx),
      label: WEEKDAY_LABELS[Number(idx)] || `Day ${idx}`,
      count: count as number,
    }));
  });

  let maxWeekdayCount = $derived(Math.max(...weekdayEntries.map(e => e.count), 1));

  interface DayPart { label: string; hours: number[]; count: number; }
  let dayParts = $derived.by(() => {
    const morning: DayPart = { label: 'Morning (6–12)', hours: [6, 7, 8, 9, 10, 11], count: 0 };
    const afternoon: DayPart = { label: 'Afternoon (12–18)', hours: [12, 13, 14, 15, 16, 17], count: 0 };
    const evening: DayPart = { label: 'Evening (18–24)', hours: [18, 19, 20, 21, 22, 23], count: 0 };
    const night: DayPart = { label: 'Night (0–6)', hours: [0, 1, 2, 3, 4, 5], count: 0 };

    for (const [k, v] of Object.entries(normalizedHours)) {
      const hour = Number(k);
      const count = v as number;
      if (hour >= 6 && hour < 12) morning.count += count;
      else if (hour >= 12 && hour < 18) afternoon.count += count;
      else if (hour >= 18 && hour < 24) evening.count += count;
      else night.count += count;
    }
    return [morning, afternoon, evening, night];
  });

  let maxDayPartCount = $derived(Math.max(...dayParts.map(d => d.count), 1));

  function hasHourData(): boolean { return Object.keys(hourData || {}).length > 0; }
  function hasWeekdayData(): boolean { return Object.keys(weekdayData || {}).length > 0; }
  function hasData(): boolean { return hasHourData() || hasWeekdayData(); }
</script>

{#if hasData()}
  <div class="time-section-panel">
    <div class="metrics-headline">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
      </svg>
      <h3>Time</h3>
    </div>

    <div class="tab-bar">
      <button class="tab-btn" class:active={activeTab === 'day'} onclick={() => activeTab = 'day'}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="5"/><path d="M12 1v2"/><path d="M12 21v2"/><path d="M4.22 4.22l1.42 1.42"/><path d="M18.36 18.36l1.42 1.42"/><path d="M1 12h2"/><path d="M21 12h2"/><path d="M4.22 19.78l1.42-1.42"/><path d="M18.36 5.64l1.42-1.42"/>
        </svg>
        <span>Day</span>
      </button>
      <button class="tab-btn" class:active={activeTab === 'hour'} onclick={() => activeTab = 'hour'}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
        </svg>
        <span>Hour</span>
      </button>
      <button class="tab-btn" class:active={activeTab === 'week'} onclick={() => activeTab = 'week'}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>
        </svg>
        <span>Week</span>
      </button>
    </div>

    {#if activeTab === 'day'}
      <div class="tab-content">
        <div class="part-bars">
          {#each dayParts as part}
            <div class="part-row">
              <div class="part-label">{part.label}</div>
              <div class="part-bar-track">
                <div class="part-bar-fill" style="width: {maxDayPartCount > 0 ? (part.count / maxDayPartCount) * 100 : 0}%"></div>
              </div>
              <div class="part-value">{n(part.count)}</div>
              <div class="part-pct">{maxDayPartCount > 0 ? Math.round((part.count / maxDayPartCount) * 100) : 0}%</div>
            </div>
          {/each}
        </div>
      </div>
    {:else if activeTab === 'hour'}
      <div class="tab-content">
        <div class="hour-chart">
          {#each hourEntries as entry}
            <div class="hour-bar-wrapper" title="{entry.label}: {n(entry.count)} visits">
              <div class="hour-bar" style="height: {Math.max((entry.count / maxHourCount) * 100, 2)}px" class:zero={entry.count === 0}></div>
              <span class="hour-label">
                {#if entry.hour === 0}12a
                {:else if entry.hour === 12}12n
                {:else if entry.hour < 12}{entry.hour}a
                {:else}{entry.hour - 12}p
                {/if}
              </span>
            </div>
          {/each}
        </div>
      </div>
    {:else if activeTab === 'week'}
      <div class="tab-content">
        <div class="weekday-chart">
          {#each weekdayEntries as entry}
            <div class="weekday-bar-wrapper" title="{entry.label}: {n(entry.count)} visits">
              <div class="weekday-bar" style="height: {Math.max((entry.count / maxWeekdayCount) * 100, 2)}px" class:zero={entry.count === 0}></div>
              <span class="weekday-label">{entry.label.slice(0, 3)}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </div>
{/if}

<style>
  .time-section-panel {
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
    font-weight: 700;
    color: #333;
    margin: 0;
  }
  .metrics-headline svg {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }
  .tab-bar {
    display: flex;
    gap: 4px;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 16px;
  }
  .tab-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border: none;
    background: none;
    font-size: 13px;
    color: #888;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    transition: all 0.15s;
    font-family: inherit;
  }
  .tab-btn:hover { color: #555; background: #f9fafb; border-radius: 6px 6px 0 0; }
  .tab-btn.active { color: #2563eb; border-bottom-color: #2563eb; font-weight: 600; }
  .tab-btn svg { width: 16px; height: 16px; }
  .tab-content { min-height: 120px; }
  .part-bars { display: flex; flex-direction: column; gap: 12px; padding: 8px 0; }
  .part-row { display: flex; align-items: center; gap: 12px; }
  .part-label { font-size: 13px; color: #555; width: 150px; flex-shrink: 0; }
  .part-bar-track { flex: 1; height: 28px; background: #f3f4f6; border-radius: 14px; overflow: hidden; }
  .part-bar-fill { height: 100%; background: linear-gradient(90deg, #2563eb, #60a5fa); border-radius: 14px; transition: width 0.3s ease; min-width: 4px; }
  .part-value { font-size: 14px; font-weight: 600; color: #111; width: 60px; text-align: right; }
  .part-pct { font-size: 12px; color: #888; width: 40px; text-align: right; }
  .hour-chart { display: flex; align-items: flex-end; gap: 3px; height: 130px; padding: 8px 0; overflow-x: auto; }
  .hour-chart::-webkit-scrollbar { height: 4px; }
  .hour-chart::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }
  .hour-bar-wrapper { display: flex; flex-direction: column; align-items: center; flex: 1 0 auto; min-width: 28px; }
  .hour-bar { width: 100%; max-width: 28px; background: linear-gradient(180deg, #2563eb 0%, #60a5fa 100%); border-radius: 3px 3px 0 0; transition: height 0.3s ease; min-height: 2px; }
  .hour-bar.zero { background: #e5e7eb; min-height: 2px; }
  .hour-bar-wrapper:hover .hour-bar { background: linear-gradient(180deg, #1d4ed8 0%, #3b82f6 100%); }
  .hour-label { font-size: 9px; color: #999; margin-top: 4px; white-space: nowrap; }
  .weekday-chart { display: flex; align-items: flex-end; gap: 8px; height: 130px; padding: 8px 12px; }
  .weekday-bar-wrapper { display: flex; flex-direction: column; align-items: center; flex: 1; }
  .weekday-bar { width: 100%; max-width: 48px; background: linear-gradient(180deg, #2563eb 0%, #60a5fa 100%); border-radius: 3px 3px 0 0; transition: height 0.3s ease; min-height: 2px; }
  .weekday-bar.zero { background: #e5e7eb; min-height: 2px; }
  .weekday-bar-wrapper:hover .weekday-bar { background: linear-gradient(180deg, #1d4ed8 0%, #3b82f6 100%); }
  .weekday-label { font-size: 10px; color: #999; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
</style>
