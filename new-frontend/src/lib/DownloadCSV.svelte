<script lang="ts">
  /**
   * Download button that exports dashboard query data as CSV.
   *
   * Props:
   *   data: Record<string, Record<string, number>> - the raw query response
   *   hostName: string - the selected site name
   *   startDate: string - start date (YYYY-MM-DD) for filename
   *   endDate: string - end date (YYYY-MM-DD) for filename
   */
  let {
    data = {} as Record<string, Record<string, number>>,
    hostName = 'unknown',
    startDate = '',
    endDate = ''
  }: {
    data: Record<string, Record<string, number>>;
    hostName: string;
    startDate: string;
    endDate: string;
  } = $props();

  let downloading = $state(false);

  function formatDate(d: string): string {
    if (!d) return 'all';
    return d.replace(/-/g, '');
  }

  function downloadCSV(): void {
    downloading = true;
    try {
      const rows: string[][] = [];
      rows.push(['category', 'item', 'count']);

      for (const [category, items] of Object.entries(data)) {
        for (const [item, count] of Object.entries(items)) {
          rows.push([category, item, String(count)]);
        }
      }

      const csvContent = rows
        .map((row) =>
          row
            .map((cell) => {
              const str = String(cell);
              if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                return '"' + str.replace(/"/g, '""') + '"';
              }
              return str;
            })
            .join(',')
        )
        .join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const filename = `counter-${hostName}-${formatDate(startDate)}_${formatDate(endDate)}.csv`;

      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } finally {
      downloading = false;
    }
  }

  function hasData(): boolean {
    return Object.keys(data).length > 0;
  }
</script>

{#if hasData()}
  <button class="btn-download" onclick={downloadCSV} disabled={downloading} title="Download data as CSV">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
    {downloading ? 'Downloading...' : 'CSV'}
  </button>
{/if}

<style>
  .btn-download {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    cursor: pointer;
    color: #555;
    transition: all 0.15s;
    font-family: inherit;
  }
  .btn-download:hover:not(:disabled) {
    background: #e5e7eb;
    color: #333;
  }
  .btn-download:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .btn-download svg {
    width: 16px;
    height: 16px;
  }
</style>
