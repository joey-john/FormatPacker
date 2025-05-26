import pandas as pd
from pathlib import Path

from point_object import PointObject, GroupObjectList

def ExcelInput() -> list[PointObject]:
    """ Creates Excel Test Data, doesn't test Group Functionality but can verify results """
    # PointObject List
    objects: list[PointObject] = []
    
    # Workbook Input Path
    WB_PATH = Path("Inputs\input_fixed.xlsx")

    if not WB_PATH.exists():
        raise FileNotFoundError(WB_PATH)


    # --- Create Datafrane from Excel Workbook (WB_PATH) ------------------------- #
    df = pd.read_excel(WB_PATH, usecols="A:F", header=2)
    df = df.dropna(subset=["Name"])

    for _, row in df.iterrows():
        name        = row["Name"]
        size        = int(row["Size"])
        period      = int(row["Period"])
        start_frame = int(row["Start_Frame"]) if pd.notna(row["Start_Frame"]) else None
        offset      = int(row["Offset"])      if pd.notna(row["Offset"])      else None
        
        objects.append(PointObject(name, size, period, start_frame, offset))
    
    return objects    