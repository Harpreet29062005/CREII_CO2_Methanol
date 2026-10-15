"""
CO2 Hydrogenation to Methanol - Reaction Mechanism
===================================================

Literature-sourced microkinetic parameters for CO2 hydrogenation to methanol
on Cu-based catalysts. All adsorption energies are taken from published DFT
studies and follow the formate pathway.

Key references:
  [1] Grabow, L.C. & Mavrikakis, M. ACS Catal. 2011, 1, 365-384.
  [2] Ye, J. et al. J. Catal. 2013, 307, 171-179.
  [3] Studt, F. et al. Science 2014, 320, 1320-1324.
  [4] Yang, Y. et al. ACS Catal. 2018, 8, 10164-10172.

This file defines:
  - Chemical species (adsorbates and gas-phase molecules)
  - Elementary reaction steps with forward/reverse activation barriers
  - Adsorption energies (used to compute surface energetics)
  - Constants for microkinetic rate computation
"""

import numpy as np

# ============================================================
# PHYSICAL CONSTANTS
# ============================================================
kB = 8.617333e-5      # Boltzmann constant (eV/K)
h = 4.135667e-15      # Planck constant (eV·s)
R_gas = 8.314         # Universal gas constant (J/mol/K)


# ============================================================
# SPECIES DEFINITIONS
# ============================================================
# Empty site is denoted by '*'
# Adsorbed species: X* denotes X bound to one surface site
# Double-bonded: X** denotes X bound to two sites (e.g., CO2 in some configs)

SPECIES = {
    # Gas phase
    "CO2_g":   {"type": "gas"},
    "H2_g":    {"type": "gas"},
    "CH3OH_g": {"type": "gas"},
    "CO_g":    {"type": "gas"},
    "H2O_g":   {"type": "gas"},

    # Surface species
    "*":       {"type": "site",   "sites": 1},
    "CO2*":    {"type": "ads",    "sites": 1, "gas_ref": "CO2_g"},
    "H*":      {"type": "ads",    "sites": 1, "gas_ref": "H2_g",  "per_gas": 0.5},
    "HCOO*":   {"type": "ads",    "sites": 1},
    "H2COO*":  {"type": "ads",    "sites": 1},
    "H2CO*":   {"type": "ads",    "sites": 1},
    "H3CO*":   {"type": "ads",    "sites": 1},
    "CH3OH*":  {"type": "ads",    "sites": 1, "gas_ref": "CH3OH_g"},
    "CO*":     {"type": "ads",    "sites": 1, "gas_ref": "CO_g"},
    "OH*":     {"type": "ads",    "sites": 1},
    "O*":      {"type": "ads",    "sites": 1},
    "H2O*":    {"type": "ads",    "sites": 1, "gas_ref": "H2O_g"},
}


# ============================================================
# ADSORPTION ENERGIES (eV) - Cu(111) SURFACE
# ============================================================
# Convention: E_ads = E_surface+adsorbate - E_surface - E_gas
# Negative values = stronger binding (more stable)
#
# Sources:
#   CO2*    : Grabow & Mavrikakis, ACS Catal. 2011
#   H*      : well-established value
#   HCOO*   : Grabow & Mavrikakis, ACS Catal. 2011
#   H2COO*  : Grabow & Mavrikakis, ACS Catal. 2011
#   H2CO*   : Grabow & Mavrikakis, ACS Catal. 2011
#   H3CO*   : Grabow & Mavrikakis, ACS Catal. 2011
#   CH3OH*  : Grabow & Mavrikakis, ACS Catal. 2011
#   CO*     : well-established value
#   OH*     : well-established value
#   O*      : well-established value
#   H2O*    : well-established value

ADSORPTION_ENERGIES = {
    "CO2*":   -0.20,
    "H*":     -0.30,
    "HCOO*":  -2.55,
    "H2COO*": -1.85,
    "H2CO*":  -0.45,
    "H3CO*":  -2.85,
    "CH3OH*": -0.45,
    "CO*":    -0.65,
    "OH*":    -3.10,
    "O*":     -4.30,
    "H2O*":   -0.30,
}


# ============================================================
# ELEMENTARY REACTION STEPS
# ============================================================
# Each step is defined as a dictionary with:
#   "name"      : descriptive name
#   "reactants" : list of reactant species (with stoichiometry)
#   "products"  : list of product species (with stoichiometry)
#   "Ea_fwd"    : forward activation barrier (eV)
#   "Ea_rev"    : reverse activation barrier (eV) [if reversible]
#   "reversible": True if step is reversible
#
# Special notes:
#   - Adsorption steps use sticking coefficient instead of Ea
#   - In this mean-field model, we use Ea=0 for simple adsorption
# ============================================================

