"""
Interface to query the RxNorm API.
"""
import requests
import Levenshtein as lev
import time
import itertools

RXNORM_REST = "http://rxnav.nlm.nih.gov/REST/"
RXNORM_CLASS_API = "http://rxnav.nlm.nih.gov/REST/rxclass/class/"
RXNORM_CLASS_RXCUI_API = RXNORM_CLASS_API + "byRxcui"
RXNORM_CLASS_NAME_API = RXNORM_CLASS_API + "byDrugName"

SEARCH_URL = RXNORM_REST + "rxcui"
SUGGESTION_URL = RXNORM_REST + "spellingsuggestions"
DRUGS_URL = RXNORM_REST + "drugs"
CLASS_URL = RXNORM_REST + "rxcui/"
APPROXIMATE_URL = RXNORM_REST + "approximateTerm/"
INTERACTION_URL = RXNORM_REST + "interaction/interaction.json"

JSON_HEADER = {'Accept': 'application/json'}

SLEEP_TIME = 1.0


def _query_rxcui(payload):
    conceptR = requests.get(SEARCH_URL, params=payload, headers=JSON_HEADER)
    crJson = conceptR.json()['idGroup']
    time.sleep(SLEEP_TIME)
    if 'rxnormId' in crJson:
        return crJson['rxnormId'][0]
    return None


def get_rxcui(drug):
    """
    Perform a straightforward lookup of the RXCUI
    If doesn't exist it returns None
    """
    payload = {'name': drug, 'search': 2}
    return _query_rxcui(payload)


def get_suggestion(drug, acceptRatio=0.9):
    """
    Get spelling suggestions
    """
    payload = {'name': drug}
    suggestR = requests.get(SUGGESTION_URL, params=payload,
                            headers=JSON_HEADER)
    suggestJson = suggestR.json()
    time.sleep(SLEEP_TIME)
    # if there's no sugestion just remove it
    if suggestJson['suggestionGroup']['suggestionList'] is None:
        return None
    # make sure the new suggestion is close at least
    newDrug = suggestJson['suggestionGroup']['suggestionList']['suggestion'][0]
    if lev.distance(str(drug), str(newDrug.lower())) > 1 and lev.ratio(str(drug), str(newDrug.lower())) < acceptRatio:
        return None
    return newDrug


def get_approx_term(drug):
    """
    Get approximate / related drugs
    """
    payload = {'term': drug, 'maxEntries': 1}
    response = requests.get(APPROXIMATE_URL, params=payload,
                            headers=JSON_HEADER)
    txt = response.json()
    time.sleep(SLEEP_TIME)
    # just go through the first one
    if "candidate" not in txt["approximateGroup"] or \
       txt["approximateGroup"]['candidate'] is None:
        return None
    rxcui = txt["approximateGroup"]['candidate'][0]['rxcui']
    # look up related ones
    relatedDrugs = get_related(rxcui, matchType=["SBD"])
    if relatedDrugs is None:
        return None
    drugWords = drug.split(' ')
    # check to see if any of them contain all of the drug words
    if any([all([dd in x for dd in drugWords]) for x in relatedDrugs]):
        # if so just return the brand name
        return get_related(rxcui, matchType=["BN"])
    return None


def _get_concepts(x):
    if 'conceptProperties' not in x:
        return None
    return x['conceptProperties']


def get_drugs(drug):
    """
    """
    payload = {'name': drug}
    response = requests.get(DRUGS_URL, params=payload, headers=JSON_HEADER)
    txt = response.json()
    time.sleep(SLEEP_TIME)
    if 'drugGroup' not in txt or 'conceptGroup' not in txt['drugGroup']:
        return None
    drugNames = filter(lambda x: x["tty"] == 'SBD',
                       txt['drugGroup']['conceptGroup'])
    if len(drugNames) == 0:
        return None
    drugNames = _get_concepts(drugNames[0])
    if drugNames is None or len(drugNames) == 0:
        return None
    brands = map(lambda x: x["name"], drugNames)
    brands = set(map(lambda x: x[x.find("[") + 1:x.find("]")], brands))
    return brands


