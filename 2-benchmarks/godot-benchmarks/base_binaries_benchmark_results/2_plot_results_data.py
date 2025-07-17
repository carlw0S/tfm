#!/usr/bin/env python3
import os
import argparse
import logging
import json

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
sns.set_theme(style="whitegrid")

AVAILABLE_STATS = ["time", "render_cpu", "render_gpu", "idle", "physics"]

def validate_args(args):
    if not os.path.isfile(args.csv):
        logging.error(f"El archivo CSV no existe: {args.csv}")
        exit(1)
    stats = [s.strip() for s in args.statistic.split(",")]
    invalid = [s for s in stats if s not in AVAILABLE_STATS]
    if invalid:
        logging.error(f"Estadísticas no válidas: {invalid}. Elige de: {AVAILABLE_STATS}")
        exit(1)
    # Versions es obligatorio y define tanto filtro como orden
    versions = [v.strip() for v in args.versions.split(",")]
    if not versions:
        logging.error("Debes especificar al menos una versión en --versions.")
        exit(1)
    logging.debug("Argumentos validados correctamente.")

def load_and_filter(df, args):
    stats = [s.strip() for s in args.statistic.split(",")]
    df = df.dropna(subset=stats)
    if args.machines:
        machines = [m.strip() for m in args.machines.split(",")]
        df = df[df["machine"].isin(machines)]
    # Filtrar y ordenar por versiones
    versions = [v.strip() for v in args.versions.split(",")]
    df = df[df["version"].isin(versions)]
    # Conservar el orden de versiones para plots
    df["version"] = pd.Categorical(df["version"], categories=versions, ordered=True)
    logging.info(f"Filtrado final: {len(df)} filas.")
    return df, versions

def remove_outliers(df, stat):
    logging.info(f"Eliminando outliers en '{stat}'…")
    kept = []
    for (_, _), group in df.groupby(["benchmark", "version"]):
        q1, q3 = group[stat].quantile([0.25, 0.75])
        iqr = q3 - q1
        mask = group[stat].between(q1 - 1.5*iqr, q3 + 1.5*iqr)
        kept.append(group[mask])
    return pd.concat(kept, ignore_index=True) if kept else df.iloc[0:0]

def generate_summary(df, stat, outpath):
    summary = df.groupby(["benchmark","version"], observed=False)[stat]\
                .agg(['mean','std','count']).reset_index()
    summary.to_csv(outpath, index=False)
    logging.info(f"Tabla resumen guardada en: {outpath}")

def plot_distribution(df, stat, output_dir, versions, kind="box"):
    os.makedirs(output_dir, exist_ok=True)
    plot_fn = sns.boxplot if kind=="box" else sns.violinplot
    for bench in df["benchmark"].unique():
        sub = df[df["benchmark"]==bench]
        if sub["version"].nunique()<2: continue
        plt.figure(figsize=(10,6))
        plot_fn(
            data=sub,
            x="version", y=stat, hue="machine",
            order=versions
        )
        plt.title(f"{bench} — {stat}")
        plt.xticks(rotation=45)
        plt.tight_layout()
        safe = bench.replace("/","_").replace(" ","_")
        ext = "boxplot" if kind=="box" else "violinplot"
        plt.savefig(os.path.join(output_dir, f"{safe}_{stat}_{ext}.png"))
        plt.close()
    logging.info(f"{kind.capitalize()}plots generados en: {output_dir}")

def plot_heatmap(df, stat, output_file, versions):
    pivot = df.groupby(["benchmark","version"], observed=False)[stat].mean().unstack()
    pivot = pivot.reindex(columns=versions)
    plt.figure(figsize=(12, max(6, len(pivot)*0.2)))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="coolwarm",
                cbar_kws={"label":stat})
    plt.title(f"Benchmark Mean {stat} by Version")
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    logging.info(f"Heatmap guardado en: {output_file}")

def save_config(args, outdir):
    cfg = vars(args)
    with open(os.path.join(outdir,"config_used.json"),"w") as f:
        json.dump(cfg, f, indent=2)
    logging.info(f"Configuración guardada en: {outdir}/config_used.json")

def main():
    parser = argparse.ArgumentParser(
        description="Visualiza benchmarks de Godot con orden de versiones basado en --versions."
    )
    parser.add_argument("--csv", required=True, help="Ruta al CSV parseado")
    parser.add_argument("--statistic", required=True,
                        help="Estadísticas separadas por coma")
    parser.add_argument("--machines", help="Máquinas separadas por coma")
    parser.add_argument("--versions", required=True,
                        help="Versiones a incluir y su orden, separadas por coma")
    parser.add_argument("--fuse", action="store_true",
                        help="Fusiona máquinas en 'ALL'")
    parser.add_argument("--remove-outliers", action="store_true",
                        help="Elimina outliers IQR")
    parser.add_argument("--debug", action="store_true",
                        help="Logs DEBUG")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    validate_args(args)

    df = pd.read_csv(args.csv)
    df, versions = load_and_filter(df, args)
    if df.empty:
        logging.warning("No hay datos tras filtrado")
        return

    if args.fuse:
        df["machine"]="ALL"

    base = os.path.dirname(args.csv)
    stats = [s.strip() for s in args.statistic.split(",")]
    for stat in stats:
        out_base = os.path.join(base, f"plots_{stat}")
        os.makedirs(out_base, exist_ok=True)

        save_config(args, out_base)
        generate_summary(df, stat, os.path.join(out_base, f"{stat}_summary.csv"))

        before_csv = os.path.join(out_base, f"{stat}_filtered_before.csv")
        df.to_csv(before_csv, index=False)
        logging.info(f"Datos antes de outliers guardados en: {before_csv}")

        df_stat = remove_outliers(df, stat) if args.remove_outliers else df
        after_csv = os.path.join(out_base, f"{stat}_filtered_after.csv")
        df_stat.to_csv(after_csv, index=False)
        logging.info(f"Datos post-outliers guardados en: {after_csv}")

        plot_distribution(df_stat, stat, os.path.join(out_base,"boxplots"), versions, kind="box")
        plot_distribution(df_stat, stat, os.path.join(out_base,"violins"), versions, kind="violin")
        plot_heatmap(df_stat, stat, os.path.join(out_base,f"heatmap_{stat}.png"), versions)

    logging.info("Plots generados.") 

if __name__=="__main__":
    main()
