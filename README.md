# Geospatial Service Registry

A Flask + SQLAlchemy + MySQL backend for a Service Provider Directory.  
Providers register their location and service radius; the `/search` endpoint returns every provider whose coverage circle contains a queried coordinate (Haversine formula).

---

## Stack
- **Python 3.11** / Flask 3
- **SQLAlchemy** ORM
- **MySQL 8** (via PyMySQL driver)
- **Docker / docker-compose** for one-command setup

---

## Quick Start (Docker — recommended)

```bash
docker-compose up --build
```

The API will be available at **http://localhost:5000** and the UI at the same address.  
MySQL data is persisted in the `mysql_data` Docker volume.

---

## Local Setup (without Docker)

1. **Create & activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the database**  
   Copy `.env.example` to `.env` and update the connection string:
   ```
   DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/geospatial_registry
   ```
   Create the database in MySQL first:
   ```sql
   CREATE DATABASE geospatial_registry;
   ```

4. **Run the app**
   ```bash
   python main.py
   ```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users` | Register a new provider |
| `GET` | `/users` | List all providers |
| `PATCH` | `/users/<id>` | Update a provider |
| `DELETE` | `/users/<id>` | Remove a provider |
| `GET` | `/search?lat=&long=` | Find providers covering a coordinate |

### POST /users — body (JSON)
```json
{
  "name": "Alpha Distribution",
  "lat": 34.0522,
  "long": -118.2437,
  "service_radius": 25.5
}
```

### GET /search
```
GET /search?lat=34.05&long=-118.24
```
Returns providers sorted by distance (closest first), each including a `distance_km` field.

---

## Validation Rules
- `lat` must be between **-90** and **90**
- `long` must be between **-180** and **180**
- `service_radius` must be a **positive** number
- `name` max **100 characters**
- All numeric fields reject non-numeric strings with a `400` error
- Edit/Delete of a non-existent ID returns `404`