def lower_name(x):
    return x["name"].lower()


def get_related(rxcui, matchType=["MIN", "BN"], mapFunc=lower_name):
    drugURL = CLASS_URL + rxcui + "/allrelated"
    response = requests.get(drugURL, headers=JSON_HEADER)
    txt = response.json()
    time.sleep(SLEEP_TIME)
    if 'allRelatedGroup' not in txt or \
       "conceptGroup" not in txt['allRelatedGroup']:
        return None
    drugInfo = filter(lambda x: x["tty"] in matchType,
                      txt['allRelatedGroup']['conceptGroup'])
    if len(drugInfo) == 0:
        return None
    drugInfo = map(_get_concepts, drugInfo)
    drugInfo = filter(None, drugInfo)
    if len(drugInfo) == 0:
        return None
    drugInfo = list(itertools.chain(*drugInfo))
    ingredients = map(mapFunc, drugInfo)
    return ingredients


def _get_concept_item(drugInfo, id):
    if "rxclassMinConceptItem" not in drugInfo:
        return None
    return drugInfo["rxclassMinConceptItem"][id]


def _query_rxclass(queryLoc, payload, conceptID="className"):
    response = requests.get(queryLoc, params=payload,
                            headers=JSON_HEADER)
    txt = response.json()
    time.sleep(SLEEP_TIME)
    if "rxclassDrugInfoList" not in txt or \
       "rxclassDrugInfo" not in txt["rxclassDrugInfoList"]:
        return []
    drugInfo = map(lambda x: _get_concept_item(x, conceptID),
                   txt["rxclassDrugInfoList"]["rxclassDrugInfo"])
    return filter(None, drugInfo)


def get_ingredients(rxcui):
    payload = {'rxcui': rxcui, "relaSource": "NDFRT",
               "relas": "has_Ingredient"}
    return _query_rxclass(RXNORM_CLASS_RXCUI_API, payload)


def ndc_to_rxcui(ndc):
    payload = {'idtype': "NDC", 'id': ndc}
    return _query_rxcui(payload)


def rxcui_to_category(rxcui, relaSource="MESH"):
    """
    Get the concept type for either MESH or ATC
    """
    payload = {'rxcui': rxcui, "relaSource": relaSource}
    return _query_rxclass(RXNORM_CLASS_RXCUI_API, payload, "classId")


def drug_to_category(drugName, relaSource="MESH"):
    """
    Get the concept type for either MESH or ATC using drug name
    """
    payload = {'drugName': drugName, "relaSource": relaSource}
    return _query_rxclass(RXNORM_CLASS_NAME_API, payload, "classId")


def _get_drug_interaction(ddi):
    if "interactionConcept" not in ddi:
        return None
    ip = ddi["interactionConcept"]
    if len(ip) < 2:
        return None
    return {"rxcui": ip[1]["minConceptItem"]["rxcui"],
            "name": ip[1]["minConceptItem"]["name"]}


def rxcui_ddi(rxcui):
    payload = {'rxcui': rxcui}
    response = requests.get(INTERACTION_URL, params=payload,
                            headers=JSON_HEADER)
    txt = response.json()
    time.sleep(SLEEP_TIME)
    interactions = []
    if "interactionTypeGroup" not in txt:
        return interactions
    for itg in txt["interactionTypeGroup"]:
        if "interactionType" not in itg:    # noqa
            continue
        # filter out those without interaction pair
        possibleInt = filter(lambda x: "interactionPair" in x,
                             itg["interactionType"])
        ipList = map(lambda x: x["interactionPair"], possibleInt)
        ipList = [item for sublist in ipList for item in sublist]
        tmpInt = map(_get_drug_interaction, ipList)
        interactions.extend(filter(None, tmpInt))
    return interactions
