"""
Preprocess the medication file by:
    - format the medication
    - each line has a single reason
    - cleans up some words
"""
import csv
import re
import json
import difflib
import sys
import time
sys.path.append("../data-preprocess")

import formatMed

def appendDrugs(drugName, drugCats, drugDict):
    if not drugDict.has_key(drugName):
        drugDict[drugName] = {"cat":drugCats, "type": "generic"}
    return drugDict


def format_med_string(drug):
    drug = drug.strip().lower()
    words = drug.split()
    word_list = set(words)
    drug = " ".join(sorted(word_list, key=words.index))
    return drug


def _return_drug(med, drugType):
    return {"type": 'D', "cat": drugType, "name": med}


def search_drug(med, medDict):
    medupdate, drugType = formatMed.get_med_approx(med, medDict)
    if drugType is not None:
        return _return_drug(med, drugType)
    medWords = med.split()
    if len(medWords) > 1:
        ## try the last word
        medupdate, drugType = formatMed.get_med_approx(medWords[-1], medDict)
        if drugType is not None:
            return _return_drug(med, drugType)
    medupdate, drugType = formatMed.get_med_approx(medWords[0], medDict)
    if drugType is not None:
            return _return_drug(med, drugType)
    return None
    

def main():
    medFile = open('raw_data.csv', 'rb')
    medReader = csv.reader(medFile, delimiter=",")
    outFile = open('med_processed_with_categories.csv', 'wb')
    outWriter = csv.writer(outFile, delimiter=",")
    ## read and write the header and add a new column for revised symptoms
    header = medReader.next()
    outWriter.writerow(header + ['cat_v2', 'med_v2', 'med_class', 'help_v2'])
    MED_NAME_IDX = 1       ## MED NAME COLUMN
    MED_TYPE_IDX = 1        ## MEDICATION CLASSIFICATION
    suppDict = json.load(open('../data-preprocess/data/rxlist-supp.json', 'rb'))
    medDict = json.load(open('create_med_dict_file_OUTPUT.json', 'rb')) 
    drugDict = {}
    for row in medReader:
        print row
        if len(row) <= 0:
            continue
        med = format_med_string(row[MED_NAME_IDX])
        medType = row[MED_TYPE_IDX].lower()
        medHelp = ''
        if med == "":
            continue
        if med in drugDict:
            medInfo = drugDict[med]
            for medCat in medInfo['cat']:
                outWriter.writerow(row + [medInfo['type'], medInfo['name'], medCat, medHelp])
            continue
        print "Looking up:" + med
        # see if it exists in the medication dictionar
        medInfo = search_drug(med, medDict)
        if medInfo is not None:
            drugDict[med] = medInfo
            for medCat in medInfo['cat']:
                outWriter.writerow(row + [medInfo['type'], medInfo['name'], medCat, medHelp])
            continue 
        # next try the supplement dictionary
        drugType = formatMed.get_supp_approx(med, suppDict)
        if drugType is not None:
            drugDict[med] = {"type": 'S', "cat": drugType, "name": med}
            outWriter.writerow(row + ['S', med, drugType, medHelp])
        else: 
            print "unable to resolve drug:" + med
            drugDict[med] = {"type": 'U', "cat": "unknown", "name": med}
            outWriter.writerow(row + ['U', med, "unknown", medHelp])
    medFile.close()
    outFile.close()
    
if __name__ == "__main__":
    main()
