import os
import database.test
import utils.Stream as Stream

if __name__ == "__main__":
    downloadPath = os.path.expanduser("~/data/CAMDA2015-data-local/download")
    Stream.openLog(os.path.join(downloadPath, "log.txt"), clear = False)
    database.test.downloadProjects(downloadPath, ["meth_array"])