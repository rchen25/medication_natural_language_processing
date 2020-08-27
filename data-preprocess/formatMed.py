import difflib
import json
import re
import pprint
import Levenshtein
import numpy as np
import itertools
import queryRxNorm
from format_tools import not_decimal, clean_words

MED_SYN = json.load(open("data/med_synonym.json"))


def decimal_and_pattern(x, patt):
    if patt not in x:
        return x
    if re.match(r'^\d+\.?\d*', x):
        return ''
    return x


def _check_num_slash(x):
    if re.match(r'^\d+/\d+', x):
        return ''
    return x


def _split_and_strip(txt, delim):
    word = txt.split(delim)
    return map(lambda x: x.strip(), word)


def try_splits(med):
    word = [med]
    if ":" in med:
        word = _split_and_strip(med, ":")
    elif "(" in med:
        word = _split_and_strip(med, "(")
        word = map(lambda x: x.replace(")", "").strip(), word)
    elif ";" in med:
        word = _split_and_strip(med, ";")
    return word


def _format_return(med, words, medDict):
    if med in medDict:
        return med, words, medDict[med]
    return med, words, None


def try_with(med, words, medDict):
    if "/" in med:
        tmpMed = med.replace("/", " with ")
        tmpWords = clean_words(tmpMed.split(' '))
        tmpMed = ' '.join(tmpWords)
        if tmpMed in medDict:
            return _format_return(tmpMed, tmpWords, medDict)
    return _format_return(med, words, medDict)


def fix_sort_slash(med, words, medDict):
    if "/" not in med:
        return _format_return(med, words, medDict)
    slashWords = med.split('/')
    slashWords = clean_words(slashWords)
    slashWords = sorted(slashWords)
    med1 = '/'.join(slashWords)
    return _format_return(med1, slashWords, medDict)


def try_no_slash(med, words, medDict):
    if "/" in med:
        tmpMed = ' '.join(words)
        if tmpMed in medDict:
            return _format_return(tmpMed, words, medDict)
        tmpMed = ' '.join(words[::-1])
        if tmpMed in medDict:
            return _format_return(tmpMed, words, medDict)
    return _format_return(med, words, medDict)


def slash_subclass(med, words, medDict):
    if "/" in med:
        slashWords = med.split('/')
        slashWords = clean_words(slashWords)
        slashCat = map(lambda x: x in medDict, slashWords)
        if all(slashCat):
            slashCat = map(lambda x: medDict[x], slashWords)
            if all(x == slashCat[0] for x in slashCat):
                return _format_return(slashWords[0], words, medDict)
    return _format_return(med, words, medDict)


def fix_dash(med, words, medDict):
    if "-" not in med:
        return _format_return(med, words, medDict)
    noDash = med.replace('-', ' ')
    words = clean_words(noDash.split(' '))
    tmpWords = sorted(words)
    tmpMed = '/'.join(tmpWords)
    if tmpMed in medDict:
        return _format_return(tmpMed, tmpWords, medDict)
    return _format_return(' '.join(words), words, medDict)


def fix_synonyms(med, medWords, medDict, charSep=' '):
    synDict = {"+": "/", "with": "/"}
    synDict.update(MED_SYN)
    for k, word in enumerate(medWords):
        if word in synDict:
            medWords[k] = synDict[word]
    return _format_return(charSep.join(medWords), medWords, medDict)


