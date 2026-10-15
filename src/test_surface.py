"""
Test Cantera Surface Chemistry — with REAL elements
Tests H2 dissociative adsorption on a Pt-like surface
"""

import cantera as ct
import os

YAML_MECH = """
units: {length: cm, quantity: mol, activation-energy: J/mol}

phases:
- name: gas
  thermo: ideal-gas
  species: [H2, H2O]
  kinetics: gas
  reactions: all
  state: {T: 500, P: 1 atm}

- name: surface
  thermo: ideal-surface
  species: [H(s), O(s), X]
  kinetics: surface
  reactions: all
  site_density: 1.77e-9
  state: {T: 500, P: 1 atm}

species:
- name: H2
  composition: {H: 2}
  thermo:
    model: NASA7
    temperature-ranges: [300, 1000, 3000]
    data:
    - [3.3, 0.0001, 0, 0, 0, -1000, -3.3]
    - [3.0, 0.0005, 0, 0, 0, -1000, -2.5]

- name: H2O
  composition: {H: 2, O: 1}
  thermo:
    model: NASA7
    temperature-ranges: [300, 1000, 3000]
    data:
    - [4.0, -0.001, 0.000003, 0, 0, -30000, -0.8]
    - [3.0, 0.001, 0, 0, 0, -30000, 4.0]

- name: H(s)
  composition: {H: 1}
  thermo:
    model: NASA7
    temperature-ranges: [300, 1000, 3000]
    data:
    - [2.0, 0, 0, 0, 0, -5000, 3.0]
    - [2.0, 0, 0, 0, 0, -5000, 3.0]
  sites: 1

- name: O(s)
  composition: {O: 1}
  thermo:
    model: NASA7
    temperature-ranges: [300, 1000, 3000]
    data:
    - [2.0, 0, 0, 0, 0, -8000, 3.0]
    - [2.0, 0, 0, 0, 0, -8000, 3.0]
  sites: 1

- name: X
  composition: {}
  thermo:
    model: NASA7
    temperature-ranges: [300, 1000, 3000]
    data:
    - [2.0, 0, 0, 0, 0, 0, 3.0]
    - [2.0, 0, 0, 0, 0, 0, 3.0]
  sites: 1

reactions:
- equation: H2 + 2 X <=> 2 H(s)
  rate-constant: {A: 1e13, b: 0, Ea: 0}

- equation: H(s) + O(s) <=> H2O + 2 X
  rate-constant: {A: 1e13, b: 0, Ea: 60000}
"""

yaml_path = "data/test_surface.yaml"
os.makedirs("data", exist_ok=True)
with open(yaml_path, "w") as f:
    f.write(YAML_MECH)

print(f"Written: {yaml_path}\n")

try:
    surf = ct.Interface(yaml_path, "surface")
    print("SUCCESS: Surface mechanism loaded")
    print(f"  Species: {surf.species_names}")
    print(f"  Site density: {surf.site_density:.3e} mol/cm^2")
    print(f"  Reactions: {surf.n_reactions}")
    print(f"  Reaction list: {surf.reaction_equations()}")

    gas = surf.adjacent["gas"]
    gas.TPX = 500, 1e5, "H2:1"
    surf.TP = 500, 1e5
    surf.coverages = "X:1"

    print(f"\nInitial gas: {gas.T:.1f} K, {gas.P/1e5:.2f} bar")
    print(f"Initial surface:")
    for sp in surf.species_names:
        idx = surf.species_index(sp)
        print(f"  {sp}: theta = {surf.coverages[idx]:.4e}")

    print("\nOK Cantera surface chemistry works with real elements.")
    print("Ready to build the full CO2-to-methanol mechanism.")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()