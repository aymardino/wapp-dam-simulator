# Reference data: sources and assumptions

*"Reference 2024 (public sources)" set, scenario `reference_2024` in `engine/scenarios.py`. Version of 3 October 2026. Default scenario of the rooms and of the public site; the Deliverable 2 set (`reference`) remains the regression test set. Values marked (est.) are to be validated with SENELEC and the WAPP coordination centre. Version française : [fr/DONNEES_DE_REFERENCE.md](fr/DONNEES_DE_REFERENCE.md).*

**Principle.** Each zone offers its available plants by technology (quantity in available MW, price in USD/MWh close to the variable cost) and demands its peak (quantity in MW at the peak, modulated by the hourly load profile; decreasing buy prices by tranche: 220 to 230 for the base, 160 to 180 for the next tranche, 110 to 130 for the last, under the 500 cap). Values without a direct source are marked **(est.)**. Prices produced on these data are simulation results, not observed market prices: the WAPP day-ahead market has not started yet.

## 1. Capacities and peaks per country

| Zone | Installed capacity | Available (retained) | Peak (retained) | Main units of the set | Sources |
|------|-------------------:|---------------------:|----------------:|-----------------------|---------|
| NGA | 13,625 MW (NERC) | 5,750 MW | 5,800 MW | Kainji-Jebba-Shiroro-Zungeru hydro, Egbin, Azura-Edo, Okpai, NIPP and other gas plants | peak delivered 5,801.84 MW on 4 March 2025 (TCN); NERC capacity 13,625 MW: [Channels TV](https://www.channelstv.com/2025/03/06/tcn-announces-peak-in-power-generation-to-5801-84mw), [Leadership](https://leadership.ng/transmission-not-nigerias-power-constraint-tcn/) |
| GHA | 5,260 MW, 4,856 MW dependable (Nov. 2024) | 4,740 MW | 3,200 MW | Akosombo-Kpong-Bui, CCGT (TICO, Cenpower, Amandi), Sunon Asogli, AKSA and OCGT, Karpowership, solar | [Trade.gov, Ghana energy sector](https://www.trade.gov/country-commercial-guides/ghana-energy-sector), [Ghanaian Times](https://ghanaiantimes.com.gh/averting-power-crisis-govt-eyes-1200-megawatt-gas-fired-plant/amp/) |
| CIV | 2,907 MW (end 2023) | 2,660 MW | 2,200 MW (est.) | CI-Energies hydro, Azito, CIPREL, Atinkou, HFO, solar | capacity and 13,343 GWh generation: [economie-ivoirienne.ci](https://economie-ivoirienne.ci/activites-sectorielles/electricite.html); peak estimated from annual generation and a 0.7 load factor |
| SEN | 1,960 MW (2023) | 1,440 MW | 1,250 MW (est.) | OMVS (share), solar, Taïba N'Diaye wind, Sendou coal, gas CCGT, HFO | [Senelec annual report 2023](https://www.senelec.sn/media/rapports/pdf/rapport-annuel-senelec-2023-vf-ok1745314522.pdf); HFO 70 % of 2022 generation: [IEA Senegal 2023](https://iea.blob.core.windows.net/assets/b80ed5fc-7483-4b65-ae73-d39d5b2de40d/Senegal2023.pdf) |
| BFA | 684 MW (end 2025; 61 % thermal, 34 % solar, 5 % hydro), 220 to 300 MW imported | 635 MW | 600 MW (est.) | solar (Zagtouli, Nagréongo, Kodeni, Zina), Bagré-Kompienga, SONABEL HFO | [Sidwaya](https://www.sidwaya.info/delestage-au-burkina-faso-la-demande-depasse-loffre-directeur-general-sonabel-souleymane-ouedraogo/), [Burkina24](https://burkina24.com/?p=59904), [Horonya finance](https://www.horonyafinance.com/burkina-deficit-energetique-400-milliards-fcfa-necessaires-a-la-sonabel-pour-combler-un-gap-de-400-megawatts/) |
| MLI | ≈ 310 MW grid-connected + imports (old figure); 500 million litres of fuel in 2024 | 650 MW | 650 MW (est.) | OMVS-Sélingué (share), solar, EDM-SA HFO/diesel | [DLA Piper, power reforms](https://www.dlapiperafrica.com/en/africa-wide/insights/africa-connected/issue-03/power-reforms-in-west-africa.html), [Bamada](https://bamada.net/besoins-energetiques-du-mali-en-2024-500-millions-de-litres-de-carburant-pour-309-milliards-de-fcfa) |
| NER | Gorou Banda diesel 80 MW, solar 30 MW and more, contractual import 120 MW | 258 MW | 330 MW (est.) | solar, Anou Araren coal, NIGELEC diesel/HFO | [PV Magazine](https://www.pv-magazine.com/2023/07/19/niger-commissions-30-mw-solar-plant/), [World Bank, Niger PAD](https://documents1.worldbank.org/curated/en/630161534524243997/pdf/NIGER-ELECTRICITY-PAD-08142018.pdf), [AllAfrica, supply cut to 46 MW](https://allafrica.com/stories/202504180380.html) |
| BEN | Maria-Gléta 127 MW, Illoulofin 25 MW, contractual import 260 MW (200 MW exchanged); projected peak 700 MW in 2030 | 237 MW | 400 MW (est.) | solar, Nangbéto (share), Maria-Gléta, rental | [BIDC](https://www.bidc-ebid.org/en/?p=139903), [Illoulofin](https://en.wikipedia.org/wiki/Illoulofin_Solar_Power_Station), [AfDB, CEB-NEPA](https://www.afdb.org/fileadmin/uploads/afdb/Documents/Environmental-and-Social-Assessments/ADF-BD-IF-2002-128-EN-NIGERIA-BENIN-TOGO-EIA-CEB-NEPA-330KV-POWER-INTERCONNEXION-PROJECT.PDF) |
| TGO | 327 to 330 MW (2023-2024; gas 52 %, solar 22 %), Nangbéto 65 MW, ContourGlobal 100 MW, ≈ 75 MW bought from Nigeria | 270 MW | 310 MW (est.) | solar (Blitta, Dapaong), Nangbéto (share), Kékéli, ContourGlobal | [Climatescope Togo](https://global-climatescope.org/markets/togo), [The Global Economy](https://www.theglobaleconomy.com/Togo/electricity_production_capacity/), [Arise](https://www.arise.tv/togo-seeks-increased-electricity-supply-from-nigeria/) |
| GIN | 1,410 MW installed, 1,035 MW available (Souapiti 450, Kaleta 240) | 1,070 MW | 850 MW (est.) | Souapiti-Kaleta-Garafiri hydro, Tombo-Kipé HFO | [World Bank, Guinea](https://documents1.worldbank.org/curated/en/099050925174542646/pdf/P511453-12d6c125-5ec9-4fd2-874e-9a1685585cee.pdf), [EDG report 2023](https://edg.com.gn/wp-content/uploads/2025/02/RAPPORT-ACTIVITES-EDG-SA-Excercice-2023.pdf) |
| SLE | 494 MW (GEM, rentals included); observed peak 85 MW (2020), unconstrained demand 105 MW (2022) | 135 MW | 115 MW | Bumbuna, Karpowership, EDSA thermal | [World Bank, Sierra Leone PAD](https://documents1.worldbank.org/curated/en/099050123103517589/pdf/BOSIB02d6608d80d80a8c80311ab3b789a5.pdf), [GEM](https://www.gem.wiki/Power_Sector_Transition_in_the_West_African_Power_Pool) |
| LBR | 126 MW (88 hydro + 38 thermal), peak 85 MW | 115 MW | 90 MW | Mount Coffee, Bushrod | [AfDB blog](https://blogs.afdb.org/economic-growth/the-liberian-model-smart-hydropower-and-regional-trade-reshaping-west-african-energy), [Mount Coffee](https://en.wikipedia.org/wiki/Mount_Coffee_Hydropower_Project) |
| GMB | ≈ 78 MW available, peak 106 to 140 MW | 110 MW | 125 MW | Brikama-Kotu HFO, Jambur solar | [The Point](https://thepoint.gm/africa/gambia/headlines/nawec-announces-load-shedding-as-power-demand-hits-140mw), [Kerr Fatou](https://www.kerrfatou.com/gambia-faces-26-megawatt-power-shortfall-as-nawec-urges-conservation/) |
| GNB | ≈ 30 MW installed, peak 63 MW | 28 MW | 63 MW | Karpowership | [World Bank, Guinea-Bissau](https://documents1.worldbank.org/curated/en/629941622730511131/pdf/Concept-Project-Information-Document-PID-Guinea-Bissau-Solar-Energy-Scale-up-and-Access-Project-P174576.pdf) |

Operating capacities per country according to Global Energy Monitor (cross-check): [GEM, Power Sector Transition in the WAPP](https://www.gem.wiki/Power_Sector_Transition_in_the_West_African_Power_Pool). Regional peak and mix: [ESMAP, hydropower in WAPP](https://www.esmap.org/sites/default/files/2022/Hydropower%20Uganda/05%20PPT_ESMAP%20-%20HYDRO%202023%20-%20WAPP_Last%20Version.pdf).

## 2. Interconnections

| Model line | Asset | Retained capacity | Source or assumption |
|------------|-------|------------------:|----------------------|
| NGA→BEN | 330 kV Ikeja–Sakété | 200 MW | 260 MW contractual, 200 MW exchanged in practice because of the line constraint: [AfDB, CEB-NEPA project](https://www.afdb.org/fileadmin/uploads/afdb/Documents/Environmental-and-Social-Assessments/ADF-BD-IF-2002-128-EN-NIGERIA-BENIN-TOGO-EIA-CEB-NEPA-330KV-POWER-INTERCONNEXION-PROJECT.PDF); reinforcement under way: [WAPP](https://www.ecowapp.org/en/news/strengthening-330-kv-nigeria%E2%80%93benin-interconnection-wapp-project-recognized-internationally) |
| NGA→NER | 132 kV Birnin Kebbi–Niamey | 120 MW | contractual capacity 120 MW: [World Bank, Niger PAD](https://documents1.worldbank.org/curated/en/630161534524243997/pdf/NIGER-ELECTRICITY-PAD-08142018.pdf); the 330 kV North Core backbone (600 MW) is nearing completion: [VON](https://von.gov.ng/electricity-wapp-north-core-project-nears-completion/) |
| BEN→TGO | CEB 161 kV network and 330 kV Sakété–Lomé | 300 MW (est.) | asset described without a published capacity: [AfDB, Ghana-Togo-Benin](https://www.afdb.org/fileadmin/uploads/afdb/Documents/Environmental-and-Social-Assessments/ADF-BD-IF-2006-245-EN-MULTINATIONAL-GHANA-TOGO-BENIN-POWER-INTERCONNECTION-PROJECT-VRA-CEB-SUMMARY-REPORT.PDF) |
| TGO→GHA | 330 kV Volta–Lomé C and 161 kV | 300 MW (est.) | idem |
| GHA→CIV | 225 kV Prestea–Riviera (1983) | 200 MW (est.) | single-circuit 225 kV line; 330 kV reinforcement signed in 2025: [AU-PIDA](https://map.au-pida.org/projects/show/20050001) |
| GHA→BFA | 225 kV Bolgatanga–Ouagadougou | 100 MW | [EIB](https://www.eib.org/en/projects/pipelines/all/20100346), [Graphic](https://www.graphic.com.gh/news/general-news/ghana-to-increase-power-supply-to-burkina-faso.html) |
| CIV→BFA | 225 kV Ferkessédougou–Bobo-Dioulasso | 100 MW | [Oxford Business Group](https://oxfordbusinessgroup.com/reports/cote-divoire/2015-report/economy/doing-its-share-regional-exchanges-offer-an-efficient-way-to-extend-and-improve-access-to-power-supplies) |
| CIV→MLI | 225 kV Ferkessédougou–Sikasso–Ségou | 200 MW (est.) | line sized for 400 MW ([Bamada](https://bamada.net/interconnexion-electrique-mali-cote-divoire-les-installations-ont-ete-inaugurees-a-sikasso)); exchange capacity cautiously retained at half |
| CIV→LBR, LBR→SLE, SLE→GIN | CLSG 225 kV double circuit | 290 MW | total transfer capacity 290 MW: [GI Hub](https://cdn.gihub.org/umbraco/media/2519/gih-showcase-projects-2019-cslg-interconnector-project-art-web.pdf) |
| GIN→GNB, GNB→GMB, GMB→SEN | OMVG 225 kV loop | 300 MW (est.) per section | loop designed for 800 MW: [World Bank, OMVG](https://documents1.worldbank.org/curated/en/442701468194079362/pdf/895940PAD0P146010Box391424B00OUO090.pdf) |
| SEN→MLI | OMVS 225 kV network (Manantali 200 MW, Félou 60 MW) | 150 MW (est.) | [ESMAP, Manantali](https://www.esmap.org/sites/esmap.org/files/BN004-10_REISP-CD_Manantali-Generation.pdf); no published exchange capacity |

The interdependence constraint α = 0.7 on GHA→BFA and CIV→BFA is kept as is (Deliverable 2).

## 3. Costs by technology (sell order prices)

| Technology | Retained price (USD/MWh) | Rationale |
|------------|-------------------------:|-----------|
| Hydro | 12 to 36 | water value, near-zero variable cost; staggered to reflect reservoir management |
| Solar, wind | 4 to 8 | zero marginal cost, offered first (must-run) |
| Gas, Nigeria | 24 to 55 | gas at $2.42/MMBtu for the power sector in 2024 ([Premium Times](https://www.premiumtimesng.com/business/business-news/682642-nigerian-petroleum-agency-announces-new-gas-price-for-strategic-sector.html)): fuel ≈ $17/MWh in combined cycle, 25 in open cycle, plus operation |
| Gas, Ghana | 68 to 125 | weighted average gas cost $8.12/MMBtu in 2024 ([PURC](https://www.purc.com.gh/attachment/315187-20240410010442.pdf)); generation cost in the tariff $81/MWh in 2023 ([LinkedIn, N. D. Asante](https://www.linkedin.com/pulse/tariff-insights-ghana-power-costs-1-generation-nii-darko-asante)) |
| Gas, Côte d'Ivoire | 46 to 62 | domestic gas cheaper than imported; Ivorian tariff about half the Senegalese one ([Energy Capital & Power](https://energycapitalpower.com/gas-halve-senegal-electricity-prices-2023/)) |
| Heavy fuel oil | 125 to 210 | fuel $105 to $150/MWh for HFO delivered between $550 and $700/t ([USPE](https://uspeglobal.com/articles/hfo-power-plant-cost-breakdown/)), plus operation; diesel above |
| Coal | 65 to 90 | Sendou (Senegal), Anou Araren (Niger); assumption |

## 4. What remains to be validated

- 2023-2024 peak demands for SEN, CIV, BFA, MLI, NER, BEN, TGO, GIN: utility data (annual reports) or the WAPP coordination centre.
- Real exchange capacities of the lines marked (est.), in particular the Ghana–Togo–Benin corridor and the OMVG loop; the WAPP computes NTC daily.
- Variable costs per plant (power purchase agreements), if SENELEC and EPEX can share them in aggregate form.
- `reference_2024` is already the default scenario of the rooms; once validated, recalibrate the values and, if needed, the regression tests.
