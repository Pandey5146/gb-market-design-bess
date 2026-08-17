# GB Market Design, Network Constraints and Battery Flexibility

## A PyPSA-GB study of commercially scheduled storage and network-constrained redispatch

## Overview

This project investigates how electricity-market design and transmission constraints affect the system value of battery energy storage in Great Britain.

The central research question is:

> **Does commercially rational battery dispatch based on a non-locational wholesale price necessarily provide network-optimal flexibility?**

The project combines:

- empirical Elexon and NESO data,
- the open-source PyPSA-GB electricity-system model,
- a two-stage wholesale and balancing-market simulation,
- network-constrained redispatch analysis,
- controlled BESS counterfactuals,
- carrier-level cost decomposition,
- and individual-asset redispatch diagnostics.

The analysis finds that additional battery storage can improve renewable utilisation without necessarily reducing balancing expenditure.

In the principal January 2020 counterfactual, adding a **120 MW / 240 MWh BESS** at a renewable-constrained model node:

- reduced onshore-wind downward redispatch by approximately **2.54 GWh**,
- reduced net physical CCGT generation by approximately **3.36 GWh**,
- but increased modelled balancing / constraint cost by approximately **£0.47 million (+1.13%)**.

The additional cost was not primarily caused by the new battery taking expensive balancing actions.

Instead, the battery's wholesale operation changed the subsequent network-constrained solution, resulting in materially different two-sided redispatch across CCGTs and existing pumped-storage assets.

The study therefore highlights a potential difference between:

> **commercially rational flexibility**

and

> **system-optimal flexibility.**

---

# 1. Research Motivation

Increasing renewable generation in Great Britain creates a growing interaction between:

- generation location,
- transmission capacity,
- electricity-market design,
- wholesale prices,
- renewable curtailment,
- storage operation,
- and balancing actions.

A system optimisation model may identify battery charging or discharging that reduces transmission congestion, renewable curtailment or total system cost.

A commercial battery operator, however, does not directly optimise total electricity-system cost.

It responds to available revenue opportunities and market signals.

If those market signals do not fully represent the location and severity of network constraints, commercially attractive storage operation may differ from the operation preferred by the physical electricity system.

This motivates the central question of the project:

> **Can battery storage improve renewable utilisation while still producing a more expensive network-balancing outcome because its initial commercial dispatch signal does not fully represent transmission constraints?**

---

# 2. Research Questions

The project addresses four related research questions.

### RQ1 — Empirical constraint behaviour

How are wind-generation conditions associated with observed GB transmission-constraint expenditure?

### RQ2 — Historical model behaviour

Can the PyPSA-GB market workflow reproduce a meaningful scale of historical network-constrained redispatch and constraint expenditure?

### RQ3 — Battery flexibility

How does incremental BESS capacity at a renewable-constrained model node affect:

- wind downward redispatch,
- thermal redispatch,
- physical generation,
- balancing volumes,
- and balancing cost?

### RQ4 — Market design

If a battery is initially dispatched against an unconstrained system-wide wholesale signal, does that commercial dispatch necessarily reduce the cost of the subsequent network-constrained balancing problem?

---

# 3. Research Gap

The starting point for this project was the observation that renewable curtailment, network constraints and battery flexibility are frequently investigated from a system-optimisation perspective.

That leaves an important distinction between:

