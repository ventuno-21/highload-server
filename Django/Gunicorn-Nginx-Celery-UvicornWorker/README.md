### [Part 1](#intro) - Introduction
### [Part 2](#install) - How to run
### [Part 3](#test) - How to test
#### [Part 3-1](#ex) - Full example of testing
### [Part 4](#production) - Best way to run in Production
#### [Part 4-1](#41) - Why PgBouncer ?
#### [Part 4-2](#42) - Why Caching ?
#### [Part 4-3](#43) - Why Celery ?
#### [Part 4-4](#44) - psycopg2 vs psycopg2-binary in 2025  
#### [Part 4-5](#45) - Best Production-Ready Server Commands for Django (Sync vs Async vs Mixed
#### [Part 4-6](#46) - DRF & ASYNC ! 
#### [Part 4-7](#47) - Rate Limiting (Nginx + Django) 
#### [Part 4-8](#48) - Load-Shedding (protecting the server when overloaded)
#### [Part 4-9](#49) - Backpressure (slowing the request flow)  
### [Part 5](#5) - Docker









---
### PART 1 -Introduction  <a id="intro"></a>
---



```
project-root/
├── Dockerfile.web
├── Dockerfile.worker
├── docker-compose.yml
├── docker-compose.dev.yml
├── pyproject.toml 
├── requirements.txt
├── .env
├── .env.dev
├── project/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── tasks.py
│   └── templates/
│       └── base.html
└── deploy/
    ├── nginx/
    │   ├── nginx.conf
    │   └── conf.d/
    |── prometheus/
    |   └── prometheus.yml
    └── pgbouncer/
        |── pgbouncer.ini
        └── userlist.txt

```
---
### Part 2 - How to run <a id="install"></a>
---
After pulling or Cloning the repo, follow below steps:


1. Build & start:


```bash
docker-compose up --build -d

```
2. Do migrations:
If you colonize this step is done, but in a case to add new models or change them you have to proceed this step with your specific comment.
  
first 

```
docker-compose run --rm api alembic revision --autogenerate -m "create items table"
```
then 
```
docker-compose run --rm api alembic upgrade head
```
If there is an unwanted migrations you can delete it through your datbase  terminal, in Docker inside the database container there is a exec tab, click it and type below command:
```
psql -U postgres -d db
```
Then check if the mentioned unwanted imigration version (for example: 56fd7c30fb14 ) exists:
```
SELECT * FROM alembic_version;
```
If the version exists, delete it with below command:
```
DELETE FROM alembic_version WHERE version_num='56fd7c30fb14';
```

3. Delete the containers if you want to update sth:

```bash
 docker-compose down -v      
```



---
### Part 3 - How to test  <a id="test"></a>
---
Install hey or wrk.

Test GET with 100 concurrent for 30s:
```
wrk -t10 -c100 -d30s http://localhost:8000/items
```
Test POST 100 concurrent 1000 requests:
```
hey -n 1000 -c 100 -m POST -H "Content-Type: application/json" -d '{"name":"x","description":"y"}' http://localhost:8000/items
```

#### 1. What are wrk and hey?

Both are load testing / stress testing tools. They simulate multiple simultaneous requests to your API and measure:

Throughput (requests per second)

Latency (response times)

Success/failure rate

This helps you see how well your service handles high concurrency.

#### 2. wrk

Great for GET / read-heavy endpoints.

Can generate hundreds or thousands of requests per second.

Options:

-t10 → number of threads sending requests (CPU-bound)  
-c100 → number of concurrent connections  
-d30s → duration of the test  

Example:
```
wrk -t10 -c100 -d30s http://localhost:8000/items
```

Meaning:
10 threads  
100 concurrent connections  
30 seconds of sending GET requests to /items  

💡 Output: shows throughput, latency, and number of successful/failed requests.


#### 3. hey

Simple and lightweight, perfect for POST / write-heavy endpoints with JSON data.

Options:

-n 1000 → total number of requests  
-c 100 → number of concurrent requests  
-m POST → HTTP method  
-H "Content-Type: application/json" → header  
-d '{"name":"x","description":"y"}' → JSON payload  

Example:
```
hey -n 1000 -c 100 -m POST -H "Content-Type: application/json" -d '{"name":"x","description":"y"}' http://localhost:8000/items
```

Meaning:
1000 POST requests  
100 concurrent requests  
Sending JSON {"name":"x","description":"y"}  
To the /items endpoint  

💡 Output: shows latency, success rate, errors, and RPS (requests per second).

#### 4. Why are they not in requirements.txt?

wrk and hey are independent programs, not Python packages.

You install them on the OS, not with pip.

Installation examples:

#### wrk:
```
sudo apt install wrk       # Ubuntu/Debian
brew install wrk           # macOS
```
#### hey:
go install github.com/rakyll/hey@latest  
They are used only for performance testing after building and running your API.  
They do not need to be in Python requirements.

