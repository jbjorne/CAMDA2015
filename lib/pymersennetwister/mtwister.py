#!/usr/bin/env python
from __future__ import division
from __future__ import print_function

"""
A Pure python Mersenne Twister PRNG from
https://github.com/coolbutuseless/pymersennetwister
licensed under:

The MIT License (MIT)

Copyright (c) 2014 coolbutuseless

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# The coefficients for MT19937 are:
#    (w, n, m, r) = (32, 624, 397, 31)
#    w      = 32                - Word size in bits
#    n      = 624               - degree of recurrence
#    m      = 397               - middle word. Number of parallel sequences
#    r      = 31                - number of bits of the lower bitmask
#    a      = 9908B0DF16        - co-effs of the raional normal form twist matrix
#    u      = 11                - tempering bit shift
#    (s, b) = (7, 9D2C568016)   - 
#    (t, c) = (15, EFC6000016)  - 
#    l      = 18                - tempering bit shifts

class MTwister(object):
    def __init__(self):
        self.MT = [0] * 624
        self.index = 0

    # // Initialize the generator from a seed
    # function initialize_generator(int seed) {
    #     index := 0
    #     MT[0] := seed
    #     for i from 1 to 623 { // loop over each other element
    #         MT[i] := last 32 bits of(1812433253 * (MT[i-1] xor (right shift by 30 bits(MT[i-1]))) + i) // 0x6c078965
    #     }
    # }
    def set_seed(self, seed):
        self.index = 0
        self.MT[0] = int(seed & 0xffffffff)
        for i in range(1, 624):
            self.MT[i] = (1812433253 * (self.MT[i-1] ^ (self.MT[i-1] >> 30)) + i) & 0xffffffff
    
    def set_seed_R(self, seed):
        """ How R scrambles an integer seed to create the twister state
        from R3.0.3 src/main/RNG.c
        """
        self.index = 0
        for i in range(51):
            # Initial scrambling
            # has to be 51 instead of R's 50 due to the nature of the dummy[]
            # buffer being 1-indexed in R, but 0-indexed in C
            seed = (69069 * seed + 1) & 0xffffffff 
        for i in range(624):
            seed = (69069 * seed + 1) & 0xffffffff 
            self.MT[i] = int(seed)

    def set_seed_python(self, seed):
        self.set_seed(19650218)
        mt = self.MT
        i = 1
        mt[i] = ((mt[i] ^ ((mt[i-1] ^ (mt[i-1] >> 30)) * 1664525)) + seed) & 0xffffffff
        i += 1
        for k in range(623, 1, -1):
            mt[i] = ((mt[i] ^ ((mt[i-1] ^ (mt[i-1] >> 30)) * 1566083941)) - i) & 0xffffffff
            i += 1
        mt[0] = 0x80000000 # MSB is 1; assuring non-zero initial array


    # // Extract a tempered pseud random number based on the index-th value,
    # // calling generate_numbers() every 624 numbers
    # function extract_number() {
    #     if index == 0 {
    #         generate_numbers()
    #     }
    # 
    #     int y := MT[index]
    #     y := y xor (right shift by 11 bits(y))
    #     y := y xor (left shift by 7 bits(y) and (2636928640)) // 0x9d2c5680
    #     y := y xor (left shift by 15 bits(y) and (4022730752)) // 0xefc60000
    #     y := y xor (right shift by 18 bits(y))
    #
    #     index := (index + 1) mod 624
    #     return y
    # }
    def random_uint32(self):
        if self.index == 0:
            self.generate_numbers()

        y = self.MT[self.index]
        y = y ^  (y >> 11)
        y = y ^ ((y <<  7) & 2636928640)
        y = y ^ ((y << 15) & 4022730752)
        y = y ^  (y >> 18)

        self.index = (self.index + 1) % 624
        return y 

    def random(self):
        return self.random_uint32() / (1<<32)

    def random_cpython(self):
        """ 
        CPython random.random() implementation from: Modules/_randommodule.c
        Returns a random number with 53bits of precision

        random_random is the function named genrand_res53 in the original code;
        generates a random number on [0,1) with 53-bit resolution; note that
        9007199254740992 == 2**53; I assume they're spelling "/2**53" as
        multiply-by-reciprocal in the (likely vain) hope that the compiler will
        optimize the division away at compile-time.  67108864 is 2**26.  In
        effect, a contains 27 random bits shifted left 26, and b fills in the
        lower 26 bits of the 53-bit numerator.
        The orginal code credited Isaku Wada for this algorithm, 2002/01/09.
        """
        a = self.random_uint32() >> 5
        b = self.random_uint32() >> 6
        return (a*67108864.0+b) * (1.0/9007199254740992.0)


    # for i from 0 to 623 {
    #     int y := (MT[i] and 0x80000000)                       // bit 31 (32nd bit) of MT[i]
    #                    + (MT[(i+1) mod 624] and 0x7fffffff)   // bits 0-30 (first 31 bits) of MT[...]
    #     MT[i] := MT[(i + 397) mod 624] xor (right shift by 1 bit(y))
    #     if (y mod 2) != 0 { // y is odd
    #         MT[i] := MT[i] xor (2567483615) // 0x9908b0df
    #     }
    # }
    def generate_numbers(self):
        for i in range(624):
            y = (self.MT[i] & 0x80000000) + (self.MT[(i+1) % 624] & 0x7fffffff)
            self.MT[i] = self.MT[(i + 397) % 624] ^ (y >> 1)
            if y % 2 != 0: 
                self.MT[i] = self.MT[i] ^ 2567483615  # 0x9908b0df

    def check_seed(self):
        assert all(isinstance(x, int) for x in self.MT)
        assert any(x > 0 for x in self.MT)

if __name__ == '__main__':
    mt = MTwister()
    mt.set_seed(1)
    mt.check_seed()
