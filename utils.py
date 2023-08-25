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

    for dataset_info in data['datasets']:
        dataset = dataset_info['dataset']
        dataset_link = dataset_info['dataset_links'][0]['url'] if dataset_info['dataset_links'] else None
        papers = dataset_info['sota']['rows']
        
        processed_papers = {}
        subtask_metric_recent_counts = {} # Counting recent papers within the last year

        valid_papers = [paper for paper in papers if paper['paper_date'] is not None]

        for paper in sorted(valid_papers, key=lambda p: p['paper_date']):
            date = paper['paper_date']
            metrics = paper['metrics']
            recent_date = date is not None and datetime.strptime(date, "%Y-%m-%d") > (datetime.now() - timedelta(days=365))

            for metric_name, metric_value in metrics.items():
                subtask_metric_key = (dataset, metric_name)
                if recent_date:
                    subtask_metric_recent_counts[subtask_metric_key] = subtask_metric_recent_counts.get(subtask_metric_key, 0) + 1

                if metric_name not in processed_papers:
                    processed_papers[metric_name] = {}

                # Store the maximum value for the date and attach the paper information
                if date not in processed_papers[metric_name] or processed_papers[metric_name][date]['value'] < metric_value:
                    processed_papers[metric_name][date] = {
                        'value': metric_value,
                        'paper_title': paper['paper_title'],
                        'paper_url': paper['paper_url'],
                    }

        # Filtering out subtask-metric combinations without recent papers
        for subtask_metric_key, count in subtask_metric_recent_counts.items():
            if count >= 5:
                _, metric_name = subtask_metric_key
                if metric_name in processed_papers:
                    if dataset not in processed_data:
                        processed_data[dataset] = {'dataset_link': dataset_link, 'metrics': {}}
                    processed_data[dataset]['metrics'][metric_name] = processed_papers[metric_name]

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
