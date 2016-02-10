import os
from src.database.download import downloadProjects
from src.database.build import importProjects
import src.utils.Stream as Stream
from src.utils.common import splitOptions

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-a', "--action", default="download,build", dest="action")
    groupD = parser.add_argument_group('download', 'Download ICGC files')
    parser.add_argument('-d','--download', default=None, help="Download directory (optional)")
    parser.add_argument('-s','--skipTypes', default="meth_array,meth_seq", help="Do not download these dataTypes")
    parser.add_argument('-c','--clear', help='Delete existing downloads', action='store_true', default=False)
    groupB = parser.add_argument_group('build', 'Build the database from downloaded files')
    parser.add_argument('-s','--skipTypes', default="meth_array,meth_exp", help="Do not download these dataTypes")
    parser.add_argument('-l','--limitTypes', default=None, help="Use only these datatypes")
    parser.add_argument('-b','--batchSize', type=int, default=200000, help="SQL insert rows batch size")
    options = parser.parse_args()
    
    if options.download == None:
        options.download = os.path.join(options.output, "download")
    
    actions = splitOptions(options.action, ["download", "build"])
    skipTypes = options.skipTypes.split(",") if options.skipTypes else None
    limitTypes = options.limitTypes.split(",") if options.limitTypes else None
    Stream.openLog(options.output + ".log.txt", clear = True)
    if "download" in actions:
        print "======================================================"
        print "Downloading ICGC files"
        print "======================================================"
        downloadProjects(options.download, skipTypes, options.clear)
    if "build" in actions:
        print "======================================================"
        print "Building ICGC database"
        print "======================================================"
        importProjects(options.download, options.output, skipTypes, limitTypes, options.batchSize)