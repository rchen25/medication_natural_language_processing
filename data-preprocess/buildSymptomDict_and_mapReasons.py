import csv
import pprint
import difflib
from collections import Counter
from nltk.stem.lancaster import LancasterStemmer
import pandas as pd
import numpy as np
import sys

filename_input_med_processed_drugs_only = sys.argv[1] #ex; med_processed_with_categories.csv
filename_output_patient_matchedReason_med = sys.argv[2] #ex; df_all_patient_matched_reason_med.csv
filename_output_matched_reason_count = sys.argv[3] #ex; df_matched_reason_count.csv
filename_output_unmatched_reason_count = sys.argv[4] #ex: df_unmatched_reason_count.csv

### COLUMNS TO USE
MED_REASON_IDX = 2
PATIENT_IDX = 0
MED_CLASS_IDX = 5

CFS_SI_SYMPTOMS =['sore throat', 'lymph', 'pem', 'muscle pain', 
    'joint pain', 'unrefreshing sleep', 'headaches',
    'memory', 'concentration', 'diarrhea', 'fever', 'chills',
    'sleep', 'nausea', 'pain', 'sinus', 'shortness of breath', 
    'light sensitivity', 'depression']

st = LancasterStemmer()

def stemSymptom(word):
    """ Stem a set of words """
    words = word.split(' ')
    words = map(lambda x: st.stem(x), words)
    return ' '.join(words)

STEM_CFS_SI = [stemSymptom(word) for word in CFS_SI_SYMPTOMS]

""" COMMON SYNONYMS (mapping to main categories) """
SYNONYMS = {
    ## common synoyms for concentration
    "fog": "cont", "stay awak": "cont","brain fog":"cont", 
    "ment fog":"cont", "awak": "cont","gen cog":"cont", "gen cog funct":"cont",
    "increas cont":"cont", "daytim sleepy": "cont", "ment foc": "cont",
    "focus":"cont", "foc": "cont", "slow brain":"cont", "clar":"cont",
    ## ADD and ADHD as mental concentration
    "ad":"cont", "adhd":"cont",
    "mem prob":"mem", "short mem":"mem",
    "ach":"pain", "insomn":"sleep", "bp":"blood press",
    "high bp": "hypertend", "high blood press": "hypertend", ## high bp = hypertension
     ## panic attacks = anxiety, relax = anxiety
    "pan attack":"anxy", "anti-anxiety":"anxy", "relax":"anxy",
    ## sinus related things
    "hayfev":"sin", "sin press":"sin", "decongest":"sin", "hay fev":"sin",
    "antidepress":"depress",
    "migrain":"headach", 
    "energy":"fatigu", "energy increas":"fatigu","energ":"fatigu",
    "ic":"blad", ## ic = bladder condition
    "epilepsy":"seiz", ## epilepsy = seizure
    "ur acid buildup":"gout", ## uric acid buildup = gout
    ## various synynoms for cfs
    "cfs proto":"cfs", "myalg encephalomyelit": "cfs", "cfid":"cfs",
    "myalg encephalomyelit (me)": "cfs", "m.e.":"cfs", "me":"cfs",
    "control heavy":"menst", "fibro":"fibromyalg", "fibrom":"fibromyalg",
    "doct":"doct ord", "doct suggest":"doct ord", ## doctor orders
    "not spec":"unknown", "not sur":"unknown", "doesn't know":"unknown",
    "don't rememb":"unknown", "vary reason":"unknown", ## not specified
    "joint flex":"joint", "joint funct":"joint", "joint heal":"joint",
    ## general health
    "good heal":"gen heal", "maint heal":"gen heal", "gen":"gen heal",
    "heal":"gen heal", "gen good heal":"gen heal", 
    "gen wel":"gen heal", "heal benefit":"gen heal",
    }

def subSynonyms(word):
    if SYNONYMS.has_key(word):
        return SYNONYMS[word]
    else:
        return word

