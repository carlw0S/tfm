import json
import os
import shutil
import subprocess
import sys
import time
from typing import List

from custom.jmetal.fitness_function import FitnessFunction
from custom.jmetal.util import LlvmUtils

"""
.. module:: godot_fitness_function
   :platform: Unix, Windows
   :synopsis: Fitness function for the Godot runtime optimization problem.
.. moduleauthor:: Carlos Benito-Jareño <carlos.benito@uca.es>
"""

class GodotRuntimeFitnessFunction(FitnessFunction):
    """
    Fitness function for the Godot runtime optimization problem.
    Calculates the fitness value based on the worst runtime of five executions of a benchmark.

    :param str godot_source_path: Path to the folder that contains the godot.bc file.
    :param float opt_timeout: Timeout for the optimization process (opt command).
    :param float clang_timeout: Timeout for the Clang compilation process.
    :param str benchmark: Name of the benchmark in the godot-benchmarks project to use in the evaluations.
    :param str benchmark_statistic: Name of the benchmark statistic to use in the evaluations (render_cpu, render_gpu, idle, physics or time).
    :param float benchmark_timeout: Timeout for one benchmark execution.
    """
    def __init__(self,
                 godot_source_path: str,
                 opt_timeout: float,
                 clang_timeout: float,
                 benchmark: str,
                 benchmark_statistic: str,
                 benchmark_timeout: float):
        super().__init__()
        self.godot_source_path = godot_source_path
        self.godot_source_copy_path = godot_source_path + '_evaluation'
        self.opt_timeout = opt_timeout
        self.clang_timeout = clang_timeout
        self.benchmark = benchmark
        self.benchmark_statistic = benchmark_statistic
        self.benchmark_timeout = benchmark_timeout

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

        start = time.perf_counter()    # !!! DEBUG?

        try:
            subprocess.run(
                opt_command, 
                shell=True, 
                timeout=self.opt_timeout, 
                check=True, 
                stderr=subprocess.STDOUT
            )
        except subprocess.SubprocessError as e:
            opt_ok = False

        finish = time.perf_counter()
        duration = finish - start
        print(f"Tiempo transcurrido en opt: {duration:.4f} segundos")

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

        start = time.perf_counter()

        try:
            subprocess.run(
                clang_command, 
                shell=True, 
                timeout=self.clang_timeout, 
                check=True, 
                stderr=subprocess.STDOUT
            )
        except subprocess.SubprocessError as e:
            compile_ok = False

        finish = time.perf_counter()
        duration = finish - start
        print(f"Tiempo transcurrido en clang: {duration:.4f} segundos")

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
                        cwd='/home/fedora/Carlos/godot-benchmarks', # !!! CUIDAO CON ESTA RUTA
                        shell=True, 
                        timeout=self.benchmark_timeout, 
                        check=True, 
                        stderr=subprocess.STDOUT
                    )
                    success = True
                except subprocess.SubprocessError as e:
                    attempt += 1
                    print('DEBUG --- BENCHMARK HA PETAO')
                    print(e)

            if not success:
                benchmark_ok = False
                break

        return benchmark_ok

    def _get_worst_benchmark_value(self, benchmark_statistic: str) -> float | None:
        """
        Reads run_1.json to run_5.json in and returns the worst (highest)
        value of the given benchmark_statistic found in the 'results' field.

        :param benchmark_statistic: The statistic to look for in the benchmark results (e.g., 'render_cpu').
        :return worst_value: The worst value found for the given benchmark_statistic, or None if no valid values were found.
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
        print(passes)   # !!! DEBUG
        opt_ok = self._apply_opt_allinone(passes, input_filename, output_filename)
        if not opt_ok:
            # Bad list of passes; applying them one by one is not viable in this problem, at least for now
            print('DEBUG --- OPT HA PETAO')
            return sys.float_info.max

        # Compile into a Godot binary
        input_filename = output_filename
        output_filename = 'godot_solution.out'
        compile_ok = self._compile(input_filename, output_filename)
        if not compile_ok:
            # Compiling went wrong for whatever reason
            print('DEBUG --- CLANG HA PETAO')
            return sys.float_info.max

        # Execute benchmark (wcase)
        benchmark_ok = self._run_benchmark(output_filename)
        if not benchmark_ok:
            # Benchmark went wrong for whatever reason
            print('DEBUG --- BENCHMARK HA PETAO 3 VECES')
            return sys.float_info.max

        # Get worst runtime
        fitness_value = self._get_worst_benchmark_value(self.benchmark_statistic)
        if not fitness_value:
            # Reading the benchmark results went wrong for whatever reason
            return sys.float_info.max
        
        return fitness_value

    def calculate(self, solution_variables: List[int]) -> float:
        return self._calculate_fitness_value(solution_variables)

    def name(self) -> str:
        return "Godot Runtime Fitness Function"