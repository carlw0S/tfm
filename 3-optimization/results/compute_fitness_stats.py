import argparse
import json
from pathlib import Path

def load_stats(path: Path) -> dict:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        stats = json.load(f)
    return stats

def compute_individual_times(stats: dict, step: str) -> float:
    time_values = [indiv[step]["duration"] for indiv in stats.values() if indiv[step]["success"]]
    min_time = min(time_values) if time_values else 0.0
    max_time = max(time_values) if time_values else 0.0
    avg_time = sum(time_values) / len(time_values) if time_values else 0.0
    stddev_time = (sum((x - avg_time) ** 2 for x in time_values) / len(time_values)) ** 0.5 if time_values else 0.0
    return min_time, max_time, avg_time, stddev_time

def compute_total_times(stats: dict) -> float:
    total_times = [
        indiv["opt"]["duration"] + indiv["clang"]["duration"] + indiv["benchmark"]["duration"]
        for indiv in stats.values() if indiv["opt"]["success"] and indiv["clang"]["success"] and indiv["benchmark"]["success"]
    ]
    min_time = min(total_times) if total_times else 0.0
    max_time = max(total_times) if total_times else 0.0
    avg_time = sum(total_times) / len(total_times) if total_times else 0.0
    stddev_time = (sum((x - avg_time) ** 2 for x in total_times) / len(total_times)) ** 0.5 if total_times else 0.0
    return min_time, max_time, avg_time, stddev_time

def count_unsuccessful(stats: dict, step: str) -> int:
    return sum(1 for indiv in stats.values() if not indiv[step]["success"])

def main() -> None:
    p = argparse.ArgumentParser(
        description="Graficar la evolución del fitness a partir de logs de GA o SA (detección automática)."
    )
    p.add_argument("log", type=Path, help="Ruta al archivo fitness_stats.txt")
    args = p.parse_args()

    stats = load_stats(args.log)
    opt_min_time, opt_max_time, opt_avg_time, opt_stddev_time = compute_individual_times(stats, "opt")
    clang_min_time, clang_max_time, clang_avg_time, clang_stddev_time = compute_individual_times(stats, "clang")
    benchmark_min_time, benchmark_max_time, benchmark_avg_time, benchmark_stddev_time = compute_individual_times(stats, "benchmark")

    print("opt:")
    print(f"\tTiempo mínimo: {opt_min_time:.2f} s")
    print(f"\tTiempo máximo: {opt_max_time:.2f} s")
    print(f"\tTiempo promedio: {opt_avg_time:.2f} s")
    print(f"\tDesviación estándar: {opt_stddev_time:.2f} s")
    print()

    print("clang:")
    print(f"\tTiempo mínimo: {clang_min_time:.2f} s")
    print(f"\tTiempo máximo: {clang_max_time:.2f} s")
    print(f"\tTiempo promedio: {clang_avg_time:.2f} s")
    print(f"\tDesviación estándar: {clang_stddev_time:.2f} s")
    print()

    print("benchmark:")
    print(f"\tTiempo mínimo: {benchmark_min_time:.2f} s")
    print(f"\tTiempo máximo: {benchmark_max_time:.2f} s")
    print(f"\tTiempo promedio: {benchmark_avg_time:.2f} s")
    print(f"\tDesviación estándar: {benchmark_stddev_time:.2f} s")
    print()

    print(f"Tiempo total mínimo (hipotético, mejores tiempos permitiendo individuos distintos): {opt_min_time + clang_min_time + benchmark_min_time:.2f} s")
    print(f"Tiempo total máximo (hipotético, peores tiempos permitiendo individuos distintos): {opt_max_time + clang_max_time + benchmark_max_time:.2f} s")
    print()

    min_total_time, max_total_time, avg_total_time, stddev_time = compute_total_times(stats)
    print(f"Mejor tiempo total (mejor individuo): {min_total_time:.2f} s")
    print(f"Peor tiempo total (peor individuo): {max_total_time:.2f} s")
    print(f"Tiempo total promedio: {avg_total_time:.2f} s")
    print(f"Desviación estándar del tiempo total: {stddev_time:.2f} s")
    print()

    opt_failures = count_unsuccessful(stats, "opt")
    clang_failures = count_unsuccessful(stats, "clang")
    benchmark_failures = count_unsuccessful(stats, "benchmark")
    print(f"Fases de opt fallidas: {opt_failures}")
    print(f"Fases de clang fallidas (incluye los fallos de opt): {clang_failures}")
    print(f"Fases de benchmark fallidas (incluye los fallos de opt y clang): {benchmark_failures}")

if __name__ == "__main__":
    main()
