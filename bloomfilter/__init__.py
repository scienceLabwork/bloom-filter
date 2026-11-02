#NOTE: Bloom filter from scratch. Developed by Rudra Shah"""
from __future__ import annotations
import math
from hashlib import blake2b
import struct

class BloomFilter:
    def __init__(self, capacity, error_rate=0.01):
        if(capacity<=0):
            raise ValueError

        if(error_rate<=0 or error_rate>=1):
            raise ValueError
        
        #NOTE:We have n=Capacity and p=error_rate
        self.capacity = capacity
        self.error_rate = error_rate
        self.m = math.ceil((-1*capacity*math.log(error_rate))/(math.pow(math.log(2),2)))
        self.k = max(1,round((self.m/capacity)*math.log(2)))
        self.bits = bytearray(self.size_bytes)
        self._added = 0

    @property
    def size_bytes(self) -> int:  # Milestone 1
        return (self.m+7)//8

    def _indexes(self, item):
        if(type(item)!=bytes):
            item = bytes(item, encoding='UTF-8')
        T_hash = blake2b(item, digest_size=16).digest() #16 here means 16 bytes
        T_hash = (struct.unpack("<QQ", T_hash))
        h1 = T_hash[0]
        h2 = T_hash[1]
        h2 |= 1
        pos = []
        for i in range(self.k):
            index_i = (h1 + (i*h2))%self.m
            pos.append(index_i)
        return pos

    def add(self, item) -> None:  # Milestone 2
        if(type(item)!=str and type(item)!=bytes):
            raise Exception("Needs byte or String.")
        pos = self._indexes(item)
        self._added += 1
        for i in pos:
            self.bits[i>>3] |= 1 << (i&7)

    def update(self, items) -> None:  # Milestone 2
        for item in items:
            self.add(item)

    def __contains__(self, item) -> bool:  # Milestone 2
        pos = self._indexes(item)
        ans = True
        for i in pos:
            index_i = self.bits[i>>3] & (1<<(i&7))
            if(index_i==0):
                ans = False
                break
        return ans

    def bits_set(self) -> int:  # Milestone 3
        return int.from_bytes(self.bits, byteorder='big').bit_count()

    def estimated_items(self) -> float:  # Milestone 3
        x = self.bits_set()
        if(x==self.m):
            return float('inf')
        return round((-1*(self.m/self.k))*math.log(1-(x/self.m)),2)

    def expected_error_rate(self, n=None) -> float:  # Milestone 3
        if(n==None):
            n = self.estimated_items()
        return math.pow(1-math.pow(math.e,(-self.k*n/self.m)), self.k)

    def union(self, other) -> "BloomFilter":  # Milestone 3
        bf = other
        if(bf.m!=self.m):
            raise ValueError
        if(bf.k!=self.k):
            raise ValueError
        bf_union = BloomFilter(self.capacity, self.error_rate)
        union_int = int.from_bytes(bytes(self.bits),byteorder='big')|int.from_bytes(bytes(bf.bits),byteorder='big')
        bf_union.bits = bytearray(union_int.to_bytes(len(self.bits), byteorder='big')) 
        bf_union._added = bf._added + self._added
        return bf_union

    def to_bytes(self) -> bytes:  # Milestone 3
        header = struct.pack("<QdQ", self.capacity, self.error_rate, self._added)
        return header + bytes(self.bits)
    
    @classmethod
    def from_bytes(cls, data) -> "BloomFilter":  # Milestone 3
        capacity, error_rate, items_count = struct.unpack('<QdQ',data[:24])
        bits_data = data[24:]
        bf = cls(capacity, error_rate)
        if(len(bits_data)!=bf.size_bytes):
            raise ValueError
        bf._added = items_count
        bf.bits = bytearray(bits_data)
        return bf