#!/bin/bash

# ###
# Tanto este script como la carpeta BASE_BINARIES deben estar situados
# en la carpeta godot-benchmarks, clonada desde el repositorio:
#       https://github.com/godotengine/godot-benchmarks.git
# POR CIERTO, RECUERDA QUE HAY QUE IMPORTAR EL PROYECTO CON ALGÚN GODOT
# AL MENOS UNA VEZ !!!
# ###

# Inicializar variables
benchmark=""
repetitions=""
directories=()
mode=""

# Función de ayuda
show_help() {
    echo "Uso:"
    echo "  $0 --all --dirs <dir1> [...] --repetitions <N>"
    echo "  $0 --benchmark <benchmark_path> --dirs <dir1> [...] --repetitions <N>"
    echo ""
    echo "Opciones:"
    echo "  --all                          Ejecuta todos los benchmarks disponibles"
    echo "  --benchmark <path>             Ejecuta solo el benchmark indicado (ej. rendering/culling/basic_cull)"
    echo "  --dirs <d1> [d2 ...]           Directorios de compilación a usar (obligatorio)"
    echo "  --repetitions <N>              Número de repeticiones (obligatorio)"
    echo "  --help                         Muestra esta ayuda"
    echo ""
    echo "Directorios disponibles:"
    echo "  O0 O1 O2 O3 Os Oz web no-opt scons-emitllvm scons-llvm scons-default"
}

# Parseo de argumentos
while [[ $# -gt 0 ]]; do
    case "$1" in
        --all)
            if [[ -n "$mode" ]]; then
                echo "Error: no puedes usar --all y --benchmark juntos."
                exit 1
            fi
            mode="all"
            shift
            ;;
        --benchmark)
            if [[ -n "$mode" ]]; then
                echo "Error: no puedes usar --benchmark y --all juntos."
                exit 1
            fi
            mode="custom"
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                echo "Error: debes especificar un benchmark después de --benchmark"
                exit 1
            fi
            benchmark="$1"
            shift
            ;;
        --dirs)
            shift
            while [[ $# -gt 0 && "$1" != --* ]]; do
                directories+=("$1")
                shift
            done
            ;;
        --repetitions)
            shift
            if [[ "$1" =~ ^[0-9]+$ ]]; then
                repetitions="$1"
                shift
            else
                echo "Error: '--repetitions' requiere un número entero"
                exit 1
            fi
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Error: opción desconocida '$1'"
            show_help
            exit 1
            ;;
    esac
done

# Validaciones obligatorias
if [[ -z "$mode" ]]; then
    echo "Error: debes usar --all o --benchmark"
    show_help
    exit 1
fi

if [[ -z "$repetitions" ]]; then
    echo "Error: debes especificar --repetitions"
    show_help
    exit 1
fi

if [[ "${#directories[@]}" -eq 0 ]]; then
    echo "Error: debes especificar al menos un directorio con --dirs"
    show_help
    exit 1
fi

# Ejecutar benchmarks
for dir in "${directories[@]}"; do
    echo "Ejecutando benchmarks para: $dir"

    results_dir="./BASE_BINARIES_RESULTS/$dir"
    mkdir -p "$results_dir"

    binary="./BASE_BINARIES/$dir/godot_$dir"

    if [[ ! -x "$binary" ]]; then
        echo "  Advertencia: Binario no encontrado o no ejecutable: $binary"
        continue
    fi

    for i in $(seq 1 "$repetitions"); do
        if [[ "$mode" == "all" ]]; then
            output_file="$results_dir/results_${dir}_all_iter${i}.json"
            stdout_file="$results_dir/stdout_${dir}_all_iter${i}.txt"
            stderr_file="$results_dir/stderr_${dir}_all_iter${i}.txt"

            echo "  Ejecución $i: $binary (todos los benchmarks)"
            "$binary" -- --run-benchmarks --save-json="$output_file" > "$stdout_file" 2> "$stderr_file"

        elif [[ "$mode" == "custom" ]]; then
            benchmark_sanitized=$(echo "$benchmark" | tr '/' '_')

            output_file="$results_dir/results_${dir}_${benchmark_sanitized}_iter${i}.json"
            stdout_file="$results_dir/stdout_${dir}_${benchmark_sanitized}_iter${i}.txt"
            stderr_file="$results_dir/stderr_${dir}_${benchmark_sanitized}_iter${i}.txt"

            echo "  Ejecución $i: $binary (benchmark: $benchmark)"
            "$binary" -- --run-benchmarks --include-benchmarks="$benchmark" --save-json="$output_file" > "$stdout_file" 2> "$stderr_file"
        fi
    done
done

