import os
import json
import pandas as pd
import re
from tqdm import tqdm

def extract_info_from_path(file_path):
    parts = file_path.split(os.sep)
    machine = parts[-3]  # e.g. minisforum1
    version = parts[-2]  # e.g. O3
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
                    print(f"⚠️ Error leyendo {filepath}: {e}")

    df = pd.DataFrame(all_data)
    return df

if __name__ == "__main__":
    root_dir = "/Users/carlos/Documents/TFM/BASE_BINARIES_RESULTS/2025-06-25"
    df = collect_all_benchmarks(root_dir)
    print(f"{len(df)} filas cargadas.")
    df.to_csv("benchmark_results.csv", index=False)
    print("✅ Datos exportados a benchmark_results.csv")
