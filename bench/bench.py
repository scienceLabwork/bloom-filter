#NOTE: python bench/bench.py | tee bench/results.txt
import os
import platform
import sys
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bloomfilter import BloomFilter

CAPACITY = 10_00_000
NUM_PROBES = 5_00_000
ERROR_RATES = [0.01, 0.001]

MEMBER = "user-{id}@example.com"
NON_MEMBER = "other-{id}@example.com"

def make_items(template, count):
    return [template.format(id=str(i).zfill(7)) for i in range(1, count + 1)]

def set_memory_bytes(s):
    # getsizeof(set) counts only the set's table, so add every string it holds.
    return sys.getsizeof(s) + sum(sys.getsizeof(x) for x in s)

def run(p, items, probes, set_bytes):
    bf = BloomFilter(CAPACITY, p)

    start = time.perf_counter()
    bf.update(items)
    add_time = time.perf_counter() - start
 
    assert all(x in bf for x in items[:10_000]), "false negative found, filter is broken"

    start = time.perf_counter()
    false_positives = sum(x in bf for x in probes)
    lookup_time = time.perf_counter() - start

    size_mb = bf.size_bytes / 1e6
    return {
        "target": p,
        "bits_per_item": bf.m / CAPACITY,
        "k": bf.k,
        "size_mb": size_mb,
        "times_smaller": (set_bytes / 1e6) / size_mb,
        "measured_fpr": false_positives / len(probes),
        "adds_per_sec": len(items) / add_time,
        "lookups_per_sec": len(probes) / lookup_time,
    }

def main():
    print(f"Python {platform.python_version()} on {platform.system()} {platform.machine()}")
    print("Building test data...")
    items = make_items(MEMBER, CAPACITY)
    probes = make_items(NON_MEMBER, NUM_PROBES)

    ref = set(items)
    set_bytes = set_memory_bytes(ref)
    del ref

    avg_len = sum(len(x) for x in items) / len(items)
    print(f"{CAPACITY:,} strings, ~{avg_len:.0f} chars each, {NUM_PROBES:,} non-member probes\n")
    print(f"Python set (exact): {set_bytes / 1e6:.1f} MB\n")

    header = (f"{'Target FPR':>10} | {'bits/item':>9} | {'k':>2} | {'Size MB':>7} | "
              f"{'vs set':>7} | {'Measured FPR':>12} | {'adds/s':>9} | {'lookups/s':>9}")
    print(header)
    print("-" * len(header))
    for p in ERROR_RATES:
        r = run(p, items, probes, set_bytes)
        print(f"{r['target']:>10} | {r['bits_per_item']:>9.1f} | {r['k']:>2} | {r['size_mb']:>7.2f} | "
              f"{r['times_smaller']:>6.0f}x | {r['measured_fpr']:>12.5f} | "
              f"{r['adds_per_sec']:>9,.0f} | {r['lookups_per_sec']:>9,.0f}")

if __name__ == "__main__":
    main()