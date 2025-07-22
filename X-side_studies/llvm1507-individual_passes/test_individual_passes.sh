#!/bin/bash

# Lista de passes
all_passes=(
'-aa' '-aa-eval' '-adce' '-add-discriminators' '-aggressive-instcombine' '-alignment-from-assumptions' '-always-inline' '-annotation-remarks' '-annotation2metadata' '-assume-builder' '-assume-simplify' '-assumption-cache-tracker' '-atomic-expand' '-attributor' '-attributor-cgscc' '-barrier' '-basic-aa' '-basiccg' '-bbsections-profile-reader' '-bdce' '-block-freq' '-bounds-checking' '-branch-prob' '-break-crit-edges' '-called-value-propagation' '-callsite-splitting' '-canon-freeze' '-cfl-anders-aa' '-cfl-steens-aa' '-check-debugify' '-check-debugify-function' '-codegenprepare' '-consthoist' '-constmerge' '-constraint-elimination' '-correlated-propagation' '-cost-model' '-cross-dso-cfi' '-cseinfo' '-cycles' '-da' '-dce' '-deadargelim' '-deadargha' '-debugify' '-debugify-function' '-delinearize' '-demanded-bits' '-dfa-jump-threading' '-dfsan' '-div-rem-pairs' '-divergence' '-domfrontier' '-domtree' '-dot-callgraph' '-dot-cfg' '-dot-cfg-only' '-dot-dom' '-dot-dom-only' '-dot-postdom' '-dot-postdom-only' '-dot-regions' '-dot-regions-only' '-dot-scops' '-dot-scops-only' '-dse' '-dwarfehprepare' '-early-cse' '-early-cse-memssa' '-edge-bundles' '-elim-avail-extern' '-expand-reductions' '-expandmemcmp' '-expandvp' '-external-aa' '-extract-blocks' '-fastpretileconfig' '-fasttileconfig' '-fix-irreducible' '-flattencfg' '-float2int' '-forceattrs' '-function-attrs' '-function-specialization' '-gisel-known-bits' '-global-merge' '-globaldce' '-globalopt' '-globals-aa' '-globalsplit' '-guard-widening' '-gvn' '-gvn-hoist' '-gvn-sink' '-hardware-loops' '-hotcoldsplit' '-indirectbr-expand' '-indvars' '-infer-address-spaces' '-inferattrs' '-inject-tli-mappings' '-inline' '-instcombine' '-instcount' '-instnamer' '-instruction-select' '-instsimplify' '-interleaved-access' '-interleaved-load-combine' '-internalize' '-intervals' '-ipsccp' '-ir-similarity-identifier' '-irce' '-iroutliner' '-irtranslator' '-iv-users' '-jmc-instrument' '-jump-threading' '-lazy-block-freq' '-lazy-branch-prob' '-lazy-value-info' '-lcssa' '-lcssa-verification' '-legalizer' '-libcalls-shrinkwrap' '-licm' '-lint' '-load-store-vectorizer' '-loadstore-opt' '-localizer' '-loop-accesses' '-loop-data-prefetch' '-loop-deletion' '-loop-distribute' '-loop-extract' '-loop-extract-single' '-loop-flatten' '-loop-fusion' '-loop-guard-widening' '-loop-idiom' '-loop-instsimplify' '-loop-interchange' '-loop-load-elim' '-loop-predication' '-loop-reduce' '-loop-reroll' '-loop-rotate' '-loop-simplify' '-loop-simplifycfg' '-loop-sink' '-loop-unroll' '-loop-unroll-and-jam' '-loop-vectorize' '-loop-versioning' '-loop-versioning-licm' '-loops' '-lower-amx-intrinsics' '-lower-amx-type' '-lower-constant-intrinsics' '-lower-expect' '-lower-global-dtors' '-lower-guard-intrinsic' '-lower-matrix-intrinsics' '-lower-matrix-intrinsics-minimal' '-lower-widenable-condition' '-loweratomic' '-lowerinvoke' '-lowerswitch' '-lowertilecopy' '-machine-block-freq' '-machine-branch-prob' '-machine-domfrontier' '-machine-loops' '-machinedomtree' '-make-guards-explicit' '-mem2reg' '-memcpyopt' '-memdep' '-memoryssa' '-memprof' '-memprof-module' '-mergefunc' '-mergeicmps' '-mergereturn' '-metarenamer' '-mldst-motion' '-module-debuginfo' '-module-summary-analysis' '-module-summary-info' '-nary-reassociate' '-newgvn' '-objc-arc' '-objc-arc-aa' '-objc-arc-apelim' '-objc-arc-contract' '-objc-arc-expand' '-openmp-opt-cgscc' '-opt-remark-emitter' '-pa-eval' '-partial-inliner' '-partially-inline-libcalls' '-phi-values' '-place-backedge-safepoints-impl' '-place-safepoints' '-polly-ast' '-polly-canonicalize' '-polly-cleanup' '-polly-codegen' '-polly-dce' '-polly-delicm' '-polly-dependences' '-polly-detect' '-polly-dump-module' '-polly-export-jscop' '-polly-flatten-schedule' '-polly-function-dependences' '-polly-function-scops' '-polly-import-jscop' '-polly-mse' '-polly-opt-isl' '-polly-optree' '-polly-prepare' '-polly-print-ast' '-polly-print-delicm' '-polly-print-dependences' '-polly-print-detect' '-polly-print-flatten-schedule' '-polly-print-function-dependences' '-polly-print-function-scops' '-polly-print-import-jscop' '-polly-print-opt-isl' '-polly-print-optree' '-polly-print-scops' '-polly-print-simplify' '-polly-prune-unprofitable' '-polly-scop-inliner' '-polly-scops' '-polly-simplify' '-polyhedral-info' '-postdomtree' '-pre-amx-config' '-pre-isel-intrinsic-lowering' '-print-alias-sets' '-print-callgraph' '-print-callgraph-sccs' '-print-cfg-sccs' '-print-dom-info' '-print-externalfnconstants' '-print-function' '-print-lazy-value-info' '-print-memdeps' '-print-memderefs' '-print-memoryssa' '-print-module' '-print-must-be-executed-contexts' '-print-mustexecute' '-print-polyhedral-info' '-print-predicateinfo' '-profile-summary-info' '-prune-eh' '-pseudo-probe-inserter' '-reaching-deps-analysis' '-reassociate' '-redundant-dbg-inst-elim' '-reg2mem' '-regbankselect' '-regions' '-replace-with-veclib' '-rewrite-statepoints-for-gc' '-rewrite-symbols' '-rpo-function-attrs' '-safe-stack' '-scalar-evolution' '-scalarize-masked-mem-intrin' '-scalarizer' '-sccp' '-scev-aa' '-scoped-noalias-aa' '-select-optimize' '-separate-const-offset-from-gep' '-simple-loop-unswitch' '-simplifycfg' '-sink' '-sjljehprepare' '-slp-vectorizer' '-slsr' '-speculative-execution' '-sroa' '-stack-protector' '-stack-safety' '-stack-safety-local' '-strip' '-strip-dead-debug-info' '-strip-dead-prototypes' '-strip-debug-declare' '-strip-gc-relocates' '-strip-nondebug' '-strip-nonlinetable-debuginfo' '-structurizecfg' '-tailcallelim' '-targetlibinfo' '-targetpassconfig' '-tbaa' '-tileconfig' '-tilepreconfig' '-tlshoist' '-transform-warning' '-tti' '-type-promotion' '-unify-loop-exits' '-unreachableblockelim' '-vector-combine' '-verify' '-verify-safepoint-ir' '-view-callgraph' '-view-cfg' '-view-cfg-only' '-view-dom' '-view-dom-only' '-view-postdom' '-view-postdom-only' '-view-regions' '-view-regions-only' '-view-scops' '-view-scops-only' '-virtregmap' '-wasmehprepare' '-winehprepare' '-write-bitcode' '-x86-avoid-' '-x86-avoid-trailing-call' '-x86-cf-opt' '-x86-cmov-conversion' '-x86-codegen' '-x86-domain-reassignment' '-x86-evex-to-vex-compress' '-x86-execution-domain-fix' '-x86-fixup-' '-x86-fixup-bw-insts' '-x86-fixup-setcc' '-x86-flags-copy-lowering' '-x86-lvi-load' '-x86-lvi-ret' '-x86-optimize-' '-x86-partial-reduction' '-x86-pseudo' '-x86-return-thunks' '-x86-seses' '-x86-slh' '-x86-winehstate'
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
