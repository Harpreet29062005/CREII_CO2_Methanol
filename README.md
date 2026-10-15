\# CREII — Multiscale Computational Study of CO₂ Hydrogenation to Methanol



\*\*Author:\*\* Harpreet Thappa

\*\*Course:\*\* CREII (Computational Study of Heterogeneous Catalytic Reactions)

\*\*Institution:\*\* NIT Srinagar — Department of Chemical Engineering

\*\*Date:\*\* November 2026



\---



\## Overview



This project presents a \*\*multiscale computational study\*\* of CO₂ hydrogenation to methanol over Cu-based catalysts. It combines:



1\. \*\*Analytical microkinetic modeling\*\* — Langmuir-Hinshelwood surface chemistry

2\. \*\*Sabatier volcano analysis\*\* — descriptor-based catalyst screening

3\. \*\*Degree of Rate Control (DRC)\*\* — identification of the rate-determining step

4\. \*\*Cantera PFR reactor model\*\* — industrial reactor-scale performance



The model correctly reproduces the industrial observation that \*\*Cu/ZnO is the optimal catalyst\*\* for methanol synthesis — validating the approach against real-world data.



\---



\## Key Results



| Metric | Value |

|--------|-------|

| \*\*Optimal catalyst\*\* | Cu/ZnO |

| \*\*TOF (500 K, 50 bar)\*\* | 3.49 × 10³ s⁻¹ |

| \*\*Methanol selectivity\*\* | 99.99% |

| \*\*Rate-determining step\*\* | HCOO formation (DRC = 1.00) |

| \*\*Volcano peak\*\* | ΔE\_CO₂ = −0.15 eV, ΔE\_H = −0.03 eV |

| \*\*Optimal reactor T\*\* | \~560 K |

| \*\*Apparent Ea (Cu/ZnO)\*\* | 917 meV |



\---



\## Project Structure

CREII\_CO2\_Methanol/

├── data/ # Reference data (empty — uses mechanism.py)

├── src/

│ ├── mechanism.py # 13-step elementary mechanism

│ ├── microkinetics.py # Analytical Langmuir-Hinshelwood model

│ ├── volcano.py # Sabatier volcano plot generator

│ ├── sensitivity.py # Temperature sensitivity analysis

│ ├── reactor.py # Cantera PFR reactor model

│ ├── make\_paper.py # Word paper generator

│ └── test\_cantera\_surface.py

├── results/

│ └── figures/

│ ├── volcano\_v2.png

│ ├── temperature\_sensitivity.png

│ └── reactor\_analysis.png

├── docs/report/

│ └── CREII\_CO2\_Methanol\_Paper.docx

└── README.md


\---



\## Methodology Summary



\### Microkinetic Model

\- \*\*Mechanism:\*\* 13 elementary steps following the formate pathway

\- \*\*Coverage model:\*\* Competitive Langmuir isotherm

&#x20; - θ\* = 1 / (1 + K\_CO₂·P\_CO₂ + √(K\_H₂·P\_H₂))

&#x20; - θ\_CO₂ = K\_CO₂·P\_CO₂ / D

&#x20; - θ\_H = √(K\_H₂·P\_H₂) / D

\- \*\*TOF:\*\* Calculated from the rate-determining step

&#x20; - TOF = k\_RDS · θ\_CO₂ · θ\_H

\- \*\*Sabatier penalty:\*\* BEP-type scaling of RDS barrier with binding energy

&#x20; - Ea\_RDS = Ea\_RDS° + γ · max(0, E\_opt − E\_ads)



\### Reactor Model

\- \*\*Type:\*\* Plug-flow reactor (PFR)

\- \*\*Conditions:\*\* 8 m length, 3 m diameter, GHSV = 10,000 h⁻¹

\- \*\*Feed:\*\* H₂:CO₂ = 3:1 with N₂ balance

\- \*\*Equilibrium:\*\* Literature-based conversion model

\- \*\*Tool:\*\* Cantera 3.2



\---



\## Software Requirements



\- Python 3.13

\- numpy, scipy, matplotlib

\- cantera >= 3.2

\- python-docx



Install all dependencies:



```bash

pip install numpy scipy matplotlib cantera python-docx
How to Run

1\. Microkinetic base case
python src/microkinetics.py

2. Generate volcano plot
python src/volcano.py

3. Temperature sensitivity analysis
python src/sensitivity.py

4. Reactor model
python src/reactor.py

5. Generate Word paper
python src/make\_paper.py

Key Figures

Figure 1 — Sabatier volcano plot for CO₂ hydrogenation



Figure 2 — Temperature sensitivity analysis (4 panels)



Figure 3 — PFR reactor analysis (4 panels)



All figures are saved in results/figures/.

References

Grabow, L. C., \& Mavrikakis, M. (2011). ACS Catalysis, 1(4), 365–384.



Studt, F., et al. (2014). ChemCatChem, 6(11), 3120–3125.



Ye, J., et al. (2013). ACS Catalysis, 3(6), 1296–1306.



Bligaard, T., et al. (2004). Journal of Catalysis, 224(1), 206–217.



Campbell, C. T. (2017). ACS Catalysis, 7(4), 2770–2779.



Vanden Bussche, K. M., \& Froment, G. F. (1996). Journal of Catalysis, 161(1), 1–10.



Behrens, M., et al. (2012). Science, 336(6083), 893–897.



Medford, A. J., et al. (2015). Journal of Catalysis, 328, 36–42.

Author

Harpreet Thappa

Chemical Engineering, 5th Semester

National Institute of Technology Srinagar

happythappa5@gmail.com

