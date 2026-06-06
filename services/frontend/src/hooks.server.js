import { redirect } from '@sveltejs/kit';

/** @type {import('@sveltejs/kit').Handle} */
export async function handle({ event, resolve }) {
  const sessionid = event.cookies.get('sessionid');
  
  if (sessionid) {
    try {
      const response = await fetch('http://backend:8000/api/auth/user/', {
        headers: {
          'Cookie': `sessionid=${sessionid}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const userData = await response.json();
        event.locals.user = {
          pk: userData.pk,
          username: userData.username,
          email: userData.email,
          timezone: userData.timezone || 0,
          prefs: userData.prefs || {},
          hide_hosts: userData.hide_hosts || false
        };
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    }
  }

  const response = await resolve(event);
  return response;
}

/** @type {import('@sveltejs/kit').HandleServerError} */
export function handleError({ error }) {
  console.error('Server error:', error);
  return {
    message: 'Internal server error',
    errorId: crypto.randomUUID()
  };
}
```

```javascript--- a/services/frontend/src/lib/api.js
