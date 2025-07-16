import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import argparse
import numpy as np

sns.set(style="whitegrid")

def load_data(csv_path, metric, categories, machines, versions, benchmarks):
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=[metric])

    if categories:
        df = df[df["category"].str.lower().apply(lambda x: any(cat in x for cat in categories))]
    if machines:
        df = df[df["machine"].isin(machines)]
    if versions:
        df = df[df["version"].isin(versions)]
    if benchmarks:
        df = df[df["benchmark"].str.lower().apply(lambda x: any(b in x for b in benchmarks))]

    print(f"📊 Filtrado final: {len(df)} filas.")
    return df

def filter_data(df, fuse):
    if fuse:
        df = df.copy()
        df["machine"] = "ALL"
    return df

def remove_outliers(df, metric):
    print(f"🔍 Eliminando outliers en '{metric}'...")
    def iqr_filter(group):
        q1 = group[metric].quantile(0.25)
        q3 = group[metric].quantile(0.75)
        iqr = q3 - q1
        mask = (group[metric] >= q1 - 1.5 * iqr) & (group[metric] <= q3 + 1.5 * iqr)
        removed = (~mask).sum()
        if removed > 0:
            print(f"  • {group['benchmark'].iloc[0]} ({group['version'].iloc[0]}): {removed} outliers removidos")
        return group[mask]

    return df.groupby(["benchmark", "version"], group_keys=False).apply(iqr_filter)

def generate_summary_table(df, metric, outpath):
    summary = df.groupby(["benchmark", "version"])[metric].agg(['mean', 'std', 'count']).reset_index()
    summary.to_csv(outpath, index=False)
    print(f"✅ Tabla resumen guardada en: {outpath}")

def plot_boxplots(df, metric, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for bench in df["benchmark"].unique():
        sub = df[df["benchmark"] == bench]
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=sub, x="version", y=metric, hue="machine")
        plt.title(f"{bench} — {metric}")
        plt.xticks(rotation=45)
        plt.tight_layout()
        safe_name = bench.replace("/", "_").replace(" ", "_")
        plt.savefig(os.path.join(output_dir, f"{safe_name}_{metric}_boxplot.png"))
        plt.close()

def plot_violinplots(df, metric, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for bench in df["benchmark"].unique():
        sub = df[df["benchmark"] == bench]
        plt.figure(figsize=(10, 6))
        sns.violinplot(data=sub, x="version", y=metric, hue="machine", split=False)
        plt.title(f"{bench} — {metric}")
        plt.xticks(rotation=45)
        plt.tight_layout()
        safe_name = bench.replace("/", "_").replace(" ", "_")
        plt.savefig(os.path.join(output_dir, f"{safe_name}_{metric}_violinplot.png"))
        plt.close()

def plot_heatmap(df, metric, output_file):
    pivot = df.groupby(["benchmark", "version"])[metric].mean().unstack()
    plt.figure(figsize=(12, max(6, len(pivot) * 0.2)))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="coolwarm", cbar_kws={"label": metric})
    plt.title(f"Benchmark Mean {metric} by Version")
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

def main(args):
    categories = [c.strip().lower() for c in args.categories.split(",")] if args.categories else None
    machines = [m.strip() for m in args.machines.split(",")] if args.machines else None
    versions = [v.strip() for v in args.versions.split(",")] if args.versions else None
    benchmarks = [b.strip().lower() for b in args.benchmarks.split(",")] if args.benchmarks else None

    df = load_data(args.csv, args.metric, categories, machines, versions, benchmarks)
    if df.empty:
        print("⚠️ No se encontraron datos tras el filtrado.")
        return

    df = filter_data(df, args.fuse)
    tag = "fused" if args.fuse else "by_machine"
    out_base = f"plots_{args.metric}_{tag}"

    if args.summary_table:
        generate_summary_table(df, args.metric, f"{out_base}_summary.csv")

    if args.remove_outliers:
        df = remove_outliers(df, args.metric)

    plot_boxplots(df, args.metric, os.path.join(out_base, "boxplots"))
    plot_violinplots(df, args.metric, os.path.join(out_base, "violins"))
    plot_heatmap(df, args.metric, os.path.join(out_base, f"heatmap_{args.metric}.png"))
    print(f"✅ Gráficas generadas en: {out_base}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Godot benchmark visualization with advanced filters.")
    parser.add_argument("--csv", default="benchmark_results.csv", help="Path to the benchmark CSV")
    parser.add_argument("--metric", default="time", help="Metric to visualize")
    parser.add_argument("--fuse", action="store_true", help="Fuse all machines into one group")

    # NUEVAS OPCIONES
    parser.add_argument("--categories", help="Comma-separated list of category substrings")
    parser.add_argument("--machines", help="Comma-separated list of machine names to include")
    parser.add_argument("--versions", help="Comma-separated list of engine versions to include")
    parser.add_argument("--benchmarks", help="Comma-separated list of benchmark name substrings")

    parser.add_argument("--summary-table", action="store_true", help="Export summary table (mean, std, count)")
    parser.add_argument("--remove-outliers", action="store_true", help="Remove outliers based on metric values")

    args = parser.parse_args()
    main(args)
