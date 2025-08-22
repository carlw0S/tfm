#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para graficar el progreso de algoritmos de búsqueda:
- Algoritmo Genético (GA): múltiples valores de fitness por generación (mejor, peor y promedio).
- Simulated Annealing (SA): un único valor de fitness por iteración/generación.

Detección automática del formato del log:
- GA si aparecen bloques "## EPOCH N ##"
- SA si aparecen bloques "## ITERATION N ##"

Para GA se grafica: mejor, peor y promedio (por generación).
Para SA se grafica: fitness por iteración y mejor histórico acumulado.

Por defecto se asume que "más bajo es mejor". Si en tu problema es al revés,
usa la opción --maximize.
"""

from __future__ import annotations
import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import matplotlib.pyplot as plt

# Expresiones regulares para localizar generacións/iteraciones y valores de fitness.
EPOCH_RE      = re.compile(r"^\s*##\s*EPOCH\s+(\d+)\s*##\s*$")
ITER_RE       = re.compile(r"^\s*##\s*ITERATION\s+(\d+)\s*##\s*$")
FIT_RE        = re.compile(r"Fitness:\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))")

def detectar_formato(path: Path) -> str:
    """
    Intenta detectar si el fichero es de GA o SA.
    Devuelve "GA", "SA" o lanza SystemExit si no se reconoce.
    """
    es_ga = False
    es_sa = False
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            if EPOCH_RE.match(line):
                es_ga = True
            if ITER_RE.match(line):
                es_sa = True
            if i > 1000 and (es_ga or es_sa):
                break
    if es_ga and not es_sa:
        return "GA"
    if es_sa and not es_ga:
        return "SA"
    if es_ga and es_sa:
        # Si por algún motivo aparecen ambos, priorizamos GA y avisamos.
        print("Aviso: se detectaron patrones de GA y SA; se asumirá GA.")
        return "GA"
    raise SystemExit("No se pudo detectar el formato del log (ni GA ni SA).")

def parse_log_ga(path: Path) -> Dict[int, List[float]]:
    """
    Analiza un log de GA y devuelve: generación -> lista de fitness de su población.
    """
    epoch_fitness: Dict[int, List[float]] = {}
    current_epoch: int | None = None
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m_epoch = EPOCH_RE.match(line)
            if m_epoch:
                current_epoch = int(m_epoch.group(1))
                epoch_fitness.setdefault(current_epoch, [])
                continue
            if current_epoch is not None:
                for m_fit in FIT_RE.finditer(line):
                    epoch_fitness[current_epoch].append(float(m_fit.group(1)))
    # Filtrar generacións sin datos
    return {e: vals for e, vals in epoch_fitness.items() if vals}

def parse_log_sa(path: Path) -> Dict[int, float]:
    """
    Analiza un log de SA y devuelve: iteración/generación -> fitness (único valor).
    """
    iter_fitness: Dict[int, float] = {}
    current_iter: int | None = None
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m_it = ITER_RE.match(line)
            if m_it:
                current_iter = int(m_it.group(1))
                continue
            if current_iter is not None:
                m_fit = FIT_RE.search(line)
                if m_fit:
                    iter_fitness[current_iter] = float(m_fit.group(1))
    # Filtrar iteraciones sin datos
    return dict(sorted(iter_fitness.items()))

def resumen_ga(epoch_fitness: Dict[int, List[float]], maximize: bool = False
               ) -> Tuple[List[int], List[float], List[float], List[float]]:
    """
    Calcula, para cada generación (GA), el mejor, peor y promedio de fitness.
    Si maximize=True, el mejor será el máximo; de lo contrario, el mínimo.
    """
    epochs = sorted(epoch_fitness.keys())
    best, worst, avg = [], [], []
    for e in epochs:
        vals = np.asarray(epoch_fitness[e], dtype=float)
        if maximize:
            best.append(float(np.max(vals)))
            worst.append(float(np.min(vals)))
        else:
            best.append(float(np.min(vals)))
            worst.append(float(np.max(vals)))
        avg.append(float(np.mean(vals)))
    return epochs, best, worst, avg

def resumen_sa(iter_fitness: Dict[int, float], maximize: bool = False
               ) -> Tuple[List[int], List[float], List[float]]:
    """
    Para SA devolvemos:
    - xs: lista ordenada de iteraciones
    - ys: fitness por iteración
    - ybest: mejor histórico acumulado (según minimizar o maximizar)
    """
    xs = sorted(iter_fitness.keys())
    ys = [iter_fitness[i] for i in xs]
    ybest = []
    if maximize:
        best_so_far = -np.inf
        for v in ys:
            best_so_far = max(best_so_far, v)
            ybest.append(best_so_far)
    else:
        best_so_far = np.inf
        for v in ys:
            best_so_far = min(best_so_far, v)
            ybest.append(best_so_far)
    return xs, ys, ybest

def plot_ga(epochs: List[int], best: List[float], worst: List[float], avg: List[float],
            title: str, out_path: Path | None) -> None:
    """
    Grafica el progreso de GA: mejor, peor y promedio por generación.
    """
    plt.figure(figsize=(6, 4))
    plt.plot(epochs, worst, label="Peor fitness")
    plt.plot(epochs, avg,   label="Fitness promedio")
    plt.plot(epochs, best,  label="Mejor fitness")
    plt.xlabel("Generación")
    plt.ylabel("Fitness (tiempo de ejecución, ms)")
    # plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path, dpi=180)
        print(f"Gráfica (GA) guardada en: {out_path}")
    else:
        plt.show()

def plot_sa(xs: List[int], ys: List[float], ybest: List[float],
            title: str, out_path: Path | None) -> None:
    """
    Grafica el progreso de SA: fitness por iteración y mejor histórico acumulado.
    """
    plt.figure(figsize=(6, 4))
    plt.plot(xs, ys,    label="Fitness de la iteración")
    plt.plot(xs, ybest, label="Mejor fitness histórico")
    plt.xlabel("Iteración")
    plt.ylabel("Fitness (tiempo de ejecución, ms)")
    # plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path, dpi=180)
        print(f"Gráfica (SA) guardada en: {out_path}")
    else:
        plt.show()

def maybe_escribir_csv_ga(epochs: List[int], best: List[float], worst: List[float], avg: List[float],
                          csv_path: Path | None) -> None:
    """
    Guarda un CSV con las estadísticas por generación (GA).
    """
    if not csv_path:
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8") as f:
        f.write("generacion,mejor,peor,promedio\n")
        for e, b, w, a in zip(epochs, best, worst, avg):
            f.write(f"{e},{b},{w},{a}\n")
    print(f"CSV (GA) guardado en: {csv_path}")

def maybe_escribir_csv_sa(xs: List[int], ys: List[float], ybest: List[float],
                          csv_path: Path | None) -> None:
    """
    Guarda un CSV con fitness por iteración y mejor histórico (SA).
    """
    if not csv_path:
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8") as f:
        f.write("iteracion,fitness,mejor_historico\n")
        for i, v, b in zip(xs, ys, ybest):
            f.write(f"{i},{v},{b}\n")
    print(f"CSV (SA) guardado en: {csv_path}")

def main() -> None:
    p = argparse.ArgumentParser(
        description="Graficar la evolución del fitness a partir de logs de GA o SA (detección automática)."
    )
    p.add_argument("log", type=Path, help="Ruta al log (GA: progress_ga-*.txt, SA: progress_sa-*.txt)")
    p.add_argument("-o", "--out", type=Path, default=None,
                   help="Ruta de salida de la imagen (ej: plots/progreso.png). Si no se indica, se muestra en pantalla.")
    p.add_argument("--csv", type=Path, default=None,
                   help="Ruta opcional para guardar un CSV con el resumen.")
    p.add_argument("--maximize", action="store_true",
                   help="Si se activa, se interpreta que valores mayores de fitness son mejores (por defecto: minimizar).")
    p.add_argument("--title", default=None,
                   help="Título de la gráfica. Si no se indica, se usa uno acorde al formato detectado.")
    args = p.parse_args()

    formato = detectar_formato(args.log)

    if formato == "GA":
        epoch_fitness = parse_log_ga(args.log)
        if not epoch_fitness:
            raise SystemExit("No se encontraron valores de fitness por generación (GA). Revisa el formato del log.")
        epochs, best, worst, avg = resumen_ga(epoch_fitness, maximize=args.maximize)
        title = args.title or "Progreso del Algoritmo Genético (GA)"
        plot_ga(epochs, best, worst, avg, title=title, out_path=args.out)
        maybe_escribir_csv_ga(epochs, best, worst, avg, csv_path=args.csv)

    elif formato == "SA":
        iter_fitness = parse_log_sa(args.log)
        if not iter_fitness:
            raise SystemExit("No se encontraron valores de fitness por iteración (SA). Revisa el formato del log.")
        xs, ys, ybest = resumen_sa(iter_fitness, maximize=args.maximize)
        title = args.title or "Progreso de Simulated Annealing (SA)"
        plot_sa(xs, ys, ybest, title=title, out_path=args.out)
        maybe_escribir_csv_sa(xs, ys, ybest, csv_path=args.csv)

if __name__ == "__main__":
    main()
