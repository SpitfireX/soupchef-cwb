import os
import argparse

def merge_all(infolder, outpath, filter, trim):
    
    infiles = []

    for path, dirs, files in os.walk(infolder):
        for file in files:
            if str(file).endswith(filter):
                infiles.append((path, file))

    with open(outpath, mode='w', encoding='utf-8') as outfile:
        for path, file in infiles:

            with open(os.path.join(path, file), mode='r', encoding='utf-8-sig') as infile:
                lines = infile.readlines()
            
            if trim:
                outfile.writelines(lines[1:-2])
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
    
    args = argparser.parse_args()

    infolder = os.path.expanduser(args.infolder)
    outpath = os.path.expanduser(args.outpath)
    extension = args.extension
    trim = args.trim

    merge_all(infolder, outpath, extension, trim)


if __name__ == "__main__":
    main()
