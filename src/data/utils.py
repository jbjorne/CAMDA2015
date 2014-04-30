import gzip

def blocks(file, size=65536):
    while True:
        b = file.read(size)
        if not b: break
        yield b

# From http://stackoverflow.com/questions/9629179/python-counting-lines-in-a-huge-10gb-file-as-fast-as-possible
# by user glglgl
def countLines(filename):
    if filename.endswith(".gz"):
        openCmd = gzip.open
    else:
        openCmd = open
    with openCmd(filename, "r") as f:
        return sum(bl.count("\n") for bl in blocks(f))