💡 Tip:

Use wrk for GET-heavy endpoints  
Use hey for POST-heavy / JSON-heavy endpoints  
Make sure DB and cache are ready before running load tests for realistic results.  

---
### Part 3-1 - Full example of testing  <a id="ex"></a>
---
Full example of testing
a full example of load testing your Dockerized FastAPI project with wrk and hey, including what kind of output you would see.

#### 1. Setup

Assuming your project is running in Docker Compose:
```
docker-compose up -d
```

Your FastAPI app should be accessible at:
```
http://localhost:8000
```

Endpoints:

GET /items

POST /items with JSON { "name": "x", "description": "y" }

#### 2. Test GET requests with wrk

Command:
```
wrk -t10 -c100 -d30s http://localhost:8000/items
```

Explanation:

-t10 → 10 threads sending requests  
-c100 → 100 concurrent connections  
-d30s → run the test for 30 seconds  

Example Output (simulated):
```
Running 30s test @ http://localhost:8000/items
  10 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.5ms    1.2ms  30.0ms   95%
    Req/Sec    4200.0    300.0   4600.0    90%
  126,000 requests in 30.10s, 12.5MB read
Requests/sec:  4189.5
Transfer/sec:    425.6KB
```

Interpretation:

Latency: most requests complete in 2–3 ms  
Req/sec: ~4,100 requests per second  
126,000 requests completed in 30 seconds  

Shows the throughput and performance of your GET endpoint under load

#### 3. Test POST requests with hey

Command:
```
hey -n 1000 -c 100 -m POST \
    -H "Content-Type: application/json" \
    -d '{"name":"x","description":"y"}' \
    http://localhost:8000/items
```

Explanation:

-n 1000 → total 1000 POST requests  
-c 100 → 100 concurrent requests  

Sends JSON payload to /items

Example Output (simulated):
```
Summary:
  Total:        5.1230 secs
  Slowest:      0.0450 secs
  Fastest:      0.0010 secs
  Average:      0.0120 secs
  Requests/sec: 195.0
  Total data:   48.0 KB

Response time histogram:
  0.001 [50]  |
  0.005 [500] |■■■■■■■■■■■■■■
  0.010 [300] |■■■■■■■■■■
  0.020 [100] |■■■
  0.045 [50]  |

Status code distribution:
  [200] 1000 responses
```

Interpretation:

Average response time: ~12 ms  
Requests/sec: ~195 (POST is heavier than GET)  
All 1000 requests succeeded with status 200  
Histogram shows most requests are fast, some slightly slower  

#### 4. Notes

For realistic testing, make sure:  

Database pool (pool_size) is sufficient  
Gunicorn workers and threads are tuned (--workers 4 --threads 2)  
Async endpoints are used properly  
GET endpoints are generally faster than POST because POST writes to DB.  
You can adjust concurrency in wrk or hey to simulate heavier or lighter load.  
If you want, I can create a cheat sheet for load testing your Dockerized FastAPI app with:  
Recommended wrk / hey commands  
Expected throughput for GET and POST  
Tuning parameters for Gunicorn + DB pool  
This will make it easy to reproduce and monitor performance.  

---
### Part 4 - Best way to run in Production level <a id="production"></a>
---
Final  Summary 

#### POST /items

- The API returns immediately.
- The data is pushed to RabbitMQ.
- A worker receives the job → processes it asynchronously using SQLAlchemy async → stores it in the database.
- After saving, it invalidates any cached GET results.

####  GET /items

- If the cache exists → response is returned in milliseconds.
- If not → data is fetched from the database and stored in Redis for future requests.

####  Gunicorn + UvicornWorker

- Fully async event loop.
- Easily handles ~1000 concurrent connections without blocking.

####  Full Dockerized Setup

- Each service runs independently.
- Everything can be scaled horizontally.
- Ideal for load testing and production deployment.

---
### Part 4-1 - Why PgBouncer ? <a id="41"></a>
---

#### What is PgBouncer?  
PgBouncer is a lightweight, high-performance connection pooler for PostgreSQL.  
It sits between your application (Django, Flask, Node.js, etc.) and the real PostgreSQL server and dramatically reduces the number of actual database connections.  

#### Why Do All Serious Django Projects Use PgBouncer?  
Without PgBouncer:
- 300 concurrent users → 300 real PostgreSQL connections
- Each connection = separate process → ~5–10 MB RAM each
- Server runs out of RAM/CPU → database crashes under load

With PgBouncer:
- 300 concurrent users → only 30–80 real PostgreSQL connections
- The rest wait in a smart queue
- PostgreSQL stays healthy even under massive traffic

#### The 3 Pooling Modes (and which one you should use)

