#!/bin/bash

benchmark=""
directories=()
repetitions=""
mode=""

show_help() {
    echo "Uso:"
    echo "  $0 --all --dirs <dir1> [...] --repetitions <N>"
    echo "  $0 --benchmark <path> --dirs <dir1> [...] --repetitions <N>"
    echo ""
    echo "Opciones:"
    echo "  --all                          Ejecuta todos los benchmarks disponibles"
    echo "  --benchmark <path>             Ejecuta solo el benchmark indicado (ej. rendering/culling/basic_cull)"
    echo "  --dirs <d1> [d2 ...]           Directorios con binarios base a usar (obligatorio)"
    echo "  --repetitions <N>              Número de repeticiones (obligatorio)"
    echo "  --help                         Muestra esta ayuda"
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
    base_binary_folder_name=$(basename "${dir%/}")

    echo "=============================="
    echo "Ejecutando benchmarks para: $base_binary_folder_name"

    results_dir="./results/$base_binary_folder_name"
    mkdir -p "$results_dir"

    binary=$(find "$dir" -maxdepth 1 -type f -name "*.out" | head -n 1)

    if [[ -z "$binary" || ! -x "$binary" ]]; then
        echo "  Advertencia: Binario no encontrado o no ejecutable en '$dir'"
        continue
    fi

    for i in $(seq 1 "$repetitions"); do
        if [[ "$mode" == "all" ]]; then
            output_file="$results_dir/results_${base_binary_folder_name}_all_iter${i}.json"
            stdout_file="$results_dir/stdout_${base_binary_folder_name}_all_iter${i}.txt"
            stderr_file="$results_dir/stderr_${base_binary_folder_name}_all_iter${i}.txt"

            echo "  Ejecución $i: $binary (todos los benchmarks)"
            "$binary" -- --run-benchmarks --save-json="$output_file" > "$stdout_file" 2> "$stderr_file"

        elif [[ "$mode" == "custom" ]]; then
            benchmark_sanitized=$(echo "$benchmark" | tr '/.' '__' | tr -cd '[:alnum:]_')

            output_file="$results_dir/results_${base_binary_folder_name}_${benchmark_sanitized}_iter${i}.json"
            stdout_file="$results_dir/stdout_${base_binary_folder_name}_${benchmark_sanitized}_iter${i}.txt"
            stderr_file="$results_dir/stderr_${base_binary_folder_name}_${benchmark_sanitized}_iter${i}.txt"

            echo "  Ejecución $i: $binary (benchmark: $benchmark)"
            "$binary" -- --run-benchmarks --include-benchmarks="$benchmark" --save-json="$output_file" > "$stdout_file" 2> "$stderr_file"
        fi
    done
done
