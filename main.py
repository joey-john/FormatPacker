""" ================================================================================================
# Name         : main.py
# Date         : 05/09/2025
# Description  : run FormatPacker
# Notes        : -
================================================================================================ """
import sys
import warnings
warnings.simplefilter(action='ignore', category=UserWarning)

import pandas as pd

from point_object import PointObject, GroupObjectList
from FormatPacker import FormatPacker, FramePackingError
from Inputs.large_objects import large_objects
from Inputs.excel_objects import ExcelInput
from Inputs.manual_objects import ManualInput


# =========================== Verify Python Version ========================== #
if sys.version_info < (3, 10):
    print("ERROR: Python version must be >= 3.10")
    sys.exit(1)

# ==================================== Run =================================== #
def run(packer: FormatPacker, build_outputs: bool = False) -> None:
    """ Run FormatPacker Test Given List of Points """
    # Run the FormatPacker
    packer.pack()
    
    # Create DataFrames & Export the Output to Excel
    if build_outputs:
        packer.build_output()
        

# ============================== Format Packers ============================== #
def Excel_FormatPacker():
    return FormatPacker(ExcelInput(), frame_size=1000)

def Manual_FormatPacker():
    return FormatPacker(ManualInput(), frame_size=1000)

def Large_FormatPacker(n=None):
    objects = large_objects[:n] if n else large_objects
    packer = FormatPacker(objects, frame_size=1000)
    return packer
    
    
# ============================================================================ #
#                                     MAIN                                     #
# ============================================================================ #
if __name__ == '__main__':
    if len(sys.argv) > 1:
        match sys.argv[1].casefold():
            case "excel":
                run(Excel_FormatPacker()) 
            case "manual":
                run(Manual_FormatPacker())
            case "large":
                run(Large_FormatPacker())
            case _:
                print("Unknown Argument")
    else:
        run(Excel_FormatPacker()) 
        run(Manual_FormatPacker())
        run(Large_FormatPacker())