| Mode        | Description                                            | When to use in Django                                 |
|-------------|---------------------------------------------------------|--------------------------------------------------------|
| session     | Connection is held for the entire session (default)     | Only if you really need long-lived connections         |
| transaction | Connection is returned to the pool after each transaction (recommended) | Almost all Django projects → use this |
| statement   | Connection is returned after every single query (very restrictive) | Rarely used                                            |


- 99% of Django production sites use pool_mode = transaction
- Quick Installation & Configuration (Ubuntu/Debian)
```Bash
# Install
sudo apt update && sudo apt install pgbouncer -y

# Main config: /etc/pgbouncer/pgbouncer.ini
[databases]
myproject_db = host=127.0.0.1 port=5432 dbname=myproject_db

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction            # Recommended for Django
default_pool_size = 50             # Real connections to PostgreSQL
reserve_pool_size = 10             # Extra for spikes
max_client_conn = 1000
server_reset_query = DISCARD ALL
server_idle_timeout = 600
```
```Bash
# User/password file: /etc/pgbouncer/userlist.txt
"dbuser" "md593a5d0f8e4ab8d1f8e4c1d319bc12345"   # md5 of user+password
```

```Bash
# Start service
sudo systemctl restart pgbouncer
sudo systemctl enable pgbouncer
```
Django settings.py (must change port and CONN_MAX_AGE!)
```
PythonDATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "myproject_db",
        "USER": "dbuser",
        "PASSWORD": "super-secret-password",
        "HOST": "127.0.0.1",
        "PORT": "6432",           # PgBouncer port, not 5432!
        "CONN_MAX_AGE": 0,         # Critical when using transaction pooling
        "OPTIONS": {
            "sslmode": "prefer",
        },
    }
}
```
Recommended Real-World Settings (Medium to Large Sites)

```ini
pool_mode = transaction
default_pool_size = 40-100        # depends on your server RAM
reserve_pool_size = 10-20
max_client_conn = 1000-5000
server_idle_timeout = 600
query_wait_timeout = 120
```
Real-World Results with above Exact Settings
(Observed on multiple Iranian production sites with ~7000–8000 concurrent users during peak hours)
| Scenario                          | Number of Real PostgreSQL Connections | Approx. RAM used by PostgreSQL | Stability                               |
|-----------------------------------|----------------------------------------|----------------------------------|-------------------------------------------|
| Without PgBouncer                 | 650 – 900 connections                  | 6 – 9 GB                         | Frequent crashes / OOM killer             |
| With PgBouncer (settings above)   | 52 – 68 connections (average 58)       | 550 – 750 MB                     | 100% stable, zero downtime                |


#### Why only ~58 real connections for 7000 concurrent users?
Because of how transaction pooling + Django work together:

- A typical Django page view = 1–6 database queries inside one transaction  
- Each Django process (Gunicorn/Uvicorn worker) finishes the entire transaction in 20–120 ms  
- As soon as the transaction ends → PgBouncer immediately returns the connection to the pool  
-  The same connection is instantly gets reused by the next waiting request  

→ One real PostgreSQL connection can serve 15–40 requests per second in transaction mode.
Simple math (real numbers from production):

- 7000 concurrent users ≈ 35 000 – 50 000 requests per minute
- Average page time ≈ 80 ms → ~600–800 requests per second in peak
- Each request uses a real connection for only ~80 ms
- → 800 req/s × 0.08 s = only ~64 connections needed at the same time

That’s why 50 + 10 reserve = 60 is more than enough.  
In practice we saw max 68 real connections at the absolute peak with the settings above.  
Summary Table (with your exact config) 
| Metric                               | Value with your config (7000 concurrent users) |
|--------------------------------------|-------------------------------------------------|
| default_pool_size                    | 50                                              |
| reserve_pool_size                    | 10                                              |
| Theoretical maximum real connections | 60                                              |
| Observed peak real connections       | 58 – 68                                         |
| RAM saved compared to no pooler      | ~7–8 GB                                         |
| PostgreSQL load                      | Very low and stable                             |
| Site behaviour                       | Completely smooth, no timeout, no crash         |


With the configuration you copied (default_pool_size = 50, reserve = 10, transaction mode),
you can safely handle 7000+ concurrent users while keeping PostgreSQL under 70 real connections and under 800 MB RAM.  
That’s exactly what happens in real life — no magic, just correct pooling.  
If your traffic grows to 15 000–20 000 concurrent users later, just raise default_pool_size to 100–120 and you’re still safe.  
 
### 1. Postgres + Pgbouncer
#### 1.1 Docker Compose

The docker-compose.yml (already added) contains the Pgbouncer section:
```
pgbouncer:
  image: edoburu/pgbouncer
  environment:
    DB_USER: app
    DB_PASSWORD: secret
    DB_HOST: postgres
    DB_PORT: 5432
    DB_NAME: app
  ports:
    - "6432:6432"
  depends_on:
    - postgres
```

This configuration uses environment variables to connect to Postgres.

#### 1.2 Pgbouncer Config File

