import argparse
import time
import numpy as np
from itertools import product
from tqdm import tqdm


class Simulator(object):

    def __init__(self,
                 config_file='example.cfg',
                 trace_file='example.trc',
                 config=None
                 ):

        self.cache_size = None
        self.block_size = None
        self.associativity = None
        self.n_blocks = None
        self.n_sets = None
        self.nb_address = 32
        self.nb_index = None
        self.nb_offset = None
        self.nb_tag = None

        self.trace = {
                'address': None,
                'tag':  None,
                'index': None,
                'offset': None,
                'hit': None
                }

        # Use parameters passed otherwise use config file
        if config is None:
            self.__read_config(config_file)
        else:
            self.cache_size, self.block_size = config['Cache Size'], config['Block Size']
            self.associativity = config['Associativity']

        self.__get_config()
        self.__get_trace(trace_file)

        # Default block data struct
        self.block = {
                'valid': 0,
                'tag': None,
                'last_used': 0
                }

        # k sets with n blocks
        self.sets = {k: {n: self.block.copy() for n in range(self.associativity)} for k in range(self.n_sets)}


    def __read_config(self, config_file):
        # Read config file params to dictionary
        config = open(config_file, 'r').read().splitlines()
        config = [param.split('=') for param in config]
        config = {param[0]: param[1] for param in config}
        self.cache_size, self.block_size = int(config['Cache Size']), int(config['Block Size'])
        self.associativity = config['Associativity']


    def __get_config(self):
        """ Parse configuration file params and calculate cache params """

        # Calculate n blocks = cache size / block size
        self.n_blocks = self.cache_size // self.block_size

        # Get associativity (can be direct, n, or fully)
        # Direct mapped
        if self.associativity.lower() == 'direct':
            self.associativity = 1
            self.n_sets = self.n_blocks

        # Fully mapped
        elif self.associativity.lower() == 'fully':
            self.associativity = self.n_blocks
            self.n_sets = 1

        # N associativity
        else:
            self.associativity = int(self.associativity)
            self.n_sets = self.n_blocks // self.associativity


        # Calculate memory address bit configurations
        self.nb_offset = np.log2(self.block_size).astype(int)
        self.nb_index = np.log2(self.n_sets).astype(int)
        self.nb_tag = self.nb_address - (self.nb_index + self.nb_offset)


    def __get_trace(self, trace_file):
        """ Parse memory addresses from trace file """

        # Read memory addresses and convert from str -> int
        trace = open(trace_file, 'r').read().splitlines()
        self.trace['address'] = np.array([int(address, 16) for address in trace], dtype=np.uint32)
        self.trace['n_accesses'] = len(self.trace['address'])
        self.trace['hit'] = [False] * self.trace['n_accesses']

        # Calculate tag, index, and offset values
        # offset = address & 2**offset bits - 1
        self.trace['offset'] = np.bitwise_and(self.trace['address'], 2**self.nb_offset - 1)

        # tag = (address >> index+offset bits) & 2**tag bits - 1
        self.trace['tag'] = np.right_shift(self.trace['address'], self.nb_index + self.nb_offset)
        self.trace['tag'] = np.bitwise_and(self.trace['tag'], 2**self.nb_tag - 1)

        # If n_sets=1 then no bits are allocated for the index
        if self.n_sets == 1:
            self.trace['index'] = [0] * len(self.trace['address'])
        # Else index = (address >> offset bits) & 2**index bits - 1
        else:
            self.trace['index'] = np.right_shift(self.trace['address'], self.nb_offset)
            self.trace['index'] = np.bitwise_and(self.trace['index'], 2**self.nb_index - 1)


    def simulate(self):
        """ Run simulation """

        # Loop for all addresses in trace
        for i in tqdm(range(self.trace['n_accesses'])):

            tag, set = self.trace['tag'][i], self.trace['index'][i]

            # Check for tag match. If match then hit
            match = next((block for block in self.sets[set] \
                          if self.sets[set][block]['tag'] == tag), None)

            if match is not None:
                self.sets[set][match]['last_used'] = time.time()
                self.trace['hit'][i] = True
                continue

            # Check if any block in set has no data yet (valid=0)
            # MISS
            unset = next((block for block in self.sets[set] \
                          if self.sets[set][block]['valid'] == 0), None)

            if unset is not None:
                self.sets[set][unset]['valid'] = 1
                self.sets[set][unset]['tag'] = tag
                self.sets[set][unset]['last_used'] = time.time()
                continue

            # If all blocks contains data with different tags
            # Then replace via least recently used via the last_used param
            # MISS
            lru = np.argmin([self.sets[set][block]['last_used'] for block in self.sets[set]])

            self.sets[set][lru]['tag'] = tag
            self.sets[set][lru]['last_used'] = time.time()


        # Print results
        n_accesses = self.trace['n_accesses']
        hits = sum(self.trace['hit'])
        misses = n_accesses - hits
        hit_rate = (hits / n_accesses) * 100.0


        print('Cache Size {:d} - Block Size {:d} - Associativity {:d}'.format(self.cache_size, self.block_size, self.associativity))
        print('Num Blocks {:d} - Num Sets {:d}'.format(self.n_blocks, self.n_sets))
        print('Tag Length {:d} - Index Length {:d} - Offset Length {:d}'.format(self.nb_tag, self.nb_index, self.nb_offset))
        print('Num Accesses {:d} - Num Hits {:d} - Num Misses {:d}'.format(n_accesses, hits, misses))
        print('Hit Rate: {:.2f}'.format(hit_rate))
        return hit_rate


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='EE5123 Computer Architecture\nIsaac Corley\nCache Simulator')
    parser.add_argument('-trace', type=str, required=True, help='Path to memory address trace .trc file')
    parser.add_argument('-grid', action='store_true', help='(Optional) Perform grid search across various configurations')
    parser.add_argument('-config', type=str, default=None, help='Path to simulation configuration .cfg file')
    args = parser.parse_args()

    if args.grid:
        cache_size = [8*1024, 64*1024, 256*1024, 1024*1024]
        block_size = 32
        associativity = ['direct', '2', '4', '8', 'fully']
        with open('grid_search.csv', 'w') as f:
            f.write(','.join(['cache_size', 'block_size', 'associativity', 'hit_rate', '\n']))
            
        for a, c in product(associativity, cache_size):
            config = {
                    'Cache Size': c,
                    'Block Size': block_size,
                    'Associativity': a
                    }
            sim = Simulator(config=config)
            hit_rate = sim.simulate()
            
            with open('grid_search.csv', 'a', newline='')as f:
                f.write(','.join([str(c), str(block_size), a, '{:.2f}'.format(hit_rate), '\n']))

    else:
        sim = Simulator(config_file=args.config, trace_file=args.trace)
        hit_rate = sim.simulate()
