<script lang="ts">
  /**
   * Displays recent visit log entries from the tracker's Redis logs.
   *
   * Props:
   *   logs: Array - visit log entries
   *   hostName: string - currently selected host
   */
  interface LogEntry {
    timestamp: string;
    date: string;
    time: string;
    country: string;
    referrer: string;
    device: string;
    platform: string;
    site: string;
    extra: string;
  }

  let { logs = [] as LogEntry[], hostName = '' }: { logs: LogEntry[]; hostName: string } = $props();

  let filteredLogs = $derived.by(() => {
    if (!logs || logs.length === 0) return [];
    if (hostName) {
      return logs.filter(l => l.site === hostName).slice(0, 50);
    }
    return logs.slice(0, 50);
  });

  function hasData(): boolean {
    return filteredLogs.length > 0;
  }

  function formatReferrer(referrer: string): string {
    if (!referrer || referrer === '-') return '-';
    try {
      const url = new URL(referrer.startsWith('http') ? referrer : 'https://' + referrer);
      return url.hostname;
    } catch {
      return referrer;
    }
  }

  function getDeviceIcon(device: string): string {
    const d = (device || '').toLowerCase();
    const icons: Record<string, string> = {
      'phone': 'M17 1.01L7 1c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V3c0-1.1-.9-1.99-2-1.99zM17 19H7V5h10v14z',
      'tablet': 'M18.5 0h-14A2.5 2.5 0 0 0 2 2.5v19A2.5 2.5 0 0 0 4.5 24h14a2.5 2.5 0 0 0 2.5-2.5v-19A2.5 2.5 0 0 0 18.5 0zm-7 23c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm7.5-4H4V3h15v16z',
      'computer': 'M20 18c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2H0v2h24v-2h-4zM4 6h16v10H4V6z',
      'tv': 'M21 3H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h5v2h8v-2h5c1.1 0 1.99-.9 1.99-2L23 5c0-1.1-.9-2-2-2zm0 14H3V5h18v12z',
      'console': 'M21.5 0h-19A2.5 2.5 0 0 0 0 2.5v19A2.5 2.5 0 0 0 2.5 24h19a2.5 2.5 0 0 0 2.5-2.5v-19A2.5 2.5 0 0 0 21.5 0zM12 22c-5.52 0-10-4.48-10-10S6.48 2 12 2s10 4.48 10 10-4.48 10-10 10zm-4-6h8v2H8v-2zm0-3h8v2H8v-2zm0-3h8v2H8v-2zm-3-2h2v2H5V8zm0 3h2v2H5v-2z',
      'wearable': 'M20 8h-2.81c-.45-.78-1.07-1.45-1.82-1.96L17 4.41 15.59 3l-2.17 2.17C12.96 5.06 12.49 5 12 5c-.49 0-.96.06-1.41.17L8.41 3 7 4.41l1.62 1.63C7.88 6.55 7.26 7.22 6.81 8H4v2h2.09c-.05.33-.09.66-.09 1v1H4v2h2v1c0 .34.04.67.09 1H4v2h2.81c1.04 1.79 2.97 3 5.19 3s4.15-1.21 5.19-3H20v-2h-2.09c.05-.33.09-.66.09-1v-1h2v-2h-2v-1c0-.34-.04-.67-.09-1H20V8zm-6 8h-4v-2h4v2zm0-4h-4v-2h4v2z',
      'unknown': 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z',
    };
    return icons[d] || icons['unknown'];
  }

  function getCountryFlag(code: string): string {
    if (!code || code === 'xx' || code === '') return '';
    const c = code.toUpperCase();
    const offset = 0x1F1E6 - 65;
    return String.fromCodePoint(c.charCodeAt(0) + offset, c.charCodeAt(1) + offset);
  }

  function formatTimestamp(date: string, time: string): string {
    if (!date) return '';
    const today = new Date().toISOString().slice(0, 10);
    if (date === today && time) return time;
    return date + (time ? ' ' + time : '');
  }
</script>

{#if hasData()}
  <div class="logs-panel">
    <div class="metrics-headline">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9E9E9E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H15"/>
        <path d="M10 17L15 12L10 7"/>
        <path d="M15 12H3"/>
      </svg>
      <h3>Recent Visits</h3>
      <span class="log-count">{filteredLogs.length} entries</span>
    </div>
    <div class="logs-table-wrapper">
      <table class="logs-table">
        <thead>
          <tr>
            <th class="col-time">Time</th>
            <th class="col-country"></th>
            <th class="col-referrer">Referrer</th>
            <th class="col-device">Device</th>
            <th class="col-platform">Platform</th>
            <th class="col-site">Site</th>
          </tr>
        </thead>
        <tbody>
          {#each filteredLogs as log}
            <tr>
              <td class="col-time">{formatTimestamp(log.date, log.time)}</td>
              <td class="col-country">
                {#if getCountryFlag(log.country)}
                  <span class="flag" title={log.country.toUpperCase()}>{getCountryFlag(log.country)}</span>
                {:else}
                  <span class="flag flag-unknown" title="Unknown">🌐</span>
                {/if}
              </td>
              <td class="col-referrer" title={log.referrer}>{formatReferrer(log.referrer)}</td>
              <td class="col-device">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="#666" title={(log.device || 'Unknown')}>
                  <path d={getDeviceIcon(log.device)}/>
                </svg>
                <span class="device-label">{log.device || 'Unknown'}</span>
              </td>
              <td class="col-platform">{log.platform || '-'}</td>
              <td class="col-site">{log.site}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
{/if}

<style>
  .logs-panel { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-top: 24px; }
  .metrics-headline { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
  .metrics-headline h3 { font-size: 16px; font-weight: 700; color: #333; margin: 0; }
  .metrics-headline svg { width: 20px; height: 20px; flex-shrink: 0; }
  .log-count { font-size: 12px; color: #888; margin-left: auto; }
  .logs-table-wrapper { overflow-x: auto; scrollbar-width: thin; }
  .logs-table-wrapper::-webkit-scrollbar { height: 4px; }
  .logs-table-wrapper::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }
  .logs-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .logs-table th { text-align: left; padding: 8px 12px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; border-bottom: 1px solid #e5e7eb; font-weight: 600; }
  .logs-table td { padding: 8px 12px; border-bottom: 1px solid #f3f4f6; color: #555; }
  .logs-table tbody tr:hover { background: #f9fafb; }
  .col-time { white-space: nowrap; color: #888; font-size: 12px; width: 110px; }
  .col-country { width: 36px; text-align: center; }
  .col-referrer { min-width: 120px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .col-device { white-space: nowrap; width: 120px; }
  .col-platform { white-space: nowrap; width: 100px; }
  .col-site { white-space: nowrap; width: 130px; font-size: 12px; color: #888; }
  .flag { font-size: 16px; line-height: 1; }
  .flag-unknown { font-size: 14px; }
  .device-label { margin-left: 4px; font-size: 12px; vertical-align: middle; }
</style>