def fix_words(med, medWords, medDict):
    medWords = map(lambda x: x.replace(';', ''), medWords)
    medWords = map(lambda x: x.replace('\'', ''), medWords)
    badWords = set(['inj.', 'inj', 'injection', 'cream', 'hcl',
                    'oral', 'concentrate', 'ointment', 'liquid',
                    'suspension', "patch", 'chewable', '.', 'neb',
                    'flush', 'protocol', 'initiated', 'patient', 'uses',
                    'intra-muscular', 'intramuscular', 'transdermal',
                    'valerate', 'sublingual', 'syrup', 'extract',
                    'capsule', 'cap', 'dissolve', 'tablet', 'tab', 'mdi',
                    'soln', 'solution', 'infusion', '%', 'sustained',
                    'elixir', 'powder', 'inhaler', 'hfa', 'suppository',
                    'topical', 'disintegrating', 'delayed', 'jelly', 'gel',
                    'monohydrate', 'macrocrystals', 'macrocrystal', 'otic',
                    'immediate', 'releas', 'release', 'pca', 'h2o', 'human',
                    'sliding', 'scale', 'scal', 'bolus', 'take',
                    'home', 'pack', 'coated', 'parenteral', 'vaginal', "#",
                    'supp', 'supplements', 'er'])
    words = sorted(set(medWords).difference(badWords), key=medWords.index)
    words = map(lambda x: x.replace('%', ''), words)
    words = map(_check_num_slash, words)
    words = clean_words(words)
    return _format_return(' '.join(words), words, medDict)


def _remove_word(words, txt, medDict):
    medWords = filter(lambda x: x not in set(['hr', 'ns', txt, '/']), words)
    medWords = map(lambda x: decimal_and_pattern(x, txt), medWords)
    medWords = clean_words(medWords)
    return _format_return(' '.join(medWords), medWords, medDict)


def check_strength(med, words, medDict):
    for pattern in ['mg/ml', 'mcg/hr', 'mg/hr', 'gm/l', 'gm', 'ml',
                    'units/ns', 'units', 'cd', 'cr', 'la', 'sr', 'tr'
                    'xl', 'xr', 'ds', 'dr', 'qt']:
        if pattern in med:
            med, words, medT = _remove_word(words, pattern, medDict)
    if 'mg' in med and "/" in med:
        # remove the word with mg in it
        return _remove_word(words, 'mg', medDict)
    if 'mcg' in med and "/" in med:
        return _remove_word(words, 'mcg', medDict)
    return _format_return(med, words, medDict)


def check_eyes(med, words, medDict):
    if 'ophthalmic' in med:
        return _remove_word(words, 'ophthalmic', medDict)
    if 'eye drop' in med:
        cleanWords = set(words).difference(set(['eye', 'drops', 'drop']))
        cleanWords = sorted(cleanWords, key=words.index)
        medWords = clean_words(cleanWords)
        medWords = filter(not_decimal, cleanWords)
        return _format_return(' '.join(medWords), medWords, medDict)
    return _format_return(med, words, medDict)


def fuzzy_match(med, words, medDict):
    txt = difflib.get_close_matches(med, medDict.keys(),
                                    cutoff=0.9, n=1)
    if len(txt) > 0:
        print "matched:" + med + " with " + txt[0]
        return _format_return(txt[0], words, medDict)
    return _format_return(med, words, medDict)


def _check_dist(med, x):
    return (Levenshtein.ratio(str(med), str(x)) > 0.85 and
            Levenshtein.distance(str(med), str(x)) < 2)


def quick_match(med, words, medDict):
    medKeys = medDict.keys()
    tmp = map(lambda x: _check_dist(med, x), medKeys)
    if any(tmp):
        idx = np.flatnonzero(np.array(tmp))[0]
        return _format_return(medKeys[idx], words, medDict)
    return _format_return(med, words, medDict)


def quick_lookup(med, words, medDict):
    quickLookup = {'sodium chloride': 'sodium chloride',
                   'levothyroxine': 'synthroid',
                   'heparin': 'heparin',
                   'immune globulin': 'immune globulins',
                   "dialysate": "dialysate",
                   'epoetin': 'epoetin alfa',
                   "kayexalate": "kayexalate",
                   'penicillin': "penicillins",
                   "prismasol": "prismasol",
                   "quinolone": "quinolones",
                   'synthroid': 'synthroid',
                   'tetanus': 'immunostimulants',
                   'tpn': 'tpn',
                   'vaccine': 'vaccine'}
    for k, v in quickLookup.iteritems():
        if k in med and 'discontinue' not in med:
            return _format_return(v, words, medDict)
    return _format_return(med, words, medDict)


