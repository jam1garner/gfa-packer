import sys,os,zlib,binascii,struct
        
def int32(integer):
    return struct.pack("<L",integer)

def getString(file):
    result = ""
    tmpChar = file.read(1)
    while ord(tmpChar) != 0:
        result += tmpChar
        tmpChar =file.read(1)
    return result

if len(sys.argv) <= 2 or len(sys.argv) > 3:
    print 'Usage:'
    print 'gfa-packer.py [folderToCompress] [gfa to copy hashes from]'
    quit()

filenames = []
for subdir,dirs,files in os.walk(sys.argv[1]):
    for file in files:
        filePath = subdir + os.sep + file
        filenames.append([file,filePath])

uncompressedString = ""

hashes = []
lengths = []
for i in range(len(filenames)):
    with open(filenames[i][1],"rb") as f:
        new = f.read()
    uncompressedString += new
    hashes.append(zlib.crc32(new))
    lengths.append(len(new))
    if i != len(filenames) - 1:
        uncompressedString += (chr(0) * (0x2000 - len(new)))

with open("temp1.bin","wb") as f:
    f.write(uncompressedString)

os.system("bpe.exe temp1.bin temp2.bin 8192 4096 200 3")

with open("temp2.bin","rb") as f:
    compressed = f.read()

with open(sys.argv[2], 'rb') as f:
    f.seek(0xC)
    countOffset = struct.unpack('<L', f.read(4))[0]
    f.seek(countOffset)
    count = struct.unpack('<L', f.read(4))[0]
    hashes = {}
    for i in range(count):
        fileHash = f.read(4)
        nameOffset = struct.unpack('<L', f.read(4))[0]
        cont = f.tell()
        f.seek(nameOffset & 0x00ffffff)
        name = getString(f)
        f.seek(cont + 8)
        hashes[name] = fileHash

with open(sys.argv[1].rstrip('/').rstrip('\\')+".gfa",'wb') as f:
    #actually make the file
    f.write(binascii.unhexlify('47 46 41 43 01 03 00 00 01 00 00 00 2C 00 00 00 EA 00 00 00 00 20 00 00'.replace(' ','')))
    f.write(int32(len(compressed)))
    f.write(chr(0) * 0x10)
    f.write(int32(len(filenames)))
    currentOffset = 0x30 + (0x10 * len(filenames))
    dataStart = 0x2000
    for i in range(len(filenames)):
        if filenames[i][0] in hashes:
            f.write(hashes[filenames[i][0]])
        else:
            f.write(int32(0xFFFFFFFF))
            print 'No hash found for file '+filenames[i][0]
        f.write(int32(currentOffset))
        currentOffset += len(filenames[i][0]) + 1
        f.write(int32(lengths[i]))
        f.write(int32(dataStart))
        dataStart += 0x2000
    for i,j in filenames:
        f.write(i+chr(0))

    f.write(chr(0) * (0x2000 - f.tell()))

    f.write(binascii.unhexlify('47 46 43 50 01 00 00 00 01 00 00 00'.replace(' ','')))
    f.write(int32(len(uncompressedString)))
    f.write(int32(len(compressed)))
    f.write(compressed)
    
