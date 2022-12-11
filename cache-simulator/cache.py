import sys
import re
import math

'''# cache'''
class Cache(object):
    def __init__(self, blockSize, cacheSize, associativity, replacementPolicy, writePolicy):
        self.config = {}
        self.config['blockSize'] = blockSize
        self.config['cacheSize'] = cacheSize
        self.config['associativity'] = associativity
        self.config['replacementPolicy'] = replacementPolicy
        self.config['writePolicy'] = writePolicy
        self.config['numBlocks'] = cacheSize / blockSize
        self.config['numWays'] = associativity
        self.config['numSets'] = cacheSize / (blockSize * associativity)

        # cache variables
        self.stats = {}
        self.stats['Reads'] = 0
        self.stats['ReadHits'] = 0
        self.stats['ReadMisses'] = 0
        self.stats['Writes'] = 0
        self.stats['WriteHits'] = 0
        self.stats['WriteMisses'] = 0
        self.stats['WriteBacks'] = 0
        self.stats['MemTraffic'] = 0

        # state matrices
        self.rows = self.config['numSets']
        self.cols = self.config['numWays']
        self.TAG_MAT = [([int(1)] * self.cols) for row in range(int(self.rows))]
        self.VALID_MAT = [([0] * self.cols) for row in range(int(self.rows))]
        self.DIRTY_MAT = [([0] * self.cols) for row in range(int(self.rows))]
        self.LRU_MAT = [([0] * self.cols) for row in range(int(self.rows))]
        self.FIFO_MAT = [([0] * self.cols) for row in range(int(self.rows))]

    # TODO: issue read function
    def issueRead(self, address):
        self.stats['MemTraffic'] += 1
        return None

    # TODO: issue write function
    def issueWrite(self, address):
        self.stats['MemTraffic'] += 1
        return None

    def decodeAddress(self, address):
        # calclating length of tag, index & offset from cache configuration
        lenAddr = 32
        lenOffset = int(math.log(self.config['blockSize'], 2))
        lenIndex = int(math.log(self.config['numSets'], 2))
        lenTag = lenAddr - lenOffset - lenIndex
        # exctracting tag, index & offset from address
        trace = (int(address, 16))
        maskTag = int(('1' * lenTag + '0' *
                       lenIndex + '0' * lenOffset), 2)
        tag = (trace & maskTag) >> (
            lenIndex + lenOffset)
        maskIndex = int(('0' * lenIndex + '1' *
                         lenIndex + '0' * lenOffset), 2)
        index = (trace & maskIndex) >> (lenOffset)
        # maskOffset = int(('0' * lenOffset + '0' *
        #                   lenOffset + '1' * lenOffset), 2)
        # offset = (trace & maskOffset)
        return (tag, index)

    def encodeAddress(self, tag, index):
        lenOffset = int(math.log(self.config['blockSize'], 2))
        lenIndex = int(math.log(self.config['numSets'], 2))
        address = (tag << (lenIndex + lenOffset)) + (index << lenOffset)
        return address

    def updateBlockUsed(self, index, way):
        # 0 for LRU, 1 for FIFO
        if self.config['replacementPolicy'] == 0:
            self.LRU_MAT[index][way] = max(self.LRU_MAT[index]) + 1
        elif self.config['replacementPolicy'] == 1:
            self.FIFO_MAT[index][way] = min(self.FIFO_MAT[index]) + 1
        return None

    def chooseBlockToEvict(self, index):
        # 0 for LRU, 1 for FIFO
        if self.config['replacementPolicy'] == 0:
            lru = min(self.LRU_MAT[index])
            lru_way = self.LRU_MAT[index].index(lru)
            return lru_way
        elif self.config['replacementPolicy'] == 1:
            fifo = min(self.FIFO_MAT[index])
            fifo_way = self.FIFO_MAT[index].index(fifo)
            return fifo_way

    # read method
    def readFromAddress(self, currentAddress):
        (currentTag, currentIndex) = self.decodeAddress(currentAddress)
        self.stats['Reads'] += 1
        # WTNA
        if self.config['writePolicy'] == 1:
            if (currentTag in self.TAG_MAT[currentIndex]) and self.VALID_MAT[currentIndex][self.TAG_MAT[currentIndex].index(currentTag)]:
                # Read Hit
                self.stats['ReadHits'] += 1
                foundWay = self.TAG_MAT[currentIndex].index(currentTag)
                # update matirces and counters
                self.updateBlockUsed(currentIndex, foundWay)
                return 1
            else:
                # Read Miss
                self.stats['ReadMisses'] += 1
                # if unused block, bring in block from next level, set V=1 & D=0
                if 0 in self.VALID_MAT[currentIndex]:
                    foundWay = self.VALID_MAT[currentIndex].index(0)
                    # bring in the block from next level
                    self.issueRead(self.encodeAddress(currentTag, currentIndex))
                    # update matirces and counters
                    self.VALID_MAT[currentIndex][foundWay] = 1
                    self.TAG_MAT[currentIndex][foundWay] = currentTag
                    self.updateBlockUsed(currentIndex, foundWay)
                else:
                    # if no unused block, evict LRU/FIFO, allocate block, set V=1 & D=0, assign tag
                    foundWay = self.chooseBlockToEvict(currentIndex)
                    # if block not dirty, no worries, just bring in the block from next level
                    self.issueRead(self.encodeAddress(currentTag, currentIndex))
                    # update matirces and counters
                    self.VALID_MAT[currentIndex][foundWay] = 1
                    self.TAG_MAT[currentIndex][foundWay] = currentTag
                    self.updateBlockUsed(currentIndex, foundWay)
            return 0
        # WBWA
        if self.config['writePolicy'] == 0:
            if (currentTag in self.TAG_MAT[currentIndex]) and self.VALID_MAT[currentIndex][self.TAG_MAT[currentIndex].index(currentTag)]:
                # Read Hit
                self.stats['ReadHits'] += 1
                foundWay = self.TAG_MAT[currentIndex].index(currentTag)
                # update matirces and counters
                self.updateBlockUsed(currentIndex, foundWay)
                return 1
            else:
                # Read Miss
                self.stats['ReadMisses'] += 1
                # if unused block, bring in block from next level, set V=1 & D=0
                if 0 in self.VALID_MAT[currentIndex]:
                    foundWay = self.VALID_MAT[currentIndex].index(0)
                    # bring in the block from next level
                    self.issueRead(self.encodeAddress(currentTag, currentIndex))
                    # update matirces and counters
                    self.VALID_MAT[currentIndex][foundWay] = 1
                    self.TAG_MAT[currentIndex][foundWay] = currentTag
                    self.updateBlockUsed(currentIndex, foundWay)
                else:
                    # if no unused block, evict LRU/FIFO, allocate block, set V=1 & D=0, assign tag
                    foundWay = self.chooseBlockToEvict(currentIndex)
                    foundTag = self.TAG_MAT[currentIndex][foundWay]
                    # Policy =0 =WBWA, V=1, D=0, issue read from  next level
                    if self.DIRTY_MAT[currentIndex][foundWay] == 1:
                        # if block dirty, first writeback
                        self.issueWrite(self.encodeAddress(foundTag, currentIndex))
                        self.stats['WriteBacks'] += 1
                        self.DIRTY_MAT[currentIndex][foundWay] = 0
                    # if block not dirty, no worries, just bring in the block from next level
                    self.issueRead(self.encodeAddress(currentTag, currentIndex))
                    # update matirces and counters
                    self.VALID_MAT[currentIndex][foundWay] = 1
                    self.DIRTY_MAT[currentIndex][foundWay] = 0
                    self.TAG_MAT[currentIndex][foundWay] = currentTag
                    self.updateBlockUsed(currentIndex, foundWay)
                return 0

    def writeToAddress(self, currentAddress):
        (currentTag, currentIndex) = self.decodeAddress(currentAddress)
        self.stats['Writes'] += 1
        # WTNA
        if self.config['writePolicy'] == 1:
            if (currentTag in self.TAG_MAT[currentIndex]) and self.VALID_MAT[currentIndex][self.TAG_MAT[currentIndex].index(currentTag)]:
                self.stats['WriteHits'] += 1
                foundWay = self.TAG_MAT[currentIndex].index(currentTag)
                # Policy =1 =WTNA, write to cache, write to next level
                self.TAG_MAT[currentIndex][foundWay] = currentTag
                self.issueWrite(self.encodeAddress(currentTag, currentIndex))
                # update matirces and counters
                self.updateBlockUsed(currentIndex, foundWay)
                return 1
            else:
                # Write Miss
                self.stats['WriteMisses'] += 1
                self.issueWrite(self.encodeAddress(currentTag, currentIndex))
            return 0
        # WBWA
        if self.config['writePolicy'] == 0:
            if (currentTag in self.TAG_MAT[currentIndex]) and self.VALID_MAT[currentIndex][self.TAG_MAT[currentIndex].index(currentTag)]:
                self.stats['WriteHits'] += 1
                foundWay = self.TAG_MAT[currentIndex].index(currentTag)
                # Policy =0 =WBWA, D=1, write to cache, no write to next level
                self.DIRTY_MAT[currentIndex][foundWay] = 1
                # update matirces and counters
                self.updateBlockUsed(currentIndex, foundWay)
                return 1
            else:
                # Write Miss
                self.stats['WriteMisses'] += 1
                # if unused block, allocate block, set V=1 & D=0, assign tag
                if 0 in self.VALID_MAT[currentIndex]:
                    foundWay = self.VALID_MAT[currentIndex].index(0)
                    # Policy =0 =WBWA, bring in the block, D=1, V=1, write to cache, no write to next level
                    # bring in the block from next level
                    self.issueRead(self.encodeAddress(currentTag, currentIndex))
                    # update matirces and counters
                    self.VALID_MAT[currentIndex][foundWay] = 1
                    self.DIRTY_MAT[currentIndex][foundWay] = 1
                    self.TAG_MAT[currentIndex][foundWay] = currentTag
                    self.updateBlockUsed(currentIndex, foundWay)
                else:
                    foundWay = self.chooseBlockToEvict(currentIndex)
                    foundTag = self.TAG_MAT[currentIndex][foundWay]
                    # update matirces and counters
                    # Policy =0 =WBWA
                    if self.DIRTY_MAT[currentIndex][foundWay] == 1:
                        # if block dirty, first writeback, write to cache
                        self.stats['WriteBacks'] += 1
                        self.issueWrite(self.encodeAddress(foundTag, currentIndex))
                    elif self.DIRTY_MAT[currentIndex][foundWay] == 0:
                        # if block not dirty, write to cache
                        self.DIRTY_MAT[currentIndex][foundWay] = 1
                    # bring in the block from next level
                    self.issueRead(self.encodeAddress(currentTag, currentIndex))
                    self.TAG_MAT[currentIndex][foundWay] = currentTag
                    self.updateBlockUsed(currentIndex, foundWay)
                return 0

    def printStats(self):
        print ("\n", "TAG matrix is\n", self.TAG_MAT)
        print ("\n", "LRU matrix is\n", self.LRU_MAT)
        print ("\n", "FIFO matrix is\n", self.FIFO_MAT)
        print ("\n", "VALID matrix is\n", self.VALID_MAT)
        print ("\n", "DIRTY matrix is\n", self.DIRTY_MAT)
        print ("\n", "Cache Stats are\n", self.stats)
        return None

