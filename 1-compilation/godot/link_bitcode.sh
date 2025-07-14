#!/bin/bash

# Lista de directorios relevantes en Godot (es decir, que contienen archivos .llvm.o)
search_dirs=("core" "drivers" "editor" "main" "modules" "platform" "scene" "servers" "thirdparty")

# Archivo de salida
output="godot.bc"

echo "Escaneando las siguientes carpetas para buscar LLVM bitcode:"
for dir in "${search_dirs[@]}"; do
    echo "   - $dir/"
done

# Encuentra todos los archivos .llvm.o
all_objs=$(find "${search_dirs[@]}" -name '*.llvm.o' 2>/dev/null)

# Filtra solo los archivos válidos (es decir, .llvm.o que contengan bitcode real, y no otros tipos de archivos)
valid_objs=()
for f in $all_objs; do
    if file "$f" | grep -q "LLVM IR bitcode"; then
        valid_objs+=("$f")
    else
        echo "[!] Ignorado (no es bitcode): $f"
    fi
done

echo "Encontrados ${#valid_objs[@]} archivos válidos en bitcode."

if [ ${#valid_objs[@]} -eq 0 ]; then
    echo "[ERROR] No hay nada que enlazar. ¿Has incluido el flag -emit-llvm en el ccflags del scons?"
    exit 1
fi

# Enlaza todo el bitcode en un solo archivo
echo "Enlazando en: $output"
llvm-link "${valid_objs[@]}" -o "$output"

if [ $? -eq 0 ]; then
    echo "[OK] Bitcode global generado: $output"
else
    echo "[ERROR] Algo falló al enlazar."
    exit 1
fi