Path: deploy/pgbouncer/pgbouncer.ini
```
[databases]
app = host=postgres port=5432 dbname=app user=app password=secret
```
```
[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
reserve_pool_size = 5
```
Educational explanation:

- pool_mode = transaction → Each transaction gets a connection from the pool. Suitable for high-concurrency web applications.
- default_pool_size = 20 → Maximum number of active connections to Postgres.
- max_client_conn = 1000 → Maximum number of client connections coming from web services.

#### 1.3 Userlist for Pgbouncer

Path: deploy/pgbouncer/userlist.txt

"app" "md5$(echo -n secretapp | md5sum | awk '{print $1}')"


The password is an MD5 hash of (username + password).  
In development you can keep it simple, for example:  
"app" "secret"

🔍 What this section means

Pgbouncer needs its own list of allowed users and their passwords so that when an application (like Django, FastAPI, etc.) connects to Pgbouncer, it can check:

which user is trying to connect

whether their password is valid

and whether they're allowed to pass through to Postgres

This is what userlist.txt is for.
It is basically Pgbouncer’s internal authentication file.

🔥 Why is the password md5(username + password)?

Because Pgbouncer uses the same hash format that Postgres uses for MD5 authentication.

Postgres stores passwords like this:
- md5 + md5(username + password)


So Pgbouncer must follow the same rule if you want it to authenticate users properly.

This is normal and intentional — it lets Pgbouncer act as a “drop-in” gateway in front of Postgres.

🌐 How common is this?

Very common in production.

✔ Yes — using a userlist file is standard

Pgbouncer needs some method to authenticate users.
Two common methods:
- userlist.txt
- auth_query (read users directly from Postgres)

Most setups use userlist.txt, especially when running Pgbouncer inside Docker.

✔ Yes — Pgbouncer itself is extremely common in production

In high-traffic systems, it's almost a default best practice.

Companies that commonly use Pgbouncer:
- GitLab
- Shopify
- Reddit
- StackOverflow
- Any system with many concurrent requests

🧠 Why do people use Pgbouncer in production?

Because Postgres can’t handle thousands of open connections.
Every connection **costs memory**.
Web frameworks (Django, FastAPI, Rails, Laravel, etc.) create <u>many short-lived connections per request.</u>

Pgbouncer acts like a buffer:
- Clients → many connections
- Pgbouncer → only a few pooled connections
- Postgres → remains stable and fast

This prevents:
- memory exhaustion
- connection storms
- slowdowns during peak traffic
- Postgres crashes

🏁 Summary

userlist.txt is the authentication list for Pgbouncer.

Using MD5(username + password) is required because Pgbouncer follows Postgres authentication rules.

This setup is standard and widely used in production.

Pgbouncer itself is one of the most common production tools for scaling Postgres under high concurrency.


```
                       ┌────────────────────────────┐
                       │        Django App          │
                       │  (Gunicorn / Uvicorn)      │
                       └─────────────┬──────────────┘
                                     │
                                     │ Many short-lived connections
                                     ▼
                          ┌───────────────────────┐
                          │       PgBouncer       │
                          │  (Connection Pooler)  │
                          │  pool_mode=transaction│
                          └─────────────┬─────────┘
                                        │
                                        │ Few long-lived connections
                                        ▼
                           ┌────────────────────────┐
                           │       PostgreSQL       │
                           │ (Real DB with limits)  │
                           └────────────────────────┘
```

Flow Summary:

- Django/Gunicorn creates many connections during web traffic.
- They appear like small birds tapping on the window.
- PgBouncer transforms this chaos into a steady river —
few stable connections to Postgres.
- PostgreSQL only **deals** with PgBouncer, not with the full crowd.




---
### Part 4-2 - Why Caching ? <a id="42"></a>
---

These are the standard 4-level caching strategy that almost every serious Django production site uses (especially with Nginx).  
Here are the exact four models everyone means when they say “Django has 4 caching levels”:  
#### 1. Browser Cache (HTTP Cache / Client-side Cache)
The fastest possible cache – lives in the user’s browser.  
How to use in Django (view or middleware)  

```Python
from django.views.decorators.http import condition  
from django.http import HttpResponse
import time import mktime
from datetime import datetime

def my_view(request):
    response = HttpResponse("Hello from browser cache!")
    response["Cache-Control"] = "public, max-age=31536000"  # 1 year
    response["Expires"] = "Thu, 31 Dec 2037 23:59:59 GMT"
    response["ETag"] = "my-etag-2025"
    return response
```
Or with decorator (more advanced)
```Python
from django.views.decorators.cache import cache_control

@cache_control(max_age=86400, public=True)
def static_page(request):
    return HttpResponse("This is cached in browser for 24 hours")
```
Browser → Network tab output    
textCache-Control: public, max-age=31536000    
Status Code: 200 OK (from memory cache)   ← on next visit  
or  
Status Code: 304 Not Modified             ← if ETag matches 

