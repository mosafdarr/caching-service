````markdown
# Caching Service

A **FastAPI‑based microservice** that provides deterministic caching for transformed payloads.  
This project simulates a production‑ready **caching layer** with in‑memory decorators, database‑backed persistence, and containerized deployment.

---

## Table of Contents

1. [Overview](#overview)
2. [What does this service do?](#what-does-this-service-do)
3. [Features](#features)
4. [Architecture](#architecture)
   - [Flow: POST /payload](#flow-post-payload)
   - [Flow: GET /payloadid](#flow-get-payloadid)
   - [CLI Tool (`cache-cli`)](#cli-tool-cache-cli)
   - [How requests flow](#how-requests-flow)
   - [Modules](#modules)
5. [Tech Stack](#tech-stack)
6. [Setup](#setup)
   - [Clone Repository](#clone-repository)
   - [Environment Variables](#environment-variables)
   - [Create & Activate Virtual Environment](#create--activate-virtual-environment)
   - [Poetry Environment](#poetry-environment)
   - [Database](#database)
7. [Running Locally](#running-locally)
   - [Uvicorn](#uvicorn)
   - [Docker](#docker)
   - [Choosing a `WORKERS` value](#choosing-a-workers-value)
8. [API Reference](#api-reference)
   - [Health Check](#health-check)
   - [Create Payload](#create-payload)
   - [Read Payload](#read-payload)
9. [Testing](#testing)
   - [Unit Tests](#unit-tests)
   - [Mocking Strategy](#mocking-strategy)
10. [Performance Notes](#performance-notes)
11. [Why these choices?](#why-these-choices)
12. [Cost & Scaling Considerations](#cost--scaling-considerations)
13. [Development Guidelines](#development-guidelines)
14. [What can be improved?](#what-can-be-improved)

---

## Overview

The **Caching Service** generates deterministic payloads from two lists of strings:

- **Input**: two lists of equal length.
- **Transformation**: normalization, validation, interleaving.
- **Output**: an uppercase, comma‑separated string.

It uses:

- **Deterministic hashing** to generate a stable `payload_id`.
- **Read‑through and write‑through decorators** to emulate Redis.
- **Database persistence** with SQLAlchemy for payload caching.
- **In‑memory registries** to short‑circuit repeated requests.

---

## What does this service do?

- **Speeds up repeated requests** using fast in‑memory caching (Redis is emulated in this demo).
- **Prevents duplicate work**: the same payload always yields the same ID.
- **Easy to run** locally (Docker) and move to the cloud.
- **Shows performance**: a CLI tool reports speed and cache hits/misses.
- **Safe config**: uses Pydantic for typed settings.

---

## Features

- **FastAPI** for endpoints and OpenAPI docs (`/docs`, `/redoc`).
- **Pydantic models** for validation and serialization.
- **SQLAlchemy ORM** with Alembic migrations.
- **Structured logging** with Loguru.
- **Dockerized deployment** with Poetry dependency management.
- **Thorough unit tests** (mocked and non‑mocked) covering edge cases.

---

## Architecture

### Flow: POST /payload

- Client sends JSON data.
- Service hashes it to get a unique ID.
- If result exists: returns it fast (**cache HIT**).
- If not: computes, stores, and returns the result (**cache MISS**).

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Decorator as @check_redis_cache
    participant Controller as CacheController
    participant Transformer as TransformerApp
    participant DB as Database

    Client->>FastAPI: POST /payload {list_1, list_2}
    FastAPI->>Decorator: calculate payload_id
    alt payload_id in cache
        Decorator-->>Client: {payload_id}
    else cache miss
        Decorator->>Controller: create(payload_id, payload, db_session)
        Controller->>DB: check existing payload_id
        alt hit
            DB-->>Controller: cached record
            Controller-->>Decorator: {payload_id}
        else miss
            Controller->>Transformer: transform(payload)
            Transformer-->>Controller: {"output": "..."}
            Controller->>DB: persist (payload_id, input, output)
            DB-->>Controller: commit
            Controller-->>Decorator: {payload_id}
        end
        Decorator-->>Client: {payload_id}
    end
````

### Flow: GET /payload/{id}

* Fetch the result by ID if cached (read‑through).

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Decorator as @cache_read_through
    participant Controller as CacheController
    participant DB as Database

    Client->>FastAPI: GET /payload/{id}
    FastAPI->>Decorator: lookup id in REDIS_OUTPUT_CACHE
    alt hit
        Decorator-->>Client: {"output": "..."}
    else miss
        Decorator->>Controller: get(payload_id, db_session)
        Controller->>DB: query payload_id
        alt found
            DB-->>Controller: cached row
            Controller-->>Decorator: {"output": "..."}
            Decorator->>REDIS_OUTPUT_CACHE: store result
            Decorator-->>Client: {"output": "..."}
        else not found
            Controller-->>Client: 404
        end
    end
```

### CLI Tool (`cache-cli`)

* Lets you exercise both endpoints.
* Shows how fast and consistent the cache is.

**Examples:**

```bash
python3 -m cache_cli -r 5 -j '{"list_1":["a"],"list_2":["b"]}'
```

**Local test sample (illustrative):**

```
=== cache-cli summary ===
Host: http://localhost:8000
Repeat: 100,000
Unique Payload IDs: f44216d4fbf66c4fd3c65813504d45d782ae13c4964d148d83435d316d7a8470
Total time: 17.855 min  |  Avg/iter: 10.713 ms
```

> Note: The above was observed on a local machine under simulated load. Real‑world latency and concurrency will vary by hardware, network, and deployment topology.

### How requests flow

* **Cache HIT:**

  1. Client sends request.
  2. Service hashes payload, checks the cache.
  3. If found, returns result immediately.

* **Cache MISS:**

  1. If not found, the service locks the ID (to avoid thundering herds).
  2. Computes the result, stores it in the cache and DB.
  3. Returns the result to the client.
  4. Concurrent requests for the same payload wait on the first computation.

### Modules

* `src/index.py`: app entry point, health check.
* `src/settings.py`: config loader via `.env`.
* `libintegration/domain/models/cache_model.py`: Pydantic schemas.
* `libintegration/domain/controllers/cache_controller.py`: controller logic.
* `libintegration/domain/apps/transformer.py`: pure interleaving logic (simulates a third‑party service).
* `libintegration/domain/routers/caches.py`: FastAPI router with decorators.
* `schema/tables.py`: SQLAlchemy table definitions.
* `tests/`: unit tests for all endpoints.

---

## Tech Stack

* **Language:** Python 3.11+
* **Framework:** FastAPI + Uvicorn (local) / gunicorn (prod)
* **Schema/Validation:** Pydantic
* **ORM/Migrations:** SQLAlchemy + Alembic
* **Packaging:** Poetry
* **Container:** Docker
* **Logging:** Loguru
* **Cache (demo):** in‑memory dicts simulating Redis

---

## Setup

### Clone Repository

```bash
git clone git@github.com:mosafdarr/caching-service.git
cd caching-service
```

### Environment Variables

Create a `.env` at the project root:

```env
PROJECT_NAME=Caching Service
DATABASE_URL=postgresql://user:password@localhost:5432/caching_db
DATABASE_ENGINE_ECHO=false
```

### Create & Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Poetry Environment

Install dependencies:

```bash
pip install poetry
poetry install
```

### Database

Run migrations:

```bash
alembic upgrade head
```

---

## Running Locally

### Uvicorn

```bash
cd src
uvicorn index:app --reload --port 8000
```

### Docker

Build and run the container:

```bash
# Build the image
docker build -t caching-service:latest .

# Run the container (example)
docker run -d --name caching-service \
  --env-file .env \
  -p 8000:8000 \
  -e WORKERS=8 \
  caching-service:latest
```

#### What each option does

* **`docker build -t caching-service:latest .`**
  Build an image and tag it as `caching-service:latest`.

* **`docker run -d --name caching-service`**
  Start the container in detached mode (`-d`) and name it `caching-service`.

* **`--env-file .env`**
  Load environment variables from your `.env` file.

* **`-p 8000:8000`**
  Map container port `8000` → host port `8000`. Clients connect to the host port.

* **`-e WORKERS=8`**
  Set the `WORKERS` environment variable inside the container.
  The web server uses this to start that many worker processes.

* **`caching-service:latest`**
  The image name and tag to run.

### Choosing a `WORKERS` value

The right number of workers depends on:

* CPU cores available on the host,
* whether the app is **CPU‑bound** (heavy computation) or **I/O‑bound**,
* memory overhead per worker.

**Rules of thumb:**

* **Gunicorn (sync / CPU‑bound apps):**

  ```text
  workers = (2 * CPU_CORES) + 1
  ```

  Example: 4 cores → `workers = 9`

* **Async servers (Uvicorn / FastAPI, I/O‑bound apps):**

  ```text
  workers ≈ CPU_CORES
  ```

  or

  ```text
  workers = 2 * CPU_CORES
  ```

---

## API Reference

### Health Check

```bash
curl -X GET http://localhost:8000/health
```

**Response:**

```json
{"message": "Application's health is good."}
```

### Create Payload

**POST /payload**

**Request:**

```bash
curl -X POST http://localhost:8000/payload \
  -H "Content-Type: application/json" \
  -d '{"list_1":["first string","second string"],"list_2":["other string","another string"]}'
```

**Response:**

```json
{"payload_id": "bda123f..."}
```

### Read Payload

**GET /payload/{id}**

**Request:**

```bash
curl -X GET http://localhost:8000/payload/bda123f...
```

**Response:**

```json
{"output": "FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING"}
```

---

## Testing

### Unit Tests

Run the full suite:

```bash
pytest -vv
```

### Mocking Strategy

* `tests/mock.py`: stores deterministic payloads and expected outputs.
* Controller calls (`CacheController.get`, `.create`) are patched.
* The hash function is patched for predictable IDs.

---

## Performance Notes

* **Hashing:** linear in payload size, **O(n)**.
* **In‑memory cache lookups:** expected **O(1)**.
* **Locking/coordination:** constant‑time map/set operations in the demo (**O(1)**); real distributed locks add network latency.
* **Database lookups:** **O(log n)** typical with B‑tree indexes on `payload_id` (effectively near‑constant for practical sizes).
* **End‑to‑end latency:** dominated by cache miss path (transform + DB round‑trip).

---

## Why these choices?

* **Multi‑layer cache**

  * Fastest for repeated data.
  * A shared cache (e.g., Redis) lets multiple app instances reuse results.
  * The database acts as a durable backing store if the cache misses/evicts.

* **Idempotency**

  * Hashing the payload means the same input always produces the same ID.
  * Avoids duplicate work and duplicate storage.

* **Typed config**

  * Pydantic ensures settings are correct and validated at startup.

* **CLI tool**

  * Simple way to test, benchmark, and observe cache hit/miss behavior.

---

## Cost & Scaling Considerations

> High‑level, vendor‑agnostic guidance..

* **API Gateway Caching**

  * **Pros:** offloads GET traffic before it hits your service; can drastically reduce egress to app instances.
  * **Cons:** cache size and TTL tuning required; write operations (POST) typically bypass the cache.

* **Serverless (API Gateway + Functions)**

  * **Pros:** scales to zero; pay per request/compute; good for spiky traffic; easy multi‑AZ by default.
  * **Cons:** cold starts (mitigations exist); function timeouts. Keep your lambda warm by hitting it after a specific time.

* **Managed Redis / MemoryDB / Memorystore**

  * **Pros:** sub‑millisecond read path for hot keys; shared across app replicas; supports TTLs, eviction policies.
  * **Cons:** additional cost and ops; network hop adds \~sub‑ms–few‑ms latency vs in‑process dict.

---

## Development Guidelines

Use conventional commits:

* `feat: add payload endpoint`
* `fix: correct transformer validation`
* `chore: setup dockerfile`

**Logging:** always log entry/exit points in controllers.
**Tests:** add regression tests for every bug fix.
**DB migrations:** always via Alembic; never edit tables manually.

---

## What can be improved?

* Replace in‑memory caches (`REDIS_CACHED_IDS`, `REDIS_OUTPUT_CACHE`) with a real Redis cluster.
* When a distributed cache is introduced, **retain a small in‑process cache** for hot keys.
* Perform realistic load testing to validate high‑concurrency behavior.
* Add API Gateway caching for even faster GETs.
* Use managed Redis for scaling and operational simplicity.
* Add background workers to **pre‑warm** popular keys on deploy/scale‑out.

````