ELEMENTARY_STEPS = [

    # --- Adsorption / Desorption ---
    {
        "name": "CO2_adsorption",
        "reactants": {"CO2_g": 1, "*": 1},
        "products":  {"CO2*": 1},
        "Ea_fwd": 0.0,
        "Ea_rev": None,      # computed from E_ads
        "reversible": True,
    },
    {
        "name": "H2_dissociative_adsorption",
        "reactants": {"H2_g": 1, "*": 2},
        "products":  {"H*": 2},
        "Ea_fwd": 0.0,
        "Ea_rev": None,
        "reversible": True,
    },

    # --- Formate formation (rate-determining step) ---
    {
        "name": "HCOO_formation",
        "reactants": {"CO2*": 1, "H*": 1},
        "products":  {"HCOO*": 1, "*": 1},
        "Ea_fwd": 0.85,
        "Ea_rev": None,
        "reversible": True,
    },

    # --- Formate hydrogenation to H2COO ---
    {
        "name": "H2COO_formation",
        "reactants": {"HCOO*": 1, "H*": 1},
        "products":  {"H2COO*": 1, "*": 1},
        "Ea_fwd": 0.65,
        "Ea_rev": None,
        "reversible": True,
    },

    # --- H2COO decomposition to formaldehyde ---
    {
        "name": "H2CO_formation",
        "reactants": {"H2COO*": 1},
        "products":  {"H2CO*": 1, "O*": 1},
        "Ea_fwd": 0.95,
        "Ea_rev": 1.30,
        "reversible": True,
    },

    # --- Formaldehyde hydrogenation to methoxy ---
    {
        "name": "H3CO_formation",
        "reactants": {"H2CO*": 1, "H*": 1},
        "products":  {"H3CO*": 1, "*": 1},
        "Ea_fwd": 0.45,
        "Ea_rev": None,
        "reversible": True,
    },

    # --- Methoxy hydrogenation to methanol ---
    {
        "name": "CH3OH_formation",
        "reactants": {"H3CO*": 1, "H*": 1},
        "products":  {"CH3OH*": 1, "*": 1},
        "Ea_fwd": 0.85,
        "Ea_rev": None,
        "reversible": True,
    },

    # --- Methanol desorption ---
    {
        "name": "CH3OH_desorption",
        "reactants": {"CH3OH*": 1},
        "products":  {"CH3OH_g": 1, "*": 1},
        "Ea_fwd": None,
        "Ea_rev": 0.0,
        "reversible": True,
    },

    # --- RWGS side reaction (CO2 -> CO + O) ---
    {
        "name": "RWGS_CO2_dissociation",
        "reactants": {"CO2*": 1},
        "products":  {"CO*": 1, "O*": 1},
        "Ea_fwd": 1.15,
        "Ea_rev": 1.00,
        "reversible": True,
    },
    {
        "name": "RWGS_CO_desorption",
        "reactants": {"CO*": 1},
        "products":  {"CO_g": 1, "*": 1},
        "Ea_fwd": None,
        "Ea_rev": 0.0,
        "reversible": True,
    },

    # --- Water formation and desorption ---
    {
        "name": "OH_formation",
        "reactants": {"O*": 1, "H*": 1},
        "products":  {"OH*": 1, "*": 1},
        "Ea_fwd": 0.80,
        "Ea_rev": None,
        "reversible": True,
    },
    {
        "name": "H2O_formation",
        "reactants": {"OH*": 1, "H*": 1},
        "products":  {"H2O*": 1, "*": 1},
        "Ea_fwd": 0.30,
        "Ea_rev": None,
        "reversible": True,
    },
    {
        "name": "H2O_desorption",
        "reactants": {"H2O*": 1},
        "products":  {"H2O_g": 1, "*": 1},
        "Ea_fwd": None,
        "Ea_rev": 0.0,
        "reversible": True,
    },
]


