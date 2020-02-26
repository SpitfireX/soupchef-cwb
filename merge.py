import os
import argparse
import gzip

def merge_all(infolder, outpath, filter, trim, compression):
    
    infiles = []

    for path, dirs, files in os.walk(infolder):
        for file in files:
            if str(file).endswith(filter):
                infiles.append((path, file))

    if compression:
        outfile = gzip.open(outpath, mode='wt', encoding='utf-8')
    else:
        outfile = open(outpath, mode='w', encoding='utf-8')

    with outfile:
        for path, file in infiles:

            with open(os.path.join(path, file), mode='r', encoding='utf-8-sig') as infile:
                lines = infile.readlines()
            
            if trim:
                outfile.writelines(lines[1:-1])
            else:
                outfile.writelines(lines)


def main():
    
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-o', default='output/corpus.vrt', dest='outpath',
        help='Sets the output file.')
    argparser.add_argument('-i', dest='infolder', required=True,
        help='Sets the input folder.')
    argparser.add_argument('-e', default='.vrt', dest='extension',
        help='Sets the file extension filter.')
    argparser.add_argument('--trim', action='store_true', default=False, dest='trim',
        help="Trims the first and last line of the input files (i.e. the enclosing root element in vrt/xml files).")
    argparser.add_argument('--gz', action='store_true', default=False, dest='compression',
        help="Gzip kompression of the output file.")
    
    args = argparser.parse_args()

    infolder = os.path.expanduser(args.infolder)
    outpath = os.path.expanduser(args.outpath)
    extension = args.extension
    trim = args.trim
    compression = args.compression

    merge_all(infolder, outpath, extension, trim, compression)


if __name__ == "__main__":
    main()
