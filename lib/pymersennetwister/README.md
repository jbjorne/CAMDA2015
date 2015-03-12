pymersennetwister
=================

Pure python Mersenne Twister PRNG

* Based upon pseudocode from https://en.wikipedia.org/wiki/Mersenne_twister

### Validation ###
* Validated against R's mersenne twister implementation for 32-bit output  
    * test_generate.R creates 
        * test_seed.py (R's RNG seed state) 
        * test_randoms.py (R's first 1000 uniform random numbers)
    * test_mersenne.py compares R's output with MTwister output
* Validated against CPython's mersenne twister implementation (53 bit precision)
    * test_cpython.py

### Timing ###
Time taken to generate 1 Million random numbers

| PRNG            | CPython       | pypy         |
|-----------------|---------------|--------------|
| random.random() | 0.13 seconds  | 0.04 seconds |
| MTwister        | 6 seconds     | 0.14 seconds |

### ToDo ###
* match seeding algorithms. How seeding with an integer behaves is implementation dependent
    * CPython - totally don't know what CPython does with random.seed(1)
* Implement exact jumpahead - http://www.math.sci.hiroshima-u.ac.jp/~m-mat/MT/JUMP/index.html

### Testing ###
* py.test
* Tested with cpython2.7, 3.3.4 and pypy

### References ###
* M. Matsumoto and T. Nishimura, "Mersenne Twister: A 623-dimensionally equidistributed uniform pseudorandom number generator", ACM Trans. on Modeling and Computer Simulation Vol. 8, No. 1, January pp.3-30 (1998) DOI:10.1145/272991.272995 http://www.math.sci.hiroshima-u.ac.jp/~m-mat/MT/ARTICLES/mt.pdf
* Hiroshi Haramoto, Makoto Matsumoto, and Pierre LfEcuyer, "A Fast Jump Ahead Algorithm for Linear Recurrences in a Polynomial Space", Sequences and Their Applications - SETA 2008, 290--298, DOI:10.1007/978-3-540-85912-3_26 http://www.math.sci.hiroshima-u.ac.jp/~m-mat/MT/ARTICLES/jump-seta-lfsr.pdf
* Hiroshi Haramoto, Makoto Matsumoto, Takuji Nishimura, François Panneton, Pierre LfEcuyer, "Efficient Jump Ahead for F2-Linear Random Number Generators", INFORMS JOURNAL ON COMPUTING, Vol. 20, No. 3, Summer 2008, pp. 385-390 DOI: 10.1287/ijoc.1070.0251 http://www.math.sci.hiroshima-u.ac.jp/~m-mat/MT/ARTICLES/jumpf2-printed.pdf 
