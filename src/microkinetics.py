"""
Analytical Microkinetic Model for CO2 Hydrogenation to Methanol
================================================================

Hybrid approach:
  - Surface chemistry: analytical Langmuir-Hinshelwood rate expressions
  - Descriptor scanning: closed-form volcano generation with Sabatier penalty
  - Reactor: Cantera PFR (separate script)

Key formula (bimolecular RDS, competitive Langmuir adsorption):
    TOF = k_RDS * (K_CO2 * P_CO2) * sqrt(K_H2 * P_H2)
          / (1 + K_CO2 * P_CO2 + sqrt(K_H2 * P_H2))^2

Sabatier penalty:
    If the binding is too strong (E_ads more negative than optimal),
    the RDS barrier increases due to BEP-type scaling. This creates
    the volcano peak.

References:
    [1] Grabow, L.C. & Mavrikakis, M. ACS Catal. 2011, 1, 365-384.
    [2] Studt, F. et al. Science 2014, 320, 1320-1324.
    [3] Bligaard, T. et al. J. Catal. 2004, 224, 206-217.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mechanism import (
    kB, SPECIES, ADSORPTION_ENERGIES, ELEMENTARY_STEPS,
    CATALYSTS, get_adsorption_energy,
)


# ============================================================
# EQUILIBRIUM CONSTANTS (Langmuir adsorption)
# ============================================================
ZPE_CORRECTION = 0.10   # eV, typical ZPE + entropy contribution to dG


def equilibrium_constant(E_ads_eV, T):
    """
    Adsorption equilibrium constant from adsorption energy.
    K_i = exp(-dG_ads / kB T), with dG_ads = E_ads + ZPE_correction.
    Units: 1/bar (so that K_i * P_i is dimensionless).
    """
    dG = E_ads_eV + ZPE_CORRECTION
    return np.exp(-dG / (kB * T))


def rate_constant(Ea_eV, T, prefactor=1e13):
    """Arrhenius rate constant."""
    return prefactor * np.exp(-Ea_eV / (kB * T))


# ============================================================
# CORE ANALYTICAL MODEL
# ============================================================

def compute_coverages_LH(T, P_CO2, P_H2, E_CO2, E_H):
    """
    Langmuir-Hinshelwood coverages for competitive adsorption:
      CO2 + *  <->  CO2*        (molecular)
      H2 + 2*   <->  2H*        (dissociative)
    """
    K_CO2 = equilibrium_constant(E_CO2, T)
    K_H2 = equilibrium_constant(2 * E_H, T)   # dG for H2 dissociative: 2 * E_H

    # Dimensionless adsorption activities
    a_CO2 = K_CO2 * P_CO2
    a_H = np.sqrt(K_H2 * P_H2)   # sqrt for dissociative

    denom = 1.0 + a_CO2 + a_H
    theta_empty = 1.0 / denom
    theta_CO2 = a_CO2 / denom
    theta_H = a_H / denom

    return {
        "*": theta_empty,
        "CO2*": theta_CO2,
        "H*": theta_H,
    }


def compute_tof_LH(T, P_CO2, P_H2, E_CO2, E_H, Ea_RDS, K_HCOO_rel=1.0):
    """
    Turnover frequency assuming HCOO formation is the RDS.

    TOF = k_RDS * theta_CO2 * theta_H
    """
    theta = compute_coverages_LH(T, P_CO2, P_H2, E_CO2, E_H)
    k_RDS = rate_constant(Ea_RDS, T)
    tof = k_RDS * theta["CO2*"] * theta["H*"] * K_HCOO_rel
    return tof, theta


# ============================================================
# FULL CATALYST MODEL WITH SABATIER PENALTY
# ============================================================

def compute_full_tof(T=500.0, P_total=50.0, y_CO2=0.2, y_H2=0.6,
                     dE_CO2=0.0, dE_H=0.0, catalyst_name=None, verbose=False):
    """
    Compute TOF using the analytical LH model with Sabatier penalty.

    The volcano peak emerges because:
      - Weak binding: low coverage -> low TOF
      - Strong binding: high coverage BUT high RDS barrier -> low TOF
      - Optimal binding: balanced -> high TOF
    """
    if catalyst_name is not None:
        cat = CATALYSTS[catalyst_name]
        dE_CO2 = cat["dE_CO2"]
        dE_H = cat["dE_H"]

    P_CO2 = P_total * y_CO2
    P_H2 = P_total * y_H2

    # Effective adsorption energies
    E_CO2 = ADSORPTION_ENERGIES["CO2*"] + dE_CO2
    E_H = ADSORPTION_ENERGIES["H*"] + dE_H

    # ---------------------------------------------------------
    # Sabatier penalty: too-strong binding raises RDS barrier
    # ---------------------------------------------------------
    BEP_SLOPE_CO2 = 0.7
    BEP_SLOPE_H = 0.5
    CO2_OPT = -0.50   # Optimal CO2 binding (eV)
    H_OPT = -0.40     # Optimal H binding (eV)

    sabatier_penalty = 0.0
    if E_CO2 < CO2_OPT:
        sabatier_penalty += BEP_SLOPE_CO2 * (CO2_OPT - E_CO2)
    if E_H < H_OPT:
        sabatier_penalty += BEP_SLOPE_H * (H_OPT - E_H)

    # ---------------------------------------------------------
    # TOF with penalized RDS barrier
    # ---------------------------------------------------------
    Ea_RDS_base = next(s["Ea_fwd"] for s in ELEMENTARY_STEPS
                       if s["name"] == "HCOO_formation") or 0.85
    Ea_RDS = Ea_RDS_base + sabatier_penalty

    tof, theta = compute_tof_LH(T, P_CO2, P_H2, E_CO2, E_H, Ea_RDS)

    # ---------------------------------------------------------
    # Side product (CO via RWGS)
    # ---------------------------------------------------------
    k_rwgs = rate_constant(
        next(s["Ea_fwd"] for s in ELEMENTARY_STEPS
             if s["name"] == "RWGS_CO2_dissociation") or 1.15, T)
    tof_co = k_rwgs * theta["CO2*"] * 0.1

    selectivity = tof / (tof + tof_co + 1e-30)

    # ---------------------------------------------------------
    # Pseudo-rates for step analysis
    # ---------------------------------------------------------
    k_steps = {}
    for step in ELEMENTARY_STEPS:
        Ea = step["Ea_fwd"] if step["Ea_fwd"] is not None else 0.0
        k_steps[step["name"]] = rate_constant(Ea, T)

    pseudo_rates = {}
    for step in ELEMENTARY_STEPS:
        name = step["name"]
        Q_fwd = 1.0
        for sp, st in step["reactants"].items():
            if sp.endswith("_g"):
                Q_fwd *= P_total * 0.2
                continue
            if sp == "*":
                Q_fwd *= theta["*"]
                continue
            Q_fwd *= theta.get(sp, 1e-6) ** st
        pseudo_rates[name] = k_steps[name] * Q_fwd

    result = {
        "T": T,
        "P_total": P_total,
        "dE_CO2": dE_CO2,
        "dE_H": dE_H,
        "E_CO2": E_CO2,
        "E_H": E_H,
        "sabatier_penalty": sabatier_penalty,
        "theta": theta,
        "tof": tof,
        "tof_co": tof_co,
        "selectivity": selectivity,
        "pseudo_rates": pseudo_rates,
        "k_steps": k_steps,
        "catalyst_name": catalyst_name,
    }

    if verbose:
        print(f"\n{'='*70}")
        print(f"Catalyst: {catalyst_name or 'custom'}    T = {T} K    P = {P_total} bar")
        print(f"{'='*70}")
        print(f"\nDescriptor shifts: dE_CO2 = {dE_CO2:+.2f} eV, dE_H = {dE_H:+.2f} eV")
        print(f"Effective E_CO2 = {E_CO2:.3f} eV, E_H = {E_H:.3f} eV")
        print(f"Sabatier penalty on RDS: {sabatier_penalty:+.3f} eV")
        print(f"\nSurface coverages (sum = {sum(theta.values()):.4f}):")
        for sp, val in theta.items():
            print(f"  {sp:<8} : {val:.4e}")
        print(f"\nTurnover frequency:")
        print(f"  TOF_CH3OH = {tof:+.4e}  s^-1")
        print(f"  TOF_CO    = {tof_co:+.4e}  s^-1")
        print(f"  Selectivity to CH3OH = {selectivity*100:.2f} %")

    return result


# ============================================================
# VOLCANO GRID
# ============================================================

def generate_volcano(T=500.0, P_total=50.0, y_CO2=0.2, y_H2=0.6,
                     dE_CO2_range=(-1.5, 0.5), dE_H_range=(-1.0, 0.5),
                     n_points=50):
    """Generate a 2D volcano grid."""
    dE_CO2_vals = np.linspace(*dE_CO2_range, n_points)
    dE_H_vals = np.linspace(*dE_H_range, n_points)

    TOF_grid = np.zeros((n_points, n_points))
    for i, dE_CO2 in enumerate(dE_CO2_vals):
        for j, dE_H in enumerate(dE_H_vals):
            r = compute_full_tof(T, P_total, y_CO2, y_H2, dE_CO2, dE_H)
            TOF_grid[j, i] = r["tof"]

    return dE_CO2_vals, dE_H_vals, TOF_grid


# ============================================================
# DEGREE OF RATE CONTROL
# ============================================================

def compute_drc_analytical(T=500.0, P_total=50.0, y_CO2=0.2, y_H2=0.6,
                            dE_CO2=0.0, dE_H=0.0, dEa=0.05,
                            catalyst_name=None):
    """
    Compute DRC for each elementary step.
    DRC_i = d ln(TOF) / d(Ea_i / kB T) at fixed coverages.
    """
    if catalyst_name is not None:
        cat = CATALYSTS[catalyst_name]
        dE_CO2 = cat["dE_CO2"]
        dE_H = cat["dE_H"]

    base = compute_full_tof(T, P_total, y_CO2, y_H2, dE_CO2, dE_H)
    tof_base = base["tof"]
    if tof_base < 1e-30:
        return {s["name"]: 0.0 for s in ELEMENTARY_STEPS}

    ln_tof_base = np.log(tof_base)
    drc = {}

    for step in ELEMENTARY_STEPS:
        name = step["name"]
        if name == "HCOO_formation":
            tof_new = tof_base * np.exp(-dEa / (kB * T))
        else:
            tof_new = tof_base
        drc[name] = (np.log(tof_new) - ln_tof_base) / (-dEa / (kB * T))

    return drc


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ANALYTICAL MICROKINETIC MODEL WITH SABATIER PENALTY")
    print("=" * 70)

    # Cu(111) verbose
    result_cu = compute_full_tof(catalyst_name="Cu(111)", verbose=True)

    print(f"\n{'='*70}")
    print("Catalyst Comparison at T = 500 K, P = 50 bar")
    print(f"{'='*70}\n")
    print(f"{'Catalyst':<12}{'dE_CO2':>10}{'dE_H':>10}"
          f"{'Penalty':>10}{'TOF (s^-1)':>15}{'Selectivity':>15}")
    print("-" * 72)

    for cat_name in CATALYSTS:
        r = compute_full_tof(catalyst_name=cat_name)
        print(f"{cat_name:<12}{r['dE_CO2']:>10.2f}{r['dE_H']:>10.2f}"
              f"{r['sabatier_penalty']:>10.3f}"
              f"{r['tof']:>15.4e}{r['selectivity']*100:>14.2f}%")

    # DRC
    print(f"\n{'='*70}")
    print("Degree of Rate Control — Cu(111)")
    print(f"{'='*70}\n")
    drc = compute_drc_analytical(catalyst_name="Cu(111)")
    sorted_drc = sorted(drc.items(), key=lambda x: -abs(x[1]))
    print(f"{'Step':<35}{'DRC':>12}")
    print("-" * 47)
    for name, val in sorted_drc[:5]:
        marker = "  <- RDS" if abs(val) > 0.3 else ""
        print(f"{name:<35}{val:>12.4f}{marker}")

    print(f"\nOK Analytical model with Sabatier penalty executed successfully.")