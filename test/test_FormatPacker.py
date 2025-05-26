""" ================================================================================================
# Name         : test_FormatPacker.py
# Date         : 05/12/2025
# Description  : Testing Format Packer
# Notes        : -
================================================================================================ """
import unittest
print(__package__)
from point_object import PointObject, GroupObjectList
from FormatPacker import FramePackingError, FormatPacker
from main import ManualInput

test_objects = ManualInput()

def ExpectedFrequency(point: PointObject, total_frames: int = 32) -> int:
    """ Calculate the Expected Frequency of a Point Object factoring in Start_Frame

    Args:
        point (PointObject): Point Object
        total_frames (int, optional): Total Number of Frames. Defaults to 32.

    Returns:
        int: frequency
    """
    start_frame = point.Start_Frame if point.Start_Frame is not None else 0
    if start_frame >= total_frames:
        return 0
    else:
        return 1 + (total_frames - 1 - start_frame) // point.Period


# ============================================================================ #
#                                 Format Packer                                #
# ============================================================================ #
class FormatPackerTestCase(unittest.TestCase):
   
    @classmethod
    def setUpClass(cls):
        # Test Objects List
        cls.test_objects = test_objects
       
        cls.packer = FormatPacker(test_objects, frame_size=1000, num_frames=32, output_path="packer_out.xlsx")
        cls.packer.pack()
        cls.packer._to_dataframes()
       
        # Dataframes
        cls.objects_df = cls.packer.objects_df
        cls.schedule_df = cls.packer.schedule_df
        cls.memorymap_df = cls.packer.memorymap_df
        cls.frameorder_df = cls.packer.frameorder_df
        cls.framesummary_df = cls.packer.framesummary_df
   
   
    def setUp(self):
        return super().setUp()
   
   
    def test_frequency(self):
        """ Validate Point Frequency """
        for i, obj in enumerate(self.packer.objects):
            count = sum(1 for f in range(self.packer.NUM_FRAMES) if self.schedule_df.at[i, str(f)] == obj.Name)
            self.assertEqual(count, ExpectedFrequency(obj))
       

    def test_size(self):
        """ Validate Point Size """
        for idx, obj in enumerate(self.packer.objects):
            name   = obj.Name
            size   = obj.Size
            period = obj.Period
            sf     = obj.Start_Frame  
            for f in range(self.packer.NUM_FRAMES):
                col = self.memorymap_df[f]
                actual = int((col == name).sum())
                if sf is not None:
                    should = (f >= sf and (f - sf) % period == 0)
                else:
                    should = (self.schedule_df[str(f)][idx] == name)
                expected = size if should else 0        
            self.assertEqual(actual, expected, f"{name} in frame {f}: expected {expected} bits, got {actual}")    
           
           

    def test_start_frame(self):
        """ Validate Point Start_Frame's if defined """
        for obj in (self.packer.objects):
            if obj.Start_Frame is not None:
                idx = self.objects_df.index[self.objects_df["Name"] == obj.Name][0]  
                for f in range(self.packer.NUM_FRAMES):
                    expected = (f >= obj.Start_Frame and (f - obj.Start_Frame) % obj.Period == 0)
                    actual   = (self.schedule_df[str(f)][idx] == obj.Name)
                    self.assertEqual(actual, expected, f"{obj.Name} presence in frame {f}: expected {expected}, got {actual}")
   

    def test_offset(self):
        "Validate Point Offsets if defined "
        for obj in (self.packer.objects):
            if obj.Offset is not None:
                idx = self.objects_df.index[self.objects_df["Name"] == obj.Name][0]
                for f in range(self.packer.NUM_FRAMES):
                    if self.schedule_df[str(f)][idx] == obj.Name:
                        col = self.memorymap_df[f]
                        positions = col[col == obj.Name].index.tolist()
                        self.assertTrue(positions, f"{obj.Name} not found in memory map of frame {f}")
                        first_bit = positions[0]
                        self.assertEqual(first_bit, obj.Offset, f"{obj.Name} in frame {f}: expected start bit {obj.Offset}, got {first_bit}")
   
   
    def test_groupobjects(self):
        """ Validate Group Objects """
        for grp in self.packer._groups:
            names   = [p.Name for p in grp]
            period  = grp.Period
            sf      = grp.Start_Frame
            offset  = grp.Offset
            sizes   = {p.Name: p.Size for p in grp}

            for f in range(self.packer.NUM_FRAMES):
                # presence flags
                pres = []
                for name in names:
                    idx = self.objects_df.index[self.objects_df["Name"] == name][0]
                    pres.append(self.schedule_df.at[idx, str(f)] == name)
                self.assertTrue(all(pres) or not any(pres), f"Group {names} inconsistent presence in frame {f}: {pres}")
                if all(pres):
                    # check contiguous start bits
                    col = self.memorymap_df[f]
                    starts = [col[col == name].index[0] for name in names]
                    for i in range(len(names) - 1):
                        a, b = names[i], names[i+1]
                        self.assertEqual(starts[i+1], starts[i] + sizes[a], f"{b} not contiguous after {a} in frame {f}")
                    # check order in frameorder_df
                    order = self.frameorder_df[f].tolist()
                    idxs  = [order.index(name) for name in names]
                    self.assertEqual(idxs, sorted(idxs), f"Group {names} out of order in frame {f}: {order}")

   
if __name__ == '__main__':
    unittest.main(verbosity=2)
   

