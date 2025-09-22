```markdown
# INSTRUCTIONS.md
**FastAPI Caching Service: Simple Design Guide**  
_Last updated: 2025‑09‑22_

---

## Who is this for?

- Engineers, reviewers, and anyone curious about **why** this service is built this way.
- Read this if you want to understand the design.  
- For setup or usage, see `README.md`.

---

## What does this service do?

- **Speeds up repeated requests** using fast in-memory caching (Redis in demo).
- **Prevents duplicate work**: same payload always gives the same ID.
- **Easy to run** locally (Docker) and move to the cloud.
- **Shows performance**: CLI tool reports speed and cache hits/misses.
- **Safe config**: Uses Pydantic for settings.

---

## How does it work?

- **POST /payload**:  
    - Send JSON data.
    - Service hashes it to get a unique ID.
    - If result exists: returns it fast (**cache HIT**).
    - If not: computes, stores, and returns the result (**cache MISS**).

- **GET /payload/{id}**:  
    - Fetch result by ID if cached.

- **CLI tool (`cache-cli`)**:  
    - Lets you test both endpoints.
    - Shows how fast and consistent the cache is.

**Example:** python3 -m cache_cli -r 5 -j '{"list_1":["a"],"list_2":["b"]}'

---

## What’s the architecture?

- **FastAPI** app (async, type-safe).
- **Redis** (in-memory, demo) as main cache.
- **Pydantic** for config.
- **Docker** for easy setup.
- **Optional**: API Gateway, Lambda, or containers.

**How requests flow:**

- **Cache HIT:**  
    1. Client sends request.
    2. Service hashes payload, checks cache.
    3. If found, returns result instantly.

- **Cache MISS:**  
    1. If not found, service locks the ID.
    2. Computes result, stores in cache.
    3. Returns result to client.
    4. If another request comes for same payload, it waits for result.

---

## Why these choices?

- **Multi-layer cache:**  
    - Fastest for repeated data.
    - Redis lets multiple servers share cache.
    - Database is backup if cache misses.

- **Idempotency:**  
    - Hashing payload means same input always gives same ID.
    - No duplicate work or storage.

- **Typed config:**  
    - Pydantic ensures settings are correct and safe.

- **CLI tool:**  
    - Easy to test and measure cache performance.

---

## How fast is it?

- **Hashing:** Linear in payload size.
- **Redis:** Instant (O(1)).
- **Locking:** Instant (O(1)).
- **Database:** Instant (O(1)).

---

## What can be improved?

- Add API Gateway caching for even faster GETs.
- Use managed Redis for scaling.
- Add worker tools to keep cache warm.

```
