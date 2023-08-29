from datetime import datetime, timedelta
import requests
import gzip
import json

def get_data():

    url = "https://production-media.paperswithcode.com/about/evaluation-tables.json.gz"
    response = requests.get(url)

    # Decompress the gzipped content
    decompressed_content = gzip.decompress(response.content)

    # Parse the JSON content
    data = json.loads(decompressed_content)

    return data


def process_data(data):
    processed_data = {}

    for dataset, details in data.items():
        processed_papers = {}
        dataset_links = details.get('dataset_links', [])
        task = details.get('task', '')
        subtask_description = details.get('subtask_description', '')
        papers = details['sota_rows']

        # Filter out papers without a date and sort the remaining by date
        valid_papers = [paper for paper in papers if paper['paper_date'] is not None]
        for paper in sorted(valid_papers, key=lambda p: datetime.strptime(p['paper_date'], "%Y-%m-%d")):
            date = paper['paper_date']
            metrics = paper.get('metrics', {})

            for metric_name, metric_value in metrics.items():
                if metric_name not in processed_papers:
                    processed_papers[metric_name] = {}

                if date not in processed_papers[metric_name] or processed_papers[metric_name][date]['value'] < metric_value:
                    processed_papers[metric_name][date] = {
                        'value': metric_value,
                        'paper_title': paper['paper_title'],
                        'paper_url': paper['paper_url'],
                    }

        processed_data[dataset] = {
            'sota_rows': processed_papers,
            'dataset_links': dataset_links,
            'task': task,
            'subtask_description': subtask_description
        }

    return processed_data

def document_schema(data, path="", result=None):

    from collections import defaultdict

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

def process_subtask(subtask, results):
    if 'datasets' in subtask:
        for dataset in subtask['datasets']:
            dataset_name = dataset['dataset']
            sota_rows = dataset.get('sota', {}).get('rows', [])
            dataset_links = dataset.get('dataset_links', [])
            task = subtask.get('task', '')
            subtask_description = subtask.get('description', '')
            
            results[dataset_name] = {
                'sota_rows': sota_rows,
                'dataset_links': dataset_links,
                'task': task,
                'subtask_description': subtask_description
            }

    if 'subtasks' in subtask:
        for child_subtask in subtask['subtasks']:
            process_subtask(child_subtask, results)

def process_json(data):
    results = {}
    for task in data:
        for subtask in task['subtasks']:
            process_subtask(subtask, results)
    return results