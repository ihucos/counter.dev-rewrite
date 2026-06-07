<script>
  /**
   * Download button that exports dashboard query data as CSV.
   *
   * Props:
   *   data: Record<string, Record<string, number>> - the raw query response (category -> {item: count})
   *   hostName: string - the selected site name
   *   startDate: string - start date (YYYY-MM-DD) for filename
   *   endDate: string - end date (YYYY-MM-DD) for filename
   */
  let { data = {}, hostName = 'unknown', startDate = '', endDate = '' } = $props();

  let downloading = $state(false);

  function formatDate(d) {
    if (!d) return 'all';
    return d.replace(/-/g, '');
  }

  function downloadCSV() {
    downloading = true;
    try {
      const rows = [];
      // Header row
      rows.push(['category', 'item', 'count']);

      for (const [category, items] of Object.entries(data)) {
        for (const [item, count] of Object.entries(items)) {
          rows.push([category, item, String(count)]);
        }
      }

      // Build CSV content
      const csvContent = rows
        .map((row) =>
          row
            .map((cell) => {
              // Escape quotes and wrap in quotes if contains comma, quote, or newline
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

  function hasData() {
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
