import os
from xldg.data import Path, MeroX, CrossLink, ProteinStructure, ProteinChain, Domain, Fasta
from xldg.graphics import Circos, CircosConfig

if __name__ == "__main__":
    # Circos
    cwd = os.path.join(r'D:\2025-04-03_Meeting-Oleksandr\ZHRM\Shp2\unselected')
    monomer_path = os.path.join(cwd, "Shp2_af2_closed.pdb")
    structure = ProteinStructure.load_data(monomer_path)
    structure.predict_crosslinks()


    # for i in range(0, 35):
    #     print(structure.is_path_distance_in_range(516, 539, 10, 35))