""" categorization on pattern matching """
CATEGORY_WORDS = {"joint pain": "joint pain", "kne":"joint pain", 
    "elbow":"joint pain",
    ## muscle pain
    "muscle": "muscle pain", "cramp":"muscle pain", "spasm":"muscle pain",
    ## sore throat
    "sor throat": "sor throat", "throat": "sor throat",
    ## sinus related things
    "sin decongest": "sin", "congest":"sin", "sin infect":"sin", 
    "sinusit":"sin", "allergy":"sin", "sin press":"sin", "sin":"sin",
    "nas":"sin", "allerg":"sin", "rhinit":"sin",
    ## concentration
    "daytim sleepy":"cont", "cognit":"cont", "alert":"cont", "ment clar":"cont",
    "fibro fog":"cont",
    "sleep":"sleep", ## insomnia / sleeping
    ## migraines and headaches
    "migrain":"headach","headach":"headach",
    "nause":"nause", "dizzy":"dizzy",     ## nausea
    "lymph": "lymph", ## lymph nodes
    ## energy / fatigue
    "fatigu":"fatigu", "exhaust": "fatigu", "energy":"fatigu", "exaust":"fatigu",
    "pain":"pain", "ach":"pain", ## general pain
    ## fibromyalgia
    "fibromyalg":"fibromyalg", "cfs":"cfs",
    ## hormone related things
    "hormon":"hormon", "hrt":"hormon", "testosteron":"hormon", "estrog":"hormon",
    "anxy":"anxy", ## anxiety
    ## depression
    "depress":"depress", "bipol":"bipol", "mood":"mood",
    "hypertend":"hypertend", ## hypertension
    "asthm":"asthm", ##asthma
    "diabet":"diabet", ## diabetes
    ## heart / cardiovascular
    "cardiac": "cardiovascul", "cardio-vas":"cardiovascul", "chf":"cardiovascul",
    "cardio":"cardiovascul", "afib":"cardiovascul", "heart":"cardiovascul",
    ## immunity related diseases
    "thyroid":"immun", "hashimoto":"immun", "immun":"immun", "sjorg":"immun",
    "arthrit":"arthrit",
    ## inflamation
    "edem":"inflam","inflam":"inflam",
    "tmj":"joint", ## TMJ = joint issue
    ## digestive system issues
    "reflux":"digest","constip":"digest", "gi":"digest", "bowel":"digest", 
    "stool":"digest","gastro":"digest", "stomach":"digest", "gerd":"digest",
    "digest":"digest", "gut":"digest", "intest":"digest", "motil":"digest",
    "gastrit":"digest", "heartburn":"digest", "colit":"digest", 
    "colon":"digest", "colostom":"digest","probiot":"probiot",
    ## Herpes
    "hhv6":"herp", "herp":"herp", "hhv-6": "herp", "ebv":"herp", 
    "epstein": "herp", "hsv-1":"herp", "hsv1":"herp", "hsv-2":"herp",
    "hsv2":"herp",
    ## lungs
    "copd":"lung", "emphysem":"lung", "emphyzem":"lung", "enphyzem":"lung", 
    "lung":"lung",
    ## movement disorders
    "restless leg":"mov", "rls":"mov", "myoclon":"mov", "trem":"mov", 
    "limb":"mov", "dyskines":"mov",
    ## period, pms, menopaus
    "pms":"menst", "period": "menst","menst":"menst", "menopaus":"menst", 
    "hot flash": "menst","menapaus": "menst",
    ## triglyceride and cholesterol
    "cholesterol":"lipid", "triglycerid":"lipid", "high chol":"lipid",
    "hyperlipidem":"lipid",
    ## blood peressure will go into one
    "blood press":"blood press", "bp":"blood press", "hypotend":"blood press",
    "dry mou": "dry mou", ## dry mouth
    "tinnit":"ear",## ringing of the ears
    "dandruff":"skin", "eczem":"skin", "atop derm":"skin", "actin keratos":"skin",
    "rash":"skin", "psorias":"skin", "skin":"skin", "derm":"skin",## skin conditions 
    "blad":"blad", "urin":"blad", ## bladder conditions
    "brain":"brain", ## brain health
    "liv":"liv", ## liver health
    "mal pattern":"hair", "hair":"hair", ## hair-related things
    "bon":"bon", "osteopen":"bon", "osteoporos":"bone",## bone related disease
    "nerv":"neuro", "neuro":"neuro", ## neurological function
    "fung":"fung", "ringworm":"fung", "yeast":"fung",## fungal infection
    "mitochondr":"mitochondr",
    ## blood disorders
    "fact v leid":"blood disord",
    ## viral supression
    "strep": "strep",
    "fibroid":"fibroid", ## fibroid,
    "ey heal":"vis", "ey swel":"vis", "eyesight":"vis", "glaucom":"vis",
    "night vis":"vis", "night blind":"vis", ## put the ey disorders together
    ## supplements are for deficiency purposes
    "vitamin": "deficy", "deficy":"deficy", "omega":"deficy", "suppl":"deficy",
    "calc":"deficy", "nutrit":"deficy",
    "antioxid":"antioxid",
    "weight":"weight"
    }

