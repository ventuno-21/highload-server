### [Part 1](#intro) - Introduction
### [Part 2](#install) - How to run
### [Part 3](#test) - How to test
### [Part 3-1](#ex) - Full example of testing
### [Part 4](#production) - Best way to run in Production
### [Part 4-1](#guni) - Why Gunicorn
### [Part 4-2](#load) - Why Load balancing
### [Part 4-3](#rate) - Why Rate limiting
### [Part 4-3-1](#431) - Why do we do Rate Limiting in Nginx?
### [Part 4-3-2](#432) - Why not do Rate Limiting inside the API? 

---
### PART 1 -Introduction  <a id="intro"></a>
---

The architecture we implemented provides a scalable and high-performance web service. Gunicorn serves as the primary web server for running FastAPI, and by using async workers, it can efficiently handle a large number of concurrent requests. Each FastAPI instance processes incoming requests while avoiding blocking due to I/O operations, which improves response time and overall system performance.
On top of that, NGINX is used as both a Load Balancer and Rate Limiter. The Load Balancer distributes incoming traffic across multiple FastAPI instances, ensuring high availability and enabling the system to scale horizontally by adding more servers. Meanwhile, Rate Limiting protects the system from overload and potential abuse by limiting the number of requests a single IP can send within a given timeframe.

The combination of Gunicorn for async request handling, NGINX for load distribution, and rate limiting results in a system that is both reliable and resilient under high load. This setup ensures that even during traffic spikes or potential DoS attacks, the service can continue to respond effectively to users while maintaining stability and performance.

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
```

          ┌──────────────┐
          │   Clients    │
          │(Users / API) │
          └──────┬───────┘
                 │ HTTP Requests
                 ▼
          ┌──────────────┐
          │    NGINX     │
          │ Load Balancer│
          │ + Rate Limit │
          └──────┬───────┘
                 │
 ┌───────────────┼───────────────┐
 ▼               ▼               ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│ API 1   │   │ API 2   │   │ API 3   │
│FastAPI  │   │FastAPI  │   │FastAPI  │
│Gunicorn │   │Gunicorn │   │Gunicorn │
└────┬────┘   └────┬────┘   └────┬────┘
     │             │             │
     ▼             ▼             ▼
┌───────────────────────────────────┐
│          PostgreSQL DB            │
│  Async connections via SQLAlchemy │
└───────────────────────────────────┘
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
Proceed this step with your specific comment:  
  
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
### Part 4-1 -  Why Gunicorn <a id="Guni"></a>
---
Gunicorn / UvicornWorkers

Main purpose: run FastAPI/Django and handle requests.

Advantages:  
You can specify the number of workers and threads → can handle multiple concurrent requests.  
Using async workers (UvicornWorker) allows I/O-heavy tasks (like DB/network) to avoid blocking.  

Limitations:  
The number of workers is limited by CPU and RAM → if 1000 requests come simultaneously, a queue may form or requests may timeout.


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
               │        Gunicorn Master      │
               └─────────────┬───────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
   ┌───────────────┐                     ┌───────────────┐
   │  Worker 1     │                     │  Worker 2     │
   │ (Process)     │                     │ (Process)     │
   └─────┬─────────┘                     └─────┬─────────┘
         │                                     │
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

- Single Uvicorn → only 1 process → limited by CPU → can block requests.
- Gunicorn + UvicornWorker → multiple processes + async → high concurrency.
- Threads + async → more requests handled concurrently per worker.
Ideal for production with many simultaneous users and I/O-heavy endpoints.

---
### Part 4-2 -  Why Load Balancer (NGINX) <a id="load"></a>
---
Main purpose: distribute load between multiple instances of the application.  

Advantages:  
- You can run multiple Gunicorn/FastAPI instances and balance traffic between them.  
- If one instance fails, the others continue → high availability.  

Limitations:   
- The load balancer cannot prevent attacks or floods by itself.  
- It only distributes load, it does not control traffic.  

---
### Part 4-2 -  Rate Limiting (NGINX) <a id="rate"></a>
---

Main purpose: prevent overload and attacks (DoS, flood).

Advantages:
- Limit the number of requests per IP per time unit → protects the system from saturation.
- When traffic is high, it prevents a few IPs from consuming all resources.

Limitations:
- Rate limiting cannot perform load balancing.
- It only protects against excessive requests, it does not improve performance.

✅ Why use all three together?  
Component	Main Purpose  
- Gunicorn / Uvicorn	Run the app, handle concurrency  
- Load Balancer	Distribute load between instances, high availability  
- Rate Limiting	Protect against floods and overload  

Together:
Gunicorn → process requests  
- NGINX Load Balancer → distribute requests between multiple Gunicorn instances
- NGINX Rate Limit → prevent any single IP from consuming too many resources
- Result → a scalable, stable, and attack-resistant system with low latency.

💡 Real-world example:   
Suppose 1000 users send POST requests at the same time:  
Without Rate Limiting: all requests go to Gunicorn → long queues → timeout and crash.  
Without Load Balancer: only one instance handles requests → CPU/RAM limits reached.  
With both: requests are distributed between instances, and no single IP can monopolize resources → system stays healthy.  

---
### Part 4-3-1 -  Why do we do Rate Limiting in Nginx? <a id="431"></a>
---
 Why do we do Rate Limiting in Nginx?  
Advantages:  
- Reduces load on the API
- Requests that exceed the limit never reach the application.

Example: 1,000 simultaneous requests → 900 are blocked → API handles only 100 requests.

This saves CPU and memory on your app and database.

High performance

Nginx is written in C and handles rate limiting very efficiently.

No Python/Django/FastAPI overhead.

Protects against attacks (DDoS / spam)

Blocks abusive traffic before it reaches your API.

Works for multiple APIs

If you have multiple services behind a load balancer, Nginx can handle rate limiting centrally.

---
### Part 4-3-2 -  Why not do it inside the API? <a id="432"></a>
---

Disadvantages:  
- Adds load to the API  
- Even requests that should be blocked reach your application.  
- CPU, memory, and database connections are consumed unnecessarily.  
- More complexity  
- You need custom code for rate limiting, usually with Redis or a database.  
- Managing bursts and concurrency is harder.  
- Less effective under high load
- With thousands of simultaneous requests, the API itself can get overwhelmed before rate limiting takes effect.


### Summary of benefits

- Reduces API and database load
- Protects the app before it processes requests
- Better handling of high traffic scenarios
- Easier for multiple services behind a load balancer

🔹 Practical conclusion
Where to apply	Best for	Disadvantages
Nginx / Load Balancer	High load, multiple services, DDoS protection	Less flexibility for complex API logic (e.g., per-user rules)
Inside API	Complex rules (e.g., per user, subscription tier)	Adds load to API, slower under high traffic

💡 Recommended hybrid approach:

- General/simple rate limiting → handled by Nginx
- Advanced per-user rules → handled inside the API
