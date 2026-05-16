import csv
import json
import os
import subprocess


def _ensure_folder(folder_path):
    os.makedirs(folder_path, exist_ok=True)


def _repository_name_from_path(repo_path):
    return os.path.basename(repo_path.rstrip(os.sep))


def _run_radon_cc(repo_path):
    try:
        output = subprocess.check_output(
            ['radon', 'cc', '-j', repo_path],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except FileNotFoundError:
        raise RuntimeError('Radon CLI is not installed. Install it with `pip install radon`.')
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f'Radon command failed:\n{exc.output}') from exc

    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError('Could not parse radon JSON output.') from exc


def _write_radon_json(radon_data, target_folder, repo_name):
    safe_name = f'radon_output_{repo_name}.json'
    json_path = os.path.join(target_folder, safe_name)
    with open(json_path, 'w', encoding='utf-8') as file:
        json.dump({repo_name: radon_data}, file, indent=4)
    return json_path


def _write_radon_csv(radon_data, target_folder, repo_name):
    safe_name = f'radon_output_{repo_name}.csv'
    csv_path = os.path.join(target_folder, safe_name)
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Repository', 'File Name', 'Type', 'Name', 'Line', 'Complexity', 'Rank'])
        for file_name, entries in radon_data.items():
            base_name = os.path.basename(file_name)
            for entry in entries:
                writer.writerow([
                    repo_name,
                    base_name,
                    entry.get('type', ''),
                    entry.get('name', ''),
                    entry.get('lineno', ''),
                    entry.get('complexity', ''),
                    entry.get('rank', ''),
                ])
    return csv_path


def generate(repo_path, target_folder):
    """Generate a Radon complexity report in JSON and CSV formats."""
    # Allow passing a list of repo paths (for user option)
    if not repo_path:
        print('Radon generation skipped: repo_path is empty.')
        return

    # If a list/tuple is passed, iterate
    if isinstance(repo_path, (list, tuple)):
        for path in repo_path:
            generate(path, target_folder)
        return

    # Single path
    if not os.path.isdir(repo_path):
        print(f'Radon generation skipped: source path does not exist: {repo_path}')
        return

    _ensure_folder(target_folder)
    repo_name = _repository_name_from_path(repo_path)
    radon_data = _run_radon_cc(repo_path)
    json_path = _write_radon_json(radon_data, target_folder, repo_name)
    csv_path = _write_radon_csv(radon_data, target_folder, repo_name)

    print('Saved radon JSON to', json_path)
    print('Saved radon CSV to', csv_path)


if __name__ == '__main__':
    print('This module provides `generate(repo_path, target_folder)` for radon output generation.')