def replaceKeyword(symptom):
    for k,v in CATEGORY_WORDS.items():
        if k in symptom:
            return v
    return symptom



medFile = open(filename_input_med_processed_drugs_only, 'rb')
medReader = csv.reader(medFile, delimiter=",")
medReader.next() ## Read the header file

l_orig_sx = []
l_mapped_sx = []
l_num_matched_sx = []
l_unmatched = []
l_unmatched_ratio = []
l_matched = []
l_patients = []
l_meds = []

symptomCounter = Counter()
for row in medReader:
    patient_id = str(row[PATIENT_IDX].strip())
    l_patients.append(patient_id)
    med_class = row[MED_CLASS_IDX].strip().lower()
    l_meds.append(med_class)
    symptom = row[MED_REASON_IDX].strip().lower()
    l_orig_sx.append(symptom)
    if symptom == '':
        continue
    symptom = subSynonyms(symptom)
    ## try to find the closest match
    symptomMatch = difflib.get_close_matches(symptom, STEM_CFS_SI, n=1)
    l_num_matched_sx.append(len(symptomMatch))
    if len(symptomMatch) == 0 or difflib.SequenceMatcher(None, symptom, symptomMatch[0]).ratio() < 0.9:
        l_unmatched.append(symptom)
        if len(symptomMatch) == 0:
            l_unmatched_ratio.append(np.nan)
        else:
            l_unmatched_ratio.append(difflib.SequenceMatcher(None, symptom, symptomMatch[0]).ratio())
        ### here try to do pattern matching
        symptom = replaceKeyword(symptom)
        symptomCounter[symptom] += 1
        l_mapped_sx.append(symptom)
    else:
        l_matched.append(symptom)
        symptomCounter[symptomMatch[0]] += 1
        l_mapped_sx.append(symptomMatch[0])

d_unmatched_counts = Counter(l_unmatched)
l_unmatched_counts = [d_unmatched_counts[x] for x in l_unmatched]

df_all_patient_matched_reason_med = pd.DataFrame([])
df_all_patient_matched_reason_med['PATIENT'] = l_patients
df_all_patient_matched_reason_med['REASON_ORIG'] = l_orig_sx
df_all_patient_matched_reason_med['REASON_MAPPED'] = l_mapped_sx
df_all_patient_matched_reason_med['MED'] = l_meds
df_all_patient_matched_reason_med.to_csv(filename_output_patient_matchedReason_med , index = None, header = False)

df_unmatched = pd.DataFrame([])
df_unmatched['UNMATCHED_SX_NAME'] = l_unmatched
df_unmatched['RATIO'] = l_unmatched_ratio
df_unmatched['COUNT'] = l_unmatched_counts
df_unmatched.to_csv('df_unmatched_SX_NAME_COUNT.csv', header = True, index = None)
df_unmatched_unique = pd.DataFrame([])
df_unmatched_unique['UMATCHED_SX_NAME'] = list(np.unique(l_unmatched))
df_unmatched_unique['COUNT'] = [d_unmatched_counts[x] for x in  list(np.unique(l_unmatched))]
df_unmatched_unique = df_unmatched_unique.sort_values(by=['COUNT'], ascending=False)
df_unmatched_unique.to_csv(filename_output_unmatched_reason_count, header = False, index = None)

with open('symptom_count.txt', 'wb') as outfile:
    symptomWriter = csv.writer(outfile, delimiter="\t")
    for k, v in symptomCounter.items():
        symptomWriter.writerow([k, v])
medFile.close()

df_matched_symptom_count = pd.read_csv('symptom_count.txt', header = None, delimiter='\t')
df_matched_symptom_count = df_matched_symptom_count.sort_values(by=[1], ascending=False)
df_matched_symptom_count.to_csv(filename_output_matched_reason_count , index = None, header = False)

print(pprint.pformat(dict(symptomCounter)))
print len(symptomCounter)
