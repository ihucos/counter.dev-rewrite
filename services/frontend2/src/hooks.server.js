/** @type {import('@sveltejs/kit').Handle} */
export async function handle({ event, resolve }) {
  const { cookies } = event;
  const sessionid = cookies.get('sessionid');

  if (sessionid) {
    try {
      const response = await fetch('http://django:8000/api/auth/user/', {
        headers: {
          'Cookie': `sessionid=${sessionid}`,
        },
      });

      if (response.ok) {
        const user = await response.json();
        event.locals.user = {
          pk: user.pk,
          username: user.username,
          email: user.email,
          timezone: user.timezone,
          prefs: user.prefs || {},
          hide_hosts: user.hide_hosts || false,
        };
      } else {
        event.locals.user = null;
      }
    } catch (error) {
      console.error('Auth hook error:', error);
      event.locals.user = null;
    }
  } else {
    event.locals.user = null;
  }

  const response = await resolve(event);
  return response;
}