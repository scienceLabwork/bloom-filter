# Bloom Filter (from scratch)

I built this Bloom filter in plain Python to really understand how it works, not just use a library. No dependencies, only the standard library (`hashlib`, `struct`, `math`).

A Bloom filter tells you if you have **maybe** seen something before or **definitely not**. It never stores the actual data, only bits. That's why it's so small. The catch is it can sometimes say "maybe" for something you never added (false positive), but it will never say "no" for something you did add.

## Why I built this

Where I see this being useful: checking if a username is taken, if a URL is already crawled, or if a key might be on disk before doing an expensive DB call. If the filter says "no", you skip the DB completely.

## Results

Ran on my MacBook (Apple Silicon, Python 3.11), 10,00,000 email-like strings, tested against 5,00,000 strings that were never added.

| | Size | vs Python set | Measured false positive rate |
|---|---|---|---|
| Python `set` | 106.6 MB | 1x | 0% (exact) |
| Bloom, target 1% | 1.20 MB | **89x smaller** | 1.006% |
| Bloom, target 0.1% | 1.80 MB | **59x smaller** | 0.103% |

Measured rate came almost exactly on target, which tells me the sizing math and the hashing are both right.

**NOTE:** The memory saving changes a bit by machine and Python version because the size of Python's `set` changes. I have seen 84x to 89x. The Bloom filter itself is always 1.2 MB at 1% target.

Speed at 1% target is around 5.2 lakh adds/sec and 6.9 lakh lookups/sec (a bit slower at 0.1% because k is 10 instead of 7). It's pure Python so not super fast, a C or Go version would be much faster.

Full output is in `bench/results.txt`.

## How it works

**1. Sizing**

For `n` = capacity and `p` = error rate:

```
m = -n * ln(p) / (ln 2)^2      -> number of bits
k = (m / n) * ln 2             -> number of hash functions
```

For 1% this comes to about 9.6 bits per item and k = 7. Doesn't matter how long the string is, a set has to keep the full string.

**2. Hashing (double hashing)**

Instead of running 7 different hash functions, I take one `blake2b` hash of 16 bytes and split it into two 64-bit numbers `h1` and `h2`. Then:

```
index_i = (h1 + i * h2) % m
```

This trick is from Kirsch and Mitzenmacher, gives the same accuracy as k separate hashes. I also do `h2 |= 1` to make it odd, otherwise if `h2` shares a factor with `m` the positions can repeat and false positives go up.

I didn't use Python's `hash()` because it's randomized for strings every time the program starts, so a saved filter would give wrong answers after restart.

**3. Bits**

Bits are stored in a `bytearray`. For bit `i`:
- byte = `i >> 3` (same as `i // 8`)
- bit inside byte = `i & 7` (same as `i % 8`)

Set: `bits[i>>3] |= 1 << (i&7)`
Check: `bits[i>>3] & (1 << (i&7))`

## Features

- `add`, `update` (add many), and `in` for lookup
- Works with both `str` and `bytes`, same item either way
- `estimated_items()` guesses how many unique items are inside just from how many bits are set. Duplicates don't increase it.
- `expected_error_rate(n)` uses `(1 - e^(-kn/m))^k` to predict the false positive rate
- `union()` merges two filters by OR-ing the bits. Both need the same `m` and `k`, else it raises `ValueError`
- `to_bytes()` / `from_bytes()` to save and load. I store a 24 byte header (`capacity`, `error_rate`, items added) using `struct.pack("<QdQ")` and then the raw bits. Without the header you can't get `k` back and every lookup after loading would be wrong.

## Usage

```python
from bloomfilter import BloomFilter

bf = BloomFilter(capacity=10_00_000, error_rate=0.01)
bf.add("rudra@gmail.com")
bf.update(["a@x.com", "b@x.com"])

"rudra@gmail.com" in bf    # True
"nobody@x.com" in bf       # False (almost always)

# save and load
with open("users.bloom", "wb") as f:
    f.write(bf.to_bytes())

with open("users.bloom", "rb") as f:
    bf = BloomFilter.from_bytes(f.read())
```

## Run it

Needs **Python 3.10+** (I use `int.bit_count()`). On Mac use `python3` if `python` is not found, or activate the venv first.

**1. Setup (one time)**

```
git clone https://github.com/scienceLabwork/bloom-filter.git
cd bloom-filter
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**2. Try the demo**

```
python main.py
```

It walks through everything: add and check, stats, save and load, union, and what happens when you overfill the filter. The last part is my favourite, at 3x capacity the false positive rate jumps from about 1% to about 46%.

**3. Run the tests**

```
python -m pytest -q
```

All tests should pass. To run just one test:

```
python -m pytest -q -k test_no_false_negatives
```

**4. Run the benchmark**

```
python bench/bench.py
```

Takes around 10 seconds. To save the output like I did:

```
python bench/bench.py | tee bench/results.txt
```

Your numbers will be a bit different from mine, depends on the machine and Python version.

## Tests

- No false negatives on 1,00,000 items
- Measured false positive rate stays close to target for 10%, 1% and 0.1%
- Filling 3x over capacity: the measured rate matches the formula within 10%, and it's clearly broken (above 20%)
- Item estimate within 3% of the real count, and duplicates don't inflate it
- Union keeps items from both sides, and rejects filters of different size
- Save and load gives the same filter, and cut-off data raises `ValueError`
- Can still add after loading a saved filter
- `str` and `bytes` versions of the same text are treated as the same item
- Bad capacity or error rate is rejected

## Limits

- You can't delete an item. Turning off a bit might break another item sharing that bit. A counting Bloom filter fixes this but uses more memory.
- You can't list what's inside, the bits don't remember who set them.
- You have to know roughly how many items you'll add. If you go over capacity the error rate climbs fast (the 3x test shows it).
- The set comparison counts the strings themselves. A Bloom filter can't give the strings back, so it's not a replacement for a set, it's a cheap check in front of one.

## Files

```
bloomfilter/__init__.py   the filter
main.py                   quick demo of every feature
tests/test_bloom.py       tests
bench/bench.py            benchmark
bench/results.txt         my benchmark output
```

Rudra Shah · [GitHub](https://github.com/scienceLabwork) · [rudrashah.in](https://rudrashah.in)