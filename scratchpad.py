import requests
import gzip
import json

url = "https://production-media.paperswithcode.com/about/evaluation-tables.json.gz"
response = requests.get(url)

# Decompress the gzipped content
decompressed_content = gzip.decompress(response.content)

# Parse the JSON content
data = json.loads(decompressed_content)

from collections import defaultdict

def document_schema(data, path="", result=None):
    if result is None:
        result = defaultdict(set)

    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}/{key}" if path else key
            if isinstance(value, (list, dict)):
                document_schema(value, new_path, result)
            else:
                result[new_path].add(value)
    elif isinstance(data, list):
        for item in data:
            document_schema(item, path, result)

    return result

def summarize_schema(schema):
    summary = {}
    for key, values in schema.items():
        cleaned_key = "/".join([part.split("[")[0] for part in key.split("/")])
        summary[cleaned_key] = list(values)
    return summary

schema = document_schema(data)
summary = summarize_schema(schema)
for key, values in summary.items():
    print(f"{key}: {values}")

def process_subtask(subtask, results):
    if 'datasets' in subtask:
        for dataset in subtask['datasets']:
            dataset_name = dataset['dataset']
            sota_rows = dataset['sota']['rows'] if 'sota' in dataset else []
            results[dataset_name] = sota_rows

    # Process any sub-subtasks
    if 'subtasks' in subtask:
        for child_subtask in subtask['subtasks']:
            process_subtask(child_subtask, results)

def process_json(data):
    results = {}
    for task in data:
        for subtask in task['subtasks']:
            process_subtask(subtask, results)
    return results

results = process_json(data)