import os
from src.database.download import downloadProjects
from src.database.build import importProjects
import src.utils.Stream as Stream
from src.utils.common import splitOptions

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Download ICGC release 20 and store it in an SQLite database')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-a', "--action", default="download,build", dest="action")
    parser.add_argument('-s','--skipTypes', default="meth_array,meth_seq", help="Do not download or import these dataTypes")
    groupD = parser.add_argument_group('download', 'Download ICGC files')
    parser.add_argument('-d','--download', default=None, help="Download directory (optional)")
    parser.add_argument('-p','--projects', default=None, help="Download only these ICGC projects")
    parser.add_argument('-c','--clear', help='Delete existing downloads', action='store_true', default=False)
    groupB = parser.add_argument_group('build', 'Build the database from downloaded files')
    parser.add_argument('-l','--limitTypes', default=None, help="Use only these datatypes")
    parser.add_argument('-b','--batchSize', type=int, default=200000, help="SQL insert rows batch size")
    options = parser.parse_args()
    
    if options.download == None:
        options.download = os.path.join(options.output, "download")
    
    actions = splitOptions(options.action, ["download", "build"])
    skipTypes = options.skipTypes.split(",") if options.skipTypes else None
    limitTypes = options.limitTypes.split(",") if options.limitTypes else None
    projects = options.projects.split(",") if options.projects else None
    Stream.openLog(os.path.join(options.output, "log.txt"))
    if "download" in actions:
        print "======================================================"
        print "Downloading ICGC files"
        print "======================================================"
        downloadProjects(options.download, skipTypes, options.projects, options.clear)
    if "build" in actions:
        print "======================================================"
        print "Building ICGC database"
        print "======================================================"
        importProjects(options.download, os.path.join(options.output, "ICGC-20.sqlite"), skipTypes, limitTypes, options.batchSize)