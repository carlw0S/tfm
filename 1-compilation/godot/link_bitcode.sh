#!/bin/bash

# Lista de directorios relevantes en Godot (es decir, que contienen archivos .llvm.o)
SEARCH_DIRS=("core" "drivers" "editor" "main" "modules" "platform" "scene" "servers" "thirdparty")

# Archivo de salida
OUTPUT="godot.bc"

echo "Escaneando las siguientes carpetas para buscar LLVM bitcode:"
for dir in "${SEARCH_DIRS[@]}"; do
    echo "   - $dir/"
done

# Encuentra todos los archivos .llvm.o
ALL_OBJS=$(find "${SEARCH_DIRS[@]}" -name '*.llvm.o' 2>/dev/null)

# Filtra solo los archivos válidos (es decir, .llvm.o que contengan bitcode real, y no otros tipos de archivos)
VALID_OBJS=()
for f in $ALL_OBJS; do
    if file "$f" | grep -q "LLVM IR bitcode"; then
        VALID_OBJS+=("$f")
    else
        echo "[!] Ignorado (no es bitcode): $f"
    fi
done

echo "Encontrados ${#VALID_OBJS[@]} archivos válidos en bitcode."

if [ ${#VALID_OBJS[@]} -eq 0 ]; then
    echo "[ERROR] No hay nada que enlazar. ¿Has incluido el flag -emit-llvm en el ccflags del scons?"
    exit 1
fi

# Enlaza todo el bitcode en un solo archivo
echo "Enlazando en: $OUTPUT"
llvm-link "${VALID_OBJS[@]}" -o "$OUTPUT"

if [ $? -eq 0 ]; then
    echo "[OK] Bitcode global generado: $OUTPUT"
else
    echo "[ERROR] Algo falló al enlazar."
    exit 1
fi
