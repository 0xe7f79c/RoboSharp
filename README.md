# RoboSharp
The robotic sharp. 

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