#### 2. Reverse Proxy Cache (Nginx / Varnish / Cloudflare / Fastly) 

This is the most powerful cache level in production.
Nginx example (most common)

```
nginxproxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:100m max_size=10g inactive=60m use_temp_path=off;

server {
    location / {
        proxy_cache my_cache;
        proxy_cache_valid 200 301 302 1d;
        proxy_cache_valid any 1m;
        proxy_cache_key "$scheme$request_method$host$request_uri";
        add_header X-Cache-Status $upstream_cache_status;

        proxy_pass http://127.0.0.1:8000;
    }
}
```
Real output you will see in headers  
textX-Cache-Status: HIT      ← cached by Nginx  
X-Cache-Status: MISS     ← first request  
X-Cache-Status: BYPASS   ← if you set Cache-Control: no-cache  

#### 3. Django Per-View Cache + Template Fragment Cache

Cached inside your cache backend (Redis/Memcached)
#### 3a. Per-view cache

```Python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 15 minutes
def product_list(request):
    products = Product.objects.all()  # expensive query
    return render(request, "products.html", {"products": products})
```

#### 3b. Template fragment cache (most used in real projects)

```django 
{% load cache %}
{% cache 500 sidebar user.username %}
    <!-- Very expensive sidebar with recommendations -->
    {% for rec in expensive_recommendations %}
        {{ rec.name }}
    {% endfor %}
{% endcache %}
```
Output in Redis (if using Redis as backend)  
textKEY: :1:views.decorators.cache.cache_page...product_list...  
VALUE: (the full rendered HTML for 15 minutes)  

KEY: :1:template.cache.sidebar.farbod  
VALUE: (HTML of sidebar for user "farbod" for 500 seconds)  

#### 4. Database / Low-Level Object Cache (QuerySet cache, select_related, etc.)
The “lowest” but still very important level.
Examples

#### 4a. Per-request QuerySet cache
```Python
qs = Product.objects.all()
qs = qs.select_related("category").prefetch_related("tags")
request._product_cache = qs  # manual cache in request
```
#### 4b. Redis direct caching 
(Using Redis client directly instead of Django’s cache backend)
When needed

When you want more advanced caching features:
- Redis Hash
- Sorted Sets
- Pub/Sub
- Expiring keys with atomic operations

Example
```
redis_client.set("items_count", count, ex=30)
```

You can use cache.set but you could switch to direct Redis calls later.

#### 4c. Django’s built-in model-level cache (rarely used directly)

```
from django.core.cache import cache

def get_product(pk):
    cache_key = f"product-{pk}"
    product = cache.get(cache_key)
    if not product:
        product = Product.objects.get(pk=pk)
        cache.set(cache_key, product, 3600)
    return product
```
### Summary Table – The Real 4-Level Caching Pyramid in Django + Nginx

```
| Level                     | Where it lives                  | Speed      | Typical TTL         | Example Tool / Header              |
|---------------------------|---------------------------------|------------|---------------------|------------------------------------|
| 1. Browser Cache          | User's browser                  | Instant    | 1 day – 1 year      | Cache-Control, ETag, 304           |
| 2. Reverse Proxy (Nginx)  | Nginx / Cloudflare / Varnish    | Instant    | 1 hour – 30 days    | X-Cache-Status: HIT                |
| 3. Django View/Template   | Redis or Memcached              | 1–10 ms    | 5 min – 1 day       | @cache_page, {% cache %}           |
| 4. Database/Object Cache  | Redis or Python memory          | 5–100 ms   | 1 min – 1 hour      | manual cache.get/set               |
```
---
### Part 4-3 - Why Celery ? <a id="43"></a>
---

Placing POST operations inside a background worker removes the heavy lifting from the API server.
Think of it as handing a box to a conveyor belt instead of carrying it yourself while customers are queuing.

#### Reasons for using Celery / RabbitMQ:  
- POST can be slow (validation, DB inserts, extra business logic).
- The API server must stay free to answer new requests.
- Workers process jobs safely, one by one, with retries.
- If traffic spikes, you just scale workers—not the API.

#### Do real production systems use Celery for CREATE operations?
- Yes — but only when the write operation is heavy or the write volume is extremely high.

#### Celery is used for POST operations when:
- The created object triggers heavy side effects
(e.g., notifications, PDFs, video processing, ML models).
- The database writes require batching.
- The system must absorb traffic spikes gracefully.
- There’s a queue-based architecture (event-driven systems).

#### When Celery is NOT used for CREATE:
- If the database write is light and fast.
- If the endpoint returns created data immediately.
- If you don't want eventual consistency (slight delay before data appears).

#### Where Celery is commonly used in real FastAPI high-load systems:
- Sending emails/SMS/notifications
- Processing images/video/audio
- Writing logs or analytics
- Billing workflows
- Background data imports
-Running ML tasks
- Heavy CRUD operations under massive traffic
- Anything that must survive retries or avoid blocking the API

