# ###
# NOTAS DE CARLOS
#
# ORIGEN: Josemi, 2025-06-26
# DESTINO: TFM Godot
# MODIFICACIONES:
#   - Adaptados los import de IntervalUtils e IntervalValue
#   - HE HECHO UNA CRIBA A MEDIDA QUE TENGO QUE DOCUMENTAR !!!
# ###

# v4 version
# minor issues fixed


import os
import subprocess
import time
import random
from shutil import copy as copyfile
import sys
import numpy as np
from typing import Union

from custom.jmetal.util.IntervalUtilsV1 import IntervalUtils
from custom.jmetal.util.IntervalValueV1 import IntervalValue

class LlvmUtils():
    '''
    llvmpath = llvm path
    basepath = work path
    bechmark = benchmark folder name, has to be in work path
    generator = script to merge all benchmark suite
    source = name for benchmark IR code
    runs = how many times should the benchmark be run
    jobid = job identifier code
    '''

    def __init__(self, llvmpath: str = "", basepath: str = "./", benchmark: str = "polybench_small",
                 generator: str = "original_merged_generator.sh", source: str = "polybench_small_original.bc",
                 runs: int = 1, worstruns: int = 1, jobid: str = "", useperf : bool = False, useinterval: bool = False, n_iterations: int = 500,
                 significance_level: int = 5, usedelay: bool = False, usenuma: bool = False, useworstcase: bool = False):
        self.llvmpath = llvmpath
        self.basepath = basepath
        self.benchmark = benchmark
        self.generator = generator
        self.source = source
        self.runs = runs
        self.worstruns = worstruns
        self.jobid = jobid
        self.onebyones = 0
        self.useperf = useperf
        self.useinterval = useinterval
        self.n_iterations = n_iterations
        self.significance_level = significance_level
        self.usedelay = usedelay
        self.useworstcase = useworstcase
        if usenuma:
            self.usenuma = "taskset -c 72-95"
        else:
            self.usenuma = ""

    @staticmethod
    def get_passes() -> list:
        all_passes = [
            "-aa",
            "-adce",
            "-add-discriminators",
            "-aggressive-instcombine",
            "-alignment-from-assumptions",
            "-always-inline",
            "-annotation-remarks",
            "-annotation2metadata",
            "-assume-builder",
            "-assume-simplify",
            "-atomic-expand",
            "-basic-aa",
            "-bdce",
            "-block-freq",
            "-bounds-checking",
            "-branch-prob",
            "-break-crit-edges",
            "-called-value-propagation",
            "-callsite-splitting",
            "-canon-freeze",
            "-cfl-anders-aa",
            "-cfl-steens-aa",
            "-codegenprepare",
            "-consthoist",
            "-constmerge",
            "-constraint-elimination",
            "-correlated-propagation",
            "-cost-model",
            "-cross-dso-cfi",
            "-cycles",
            "-da",
            "-dce",
            "-deadargelim",
            "-demanded-bits",
            "-dfa-jump-threading",
            "-dfsan",
            "-div-rem-pairs",
            "-divergence",
            "-domfrontier",
            "-domtree",
            "-dse",
            "-dwarfehprepare",
            "-early-cse",
            "-early-cse-memssa",
            "-elim-avail-extern",
            "-expand-reductions",
            "-expandmemcmp",
            "-expandvp",
            "-extract-blocks",
            "-flattencfg",
            "-float2int",
            "-forceattrs",
            "-function-attrs",
            "-function-specialization",
            "-global-merge",
            "-globaldce",
            "-globalopt",
            "-globals-aa",
            "-globalsplit",
            "-guard-widening",
            "-gvn",
            "-gvn-hoist",
            "-gvn-sink",
            "-hardware-loops",
            "-hotcoldsplit",
            "-indirectbr-expand",
            "-indvars",
            "-infer-address-spaces",
            "-inferattrs",
            "-inject-tli-mappings",
            "-inline",
            "-instcombine",
            "-instsimplify",
            "-interleaved-access",
            "-interleaved-load-combine",
            "-internalize",
            "-ipsccp",
            "-irce",
            "-iv-users",
            "-jmc-instrument",
            "-jump-threading",
            "-lazy-value-info",
            "-lcssa",
            "-libcalls-shrinkwrap",
            "-licm",
            "-lint",
            "-load-store-vectorizer",
            "-loop-data-prefetch",
            "-loop-deletion",
            "-loop-distribute",
            "-loop-extract",
            "-loop-extract-single",
            "-loop-flatten",
            "-loop-fusion",
            "-loop-idiom",
            "-loop-instsimplify",
            "-loop-interchange",
            "-loop-load-elim",
            "-loop-predication",
            "-loop-reduce",
            "-loop-reroll",
            "-loop-rotate",
            "-loop-simplify",
            "-loop-simplifycfg",
            "-loop-sink",
            "-loop-unroll",
            "-loop-unroll-and-jam",
            "-loop-vectorize",
            "-loop-versioning",
            "-loop-versioning-licm",
            "-loops",
            "-lower-constant-intrinsics",
            "-lower-expect",
            "-lower-global-dtors",
            "-lower-guard-intrinsic",
            "-lower-matrix-intrinsics",
            "-lower-matrix-intrinsics-minimal",
            "-lower-widenable-condition",
            "-loweratomic",
            "-lowerinvoke",
            "-lowerswitch",
            "-make-guards-explicit",
            "-mem2reg",
            "-memcpyopt",
            "-memdep",
            "-memoryssa",
            "-memprof",
            "-memprof-module",
            "-mergefunc",
            "-mergeicmps",
            "-mergereturn",
            "-metarenamer",
            "-mldst-motion",
            "-nary-reassociate",
            "-newgvn",
            "-openmp-opt-cgscc",
            "-partial-inliner",
            "-partially-inline-libcalls",
            "-phi-values",
            "-postdomtree",
            "-reassociate",
            "-redundant-dbg-inst-elim",
            "-reg2mem",
            "-regions",
            "-replace-with-veclib",
            "-rewrite-statepoints-for-gc",
            "-rewrite-symbols",
            "-rpo-function-attrs",
            "-safe-stack",
            "-scalar-evolution",
            "-scalarize-masked-mem-intrin",
            "-scalarizer",
            "-sccp",
            "-scev-aa",
            "-scoped-noalias-aa",
            "-select-optimize",
            "-separate-const-offset-from-gep",
            "-simple-loop-unswitch",
            "-simplifycfg",
            "-sink",
            "-sjljehprepare",
            "-slp-vectorizer",
            "-slsr",
            "-speculative-execution",
            "-sroa",
            "-stack-safety",
            "-stack-safety-local",
            "-strip",
            "-strip-dead-debug-info",
            "-strip-dead-prototypes",
            "-strip-debug-declare",
            "-strip-gc-relocates",
            "-strip-nondebug",
            "-strip-nonlinetable-debuginfo",
            "-structurizecfg",
            "-tailcallelim",
            "-targetlibinfo",
            "-tbaa",
            "-tlshoist",
            "-transform-warning",
            "-type-promotion",
            "-unreachableblockelim",
            "-vector-combine",
            "-verify",
            "-verify-safepoint-ir",
            "-x86-partial-reduction",
            ""
        ]

        return all_passes

    """
    @staticmethod
    def get_passes() -> list:
        all_passes = ['-aa','-atomic-expand','-basic-aa','-block-freq','-branch-prob','-cfl-anders-aa','-cfl-steens-aa',
                      '-codegenprepare','-cost-model','-cycles','-da','-demanded-bits','-divergence','-domfrontier','-domtree',
                      '-dwarfehprepare','-early-cse-memssa','-expand-reductions','-expandmemcmp','-expandvp',
                      '-global-merge','-globals-aa','-hardware-loops','-hexagon-loop-idiom','-hexagon-vc','-hexagon-vlcr',
                      '-indirectbr-expand','-interleaved-access','-interleaved-load-combine','-iv-users','-jmc-instrument',
                      '-lazy-value-info','-loop-extract-single','-loops','-lower-amx-intrinsics','-lower-amx-type',
                      '-lower-matrix-intrinsics-minimal','-memdep','-memoryssa','-mve-tail-predication','-objc-arc-aa',
                      '-phi-values', '-postdomtree','-pre-amx-config', '-pre-isel-intrinsic-lowering','-regions','-replace-with-veclib', '-safe-stack',
                      '-scalar-evolution','-scev-aa','-scoped-noalias-aa','-select-optimize','-si-annotate-control-flow','-sjljehprepare',
                      '-stack-safety','-stack-safety-local','-systemz-tdc','-targetlibinfo','-tbaa','-type-promotion','-unreachableblockelim',
                      '-verify-safepoint-ir','-wasm-add-missing-prototypes','-wasm-fix-function-bitcasts','-wasm-lower-em-ehsjlj',
                      '-wasm-mclower-prepass','-wasm-optimize-returned','-wasmehprepare','-winehprepare', '-adce', '-add-discriminators', '-aggressive-instcombine', '-alignment-from-assumptions', 
                      '-always-inline', '-annotation-remarks', '-annotation2metadata', '-assume-builder', '-assume-simplify',
                      '-bdce', '-bounds-checking', '-break-crit-edges', '-called-value-propagation',
                      '-callsite-splitting', '-canon-freeze','-consthoist', '-constmerge', '-constraint-elimination',
                      '-correlated-propagation', '-cross-dso-cfi', '-dce', '-deadargelim', '-dfa-jump-threading', '-div-rem-pairs',
                      '-dse', '-early-cse', '-elim-avail-extern', '-extract-blocks', '-fix-irreducible', '-flattencfg', '-float2int', 
                      '-forceattrs', '-function-attrs', '-function-specialization', '-globaldce', '-globalopt', '-globalsplit', '-guard-widening',
                      '-gvn', '-gvn-hoist', '-gvn-sink', '-hotcoldsplit', '-indvars', '-infer-address-spaces', '-inferattrs', '-inject-tli-mappings',
                      '-inline', '-instcombine', '-instcount', '-instnamer', '-instsimplify', '-ipsccp', '-irce', '-iroutliner',
                      '-jump-threading', '-lcssa', '-libcalls-shrinkwrap', '-load-store-vectorizer', '-loop-data-prefetch', 
                      '-loop-deletion', '-loop-distribute', '-loop-extract', '-loop-flatten', '-loop-fusion', '-loop-idiom', '-loop-instsimplify', 
                      '-loop-interchange', '-loop-load-elim', '-loop-predication', '-loop-reduce', '-loop-reroll', '-loop-rotate', '-loop-simplify', 
                      '-loop-simplifycfg', '-loop-sink', '-loop-unroll', '-loop-unroll-and-jam', '-loop-vectorize', '-loop-versioning', 
                      '-lower-constant-intrinsics', '-lower-expect', '-lower-global-dtors', '-lower-guard-intrinsic',
                      '-lower-matrix-intrinsics', '-lower-widenable-condition', '-loweratomic', '-lowerinvoke', '-lowerswitch', '-make-guards-explicit',
                      '-mem2reg', '-memcpyopt', '-mergefunc', '-mergeicmps', '-mergereturn', '-mldst-motion', 
                      '-nary-reassociate', '-newgvn', '-objc-arc', '-objc-arc-apelim', '-objc-arc-contract', '-objc-arc-expand',
                      '-partial-inliner', '-partially-inline-libcalls', '-reassociate', '-redundant-dbg-inst-elim', '-reg2mem', '-rewrite-statepoints-for-gc', '-rewrite-symbols', 
                      '-rpo-function-attrs', '-scalarize-masked-mem-intrin', '-scalarizer', '-sccp', '-separate-const-offset-from-gep',
                      '-simple-loop-unswitch', '-simplifycfg', '-sink', '-slsr', '-speculative-execution', 
                      '-sroa', '-strip', '-strip-dead-debug-info', '-strip-dead-prototypes', '-strip-debug-declare', 
                      '-strip-gc-relocates', '-strip-nondebug', '-strip-nonlinetable-debuginfo', '-structurizecfg', 
                      '-tailcallelim', '-tlshoist', '-transform-warning', '-unify-loop-exits', '-vector-combine', '-verify',""]
        return all_passes
    """

    # To convert the original benchmark into LLVM IR
    def benchmark_link(self) -> None:
        os.chdir("{}{}/".format(self.basepath,self.benchmark))
        os.system("./{} {}".format(self.generator,self.llvmpath))
        copyfile("{}".format(self.source),"../{}".format(self.source))
        os.chdir("../")

    # To get the runtime
    def get_runtime(self,passes: str = "-O3") -> Union[float, IntervalValue]:
        if (os.path.exists("{}optimized_{}.bc".format(self.basepath,self.jobid))):
            os.remove("{}optimized_{}.bc".format(self.basepath,self.jobid))
        copyfile("{}{}".format(self.basepath,self.source),"{}optimized_{}.bc".format(self.basepath,self.jobid))
        # os.system("ls")
        median = 0.0
        desviation = None
        if self.toIR(passes):
            os.system("{}clang-15 -lm -O0 -Wno-everything -disable-llvm-optzns -disable-llvm-passes {}".format(
                       self.llvmpath,"-Xclang -disable-O0-optnone {}optimized_{}.bc -o {}exec_{}.o".format(
                       self.basepath,self.jobid,self.basepath,self.jobid)))
            if self.useperf:
                runtimes = []
                if self.usedelay:
                    for i in range(self.runs):
                        cmd = subprocess.check_output("{} {}runtimes.sh {}exec_{}.o 1".format(
                                self.usenuma, self.basepath,self.basepath,self.jobid),shell=True)
                        if i==0:
                            runtimes = np.array(cmd.decode("utf-8")[:-1].split(","),dtype=float)
                        else:
                            runtimes = np.concatenate((runtimes,np.array(cmd.decode("utf-8")[:-1].split(","),dtype=float)),axis=0)

                        time.sleep(random.randint(1,3))
                else:
                    cmd = subprocess.Popen(["bash", "runtimes.sh", f"exec_{self.jobid}.o", str(self.runs)],
                            stdout=subprocess.PIPE)
                    out, err = cmd.communicate()
                    if cmd.returncode == 0:
                        runtimes = np.array(out.decode("utf-8")[:-1].split(","),dtype=float)
                    else:
                        runtimes = np.array([sys.maxsize])
                if self.useinterval:
                    if self.useworstcase:
                        sorted_runtimes = runtimes[np.argsort(runtimes)]
                        median = IntervalUtils.make_interval(runtimes = sorted_runtimes[-self.worstruns:], n_iterations = self.n_iterations
                         ,significance_level = self.significance_level)
                    else:
                        median = IntervalUtils.make_interval(runtimes = runtimes, n_iterations = self.n_iterations
                             ,significance_level = self.significance_level)
                        desviation = np.std(runtimes)
                elif self.useworstcase:
                    median = np.amax(runtimes)
                    deviation = np.std(runtimes)
                else:
                    median = np.median(runtimes)
                    desviation = np.std(runtimes)
                    #print("median : {}".format(median))
                    #exit(1)
            else:
                array = []
                if self.usedelay:
                    for _ in range(self.runs):
                        start_time = time.time()
                        p = subprocess.Popen([f'./exec_{self.jobid}.o'])
                        try:
                            p.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            p.kill()
                        array.append(time.time() - start_time)
                        time.sleep(random.randint(1,3))
                else:
                    for _ in range(self.runs):
                        start_time = time.time()
                        p = subprocess.Popen([f'./exec_{self.jobid}.o'])
                        try:
                            p.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            p.kill()
                        array.append(time.time() - start_time)
                if self.useinterval:
                    if self.worstcase:
                        runtimes = np.array(array)
                        sorted_runtimes = runtimes[np.argsort(runtimes)]
                        median = IntervalUtils.make_interval(runtimes = sorted_runtimes[-self.worstruns:], n_iterations = self.n_iterations
                         ,significance_level = self.significance_level)
                    else:
                        median = IntervalUtils.make_interval(runtimes = np.array(array), n_iterations = self.n_iterations
                             ,significance_level = self.significance_level)
                        desviation = np.std(np.array(array))
                elif self.useworstcase:
                    median = np.amax(np.array(array))
                    desviation = np.std(np.array(array))
                else:
                    median = np.median(np.array(array))
                    desviation = np.std(np.array(array))
        else:
            median = sys.maxsize
        return median, desviation

    # To get the number of lines of code
    def get_codelines(self,passes: str = '-O3',source: str = "optimized.bc",
                  output: str = "optimized.ll") -> int:
        source = "{}{}".format(self.basepath,source.replace(".bc","_{}.bc".format(self.jobid)))
        output = "{}{}".format(self.basepath,output.replace(".bc","_{}.bc".format(self.jobid)))
        if self.toIR(passes):
            self.toAssembly()
            with open("{}optimized_{}.ll".format(self.basepath,self.jobid),'r') as file:
                result = -len(file.readlines())
        else:
            result = 0
        return result

    # To apply transformations
    def toIR(self, passes: str = '-O3') -> bool:
        if (os.path.exists("{}optimized_{}.bc".format(self.basepath,self.jobid))):
            os.remove("{}optimized_{}.bc".format(self.basepath,self.jobid))
        copyfile("{}{}".format(self.basepath,self.source),"{}optimized_{}.bc".format(self.basepath,self.jobid))
        cmd = subprocess.Popen("{}opt-15 {} {}optimized_{}.bc -o {}optimized_{}.bc".format(
                                    self.llvmpath, "-polly-canonicalize", self.basepath,self.jobid,
                                    self.basepath,self.jobid),shell=True)
        try:
            cmd.wait(timeout=20)
        except subprocess.TimeoutExpired as e:
            cmd.kill()
            print('Error {}'.format(e),file=sys.stderr)
            print('Sentence: {}'.format(passes),file=sys.stderr)

        result = self.allinone(passes)
        if not result:
            copyfile("{}{}".format(self.basepath,self.source),"{}optimized_{}.bc".format(self.basepath,self.jobid))
            result = self.onebyone(passes)
        return result

    # To transform from LLVM IR to assembly code
    def toAssembly(self, source: str = "optimized.bc", output: str = "optimized.ll"):
        source = "{}{}".format(self.basepath,source.replace(".bc","_{}.bc".format(self.jobid)))
        output = "{}{}".format(self.basepath,output.replace(".ll","_{}.ll".format(self.jobid)))
        os.system("{}llc {}{} -o {}{}".format(self.llvmpath,
                  self.basepath,source,self.basepath,output))

    # To apply transformations in one line
    def allinone(self, passes: str = '-O3') -> bool:
        result = True
        #print("{}opt-15 {} {}optimized_{}.bc -o {}optimized_{}.bc".format(
        #                        self.llvmpath,passes,self.basepath,self.jobid,self.basepath,
        #                        self.jobid))
        cmd = subprocess.Popen("timeout 20 {}opt-15 {} {}optimized_{}.bc -o {}optimized_{}.bc".format(
                                self.llvmpath,passes,self.basepath,self.jobid,self.basepath,
                                self.jobid),shell=True, stderr = subprocess.PIPE)
        try:
            cmd.wait(timeout=20)
            if cmd.returncode != 0:
                result = False
        except subprocess.TimeoutExpired as e:
            cmd.kill()
            print('Error {}'.format(e),file=sys.stderr)
            print('Sentence: {}'.format(passes),file=sys.stderr)
            result = False
        return result

    # To apply transformations one by one
    def onebyone(self, passes: str = '-O3') -> bool:
        result = True
        passeslist = passes.split(' ')
        self.onebyones += 1

        for llvm_pass in passeslist:
            #print("{}opt-15 {} {}optimized_{}.bc -o {}optimized_{}.bc".format(
            #                        self.llvmpath,llvm_pass, self.basepath,self.jobid,
            #                        self.basepath,self.jobid))
            cmd = subprocess.Popen("timeout 5 {}opt-15 {} {}optimized_{}.bc -o {}optimized_{}.bc".format(
                                    self.llvmpath,llvm_pass, self.basepath,self.jobid,
                                    self.basepath,self.jobid),shell=True)
            try:
                cmd.wait(timeout=5)
                if cmd.returncode != 0:
                    result = False
            except subprocess.TimeoutExpired as e:
                cmd.kill()
                print('Error {}'.format(e),file=sys.stderr)
                print('Sentence: {}'.format(passes),file=sys.stderr)
                result = False
        return result

    # To get the number of time onebyone is run
    def get_onebyone(self):
        return self.onebyones

    # To add a file to the output file
    @staticmethod
    def mergeDict(input_: str,output_: str):
        dic = dict()
        LlvmUtils.fileToDictionary(input_,dic)
        LlvmUtils.fileToDictionary(output_,dic)
        LlvmUtils.dictionaryToFile(output_,dic)

    # File to dictionary
    @staticmethod
    def fileToDictionary(input_: str, dic: list):
        with open(input_,"r") as file:
                lines = file.readlines()
                for line in lines:
                    index = line.rfind(',')
                    key = "["+"{}".format(line[:index])+"]"
                    value = "{}".format(line[index+1:])[:-1]
                    dic.update({key: value})

    # Dictionary to file
    @staticmethod
    def dictionaryToFile(filename: str, dic: list):
        with open(filename,"w") as file:
                for keys,values in dic.items():
                    key = '{}'.format(keys).replace("[","").replace("]","")
                    key = '{}'.format(key).replace(", ",",")
                    file.write('{},{}\n'.format(key,values))

    # To encode file from passes to integers
    @staticmethod
    def encode(input_: str, output_: str):
        with open(input_,'r') as inputfile:
            lines = inputfile.readlines()
            with open(output_,'w') as ouputfile:
                for line in lines:
                    index = line.rfind(',')
                    keys = "{}".format(line[:index]).split(",")
                    value = "{}".format(line[index+1:])[:-1]
                    newkey = ""
                    for key in keys:
                        newkey += '{},'.format(LlvmUtils.get_passes().index(key))
                    ouputfile.write('{}{}\n'.format(newkey,value))

    # To decode file from integers to passes
    @staticmethod
    def decode(input_: str,output_: str):
        with open(input_,'r') as inputfile:
            lines = inputfile.readlines()
            with open(output_,'w') as ouputfile:
                for line in lines:
                    index = line.rfind(',')
                    keys = "{}".format(line[:index]).split(",")
                    value = "{}".format(line[index+1:])[:-1]
                    newkey = ""
                    for key in keys:
                        newkey += '{},'.format(LlvmUtils.get_passes()[int(key)])
                    ouputfile.write('{}{}\n'.format(newkey,value))
