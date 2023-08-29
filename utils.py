from datetime import datetime, timedelta
import requests
import gzip
import json
from collections import defaultdict

def get_data(url = "https://production-media.paperswithcode.com/about/evaluation-tables.json.gz"):
    response = requests.get(url)
    return json.loads(gzip.decompress(response.content))

def process_papers(papers):
    """
    Process a list of papers to aggregate metric values.
    Also counts how many recent papers have contributed to each metric.
    """
    processed = defaultdict(dict)
    recent_counts = {}
    valid_papers = [p for p in papers if p['paper_date']]

    for paper in sorted(valid_papers, key=lambda p: p['paper_date']):
        date = paper['paper_date']
        is_recent = datetime.strptime(date, "%Y-%m-%d") > (datetime.now() - timedelta(days=365))
        
        for metric, value in paper['metrics'].items():
            if is_recent:
                recent_counts[metric] = recent_counts.get(metric, 0) + 1

            # Update metric only if new value is greater
            if date not in processed[metric] or processed[metric][date]['value'] < value:
                processed[metric][date] = {'value': value, 'paper_title': paper['paper_title'], 'paper_url': paper['paper_url']}

    return processed, recent_counts

def process_data(data):
    """Process the raw data to compile a summary of SOTA metrics by dataset."""
    processed_data = {}
    
    for dataset, details in data.items():
        dataset_info = {
            'dataset_links': details.get('dataset_links', []),
            'task': details.get('task', ''),
            'subtask_description': details.get('subtask_description', '')
        }
        
        processed_papers, recent_counts = process_papers(details['sota_rows'])
        
        # Only include metrics with 5 or more recent papers
        for metric, count in recent_counts.items():
            if count >= 5 and metric in processed_papers:
                if dataset not in processed_data:
                    processed_data[dataset] = dataset_info
                processed_data[dataset].setdefault('sota_rows', {})[metric] = processed_papers[metric]
                
    return processed_data

def document_schema(data, path="", result=None):
    """Recursively document the schema of nested dictionaries and lists."""
    if result is None:
        result = defaultdict(set)
        
    if isinstance(data, dict):
        for key, value in data.items():
            document_schema(value, f"{path}/{key}" if path else key, result)
    elif isinstance(data, list):
        for item in data:
            document_schema(item, path, result)
    else:
        result[path].add(type(data).__name__)
        
    return result

def summarize_schema(schema):
    """Summarize schema by removing list indices and consolidating types."""
    return {"/".join([part.split("[")[0] for part in key.split("/")]): list(values) for key, values in schema.items()}

def process_subtask(subtask, results):
    """Recursively process subtasks and their datasets to populate results."""
    for dataset in subtask.get('datasets', []):
        results[dataset['dataset']] = {
            'sota_rows': dataset.get('sota', {}).get('rows', []),
            'dataset_links': dataset.get('dataset_links', []),
            'task': subtask.get('task', ''),
            'subtask_description': subtask.get('description', '')
        }
    for child in subtask.get('subtasks', []):
        process_subtask(child, results)

def process_json(data):
    """Process the root level of the JSON data."""
    results = {}
    for task in data:
        for subtask in task['subtasks']:
            process_subtask(subtask, results)
    return results
