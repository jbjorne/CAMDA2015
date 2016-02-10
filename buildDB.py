import os
import database.download
import utils.Stream as Stream

if __name__ == "__main__":
    downloadPath = os.path.expanduser("~/data/CAMDA2015-data-local/download")
    Stream.openLog(os.path.join(downloadPath, "log.txt"), clear = False)
    database.download.downloadProjects(downloadPath, ["meth_array","meth_seq"])