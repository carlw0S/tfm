#!/bin/bash

# Lista de passes
all_passes=(
'-aa' '-atomic-expand' '-basic-aa' '-block-freq' '-branch-prob' '-cfl-anders-aa' '-cfl-steens-aa'
'-codegenprepare' '-cost-model' '-cycles' '-da' '-demanded-bits' '-divergence' '-domfrontier' '-domtree'
'-dwarfehprepare' '-early-cse-memssa' '-expand-reductions' '-expandmemcmp' '-expandvp'
'-global-merge' '-globals-aa' '-hardware-loops' '-hexagon-loop-idiom' '-hexagon-vc' '-hexagon-vlcr'
'-indirectbr-expand' '-interleaved-access' '-interleaved-load-combine' '-iv-users' '-jmc-instrument'
'-lazy-value-info' '-loop-extract-single' '-loops' '-lower-amx-intrinsics' '-lower-amx-type'
'-lower-matrix-intrinsics-minimal' '-memdep' '-memoryssa' '-mve-tail-predication' '-objc-arc-aa'
'-phi-values' '-postdomtree' '-pre-amx-config' '-pre-isel-intrinsic-lowering' '-regions' '-replace-with-veclib' '-safe-stack'
'-scalar-evolution' '-scev-aa' '-scoped-noalias-aa' '-select-optimize' '-si-annotate-control-flow' '-sjljehprepare'
'-stack-safety' '-stack-safety-local' '-systemz-tdc' '-targetlibinfo' '-tbaa' '-type-promotion' '-unreachableblockelim'
'-verify-safepoint-ir' '-wasm-add-missing-prototypes' '-wasm-fix-function-bitcasts' '-wasm-lower-em-ehsjlj'
'-wasm-mclower-prepass' '-wasm-optimize-returned' '-wasmehprepare' '-winehprepare' '-adce' '-add-discriminators' '-aggressive-instcombine' '-alignment-from-assumptions' 
'-always-inline' '-annotation-remarks' '-annotation2metadata' '-assume-builder' '-assume-simplify'
'-bdce' '-bounds-checking' '-break-crit-edges' '-called-value-propagation'
'-callsite-splitting' '-canon-freeze' '-consthoist' '-constmerge' '-constraint-elimination'
'-correlated-propagation' '-cross-dso-cfi' '-dce' '-deadargelim' '-dfa-jump-threading' '-div-rem-pairs'
'-dse' '-early-cse' '-elim-avail-extern' '-extract-blocks' '-fix-irreducible' '-flattencfg' '-float2int' 
'-forceattrs' '-function-attrs' '-function-specialization' '-globaldce' '-globalopt' '-globalsplit' '-guard-widening'
'-gvn' '-gvn-hoist' '-gvn-sink' '-hotcoldsplit' '-indvars' '-infer-address-spaces' '-inferattrs' '-inject-tli-mappings'
'-inline' '-instcombine' '-instcount' '-instnamer' '-instsimplify' '-ipsccp' '-irce' '-iroutliner'
'-jump-threading' '-lcssa' '-libcalls-shrinkwrap' '-load-store-vectorizer' '-loop-data-prefetch' 
'-loop-deletion' '-loop-distribute' '-loop-extract' '-loop-flatten' '-loop-fusion' '-loop-idiom' '-loop-instsimplify' 
'-loop-interchange' '-loop-load-elim' '-loop-predication' '-loop-reduce' '-loop-reroll' '-loop-rotate' '-loop-simplify' 
'-loop-simplifycfg' '-loop-sink' '-loop-unroll' '-loop-unroll-and-jam' '-loop-vectorize' '-loop-versioning' 
'-lower-constant-intrinsics' '-lower-expect' '-lower-global-dtors' '-lower-guard-intrinsic'
'-lower-matrix-intrinsics' '-lower-widenable-condition' '-loweratomic' '-lowerinvoke' '-lowerswitch' '-make-guards-explicit'
'-mem2reg' '-memcpyopt' '-mergefunc' '-mergeicmps' '-mergereturn' '-mldst-motion' 
'-nary-reassociate' '-newgvn' '-objc-arc' '-objc-arc-apelim' '-objc-arc-contract' '-objc-arc-expand'
'-partial-inliner' '-partially-inline-libcalls' '-reassociate' '-redundant-dbg-inst-elim' '-reg2mem' '-rewrite-statepoints-for-gc' '-rewrite-symbols' 
'-rpo-function-attrs' '-scalarize-masked-mem-intrin' '-scalarizer' '-sccp' '-separate-const-offset-from-gep'
'-simple-loop-unswitch' '-simplifycfg' '-sink' '-slsr' '-speculative-execution' 
'-sroa' '-strip' '-strip-dead-debug-info' '-strip-dead-prototypes' '-strip-debug-declare' 
'-strip-gc-relocates' '-strip-nondebug' '-strip-nonlinetable-debuginfo' '-structurizecfg' 
'-tailcallelim' '-tlshoist' '-transform-warning' '-unify-loop-exits' '-vector-combine' '-verify'
)

INPUT_BC="godot.bc"
OUTPUT_BC_BASE="${INPUT_BC%.bc}"
CSV_FILE="opt_times.csv"
ERROR_LOG="errors.log"
TIMEOUT_DURATION=300

echo "pass,real_time_seconds,status" > "$CSV_FILE"
: > "$ERROR_LOG"

for pass in "${all_passes[@]}"; do
    safe_pass=$(echo "$pass" | sed 's/^-//;s/[^a-zA-Z0-9]/_/g')
    output_file="${OUTPUT_BC_BASE}_${safe_pass}.bc"
    temp_input="temp_input_${safe_pass}.bc"
    log_file="time_${safe_pass}.log"

    echo ">> Running pass: $pass"

    # Copia fresca del .bc original
    cp "$INPUT_BC" "$temp_input"

    { 
        /usr/bin/time -f "%e" timeout $TIMEOUT_DURATION opt "$pass" "$temp_input" -o "$output_file" 
    } 2> "$log_file"
    exit_status=$?

    # Limpieza del .bc temporal de entrada
    rm -f "$temp_input"

    if [[ $exit_status -eq 0 ]]; then
        real_time=$(cat "$log_file")
        echo "$safe_pass,$real_time,ok" >> "$CSV_FILE"
    elif [[ $exit_status -eq 124 ]]; then
        echo "$safe_pass,$TIMEOUT_DURATION,timeout" >> "$CSV_FILE"
        echo "!! Pass $pass timed out" | tee -a "$ERROR_LOG"
        rm -f "$output_file"
    else
        echo "$safe_pass,,error" >> "$CSV_FILE"
        echo "!! Pass $pass failed (code $exit_status)" | tee -a "$ERROR_LOG"
        rm -f "$output_file"
    fi
done