```text
What is optimal for the electricity system
                 ≠
What is commercially optimal for an individual asset

4. Relationship to Published PyPSA-GB Research

This project builds on the PyPSA-GB framework developed by Lyden et al. [1].

The original PyPSA-GB research provides the methodological foundation for high spatial and temporal resolution analysis of the Great Britain electricity system.

4.1 Network-constrained versus unconstrained dispatch

The published PyPSA-GB methodology supports two principal dispatch formulations:

a single-bus formulation where internal transmission constraints are ignored; and
a network-constrained linear optimal power flow formulation. [1]

This distinction provides a natural foundation for studying the difference between system-wide commercial dispatch and physically feasible network dispatch.

4.2 Scottish wind curtailment

The PyPSA-GB paper demonstrates the importance of transmission constraints through an illustrative Scottish wind-curtailment study.

For the 2035 Leading the Way scenario, the authors report:

29.4 TWh of wind curtailment when network constraints are included,
corresponding to 44.5% of potential wind generation.

When network constraints are removed:

wind curtailment falls to 14.9 TWh,
corresponding to 22.5% of potential generation. [1]

The study therefore demonstrates that ignoring transmission constraints can substantially understate renewable curtailment.

This project starts from that physical-network problem and asks a further question:

If storage is introduced at a constrained renewable location, does its commercially determined dispatch automatically produce the lowest-cost network outcome?

5. Gaps and Opportunities Identified from the Published Model

The present study is not intended to reproduce the original PyPSA-GB paper.

Instead, it uses several areas outside the main scope of the published analysis as motivation for further investigation.

Published PyPSA-GB focus	Gap / research opportunity	Response in this project
Cost-minimising dispatch	Commercial participant behaviour not explicitly modelled	Separate wholesale and balancing stages
Single-bus versus network-constrained optimisation	Sequential correction of commercial positions not central to original study	Wholesale positions followed by network-constrained redispatch
Storage represented as a system resource	Commercial versus system-optimal storage behaviour not explicitly tested	Incremental BESS follows wholesale stage before balancing
Wind curtailment under network constraints	Impact on balancing expenditure and redispatch composition	Carrier and asset-level cost decomposition
Physical power-system analysis	Market-design implications remain an extension area	Study interprets wholesale/network mismatch
Future market evolution	Locational pricing identified as a future application	Network-aware / locational BESS proposed as next counterfactual
5.1 Market mechanisms

The published PyPSA-GB methodology primarily represents generator economics using marginal operating costs.

The authors note that additional mechanisms including:

the Capacity Market,
Contracts for Difference,
and ancillary services

can influence real generator dispatch but are not included in that published model formulation. [1]

This provides an important motivation for analysing electricity-market behaviour in addition to physical dispatch.

5.2 Sequential wholesale and balancing decisions

The original paper demonstrates unconstrained and network-constrained optimisation.

However, the principal research question in this project requires a sequential process:

Wholesale schedule
       ↓
Commercial positions
       ↓
Transmission network restored
       ↓
Network infeasibility / congestion
       ↓
Balancing redispatch
       ↓
Physical dispatch

The version of PyPSA-GB used for this project contains a market workflow that enables this two-stage analysis.

5.3 Commercial versus system-optimal storage

Storage in a conventional optimisation model is generally dispatched according to the objective of the optimiser.

That answers:

What should storage do to minimise the specified system objective?

It does not necessarily answer:

What will a commercially motivated storage operator do when facing real market signals?

The present project uses the distinction between the wholesale and balancing stages to begin investigating this gap.

5.4 Locational signals

The PyPSA-GB paper identifies evolving electricity-market structures, including locational pricing, as an area where the model could support future research. [1]

This study provides an intermediate step towards that question by examining the consequences of a battery responding initially to a non-locational wholesale signal.

A direct locational-pricing counterfactual is proposed as future work.

6. Evolution of the Research Design

The final methodology was not selected at the beginning of the project.

The research question evolved as several modelling approaches were tested, challenged and rejected.

Documenting these changes is important because they informed the final research design.

6.1 Initial approach — physical congestion and renewable curtailment

The project initially began as a conventional network-constrained PyPSA-GB study.

A reduced historical GB network was used to examine:

renewable generation,
transmission loading,
constrained corridors,
wind curtailment,
and potential BESS locations.

The initial hypothesis was relatively simple:

Identify a renewable-constrained location, install a battery and measure the reduction in curtailment and system cost.

The early analysis found periods where renewable curtailment coincided with high utilisation of transmission corridors.

This established that network congestion was an important mechanism worth investigating.

However, this formulation treated the BESS principally as a system-optimised resource.

It did not address whether a commercial battery would choose the same charging and discharging pattern.

6.2 Why the original physical result was not accepted

An early January-only historical simulation appeared to show material renewable curtailment.

Instead of immediately reporting that result, the optimisation horizon was extended beyond the end of January.

The apparent end-of-month curtailment disappeared.

This indicated that the original result was influenced by optimisation-horizon boundary conditions rather than representing a robust physical finding.

The result was therefore rejected from the main analysis.

This produced an important methodological lesson:

Optimisation outputs should not automatically be interpreted as physical findings without checking sensitivity to horizon assumptions.

6.3 Full-year optimisation attempt

A full-year monolithic network optimisation was then attempted to reduce short-horizon boundary effects.

The resulting optimisation exceeded the available workstation memory.

Rather than reducing the problem until it solved and potentially changing the underlying research question, alternative computational approaches were investigated.

6.4 Rolling-horizon experiment

A rolling-horizon optimisation was implemented as a computational alternative.

The model solved successfully.

However, the rolling limited-foresight result produced materially different renewable-curtailment behaviour compared with the longer perfect-foresight model.

This demonstrated that:

Physical assumptions
+
Information horizon
+
Optimisation architecture

can all materially affect apparent flexibility requirements.

Because overlapping rolling windows also complicate direct comparison of optimisation objectives, the rolling result was retained only as a methodological sensitivity.

It was not used as the principal benchmark.

6.5 First BESS experiment rejected

An early battery experiment manually inserted a generic BESS into the physical optimisation.

The model solved and appeared to reduce renewable curtailment.

However, this result was deliberately rejected from the principal analysis.

The battery had not been introduced through the native wholesale and balancing-market workflow.

The experiment therefore answered:

What would a system optimiser do with additional storage?

rather than:

What happens when commercially scheduled storage subsequently interacts with a constrained transmission system?

Recognising this distinction changed the direction of the project.

6.6 Shift from a storage-location problem to a market-design problem

The original question was:

Can BESS reduce renewable curtailment?

The final question became:

Does commercially rational BESS dispatch also reduce network-balancing costs?

This reframing moved the project from a conventional storage optimisation exercise towards a market-design and participant-behaviour question.

6.7 Addition of empirical GB evidence

Another limitation of relying only on a historical model experiment is that a single simulated period does not demonstrate the broader relevance of the constraint problem.

An independent empirical dataset was therefore constructed using Elexon and NESO data for 2022–2025.

The empirical layer is not used to claim that the January 2020 counterfactual applies unchanged to later years.

Instead, the two layers have different purposes:

Elexon + NESO 2022–2025
        ↓
Empirical context:
When are GB constraint costs elevated?




PyPSA-GB January 2020
        ↓
Controlled counterfactual:
Why does BESS change system redispatch?

This separation avoids treating a single historical model year as representative of the entire contemporary GB electricity system.

6.8 Final research architecture

The final project architecture became:

Observed GB system behaviour
Elexon + NESO, 2022–2025
        ↓
Identify constraint regimes
        ↓
PyPSA-GB historical market model
January 2020
        ↓
Historical constraint-cost comparison
        ↓
Controlled BESS capacity sweep
0 / 50 / 70 / 100 / 120 MW
        ↓
Wholesale versus physical dispatch
        ↓
Carrier-level cost decomposition
        ↓
Individual-asset diagnostics
        ↓
Market-design interpretation

The final design therefore emerged from:

rejected hypotheses,
computational limitations,
horizon-sensitivity testing,
validation,
and a progressively more precise research question.
7. Data

The project combines empirical GB market data with PyPSA-GB model data.

7.1 Elexon

Elexon data are used to construct half-hourly and daily measures of:

electricity demand,
wind generation,
generation by technology,
and related power-system conditions. [2]
7.2 NESO

NESO constraint data are used to analyse historical:

thermal-constraint expenditure,
constraint volumes,
and total constraint costs. [3]
7.3 PyPSA-GB

PyPSA-GB provides:

generation assets,
transmission-network representation,
demand,
renewable availability,
storage,
interconnectors,
and power-system optimisation functionality. [1]

Renewable profiles use the PyPSA-GB weather-data workflow based on ERA5 / Atlite.

8. Empirical Constraint Analysis — 2022–2025

A daily empirical dataset was constructed from Elexon and NESO data.

Across 2022–2025:

mean GB electricity demand was approximately 629.8 GWh/day,
mean wind generation was approximately 177.5 GWh/day,
mean wind share of demand was approximately 28.4%,
mean thermal-constraint cost was approximately £4.11 million/day.

Higher-wind conditions were associated with materially higher constraint expenditure.

Using wind-generation regimes:

Wind regime	Mean thermal constraint cost
Normal — below 75th percentile	£2.96m/day
High — 75th–90th percentile	£6.68m/day
Extreme — 90th percentile and above	£8.83m/day

Relative to normal-wind days:

high-wind conditions were associated with approximately 126% higher mean thermal-constraint cost,
extreme-wind conditions were associated with approximately 198% higher mean thermal-constraint cost.

The correlation between wind generation and thermal-constraint cost was approximately 0.51.

The correlation between wind share of demand and thermal-constraint cost was approximately 0.53.

These results represent association rather than causality.

Constraint expenditure is also affected by:

transmission outages,
demand conditions,
geographic generation patterns,
interconnector flows,
system security requirements,
and other operating conditions.
8.1 Annual thermal-constraint expenditure

The processed NESO data produced the following annual thermal-constraint totals:

Year	Thermal constraint cost
2022	£1.709bn
2023	£0.981bn
2024	£1.482bn
2025	£1.831bn

The non-monotonic relationship reinforces that increasing renewable penetration alone does not explain constraint expenditure.

Network conditions and wider system operation remain important.

9. PyPSA-GB Market Methodology

The principal model experiment uses January 2020 at half-hourly resolution.

The model is separated into two stages.

9.1 Stage 1 — Wholesale market

Transmission constraints are relaxed during the wholesale stage.

Generators and eligible storage assets establish market positions using the wholesale optimisation.

This represents a system-wide market signal that does not initially internalise the full internal transmission network.

9.2 Stage 2 — Balancing mechanism

The physical transmission network is then restored.

Wholesale positions provide the starting point.

Generators and storage may subsequently be moved upward or downward to obtain a network-feasible physical dispatch.

Redispatch is defined as:

BM increase
=
max(physical dispatch - wholesale position, 0)

and:

BM decrease
=
max(wholesale position - physical dispatch, 0)

Balancing cost is calculated from the resulting upward and downward actions using the price representation contained in the market workflow.

This structure allows direct comparison between:

Commercial market position
           ↓
Network-feasible physical position
10. January 2020 Baseline Validation

Before conducting the BESS counterfactuals, the January 2020 market simulation was compared with observed NESO thermal-constraint expenditure.

Modelled January balancing / constraint cost:

£41.64 million

Observed NESO thermal-constraint cost:

approximately £70.5 million

The model therefore reproduces approximately:

59%

of the observed thermal-constraint-cost magnitude.

These quantities are not perfectly like-for-like.

The original PyPSA-GB authors similarly caution that historical comparisons provide confidence in model behaviour rather than constituting complete validation, because results remain sensitive to modelling inputs and assumptions. [1]

The January comparison is therefore used to demonstrate that the model reproduces a material scale of network-constrained redispatch.

It is not presented as an exact reconstruction of historical GB balancing outcomes.

11. Baseline Constraint Behaviour

The January baseline contains significant network congestion and redispatch.

Major modelled constraint-cost contributions include Scottish transmission boundaries and other highly utilised corridors.

The model exhibits the expected broad pattern of:

Renewable-rich northern generation
             ↓
Transmission constraints
             ↓
Generation constrained down
             ↓
Replacement generation required elsewhere

This provided the basis for selecting a renewable-constrained location for the incremental BESS experiment.

12. BESS Location Selection

The incremental research battery was placed at:

BEAT4-

The node was selected from the baseline redispatch diagnostics because it was associated with material downward renewable redispatch.

The location is therefore evidence-based within the model rather than arbitrarily selected.

However, BEAT4- should be interpreted as a model node.

The study does not claim that it corresponds to an exact real-world BESS connection point without additional network validation.

13. BESS Counterfactual Design

Four incremental 2-hour BESS cases were tested.

Added power	Added energy
50 MW	100 MWh
70 MW	140 MWh
100 MW	200 MWh
120 MW	240 MWh

The January 2020 baseline was otherwise retained.

This produces an internally controlled comparison between:

No additional research BESS

and:

Incremental research BESS
14. BESS Capacity-Sweep Results
BESS	BM / constraint cost	Change vs baseline	Wind-down reduction
0 MW	£41.645m	—	—
50 MW	£42.204m	+£559k (+1.34%)	1.735 GWh
70 MW	£42.148m	+£503k (+1.21%)	2.238 GWh
100 MW	£42.132m	+£487k (+1.17%)	2.155 GWh
120 MW	£42.115m	+£470k (+1.13%)	2.540 GWh

All tested BESS capacities reduce wind downward redispatch.

However, none of the additional-BESS cases reduce modelled balancing cost below the no-additional-BESS baseline.

The 120 MW case produces:

the greatest wind-down reduction among the tested capacities,
and the lowest balancing-cost increase among the additional-BESS cases.

This does not imply that 120 MW is an optimal BESS size.

Only the listed capacities were evaluated.

Figure — BESS constraint-cost response

Figure — reduction in wind downward redispatch

15. BESS Wholesale Operation

The additional batteries are active in the wholesale stage.

For the 120 MW / 240 MWh case:

wholesale charging: approximately 3.688 GWh,
wholesale discharging: approximately 3.388 GWh,
equivalent January discharge cycles: approximately 14.1.

Equivalent utilisation is approximately constant across the BESS sweep because power and energy capacity are scaled proportionally while retaining a two-hour duration.

This indicates that the new BESS is responding consistently to the wholesale market signal.

16. Direct BESS Balancing Activity

An important diagnostic is that the new research BESS itself undergoes effectively zero direct balancing movement.

For the 120 MW scenario, the incremental battery's direct BM cost contribution is negligible relative to the approximately £470k total system-cost change.

The battery is eligible to move during the balancing optimisation.

Therefore, its near-zero BM movement is an optimisation outcome rather than a modelling restriction excluding it from the balancing stage.

This means:

The additional system cost is primarily an indirect system response to the battery's wholesale position, rather than a direct cost of balancing the new battery itself.

17. Renewable Utilisation

The 120 MW BESS case reduces onshore-wind downward redispatch by approximately:

2.54 GWh

Wholesale wind generation is essentially unchanged.

The increase in physical wind generation therefore arises from:

Less wind BM decrease
        ↓
More wind reaches physical dispatch

This represents a clear renewable-utilisation benefit within the model.

18. CCGT Generation versus CCGT Redispatch

The CCGT result initially appeared counter-intuitive.

Additional CCGT upward redispatch increases substantially.

However, examining only upward actions gives an incomplete picture.

For the 120 MW scenario:

change in wholesale CCGT generation: approximately +0.065 GWh,
change in physical CCGT generation: approximately −3.36 GWh,
additional CCGT upward redispatch: approximately +10.33 GWh,
additional CCGT downward redispatch: approximately +13.75 GWh.

Therefore:

The BESS does not increase net physical CCGT generation.

Physical CCGT generation actually falls.

Instead, the system performs materially more two-sided CCGT redispatch.

Some CCGTs move upward while others move downward.

This increases gross balancing activity even though net gas generation decreases.

Figure — CCGT wholesale versus physical response

19. Redispatch Cost Decomposition

For the 120 MW / 240 MWh counterfactual, the approximately £470k increase in balancing cost is primarily explained by changes in CCGT and pumped-storage redispatch.

Carrier	Net cost change
CCGT	+£296k
Pumped Storage Hydroelectricity	+£253k
Onshore wind	−£67k
Oil	−£19k
Coal	+£10k
Other technologies	relatively small

The largest positive contributions are therefore:

CCGT redispatch
+
Pumped-storage redispatch

while reduced wind constraint-down provides a cost offset.

The result demonstrates that renewable-curtailment reduction and total balancing-cost reduction are not equivalent metrics.

20. Asset-Level Redispatch

Carrier-level averages hide large changes between individual generating units.

The 120 MW BESS counterfactual materially redistributes balancing actions across the fleet.

Selected changes include:

Asset	Δ BM up	Δ BM down	Δ net cost
West Burton CCGT	−12.36 GWh	+0.12 GWh	−£646k
Peterhead	~0	+9.03 GWh	−£190k
Seabank	+5.84 GWh	~0	+£345k
Damhead Creek	+3.50 GWh	~0	+£211k
Rocksavage	+3.31 GWh	~0	+£188k
Corby	~0	+3.16 GWh	−£158k
Medway	+2.14 GWh	~0	+£112k
Cruachan_2	+1.51 GWh	+0.60 GWh	+£176k
Coryton	+2.01 GWh	~0	+£129k
Foyers_3	+0.73 GWh	+0.64 GWh	+£86k

This shows that the system response is spatially and technologically heterogeneous.

Figure — asset-level redistribution

21. Main Finding

The principal result of this study is:

Improved renewable utilisation does not necessarily imply lower balancing expenditure.

Within the January 2020 PyPSA-GB two-stage counterfactual:

Additional BESS
        ↓
Wholesale-market operation
        ↓
Different commercial system position
        ↓
Network-constrained balancing stage
        ↓
Less wind constrained down
        ↓
More renewable electricity physically delivered


BUT


Different CCGTs move up and down
        +
Existing pumped storage changes operation
        ↓
Greater gross redispatch
        ↓
Higher total BM / constraint cost

The result therefore identifies a potential distinction between:

Commercially rational flexibility


and


System-optimal flexibility
22. Market-Design Interpretation

The result suggests that the value of storage cannot be evaluated from storage capacity and location alone.

The market signal controlling the asset also matters.

A battery may be located in a renewable-constrained region while primarily responding to a system-wide wholesale price.

Its resulting commercial position may therefore differ from the dispatch that would minimise subsequent transmission-balancing requirements.

This motivates a broader market-design question:

How should electricity-market signals reward flexible assets for the network value they provide?

23. The Market-Design Gap

The next logical counterfactual is:

Case A — commercial wholesale dispatch
Uniform wholesale price
        ↓
Battery schedule
        ↓
Network balancing

versus:

Case B — network-aware dispatch
Network / locational signal
        ↓
Battery schedule
        ↓
Network balancing

The difference in:

balancing cost,
renewable curtailment,
BESS revenue,
thermal redispatch,
and system cost

could quantify a:

market-design gap between privately optimal and system-optimal flexibility.

This is the principal future-research direction arising from the present results.

24. Important Historical-Storage Limitation

The 2024 PyPSA-GB paper states that historical electrical storage for 2010–2020 consists of large-scale pumped hydro, while batteries are represented among future storage technologies. [1]

However, the contemporary PyPSA-GB model version used in this project contains battery StorageUnits within the supplied 2020 baseline.

The January 2020 model used here contains approximately:

2.07 GW of baseline battery power,
approximately 4.14 GWh of battery energy capacity.

This creates a model-version / historical-vintage issue.

The present project therefore does not assume that the supplied battery fleet accurately reconstructs the actual January 2020 GB battery fleet.

Instead:

The supplied model baseline is retained unchanged and identical incremental BESS additions are compared against it.

The BESS sweep should therefore be interpreted as an internally controlled counterfactual experiment, not a reconstruction of historical battery deployment.

25. Limitations
25.1 Temporal scope

The detailed BESS counterfactual is restricted to January 2020.

The result should not be assumed to apply unchanged across all seasons or years.

25.2 Empirical versus model periods

The empirical analysis covers 2022–2025, whereas the detailed counterfactual uses a 2020 model.

The empirical dataset provides contemporary context.

It is not used as direct validation of the 2020 counterfactual.

25.3 Historical market reconstruction

The optimisation does not reproduce every:

generator strategy,
outage,
contract,
market mechanism,
ancillary-service commitment,
or real participant decision.
25.4 Balancing-cost comparison

Modelled BM / redispatch cost and NESO thermal-constraint expenditure are related but not perfectly equivalent quantities.

The approximately 59% comparison is therefore a scale check rather than a strict statistical validation metric.

25.5 Participant behaviour

Commercial behaviour is represented through optimisation.

The current model does not contain heterogeneous strategic agents individually maximising private profits with different expectations, risk tolerances or bidding strategies.

25.6 Network representation

Model nodes and corridors should not automatically be interpreted as exact physical substations or transmission circuits without further validation.

25.7 Causality

The empirical relationship between wind conditions and constraint costs is associative.

The project does not claim that wind generation alone causes higher constraint expenditure.

26. What This Study Does Not Claim

The study does not claim that:

batteries increase gas generation,
batteries are harmful to the GB electricity system,
120 MW is an optimal BESS size,
all BESS projects increase balancing costs,
BEAT4- is an exact recommended commercial connection point,
January 2020 represents every GB operating condition,
or the model exactly reproduces the real Balancing Mechanism.

The result is deliberately narrower:

In this controlled January 2020 two-stage model experiment, additional storage improved wind utilisation while its wholesale operation indirectly produced a more expensive network-constrained redispatch pattern.

27. Rejected and Failed Approaches

Several approaches were intentionally excluded from the final headline results.

They remain important parts of the research process.

Short-horizon curtailment result

Rejected after extending the optimisation horizon showed that the apparent curtailment was horizon-sensitive.

Full-year monolithic optimisation

Attempted but exceeded available workstation memory.

Rolling-horizon optimisation

Retained only as a limited-foresight sensitivity because results differed materially from longer perfect-foresight optimisation.

Generic manually inserted BESS

Rejected because it answered a system-optimisation question rather than the final wholesale-versus-balancing market-design question.

These failures influenced the final methodology and are documented to improve transparency and reproducibility.

28. Reproducibility

The project was developed using:

Python
PyPSA
PyPSA-GB
pandas
NumPy
matplotlib
Snakemake
HiGHS

Example environment:

conda activate pypsa-gb-stable

Important analysis scripts include:

project1_gb_market/scripts/
│
├── build_empirical_daily.py
├── prepare_bess_sweep_networks.py
├── analyse_bess_sweep.py
├── diagnose_wholesale_physical_gap.py
└── plot_asset_redispatch.py

Example execution:

python project1_gb_market/scripts/analyse_bess_sweep.py
python project1_gb_market/scripts/diagnose_wholesale_physical_gap.py
python project1_gb_market/scripts/plot_asset_redispatch.py
29. Repository Structure
project1_gb_market/


├── scripts/
│   ├── build_empirical_daily.py
│   ├── prepare_bess_sweep_networks.py
│   ├── analyse_bess_sweep.py
│   ├── diagnose_wholesale_physical_gap.py
│   └── plot_asset_redispatch.py
│
├── notebooks/
│
├── data/
│   ├── raw/
│   │   ├── elexon/
│   │   └── neso/
│   └── processed/
│
├── results/
│   ├── bess_sweep_summary.csv
│   ├── carrier_dispatch_by_scenario.csv
│   ├── carrier_dispatch_diagnostic.csv
│   └── asset_redispatch_120mw.csv
│
├── figures/
│   ├── bess_sweep_constraint_cost.png
│   ├── bess_sweep_wind_reduction.png
│   ├── bess_sweep_redispatch.png
│   ├── bess_sweep_wholesale_operation.png
│   ├── ccgt_wholesale_physical_gap.png
│   ├── bess120_carrier_redispatch_change.png
│   └── asset_level_redispatch_120mw.png
│
└── README.md
30. Future Research

The highest-priority extension is a direct comparison between:

uniform-price commercial BESS dispatch

and

network-aware / locational BESS dispatch.

Other extensions include:

seasonal robustness,
multiple weather years,
alternative BESS locations,
battery-duration sensitivity,
endogenous storage investment,
locational electricity pricing,
zonal versus national pricing,
strategic bidding,
congestion markets,
demand-side flexibility,
electrolysers,
ancillary-service stacking,
and interactions between private BESS revenue and total system value.
30.1 Agent-based extension

A particularly important future development would introduce heterogeneous market participants.

For example:

BESS operator
→ maximises private revenue


Generator
→ maximises trading / balancing profit


Electrolyser
→ responds to electricity and hydrogen value


System operator
→ maintains network feasibility

The resulting dispatch could then be benchmarked against the system-optimised solution.

This would allow explicit quantification of the difference between:

private commercial incentives
          ↓
participant behaviour


versus


system-level optimum

and would extend the present market-design question into an agent-based market simulation.

31. Contribution of This Project

The contribution is not the creation of PyPSA-GB itself.

The contribution of this project is the research workflow built around it:

connecting multi-year empirical GB constraint behaviour to a controlled power-system model;
separating wholesale scheduling from network-constrained balancing;
introducing controlled incremental BESS counterfactuals;
diagnosing wholesale versus physical dispatch;
decomposing an unexpected balancing-cost result by technology;
tracing the mechanism to individual CCGT and pumped-storage assets;
and interpreting the result through the distinction between commercial and system-optimal flexibility.

The unexpected result — improved renewable utilisation but higher balancing expenditure — became the central research finding rather than being discarded because it contradicted the original hypothesis.

32. Attribution

This project builds on the open-source PyPSA-GB model developed by Andrew Lyden and collaborators at the University of Edinburgh.

PyPSA-GB is released under the MIT licence.

Any upstream PyPSA-GB code retained or modified in this project should preserve the corresponding licence and copyright notices.

This repository should not be interpreted as an official PyPSA-GB release.

33. References
[1] PyPSA-GB

Lyden, A., Sun, W., Struthers, I., Franken, L., Hudson, S., Wang, Y. and Friedrich, D. (2024).

PyPSA-GB: An open-source model of Great Britain's power system for simulating future energy scenarios.

Energy Strategy Reviews, 53, 101375.

DOI: 10.1016/j.esr.2024.101375

[2] Elexon

Elexon BSC Open Data.

Historical GB electricity-system demand and generation datasets used in the empirical analysis.

Exact dataset/API endpoints used in the reproducible workflow will be documented alongside the data-download scripts.

[3] NESO

National Energy System Operator Open Data.

Historical constraint-cost and constraint-volume datasets used in the empirical analysis.

Exact dataset/API endpoints used in the reproducible workflow will be documented alongside the data-download scripts.

34. Project Status

Research portfolio prototype — August 2026

Completed:

multi-year empirical Elexon/NESO constraint analysis,
PyPSA-GB historical market modelling,
January 2020 validation,
controlled BESS capacity sweep,
wholesale-versus-physical dispatch diagnostics,
carrier-level cost decomposition,
asset-level redispatch analysis,
and market-design interpretation.

Planned:

repository cleanup,
reproducibility documentation,
public GitHub release,
and network-aware / locational flexibility counterfactual.