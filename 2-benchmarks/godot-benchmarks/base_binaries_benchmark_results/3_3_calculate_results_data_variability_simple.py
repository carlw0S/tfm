#!/usr/bin/env python3
import os
import argparse
import logging

import pandas as pd

# Configuración de logging (INFO por defecto, DEBUG con --debug)
def setup_logging(debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

# Estadísticas válidas
AVAILABLE_STATISTICS = ["time", "render_cpu", "render_gpu", "idle", "physics"]

def validate_args(args):
    if not os.path.isfile(args.csv):
        logging.error(f"El archivo CSV no existe: {args.csv}")
        exit(1)
    if args.statistic not in AVAILABLE_STATISTICS:
        logging.error(
            f"Estadística no válida: {args.statistic}. "
            f"Elige una de: {', '.join(AVAILABLE_STATISTICS)}"
        )
        exit(1)
    cols = pd.read_csv(args.csv, nrows=0).columns
    required = ["benchmark", "version", args.statistic]
    missing = [c for c in required if c not in cols]
    if missing:
        logging.error(f"Faltan columnas en el CSV: {missing}")
        exit(1)
    if args.top < 1:
        logging.error(f"--top debe ser un entero positivo, no {args.top}")
        exit(1)
    logging.debug("Argumentos validados correctamente.")

def load_and_filter(df, args):
    df = df.dropna(subset=[args.statistic])
    if args.machines:
        machines = [m.strip() for m in args.machines.split(",")]
        df = df[df["machine"].isin(machines)]
        logging.debug(f"Filtrado por máquinas: {machines}")
    if args.versions:
        versions = [v.strip() for v in args.versions.split(",")]
        df = df[df["version"].isin(versions)]
        logging.debug(f"Filtrado por versiones: {versions}")
    logging.info(f"Filtrado final: {len(df)} filas.")
    return df

def remove_outliers(df, stat):
    logging.info(f"Eliminando outliers (IQR) en '{stat}'…")
    kept = []
    for (bench, ver), group in df.groupby(["benchmark", "version"]):
        q1, q3 = group[stat].quantile([0.25, 0.75])
        iqr = q3 - q1
        mask = group[stat].between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
        removed = (~mask).sum()
        if removed:
            logging.debug(f"  • {bench} ({ver}): {removed} outliers eliminados")
        kept.append(group[mask])
    return pd.concat(kept, ignore_index=True) if kept else df.iloc[0:0]

def compute_relative_range(df, stat):
    pivot = df.groupby(["benchmark", "version"])[stat].mean().unstack()
    pivot = pivot.dropna(axis=0)
    absolute = pivot.max(axis=1) - pivot.min(axis=1)
    mean_all = pivot.mean(axis=1)
    relative = absolute / mean_all
    return relative

def main():
    parser = argparse.ArgumentParser(
        description="Detecta benchmarks con mayor variación relativa entre versiones."
    )
    parser.add_argument("--csv", required=True,
                        help="Ruta al CSV con resultados parseados.")
    parser.add_argument("--statistic", required=True,
                        choices=AVAILABLE_STATISTICS,
                        help="Estadística a analizar.")
    parser.add_argument("--top", type=int, default=10,
                        help="Top N benchmarks por variación relativa.")
    parser.add_argument("--machines",
                        help="Máquinas a incluir, separadas por coma.")
    parser.add_argument("--versions",
                        help="Versiones a incluir, separadas por coma.")
    parser.add_argument("--remove-outliers", action="store_true",
                        help="Eliminar outliers (IQR) antes de calcular.")
    parser.add_argument("--fuse", action="store_true",
                        help="Fusionar máquinas en 'ALL'.")
    parser.add_argument("--debug", action="store_true",
                        help="Mostrar logs DEBUG para más detalles.")
    args = parser.parse_args()

    setup_logging(args.debug)
    validate_args(args)

    df = pd.read_csv(args.csv)
    df = load_and_filter(df, args)
    if df.empty:
        logging.warning("No quedan datos tras el filtrado.")
        return

    if args.fuse:
        df["machine"] = "ALL"
        logging.info("Máquinas fusionadas en 'ALL'.")

    if args.remove_outliers:
        df = remove_outliers(df, args.statistic)
        if df.empty:
            logging.error("Tras eliminar outliers no quedan datos.")
            return

    rel = compute_relative_range(df, args.statistic)
    result = rel.sort_values(ascending=False).head(args.top).to_frame(name="relative_variation")

    logging.info(f"Top {args.top} benchmarks por variación relativa en '{args.statistic}':")
    print(result.to_string())

    base_dir = os.path.dirname(args.csv)
    fuse_tag = "fused" if args.fuse else "by_machine"
    out_csv = os.path.join(
        base_dir,
        f"variability_{args.statistic}_{fuse_tag}.csv"
    )
    result.to_csv(out_csv, index=True)
    logging.info(f"Resultado guardado en: {out_csv}")

if __name__ == "__main__":
    main()
