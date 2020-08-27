import csv
import argparse
import json
from collections import Counter


def parse_file(filename, medIdx, delim, header):
    medFile = csv.reader(open(filename, 'r'), delimiter=delim)
    medCounter = Counter()
    if header:
        medFile.next()
    for row in medFile:
        if len(row) > medIdx:
            med = row[medIdx].strip().lower()
            medCounter[med] += 1
    return medCounter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="input file")
    parser.add_argument("medIdx", type=int, help="column index for medication")
    parser.add_argument("-sep", type=int, default=1,
                        help="delimiter seperator")
    parser.add_argument('outfile', help="output file")
    parser.add_argument("-hdr", action='store_true')
    args = parser.parse_args()
    sepType = ","
    if args.sep == 2:
        sepType = "\t"
    medCounter = parse_file(args.infile, args.medIdx, sepType, args.hdr)
    with open(args.outfile, 'w') as outfile:
        json.dump(medCounter, outfile, indent=2)

if __name__ == "__main__":
    main()
