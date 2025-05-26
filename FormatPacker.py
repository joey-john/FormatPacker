
""" ================================================================================================
# Name          : FormatPacker.py
# Author        : Joseph John
# Date          : 05/09/2025
# Description   : Optimal Format Packer
---

Format Packer

Packs and proves optimality for both the ideal frame and byte position per object.
Review the class declaration documentation in FormatPacker() for available attributes and functions.
See README.md for notes and implementation details.

Typical Usage Example:

    packer = FormatPacker()
    packer.pack()
    
    # Write DataFrames to Excel Sheet
    packer.export_to_excel()
================================================================================================ """

from contextlib import contextmanager
from math import gcd
from pathlib import Path
import os
import sys

@contextmanager
def suppress_stdout():
    # Some code I borrowed from StackOverflow because ortools spouted some garbage about 
    # loading dlls from python and I hated it
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

import pandas as pd
with suppress_stdout():
    from ortools.sat.python import cp_model

from point_object import PointObject, GroupObjectList

# Custom Error Class
class FramePackingError(RuntimeError):
    """Frame-packing failed due to invalid inputs or unsolvable constraints."""
    pass


# ============================================================================ #
#                              Format Packer Class                             #
# ============================================================================ #
class FormatPacker:
    """ Format Packer Class

    Given a list of PointObjects, this class builds and solves a CP-SAT model to:
        1) maximize total frame utilization, 
        2) minimize the maximum end address,
        3) generate useful output dataframes
    
    Attributes:

        objects (list[PointObject]): List of Point Objects to Pack
        
        # Format Packer Constants
        FRAME_SIZE (int): Frame Size (bytes)
        FRAME_SIZE_BITS (int): Frame Size (bits)
        NUM_FRAMES (int): Number of Frames. Defaults to 32.
        ALIGNMENT (int): Alignment Value (Not Implemented)
        OUTPUT_PATH (Path): Path and Name for the Exported Excel File.
        
        # Unit & Capacity Sizes
        UNIT (int): Unit Scale. GCD of object sizes and FRAME_SIZE. S
                    See README.md for more details.
        CAP (int): Capacity Scaled by UNIT
        
        # CP-SAT Model & Solver
        model (CpModel): CP-SAT Model
        solver (CpSolver): CP-SAT Solver.
        
        # Attributes created after calling FormatPacker().pack()
        self.total_util (CpModel.NewConstant): aggregate number of bits placed across the entire schedule
        self.max_end (CpModel.NewIntVar): stores the value of the largest used memory bit address
        self.objects_df (pandas.DataFrame): DataFrame of all the PointObjects
        self.schedule_df (pandas.DataFrame): Schedule DataFrame
        self.memorymap_df (pandas.DataFrame): Memory Map Layout
        self.frameorder_df (pandas.DataFrame): Order of Objects per Frame
        self.framesummary_df (pandas.DataFrame): Flattened Summary of Bit Start Positions per Frame.
        
         
    """
    
    __slots__ = ("objects", "_groups", "FRAME_SIZE", "FRAME_SIZE_BITS", "NUM_FRAMES", "ALIGNMENT", "OUTPUT_PATH", 
                 "UNIT", "CAP", "model", "solver", "total_util", "max_end", 
                 "objects_df", "schedule_df", "memorymap_df", "frameorder_df", "framesummary_df", "framesummary")
    
    def __init__(self, objects: list[PointObject|GroupObjectList], frame_size: int, num_frames: int = 32, output_path: Path | str = Path("packer_out.xlsx")):
        """ Format Packer Initialization Class

        Args:
            objects (list[PointObject|GroupObjectList])     : List of Point Objects to Pack
            frame_size (int)                                : Frame Size (bytes)
            num_frames (int, optional)                      : Number of Frames. Defaults to 32.
            output_path (Path | str, optional)              : Path and name for exported excel file. Defaults to "packer_out.xlsx".
        """
        self.objects: list[PointObject] = []
        self._groups: list[GroupObjectList] = []
        
        # Add Objects
        # Add Group Objects to Objects
        # Keep a separate variable (self._groups) that holds the groups as a whole
        for obj in objects:
            if isinstance(obj, GroupObjectList):
                # The Start_Frame and Offset only matters for the first object in the group
                # We are going to add a constraint that all other objects in the same group must
                # follow the first object in the group so their Start_Frame and Offset don't matter.
                for i, p in enumerate(obj):
                    p.Period        = obj.Period
                    p.Start_Frame   = obj.Start_Frame
                    p.Offset        = obj.Offset if i ==0 else None
                self._groups.append(obj)
                self.objects.extend(obj)
            else:
                self.objects.append(obj)
        
        # --- Format Packer Constants ------------------------------------------------ #
        self.FRAME_SIZE: int        = frame_size
        self.FRAME_SIZE_BITS: int   = frame_size * 8
        self.NUM_FRAMES: int        = num_frames
        self.ALIGNMENT: int         = 8  # Not Used Right Now
        
        # --- Calculate UNIT * CAP --------------------------------------------------- #
        # Unit Scale (GCD of Sizes and FRAME SIZE) 
        unique_sizes: set[int] = set(obj.Size for obj in self.objects)
        defined_offsets_b: set[int] = set(obj.Offset for obj in self.objects if obj.Offset)
        self.UNIT = gcd(*unique_sizes, *defined_offsets_b, self.FRAME_SIZE_BITS)
        
        # Reduced Capacity per Frame
        self.CAP: int = self.FRAME_SIZE_BITS // self.UNIT

        # --- CP-SAT Model & Solver -------------------------------------------------- #
        self.model      = cp_model.CpModel()
        self.solver     = cp_model.CpSolver() 
        
        # CP-SAT Solver Parameters (see documentation for more details)
        # [required] Produce Deterministic Results from Solver
        self.solver.parameters.random_seed = 42
        self.solver.parameters.num_search_workers = 16
        
        # [optional] set max_time_in_seconds
        self.solver.parameters.max_time_in_seconds = 30
        # self.solver.parameters.search_branching = cp_model.FIXED_SEARCH
        # self.solver.parameters.linearization_level = 0
        # ---------------------------------------------------------------------------- #
        
        # Output Path
        self.OUTPUT_PATH: Path = Path(output_path)
        # DELETE --------------------------------------------------------------------- #
        # Change this in future to just raise FileExistsError or an error that it can't 
        # write because the excel sheet is open (OUTPUT_PATH)
        i = 0
        while self.OUTPUT_PATH.exists():
            self.OUTPUT_PATH = self.OUTPUT_PATH.with_stem(f"{Path(output_path).stem}_{i}")
            i += 1
        # ---------------------------------------------------------------------------- #
    
    
    # ============================== Private Methods ============================= #
    def _validate_objects(self):
        """ Validate Offset and Start_Frame """
        for obj in self.objects:
            name        = obj.Name
            size        = obj.Size
            start_frame = obj.Start_Frame
            offset      = obj.Offset
                
            # Start_Frame Check
            if (start_frame is not None) and (start_frame < 0 or start_frame > self.NUM_FRAMES-1):
                raise ValueError(f"Invalid Start_Frame: Object {name} has invalid Start_Frame={start_frame}; must be between 0 and {self.NUM_FRAMES-1}.")

            # Offset check (raw bytes → bits)
            if (offset is not None) and (offset < 0 or (offset + size > self.FRAME_SIZE_BITS)):
                raise ValueError(f"Invalid Offset: Object {name} (size={size}) at offset={offset} would overflow a {self.FRAME_SIZE}-byte frame.")



    def _build_model(self):
        """ Build CP-SAT Model """
        # 1) Create solver vars & pin offsets/start_frames on each PointObject
        for obj in self.objects:
            # PointObject solver vars (units)
            obj.start_unit = self.model.NewIntVar(0, self.CAP - (obj.Size // self.UNIT), f"sb_{obj.Name}")
            
            # Pin Offset (units) if given 
            if obj.Offset is not None:
                self.model.Add(obj.start_unit == (obj.Offset // self.UNIT))
            
            # Force exactly one phase
            if obj.Start_Frame is None and obj.Period > 1:
                    obj.phase_vars = [self.model.NewBoolVar(f"phase_{obj.Name}_{s}") for s in range(obj.Period)]
                    self.model.AddExactlyOne(obj.phase_vars)
            else:
                obj.phase_vars = []
        
        # 2) Add Group Constraints
        for grp in self._groups:
            for i in range(len(grp)-1):
                P1, P2 = grp[i], grp[i+1]
                
                if P1.phase_vars and P2.phase_vars:
                    # 2.1) points in a group must appear in the same frames
                    for s in range(P1.Period):
                        self.model.Add(P2.phase_vars[s] == P1.phase_vars[s])
                # 2.2) points in a group have contiguous placement, follow back-to-back
                self.model.Add(P2.start_unit == P1.start_unit + (P1.Size // self.UNIT))
                
        # 3) Build per-frame intervals with no overlaps
        for frame in range(self.NUM_FRAMES):
            intervals = []
            for obj in self.objects:
                p  = obj.Period
                sz = obj.Size // self.UNIT
                sf = obj.Start_Frame
                sb = obj.start_unit

                if sf is not None or p == 1:
                    sf = sf or 0
                    if frame >= sf and (frame - sf) % p == 0:
                        intervals.append(self.model.NewIntervalVar(sb, sz, sb + sz, f"intv_{obj.Name}_{frame}"))
                else:
                    # optional if this phase is chosen
                    for s, pv in enumerate(obj.phase_vars):
                        if frame % p == s:
                            intervals.append(self.model.NewOptionalIntervalVar(sb, sz, sb + sz, pv, f"intv_{obj.Name}_{frame}_{s}"))
            self.model.AddNoOverlap(intervals)
            
        # 4) Define total_util = sum(size * (NUM_FRAMES//period)) for each object
        total_util_expr = sum(obj.Size * (self.NUM_FRAMES // obj.Period) for obj in self.objects)
        self.total_util = self.model.NewConstant(total_util_expr)

        # 5) Compute self.end_units and self.max_end for second stage of solver
        # 5.1) Define end_unit[j] = start_unit[j] + size[j]
        end_unit = []
        for obj in self.objects:
            eb = self.model.NewIntVar(0, self.CAP, f"end_{obj.Name}")
            self.model.Add(eb == obj.start_unit + (obj.Size // self.UNIT))
            end_unit.append(eb)

        # 5.2) Define max_end = max(end_unit[j])
        self.max_end = self.model.NewIntVar(0, self.CAP, "max_end")
        self.model.AddMaxEquality(self.max_end, end_unit)
        
        
    def _solve(self):
        """ Two-Stage Lexicographic Solve """
        # --- Stage 1: Maximize total_util ------------------------------------------- #
        self.model.Maximize(self.total_util)
        
        status1 = self.solver.Solve(self.model)
        print()
        if status1 == cp_model.OPTIMAL:
            print("✅ Stage 1 - Optimal Proven Solution Found.")
        elif status1 == cp_model.FEASIBLE:
            print("⚠️ Stage 1 - Feasible Solution Found, optimality not proven (consider extending time limit).")
        else:
            print(f"❌ Stage 1 - No Solution Found.")
            raise FramePackingError(f"Stage 1 - No feasible packing found (maximize util)")
        
        best_util_1 = self.solver.Value(self.total_util)
        print(f"Stage 1 Complete: best total_util = {best_util_1} units")
        
        # --- Prepare for Stage 2 ---------------------------------------------------- #
        # Optimize Stage2 Solver by giving a hint for each start_unit and phase_var
        for obj in self.objects:
            # hint the start position
            self.model.AddHint(obj.start_unit, self.solver.Value(obj.start_unit))
            # hint which phase was chosen
            for pv in obj.phase_vars:
                self.model.AddHint(pv, self.solver.Value(pv))

        # --- Freeze total_util at its optimal --------------------------------------- #
        self.model.Add(self.total_util == best_util_1)

        # --- Second Stage: Minimize max_end ----------------------------------------- #
        self.model.Minimize(self.max_end)
        
        status2 = self.solver.Solve(self.model)
        print()
        if status2 == cp_model.OPTIMAL:
            print("✅ Stage 2 - Optimal Proven Solution Found.")
        elif status2 == cp_model.FEASIBLE:
            print("⚠️ Stage 2 - Feasible Solution Found, optimality not proven (consider extending time limit).")
        else:
            print(f"❌ Stage 2 - No Phase Solution Found.")
            raise FramePackingError("Stage 2 - Failed to minimize max_end after fixing total_util")
        
        best_util_2 = self.solver.Value(self.max_end)
        print(f"Stage 2 Complete: minimized max_end = {best_util_2} units")

        # TODO: Stage 3. Maybe? This would break ties by minimizing sum of start_bytes.
        # this would break any remaning ties between any solutions that are deemed by the solver as equally good
        # after computing maxed total_util + minimized max_end. I'm thinking something that prefers like the first 
        # most frame or something. Though it could be helpful to garauntee 100% deterministic results, which... 
        # I still need to test. (´。＿。｀)
        
        # UPDATE: Stage 3 definitely isnt possible considering how long it already takes to solve Stage 1 and 2 with a large input set


    def _to_dataframes(self):
        """ Create Helpful DataFrames of the Output 
        
        Produces Following DataFrame Attributes:
            self.objects_df (pandas.DataFrame): DataFrame of all the PointObjects
            self.schedule_df (pandas.DataFrame): Schedule DataFrame
            self.memorymap_df (pandas.DataFrame): Memory Map Layout
            self.frameorder_df (pandas.DataFrame): Order of Objects per Frame
            self.framesummary_df (pandas.DataFrame): Flattened Summary of Bit Start Positions per Frame.
        
        """
        # I could combine these, but the benchmark differences would be nominal and this format provides more code clarity.
        # TODO: Test benchmarks again when using actual data.

        # 1) Write Objects input to Dataframe
        self.objects_df = pd.DataFrame([obj.to_dict() for obj in self.objects], dtype=object)

        # 2) Build the “Schedule” DF
        schedule_rows: list[list[str]] = []
        for obj in self.objects:
            name        = obj.Name
            size        = obj.Size
            p           = obj.Period
            sf          = obj.Start_Frame
            
            row: dict[str] = {}
            for frame in range(self.NUM_FRAMES):
                # find chosen phase (only matters if no Start_Frame)
                if obj.phase_vars:           
                    phase = next(i for i, pv in enumerate(obj.phase_vars) if self.solver.Value(pv))
                    in_frame = (frame % p == phase)
                else:
                    sf = obj.Start_Frame or 0
                    in_frame = (frame >= sf) and ((frame - sf) % obj.Period == 0)
                        
                row[str(frame)] = name if in_frame else ""
            schedule_rows.append(row)
        self.schedule_df = pd.DataFrame(schedule_rows, dtype=object)

        # 3) Build the “Memory_Map” DF (indexed by bit 0…FRAME_SIZE_BITS-1)
        self.memorymap_df = pd.DataFrame("", index=range(self.FRAME_SIZE_BITS), columns=range(self.NUM_FRAMES), dtype=object)
        for obj in self.objects:
            name        = obj.Name
            size        = obj.Size
            p           = obj.Period
            sf          = obj.Start_Frame
            start_bit   = self.solver.Value(obj.start_unit) * self.UNIT
            
            for frame in range(self.NUM_FRAMES):
                # find chosen phase (only matters if no Start_Frame)
                if obj.phase_vars:           
                    phase = next(i for i, pv in enumerate(obj.phase_vars) if self.solver.Value(pv))
                    in_frame = (frame % p == phase)
                else:
                    sf = obj.Start_Frame or 0
                    in_frame = (frame >= sf) and ((frame - sf) % obj.Period == 0)
                
                if in_frame:
                    for b in range(start_bit, start_bit + size):
                        self.memorymap_df.iat[b, frame] = name

        # 4) Build "FrameOrder" DF (list of objects in the order they appear per frame)
        self.framesummary: list[list[tuple[int, str, int]]] = [] # [[(name, size, start_bit)]]
        frameorder: list[list[str]] = [] # list[list[str]]
        for frame in range(self.NUM_FRAMES):
            entries = []
            for obj in self.objects:
                name      = obj.Name
                size      = obj.Size
                p         = obj.Period
                sf        = obj.Start_Frame
                start_bit = self.solver.Value(obj.start_unit) * self.UNIT
                
                if obj.phase_vars:           
                    phase = next(i for i, pv in enumerate(obj.phase_vars) if self.solver.Value(pv))
                    in_frame = (frame % p == phase)
                else:
                    sf = obj.Start_Frame or 0
                    in_frame = (frame >= sf) and ((frame - sf) % obj.Period == 0)

                if in_frame:
                    entries.append((obj.Name, start_bit))

            # sort by start_unit and keep only the names
            entries.sort(key=lambda x: x[1])
            self.framesummary.append(entries)
            frameorder.append([e[0] for e in entries])

        self.frameorder_df = pd.DataFrame(frameorder, dtype=object).transpose()

        # 5) Build Format Points DF
        first_bits = {}
        for frame in self.framesummary:
            for obj, start_bit in frame:
                if obj in first_bits:
                    first_bits[obj] = min(first_bits[obj], start_bit)
                else:
                    first_bits[obj] = start_bit
        object_order = sorted(first_bits, key=lambda x: first_bits[x])
        
        self.framesummary_df = pd.DataFrame(index=object_order, columns=range(self.NUM_FRAMES), dtype=object)
        
        for i, frame in enumerate(self.framesummary):
            for name, start_bit in frame:
                self.framesummary_df.at[name, i] = start_bit
    

    def _export_to_excel(self):
        """ Write Datafranes to Excel """
        with pd.ExcelWriter(self.OUTPUT_PATH, engine="openpyxl") as writer:
            self.objects_df.to_excel(writer, index=False, sheet_name="Schedule")
            self.schedule_df.to_excel(writer, index=False, sheet_name="Schedule", startcol=len(self.objects_df.columns)+2) # 2 blank cells
            self.memorymap_df.to_excel(writer, index_label="Bits", sheet_name="Memory_Map")
            self.frameorder_df.to_excel(writer, index=False, sheet_name="Frame Order")
            self.framesummary_df.to_excel(writer, index_label="Objects", sheet_name="Frame_Summary")
            print(f"\n>>> Output written to '{self.OUTPUT_PATH.name}'")


    # ============================== Public Methods ============================== #
    def pack(self):
        """ Main Method - Do Err'thing """
        self._build_model()
        self._solve()
        
        
    def build_output(self):
        """ Generate Dataframe Outputs and write to Excel File """
        self._to_dataframes()
        self._export_to_excel()
        

if __name__ == '__main__':
    pass