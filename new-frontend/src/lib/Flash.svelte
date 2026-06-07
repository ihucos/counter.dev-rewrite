<script lang="ts">
  interface FlashMessage {
    id: number;
    msg: string;
    type: string;
  }

  interface FlashEventDetail {
    message?: string;
    type?: string;
  }

  interface FlashEvent extends CustomEvent {
    detail: FlashEventDetail;
  }

  let messages = $state<FlashMessage[]>([]);
  let nextId = 0;

  function add(msg: string, type: string = 'info'): void {
    const id = ++nextId;
    messages = [...messages, { id, msg, type }];
    setTimeout(() => { messages = messages.filter(m => m.id !== id); }, 4000);
  }

  function remove(id: number): void {
    messages = messages.filter(m => m.id !== id);
  }

  function handler(e: Event): void {
    const event = e as FlashEvent;
    const { message, type } = event.detail || {};
    if (message) add(message, type || 'info');
  }

  $effect(() => {
    window.addEventListener('flash', handler);
    return () => window.removeEventListener('flash', handler);
  });
</script>

{#if messages.length > 0}
  <div class="container">
    {#each messages as m (m.id)}
      <div class="toast toast-{m.type}">
        <span>{m.msg}</span>
        <button class="close" onclick={() => remove(m.id)}>×</button>
      </div>
    {/each}
  </div>
{/if}

<style>
  .container {
    position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
    z-index: 9999; display: flex; flex-direction: column; gap: 8px;
    width: 90%; max-width: 480px; pointer-events: none;
  }
  .toast {
    display: flex; align-items: center; gap: 12px; padding: 12px 16px;
    border-radius: 10px; box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    pointer-events: auto; animation: slideIn 0.25s ease-out; font-size: 14px;
  }
  @keyframes slideIn {
    from { opacity: 0; transform: translateY(-12px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .toast-info { background: #e8f4fd; color: #0c5460; border: 1px solid #bee5eb; }
  .toast-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
  .toast-error { background: #fee; color: #c0392b; border: 1px solid #f5c6cb; }
  .close {
    background: none; border: none; cursor: pointer; font-size: 20px;
    color: inherit; opacity: 0.6; padding: 0 4px; line-height: 1;
  }
  .close:hover { opacity: 1; }
</style>
