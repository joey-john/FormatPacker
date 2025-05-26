""" ============================================================================
# Name         : benchmark.py
# Date         : 05/09/2025
# Description  : Benchmark Timing for Format Packer
# Notes        : -
============================================================================ """
from datetime import datetime
from pathlib import Path
from pstats import Stats, SortKey
from timeit import timeit
import cProfile

from main import *


def WriteBenchmark(packer: FormatPacker, time: float|None, n: int|None = None):
    """ Write to Benchmarking Log File """
    headers = ["Date", "Version", "Test", "Time", "Configurations"]
    today = datetime.now().strftime("%m/%d/%y")
    version = "0.1.3"
    test = f"LargeInput[:{n}]" if n else "LargeInput"
    time = f"{time:3.15f}" if time else f"{str(time):1}"
    
    output_line = f"{today} | {version:7} | {test:20} | {time}\n"
    
    benchmark_file = Path("Exports/benchmark_tracker.txt")
    with benchmark_file.open('a', encoding="UTF8") as file:
        file.write(output_line)
        file.write("─────────┼─────────┼──────────────────────┼──────────────────────\n")
        
        
# ============================================================================ #
#                                     TIMER                                    #
# ============================================================================ #
def Time_FormatPacker(packer: FormatPacker, build_output: bool = False, name: str = "") -> tuple[float|None, float|None]:
    """ Time Format Packer

    Args:
        packer (Format Packer): Format Packer Object
        build_output (bool, optional): Flag to Build Dataframes. Defaults to False.
        name (str): Name of Format Packer Data for Header. Defaults to "".

    Returns:
        float, float|None: Format Pack Time and Build_Output Time if build_output is True otherwise None
    """
    print(f"=== {name} FormatPacker Timer ==================================================")
    print(f"# of Total PointObjects : {len(packer.objects)}")
    print(f"# of Group Objects      : {len(packer._groups)}")
    
    try:
        pack_timer = timeit("packer.pack()", globals=locals(), number=1)
        print("\nFormatPacker.pack() Time:", pack_timer)

        if build_output:
            print("\nFormatPacker.to_dataframes() Time:", output_timer)
            output_timer = timeit("packer.to_dataframes()", globals=globals(), number=1)
        else:
            output_timer = None

        return pack_timer, output_timer
    
    except FramePackingError as e:
        print(e)
        return None, None

# ============================================================================ #
#                                   PROFILER                                   #
# ============================================================================ #
def Profile_FormatPacker(packer: FormatPacker, build_output: bool = False, name: str = "", sortby = SortKey.TIME) -> None:
    """ Profile Format Packer

    Args:
        packer (Format Packer): Format Packer Object
        build_output (bool, optional): Flag to Build Dataframes. Defaults to False.
        name (str): Name of Format Packer Data for Header. Defaults to "".
        sortkey: Key to sort profiler results. Defaults to SortKey.TIME.
    """
    print(f"=== {name} FormatPacker Profiler ===============================================")
    print(f"# of Total PointObjects : {len(packer.objects)}")
    print(f"# of Group Objects      : {len(packer._groups)}")
    

    with cProfile.Profile() as profile:
        packer.pack()

        if build_output:
            packer._to_dataframes()

    result = Stats(profile).sort_stats(sortby)
    result.print_stats()

# ============================================================================ #
#                                     MAIN                                     #
# ============================================================================ #    
if __name__ == '__main__':
    # ---------------
    TEST_LEN = 100
    largepacker = Large_FormatPacker(TEST_LEN)
    time, _ = Time_FormatPacker(largepacker, name="Large")
    WriteBenchmark(largepacker, time, TEST_LEN)
    
    # --- Timers ---
    # Time_FormatPacker(Excel_FormatPacker(), build_output=True, name="Excel")
    # Time_FormatPacker(Manual_FormatPacker(), name="Manual")
    
    # --- Profilers ---
    sortby = SortKey.TIME
    Profile_FormatPacker(Excel_FormatPacker(), build_output=True, name="Excel", sortby=sortby)
    Profile_FormatPacker(Manual_FormatPacker(), name="Manual", sortby=sortby)
    Profile_FormatPacker(Large_FormatPacker(TEST_LEN), name="Large", sortby=sortby)