# Python-Cache-Simulator

## Implementation Details:

### Configuration Calculations:
Given cache size, block size, associativity (n, direct, or fully), address length = 32

- num_blocks = cache size / block size

- if associativity = direct
  - associativity = 1
  - num_sets = num_blocks

- elif associativity = fully
  - associativity = num_blocks
  - num_sets = 1

- else
  - associativity = n <- the provided associativity
  - num_sets = num_blocks // associativity
  
- offset length = log_2(block_size)
- index length = log_2(num_sets)
- tag length = address length - (index length + offset length)

### Tag, Index, Offset Calculations:

- offset = address & 2^(offset length) - 1
- tag = (address >> (index length + offset length)) & 2^(tag length) - 1

- if num_sets = 1
  - index = 0 # only one set
- else
  - index = (address >> (offset length)) & 2^(index length) - 1

### Default Data Structures:

Blocks: Python dictionary with the below default parameters
 ```
block = {
  'valid': 0,
  'tag': None,
  'last_used': 0
  }
```


Set: Python dictionary of n (associativity) block data structures indexed by number (0, 1, ..., n)
```
set = {n: block for n in range(associativity)}
```


Cache: Python dictionary of k (num_sets) set data structures indexed by number (0, 1, ..., k)
```
cache = {k: set for k in range(num_sets)}
```

## Simulation Algorithm:
For Address in Trace
  - Calculate Tag, Index, and Offset from Address

  - If a Block in the Indexed Set has an equivalent Tag
    - Update the Least Recently Used (LRU) parameter
    - Hit = True
  
  - Elif a Block in the Indexed Set has Valid bit = 0
    - Store Tag in the Block
    - Set Valid bit = 1 
    - Update the Least Recently Used (LRU) parameter
    - Hit = False (Miss)
  
  - Else
    - Overwrite the LRU Block's Tag
    - Update the Least Recently Used (LRU) parameter
    - Hit = False (Miss)

After simulation, the hit rate = sum(hits) / # accesses * 100%

## Dependencies (can be installed via pip):

- python==3.6.8
- numpy>=1.15.4
- tqdm>=4.29.1

## Usage:
 
usage: cache_sim.py [-h] -trace TRACE [-grid] [-config CONFIG]

optional arguments:
  -h, --help      show this help message and exit
  -trace TRACE    Path to memory address trace .trc file
  -grid           (Optional) Perform grid search across various configurations
  -config CONFIG  Path to simulation configuration .cfg file

### Example Output:

100%|--------------------------------| 695521/695521 [00:31<00:00, 22304.47it/s]

Cache Size 32768 - Block Size 64 - Associativity 4
Num Blocks 512 - Num Sets 128
Tag Length 19 - Index Length 7 - Offset Length 6
Num Accesses 695521 - Num Hits 594110 - Num Misses 101411
Hit Rate: 85.42

## Examples:

Using config and trace files.
```
python3 cache_sim.py -trace example.trc -config example.cfg
```

Performing grid search across hardcoded config parameters (output is written to grid_search.csv).
```
python3 cache_sim.py -trace example.trc -grid
```

## Grid Search Results:

Grid search was performed with the following parameter space:

cache_sizes = [8*1024, 64*1024, 256*1024, 1024*1024]
associativity =  [direct, 2, 4, 8, fully]
block_size = 32

| Cache Size	| Block Size	| Associativity	| Hit Rate |
|:----------:|:----------:|:-------------:|:--------:| 
| 8192       | 32         | direct        | 75.5     | 
| 65536      | 32         | direct        | 75.76    | 
| 262144     | 32         | direct        | 77.85    | 
| 1048576    | 32         | direct        | 85.51    | 
| 8192       | 32         | 2             | 75.52    | 
| 65536      | 32         | 2             | 75.83    | 
| 262144     | 32         | 2             | 77.85    | 
| 1048576    | 32         | 2             | 86.95    | 
| 8192       | 32         | 4             | 75.53    | 
| 65536      | 32         | 4             | 75.92    | 
| 262144     | 32         | 4             | 77.98    | 
| 1048576    | 32         | 4             | 88.02    | 
| 8192       | 32         | 8             | 75.54    | 
| 65536      | 32         | 8             | 76.01    | 
| 262144     | 32         | 8             | 78.81    | 
| 1048576    | 32         | 8             | 88.9     | 
| 8192       | 32         | fully         | 75.56    | 
| 65536      | 32         | fully         | 76.07    | 
| 262144     | 32         | fully         | 79.08    | 
| 1048576    | 32         | fully         | 91.13    | 
