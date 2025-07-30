# Copyright (c) 2024 Lucas Dooms

from dataclasses import dataclass
from typing import List

import numpy as np

from smc_lammps.generate.generator import (
    BAI,
    AtomGroup,
    AtomType,
    BAI_Kind,
    BAI_Type,
    Generator,
    MoleculeId,
    PairWise,
)
from smc_lammps.generate.structures.smc.smc_creator import SMC_Pos


@dataclass
class SMC:
    use_rigid_hinge: bool

    pos: SMC_Pos

    t_arms_heads_kleisin: AtomType
    t_hinge: AtomType
    t_atp: AtomType
    t_upper_site: AtomType
    t_middle_site: AtomType
    t_lower_site: AtomType
    t_ref_site: AtomType

    # bonds
    k_bond: float
    k_hinge: float
    max_bond_length: float

    # angles
    # Bending of elbows (kinkable arms, hence soft)
    k_elbow: float
    # Arms opening angle wrt ATP bridge (should be stiff)
    k_arm: float

    # impropers
    # Fixes site orientation (prevents free rotation, should be stiff)
    k_align_site: float
    # Folding stiffness of lower compartment (should be stiff)
    k_fold: float
    # Makes folding asymmetric (should be stiff)
    k_asymmetry: float

    # other
    bridge_width: float
    arm_length: float
    hinge_radius: float
    arms_angle_ATP: float
    folding_angle_ATP: float
    folding_angle_APO: float

    def _set_molecule_ids(self, use_rigid_hinge: bool) -> None:
        # Molecule for each rigid body
        self.mol_arm_dl = MoleculeId.get_next()
        self.mol_arm_ul = MoleculeId.get_next()
        self.mol_arm_ur = MoleculeId.get_next()
        self.mol_arm_dr = MoleculeId.get_next()
        self.mol_heads_kleisin = MoleculeId.get_next()
        self.mol_ATP = MoleculeId.get_next()

        self.mol_hinge_l = MoleculeId.get_next()
        if use_rigid_hinge:
            self.mol_hinge_r = self.mol_hinge_l
        else:
            self.mol_hinge_r = MoleculeId.get_next()

        self.mol_middle_site = self.mol_ATP
        self.mol_lower_site = self.mol_heads_kleisin

    def get_molecule_ids(self) -> List[int]:
        return [
            self.mol_arm_dl,
            self.mol_arm_ul,
            self.mol_arm_ur,
            self.mol_arm_dr,
            self.mol_heads_kleisin,
            self.mol_ATP,
            self.mol_hinge_l,
            self.mol_hinge_r,
            self.mol_middle_site,
            self.mol_lower_site,
        ]

    def _set_angles(self) -> None:
        self.align_arms = BAI_Type(
            BAI_Kind.ANGLE, "harmonic", f"{self.k_elbow} {180.0}\n"
        )
        arms_bridge_angle = np.rad2deg(
            np.arccos(self.bridge_width / self.arm_length / 4.0)
        )
        self.arms_bridge = BAI_Type(
            BAI_Kind.ANGLE, "harmonic", f"{self.k_arm} {arms_bridge_angle}\n"
        )
        self.hinge_arms = BAI_Type(BAI_Kind.ANGLE, "harmonic", f"{self.k_arm} {90.0}\n")

        self.arms_close = Generator.DynamicCoeffs(
            BAI_Kind.ANGLE,
            f"harmonic {self.k_arm} {np.rad2deg(np.arccos((self.bridge_width / 2.0 - self.hinge_radius) / self.arm_length))}\n",
            [self.arms_bridge],
        )
        self.arms_open = Generator.DynamicCoeffs(
            BAI_Kind.ANGLE,
            f"harmonic {self.k_arm} {self.arms_angle_ATP}\n",
            [self.arms_bridge],
        )

    def _set_impropers(self) -> None:
        self.imp_t1 = BAI_Type(
            BAI_Kind.IMPROPER, "harmonic", f"{self.k_align_site} {0.0}\n"
        )
        self.imp_t2 = BAI_Type(
            BAI_Kind.IMPROPER,
            "harmonic",
            f"{self.k_fold} {180.0 - self.folding_angle_APO}\n",
        )
        self.imp_t3 = BAI_Type(
            BAI_Kind.IMPROPER,
            "harmonic",
            f"{self.k_asymmetry} {abs(90.0 - self.folding_angle_APO)}\n",
        )
        self.imp_t4 = BAI_Type(
            BAI_Kind.IMPROPER, "harmonic", f"{self.k_align_site / 5.0} {90.0}\n"
        )

        self.kleisin_folds1 = Generator.DynamicCoeffs(
            BAI_Kind.IMPROPER,
            f"{self.k_fold} {180.0 - self.folding_angle_ATP}\n",
            [self.imp_t2],
        )
        self.kleisin_unfolds1 = Generator.DynamicCoeffs(
            BAI_Kind.IMPROPER,
            f"{self.k_fold} {180.0 - self.folding_angle_APO}\n",
            [self.imp_t2],
        )

        self.kleisin_folds2 = Generator.DynamicCoeffs(
            BAI_Kind.IMPROPER,
            f"{self.k_asymmetry} {abs(90.0 - self.folding_angle_ATP)}\n",
            [self.imp_t3],
        )
        self.kleisin_unfolds2 = Generator.DynamicCoeffs(
            BAI_Kind.IMPROPER,
            f"{self.k_asymmetry} {abs(90.0 - self.folding_angle_APO)}\n",
            [self.imp_t3],
        )

    def __post_init__(self) -> None:
        self._set_molecule_ids(self.use_rigid_hinge)
        self._set_angles()
        self._set_impropers()
        # create groups
        self.arm_dl_grp = AtomGroup(
            self.pos.r_arm_dl, self.t_arms_heads_kleisin, self.mol_arm_dl
        )
        self.arm_ul_grp = AtomGroup(
            self.pos.r_arm_ul, self.t_arms_heads_kleisin, self.mol_arm_ul
        )
        self.arm_ur_grp = AtomGroup(
            self.pos.r_arm_ur, self.t_arms_heads_kleisin, self.mol_arm_ur
        )
        self.arm_dr_grp = AtomGroup(
            self.pos.r_arm_dr, self.t_arms_heads_kleisin, self.mol_arm_dr
        )
        self.hk_grp = AtomGroup(
            self.pos.r_kleisin, self.t_arms_heads_kleisin, self.mol_heads_kleisin
        )

        self.atp_grp = AtomGroup(self.pos.r_ATP, self.t_atp, self.mol_ATP)

        self.hinge_l_grp = AtomGroup(
            self.pos.r_hinge[: len(self.pos.r_hinge) // 2],
            self.t_hinge,
            self.mol_hinge_l,
            charge=-0.1,
        )
        self.hinge_r_grp = AtomGroup(
            self.pos.r_hinge[len(self.pos.r_hinge) // 2 :],
            self.t_hinge,
            self.mol_hinge_r,
            charge=-0.1,
        )
        self.upper_site_grp = AtomGroup(
            self.pos.r_upper_site, self.t_upper_site, self.mol_hinge_l
        )

        # split M in three parts

        cut = 2
        self.middle_site_grp = AtomGroup(
            self.pos.r_middle_site[:cut], self.t_middle_site, self.mol_middle_site
        )
        self.middle_site_atp_grp = AtomGroup(
            self.pos.r_middle_site[cut:-1], self.t_atp, self.mol_middle_site
        )
        # ref site
        self.middle_site_ref_grp = AtomGroup(
            self.pos.r_middle_site[-1:], self.t_ref_site, self.mol_middle_site
        )

        # split B in two parts

        cut = 3
        self.lower_site_grp = AtomGroup(
            self.pos.r_lower_site[:cut], self.t_lower_site, self.mol_lower_site
        )
        self.lower_site_arm_grp = AtomGroup(
            self.pos.r_lower_site[cut:], self.t_arms_heads_kleisin, self.mol_lower_site
        )

        self.left_attach_hinge = len(self.hinge_l_grp.positions) // 2
        self.right_attach_hinge = len(self.hinge_r_grp.positions) // 2

    def get_groups(self) -> List[AtomGroup]:
        return [
            self.arm_dl_grp,
            self.arm_ul_grp,
            self.arm_ur_grp,
            self.arm_dr_grp,
            self.hk_grp,
            self.atp_grp,
            self.upper_site_grp,
            self.middle_site_grp,
            self.middle_site_atp_grp,
            self.middle_site_ref_grp,
            self.lower_site_grp,
            self.lower_site_arm_grp,
            self.hinge_l_grp,
            self.hinge_r_grp,
        ]

    def get_bonds(self, hinge_opening: float | None = None) -> List[BAI]:
        # Every joint is kept in place through bonds
        attach = BAI_Type(
            BAI_Kind.BOND,
            "fene/expand",
            f"{self.k_bond} {self.max_bond_length} {0.0} {0.0} {0.0}\n",
        )

        bonds = [
            # attach arms together
            BAI(attach, (self.arm_dl_grp, -1), (self.arm_ul_grp, 0)),
            BAI(attach, (self.arm_ur_grp, -1), (self.arm_dr_grp, 0)),
            # attach hinge and arms
            BAI(
                attach,
                (self.arm_ul_grp, -1),
                (self.hinge_l_grp, self.left_attach_hinge),
            ),
            BAI(
                attach,
                (self.arm_ur_grp, 0),
                (self.hinge_r_grp, self.right_attach_hinge),
            ),
            # attach atp bridge to arms
            BAI(attach, (self.arm_dr_grp, -1), (self.atp_grp, -1)),
            BAI(attach, (self.atp_grp, 0), (self.arm_dl_grp, 0)),
            # attach bridge to hk
            BAI(attach, (self.atp_grp, -1), (self.hk_grp, 0)),
            BAI(attach, (self.hk_grp, -1), (self.atp_grp, 0)),
        ]

        if not self.use_rigid_hinge:
            assert hinge_opening is not None
            hinge_bond = BAI_Type(
                BAI_Kind.BOND, "harmonic", f"{self.k_hinge} {hinge_opening}\n"
            )
            bonds += [
                # connect Left and Right hinge pieces together
                BAI(hinge_bond, (self.hinge_l_grp, -1), (self.hinge_r_grp, 0)),
                BAI(hinge_bond, (self.hinge_l_grp, 0), (self.hinge_r_grp, -1)),
            ]
        return bonds

    def get_angles(self) -> List[BAI]:
        return [
            # keep left arms rigid (prevent too much bending)
            BAI(
                self.align_arms,
                (self.arm_dl_grp, 0),
                (self.arm_ul_grp, 0),
                (self.arm_ul_grp, -1),
            ),
            # same, but for right arms
            BAI(
                self.align_arms,
                (self.arm_ur_grp, 0),
                (self.arm_ur_grp, -1),
                (self.arm_dr_grp, -1),
            ),
            # keep hinge perpendicular to arms
            BAI(
                self.hinge_arms,
                (self.arm_ul_grp, -2),
                (self.arm_ul_grp, -1),
                (self.hinge_l_grp, self.left_attach_hinge + 1),
            ),
            BAI(
                self.hinge_arms,
                (self.arm_ul_grp, -2),
                (self.arm_ul_grp, -1),
                (self.hinge_l_grp, self.left_attach_hinge - 1),
            ),
            BAI(
                self.hinge_arms,
                (self.arm_ur_grp, 1),
                (self.arm_ur_grp, 0),
                (self.hinge_r_grp, self.right_attach_hinge - 1),
            ),
            BAI(
                self.hinge_arms,
                (self.arm_ur_grp, 1),
                (self.arm_ur_grp, 0),
                (self.hinge_r_grp, self.right_attach_hinge + 1),
            ),
            # prevent too much bending between lower arms and the bridge
            BAI(
                self.arms_bridge,
                (self.arm_dl_grp, -1),
                (self.arm_dl_grp, 0),
                (self.atp_grp, -1),
            ),
            BAI(
                self.arms_bridge,
                (self.arm_dr_grp, 0),
                (self.arm_dr_grp, -1),
                (self.atp_grp, 0),
            ),
        ]

    def get_impropers(self) -> List[BAI]:
        kleisin_center = len(self.pos.r_kleisin) // 2
        return [
            # Fix orientation of ATP/kleisin bridge
            # WARNING: siteM is split into groups, be careful with index
            BAI(
                self.imp_t1,
                (self.arm_dl_grp, -1),
                (self.arm_dl_grp, 0),
                (self.atp_grp, -1),
                (self.middle_site_grp, 1),
            ),
            BAI(
                self.imp_t1,
                (self.arm_dr_grp, 0),
                (self.arm_dr_grp, -1),
                (self.atp_grp, 0),
                (self.middle_site_grp, 1),
            ),
            BAI(
                self.imp_t2,
                (self.arm_dl_grp, -1),
                (self.arm_dl_grp, 0),
                (self.atp_grp, -1),
                (self.hk_grp, kleisin_center),
            ),
            BAI(
                self.imp_t2,
                (self.arm_dr_grp, 0),
                (self.arm_dr_grp, -1),
                (self.atp_grp, 0),
                (self.hk_grp, kleisin_center),
            ),
            # prevent kleisin ring from swaying too far relative to the bridge
            BAI(
                self.imp_t3,
                (self.middle_site_ref_grp, 0),
                (self.arm_dl_grp, 0),
                (self.arm_dr_grp, -1),
                (self.hk_grp, kleisin_center),
            ),
            # fix hinge to a plane
            BAI(
                self.imp_t1,
                (self.hinge_l_grp, 0),
                (self.hinge_l_grp, -1),
                (self.hinge_r_grp, 0),
                (self.hinge_r_grp, -1),
            ),
            BAI(
                self.imp_t1,
                (self.hinge_l_grp, 0),
                (self.hinge_l_grp, self.left_attach_hinge),
                (self.hinge_r_grp, 0),
                (self.hinge_r_grp, self.right_attach_hinge),
            ),
            # fix hinge perpendicular to arms plane
            BAI(
                self.imp_t4,
                (self.arm_ul_grp, -2),
                (self.arm_ul_grp, -1),
                (self.hinge_l_grp, self.left_attach_hinge - 1),
                (self.hinge_l_grp, self.left_attach_hinge + 1),
            ),
            BAI(
                self.imp_t4,
                (self.arm_ur_grp, 1),
                (self.arm_ur_grp, 0),
                (self.hinge_r_grp, self.right_attach_hinge + 1),
                (self.hinge_r_grp, self.right_attach_hinge - 1),
            ),
            # # keep hinge aligned with bridge axis
            # BAI(imp_t1, (self.hingeL_group, self.left_attach_hinge), (self.hingeR_group, self.right_attach_hinge), (self.atp_group, 0), (self.atp_group, -1)),
            BAI(
                self.imp_t4,
                (self.upper_site_grp, 0),
                (self.upper_site_grp, len(self.upper_site_grp.positions) // 2),
                (self.atp_grp, len(self.atp_grp.positions) // 2),
                (self.atp_grp, -1),
            ),
        ]

    def add_repel_interactions(
        self, pair_inter: PairWise, eps: float, sigma: float, r_cut: float
    ) -> None:
        # short-range repulsion
        sigma_short = sigma / 10.0
        r_cut_short = r_cut / 10.0

        # prevent hinges from overlapping
        pair_inter.add_interaction(
            self.t_hinge,
            self.t_hinge,
            eps,
            sigma_short,
            r_cut_short,
        )
        # prevent upper site from overlapping with arms
        pair_inter.add_interaction(
            self.t_arms_heads_kleisin,
            self.t_upper_site,
            eps,
            sigma_short,
            r_cut_short,
        )
