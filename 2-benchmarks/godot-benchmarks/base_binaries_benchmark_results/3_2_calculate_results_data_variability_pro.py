#!/usr/bin/env python3
import os
import argparse
import logging

import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

# Configuración de logging (INFO por defecto, DEBUG con --debug)
def setup_logging(debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

# Constante global de estadísticas válidas
AVAILABLE_STATISTICS = ["time", "render_cpu", "render_gpu", "idle", "physics"]
# Métodos de variabilidad soportados
VAR_METHODS = ["variance", "coef_var", "robust"]

def validate_args(args):
    if not os.path.isfile(args.csv):
        logging.error(f"El archivo CSV no existe: {args.csv}")
        exit(1)
    if args.statistic not in AVAILABLE_STATISTICS:
        logging.error(
            f"Estadística no válida: {args.statistic}. Elige una de: "
            f"{', '.join(AVAILABLE_STATISTICS)}"
        )
        exit(1)
    if args.method not in VAR_METHODS:
        logging.error(
            f"Método de variabilidad no válido: {args.method}. "
            f"Elige uno de: {', '.join(VAR_METHODS)}"
        )
        exit(1)
    if args.top < 1:
        logging.error(f"--top debe ser un entero positivo, no {args.top}")
        exit(1)
    # Validar columnas en header sin leer todo el CSV
    cols = pd.read_csv(args.csv, nrows=0).columns
    missing = [c for c in ["benchmark", "version", args.statistic] if c not in cols]
    if missing:
        logging.error(f"Faltan columnas en el CSV: {missing}")
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
    filtered = []
    total_removed = 0
    for (bench, ver), group in df.groupby(["benchmark", "version"]):
        q1, q3 = group[stat].quantile([0.25, 0.75])
        iqr = q3 - q1
        mask = group[stat].between(q1 - 1.5*iqr, q3 + 1.5*iqr)
        removed = (~mask).sum()
        if removed:
            logging.debug(f"  • {bench} ({ver}): {removed} outliers eliminados")
            total_removed += removed
        filtered.append(group[mask])
    result = pd.concat(filtered, ignore_index=True) if filtered else df.iloc[0:0]
    logging.info(f"Total de outliers eliminados: {total_removed}")
    return result

def compute_variability(df, stat, method, weight):
    pivot = df.groupby(["benchmark", "version"])[stat].mean().unstack()
    pivot = pivot.dropna(axis=0)  # solo benchmarks presentes en todas las versiones
    if method == "variance":
        var = pivot.var(axis=1, ddof=0)
    elif method == "coef_var":
        var = pivot.std(axis=1, ddof=0) / pivot.mean(axis=1)
    else:  # robust = MAD/median
        median = pivot.median(axis=1)
        mad = pivot.apply(lambda row: np.median(np.abs(row - np.median(row))), axis=1)
        var = mad / median.replace({0: np.nan})
    if weight:
        var = var * pivot.mean(axis=1)
    return pivot, var

def perform_anova(df, stat, alpha):
    pvals = {}
    for bench, group in df.groupby("benchmark"):
        data = [g[stat].values for _, g in group.groupby("version")]
        p = stats.f_oneway(*data)[1] if len(data) > 1 else np.nan
        pvals[bench] = p
    benches = list(pvals.keys())
    pvalues = np.array([pvals[b] for b in benches], dtype=float)
    mask = ~np.isnan(pvalues)
    adj = np.full_like(pvalues, np.nan)
    if mask.sum() > 0:
        _, adj_p, _, _ = multipletests(pvalues[mask], alpha=alpha, method="fdr_bh")
        adj[mask] = adj_p
    return pd.Series(pvalues, index=benches), pd.Series(adj, index=benches)

def main():
    parser = argparse.ArgumentParser(
        description="Detecta benchmarks con alta variabilidad entre versiones de Godot."
    )
    parser.add_argument(
        "--csv", required=True, help="Ruta al CSV parseado con resultados."
    )
    parser.add_argument(
        "--statistic", required=True, choices=AVAILABLE_STATISTICS,
        help="Estadística a analizar."
    )
    parser.add_argument(
        "--top", type=int, default=10, help="Top N benchmarks más variables."
    )
    parser.add_argument(
        "--method", default="coef_var", choices=VAR_METHODS,
        help="Método de variabilidad (variance, coef_var, robust)."
    )
    parser.add_argument(
        "--machines", help="Máquinas a incluir, separadas por coma."
    )
    parser.add_argument(
        "--versions", help="Versiones a incluir, separadas por coma."
    )
    parser.add_argument(
        "--remove-outliers", action="store_true",
        help="Eliminar outliers (IQR) antes de calcular."
    )
    parser.add_argument(
        "--fuse", action="store_true",
        help="Fusionar máquinas en 'ALL'."
    )
    parser.add_argument(
        "--significance", action="store_true",
        help="Realizar ANOVA y ajuste de p-values."
    )
    parser.add_argument(
        "--alpha", type=float, default=0.05,
        help="Nivel de significancia para ANOVA (FDR)."
    )
    parser.add_argument(
        "--weight", action="store_true",
        help="Ponderar variabilidad por media global."
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Mostrar logs DEBUG para más detalles."
    )
    args = parser.parse_args()

    setup_logging(args.debug)
    validate_args(args)

    # Carga y filtrado
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

    pivot, var_series = compute_variability(
        df, args.statistic, args.method, args.weight
    )
    result = pd.DataFrame({
        "benchmark": var_series.index,
        "variability": var_series.values
    })

    if args.significance:
        pvals, adj_p = perform_anova(df, args.statistic, args.alpha)
        result["p_value"] = result["benchmark"].map(pvals)
        result["p_adj"] = result["benchmark"].map(adj_p)
        result["significant"] = result["p_adj"] < args.alpha

    result = result.sort_values("variability", ascending=False).reset_index(drop=True)

    logging.info(
        f"Top {args.top} benchmarks por variabilidad ({args.method}) "
        f"en '{args.statistic}':"
    )
    print(result.head(args.top).to_string(index=False))

    base_dir = os.path.dirname(args.csv)
    fuse_tag = "fused" if args.fuse else "by_machine"
    outname = os.path.join(
        base_dir,
        f"variability_{args.statistic}_{args.method}_{fuse_tag}.csv"
    )
    result.to_csv(outname, index=False)
    logging.info(f"Guardado resultado en: {outname}")

if __name__ == "__main__":
    main()
