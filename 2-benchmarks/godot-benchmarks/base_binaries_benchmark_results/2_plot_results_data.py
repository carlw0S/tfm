import os
import argparse
import json
import logging

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

sns.set_theme(style="whitegrid")

# Constante global de estadísticas válidas
AVAILABLE_STATS = ["time", "render_cpu", "render_gpu", "idle", "physics"]

def validate_args(args):
    # Verifica existencia del CSV
    if not os.path.isfile(args.csv):
        logging.error(f"El archivo CSV no existe: {args.csv}")
        exit(1)
    # Verifica estadística válida
    if args.statistic not in AVAILABLE_STATS:
        logging.error(f"Estadística no válida: {args.statistic}. Debe ser una de: {', '.join(AVAILABLE_STATS)}")
        exit(1)
    # Verifica presencia de columna en el CSV (sin leer datos completos)
    cols = pd.read_csv(args.csv, nrows=0).columns
    if args.statistic not in cols:
        logging.error(f"La columna '{args.statistic}' no está presente en el CSV.")
        exit(1)
    logging.info("Argumentos validados correctamente.")

def load_data(csv_path, statistic, machines, versions):
    df = pd.read_csv(csv_path)
    # Filtrado por estadística y valores nulos
    df = df.dropna(subset=[statistic])
    # Filtrado por máquinas y versiones
    if machines:
        df = df[df["machine"].isin(machines)]
    if versions:
        df = df[df["version"].isin(versions)]
    logging.info(f"Filtrado final: {len(df)} filas.")
    return df

def filter_data(df, fuse):
    if fuse:
        df = df.copy()
        df["machine"] = "ALL"
    return df

def remove_outliers(df, statistic):
    logging.info(f"Eliminando outliers en '{statistic}'...")
    filtered_groups = []
    for (benchmark, version), group in df.groupby(["benchmark", "version"]):
        q1 = group[statistic].quantile(0.25)
        q3 = group[statistic].quantile(0.75)
        iqr = q3 - q1
        mask = (group[statistic] >= q1 - 1.5 * iqr) & (group[statistic] <= q3 + 1.5 * iqr)
        removed = (~mask).sum()
        if removed > 0:
            logging.debug(f"  • {benchmark} ({version}): {removed} outliers eliminados")
        filtered_groups.append(group[mask])
    if filtered_groups:
        return pd.concat(filtered_groups, ignore_index=True)
    else:
        return pd.DataFrame(columns=df.columns)

def generate_summary_table(df, statistic, outpath):
    summary = df.groupby(["benchmark", "version"])[statistic].agg(['mean', 'std', 'count']).reset_index()
    summary.to_csv(outpath, index=False)
    logging.info(f"Tabla resumen guardada en: {outpath}")

def plot_distribution(df, statistic, output_dir, kind="box"):
    os.makedirs(output_dir, exist_ok=True)
    plot_func = sns.boxplot if kind == "box" else sns.violinplot
    for bench in df["benchmark"].unique():
        sub = df[df["benchmark"] == bench]
        if sub["version"].nunique() < 2:
            continue
        plt.figure(figsize=(10, 6))
        plot_func(data=sub, x="version", y=statistic, hue="machine")
        plt.title(f"{bench} — {statistic}")
        plt.xticks(rotation=45)
        plt.tight_layout()
        safe_name = bench.replace("/", "_").replace(" ", "_")
        ext = "boxplot" if kind == "box" else "violinplot"
        plt.savefig(os.path.join(output_dir, f"{safe_name}_{statistic}_{ext}.png"))
        plt.close()
    logging.info(f"{kind.capitalize()}plots generados en: {output_dir}")

def plot_heatmap(df, statistic, output_file):
    pivot = df.groupby(["benchmark", "version"])[statistic].mean().unstack()
    plt.figure(figsize=(12, max(6, len(pivot) * 0.2)))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="coolwarm", cbar_kws={"label": statistic})
    plt.title(f"Benchmark Mean {statistic} by Version")
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    logging.info(f"Heatmap guardado en: {output_file}")

def save_config(args, output_dir):
    config_path = os.path.join(output_dir, "config_used.json")
    with open(config_path, "w") as f:
        json.dump(vars(args), f, indent=2)
    logging.info(f"Configuración guardada en: {config_path}")

def main(args):
    validate_args(args)
    # Normalización de filtros
    machines = [m.strip() for m in args.machines.split(",")] if args.machines else None
    versions = [v.strip() for v in args.versions.split(",")] if args.versions else None

    df = load_data(args.csv, args.statistic, machines, versions)
    if df.empty:
        logging.warning("No hay datos tras el filtrado. Finalizando.")
        return

    df = filter_data(df, args.fuse)
    base_dir = os.path.dirname(args.csv)
    tag = "fused" if args.fuse else "by_machine"
    out_base = os.path.join(base_dir, "plots")
    paths = {
        "base": out_base,
        "summary": os.path.join(out_base, "summary.csv"),
        "filtered_before": os.path.join(out_base, "filtered_before_outliers.csv"),
        "filtered_after": os.path.join(out_base, "filtered_after_outliers.csv"),
        "box": os.path.join(out_base, "boxplots"),
        "violin": os.path.join(out_base, "violins"),
        "heatmap": os.path.join(out_base, "heatmap.png"),
    }
    os.makedirs(out_base, exist_ok=True)

    save_config(args, out_base)
    generate_summary_table(df, args.statistic, paths["summary"])
    df.to_csv(paths["filtered_before"], index=False)
    logging.info(f"Datos filtrados guardados en: {paths['filtered_before']} (antes de outliers)")

    df_stat = remove_outliers(df, args.statistic) if args.remove_outliers else df
    df_stat.to_csv(paths["filtered_after"], index=False)
    logging.info(f"Datos post-outliers guardados en: {paths['filtered_after']}")

    plot_distribution(df_stat, args.statistic, paths["box"], kind="box")
    plot_distribution(df_stat, args.statistic, paths["violin"], kind="violin")
    plot_heatmap(df_stat, args.statistic, paths["heatmap"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Visualiza los resultados de benchmarks de Godot con opciones avanzadas de filtrado y análisis."
    )
    parser.add_argument("--csv", required=True, help="Ruta al archivo CSV con los resultados parseados.")
    parser.add_argument("--statistic", required=True, help="Estadística a visualizar (por ejemplo: time, render_cpu). Obligatoria.")
    parser.add_argument("--machines", help="Máquinas a incluir, separadas por comas. Por defecto: todas.")
    parser.add_argument("--fuse", action="store_true", help="Combina todas las máquinas en una sola.")
    parser.add_argument("--versions", help="Versiones del motor a incluir, separadas por comas. Por defecto: todas.")
    parser.add_argument("--remove-outliers", action="store_true", help="Elimina valores atípicos usando IQR intercuartílico.")
    args = parser.parse_args()
    main(args)