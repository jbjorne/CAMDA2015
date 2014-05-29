from utils.download import *
import data.buildDB
import gene.buildCancerGeneIndexDB
import subprocess
import settings

# From http://code.activestate.com/recipes/577058/
def query_yes_no(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.
    
    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":"yes", "y":"yes", "no":"no", "n":"no"}
    rv = {"yes":True, "y":True, "no":False, "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while 1:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return rv[default]
        elif choice in valid.keys():
            return rv[valid[choice]]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")

def setupRLSCore():
    print "Installing RLSCore"
    url = "https://github.com/aatapa/RLScore/archive/master.zip"
    libPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
    downloaded = download(url, None, clear=False)
    if os.path.exists(os.path.join(libPath, "ext_src")):
        shutil.rmtree(os.path.join(libPath, "ext_src"))
    if os.path.exists(os.path.join(libPath, "rlscore")):
        shutil.rmtree(os.path.join(libPath, "rlscore"))
    extractPackage(downloaded, libPath, subPath="RLScore-master")
    cwd = os.getcwd()
    os.chdir(libPath)
    #print os.listdir(os.getcwd())
    subprocess.call(['python', 'setup.py'])
    os.chdir(cwd)
    # Remove installation files
    #shutil.rmtree(os.path.join(libPath, "ext_src"))

if __name__ == "__main__":
    if query_yes_no("Install RLSCore"):
        setupRLSCore()
    if query_yes_no("Download and build ICGC database (requires ~30 Gb disk space)"):
        data.buildDB.buildICGCDatabase()
    if query_yes_no("Download and build NCI Cancer Gene Index database (requires ~300 Mb disk space)"):
        print "Building NCI Cancer Gene Index database"
        gene.buildCancerGeneIndexDB.buildDB(settings.CGI_DB_PATH, settings.CGI_DOWNLOAD_PATH)