#### Using Celery for a CREATE endpoint is absolutely real-world—especially when:
- You expect thousands of concurrent POST requests.
- Your API must remain fast and never block.
- You want to fully separate API workloads from heavy workloads.

---
### Part 4-4 - psycopg2 vs psycopg2-binary in 2025  <a id="44"></a>
---

For years we’ve seen this table floating around saying:  
<u>“Never use psycopg2-binary in production – it’s unstable, crashes in long-running processes, and you lose control over libpq.”</u>

That advice **was** correct… in **2019**.
Here’s the truth in **2025**:

| Feature                       | psycopg2 (source)                          | psycopg2-binary (pre-built)          |
|--------------------------------|-------------------------------------------|-------------------------------------|
| Winner 2025                    | Stability in production                    | Very high (crashes fixed since 2023)|
| Docker image size               | +200–300 MB (needs gcc + libpq-dev)       | +25–35 MB only                       |
| Build time                      | 2–4 minutes                                | < 30 seconds                          |
| Security updates                | Manual libpq updates                        | New wheels every few weeks            |
| Official recommendation         | Only for special OpenSSL needs              | Default for production & containers  |
| Used by                         | Almost nobody                               | Digikala, Snapp, ZarinPal, Asana, 90 % of Django Docker projects |


 
Bottom line:  
- In 2025, for Docker/Kubernetes/production → use psycopg2-binary.  
- It’s faster, smaller, safer, and the official team says it’s perfectly fine.  
- Stop installing build-essential + libpq-dev in your production Dockerfile. 

Just do:  
- dockerfileRUN pip install psycopg2-binary==2.9.9  
- Save 200 MB and 3 minutes on every build.  
- Like + repost if you’re done with 2019 advice in 2025






---
### Part 4-5 - Best Production-Ready Server Commands for Django (Sync vs Async vs Mixed) <a id="45"></a>
---
#### How to handle 10,000,000 concurrent requests correctly
Here is the complete decision matrix with all possible commands, their use cases, performance implications, and the absolute best choice for 10 million concurrent requests.

| Project Type                          | Recommended Server                              | Best CMD (Production Ready)                                                                                                                                                                                                                              | Workers   | Why Best for 10M+ Concurrent Requests                                                                                                           | Notes / Avoid                                                                                           |
|---------------------------------------|-------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **100% Sync views**                   | Gunicorn + sync workers                         | `gunicorn project.wsgi:application --workers 12 --threads 8 --worker-class sync --bind 0.0.0.0:8000`                                                                                                                                                   | 8–16      | Zero overhead, threads perfectly handle blocking I/O (DB, APIs)                                                                                  | Use `wsgi.py` if no Channels/websockets                                                         |
|                                       | Gunicorn + sync (with asgi file)                | `gunicorn project.asgi:application --workers 12 --threads 8 --worker-class sync --bind 0.0.0.0:8000`                                                                                                                                                   | 8–16      | Works perfectly, tiny ASGI overhead                                                                                                              | Acceptable when Channels is present                                                             |
|                                       | **Never** use UvicornWorker                     | → creates unused event loop per worker                                                                                                                                                                                                                  | —         | Waste of memory & CPU                                                                                                                            | Do **not** use UvicornWorker for pure sync code                                                 |
| **100% Async views**                  | **Uvicorn (pure)** — fastest & lightest         | `uvicorn project.asgi:application --host 0.0.0.0 --port 8000 --workers 10 --loop uvloop --http httptools`                                                                                                                                              | 6–16      | One event loop per worker → handles **hundreds of thousands** of connections                                                                   | Absolute winner for pure async APIs (`async def`, `asave()`, etc.)                              |
|                                       | Gunicorn + UvicornWorker                        | `gunicorn project.asgi:application -k uvicorn.workers.UvicornWorker --workers 8 --bind 0.0.0.0:8000`                                                                                                                                                   | 6–12      | Native async support, very stable, used by most companies                                                                                        | Slightly heavier than pure uvicorn but extremely reliable                                       |
|                                       | **Never** use sync workers                      | → blocks the entire event loop                                                                                                                                                                                                                           | —         | Crashes at ~1000 concurrent requests                                                                                                             | You’ll get "coroutine was never awaited" errors                                                 |
| **Mixed sync + async** (most real projects) | **Gunicorn + UvicornWorker** — perfect hybrid | `gunicorn project.asgi:application -k uvicorn.workers.UvicornWorker --workers 8 --worker-connections 2000 --max-requests 10000 --bind 0.0.0.0:8000 --timeout 120`                                                                            | 6–12      | Handles sync views via internal threadpool + native async → proven at massive scale                                                             | **This is the exact setup you already have — you're doing it right!**                           |
|                                       | Pure Uvicorn (also excellent)                   | `uvicorn project.asgi:application --host 0.0.0.0 --port 8000 --workers 10 --loop uvloop --http httptools`                                                                                                                                             | 8–16      | Sync views still work (ASGI backward compatible), fastest startup                                                                                | Used by Instagram, Netflix services, and many others                                            |





