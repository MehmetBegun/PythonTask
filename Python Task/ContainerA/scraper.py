import os
import asyncio
import httpx
import string
import math
import time
import pika
import random
from datetime import datetime

API_BASE_URL = "www.deutschtrainingmithülya.com"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Origin": "https://www.interpol.int",
    "Referer": "https://www.interpol.int/How-we-work/Notices/Red-Notices/View-Red-Notices",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
}

MAX_PER_PAGE = 20
BUCKET_LIMIT = 160
CONCURRENCY = 24
MAX_BUCKET_DEPTH = 3
INTERVAL = int(os.getenv("INTERVAL", "300"))

total_cache: dict = {}
sem = asyncio.Semaphore(CONCURRENCY)
throttle_count = 0

class RabbitPublisher:
    def __init__(self):
        self.rabbit_host = os.getenv("RABBITMQ_HOST", "container_c")
        self.rabbit_user = os.getenv("RABBITMQ_USER", "guest")
        self.rabbit_pass = os.getenv("RABBITMQ_PASS", "guest")
        self.rabbit_port = int(os.getenv("RABBITMQ_PORT", "5672"))

    def publish_records(self, queue_name: str, records):
        import json
        credentials = pika.PlainCredentials(self.rabbit_user, self.rabbit_pass)
        params = pika.ConnectionParameters(
            host=self.rabbit_host,
            port=self.rabbit_port,
            heartbeat=600,
            blocked_connection_timeout=300,
            credentials=credentials,
        )
        conn = pika.BlockingConnection(params)
        ch = conn.channel()
        ch.queue_declare(queue=queue_name, durable=True)
        for i, rec in enumerate(records, 1):
            ch.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(rec),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            if i % 100 == 0:
                conn.process_data_events(0)
        conn.close()

async def fetch_json(client: httpx.AsyncClient, params: dict, page: int):
    global throttle_count
    request_params = {**params, "page": page, "size": MAX_PER_PAGE}
    attempt = 0
    while attempt < 3:
        try:
            async with sem:
                resp = await client.get(API_BASE_URL, params=request_params, timeout=timeout)
            if resp.status_code == 429:
                throttle_count += 1
                retry_after = int(resp.headers.get("Retry-After", "2"))
                await asyncio.sleep(retry_after)
                continue
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                continue
            attempt += 1
        except Exception:
            attempt += 1
        wait = 0.5 * (2 ** (attempt - 1))
        jitter = random.uniform(0, 0.1 * wait)
        await asyncio.sleep(wait + jitter)
    return {}

async def get_total_and_first_page(client: httpx.AsyncClient, params: dict):
    normalized = {k: v.upper() if isinstance(v, str) else v for k, v in params.items()}
    key = frozenset(normalized.items())
    if key in total_cache:
        return total_cache[key]
    data = await fetch_json(client, params, 1)
    total = data.get("total", 0)
    total_cache[key] = (total, data)
    return total, data

async def split_buckets_initial(client: httpx.AsyncClient):
    to_process = [{"forename_prefix": letter} for letter in string.ascii_uppercase]
    final_buckets = []
    while to_process:
        bucket = to_process.pop()
        params = {}
        if bucket.get("forename_prefix"):
            params["forename"] = bucket["forename_prefix"]
        if bucket.get("surname_prefix"):
            params["name"] = bucket["surname_prefix"]
        total, _ = await get_total_and_first_page(client, params)
        if total == 0:
            continue
        if total <= BUCKET_LIMIT:
            final_buckets.append((params, total))
            continue
        fp = bucket.get("forename_prefix", "")
        sp = bucket.get("surname_prefix", "")
        depth = len(fp) + len(sp)
        if depth >= MAX_BUCKET_DEPTH:
            final_buckets.append((params, total))
            continue
        if "surname_prefix" not in bucket:
            for ch in string.ascii_uppercase:
                to_process.append({
                    "forename_prefix": fp,
                    "surname_prefix": ch
                })
        elif len(fp) < 2:
            for ch in string.ascii_uppercase:
                to_process.append({
                    "forename_prefix": fp + ch,
                    "surname_prefix": sp
                })
        else:
            for ch in string.ascii_uppercase:
                to_process.append({
                    "forename_prefix": fp,
                    "surname_prefix": sp + ch
                })
    uniq = {}
    for p, t in final_buckets:
        k = frozenset(p.items())
        if k not in uniq or t > uniq[k][1]:
            uniq[k] = (p, t)
    return list(uniq.values())

