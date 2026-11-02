#NOTE: Small demo of every feature in the Bloom filter. Run: python main.py
import os
import time
from bloomfilter import BloomFilter

def section(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

def basic_demo():
    section("1. Add and check")
    bf = BloomFilter(capacity=1000, error_rate=0.01)
    print(f"Filter for 1000 items at 1% error -> m = {bf.m} bits, k = {bf.k}, size = {bf.size_bytes} bytes")

    users = ["rudra", "jignesh", "oliver"]
    bf.update(users)
    print(f"Added: {users}")

    for name in ["rudra", "oliver", "rudraa", "priyaka"]:
        result = "maybe present" if name in bf else "definitely not present"
        print(f"  '{name}' -> {result}")
    return bf

def stats_demo(bf):
    section("2. Stats")
    print(f"add() calls        : {bf._added}")
    print(f"Bits set           : {bf.bits_set()} out of {bf.m}")
    print(f"Estimated items    : {bf.estimated_items()}")
    print(f"Current error rate : {bf.expected_error_rate():.2e}  (tiny, only 3 items in a 1000 item filter)")

def save_load_demo(bf):
    section("3. Save and load")
    #NOTE: saved filters go in blooms_saved/, file name has date and time so nothing gets overwritten
    os.makedirs("blooms_saved", exist_ok=True)
    now = time.localtime()
    file_name = 'user_'+str(time.strftime("%Y_%m_%d_%H_%M", now))+'.bloom'
    path = os.path.join("blooms_saved", file_name)

    with open(path, "wb") as file:
        file.write(bf.to_bytes())
    print(f"Saved {os.path.getsize(path)} bytes to {path}")

    with open(path, "rb") as file:
        loaded = BloomFilter.from_bytes(file.read())

    print(f"'rudra' in loaded filter : {'rudra' in loaded}")
    loaded.add("new_user")
    print(f"Added 'new_user' after loading, found: {'new_user' in loaded}")


def union_demo(bf):
    section("4. Union of two filters")
    fruits = BloomFilter(capacity=1000, error_rate=0.01)
    fruits.update(["apple", "orange", "mango"])

    merged = bf.union(fruits)
    for item in ["rudra", "apple", "mango", "banana"]:
        print(f"  '{item}' in merged -> {item in merged}")

    #NOTE: union needs same m and k, so different capacity should fail
    try:
        bf.union(BloomFilter(capacity=50, error_rate=0.01))
    except ValueError:
        print("Union with a different sized filter -> ValueError (as expected)")

def overfill_demo():
    section("5. What happens if you add too much")
    capacity = 1000
    bf = BloomFilter(capacity, 0.01)
    probes = [f"other-{i}" for i in range(10_000)]
    added = 0
    for times in [1, 2, 3]:
        target = capacity * times
        bf.update(f"user-{i}" for i in range(added, target))
        added = target
        measured = sum(p in bf for p in probes) / len(probes)
        print(f"  {target:>5} items ({times}x capacity) -> false positive rate {measured:.2%}")

if __name__ == "__main__":
    bf = basic_demo()
    stats_demo(bf)
    save_load_demo(bf)
    union_demo(bf)
    overfill_demo()