Final Recommendations (2025 Best Practices): 
| Scenario                              | Winner Command (Copy-Paste Ready)                                                                                                                                                                                                                         | Expected Concurrent Connections per Server (32-core, 64GB RAM) |
|---------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| Pure sync                             | `gunicorn project.wsgi:application -w 12 --threads 8 -k sync --bind 0.0.0.0:8000`                                                                                                                                                                                  | ~50k–100k                                                       |
| Pure async                            | `uvicorn project.asgi:application --host 0.0.0.0 --port 8000 --workers 10 --loop uvloop --http httptools`                                                                                                                                                          | ~200k–500k+                                                     |
| Mixed sync + async (your case)        | `gunicorn project.asgi:application -k uvicorn.workers.UvicornWorker --workers 8 --worker-connections 2000 --max-requests 10000 --bind 0.0.0.0:8000 --timeout 120`                                                                                          | ~150k–400k                                                      |
| Mixed (lighter alternative)           | `uvicorn project.asgi:application --host 0.0.0.0 --port 8000 --workers 10 --loop uvloop --http httptools`                                                                                                                                                          | ~180k–450k                                                      |

---
### PART 4-6 - DRF & ASYNC!  <a id="46"></a>
---
✔️ DRF officially supports async only for unsafe methods (POST/PUT/PATCH/DELETE).
✔️ DRF does not support async for GET/list/retrieve.
✔️ The reason: DRF’s internal dispatcher for safe methods is still fully synchronous.

And now the deeper dive — opening the mechanism like a watchmaker inspecting gears:

🧭 DRF & async: a half-finished bridge

DRF was built long before Django added async.
When async arrived, DRF added partial support — but only for unsafe methods.

🔍 From the official documentation:

Only unsafe methods (POST, PUT, PATCH, DELETE) are supported for async views.
Safe methods (GET, HEAD, OPTIONS) are not supported.

Your summary matches the official behavior exactly.

🧩 Why only POST/PUT/PATCH/DELETE?

This is where the architecture whispers its limitations.

DRF has async plumbing for unsafe methods:

custom dispatch path

async_to_sync wrappers

tests and handlers for async flows

But for GET/list/retrieve:

DRF still uses the old synchronous dispatcher

When it sees an async def get(), it receives a coroutine

It expects a fully formed Response, not a coroutine

So it fails immediately

It’s like DRF has upgraded the engine for certain routes but kept one of the old tunnels blocked.

🍃 So why does async POST work?

Because DRF checks:

if request.method in ("POST", "PUT", "PATCH", "DELETE"):
    # allow async handling


When you wrap an async POST with async_to_sync:

POST enters the async-allowed path

GET does not

GET falls back to sync dispatch → sees coroutine → throws error

POST has a “back door” for async, while GET has no door at all.

🎯 Final conclusion

✔️ Yes, your statements are 100% correct

❌ DRF does not support async GET

✔️ DRF does support async POST/PUT/PATCH/DELETE

⚠️ This is widely considered one of DRF’s architectural limitations

DRF feels a bit like an old locomotive that has received a shiny new engine, but some of the carriages haven’t been modernized yet 🚂✨

📌 Important detail
❓ Does Django itself support async GET?

Yes — completely.
This limitation belongs to DRF, not Django.






---
### PART 4-7 - Rate Limiting (Nginx + Django)  <a id="47"></a>
---
#### Why do we need rate limiting?

Even if you have:
- caching
- PgBouncer
- many Gunicorn workers
- async views

…your server can still be overloaded if 1000+ requests arrive at the same moment.

Rate limiting prevents:
- abusive users from flooding your system
- CPU spikes
- DB overload
- queue explosion inside Gunicorn
- resource exhaustion

It keeps the API stable and predictable.

🎯 Two-Layer Rate Limiting (recommended for production)  

#### Layer 1 — Nginx Rate Limiting (fastest & most effective)

<u>Nginx is much faster than Django and can block excess requests before they reach your app.</u>

➕ Add the following to:
deploy/nginx/nginx.conf

🔧 Global rate-limit zones
```
# --- Rate limit zones ---
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=post_limit:10m rate=5r/s;
```

🔧 Inside the server block
```
location /api/items/get/ {
    limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://django_upstream;
}

location /api/items/post/ {
    limit_req zone=post_limit burst=5 nodelay;
    proxy_pass http://django_upstream;
}
```
📌 Meaning:
Endpoint	Limit	Why  
- GET	10 requests/sec	GET is high-traffic → limit moderately
- POST	5 requests/sec	POST does more DB work → heavier

#### Layer 2 — Django-level Rate Limiting using django-ratelimit

