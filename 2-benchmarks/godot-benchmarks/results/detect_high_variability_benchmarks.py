import pandas as pd
import argparse

def remove_outliers(df, metric):
    def iqr_filter(group):
        q1 = group[metric].quantile(0.25)
        q3 = group[metric].quantile(0.75)
        iqr = q3 - q1
        mask = (group[metric] >= q1 - 1.5 * iqr) & (group[metric] <= q3 + 1.5 * iqr)
        return group[mask]

    return df.groupby(["benchmark", "version"], group_keys=False).apply(iqr_filter)

def apply_filters(df, args):
    if args.categories:
        cats = [c.strip().lower() for c in args.categories.split(",")]
        df = df[df["category"].str.lower().apply(lambda x: any(cat in x for cat in cats))]
    if args.machines:
        machines = [m.strip() for m in args.machines.split(",")]
        df = df[df["machine"].isin(machines)]
    if args.versions:
        versions = [v.strip() for v in args.versions.split(",")]
        df = df[df["version"].isin(versions)]
    if args.benchmarks:
        names = [b.strip().lower() for b in args.benchmarks.split(",")]
        df = df[df["benchmark"].str.lower().apply(lambda x: any(n in x for n in names))]

    if args.remove_outliers:
        df = remove_outliers(df, args.metric)

    if args.fuse:
        df = df.copy()
        df["machine"] = "ALL"

    return df

def compute_variability(df, metric):
    grouped = df.groupby(["benchmark", "version"])[metric].mean().reset_index()
    pivot = grouped.pivot(index="benchmark", columns="version", values=metric)
    means = pivot.mean(axis=1)
    abs_var = pivot.var(axis=1, ddof=0)
    rel_var = abs_var / (means ** 2)
    
    result = pd.DataFrame({
        "benchmark": abs_var.index,
        "variance": abs_var.values,
        "relative_variance": rel_var.values
    }).sort_values(by="relative_variance", ascending=False).reset_index(drop=True)
    
    return result


def main(args):
    df = pd.read_csv(args.csv).dropna(subset=[args.metric])
    df = apply_filters(df, args)

    if df.empty:
        print("⚠️ No quedan datos tras aplicar los filtros.")
        return

    result = compute_variability(df, args.metric)

    # ordenar por la métrica seleccionada
    sort_col = "relative_variance" if args.relative else "variance"
    result = result.sort_values(by=sort_col, ascending=False).reset_index(drop=True)

    print(f"📊 Top {args.top} benchmarks con mayor variabilidad en '{args.metric}' "
          f"(ordenado por {'relativa' if args.relative else 'absoluta'}):")
    print(result.head(args.top).to_string(index=False))


    outname = f"variability_{args.metric}.csv"
    result.to_csv(outname, index=False)
    print(f"✅ Resultado exportado a {outname}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect benchmarks with high variability between engine versions.")
    parser.add_argument("--csv", default="benchmark_results.csv", help="Path to the benchmark CSV")
    parser.add_argument("--metric", default="time", help="Metric to analyze (e.g. time, render_cpu)")
    parser.add_argument("--top", type=int, default=10, help="Top N most variable benchmarks")
    parser.add_argument("--relative", action="store_true", help="Sort by relative variance instead of absolute")

    # Filtros compartidos con el script de plots
    parser.add_argument("--categories", help="Comma-separated list of category substrings")
    parser.add_argument("--machines", help="Comma-separated list of machine names")
    parser.add_argument("--versions", help="Comma-separated list of engine versions")
    parser.add_argument("--benchmarks", help="Comma-separated list of benchmark name substrings")

    parser.add_argument("--remove-outliers", action="store_true", help="Remove outliers based on IQR")
    parser.add_argument("--fuse", action="store_true", help="Fuse all machines into one group")

    args = parser.parse_args()
    main(args)