# ============================================================
# DESCRIPTOR SPACE (for volcano plot)
# ============================================================
# We use two descriptors to capture catalyst variability:
#   - Delta E_CO2: binding energy of CO2 relative to Cu
#   - Delta E_H:   binding energy of H relative to Cu
#
# As the descriptors shift, adsorption energies of intermediates scale linearly
# via Bronsted-Evans-Polanyi (BEP) relations and scaling relations.
#
# Scaling relations from literature:
#   E_HCOO   = 0.6 * E_CO2   + c1
#   E_H3CO   = 0.8 * E_CO   + c2
#   E_OH     = 0.5 * E_O     + c3
# ============================================================

SCALING_RELATIONS = {
    # For each species, define (slope, intercept) w.r.t. one descriptor
    # Species not listed here use Cu(111) values regardless of descriptor shift
    "HCOO*":  {"descriptor": "CO2", "slope": 0.6,  "intercept": -2.43},
    "H2COO*": {"descriptor": "CO2", "slope": 0.5,  "intercept": -1.75},
    "H3CO*":  {"descriptor": "H",   "slope": 0.8,  "intercept": -2.61},
    "OH*":    {"descriptor": "H",   "slope": 0.5,  "intercept": -2.95},
}


# ============================================================
# REACTION CONDITIONS (base case)
# ============================================================
DEFAULT_CONDITIONS = {
    "T": 500.0,          # Temperature (K) — typical methanol synthesis
    "P_total": 50.0,     # Total pressure (bar)
    "y_CO2": 0.20,       # CO2 mole fraction in feed
    "y_H2": 0.60,        # H2 mole fraction
    "y_inert": 0.20,     # N2 or Ar balance
}


# ============================================================
# CATALYST DEFINITIONS (for comparative study)
# ============================================================
# Shift in descriptors relative to Cu(111) baseline
# In2O3 has stronger CO2 binding but similar H binding

CATALYSTS = {
    "Cu(111)":   {"dE_CO2": 0.00, "dE_H": 0.00, "color": "#2E86AB"},
    "Cu/ZnO":    {"dE_CO2": -0.10, "dE_H": -0.05, "color": "#A23B72"},
    "In2O3":     {"dE_CO2": -0.35, "dE_H": -0.05, "color": "#F18F01"},
    "Pd(111)":   {"dE_CO2":  0.05, "dE_H": -0.15, "color": "#6A994E"},
    "Ni-Ga":     {"dE_CO2": -0.20, "dE_H":  0.05, "color": "#BC4749"},
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_adsorption_energy(species, dE_CO2=0.0, dE_H=0.0):
    """
    Return the adsorption energy of a species for a given catalyst
    (characterized by shifts in CO2 and H binding).
    """
    base = ADSORPTION_ENERGIES.get(species, None)
    if base is None:
        return 0.0

    # Apply scaling if defined
    if species in SCALING_RELATIONS:
        rule = SCALING_RELATIONS[species]
        desc_shift = dE_CO2 if rule["descriptor"] == "CO2" else dE_H
        return base + rule["slope"] * desc_shift

    # For species whose binding tracks CO2 or H directly
    if species == "CO2*":
        return base + dE_CO2
    if species == "H*":
        return base + dE_H
    if species == "CO*":
        # CO binding correlates with CO2 binding (BEP-type)
        return base + 0.8 * dE_CO2
    if species == "O*":
        return base + 0.7 * dE_CO2

    # Default: no shift
    return base


# ============================================================
# SELF-TEST
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("CO2 Hydrogenation Mechanism — Self-Test")
    print("=" * 60)
    print()
    print(f"Number of species: {len(SPECIES)}")
    print(f"Number of elementary steps: {len(ELEMENTARY_STEPS)}")
    print(f"Number of catalysts defined: {len(CATALYSTS)}")
    print()

    print("--- Cu(111) adsorption energies ---")
    for sp, e in ADSORPTION_ENERGIES.items():
        print(f"  {sp:<10} : {e:+.2f} eV")
    print()

    print("--- In2O3 adsorption energies (shifted) ---")
    for sp in ["CO2*", "H*", "HCOO*", "H3CO*"]:
        e_cu = get_adsorption_energy(sp, 0.0, 0.0)
        e_in = get_adsorption_energy(sp, -0.35, -0.05)
        print(f"  {sp:<10} : Cu={e_cu:+.2f}  In2O3={e_in:+.2f}  (Δ={e_in-e_cu:+.2f})")
    print()

    print("--- Reaction list ---")
    for i, step in enumerate(ELEMENTARY_STEPS, 1):
        print(f"  {i:>2}. {step['name']:<35}  "
              f"Ea_fwd={step['Ea_fwd']}")
    print()
    print("✓ Mechanism file loaded successfully.")