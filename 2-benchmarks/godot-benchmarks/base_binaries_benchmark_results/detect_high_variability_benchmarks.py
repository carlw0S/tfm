#!/usr/bin/env python3
import os
import argparse
import logging
import pandas as pd

# Configuración de logging (INFO por defecto, DEBUG con --debug)
def setup_logging(debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

# Constante global de estadísticas válidas
AVAILABLE_STATISTICS = ["time", "render_cpu", "render_gpu", "idle", "physics"]

def validate_args(args):
    # Verifica existencia del CSV
    if not os.path.isfile(args.csv):
        logging.error(f"El archivo CSV no existe: {args.csv}")
        exit(1)
    # Verifica estadística válida
    if args.statistic not in AVAILABLE_STATISTICS:
        logging.error(
            f"Estadística no válida: {args.statistic}. Elige una de: {', '.join(AVAILABLE_STATISTICS)}"
        )
        exit(1)
    # Validar columnas en header sin leer todo el CSV
    cols = pd.read_csv(args.csv, nrows=0).columns
    missing = [c for c in ["benchmark", "version", args.statistic] if c not in cols]
    if missing:
        logging.error(f"Faltan columnas en el CSV: {missing}")
        exit(1)
    # Top debe ser positivo
    if args.top < 1:
        logging.error(f"--top debe ser un entero positivo, no {args.top}")
        exit(1)
    logging.debug("Argumentos validados correctamente.")

def load_and_filter(df: pd.DataFrame, args):
    # Filtrar filas con valor nulo en la estadística
    df = df.dropna(subset=[args.statistic])
    # Filtrar por máquinas
    if args.machines:
        machines = [m.strip() for m in args.machines.split(",")]
        df = df[df["machine"].isin(machines)]
        logging.debug(f"Filtrado por máquinas: {machines}")
    # Filtrar por versiones
    if args.versions:
        versions = [v.strip() for v in args.versions.split(",")]
        df = df[df["version"].isin(versions)]
        logging.debug(f"Filtrado por versiones: {versions}")
    logging.info(f"Filtrado final: {len(df)} filas.")
    return df

def remove_outliers(df: pd.DataFrame, stat: str) -> pd.DataFrame:
    logging.info(f"Eliminando outliers (IQR) en '{stat}'…")
    filtered = []
    total_removed = 0
    for (bench, ver), group in df.groupby(["benchmark", "version"]):
        q1 = group[stat].quantile(0.25)
        q3 = group[stat].quantile(0.75)
        iqr = q3 - q1
        mask = group[stat].between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
        removed = (~mask).sum()
        if removed:
            logging.debug(f"  • {bench} ({ver}): {removed} outliers eliminados")
            total_removed += removed
        filtered.append(group[mask])
    result = pd.concat(filtered, ignore_index=True) if filtered else df.iloc[0:0]
    logging.info(f"Total de outliers eliminados: {total_removed}")
    return result

def compute_variability(df: pd.DataFrame, stat: str) -> pd.DataFrame:
    # Calcular medias por benchmark-version
    means = df.groupby(["benchmark", "version"])[stat].mean().unstack(fill_value=0)
    abs_var = means.var(axis=1, ddof=0)
    rel_var = abs_var / (means.mean(axis=1) ** 2).replace(0, float("nan"))
    return pd.DataFrame({
        "benchmark": abs_var.index,
        "variance": abs_var.values,
        "relative_variance": rel_var.values
    })

def main():
    parser = argparse.ArgumentParser(
        description="Detecta benchmarks con mayor variabilidad entre versiones de Godot."
    )
    parser.add_argument(
        "--csv", required=True, help="Ruta al archivo CSV con los resultados parseados."
    )
    parser.add_argument(
        "--statistic", required=True,
        help=f"Estadística a analizar ({', '.join(AVAILABLE_STATISTICS)})."
    )
    parser.add_argument(
        "--top", type=int, default=10, help="Top N benchmarks más variables."
    )
    parser.add_argument(
        "--relative", action="store_true",
        help="Ordenar por variabilidad relativa en lugar de absoluta."
    )
    parser.add_argument(
        "--machines", help="Máquinas a incluir, separadas por coma."
    )
    parser.add_argument(
        "--versions", help="Versiones a incluir, separadas por coma."
    )
    parser.add_argument(
        "--remove-outliers", action="store_true",
        help="Eliminar outliers (IQR) antes de calcular variabilidad."
    )
    parser.add_argument(
        "--fuse", action="store_true",
        help="Fusionar todas las máquinas en una sola etiqueta 'ALL'."
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Mostrar logs DEBUG para más detalles."
    )
    args = parser.parse_args()

    setup_logging(args.debug)
    validate_args(args)

    # Leer CSV una sola vez
    df = pd.read_csv(args.csv)

    # Aplicar filtros
    df = load_and_filter(df, args)
    if df.empty:
        logging.warning("No quedan datos tras aplicar los filtros. Saliendo.")
        return

    # Fusionar máquinas si se pide
    if args.fuse:
        df["machine"] = "ALL"
        logging.info("Máquinas fusionadas en 'ALL'.")

    # Quitar outliers si se pide
    if args.remove_outliers:
        df = remove_outliers(df, args.statistic)
        if df.empty:
            logging.error("Tras eliminar outliers no quedan datos. Saliendo.")
            return

    # Calcular variabilidad
    var_df = compute_variability(df, args.statistic)
    sort_col = "relative_variance" if args.relative else "variance"
    var_df = var_df.sort_values(sort_col, ascending=False).reset_index(drop=True)

    # Mostrar top N en consola
    logging.info(
        f"Top {args.top} benchmarks por "
        f"{'variabilidad relativa' if args.relative else 'absoluta'} en '{args.statistic}':"
    )
    print(var_df.head(args.top).to_string(index=False))

    # Guardar CSV en misma carpeta que el CSV de entrada, sin timestamp
    base_dir = os.path.dirname(args.csv)
    mode = "rel" if args.relative else "abs"
    fuse_tag = "fused" if args.fuse else "by_machine"
    outname = os.path.join(
        base_dir, f"variability_{args.statistic}_{mode}_{fuse_tag}.csv"
    )
    var_df.to_csv(outname, index=False)
    logging.info(f"Resultado completo guardado en: {outname}")

if __name__ == "__main__":
    main()
