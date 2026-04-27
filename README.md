# Online Shopping System

Django 6 + MySQL. Storefront, cart/orders, vendor area, user wallet and addresses.

## Run

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirement.txt
```

(On macOS/Linux: `source .venv/bin/activate`.)

Create a MySQL database, then add `db.cnf` next to `manage.py`:

```ini
[client]
database = your_database
user = your_user
password = your_password
host = localhost
port = 3306
default-character-set = utf8mb4
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

http://127.0.0.1:8000/ — admin at `/admin/`. Do not commit a real `db.cnf`.
