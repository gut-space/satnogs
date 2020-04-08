[doc](../README.md) > Users

# Users Management

Users information has been introduced in schema update 07. There's a new table that holds user-id, username,
salted SHA256 digest, and user role. Until we add flask-admin (or some other management panel), the process
of adding new users is manual.

To add a new user:

1. log into the server using ssh
2. psql satnogs
3. Add 

```sql
INSERT INTO users(id, username, digest, email, role)
VALUES(1, 
       'admin', 
       'pbkdf2:sha256:150000$kTuJClSh$2e93de2d7a169df346a577a24ccc85c2cf1ff62e5a64f944a301cda76ce39c68', 
       'spam@wp.pl',
       'admin');
```

You can generate the hash using the following python commands:

```python
from werkzeug.security import generate_password_hash
generate_password_hash('secret1')
```