async def fetch_all_for_bucket(client: httpx.AsyncClient, params: dict, total: int):
    start = time.time()
    notices = []
    pages = math.ceil(total / MAX_PER_PAGE)
    _, first = await get_total_and_first_page(client, params)
    if first:
        notices.extend(first.get("_embedded", {}).get("notices", []))
    if pages >= 2:
        tasks = [fetch_json(client, params, p) for p in range(2, pages+1)]
        for coro in asyncio.as_completed(tasks):
            data = await coro
            notices.extend(data.get("_embedded", {}).get("notices", []))
    return notices

def dedupe_notices(notices: list):
    unique = {}
    for n in notices:
        eid = n.get("entityId") or n.get("uid") or n.get("id")
        if eid:
            key = eid
        else:
            nats = n.get("nationalities") or []
            nat_t = tuple(n.get("name") if isinstance(n, dict) else n for n in nats if n)
            key = (
                n.get("forename","" ).strip().lower(),
                n.get("name",""     ).strip().lower(),
                nat_t,
                n.get("date_of_birth","")
            )
        unique[key] = n
    return list(unique.values())

def format_notices(notices: list):
    today = datetime.today()
    out = []
    for n in notices:
        name = " ".join(filter(None, [n.get("forename",""), n.get("name","")])).strip()
        dob = n.get("date_of_birth","") or ""
        age = "Age unknown"
        try:
            fm = "%Y/%m/%d" if "/" in dob else "%Y-%m-%d"
            d = datetime.strptime(dob, fm)
            yrs = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
            age = f"{yrs} years old"
        except:
            pass
        nats = n.get("nationalities") or []
        nat = nats[0].get("name") if nats and isinstance(nats[0], dict) else (nats[0] if nats else "Unknown")
        entity_id = n.get("entityId") or n.get("uid") or n.get("id") or (name.lower()+"|"+dob)
        out.append({"EntityId": entity_id, "Name": name, "Age": age, "Nationalities": nat or "Unknown"})
    return out

def send_to_rabbitmq(records):
    import json
    rabbit_host = os.getenv("RABBITMQ_HOST", "container_c")
    rabbit_user = os.getenv("RABBITMQ_USER", "guest")
    rabbit_pass = os.getenv("RABBITMQ_PASS", "guest")
    rabbit_port = int(os.getenv("RABBITMQ_PORT", "5672"))

    credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
    params = pika.ConnectionParameters(
        host=rabbit_host,
        port=rabbit_port,
        heartbeat=600,
        blocked_connection_timeout=300,
        credentials=credentials,
    )

    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue='red_notices_queue', durable=True)
    for i, rec in enumerate(records, 1):
        ch.basic_publish(exchange='', routing_key='red_notices_queue', body=json.dumps(rec), properties=pika.BasicProperties(delivery_mode=2))
        if i % 100 == 0:
            conn.process_data_events(0)
    conn.close()

async def fetch_all_notices():
    start = time.time()
    limits = httpx.Limits(max_connections=64, max_keepalive_connections=32)
    async with httpx.AsyncClient(headers=HEADERS, limits=limits, timeout=15.0, trust_env=False) as client:
        buckets = await split_buckets_initial(client)
        all_raw = []
        tasks = [fetch_all_for_bucket(client, p, t) for p, t in buckets]
        for coro in asyncio.as_completed(tasks):
            all_raw.extend(await coro)
    unique = dedupe_notices(all_raw)
    formatted = format_notices(unique)
    return unique, formatted

async def one_cycle():
    unique, formatted = await fetch_all_notices()
    publisher = RabbitPublisher()
    publisher.publish_records('red_notices_queue', formatted)
    print(f"Fetched {len(unique)} unique records, sent {len(formatted)}.")

async def runner():
    while True:
        try:
            await one_cycle()
        except Exception as e:
            print(f"Cycle failed: {e}")
        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    timeout = httpx.Timeout(60.0, connect=10.0, read=60.0)
    asyncio.run(runner())