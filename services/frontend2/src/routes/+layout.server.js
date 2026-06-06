/** @type {import('./$types').LayoutServerLoad} */
export function load({ locals }) {
  return {
    user: locals.user || null,
  };
}--- a/src/routes/+layout.svelte
