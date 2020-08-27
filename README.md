# Natural language processing based medication extraction from unstructured public health data

Authors: `<Masked while publication is in review>`

This repository contains code for the paper `<Publication information masked while in review>`.

## Summary

We have developed a natural language processing (NLP)-based method for automatically extracting and classifying medications and reasons they are taken, from unstructured text sources. We demonstrated the usage on unstructured public health data, as described in our publication `<Publication information masked while in review>`.

## Data Source

Generally speaking, input data that contain unstructured information related to medication names and reasons they are taken.

Data for medications and reasons should be input in CSV format. For example, see below.

```
patient_id, medication, reason_for_taking_medication
XYZ1, "metoprolol", "high blood pressure"
XYZ1, "metoperlol", "hypertension"
XYZ2, "aspirin", "muscle pain"
XYZ2, "ASX", "cardiovascular disease prevention"
XYZ2, "ciprofloxacin", "bladder infection"
XYZ3, "ibuprofen", "head ache"
```

We have included sample data in the files `<filenmaes masked>`.

## How to run

We describe below a tutorial for executing the medication extraction code using sample raw data. 


### Step 1 

```
cd data-preprocess
python extract-med-count.py raw_data.csv 1 extract_med_count_OUTPUT.json
```

### Step 2
```
python create-med-dict-file.py extract_med_count_OUTPUT.csv create_med_dict_file_OUTPUT.json
```

### Step 3
```
python preprocessMedFile.py
```

### Step 4
```
python buildSymptomDict_and_mapReasons.py med_processed_with_categories.csv df_all_patient_matched_reason_med.csv df_matched_reason_count.csv df_unmatched_reason_count.csv
```


### Mapped medications and reasons

Found in the file:

```
df_all_patient_matched_reason_med.csv
```

Columns include:

- patient
- reason
- reason stem
- drug category

```
XYZ1,seizure,seizure,antidepressants
XYZ1,blood thinner,blood thinner,unknown
XYZ1,depression,depress,unknown
XYZ1,hyperthyroidism,immun,thyroid drugs
XYZ2,back pain,pain,analgesics
XYZ2,acid reflux,digest,proton pump inhibitors
XYZ2,urinary urgency,blad,urinary antispasmodics
XYZ2,to quit smoking,to quit smoking,smoking cessation agents
```