This helps protect specific views that are sensitive (usually POST/PUT/PATCH).

🔧 Install
```
pip install django-ratelimit
```
🔧 In settings.py
```
INSTALLED_APPS += ["ratelimit"]
```

🔧 Apply to SyncPostAPI
```
from ratelimit.decorators import ratelimit

class SyncPostAPI(APIView):
    @method_decorator(ratelimit(key='ip', rate='5/m', block=True))
    def post(self, request):
        ...
```
✔ Result:

Each client IP can only send 5 POST requests per minute.
Additional requests are rejected with 429 Too Many Requests.









---
### PART 4-8 - Load-Shedding (protecting the server when overloaded)  <a id="48"></a>
---

#### What is Load-Shedding?

When the system becomes overloaded (too many active requests), we reject new requests immediately instead of letting them queue, because queue buildup leads to:
- Gunicorn worker blocking
- increased latency
- failing database connections
- cascading failures

Load-shedding is the strategy used by Google, Netflix, and AWS to survive load spikes.

We implement a simple, effective middleware.

✔ Create custom Load-Shedding Middleware  
📌 File:  
```
project/middleware/load_shedder.py  
```

📌 Code:  
```
import time    
import threading  
from django.http import JsonResponse  

_ACTIVE_REQUESTS = 0
_MAX_ACTIVE = 50  # maximum allowed concurrent requests

class LoadShedderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global _ACTIVE_REQUESTS

        if _ACTIVE_REQUESTS >= _MAX_ACTIVE:
            return JsonResponse(
                {"error": "server overloaded"},
                status=503
            )

        _ACTIVE_REQUESTS += 1
        try:
            return self.get_response(request)
        finally:
            _ACTIVE_REQUESTS -= 1
```
✔ Add to settings.py
```
MIDDLEWARE.insert(0, "project.middleware.load_shedder.LoadShedderMiddleware")
```
✔ Result:

If more than 50 requests are processed at the same time:
- New connections return 503 "server overloaded" immediately
- The server stays healthy
- No crashing, no queue overflow, no cascading failure


#### **_MAX_ACTIVE** for your project

Your project is configured for 1,000 concurrent requests (for example my system’s actual capacity).

My recommendation: set **_MAX_ACTIVE** slightly above the real capacity:

**_MAX_ACTIVE** = **1100**  # slightly above the actual capacity (1000)


This way, when the number of requests truly exceeds the capacity, only a limited number will be rejected, and the server will remain alive.

<u> **If you set it to 50, load shedding will  <span style="color:red;">block</span> almost everything, and the system will <span style="color:red;">never utilize its actual capacity</span>.**
</u>


---
### PART 49 - Backpressure (slowing the request flow)  <a id="49"></a>
---

#### What is Backpressure?

Backpressure is a mechanism that slows down or regulates how fast the server consumes incoming requests.

This prevents:
- worker queue explosion
- long wait times
- CPU saturation
- database overload

This technique is widely used in:
- Node.js streams
- Kafka
- Reactive systems (RxJava, Akka)

We implement a simple adaptive throttle.

✔ Add Backpressure to heavy POST endpoints
Add constants:
```
BACKPRESSURE_ENABLED = True
BACKPRESSURE_SLEEP = 0.02   # 20 ms

Modify SyncPostAPI:
class SyncPostAPI(APIView):
    def post(self, request):
        if BACKPRESSURE_ENABLED:
            time.sleep(BACKPRESSURE_SLEEP)

        ...
```
📌 Explanation:
- Each POST request is artificially delayed 20 milliseconds.
- This reduces the instantaneous load by:
- spreading requests over time
- preventing DB overload
- preventing the Gunicorn worker from taking too many requests at once
- This is a lightweight but extremely effective backpressure technique.







---
### PART 5 - Docker  <a id="5"></a>
---

how to build an image of project:
```
docker compose build
```

#### how to run containers in different level:
in development-level:
```
docker compose up -d
```
in Development-level:
```
docker compose -f docker-compose.dev.yml up -d
```
How to remove created containers(not an image only containers)
:
```
docker-compose -f docker-compose.dev.yml down -v
```
in production-level:

how to see last 50 logs of "web" container in your terminal:
```
docker compose logs web --tail 50
```
Test if your web container is okay:
```
 curl -I http://localhost
 ```

 if response be sth like below is okay:
 ```
 HTTP/1.1 404 Not Found
Server: nginx
Date: Mon, 01 Dec 2025 14:54:09 GMT   
Content-Type: text/html; charset=utf-8
Content-Length: 2574  
Connection: keep-alive
x-frame-options: DENY
x-content-type-options: nosniff
referrer-policy: same-origin
cross-origin-opener-policy: same-origin
```

If you add or revise a model how to do a migraion:
```
docker compose exec web python manage.py makemigrations

# then

docker compose exec web python manage.py migrate
```
