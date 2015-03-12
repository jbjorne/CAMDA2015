import urllib
import sys, os, shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.progressbar import FileTransferSpeed, Bar, Percentage, ETA, ProgressBar
import tarfile
import zipfile
import tempfile

pbar = None

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

# Modified from http://code.activestate.com/recipes/576714-extract-a-compressed-file/
def extractPackage(path, destPath, subPath=None):
    if path.endswith('.zip'):
        opener, mode = zipfile.ZipFile, 'r'
        namelister = zipfile.ZipFile.namelist
    elif path.endswith('.tar.gz') or path.endswith('.tgz'):
        opener, mode = tarfile.open, 'r:gz'
        namelister = tarfile.TarFile.getnames
    elif path.endswith('.tar.bz2') or path.endswith('.tbz'):
        opener, mode = tarfile.open, 'r:bz2'
        namelister = tarfile.TarFile.getnames
    else: 
        raise ValueError, "Could not extract `%s` as no appropriate extractor is found" % path
    
    file = opener(path, mode)
    names = namelister(file)
    if subPath == None:
        file.extractall(destPath)
    else:
        tempdir = tempfile.mkdtemp()
        file.extractall(tempdir)
        copytree(os.path.join(tempdir, subPath), destPath)
        shutil.rmtree(tempdir)
    file.close()
    return names

def downloadProgress(count, blockSize, totalSize):
    percent = int(count*blockSize*100/totalSize)
    percent = max(0, min(percent, 100)) # clamp
    pbar.update(percent)

def downloadWget(url, filename):
    import subprocess
    subprocess.call(["wget", "--output-document=" + filename, url])

def download(url, destPath=None, addName=True, clear=False):
    global pbar
    
    origUrl = url
    redirectedUrl = urllib.urlopen(url).geturl()
    if redirectedUrl != url:
        print >> sys.stderr, "Redirected to", redirectedUrl
    if destPath == None:
        destPath = os.path.join(tempfile.gettempdir(), "CAMDA2014")
    destFileName = destPath
    if addName:
        destFileName = destPath + "/" + os.path.basename(origUrl)
    if not os.path.exists(os.path.dirname(destFileName)):
        os.makedirs(os.path.dirname(destFileName))
    if clear or not os.path.exists(destFileName):
        if os.path.exists(destFileName): # clear existing file
            os.remove(destFileName)
        print >> sys.stderr, "Downloading file", redirectedUrl, "to", destFileName
        widgets = [FileTransferSpeed(),' <<<', Bar(), '>>> ', Percentage(),' ', ETA()]
        pbar = ProgressBar(widgets=widgets, maxval=100)
        pbar.start()
        try:
            urllib.FancyURLopener().retrieve(redirectedUrl, destFileName, reporthook=downloadProgress)
        except IOError, e:
            print >> sys.stderr, e.errno
            print >> sys.stderr, "Error downloading file", redirectedUrl
            pbar.finish()
            pbar = None
            print >> sys.stderr, "Attempting download with wget"
            downloadWget(origUrl, destFileName)
            if os.path.exists(destFileName):
                return destFileName
            else:
                print >> sys.stderr, "Error downloading file", origUrl, "with wget"
                return None
        pbar.finish()
        pbar = None
    else:
        print >> sys.stderr, "Skipping already downloaded file", url
    return destFileName