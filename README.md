# RoboSharp
The robotic sharp. 

This bot is a rewrite of its cluttered and slow java counterpart, following the standards set by other discord bots in python. As such, the architecture may appear "clumsy but functional".


To start, first create the user RoboSharp with the following command in pgadmin4:

### User setup
```sql
CREATE USER robosharp WITH PASSWORD '<your password here>';
```

### Permissions
The user will then require permissions to read/write/delete entries via `migrations/`.
The recommended permissions are:

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO robosharp;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO robosharp;
```

### Connection string (Dsn)

The dsn in the above example would be:
```text
postgresql://localhost:5432/robosharp?user=robosharp&password=<your password here>
```
