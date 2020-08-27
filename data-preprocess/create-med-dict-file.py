"""
Create a file-specific medication mapping.
Note that this should be run against the JSON file that is
produced from extract-med-count.py
"""
import formatMed
import json
import requests
import time
import argparse
from collections import OrderedDict


def _try_format(med, medDict):
    try:
        medName, drugType = formatMed.get_med_approx(med, medDict)
    except requests.exceptions.ConnectionError:
        print("Skipping this one:", med)
        return None
    return drugType


def _append_to_dict(k, outputDict, medDict, suppDict):
    # first try it as it is
    drugType = _try_format(k, medDict)
    if drugType is not None:
        outputDict[k] = drugType
        return True, outputDict
    # if not try the supplement approximation
    drugType = formatMed.get_supp_approx(k, suppDict)
    if drugType is not None:
        outputDict[k] = [drugType]
        return True, outputDict
    # try removing the words
    medWords = k.split()
    if len(medWords) > 1:
        # try the last word
        drugType = _try_format(medWords[-1], medDict)
        if drugType is not None:
            outputDict[k] = drugType
            return True, outputDict
        drugType = _try_format(medWords[0], medDict)
        if drugType is not None:
            outputDict[k] = drugType
            return True, outputDict
    return False, outputDict


def create_med_dict(filename, outputDict, mdFile, spFile):
    medCount = json.load(open(filename, 'rb'))
    medDict = json.load(open(mdFile, "rb"))
    suppDict = json.load(open(spFile, "rb"))
    fileDict = {}
    unmatchedDict = {}
    errList = []
    for k, v in sorted(medCount.iteritems(), key=lambda (k, v): (v, k),
                       reverse=True):
        if k in medDict:
            fileDict[k] = medDict[k]
            continue
        if k in suppDict:
            fileDict[k] = suppDict[k]
            continue
        success, fileDict = _append_to_dict(k, fileDict, medDict, suppDict)
        if success is None:
            # try again with a wait period
            time.sleep(1)
            success, fileDict = _append_to_dict(k, fileDict,
                                                medDict, suppDict)
            if success is None:
                errList.append(k)
                continue
        elif not success:
            unmatchedDict[k] = v
    # do one last check
    for med in errList[:]:
        success, fileDict = _append_to_dict(med, fileDict, medDict, suppDict)
        if success is None:
            print("Unable to resolve:", med)
            continue
        elif not success:
            unmatchedDict[med] = medCount[med]
        errList.remove(med)
    with open(outputDict, 'wb') as outfile:
        json.dump(fileDict, outfile, indent=2)
    with open('unresolved.json', 'wb') as outfile:
        json.dump(OrderedDict(sorted(unmatchedDict.items(),
                                     key=lambda t: t[1],
                                     reverse=True)),
                  outfile, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="input file")
    parser.add_argument('outfile', help="output file")
    parser.add_argument("-md", help="medication file", default="data/drugDict.json")    # noqa
    parser.add_argument("-sp", help="supplement file", default="data/rxlist-supp.json")    # noqa
    args = parser.parse_args()
    create_med_dict(args.infile, args.outfile, args.md, args.sp)

if __name__ == "__main__":
    main()
