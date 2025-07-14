#!/bin/bash

benchmark=""
directories=()
repetitions=""
mode=""
strategy=""

declare -A binaries
declare -A folder_names

total_iters=0
completed_iters=0
total_elapsed=0

show_help() {
    echo "Uso:"
    echo "  $0 --all|--benchmark <path> --dirs <dir1> [...] --repetitions <N> --strategy <by-binary|round-robin>"
    echo ""
    echo "Opciones:"
    echo "  --all                               Ejecuta todos los benchmarks disponibles"
    echo "  --benchmark <path>                  Ejecuta solo el benchmark indicado (ej. rendering/culling/basic_cull)"
    echo "  --dirs <d1> [d2 ...]                Directorios con binarios base a usar (obligatorio)"
    echo "  --repetitions <N>                   Número de repeticiones (obligatorio)"
    echo "  --strategy <by-binary|round-robin>  Estrategia de repetición (obligatorio)"
    echo "  --help                              Muestra esta ayuda"
}

parse_args() {
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
            --strategy)
                shift
                if [[ "$1" != "by-binary" && "$1" != "round-robin" ]]; then
                    echo "Error: estrategia inválida '$1'. Usa 'by-binary' o 'round-robin'"
                    exit 1
                fi
                strategy="$1"
                shift
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
}

validate_args() {
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

    if [[ -z "$strategy" ]]; then
        echo "Error: debes especificar --strategy"
        show_help
        exit 1
    fi
}

prepare_binaries() {
    for dir in "${directories[@]}"; do
        base_name=$(basename "${dir%/}")
        folder_names["$dir"]="$base_name"
        bin=$(find "$dir" -maxdepth 1 -type f -name "*.out" | head -n 1)

        if [[ -z "$bin" || ! -x "$bin" ]]; then
            echo "  Advertencia: Binario no encontrado o no ejecutable en '$dir'"
            continue
        fi
        binaries["$dir"]="$bin"
    done

    if [[ "${#binaries[@]}" -eq 0 ]]; then
        echo "Error: no se encontró ningún binario válido."
        exit 1
    fi

    total_iters=$(( ${#binaries[@]} * repetitions ))
}

run_one_benchmark() {
    local binary="$1"
    local name="$2"
    local iter="$3"

    local results_dir="./results/$name"
    mkdir -p "$results_dir"

    local suffix="all"
    local args="--run-benchmarks"

    if [[ "$mode" == "custom" ]]; then
        local sanitized=$(echo "$benchmark" | tr '/.' '__' | tr -cd '[:alnum:]_')
        suffix="$sanitized"
        args="--run-benchmarks --include-benchmarks=$benchmark"
    fi

    local output_file="$results_dir/results_${name}_${suffix}_iter${iter}.json"
    local stdout_file="$results_dir/stdout_${name}_${suffix}_iter${iter}.txt"
    local stderr_file="$results_dir/stderr_${name}_${suffix}_iter${iter}.txt"

    echo "  [$name] Iteración $iter: ejecutando..."

    local start_time=$(date +%s)

    "$binary" -- $args --save-json="$output_file" > "$stdout_file" 2> "$stderr_file"

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    total_elapsed=$((total_elapsed + duration))
    completed_iters=$((completed_iters + 1))

    local remaining_iters=$((total_iters - completed_iters))
    local avg_time=$((total_elapsed / completed_iters))
    local eta=$((remaining_iters * avg_time))

    echo "    ✔ Duración: ${duration}s | Iteraciones hechas: $completed_iters/$total_iters | ETA: ~${eta}s"
}

run_by_binary_strategy() {
    for dir in "${!binaries[@]}"; do
        bin="${binaries[$dir]}"
        name="${folder_names[$dir]}"
        echo "=============================="
        echo "Ejecutando benchmarks para: $name"

        for i in $(seq 1 "$repetitions"); do
            run_one_benchmark "$bin" "$name" "$i"
        done
    done
}

run_round_robin_strategy() {
    for i in $(seq 1 "$repetitions"); do
        echo "=============================="
        echo "Ronda $i de $repetitions"
        for dir in "${!binaries[@]}"; do
            bin="${binaries[$dir]}"
            name="${folder_names[$dir]}"
            run_one_benchmark "$bin" "$name" "$i"
        done
    done
}

### Main
parse_args "$@"
validate_args
prepare_binaries

if [[ "$strategy" == "by-binary" ]]; then
    run_by_binary_strategy
else
    run_round_robin_strategy
fi
