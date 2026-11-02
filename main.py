from bloomfilter import BloomFilter
import time

now = time.localtime()
capacity = 10
error_rate = 0.01

bf = BloomFilter(capacity,error_rate)
bf.add("rudra")
bf.add("jignesh")
bf.add("oliver")
# print(bf.__contains__("rudraa"))
# print(bf._added)
# print(bf.bits_set())
# print(bf.estimated_items())
# print(bf.expected_error_rate())

# with open('user_'+str(time.strftime("%Y_%m_%d_%H_%M", now))+'.bloom', 'wb') as file:
#     print(bf.to_bytes())
#     file.write(bf.to_bytes())

# bloom_file = "user_2026_11_03_00_08.bloom"
# bf = None
# with open(bloom_file, 'rb') as file:
#     data = file.read()
#     bf = BloomFilter.from_bytes(data)

capacity2 = 10
error_rate2 = 0.01
bf2 = BloomFilter(capacity2,error_rate2)
bf2.add("apple")
bf2.add("orange")
bf2.add("mango")

bf_union = bf.union(bf2)

print(bf_union.__contains__("apple"))