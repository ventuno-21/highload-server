### [Part 1](#intro) - Introduction
### [Part 2](#install) - How to run
### [Part 3](#test) - How to test
### [Part 3-1](#ex) - Full example of testing
### [Part 4](#production) - Best way to run in Production


---
### PART 1 -Introduction  <a id="intro"></a>
---

Simple FastAPI + Async SQLAlchemy example (Dockerized)

This project is a Dockerized FastAPI application designed to handle high-concurrency requests efficiently. It uses SQLAlchemy 2 (async) for database interactions and includes two main endpoints: a GET endpoint to fetch items and a POST endpoint to create new items. The application is production-ready, running with Gunicorn and UvicornWorker, which allows multiple worker processes and threads to handle hundreds of simultaneous requests while maintaining fast response times.

Additionally, the project supports automatic database migrations using Alembic, making it easy to keep the database schema up-to-date. Load testing can be performed using tools like wrk for GET-heavy endpoints and hey for POST-heavy endpoints, ensuring that the service performs reliably under real-world traffic. This setup makes the project scalable, stable, and suitable for deployment in production environments.

```
fastapi-sqlasync/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ db.py
│  ├─ crud.py
|─ alembic\  
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
└─ alembic.ini
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
first

```
docker-compose run --rm api alembic revision --autogenerate -m "create items table"
```
then 
```
docker-compose run --rm api alembic upgrade head
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
  0.001 [50] |
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

Why use Gunicorn + UvicornWorker in Production?  

FastAPI itself runs on an ASGI server like Uvicorn or Hypercorn. But:   

Uvicorn alone runs only a single process.

If the CPU or thread is busy, other requests have to wait.

Gunicorn can spawn multiple worker processes.

Each worker is independent and can handle requests in parallel.

UvicornWorker tells Gunicorn:

“I am async, so I can handle I/O-bound requests (DB, network) concurrently.”

Advantages:

High concurrency: hundreds of requests can be processed simultaneously.

Stability: if one worker crashes, the others continue running.

CPU utilization: multiple workers make full use of CPU cores.

Async + Sync combination: threads for concurrent requests, async for I/O-heavy tasks.

####  Do we always need this setup?

Short answer: Not always, but for **production** and **high load**, it is **almost** always recommended.

When it’s not needed:
Testing or development environment with few users.  
Very lightweight apps or simple APIs with no heavy DB/I/O.  
When you just want to run Uvicorn directly for local testing.  

When it is recommended:  
Production with many concurrent users or I/O-heavy requests.  
Projects with DB, Redis, file I/O, or external network calls.  
When you want your app to be crash-proof and scalable.  

#### Summary

**Development**: Uvicorn alone is enough.

**Production**: Gunicorn + UvicornWorker is better, especially if:

1. You have multiple CPU cores  
2. You expect many concurrent requests
3. Your app is async-heavy 

💡 Tip: For very high load, you can also add Nginx + Gunicorn + multiple containers later for extra scalability.


####  Command details
Full command:
```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4 --threads 2
```
1. Gunicorn  
Gunicorn is a WSGI/ASGI server that runs Python apps in production.

Its main job is managing multiple workers and distributing incoming requests among them.

Reason for using: Uvicorn alone is fine for development or low load, but for production, Gunicorn + workers is better.

2. app.main:app

This tells Gunicorn which FastAPI app to run:

app → folder name of your project  
main → the file main.py  
app → the FastAPI instance (app = FastAPI(...))  

Without this, Gunicorn wouldn’t know which app to start.

3.  -k uvicorn.workers.UvicornWorker

-k specifies the worker class.

UvicornWorker is an async worker, which can handle multiple concurrent I/O-bound requests (like DB or network calls).  
Without this, Gunicorn defaults to synchronous workers, which cannot properly handle async FastAPI endpoints.  

4.  --bind 0.0.0.0:8000

This makes Gunicorn listen on all network interfaces (0.0.0.0) and port 8000.  
Important so that the container can accept requests from outside or via Docker Compose.  

5.  --workers 4

Number of independent processes Gunicorn runs.  
Each worker can handle multiple requests.  
Rule of thumb: workers ≈ number of CPU cores.  

Example: 4 CPU cores → 4 workers.  

6.  --threads 2

Each worker can spawn multiple threads.  
More threads allow higher concurrency.  
Example: 4 workers × 2 threads → higher capacity for concurrent requests.  

🔹 Summary

This command ensures:

FastAPI runs safely and reliably in production.  
Multiple processes + threads increase concurrency.  
Async I/O (DB, Redis, RabbitMQ) is properly handled.  
In Docker Compose, it can handle many simultaneous requests efficiently.  

💡 Tip:

You can also add --worker-connections → maximum simultaneous connections per async worker.  

For high load (like 1000 concurrent requests), tuning workers, threads, and DB pool_size is important for optimal throughput.


### How It Works

```

               ┌─────────────────────────────┐
               │        Gunicorn Master       │
               └─────────────┬───────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
   ┌───────────────┐                     ┌───────────────┐
   │  Worker 1     │                     │  Worker 2     │
   │ (Process)     │                     │ (Process)     │
   └─────┬─────────┘                     └─────┬─────────┘
         │                                      │
 ┌───────┴───────┐                      ┌──────┴────────┐
 │ Thread 1      │                      │ Thread 1      │
 │ Async handling│                      │ Async handling│
 ├───────────────┤                      ├───────────────┤
 │ Thread 2      │                      │ Thread 2      │
 │ Async handling│                      │ Async handling│
 └───────────────┘                      └───────────────┘

... continues for Worker 3, Worker 4 if --workers=4
```

Gunicorn Master Process

Controls all workers.

Distributes incoming HTTP requests to the workers.

Monitors them, restarts crashed workers automatically.

Workers (Processes)

Each worker is a separate Python process.

Multiple workers allow CPU-bound tasks to run in parallel.

In our setup, --workers=4 means 4 separate processes.

Threads in Each Worker

Each worker can spawn multiple threads (--threads=2).

Threads help with more concurrent requests, especially small CPU-bound tasks.

Async Handling Inside Worker

Each thread can handle multiple async I/O tasks (DB queries, network calls) concurrently.

This is done by UvicornWorker, which allows async FastAPI endpoints to be non-blocking.

So even if 1 thread is waiting for a DB response, other requests are processed.

🔹 Total Concurrency Estimate

Let’s say:

--workers=4  
--threads=2  

Each async worker can handle dozens of async connections

Then total concurrency is roughly:
```
workers × threads × async connections per thread
= 4 × 2 × ~50
≈ 400–500 simultaneous requests
```

Actual number depends on DB pool size, network latency, and CPU usage.

🔹 Key Takeaways

Single Uvicorn → only 1 process → limited by CPU → can block requests.

Gunicorn + UvicornWorker → multiple processes + async → high concurrency.

Threads + async → more requests handled concurrently per worker.

Ideal for production with many simultaneous users and I/O-heavy endpoints.