def remove_parens(med, words, medDict):
    if "(" in med:
        regex = re.compile('\(.+?\)')
        med = regex.sub('', med)
        words = med.split(' ')
    if "[" in med:
        regex = re.compile('\[.+?\]')
        med = regex.sub('', med).strip()
        words = med.split(' ')
    if ":" in med:
        med = med.split(":")[0]
        words = med.split(' ')
    return _format_return(med, words, medDict)


def remove_extra(med, words, medDict):
    extraWords = ['baby', 'acetate', 'nasal', 'sulfate', 'pm', 'eye',
                  'plus', 'tears', 'spray', 'pump', 'citrate', 'enteric',
                  'carbonate', 'sodium', 'magnesium', 'single',
                  'strength', 'tartrate', 'extended', 'lozenge', 'complex',
                  'rinse', 'system', 'controlled', 'dl', 'regimem', 'xt',
                  'rate', 'electrolytes', 'instructions', 'lite', 'drugs',
                  'drugs', 'ordered', 'per', 'heo']
    for ex in extraWords:
        if ex in words:
            words.remove(ex)
            med1 = ' '.join(words)
            if med1 in medDict:
                return _format_return(med1, words, medDict)
    return _format_return(' '.join(words), words, medDict)


def fix_vitamin(med, words, medDict):
    if 'vitamins' in med:
        med = med.replace('vitamins', 'vitamin')
        words = med.split(' ')
    if 'multivitamin' in med:
        if '/' in med:
            med1 = med.replace('/', 'with')
            if med1 in medDict:
                return _format_return(med1, words, medDict)
    if 'caltrate' in med and 'vitamin d' in med:
        return _format_return('caltrate 600+d', words, medDict)
    return _format_return(med, words, medDict)


def truncate_for(med, words, medDict):
    if 'for' not in words:
        return _format_return(med, words, medDict)
    # otherwise let's drop everything after for
    forIdx = words.index('for')
    updatedWords = words[:forIdx]
    updatedMed = ' '.join(updatedWords)
    return _format_return(updatedMed, updatedWords, medDict)


def lookup_rxcui(med):
    rxcui = queryRxNorm.get_rxcui(med)
    if rxcui is not None:
        return med, rxcui
    newName = queryRxNorm.get_suggestion(med)
    if newName is None:
        return med, None
    rxcui = queryRxNorm.get_rxcui(newName)
    return newName, rxcui


def _find_most_similar(med, medKeys):
    scores = map(lambda x: Levenshtein.ratio(str(med), str(x)), medKeys)
    if np.max(scores) > 0.90:
        return medKeys[np.argmax(scores)]
    return None


def _check_items_in_dict(liItems, medDict):
    liCat = map(lambda x: x in medDict, liItems)
    if any(liCat):
        return liCat.index(True)
    return None


def check_rxnorm(med, medDict):
    newName, rxcui = lookup_rxcui(med)
    if rxcui is not None:
        # get related information
        ingd = queryRxNorm.get_related(rxcui)
        if ingd is not None:
            # clean the space between the slashes
            ingd = map(lambda x: x.replace(' / ', '/'), ingd)
            catIdx = _check_items_in_dict(ingd, medDict)
            if catIdx is not None:
                print "RxNorm Brand:" + str(med) + "->" + str(ingd[catIdx])
                return medDict[ingd[catIdx]]
            # do a soft spelling check
            ingdSoft = map(lambda x: _find_most_similar(x, medDict.keys()),
                           ingd)
            ingdSoft = filter(None, ingdSoft)
            if len(ingdSoft) > 0:
                return medDict[ingdSoft[0]]
    brands = queryRxNorm.get_drugs(newName)
    if brands is not None:
        brandsIdx = _check_items_in_dict(brands, medDict)
        if brandsIdx is not None:
            print "RxNorm Brand:" + str(med) + "->" + str(brands[brandsIdx])
            return medDict[brands[brandsIdx]]
    approxTerms = queryRxNorm.get_approx_term(med)
    if approxTerms is not None:
        approxIdx = _check_items_in_dict(approxTerms, medDict)
        if approxIdx is not None:
            print "RxNorm Brand:" + str(med) + "->" + str(approxTerms[approxIdx])   # noqa
            return medDict[approxTerms[approxIdx]]
    return None


