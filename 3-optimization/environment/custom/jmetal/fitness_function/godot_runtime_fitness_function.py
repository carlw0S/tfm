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
    :param str godot_benchmarks_repo_path: Path to the godot-benchmarks repository.
    :param str timestamp: Timestamp of the current execution for fitness stats output file.
    """
    def __init__(self,
                 godot_source_path: str,
                 opt_timeout: float,
                 clang_timeout: float,
                 benchmark: str,
                 benchmark_statistic: str,
                 benchmark_timeout: float,
                 godot_benchmarks_repo_path: str,
                 timestamp: str):
        super().__init__()
        self.godot_source_path = godot_source_path
        self.godot_source_copy_path = godot_source_path + '_evaluation'
        self.opt_timeout = opt_timeout
        self.clang_timeout = clang_timeout
        self.benchmark = benchmark
        self.benchmark_statistic = benchmark_statistic
        self.benchmark_timeout = benchmark_timeout
        self.godot_benchmarks_repo_path = godot_benchmarks_repo_path

        self.godot_raw_bitcode_filename = 'godot.bc'
        self.godot_optimized_bitcode_filename = 'godot_solution.bc'
        self.godot_binary_filename = 'godot_solution.out'

        self.stats = dict()
        self.stats_file = f'./data/fitness/stats/fitness_stats-{timestamp}.json'

    def _copy_original_source(self) -> None:
        if os.path.exists(self.godot_source_copy_path):
            shutil.rmtree(self.godot_source_copy_path)
        shutil.copytree(self.godot_source_path, self.godot_source_copy_path)

    def _run_command(self, command: str, timeout: float, attempts: int = 1, cwd: str = None) -> tuple[bool, str, float]:
        success = False
        attempt = 1
        output = ""
        start = time.perf_counter()

        while not success and attempt <= attempts:
            try:
                start = time.perf_counter()
                result = subprocess.run(
                    command,
                    stderr=subprocess.STDOUT,
                    capture_output=True,
                    cwd=cwd,
                    timeout=timeout,
                    check=True,
                    text=True
                )
                output = result.stdout
                success = True
            except subprocess.SubprocessError as e:
                output = str(e.output)
                attempt += 1
        
        finish = time.perf_counter()
        duration = finish - start

        return success, output, duration
    
    def _apply_opt_allinone(self, passes: str) -> bool:
        opt_command = [
            'opt',
            *passes.split(),
            f'{self.godot_source_copy_path}/{self.godot_raw_bitcode_filename}',
            '-o',
            f'{self.godot_source_copy_path}/{self.godot_optimized_bitcode_filename}'
        ]

        return self._run_command(
            command=opt_command,
            timeout=self.opt_timeout,
        )

    def _compile(self) -> bool:
        clang_command = [
            'clang++',
            '-o',
            f'{self.godot_source_copy_path}/{self.godot_binary_filename}',
            '-O0',
            '-fuse-ld=lld',
            '-flto=thin',
            '-static-libgcc',
            '-static-libstdc++',
            '-s',
            f'{self.godot_source_copy_path}/{self.godot_optimized_bitcode_filename}',
            '-lzstd',
            '-lpcre2-32',
            '-lrt',
            '-lpthread',
            '-ldl',
            '-l:libatomic.a'
        ]

        return self._run_command(
            command=clang_command,
            timeout=self.clang_timeout,
        )

    def _run_benchmark(self, executions: int, execution_attempts: int) -> bool:
        success = False
        output = ""
        duration = 0.0

        for i in range(1, executions + 1):
            json_path = f'{self.godot_source_copy_path}/execution_{i}.json'

            benchmark_command = [
                f'{self.godot_source_copy_path}/{self.godot_binary_filename}',
                '--',
                '--run-benchmarks',
                f'--include-benchmarks={self.benchmark}',
                f'--save-json={json_path}'
            ]

            success, output, duration = self._run_command(
                command=benchmark_command,
                timeout=self.benchmark_timeout,
                attempts=execution_attempts,
                cwd=self.godot_benchmarks_repo_path
            )

            if not success:
                break

        return success, output, duration

    def _get_worst_benchmark_value(self, benchmark_statistic: str, executions: int) -> float | None:
        worst_value = 0.0

        for i in range(1, executions + 1):
            json_path = f'{self.godot_source_copy_path}/run_{i}.json'
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    value = data['benchmarks'][0]['results'].get(benchmark_statistic)
                    if value is not None and value > worst_value:
                        worst_value = value
            except (FileNotFoundError, json.JSONDecodeError, KeyError, IndexError) as e:
                print(f'WARNING --- Failed to read {json_path}: {e}')

        return worst_value if worst_value != 0.0 else None
    
    def _save_stats(self, solution_variables: List[int], 
                    opt_success: bool, opt_output: str, opt_duration: float,
                    clang_success: bool, clang_output: str, clang_duration: float,
                    benchmark_success: bool, benchmark_output: str, benchmark_duration: float) -> None:
        self.stats[str(solution_variables)] = {
            'opt': {
                'success': opt_success,
                'output': opt_output,
                'duration': opt_duration
            },
            'clang': {
                'success': clang_success,
                'output': clang_output,
                'duration': clang_duration
            },
            'benchmark': {
                'success': benchmark_success,
                'output': benchmark_output,
                'duration': benchmark_duration
            }
        }
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def calculate(self, solution_variables: List[int]) -> float:
        """
        Calculate the fitness value based on the worst runtime of five executions of a benchmark.

        :param solution_variables: List of integers representing the LLVM passes to apply.
        :return: The fitness value (worst runtime) or sys.float_info.max if an error occurs.
        """
        self._copy_original_source()

        # Apply the "full" opt command
        passes = ' '.join([LlvmUtils.get_passes()[i] for i in solution_variables])
        print(passes)   # !!! DEBUG
        opt_success, opt_output, opt_duration = self._apply_opt_allinone(passes)
        if not opt_success:
            # Bad list of passes; applying them one by one is not viable in this problem, at least for now
            print('DEBUG --- OPT HA PETAO')
            return sys.float_info.max

        # Compile into a Godot binary
        clang_success, clang_output, clang_duration = self._compile()
        if not clang_success:
            # Compiling went wrong for whatever reason
            print('DEBUG --- CLANG HA PETAO')
            return sys.float_info.max

        # Execute benchmark (wcase)
        executions = 5
        execution_attempts = 3
        benchmark_success, benchmark_output, benchmark_duration = self._run_benchmark(executions, execution_attempts)
        if not benchmark_success:
            # Benchmark went wrong for whatever reason
            print('DEBUG --- BENCHMARK HA PETAO 3 VECES')
            return sys.float_info.max

        # Get worst runtime
        fitness_value = self._get_worst_benchmark_value(self.benchmark_statistic, executions)
        if not fitness_value:
            # Reading the benchmark results went wrong for whatever reason
            print('DEBUG --- LOS RESULTADOS DEL BENCHMARK NO SE HAN PODIDO LEER')
            return sys.float_info.max
        
        # Save stats
        self._save_stats(
            solution_variables,
            opt_success, opt_output, opt_duration,
            clang_success, clang_output, clang_duration,
            benchmark_success, benchmark_output, benchmark_duration
        )

        return fitness_value

    def name(self) -> str:
        return "Godot Runtime Fitness Function"