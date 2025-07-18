# ###
# NOTAS DE CARLOS
#
# ORIGEN: Javi, 2025-06-26
# DESTINO: TFM Godot
# MODIFICACIONES:
#   - El nombre del archivo (original: optimizationLLVMproblem.py)
#   - Refactorizado para quitar todo lo sobrante y hacer que se parezca al problema ZDT1 (el del ejemplo del GitHub)
#   - !!! USO CLANG++ EN VEZ DE CLANG (es lo que usa el scons en el compilado final)
# ###

from typing import List
import os
import shutil
import subprocess
import sys
import time # !!! DEBUG
import traceback    # !!! DEBUG
import json

from jmetal.core.problem import IntegerProblem
from jmetal.core.solution import IntegerSolution

from custom.jmetal.util import LlvmUtils

class GodotProblem(IntegerProblem):

    """
    Godot optimization problem using LLVM15; everything done sequentially. Parameters:
    :param n_passes_in_solution: Number of passes that represents any solution.
    :param godot_source_path: Path to the folder that contains the godot.bc AND huf_asm.o files.
    :param benchmark: Name of the benchmark in the godot-benchmarks project to use in the evaluations.
    :param benchmark_statistic: Name of the benchmark statistic to use in the evaluations (render_cpu, render_gpu, idle, physics or time).
    """
    def __init__(self, 
                 n_passes_in_solution: int,
                 godot_source_path: str,
                 opt_timeout: float,
                 clang_timeout: float,
                 benchmark: str,
                 benchmark_statistic: str,
                 benchmark_timeout: float,
    
    


                 max_evaluations: int = 25000,              
                 population_size : int = 30, offspring_population_size = int, verbose: bool = True,
                 jobid: str = "0",
                 dictionary_preloaded: bool = False, dictionary_name: str = 'dictionarys/llvm_dict_runtimes.data',
                 bc_directory : str = "clustered_benchmarks/clustering_benchmarks/1/bc/benchmarks_all/all.bc", runs : int = 3):
        
        self.obj_directions = [self.MINIMIZE]

        self.lower_bound = n_passes_in_solution * [0]
        self.upper_bound = n_passes_in_solution * [len(LlvmUtils.get_passes()) - 1]

        # Dictionary that contains elements coded like this:
        #   key: List of passes indexes that represents a solution that has already been evaluated
        #   value: Fitness value of said solution
        self.solutions_already_evaluated = dict()

        self.godot_source_path = godot_source_path
        self.godot_source_copy_path = godot_source_path + '_evaluate'
        self.opt_timeout = opt_timeout
        self.clang_timeout = clang_timeout
        self.benchmark = benchmark
        self.benchmark_statistic = benchmark_statistic
        self.benchmark_timeout = benchmark_timeout

        # self.llvm_utils = LlvmUtils(

        # )


        """

        # ID del trabajo
        self.jobid = jobid

        self.llvm = LlvmUtils(jobid=self.jobid,runs=runs, source = bc_directory)

        # Configuracion evaluations
        self.max_evaluations = max_evaluations
        self.evaluations = 0
        self.epoch = 1
        print('epoch {}'.format(self.epoch))

        self.phenotype = 0

        # Tamaño de la poblacion
        self.population_size = population_size

        # Numero de descendientes
        self.offspring_population_size = offspring_population_size


        self.dictionary = dict()
        self.verbose = verbose


        if dictionary_preloaded:
            LlvmUtils.fileToDictionary(dictionary_name,self.dictionary)

        """





    def number_of_objectives(self) -> int:
        return len(self.obj_directions)

    def number_of_variables(self) -> int:
        return len(self.lower_bound)

    def number_of_constraints(self) -> int:
        return 0

    def _copy_original_source(self) -> None:
        if os.path.exists(self.godot_source_copy_path):
            shutil.rmtree(self.godot_source_copy_path)
        shutil.copytree(self.godot_source_path, self.godot_source_copy_path)
    
    def _apply_opt_allinone(self, passes: str, input_filename: str, output_filename: str) -> bool:
        opt_command = ' '.join([
            f'opt',
            f'{passes}',
            f'"{self.godot_source_copy_path}/{input_filename}"',
            f'-o "{self.godot_source_copy_path}/{output_filename}"',
        ])
        opt_ok = True

        inicio = time.perf_counter()

        try:
            subprocess.run(
                opt_command, 
                shell=True, 
                timeout=self.opt_timeout, 
                check=True, 
                stderr=subprocess.STDOUT
            )
            # !!! LLVMUTILS USA LA OPCION (stderr=subprocess.PIPE) EN EL ALLINONE...
        except subprocess.SubprocessError as e:
            # !!! decidir si hacer algo mas
            opt_ok = False
            print('DEBUG --- OPT HA PETAO')
            print(e)
            # print(traceback.format_exc())
        # except subprocess.TimeoutExpired as e:
        #     cmd.kill()
        #     print('Error {}'.format(e),file=sys.stderr)
        #     print('Sentence: {}'.format(passes),file=sys.stderr)

        fin = time.perf_counter()
        duracion = fin - inicio
        print(f"Tiempo transcurrido en opt: {duracion:.4f} segundos")

        return opt_ok

    def _compile(self, input_filename: str, output_filename: str) -> bool:
        clang_command = ' '.join([
            f'clang++',
            f'-o "{self.godot_source_copy_path}/{output_filename}"',
            f'-O0',
            f'-fuse-ld=lld -flto=thin -static-libgcc -static-libstdc++ -s',
            f'"{self.godot_source_copy_path}/{input_filename}"',
            f'-lzstd -lpcre2-32 -lrt -lpthread -ldl -l:libatomic.a',
        ])
        compile_ok = True

        inicio = time.perf_counter()

        try:
            subprocess.run(
                clang_command, 
                shell=True, 
                timeout=self.clang_timeout, 
                check=True, 
                stderr=subprocess.STDOUT
            )
            # !!! LLVMUTILS USA LA OPCION (stderr=subprocess.PIPE) EN EL ALLINONE...
        except subprocess.SubprocessError as e:
            # !!! decidir si hacer algo mas
            compile_ok = False
            print('DEBUG --- CLANG HA PETAO')
            print(e)
            # print(traceback.format_exc())
        # except subprocess.TimeoutExpired as e:
        #     cmd.kill()
        #     print('Error {}'.format(e),file=sys.stderr)
        #     print('Sentence: {}'.format(passes),file=sys.stderr)

        fin = time.perf_counter()
        duracion = fin - inicio
        print(f"Tiempo transcurrido en clang: {duracion:.4f} segundos")

        return compile_ok

    def _run_benchmark(self, godot_binary_filename: str) -> bool:
        benchmark_ok = True

        for i in range(1, 6):
            json_path = f'{self.godot_source_copy_path}/run_{i}.json'

            benchmark_command = ' '.join([
                f'"{self.godot_source_copy_path}/{godot_binary_filename}"',
                '--',
                '--run-benchmarks',
                f'--include-benchmarks={self.benchmark}',
                f'--save-json="{json_path}"',
            ])

            attempt = 1
            success = False
            while attempt <= 3 and not success:
                try:
                    subprocess.run(
                        benchmark_command, 
                        cwd='/home/fedora/Carlos/godot-benchmarks',
                        shell=True, 
                        timeout=self.benchmark_timeout, 
                        check=True, 
                        stderr=subprocess.STDOUT
                    )
                    success = True
                except subprocess.SubprocessError as e:
                    # !!! decidir si hacer algo mas
                    attempt += 1
                    print('DEBUG --- BENCHMARK HA PETAO')
                    print(e)

            if not success:
                # !!! decidir si hacer algo mas
                benchmark_ok = False
                print('DEBUG --- BENCHMARK HA PETAO 3 VECES')
                break

        return benchmark_ok

    def get_worst_benchmark_value(self, benchmark_statistic: str) -> float | None:
        """
        Reads run_1.json to run_5.json in `base_path` and returns the worst (highest)
        value of the given benchmark_statistic found in the 'results' field.

        Parameters:
        - base_path: path where the JSON files are located
        - benchmark_statistic: the name of the statistic to compare (e.g., 'render_cpu')

        Returns:
        - The highest value found for that statistic, or None if no valid data is found
        """
        worst_value = float('-inf')

        for i in range(1, 6):
            json_path = f'{self.godot_source_copy_path}/run_{i}.json'
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    value = data['benchmarks'][0]['results'].get(benchmark_statistic)
                    if value is not None and value > worst_value:
                        worst_value = value
            except (FileNotFoundError, json.JSONDecodeError, KeyError, IndexError) as e:
                print(f'WARNING --- Failed to read {json_path}: {e}')

        return worst_value if worst_value != float('-inf') else None







    def _calculate_fitness_value(self, passes_indexes_list: List[int]) -> float:
        self._copy_original_source()
        
        # Apply the "full" opt command
        passes = ' '.join([LlvmUtils.get_passes()[i] for i in passes_indexes_list])
        input_filename = 'godot.bc'
        output_filename = 'godot_solution.bc'
        print(passes)
        opt_ok = self._apply_opt_allinone(passes, input_filename, output_filename)
        if not opt_ok:
            # Bad list of passes; applying them one by one is inviable in this problem, at least for now
            return sys.float_info.max    # !!! CONFIRMAR

        # Compile into a Godot binary
        input_filename = output_filename
        output_filename = 'godot_solution'
        compile_ok = self._compile(input_filename, output_filename)
        if not compile_ok:
            # Compiling went wrong for whatever reason
            return sys.float_info.max

        # Execute benchmark (wcase)
        benchmark_ok = self._run_benchmark(output_filename)
        if not benchmark_ok:
            # Benchmark went wrong for whatever reason
            return sys.float_info.max

        # Get worst runtime
        fitness_value = self.get_worst_benchmark_value(self.benchmark_statistic)
        if not fitness_value:
            # Reading the benchmark results went wrong for whatever reason
            return sys.float_info.max
        
        return fitness_value

    def evaluate(self, solution: IntegerSolution) -> IntegerSolution:
        # Avoid re-evaluating solutions
        passes_indexes_str = str(solution.variables)
        fitness_value = self.solutions_already_evaluated.get(passes_indexes_str)
        if not fitness_value:
            # fitness_value = 13   # !!! DEBUG
            # fitness_value = self.llvm.get_runtime_single(jobid=jobid, compiled=compiled)
            # fitness_value, deviation = self.llvm_utils.get_runtime(passes)
            fitness_value = self._calculate_fitness_value(solution.variables)
            self.solutions_already_evaluated.update({passes_indexes_str: fitness_value})
        print(f'DEBUG --- FITNESS: {fitness_value}')
        solution.objectives[0] = fitness_value
        return solution

    def evaluate_javi(self, solution: IntegerSolution, jobid : str,compiled : bool ) -> IntegerSolution:
        # solution: IntegerSolution = tupla_orig[0] 
        # jobid : str = tupla_orig[1]
        # compiled : bool = tupla_orig[2]
        # Para controlar qué individuo estamos evaluando
        self.phenotype +=1

        # Limite de individuos
        limit = [self.offspring_population_size if self.epoch != 1 else self.population_size]
        if self.phenotype%(limit[0]+1) == 0: # Si ha llegado al limite
            self.epoch += 1     # Siguiente epoch
            self.phenotype = 1  # Empieza 0 en fenotipo
            print("epoch {}".format(self.epoch))    # Nueva epoch
        # print("Limite " + str(limit) + " phen = " + str(self.phenotype))

        key = "{}".format(solution.variables)       # Secuencia de passes
        value = self.dictionary.get(key)            # Comprobar si ya se habia medido la secuencia de pases

        if value == None: # When the key is not in dictionary
            
            solution.objectives[0] = self.llvm.get_runtime_single(jobid=jobid, compiled= compiled)
            self.dictionary.update({key: solution.objectives[0]})       # Se añade al diccionario
            
        else: # When the key is in dictionary
            solution.objectives[0] = value
        # if self.verbose:
        #     # print("evaluated solution {:3} from epoch {:3} : variables = {}, fitness = {:>7}"\
        #     #       .format(self.phenotype,self.epoch,solution.variables,solution.objectives[0]))
        #     if self.phenotype == 1 and self.epoch == 1 :
        #         with open(f"solutions_{self.population_size}_{self.offspring_population_size}_{self.jobid}.data","w") as file:
        #             file.write("{} {} {} {}\n".format("epoch","iter","variables","fitness"))
        #     with open(f"solutions_{self.population_size}_{self.offspring_population_size}_{self.jobid}.data","a") as file:
        #         file.write("{:03} {:03} {} {}\n"\
        #            .format(self.epoch,self.phenotype,solution.variables,-solution.objectives[0]))
        return solution

    def name(self) -> str:
        return 'Godot Problem'



    """
    CARLOS: ESTO CREO QUE NO ME HACE FALTA

    def get_onebyone(self):
        return self.llvm.get_onebyone()

    ### FOR TERMINATION CRITERION ###
    def update(self, *args, **kwargs):
        self.evaluations = kwargs['EVALUATIONS']

    ### FOR TERMINATION CRITERION ###
    @property
    def is_met(self):
        met = self.evaluations >= self.max_evaluations
        if self.phenotype*self.epoch % 1 == 0 or met:
            if met:
                filename = "new_dictionary_{}_{}_{}_{}.data".format(self.population_size,
                            self.offspring_population_size, self.phenotype*self.epoch,
                            self.jobid)
            elif self.phenotype*self.epoch % 1 == 0:
                filename = "tmp_solutions_{}_{}_{}_{}.data".format(self.population_size,
                            self.offspring_population_size, self.phenotype*self.epoch,
                            self.jobid)
            LlvmUtils.dictionaryToFile(filename,self.dictionary)
        return met
    """