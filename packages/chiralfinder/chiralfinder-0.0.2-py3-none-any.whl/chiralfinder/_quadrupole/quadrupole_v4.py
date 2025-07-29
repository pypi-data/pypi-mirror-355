from .quadrupole_utils import *


class ChiralAxialType4(ChiralBase):
    def __init__(self, mol):
        super().__init__(mol)

    def find_connecting_atoms(self, bond_list, atom, prior_atom=None):
        # find all atoms connect to the input 'atom', remove 'prior_atom' in them
        connecting_atoms = []
        for bond in bond_list:
            if bond[0] == atom and not bond[1] == prior_atom:
                connecting_atoms.append(bond[1])
        return connecting_atoms

    def get_chi_mat(self):
        phConnecting = []
        for bond in self.mol.GetBonds():
            atom_1, atom_2 = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
            if self.atoms[atom_1].GetIsAromatic() and self.atoms[atom_2].GetIsAromatic():
                if not bond.GetIsAromatic():
                    # check rings, same or not
                    atom_1_ring = []
                    for ring in self.ssr:
                        if atom_1 in list(ring):
                            atom_1_ring.append(list(ring))
                    for one_ring in atom_1_ring:
                        if atom_2 not in one_ring:
                            phConnecting.append((atom_1, atom_2))
                            break

        atoms = self.mol.GetAtoms()
        # get the axis
        chiral_axes = []  # merge all confs
        mats, dets, norm_cp, signs = [], [], [], []  # for each conf
        for bond in phConnecting:
            # phbonds neighbors
            begin_neighbor = [atom.GetIdx() for atom in atoms[bond[0]].GetNeighbors()]
            end_neighbor = [atom.GetIdx() for atom in atoms[bond[1]].GetNeighbors()]
            # outside neighbors
            if bond[1] in begin_neighbor:
                begin_neighbor.remove(bond[1])
            if bond[0] in end_neighbor:
                end_neighbor.remove(bond[0])

            # only consider this type, two atoms (include H)
            if (len(begin_neighbor) != 2) or (len(end_neighbor) != 2):
                continue

            # different then chiral
            if (self.CIP_list[begin_neighbor[0]] != self.CIP_list[begin_neighbor[1]]) and (self.CIP_list[end_neighbor[0]] != self.CIP_list[end_neighbor[1]]):
                chiral_axes.append(bond)

                mat_confs = []
                det_confs = []
                norm_det_confs = []
                sign_confs = []
                for conf_ in self.coordinates:
                    begin_cor = conf_[bond[0]]
                    end_cor = conf_[bond[1]]

                    # sort the outside neighbors
                    if self.CIP_list[begin_neighbor[0]] > self.CIP_list[begin_neighbor[1]]:
                        begin_1_cor = conf_[begin_neighbor[0]]
                        begin_2_cor = conf_[begin_neighbor[1]]
                    else:
                        begin_1_cor = conf_[begin_neighbor[1]]
                        begin_2_cor = conf_[begin_neighbor[0]]

                    if self.CIP_list[end_neighbor[0]] > self.CIP_list[end_neighbor[1]]:
                        end_1_cor = conf_[end_neighbor[0]]
                        end_2_cor = conf_[end_neighbor[1]]
                    else:
                        end_1_cor = conf_[end_neighbor[1]]
                        end_2_cor = conf_[end_neighbor[0]]

                    a = begin_1_cor - (begin_cor + end_cor) / 2
                    b = begin_2_cor - (begin_cor + end_cor) / 2
                    c = end_1_cor - end_2_cor
                    cp_max = np.linalg.norm(np.cross(a, b)) * np.linalg.norm(c)
                    mat = np.array([a, b, c])
                    mat_confs.append(mat)
                    det_, sign_ = self.criterion(mat)
                    det_confs.append(det_)
                    norm_det_confs.append(det_/cp_max)
                    sign_confs.append(sign_)
                mats.append(mat_confs)
                dets.append(det_confs)
                norm_cp.append(norm_det_confs)
                signs.append(sign_confs)
        return {"chiral axes": chiral_axes, "quadrupole matrix": mats, 
                "determinant": dets, "norm CP": norm_cp, "sign": signs}
    