def get_med_approx(med, medDict):
    med = med.replace(' - ', '-')
    # search by splitting either on : or ()
    medWords = try_splits(med)
    medSuccess = map(lambda x: x in medDict, medWords)
    if any(medSuccess):
        idx = medSuccess.index(True)
        return medWords[idx], medDict[medWords[idx]]
    tmpMed = med.replace("w/", "/ ")
    words = tmpMed.split(' ')
    cleanFuncs = [remove_parens, quick_match, fix_synonyms, fix_words,
                  fix_vitamin, quick_match, try_with,
                  truncate_for, check_strength,
                  fix_sort_slash,
                  try_no_slash, slash_subclass, fix_dash,
                  check_eyes, fuzzy_match, quick_lookup,
                  remove_extra, quick_match]
    for func in cleanFuncs:
        # print str(func), tmpMed, words
        tmpMed, words, medType = func(tmpMed, words, medDict)
        if medType is not None:
            print "Med:" + str(med) + " = " + str(tmpMed)
            return tmpMed, medType
        if not len(words):
            return med, None
    if "/" in med:
        slashWords = med.split('/')
        slashWords = clean_words(slashWords)
        slashCat = map(lambda x: x in medDict, slashWords)
        if all(slashCat):
            slashCat = map(lambda x: medDict[x], slashWords)
            grpCat = set(list(itertools.chain(*slashCat)))
            print "Concatenated together:" + med
            return ' '.join(slashWords), list(grpCat)
    medType = check_rxnorm(med, medDict)
    if medType is not None:
        return med, medType
    medType = check_rxnorm(tmpMed, medDict)
    return tmpMed, medType


def format_supplement(med):
    medWords = med.split(' ')
    badWords = set(['extract', 'juice'])
    words = sorted(set(medWords).difference(badWords), key=medWords.index)
    return ' '.join(words)


def get_supp_approx(med, suppDict):
    RETURN_TYPE = "unclassified supplement"
    if med in suppDict:
        return RETURN_TYPE
    newSupp = format_supplement(med)
    if newSupp in suppDict:
        return RETURN_TYPE
    txt = difflib.get_close_matches(med, suppDict.keys(), cutoff=0.9, n=1)
    if len(txt) > 0:
        return RETURN_TYPE
    return None


def main():
    import json
    uk2 = json.load(open('ungrouped.json', 'rb'))
    medDict = json.load(open("data/drugDict.json", "rb"))
    suppDict = json.load(open("data/suppDict.json", "rb"))
    uk1 = set([])
    for med in sorted(uk2.keys()):
        if med in medDict:
            continue
        # let's try to shrink space between -
        _, medType = get_med_approx(med, medDict)
        if medType is not None:
            continue
        if med in suppDict:
            print "supplement:" + str(med)
            continue
        newSupp = format_supplement(med)
        if newSupp in suppDict:
            print "supplement:" + str(med)
            continue
        txt = difflib.get_close_matches(med, suppDict.keys(),
                                        cutoff=0.9, n=1)
        if len(txt) > 0:
            print "matched:" + med + " with " + txt[0]
            continue
        uk1.add(med)
    pprint.pprint(sorted(uk1))
    print len(uk1)


if __name__ == "__main__":
    main()
