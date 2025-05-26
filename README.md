# Optimal Solution Format Packing using a CPSAT Solver
Author: Joseph John

This project utilizes Google's OR-Tools CPSAT Solver to Pack Objects into a Variable # of Formats with variable size for use in a Time-Division Multiplexing (TDM) Schedule.
Packs and proves optimality for both the ideal frame and byte position per object. Objects have the following arguments start_frame, offset, size, and period. Objects can also be grouped together.

**NOTE:** This project was abandoned due to the time constraints for packing large number of objects. The solve was hitting the NP-hardnesss of it all and I thought a different approach would be necessary. But it's still cool to see this work.  
Even after doing extensive benchmarking and finetuning parameters, The solve time for ~2000 objects was about 30 seconds. If you see a good way I can reduce that to under 5 seconds by modifying constraints I'd be happy to look into it!
---


## Files:

- [FormatPacker.py](FormatPacker.py)
    - FormatPacker
    - See [Using the Format Packer](#using-the-format-packer)

- [point_objects.py](point_objects.py)
    - Example Test Point and Group OBjects for the FormatPacker. 

- [main.py](main.py)
    - Python Main Script. Used to test FormatPacker

- [benchmark.py](benchmark.py)
    - Python Script used for Timing, Profiling, and Crude Benchmarking

- [Inputs\input_fixed.xlsx](Inputs\input_fixed.xlsx)
    - Data to Input for Testing Format Packer (Blue DataTable)
    - Orange Table verifies the correct hook using the output excel file created by `FormatPacker.build_output()`
    - Change filename in the first cell to verify the output
    - Processed and Converted to `PointObjects` in `ExcelInput()` in main.py

- [Inputs\input.xlsx](Inputs\input.xlsx)
    - Similar to `input_fixed` except randomizes the DataTable Input
    - TODO: Needs Updating, I've been using input_fixed.xlsx

- [test\test_formatpacker.py](test_formatpacker.py)
    - Unit Testing and Correctness Verification of Manual Input data read from `ManualInput()`

## Requirements
- Python ≥ 3.10
- See [requirements.txt](requirements.txt)

### Python Setup
Python Environment Setup Steps
1. Ensure you have a python (≥ 3.10)

2. Install the Necessary Libraries (See requirements.txt)


## Using the Format Packer

### Running a Test Case with the Format Packer
Currently, [*main.py*](main.py) provides 2 functions that can be used for running test cases:

- `run_ExcelInput()`
    - Run Format Packer using a Manual Created list of objects that is defined in `ManualInput()`
    - Using a manual input allows you test the Grouping Functionality.
    - Results can be verified for corectness using *test_formatpacker.py*.
    - NOTE: The ouput excel file must be open in excel in order for input_fixed.xlsx read it

- `run_ManualInput()`
    - Run Format Packer using data defined in the excel sheet [*input_fixed.xlsx*](input_fixed.xlsx)
    - Using the excel input data does not currently test have a way to defined groups however you can validate the results of the packing in *input_fixed.xlsx* by changing the first cell to the filename of the excel sheet exported by the Format Packer as long as the file exists in this directory.

### FormatPacker Arguments
#### Inputs:
``` py
    objects (list[PointObject|GroupObjectList])         : List of Point Objects to Pack
    frame_size (int)                    : Frame Size (bytes)
    num_frames (int, optional)          : Number of Frames. Defaults to 32.
    output_path (Path | str, optional)  : Path and name for exported excel file. Defaults to "packer_out.xlsx".
```

#### Outputs:
Flexible Outputs. Call FormatPacker.build_outputs() to see example dataframes made and the excel file generated.

#### Raises:
`ValueError`
- A PointObject has a $`\textsf{Start\_Frame} \not\in[0,31`]$  
- A PointObject has an $`\textsf{Offset} + \textsf{Size} > \textsf{FRAME\_SIZE\_BITS}`$

`CalculationError(RuntimeError)`
- Frame-packing failed due to invalid inputs or unsolvable constraints


## Implementation
The `FormatPacker.pack()` function has 2 steps
1. Build a CpModel (`FormatPacker._build_model()`) 
2. Run the CpSolver on that model (`FormatPacker._solve()`).

The `FormatPacker.build_out()` function has 2 steps
1. Build Output Dataframes (`FormatPacker._to_dataframes()`)
2. Export Dataframes to Excel Workbook (`FormatPAcker._export_to_excel()`) 