'''#cache_sim'''
def traceParse(file_name):
    f = open(file_name)
    instrList = re.findall(r'(\w+)\s(\w+)', f.read())
    f.close()
    return instrList

def main():
    if len(sys.argv) != 7:
        print ('usage: sim_cache.py <BLOCKSIZE> <SIZE> <ASSOC> <REPLACEMENT_POLICY> <WRITE_POLICY> <trace_file>')
        print ('<BLOCKSIZE>          Block size in bytes. Positive Integer, Power of two')
        print ('<SIZE>               Total CACHE size in bytes. Positive Integer')
        print ('<ASSOC>              Associativity, 1 if direct mapped, N if fully associative')
        print ('<REPLACEMENT_POLICY> 0 for LRU, 1 for FIFO')
        print ('<WRITE_POLICY>       0 for WBWA, 1 for WTNA')
        print ('Example: 8KB 4-way set-associative cache with 32B block size, LRU replacement policy and WTNA write policy, gcc_trace input file')
        print ('Command: $ python cache_sim.py 4 32 4 0 1 gcc_trace.txt')
        sys.exit(1)
    else:
        blockSize = int(sys.argv[1])
        cacheSize = int(sys.argv[2])
        associativity = int(sys.argv[3])
        replacementPolicy = int(sys.argv[4])
        writePolicy = int(sys.argv[5])
        fileName = sys.argv[6]

        def printContents(cache):
            print(' ', '{:=^35}'.format(' Simulator configuration '))
            print('{: <24}'.format('  L1_BLOCKSIZE:'), '{: >12}'.format(cache.config['blockSize']))
            print('{: <24}'.format('  L1_SIZE:'), '{: >12}'.format(cache.config['cacheSize']))
            print('{: <24}'.format('  L1_ASSOC:'), '{: >12}'.format(cache.config['associativity']))
            print('{: <24}'.format('  L1_REPLACEMENT_POLICY:'), '{: >12}'.format(cache.config['replacementPolicy']))
            print('{: <24}'.format('  L1_WRITE_POLICY:'), '{: >12}'.format(cache.config['writePolicy']))
            print('{: <24}'.format('  trace_file:'), '{: >12}'.format(fileName))
            print('{:=<37}'.format('  '))
            print("")
            
            print (' ', '{:=^38}'.format(' Simulation results (raw) '))
            print ('{: <31}'.format('  a. number of L1 reads:'), '{: >8}'.format(cache.stats['Reads']))
            print ('{: <31}'.format('  b. number of L1 read misses:'), '{: >8}'.format(cache.stats['ReadMisses']))
            print ('{: <31}'.format('  c. number of L1 writes:'), '{: >8}'.format(cache.stats['Writes']))
            print ('{: <31}'.format('  d. number of L1 write misses:'), '{: >8}'.format(cache.stats['WriteMisses']))
            totalMisses = cache.stats['ReadMisses'] + cache.stats['WriteMisses']
            totalAccesses = cache.stats['Reads'] + cache.stats['Writes']
            missRate = totalMisses / float(totalAccesses)
            print ('{: <31}'.format('  e. L1 miss rate:'), '{: >8}'.format('%.4f' % missRate))
            print ('{: <31}'.format('  f. total memory traffic:'), '{: >8}'.format(cache.stats['MemTraffic']))
            print ("")
            print (' ', '{:=^42}'.format(' Simulation results (performance) '))

            # FIXME: logic for access time
            # L1 Cache Hit Time(in ns) = 0.25ns + 2.5ns * (L1_Cache Size / 512kB) + 0.025ns * (L1_BLOCKSIZE / 16B) + 0.025ns * L1_SET_ASSOCIATIVITY
            # L1 miss penalty(in ns) = 20 ns + 0.5 * (L1_BLOCKSIZE / 16 B / ns))
            # avg_access_time = (l1_hit_time + (l1_miss_rate * (miss_penalty))

            hitTime = 0.25 + (2.5 * (cache.config['cacheSize'] / (512 * 1024))) + \
                (0.025 * (cache.config['blockSize'] / 16)) + (0.025 * cache.config['associativity'])
            missPenalty = 20 + 0.5 * (cache.config['blockSize'] / 16)
            AAT = hitTime + (missRate * missPenalty)
            print ('{: <23}'.format('  1. average access time:'), '{: >18}'.format('%.4f ns' % AAT),
            sys.stdout.flush())

        # L1 cache instantiation & initialization
        L1 = Cache(blockSize, cacheSize, associativity, replacementPolicy, writePolicy)
        # parsing trace file
        instr_list = traceParse(fileName)
        for i in instr_list:
            if i[0] == 'r':
                L1.readFromAddress(i[1])
            elif i[0] == 'w':
                L1.writeToAddress(i[1])
        printContents(L1)

if __name__ == '__main__':
    main()