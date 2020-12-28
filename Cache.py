import math


class Block:
    def __init__(self):
        self.tag = 0
        self.valid = False
        self.dirty = False


class Cache:
    def __init__(self, ICache, DCache, blockSize, isUnified, associativity, writePol, allocationPol, instructions):
        self.IBlockSize = ICache // blockSize
        self.DBlockSize = DCache // blockSize
        self.ISets = [[Block() for i in range(associativity)] for j in range(self.IBlockSize // associativity)]
        self.DSets = [[Block() for i in range(associativity)] for j in range(self.DBlockSize // associativity)]
        self.ICacheSize = ICache
        self.DCacheSize = DCache
        self.blockSize = blockSize
        self.writePolicy = writePol
        self.allocationPolicy = allocationPol
        self.associativity = associativity
        self.isUnified = isUnified
        self.instructions = instructions
        self.IHits = 0
        self.IMisses = 0
        self.DHits = 0
        self.DMisses = 0
        self.demandFetch = 0
        self.copiesBack = 0
        self.DReplace = 0
        self.IReplace = 0

    def accesses(self):
        for element in self.instructions:
            if element[0] == '0':
                tag, index = self.parse_address('D', element[1])
                self.data_load(tag, index)
            elif element[0] == '1':
                tag, index = self.parse_address('D', element[1])
                self.data_store(tag, index)
            elif element[0] == '2':
                if self.isUnified:
                    tag, index = self.parse_address('D', element[1])
                    self.instruction_load(tag, index)
                else:
                    tag, index = self.parse_address('I', element[1])
                    self.instruction_load(tag, index)

    def data_load(self, tag, index):
        missFlag = True
        isDone = False
        for j in range(self.associativity):
            if self.DSets[index][j].valid and self.DSets[index][j].tag == tag:
                self.DSets[index].append(self.DSets[index].pop(j))
                self.DHits += 1
                missFlag = False
                break
        if missFlag:
            for j in range(self.associativity):
                if not self.DSets[index][j].valid:
                    self.DSets[index][j].tag = tag
                    self.DSets[index][j].valid = True
                    self.DSets[index].append(self.DSets[index].pop(j))
                    self.DMisses += 1
                    self.demandFetch += self.blockSize / 4
                    isDone = True
                    break
            if not isDone:  # if cache is full
                if self.writePolicy == 'wb' and self.DSets[index][0].dirty:
                    self.copiesBack += self.blockSize / 4
                self.DSets[index].pop(0)
                self.DReplace += 1
                newBlock = Block()
                newBlock.valid = True
                newBlock.tag = tag
                self.DSets[index].append(newBlock)
                self.DMisses += 1
                self.demandFetch += self.blockSize / 4

    def instruction_load(self, tag, index):
        missFlag = True
        isDone = False
        for j in range(self.associativity):
            if self.isUnified and self.DSets[index][j].valid and self.DSets[index][j].tag == tag:
                self.DSets[index].append(self.DSets[index].pop(j))
                self.IHits += 1
                missFlag = False
                break
            elif not self.isUnified and self.ISets[index][j].valid and self.ISets[index][j].tag == tag:
                self.ISets[index].append(self.ISets[index].pop(j))
                self.IHits += 1
                missFlag = False
                break
        if missFlag:
            for j in range(self.associativity):
                if self.isUnified and not self.DSets[index][j].valid:
                    self.DSets[index][j].tag = tag
                    self.DSets[index][j].valid = True
                    self.DSets[index].append(self.DSets[index].pop(j))
                    self.IMisses += 1
                    self.demandFetch += self.blockSize / 4
                    isDone = True
                    break
                elif not self.isUnified and not self.ISets[index][j].valid:
                    self.ISets[index][j].tag = tag
                    self.ISets[index][j].valid = True
                    self.ISets[index].append(self.ISets[index].pop(j))
                    self.IMisses += 1
                    self.demandFetch += self.blockSize / 4
                    isDone = True
                    break
            if not isDone:
                if self.isUnified:
                    if self.writePolicy == 'wb' and self.DSets[index][0].dirty:
                        self.copiesBack += self.blockSize / 4
                    self.DSets[index].pop(0)
                    self.IReplace += 1
                    newBlock = Block()
                    newBlock.valid = True
                    newBlock.tag = tag
                    self.DSets[index].append(newBlock)
                    self.IMisses += 1
                    self.demandFetch += self.blockSize / 4
                else:
                    if self.writePolicy == 'wb' and self.ISets[index][0].dirty:
                        self.copiesBack += self.blockSize / 4
                    self.ISets[index].pop(0)
                    self.IReplace += 1
                    newBlock = Block()
                    newBlock.valid = True
                    newBlock.tag = tag
                    self.ISets[index].append(newBlock)
                    self.IMisses += 1
                    self.demandFetch += self.blockSize / 4

    def data_store(self, tag, index):
        missFlag = True
        isDone = False
        if self.writePolicy == 'wt':
            if self.allocationPolicy == 'wa':
                for j in range(self.associativity):
                    if self.DSets[index][j].valid and self.DSets[index][j].tag == tag:
                        self.DSets[index].append(self.DSets[index].pop(j))
                        self.DHits += 1
                        self.copiesBack += 1
                        missFlag = False
                        break
                if missFlag:
                    for j in range(self.associativity):
                        if not self.DSets[index][j].valid:
                            self.DSets[index][j].tag = tag
                            self.DSets[index][j].valid = True
                            self.DSets[index].append(self.DSets[index].pop(j))
                            self.DMisses += 1
                            self.copiesBack += 1
                            self.demandFetch += self.blockSize / 4
                            isDone = True
                            break
                    if not isDone:
                        self.DSets[index].pop(0)
                        self.DReplace += 1
                        newBlock = Block()
                        newBlock.valid = True
                        newBlock.tag = tag
                        self.DSets[index].append(newBlock)
                        self.DMisses += 1
                        self.copiesBack += 1
                        self.demandFetch += self.blockSize / 4
            elif self.allocationPolicy == 'nw':
                for j in range(self.associativity):
                    if self.DSets[index][j].valid and self.DSets[index][j].tag == tag:
                        self.DSets[index].append(self.DSets[index].pop(j))
                        self.DHits += 1
                        self.copiesBack += 1
                        missFlag = False
                        break
                if missFlag:
                    self.DMisses += 1
                    self.copiesBack += 1
        elif self.writePolicy == 'wb':
            if self.allocationPolicy == 'wa':
                for j in range(self.associativity):
                    if self.DSets[index][j].valid and self.DSets[index][j].tag == tag:
                        self.DSets[index][j].dirty = True
                        self.DSets[index].append(self.DSets[index].pop(j))
                        self.DHits += 1
                        missFlag = False
                        break
                if missFlag:
                    for j in range(self.associativity):
                        if not self.DSets[index][j].valid:
                            self.DSets[index][j].tag = tag
                            self.DSets[index][j].valid = True
                            self.DSets[index][j].dirty = True
                            self.DSets[index].append(self.DSets[index].pop(j))
                            self.DMisses += 1
                            self.demandFetch += self.blockSize / 4
                            isDone = True
                            break
                    if not isDone:
                        if self.DSets[index][0].dirty:
                            self.copiesBack += self.blockSize / 4
                        self.DSets[index].pop(0)
                        self.DReplace += 1
                        newBlock = Block()
                        newBlock.valid = True
                        newBlock.dirty = True
                        newBlock.tag = tag
                        self.DSets[index].append(newBlock)
                        self.DMisses += 1
                        self.demandFetch += self.blockSize / 4
            elif self.allocationPolicy == 'nw':
                for j in range(self.associativity):
                    if self.DSets[index][j].valid and self.DSets[index][j].tag == tag:
                        self.DSets[index][j].dirty = True
                        self.DSets[index].append(self.DSets[index].pop(j))
                        self.DHits += 1
                        missFlag = False
                        break
                if missFlag:
                    self.copiesBack += 1
                    self.DMisses += 1

    def free_cache(self):
        for x in self.DSets:
            for y in x:
                if self.writePolicy == 'wb' and y.dirty:
                    self.copiesBack += self.blockSize / 4
                    y.dirty = False

    def parse_address(self, mode, instruction):
        if mode == 'D':
            blockCounts = self.DCacheSize // self.blockSize
            indexBits = int(math.log(blockCounts // self.associativity, 2))
            offsetBits = int(math.log(self.blockSize, 2))
        else:
            blockCounts = self.ICacheSize // self.blockSize
            indexBits = int(math.log(blockCounts // self.associativity, 2))
            offsetBits = int(math.log(self.blockSize, 2))
        tagBits = 32 - (indexBits + offsetBits)
        instruction = bin(int(instruction, 16))[2:].zfill(32)
        tag = instruction[0:tagBits]
        index = int(instruction[tagBits:tagBits + indexBits], 2)
        return tag, index


def get_input():
    fLine = input().split(' - ')
    sLine = input().split(' - ')
    if len(sLine) == 1:
        sLine.insert(0, '0')
    blockSize = int(fLine[0])
    isUnified = True if fLine[1] == '0' else False
    associativity = int(fLine[2])
    writePolicy = fLine[3]
    allocationPolicy = fLine[4]
    ICacheSize = int(sLine[0])
    DCacheSize = int(sLine[1])
    nLines = []
    while True:
        newLine = input()
        if len(newLine) <= 0:
            break
        ln = newLine.split()
        nLines.append(ln[0:2])
    tmpCache = Cache(ICacheSize, DCacheSize, blockSize, isUnified, associativity, writePolicy, allocationPolicy, nLines)
    return tmpCache


def print_output(inputCache):
    print('***CACHE SETTINGS***')
    if inputCache.isUnified:
        print('Unified I- D-cache')
        print('Size:', int(inputCache.DCacheSize))
    else:
        print('Split I- D-cache')
        print('I-cache size:', int(inputCache.ICacheSize))
        print('D-cache size:', int(inputCache.DCacheSize))
    print('Associativity:', int(inputCache.associativity))
    print('Block size:', int(inputCache.blockSize))
    if inputCache.writePolicy == 'wb':
        print('Write policy: WRITE BACK')
    elif inputCache.writePolicy == 'wt':
        print('Write policy: WRITE THROUGH')
    if inputCache.allocationPolicy == 'wa':
        print('Allocation policy: WRITE ALLOCATE')
    elif inputCache.allocationPolicy == 'nw':
        print('Allocation policy: WRITE NO ALLOCATE')
    if (inputCache.DMisses + inputCache.DHits) == 0:
        DMissRate = 0
        DHitRate = 0
    else:
        DMissRate = inputCache.DMisses / (inputCache.DMisses + inputCache.DHits)
        DHitRate = inputCache.DHits / (inputCache.DMisses + inputCache.DHits)

    if (inputCache.IMisses + inputCache.IHits) == 0:
        IMissRate = 0
        IHitRate = 0
    else:
        IMissRate = inputCache.IMisses / (inputCache.IMisses + inputCache.IHits)
        IHitRate = inputCache.IHits / (inputCache.IMisses + inputCache.IHits)
    print()
    print('***CACHE STATISTICS***')
    print('INSTRUCTIONS')
    print('accesses:', cache.IHits + cache.IMisses)
    print('misses:', cache.IMisses)
    print('miss rate: %.4f' % IMissRate, '(hit rate %.4f)' % IHitRate)
    print('replace:', inputCache.IReplace)
    print('DATA')
    print('accesses:', cache.DHits + cache.DMisses)
    print('misses:', cache.DMisses)
    print('miss rate: %.4f' % DMissRate, '(hit rate %.4f)' % DHitRate)
    print("replace:", inputCache.DReplace)
    print('TRAFFIC (in words)')
    print('demand fetch:', int(inputCache.demandFetch))
    print('copies back:', int(inputCache.copiesBack))


cache = get_input()
cache.accesses()
cache.free_cache()
print_output(cache)
