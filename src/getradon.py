import csv
import json
import os
import subprocess


def ensure_folder(folder_path):
    os.makedirs(folder_path, exist_ok=True)


def repository_name_from_path(repo_path):
    return os.path.basename(repo_path.rstrip(os.sep))


def run_radon_cc(repo_path):
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore::SyntaxWarning"

    try:
        result = subprocess.run(
            ["radon", "cc", "-j", repo_path],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "Radon CLI is not installed. Install it with `pip install radon`."
        )

    if result.returncode != 0:
        raise RuntimeError(
            "Radon command failed:\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Could not parse Radon JSON output.\n\n"
            f"STDOUT first 500 chars:\n{result.stdout[:500]}\n\n"
            f"STDERR first 500 chars:\n{result.stderr[:500]}"
        ) from exc


def write_radon_json(radon_data, target_folder, repo_name):
    safe_name = f"radon_output_{repo_name}.json"
    json_path = os.path.join(target_folder, safe_name)

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump({repo_name: radon_data}, file, indent=4, ensure_ascii=False)

    return json_path

def write_radon_csv(radon_data, target_folder, repo_name):
    safe_name = f"radon_output_{repo_name}.csv"
    csv_path = os.path.join(target_folder, safe_name)

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow([
            "Repository",
            "File Name",
            "Type",
            "Name",
            "Line",
            "End Line",
            "Complexity",
            "Rank",
            "Parent",
            "Error"
        ])

        def write_entry(file_name, entry, parent=""):
            """
            Escribe una entrada de Radon en CSV.
            Soporta funciones normales, clases, métodos, errores y closures.
            """

            # Caso raro: Radon devuelve algo que no es dict
            if not isinstance(entry, dict):
                writer.writerow([
                    repo_name,
                    os.path.basename(str(file_name)),
                    "unknown",
                    "",
                    "",
                    "",
                    "",
                    "",
                    parent,
                    str(entry)
                ])
                return

            # Caso error de Radon en un archivo concreto
            if "error" in entry:
                writer.writerow([
                    repo_name,
                    os.path.basename(str(file_name)),
                    "error",
                    "",
                    "",
                    "",
                    "",
                    "",
                    parent,
                    entry.get("error", "")
                ])
                return

            # Caso normal: función, método o clase
            writer.writerow([
                repo_name,
                os.path.basename(str(file_name)),
                entry.get("type", ""),
                entry.get("name", ""),
                entry.get("lineno", ""),
                entry.get("endline", ""),
                entry.get("complexity", ""),
                entry.get("rank", ""),
                parent,
                ""
            ])

            # Funciones internas
            closures = entry.get("closures", [])

            if isinstance(closures, list):
                for closure in closures:
                    write_entry(
                        file_name=file_name,
                        entry=closure,
                        parent=entry.get("name", "")
                    )

        for file_name, entries in radon_data.items():

            # Caso normal:
            # "archivo.py": [ {...}, {...} ]
            if isinstance(entries, list):
                for entry in entries:
                    write_entry(file_name, entry)

            # Caso posible:
            # "archivo.py": {"error": "..."}
            elif isinstance(entries, dict):
                write_entry(file_name, entries)

            # Caso raro:
            # "archivo.py": "texto"
            else:
                writer.writerow([
                    repo_name,
                    os.path.basename(str(file_name)),
                    "unknown",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    str(entries)
                ])

    return csv_path

def generate_radon(repo_path, target_folder):
    """Generate a Radon complexity report in JSON and CSV formats."""
    if not repo_path:
        print('Radon generation skipped: repo_path is empty.')
        return

    # Single path
    if not os.path.isdir(repo_path):
        print(f'Radon generation skipped: source path does not exist: {repo_path}')
        return

    ensure_folder(target_folder)
    repo_name = repository_name_from_path(repo_path)
    radon_data = run_radon_cc(repo_path)
    json_path = write_radon_json(radon_data, target_folder, repo_name)
    csv_path = write_radon_csv(radon_data, target_folder, repo_name)


