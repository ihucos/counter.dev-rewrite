declare global {
  namespace App {
    interface Locals {
      user?: {
        pk: number;
        username: string;
        email: string;
        timezone: number;
        prefs: Record<string, any>;
        hide_hosts: boolean;
      } | null;
    }
    interface PageData {
      user?: Locals['user'];
    }
    interface PageState {
      editAccount?: boolean;
    }
    interface Error {
      message: string;
      errorId?: string;
    }
  }
}
export {};
```

```html--- a/services/frontend/src/app.html
