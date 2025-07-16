import argparse
import os
import json
import pandas as pd
import re

def extract_info_from_path(file_path):
    parts = file_path.split(os.sep)
    machine = parts[-3]
    version = parts[-2]
    filename = os.path.basename(file_path)
    iter_match = re.search(r'iter(\d+)', filename)
    iteration = int(iter_match.group(1)) if iter_match else None
    return machine, version, iteration

def load_benchmark_file(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    results = []
    for bench in data.get("benchmarks", []):
        entry = {
            "category": bench.get("category"),
            "benchmark": bench.get("name"),
            "render_cpu": bench["results"].get("render_cpu"),
            "render_gpu": bench["results"].get("render_gpu"),
            "time": bench["results"].get("time"),
            "idle": bench["results"].get("idle"),
            "physics": bench["results"].get("physics"),
        }
        results.append(entry)
    return results

def collect_all_benchmarks(root_path):
    all_data = []

    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            if filename.startswith("results_") and filename.endswith(".json"):
                filepath = os.path.join(dirpath, filename)
                machine, version, iteration = extract_info_from_path(filepath)
                try:
                    benchmarks = load_benchmark_file(filepath)
                    for bench in benchmarks:
                        bench["machine"] = machine
                        bench["version"] = version
                        bench["iteration"] = iteration
                        all_data.append(bench)
                except Exception as e:
                    print(f"Error al leer {filepath}: {e}")

    df = pd.DataFrame(all_data)

    if not df.empty:
        counts = df.groupby("version")["benchmark"].nunique()
        print("Número de benchmarks únicos por versión:")
        print(counts)

    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parsea los archivos JSON de resultados de godot-benchmarks y genera un CSV unificado.")
    parser.add_argument("--root", required=True, help="Directorio raíz que contiene los resultados JSON de los benchmarks")
    args = parser.parse_args()

    df = collect_all_benchmarks(args.root)
    print(f"{len(df)} filas cargadas.")

    output_dir = os.path.join(args.root, "ANALYSIS")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "parsed_results_data.csv")
    df.to_csv(output_path, index=False)
    print(f"Archivo exportado a {output_path}")
