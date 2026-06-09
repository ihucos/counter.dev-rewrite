<script lang="ts">
  /**
   * A small indicator showing the connection status to the API.
   *
   * Props:
   *   status: string - current status ('checking', 'connected', 'disconnected')
   */
  let { status = 'checking' }: { status: string } = $props();

  let statusText = $derived.by(() => {
    switch (status) {
      case 'connected': return 'Live';
      case 'connecting': return 'Connecting...';
      case 'disconnected': return 'Disconnected';
      case 'checking': return 'Checking...';
      default: return status;
    }
  });

  let statusClass = $derived.by(() => {
    switch (status) {
      case 'connected': return 'status-live';
      case 'connecting': case 'checking': return 'status-pending';
      case 'disconnected': return 'status-error';
      default: return 'status-pending';
    }
  });
</script>

<span class="conn-status {statusClass}" title="Connection status: {statusText}">
  <span class="conn-dot"></span>
  <span class="conn-label">{statusText}</span>
</span>

<style>
  .conn-status {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    padding: 3px 10px;
    border-radius: 12px;
    white-space: nowrap;
  }
  .conn-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    display: inline-block;
  }
  .conn-label {
    font-weight: 500;
  }
  .status-live {
    background: #d1fae5;
    color: #065f46;
  }
  .status-live .conn-dot {
    background: #059669;
  }
  .status-pending {
    background: #fef3c7;
    color: #92400e;
  }
  .status-pending .conn-dot {
    background: #d97706;
  }
  .status-error {
    background: #fef2f2;
    color: #991b1b;
  }
  .status-error .conn-dot {
    background: #dc2626;
  }
</style>
