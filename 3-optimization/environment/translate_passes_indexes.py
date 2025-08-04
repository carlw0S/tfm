import sys

from custom.jmetal.util import LlvmUtils

def translate_passes_indexes(passes_indexes: list[int]) -> str:
    """
    Translates a sequence of LLVM passes expressed as a list of indexes into a string of pass names.

    :param passes_indexes: List of integers representing the indexes of LLVM passes.
    """
    if not passes_indexes:
        return ''

    return ' '.join(LlvmUtils.get_passes()[index] for index in passes_indexes)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python translate_passes_indexes.py "[<index1>, <index2>, ...]"')
        sys.exit(1)

    passes_indexes = sys.argv[1].strip('[]').split(',')
    passes_indexes = [int(index.strip()) for index in passes_indexes]
    translated_passes = translate_passes_indexes(passes_indexes)
    print(translated_passes)