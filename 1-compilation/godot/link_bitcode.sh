#!/bin/bash

# ###
# Este script debe estar situado en la carpeta godot, clonada desde:
#       https://github.com/godotengine/godot.git
# Y se usa tras compilar el proyecto con el siguiente comando, SIN OLVIDAR PONER A FALSE LOS DOS FLAGS DE PCRE2 DEL SCONSTRUCT:
#       scons platform=linuxbsd use_llvm=yes linker=lld production=yes optimize=custom ccflags="-c -O0 -Xclang -disable-O0-optnone -emit-llvm -Wl,-save-temps" linkflags="-Wl,-save-temps" verbose=yes &> VERBOSE_OUTPUT.txt
# Por último, antes de poder compilar el .bc global con clang, hay que compilar el siguiente fichero escrito en ensamblador:
#       clang -c thirdparty/zstd/decompress/huf_decompress_amd64.S -o huf_asm.o
# opt se ejecuta así:
#       opt <flags> godot.bc -o godot_opt.bc
# Y clang, así:
#       clang++ -lm -O0 godot_opt.bc huf_asm.o -o godot_opt -fuse-ld=lld -flto=thin -static-libgcc -static-libstdc++ -s -lpcre2-32 -lrt -lpthread -ldl -l:libatomic.a
# ###

# 🗂 Lista de directorios relevantes en Godot
SEARCH_DIRS=("bin" "core" "drivers" "editor" "main" "modules" "platform" "scene" "servers" "tests" "thirdparty")

# 📦 Archivo de salida
OUTPUT="godot.bc"

echo "🔍 Escaneando las siguientes carpetas para buscar LLVM bitcode:"
for dir in "${SEARCH_DIRS[@]}"; do
    echo "   ➤ $dir/"
done

# 🧩 Encuentra todos los .llvm.o
ALL_OBJS=$(find "${SEARCH_DIRS[@]}" -name '*.llvm.o' 2>/dev/null)

# 🧹 Filtrar solo los .o válidos (bitcode real)
VALID_OBJS=()
for f in $ALL_OBJS; do
    if file "$f" | grep -q "LLVM IR bitcode"; then
        VALID_OBJS+=("$f")
    else
        echo "⚠️  Ignorado (no es bitcode): $f"
    fi
done

echo "📄 Encontrados ${#VALID_OBJS[@]} archivos válidos en bitcode."

if [ ${#VALID_OBJS[@]} -eq 0 ]; then
    echo "❌ No hay nada que enlazar, bro. ¿Compilaste con -emit-llvm?"
    exit 1
fi

# 🛠️ Enlazamos todos en uno solo
echo "🔗 Enlazando en: $OUTPUT"
llvm-link "${VALID_OBJS[@]}" -o "$OUTPUT"

if [ $? -eq 0 ]; then
    echo "✅ Bitcode global generado: $OUTPUT"
else
    echo "❌ Algo petó al enlazar."
    exit 1
fi
