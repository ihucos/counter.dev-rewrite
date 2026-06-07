<script>
  import Flash from '$lib/Flash.svelte';
  import './app.css';

  let { children } = $props();
</script>

<Flash />
{@render children()}
