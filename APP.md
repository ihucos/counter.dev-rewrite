



# Stack
Go framework — Gin
ORM — sqlc + pgx
Migrations - Tern.


# API
It is a rest API

## Base API

- Create an account (Email is optional)
- Login (use session cookies)
- Login
- User can be registered
- Password can be changed
- email can be changed
- Password can be recovered
- Timezone can be changed
- Change the listed domains options
- There is a json object with simple preferences that can be changed.
- Delete account
- Delete site


## Data Ingress:
as POST data we get a list of objects with the following fields: user, site, metric, value, incr (int)
In a batched manner we:
- Create site objects that do not exist yet for the user. Ignore entries with users that do not exist.
- Increment the count on the respective Count objects

### Authentication
There is a secret key that needs to be passed with this endpoint

## Data querying

Query by those parameters:
  - start_date
  - end_date
  - site

returns a dict with the aggregated {metric: {value: count}} entries. Example:
{
    browsers: {
        "Chrome": 3,
        "Firefox": 2
    }
}




## Modelling

class User:
    id: str (uuid4 or str for legacy users)
    username: str
    email: Optional[str]
    timezone: int # an utc offset (for now) 
    prefs: dict[str, str]

class Site:
    user_id: str (
    user: User
    domain: str
    allowed_domains: list[str] (default [])
    filter_allowed_domains: bool (default False)
    

class Count
    site: Site
    date: Date
    metric: str
    value: str
    count: int



## Notes:

The api will reside at app.counter.dev, but will be accessed from counter.dev
