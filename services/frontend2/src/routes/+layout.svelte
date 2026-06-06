<script>
  import Header from '$lib/components/Header.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import EditAccountModal from '$lib/components/EditAccountModal.svelte';
  import { setUserContext } from '$lib/context.svelte.js';

  let { children, data } = $props();
  
  setUserContext(data.user);
</script>

<Header user={data.user} />
<main>
  {@render children()}
</main>
<Footer />
<EditAccountModal user={data.user} timezones={[
  { value: 0, label: 'UTC' },
  { value: -5, label: 'EST' },
  { value: -8, label: 'PST' },
  { value: 1, label: 'CET' },
  { value: 8, label: 'CST' },
]} />