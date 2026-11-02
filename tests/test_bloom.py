import pytest
from bloomfilter import BloomFilter


def test_no_false_negatives():
    bf = BloomFilter(100_000, 0.01)
    items = [f"user-{i}" for i in range(100_000)]
    bf.update(items)
    assert all(it in bf for it in items)


@pytest.mark.parametrize("p", [0.1, 0.01, 0.001])
def test_measured_false_positive_rate_matches_target(p):
    n = 50_000
    bf = BloomFilter(n, p)
    bf.update(f"in-{i}" for i in range(n))
    trials = 200_000
    measured = sum(f"out-{i}" in bf for i in range(trials)) / trials
    assert measured <= p * 1.35, f"measured {measured:.5f} vs target {p}"
    assert measured >= p * 0.4, f"suspiciously low {measured:.5f}, filter may be oversized"


def test_theory_matches_measurement_at_overfill():
    bf = BloomFilter(10_000, 0.01)
    bf.update(f"in-{i}" for i in range(30_000))  # 3x over capacity
    trials = 100_000
    measured = sum(f"out-{i}" in bf for i in range(trials)) / trials
    predicted = bf.expected_error_rate(30_000)
    assert measured == pytest.approx(predicted, rel=0.1)
    assert measured > 0.2


def test_estimated_items_close_to_truth():
    bf = BloomFilter(100_000, 0.01)
    bf.update(f"x{i}" for i in range(60_000))
    assert bf.estimated_items() == pytest.approx(60_000, rel=0.03)


def test_duplicates_do_not_inflate_estimate():
    bf = BloomFilter(10_000, 0.01)
    for _ in range(5):
        bf.update(f"x{i}" for i in range(5_000))
    assert bf.estimated_items() == pytest.approx(5_000, rel=0.05)


def test_union_contains_both_sides():
    a, b = BloomFilter(1000, 0.01), BloomFilter(1000, 0.01)
    a.update(f"a{i}" for i in range(500))
    b.update(f"b{i}" for i in range(500))
    u = a.union(b)
    assert all(f"a{i}" in u for i in range(500)) and all(f"b{i}" in u for i in range(500))


def test_union_rejects_mismatched_filters():
    with pytest.raises(ValueError):
        BloomFilter(1000, 0.01).union(BloomFilter(2000, 0.01))


def test_round_trip_serialization():
    bf = BloomFilter(5000, 0.01)
    bf.update(f"k{i}" for i in range(5000))
    clone = BloomFilter.from_bytes(bf.to_bytes())
    assert all(f"k{i}" in clone for i in range(5000))
    assert clone.bits_set() == bf.bits_set()
    with pytest.raises(ValueError):
        BloomFilter.from_bytes(bf.to_bytes()[:-1])


def test_bytes_and_str_are_the_same_item():
    bf = BloomFilter(100, 0.01)
    bf.add("héllo")
    assert "héllo".encode("utf-8") in bf


def test_rejects_bad_parameters():
    for cap, p in [(0, 0.01), (10, 0), (10, 1)]:
        with pytest.raises(ValueError):
            BloomFilter(cap, p)

def test_can_add_after_loading():
    bf = BloomFilter(100, 0.01)
    clone = BloomFilter.from_bytes(bf.to_bytes())
    clone.add("new")
    assert "new" in clone