### Rescaling Solution
Before building the model, all sizes are reduced by the calculated GCD of the object sizes and the total frame size (`FRAME_SIZE`) to make use of a smaller coefficient. 
- Smaller coefficients mean the CP-SAT solver’s propagation and cuts are more effective.
- The GCD will typically be either 2, 8, or 16
- Actual memory load per frame = $UNIT * (solver's unit-load)$

The `FramePacker.UNIT` stores the value that the model is scaling everything by. When we produce the output, we multiple everything by UNIT to get the values back in terms of bits.


### Building the CpModel
To Build the Model,

1. Point Constraints - Add Model Constraints for each `PointObject`:

    1. Define `start_unit` and `phase_vars`
        - `start_unit`: an int variable that specifies the start bit position (in units)
        - `phase_vars`: a bool for each possible phase determines which offset within the period we use.
    
    2. If Offset, add constraint to respect that offset
        ``` py
        start_unit == (Offset / UNIT)
        ```
    
    3. Add constraint that only one phase should be picked
        ``` py 
        sum(obj.phase_vars) == 1
        ```
    
    4. If Start_Frame, constrain model to respect that start_frame
        ``` py
        req = obj.Start_Frame % obj.Period
        self.model.Add(obj.phase_vars[req] == 1)
        ```

2. Group Constraints - For each `GroupObjectList`:
    - *Note: When we created the object and groups list, we moved the group's Offset and Start_Frame values to only the first object in the group and set the value of Offset and Start_Frame to `None` for every other point in the same group.*

    1. Add constraint that every point within the group must appear in the same frames
        ``` py
        self.model.Add(P2.phase_vars[s] == P1.phase_vars[s])
        ```

    2. Add constraint that every point after the first point in the group must follow each other back to back
        ```py
        self.model.Add(P2.start_unit == P1.start_unit + (P1.Size // self.UNIT))
        ```

3. Build Interval Schedule
    - For Each Frame, determine if the object can exist in that frame and mark it
    - If Start_Frame, enforce that the object must exist in that frame

    1. Forbid Overlapping
        ``` py
        self.model.AddNoOverlap(intervals)
        ```

5. Create Constant used to maximize total bits for each object
    ``` py 
    total_util_expr = sum(obj.Size * (self.NUM_FRAMES // obj.Period) for obj in self.objects)
    self.total_util = self.model.NewConstant(total_util_expr)
    ```

6. For each object, compute the `end_unit` and `max_end`
    - `end_unit` address of last bit
        - $` \textsf{end\_unit} = \sum (\textsf{Size} \times (\textsf{NUM\_FRAMES} \div \textsf{Period})) `$
    - `max_end` very last bit in frame
        - $`\textsf{max\_end} = max(\textsf{Start\_Unit} + (\textsf{Size} \div \textsf{UNIT}) )`$
    ``` py
    # for each object:
    eb = self.model.NewIntVar(0, self.CAP, f"end_{obj.Name}")
    self.model.Add(eb == obj.start_unit + (obj.Size // self.UNIT))

    # max for all objects:
    self.max_end = self.model.NewIntVar(0, self.CAP, "max_end")
    self.model.AddMaxEquality(self.max_end, end_units)
    ```

### Two-Stage Lexicographic Solver
Now we use the CpSolver to solver all the constraints we defined in our model!
In summary, 

1. Stage 1 - Maximizing `total_util`
    - We don't want to drop any object so maximize that boy

2. Stage 2 - Minimizing `max_end`
    - Prior to starting Stage 2, we take the optimal value from Stage 1 and turn it into a new constraint that the solver for Stage 2 should only consider values where the Stage 1 Solver found the maximum total_util aka `best_util_end`.
        ``` py
        self.model.Add(self.total_util == best_util_1)
        ```
    - In Stage 2, we now minimize max_end which takes the solutions where the ammount of empty space between objects was at a minimum

### Solver Status
Verifies Optimal Packing.
OR-Tools' CP-SAT proves optimality (or stops early with best known solution)

#### Possible Status Value [[*Source*](https://developers.google.com/optimization/cp/cp_solver)]
| Status        | Description                                                                                                                                                                                                                      |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| OPTIMAL       | An optimal feasible solution was found.                                                                                                                                                                                          |
| FEASIBLE      | A feasible solution was found, but we don't know if it's optimal.                                                                                                                                                                |
| INFEASIBLE    | The problem was proven infeasible.                                                                                                                                                                                               |
| MODEL_INVALID | The given `CpModelProto` didn't pass the validation step. You can get a detailed error by calling `ValidateCpModel(model_proto)`.                                                                                                |
| UNKNOWN       | The status of the model is unknown because no solution was found (or the problem was not proven INFEASIBLE) before something caused the solver to stop, such as a time limit, a memory limit, or a custom limit set by the user. |

### Deterministic Results

The CP-SAT Solver produces states deterministic results  when the `num_of_workers = 1` otherwise they solutions may vary.
To this extent, the following parameters have been set for the solver:
```python
# Specify Random Seed to use
solver.parameters.random_seed = 12345

# Set to 1 to produce a Deterministic Result
solver.parameters.num_search_workers = 1
```
Even with these parameters set, pure deterministic results are not always 100% garaunteed. In rare instances, minor variations in the final results have been obsereved. Despite the variations, all results are still optimal, valid solutions.
NOTE: Further testing is needed to provide a bester percent estimate of how often results vary.

This issue can be fixed by adding additonal constraints to the model but more testing on how that would affect the overall build time would be needed. 


#### Experimental Alternative: `solver.parameters.interleave_search`
The CP-SAT Solver also provides the parameter `solver.parameters.interleave_search = 1`.
According to the [documentation](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto):

> ``` javascript
> // Experimental. If this is true, then we interleave all our major search[]()
> // strategy and distribute the work amongst num_workers.
> //
> // The search is deterministic (independently of num_workers!), and we
> // schedule and wait for interleave_batch_size task to be completed before
> // synchronizing and scheduling the next batch of tasks.
> 
> optional bool interleave_search = 136 [default = false];
> 
> optional int32 interleave_batch_size = 134 [default = 0];
> 
> ```
