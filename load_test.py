import argparse
import concurrent.futures
import random
import threading
import time
import urllib.error
import urllib.request


ENDPOINTS = {
    "health": "/api/health",
    "courses": "/api/courses",
    "rankings": "/api/rankings",
}


def parse_mix(mix_string):
    weights = []
    for item in mix_string.split(","):
        key, weight = item.split(":", 1)
        key = key.strip().lower()
        if key not in ENDPOINTS:
            raise ValueError(f"Unknown endpoint key in mix: {key}")
        w = int(weight.strip())
        if w <= 0:
            raise ValueError("Mix weights must be positive integers")
        weights.append((key, w))
    if not weights:
        raise ValueError("Mix cannot be empty")
    return weights


def percentile(values, pct):
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int((len(sorted_values) - 1) * pct)
    return sorted_values[index]


def run_load_test(args):
    mix = parse_mix(args.mix)
    choices = [item[0] for item in mix]
    weights = [item[1] for item in mix]

    end_time = time.perf_counter() + args.duration
    latencies_ms = []
    status_counts = {}
    error_count = 0
    total_requests = 0
    lock = threading.Lock()

    def worker():
        nonlocal error_count, total_requests
        while time.perf_counter() < end_time:
            endpoint_key = random.choices(choices, weights=weights, k=1)[0]
            url = args.base_url.rstrip("/") + ENDPOINTS[endpoint_key]
            start = time.perf_counter()
            status_code = None
            failed = False
            try:
                request = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(request, timeout=args.timeout) as response:
                    status_code = response.status
                    response.read(64)
            except urllib.error.HTTPError as exc:
                status_code = exc.code
                failed = True
            except Exception:
                failed = True
            elapsed_ms = (time.perf_counter() - start) * 1000

            with lock:
                total_requests += 1
                latencies_ms.append(elapsed_ms)
                if status_code is not None:
                    status_counts[status_code] = status_counts.get(status_code, 0) + 1
                if failed:
                    error_count += 1

    start_wall = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(worker) for _ in range(args.concurrency)]
        for future in futures:
            future.result()
    elapsed_wall = max(time.perf_counter() - start_wall, 0.001)

    rps = total_requests / elapsed_wall
    error_rate = (error_count / total_requests) if total_requests else 1.0
    p50 = percentile(latencies_ms, 0.50)
    p95 = percentile(latencies_ms, 0.95)
    p99 = percentile(latencies_ms, 0.99)

    print("Load test summary")
    print(f"Base URL: {args.base_url}")
    print(f"Duration: {args.duration}s")
    print(f"Concurrency: {args.concurrency}")
    print(f"Requests: {total_requests}")
    print(f"RPS: {rps:.2f}")
    print(f"Error rate: {error_rate * 100:.2f}%")
    print(f"Latency p50: {p50:.1f} ms")
    print(f"Latency p95: {p95:.1f} ms")
    print(f"Latency p99: {p99:.1f} ms")
    print(f"Statuses: {dict(sorted(status_counts.items()))}")

    checks = []
    checks.append((error_rate <= args.max_error_rate, f"error_rate <= {args.max_error_rate * 100:.2f}%"))
    checks.append((p95 <= args.max_p95_ms, f"p95 <= {args.max_p95_ms:.1f} ms"))
    checks.append((rps >= args.min_rps, f"rps >= {args.min_rps:.2f}"))

    failures = [label for ok, label in checks if not ok]
    if failures:
        print("\nFAIL: threshold checks failed")
        for item in failures:
            print(f"- {item}")
        return 1

    print("\nPASS: all threshold checks passed")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Lightweight HTTP load test for Class Rank")
    parser.add_argument("--base-url", default="http://127.0.0.1:5500", help="Base URL for API calls")
    parser.add_argument("--duration", type=int, default=20, help="Test duration in seconds")
    parser.add_argument("--concurrency", type=int, default=25, help="Number of concurrent workers")
    parser.add_argument("--timeout", type=float, default=4.0, help="Per-request timeout in seconds")
    parser.add_argument("--mix", default="health:2,courses:5,rankings:3", help="Endpoint mix as key:weight pairs")
    parser.add_argument("--max-error-rate", type=float, default=0.02, help="Fail if error rate exceeds this fraction")
    parser.add_argument("--max-p95-ms", type=float, default=700.0, help="Fail if p95 latency exceeds this value")
    parser.add_argument("--min-rps", type=float, default=20.0, help="Fail if throughput is below this RPS")
    return parser


if __name__ == "__main__":
    parser = build_parser()
    arguments = parser.parse_args()
    raise SystemExit(run_load_test(arguments))
