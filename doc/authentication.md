# Authentication

ICUBAM supports password, token based and cookie based authentication, depending on the endpoint.

## Tokens

### JWT tokens

JWT encoded tokens are used for the `/update` endpoint of the WWW server.  For
this endpoint, each token is only valid for a `user_id`, `icu_id`  pair, and allows
to update information for a given ICU.

### External client tokens

Additional tokens are created for external clients. These tokens can be of one the following 4 types,

 - **MAP**  allows GET access to `/map` endpoint on the WWW server
 - **STATS** allows GET access to `/db/*` endpoints  on the WWW server as well
   as `/dashboard` endpoint on the backoffice server.
 - **UPLOAD** allows PUT access for the `/db/*` endpoint on the WWW server.
 - **ALL** allows all above operations.


## Cookies

JWT tokens are also stored as [secure
cookies](https://www.tornadoweb.org/en/stable/guide/security.html#cookies-and-secure-cookies)
on first successful authentication. They later give GET access to the /map
endpoint.

## Passwords

Finally, the backoffice server also includes standard password base
authentication for administrators.
