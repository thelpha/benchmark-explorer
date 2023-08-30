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

def get_most_recent_extreme_date(papers):
    if not papers:
        return datetime.min
    papers = [{'date': datetime.strptime(p['date'], '%Y-%m-%d'), 'value': float(p['value'])} for p in papers]
    max_date = max(p['date'] for p in papers if p['value'] == max(p['value'] for p in papers))
    min_date = max(p['date'] for p in papers if p['value'] == min(p['value'] for p in papers))
    return max(max_date, min_date)


def process_data(data):
    data_dict = {}

    for dataset, details in data.items():

        dataset_links = details.get('dataset_links',[])[0]
        task = details.get('task', '')
        subtask_description = details.get('subtask_description', '')
        papers = details['sota_rows']

        data_dict[dataset] = {
            'dataset_links': dataset_links,
            'task': task,
            'subtask_description': subtask_description
        }

        # Filter out papers without a date and sort the remaining by date
        valid_papers = [paper for paper in papers if paper['paper_date'] is not None]
        for paper in sorted(valid_papers, key=lambda p: datetime.strptime(p['paper_date'], "%Y-%m-%d")):
            date = paper['paper_date']
            metrics = paper.get('metrics', {})
        
            # Add each metric to the corresponding paper list at the level of data_dict[dataset][metric_name]

            for metric_name, metric_value in metrics.items():
                #Confirm that metric has a numeric value
                try:
                    metric_value = float(metric_value)

                    data_dict[dataset].setdefault(metric_name, []).append({
                            'date': date,
                            'value': metric_value,
                            'paper_title': paper['paper_title'],
                            'paper_url': paper['paper_url'],
                            'model_name': paper['model_name'],
                    })
                
                except ValueError:
                    continue
        
    data_list = []

    for dataset, data in data_dict.items():
        attributes = {k: v for k, v in data.items() if not isinstance(v, list)}
        for metric, metric_list in data.items():
            if isinstance(metric_list, list):
                new_entry = {'dataset': dataset, 'metric': metric, 'papers':metric_list, **attributes}
                if len(new_entry['papers']) >= 3: #Limit to datasets with at least 3 papers
                    data_list.append(new_entry)

    return data_dict, sorted(data_list, key=lambda x: get_most_recent_extreme_date(x['papers']), reverse=True)

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