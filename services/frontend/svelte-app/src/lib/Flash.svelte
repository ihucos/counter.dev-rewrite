<script>
  /**
   * Flash notification component for showing temporary messages.
   * Renders a toast at the top of the page that auto-dismisses.
   *
   * Flash messages can be dispatched via:
   *   window.dispatchEvent(new CustomEvent('flash', { detail: { message: '...', type: 'success'|'error'|'info' } }));
   *
   * Props:
   *   duration: number - milliseconds to show the notification (default: 4000)
   */
  let { duration = 4000 } = $props();

  let messages = $state([]);
  let idCounter = 0;

  function addMessage(message, type = 'info') {
    const id = ++idCounter;
    messages = [...messages, { id, message, type }];
    setTimeout(() => {
      removeMessage(id);
    }, duration);
  }

  function removeMessage(id) {
    messages = messages.filter(m => m.id !== id);
  }

  function handleFlashEvent(event) {
    const { message, type } = event.detail || {};
    if (message) {
      addMessage(message, type || 'info');
    }
  }

  $effect(() => {
    window.addEventListener('flash', handleFlashEvent);
    return () => window.removeEventListener('flash', handleFlashEvent);
  });
</script>

{#if messages.length > 0}
  <div class="flash-container" role="alert" aria-live="polite">
    {#each messages as msg (msg.id)}
      <div class="flash-toast flash-{msg.type}">
        <span class="flash-message">{msg.message}</span>
        <button class="flash-close" onclick={() => removeMessage(msg.id)} aria-label="Dismiss">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    {/each}
  </div>
{/if}

<style>
  .flash-container {
    position: fixed;
    top: 16px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 90%;
    max-width: 480px;
    pointer-events: none;
  }

  .flash-toast {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    pointer-events: auto;
    animation: slideIn 0.25s ease-out;
    font-size: 14px;
    line-height: 1.4;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-12px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .flash-info {
    background: #eff6ff;
    color: #1e40af;
    border: 1px solid #bfdbfe;
  }

  .flash-success {
    background: #d1fae5;
    color: #065f46;
    border: 1px solid #a7f3d0;
  }

  .flash-error {
    background: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
  }

  .flash-message {
    flex: 1;
  }

  .flash-close {
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    color: inherit;
    opacity: 0.6;
    flex-shrink: 0;
    display: flex;
    align-items: center;
  }

  .flash-close:hover {
    opacity: 1;
  }
</style>
