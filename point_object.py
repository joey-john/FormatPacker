""" ================================================================================================
# Name         : pointobject.py
# Date         : 05/09/2025
# Description  : description
# Notes        : Temporary Hooks that will be replaced, some of this stuff needs to be added to 
                 the existing code base
================================================================================================ """

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ortools.sat.python.cp_model import CpModel

# ============================ Point Object Class ============================ #
class PointObject:
    """ Point Object Class
    
    Attributes:
        Name (str)                              : Point Name
        Size (int)                              : Point Size (bits)
        Period (int)                            : Period for Point (factor of NUM_FRAMES)
        Start_Frame (int | None)                : Optional Start Frame for Point. Defaults to None
        Offset (int | None)                     : Optional Offset for Point (bits). Defaults to None.
        start_unit (CpModel.IntVar | None)      : CpModel.IntVar representing the starting unit in the frame
        phase_vars (list[CpModel.BoolVar])      : List of phases the object appears in represented by CpModel.BoolVar
    """
    
    __slots__ = ("Name", "Size", "Period", "Start_Frame", "Offset", "start_unit", "phase_vars")
    
    def __init__(self, name: str, size: int, period: int, start_frame: int | None = None, offset: int | None = None):
        """ Initialize PointObject Instance

        Args:
            name (str)                          : Point Name
            size (int)                          : Point Size (bits)
            period (int)                        : Period for point. Expected to be a factor of NUM_FRAMES
            start_frame (int | None, optional)  : Start Frame for Point. Defaults to None.
            offset (int | None, optional)       : Byte Offset for Point. Defaults to None.
        """
        # User Input
        self.Name: str                  = name
        self.Size: int                  = size # bits
        self.Period: int                = period
        self.Start_Frame: (int | None)  = start_frame
        self.Offset: (int | None)       = offset * 8 if offset is not None else None  # convert to bits
        
        # Solver Calculated Assignments
        self.start_unit: (CpModel.IntVar | None)  = None  # CpModel.IntVar (in units)
        self.phase_vars: list[CpModel.BoolVar]    = []    # list of CpModel.BoolVar
    

    def to_dict(self) -> dict[str, str|int|None]:
        """ Return Object as a Dictionary
        
        Used for writing Objects to Output Excel Workbook 

        Returns:
            dict[str, str|int|None]: _description_
        """
        return {
            "Name":         self.Name,
            "Size":         self.Size,
            "Period":       self.Period,
            "Start_Frame":  self.Start_Frame,
            "Offset":       self.Offset
        }


# ============================ Group Object Class ============================ #
class GroupObjectList(list):
    """ Group Object List Class. 
    
    Represents a list of PointObjects. Assigns the period, start_frame, and offset to all
    point objects within it. Overrides list object. All list methods can be used GroupObject.
    
    Example Usage:
        p1 = Point("Point1", size=8, period=8)
        p2 = Point("Point2", size=16, period=4)
        
        groupobj = GroupObject(period=8, p1, p2, name="_", start_frame=1, offset=8)
        
        print("p2.Period", groupobj[1].Period)   # PointObject P2
        >>> p2.Period: 8
        
    Attributes:
        Name (str)                  : Group Name (Not Used).
        Period (int)                : Period for all points within the list
        Start_Frame (int)           : Start Frame for all points within the list
        Offset (int)                : Offset for all points within the list
        
        *points (PointObject)       : Point Objects within the lis
    """
    
    def __init__(self, period: int, *points, name: str = "_", start_frame: int | None = None, offset: int | None = None):
        """ Initialize GroupObjectList Instance
        
            period (int)                        : Period for all PointObjects in Group
            *points (PointObject)               : Point Objects to add to Group
            
            name (str, Optional)                : Group Name. doesn't matter, not used. Defaults to "_"
            start_frame (int | None, optional)  : Start Frame for all PointObjects in Group. Defaults to None.
            offset (int | None, optional)       : Byte Offset for all PointObjects in Group. Defaults to None.
        """
        self.Name: str          = name
        self.Period: int        = period
        self.Start_Frame: int   = start_frame
        self.Offset: int        = offset * 8 if offset is not None else None  # convert to bits
        
        for p in points:
            p.Period        = period
            p.Start_Frame   = start_frame
            p.Offset        = offset * 8 if offset is not None else None  # convert to bits
            
        super().__init__(points)
    
    
if __name__ == '__main__':
    pass