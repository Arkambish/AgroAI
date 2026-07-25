"""Body content for the FYP Final Report.

Each chapter is a list of (kind, payload) tuples consumed by
generate_final_docx._emit(). Keeping the prose here keeps the layout engine in
generate_final_docx.py readable.

All numeric results quoted here are read from outputs/results_real/ (the real
collected dataset, 28 seasonal records). Synthetic-pipeline numbers appear only
in section 7.12, where they are explicitly labelled as architecture validation.
"""

from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.shared import Inches, Pt

REAL = "outputs/plots_real"
SYNTH = "outputs/plots"
FIGDIR = f"{SYNTH}/figures"


# ============================================================================
# Chapter 1 — Introduction
# ============================================================================

CHAPTER_1 = [
    ("chapter", ("1", "Forecasting Big Onion Yield in Sri Lanka")),

    ("h2", "1.1 Introduction"),
    ("p",
     "This chapter introduces the problem that the project addresses, explains "
     "why it matters to Sri Lanka, states the aim and objectives that the work "
     "was set against, outlines the proposed solution in terms of its users, "
     "inputs, outputs, process and technology, and finally describes how the "
     "remainder of the report is organised. The reader who finishes this "
     "chapter should understand what is being predicted, for whom, and why the "
     "prediction cannot simply be looked up in an existing government report."),
    ("p",
     "Big onion (Allium cepa L.) is one of the most economically significant "
     "non-cash field crops grown in Sri Lanka. It is a staple ingredient in "
     "practically every household kitchen, it is grown commercially in the dry "
     "and intermediate zones, and it is simultaneously one of the country's "
     "largest agricultural import lines. National annual consumption is on the "
     "order of 220,000 metric tons, and domestic cultivation covers only part "
     "of that requirement; the remainder is imported, largely from India and "
     "Pakistan, at a direct cost in foreign exchange [4], [13]. Because the "
     "import decision has to be taken months in advance of the domestic "
     "harvest reaching the market, the accuracy of the pre-harvest yield "
     "estimate translates directly into either wasted foreign exchange or a "
     "price shock at the consumer end."),

    ("h2", "1.2 Background and Motivation"),
    ("h3", "1.2.1 The information gap"),
    ("p",
     "Sri Lanka's Department of Census and Statistics operates a mature and "
     "well-documented crop-cutting survey methodology for paddy. Enumerators "
     "physically harvest measured plots at randomly selected locations, weigh "
     "the produce, and the resulting sample statistics are aggregated into "
     "district and national yield estimates with quantified sampling error. "
     "This machinery does not exist for big onion [4]. Big onion yield figures "
     "are instead compiled from the subjective assessments of agricultural "
     "instructors and divisional officers, who estimate the extent cultivated "
     "and the likely production from field visits and grower interviews. Two "
     "consequences follow. First, the estimates carry an unquantified error. "
     "Second, and more damaging for planning, they arrive after the fact: the "
     "figure for a season is finalised once that season's crop is already "
     "harvested and sold."),
    ("p",
     "A pre-harvest forecast is therefore not a marginal improvement over an "
     "existing service; it is a capability that does not currently exist for "
     "this crop. A forecast issued four to eight weeks before harvest, at the "
     "district level, would allow the Department of Agriculture and the "
     "Ministry to size imports against an evidence-based expectation of the "
     "domestic crop rather than against last year's outcome. It would allow "
     "district agricultural officers to identify districts trending towards a "
     "shortfall while there is still time to intervene with irrigation advice "
     "or pest management. It would give farmer organisations a defensible basis "
     "for negotiating forward prices with collectors."),

    ("h3", "1.2.2 Why the problem is technically hard"),
    ("p",
     "Crop yield is the outcome of a long chain of interacting biophysical "
     "processes: soil water availability, thermal accumulation, radiation "
     "interception by the canopy, nutrient supply, pest and disease pressure, "
     "and management decisions taken by thousands of individual growers. Most "
     "of these are unobserved. What is observable at scale is a set of proxies "
     "— daily weather variables, satellite-derived vegetation indices that "
     "track canopy vigour, land surface temperature, and static soil "
     "properties. Learning the mapping from proxies to yield is exactly the "
     "kind of problem that machine learning has been applied to with success "
     "for the major cereals [1], [2], [3]."),
    ("p",
     "The difficulty in the Sri Lankan big onion setting is that the published "
     "successes rest on datasets that are orders of magnitude larger than what "
     "is available here. County-level maize yield studies in the United States "
     "draw on tens of thousands of county-year records; the Sri Lankan big "
     "onion record, restricted to districts where the crop is commercially "
     "significant and to years in which consistent satellite coverage exists, "
     "yields a few dozen usable observations. This project therefore does not "
     "simply apply established methods; it has to establish which methods "
     "survive at this sample size, and it has to build an evaluation protocol "
     "honest enough that the answer can be believed."),

    ("h3", "1.2.3 The bimodal season structure"),
    ("p",
     "Sri Lankan agriculture runs on two monsoon-driven cultivation seasons. "
     "Yala runs broadly from April to August under the south-west monsoon, and "
     "Maha runs from October to March under the north-east monsoon. The two "
     "seasons differ in rainfall regime, temperature, day length and typical "
     "cultivated extent, and consequently in achievable yield. Big onion in the "
     "dry zone is predominantly a Yala crop under irrigation. Any model built "
     "for this setting must be able to represent season as a first-class "
     "conditioning variable rather than as one more numerical feature, because "
     "the yield response surface genuinely differs between the two seasons. "
     "Published architectures for single-season cash crops do not address this "
     "[8]."),

    ("h2", "1.3 Aim and Objectives"),
    ("p",
     "The aim of this project is to design, implement and rigorously evaluate "
     "an artificial-intelligence-powered decision-support system that predicts "
     "big onion harvest yield, at district and season granularity, before "
     "harvest, from openly available weather, satellite, soil and historical "
     "yield data, and that reports its predictions with honest and calibrated "
     "statements of uncertainty."),
    ("p", "The aim is decomposed into the following objectives."),
    ("bullet",
     "Objective 1 — Data foundation. Identify, acquire and integrate the "
     "relevant open data streams for the four target districts, and construct "
     "a clean analysis dataset at the district-season-year grain with a "
     "documented and reproducible transformation from raw source files."),
    ("bullet",
     "Objective 2 — Feature engineering. Derive an agronomically meaningful "
     "predictor set spanning weather aggregates, vegetation dynamics, thermal "
     "and water stress indices, historical yield memory, static soil properties "
     "and cross-modal interaction terms."),
    ("bullet",
     "Objective 3 — Comparative modelling. Implement and train a family of "
     "predictors covering classical machine learning, deep sequence learning, "
     "interpretable symbolic regression and physics-informed hybrid modelling, "
     "under one identical protocol so that their comparison is meaningful."),
    ("bullet",
     "Objective 4 — Honest evaluation. Evaluate every model using "
     "Leave-One-Year-Out cross-validation, report paired statistical "
     "significance tests rather than raw leaderboard positions, and attach "
     "distribution-free conformal prediction intervals to the point forecasts."),
    ("bullet",
     "Objective 5 — Attribution and ablation. Quantify the contribution of each "
     "input data source through a controlled ablation study, and explain "
     "individual predictions using SHAP attributions so that the system is not "
     "a black box to an agricultural officer."),
    ("bullet",
     "Objective 6 — Delivery. Expose the trained system through a documented "
     "REST interface and a decision-support dashboard that presents "
     "predictions, comparisons, explanations and recommendations to "
     "non-technical users."),

    ("h2", "1.4 The Proposed Solution"),
    ("p",
     "The solution is a three-tier system. The bottom tier is a reproducible "
     "Python data and modelling pipeline; the middle tier is a Flask REST "
     "service that exposes the pipeline's artefacts; the top tier is a Next.js "
     "web dashboard consumed by the end users. The following paragraphs state "
     "the solution in the terms required by the report guideline: users, "
     "inputs, outputs, process, technology, features and system requirements."),
    ("p",
     "Users. Four groups are served. Statistical officers at the Department of "
     "Census and Statistics use the forecast as a prior against which to sanity-"
     "check field returns. Policy analysts at the Department of Agriculture and "
     "the Ministry use district-level aggregates to size import requirements. "
     "District agricultural officers use per-district forecasts and their "
     "drivers to target extension effort. Researchers and students use the "
     "model comparison, the ablation results and the published equation."),
    ("p",
     "Inputs. For a given district, season and year the system consumes daily "
     "weather observations over the growing window, satellite vegetation and "
     "land-surface-temperature composites over the same window, static soil "
     "properties for the district, and the district's own yield history for "
     "preceding seasons and years."),
    ("p",
     "Outputs. The system returns a point forecast of average yield in metric "
     "tons per hectare, a calibrated prediction interval at a nominal ninety "
     "per cent coverage level, a ranked SHAP attribution explaining which "
     "predictors drove the forecast away from the baseline, the closed-form "
     "symbolic equation as an interpretable cross-check, and a comparison of "
     "how each candidate model scored under the shared evaluation protocol."),
    ("p",
     "Process. Raw source files are loaded and reconciled to a common "
     "district-season-year key; the record is cleaned and validated; thirty-two "
     "predictors are engineered; nine model families are trained under "
     "Leave-One-Year-Out cross-validation with inner-loop hyperparameter "
     "search; a constrained convex stacking layer is fitted on the "
     "out-of-fold predictions; conformal residual quantiles are computed; SHAP "
     "attributions are extracted; and all artefacts are written to disk for the "
     "serving layer to read."),
    ("p",
     "Technology. The modelling tier is Python with scikit-learn [21], XGBoost "
     "[18], TensorFlow/Keras [22], gplearn for symbolic regression and SHAP "
     "[19] for attribution. The serving tier is Flask. The presentation tier is "
     "Next.js with TypeScript and Tailwind CSS. Satellite data is obtained "
     "through Google Earth Engine [23]."),
    ("p",
     "System requirements. The pipeline runs to completion on a single "
     "commodity laptop with eight gigabytes of memory and no GPU, in "
     "approximately six minutes for the full run. This is a deliberate design "
     "constraint: a system intended for a government department in a "
     "resource-constrained setting must not presuppose cluster infrastructure. "
     "Every random seed is fixed so that a re-run reproduces the reported "
     "numbers exactly."),

    ("h2", "1.5 Structure of the Report"),
    ("p",
     "The remainder of this report is organised as follows. Chapter 2 reviews "
     "the work of others in crop yield prediction, covering classical machine "
     "learning, deep and hybrid architectures, mechanistic process-based "
     "modelling, the Sri Lankan literature and the small body of onion-specific "
     "work, and closes by identifying the research gaps that this project "
     "targets. Chapter 3 describes the technologies adapted to solve the "
     "problem and argues, for each, why it is appropriate to this particular "
     "problem rather than merely available. Chapter 4 presents the approach "
     "taken, describing the system in terms of its users, inputs, outputs, "
     "process and top-level architecture. Chapter 5 gives the analysis and "
     "design of the solution, module by module. Chapter 6 documents the "
     "implementation, mapping each design module onto the source files, "
     "algorithms and configuration that realise it. Chapter 7 reports the "
     "evaluation: the dataset, the protocol, the model comparison, the "
     "mechanistic-backbone and stacking studies, the ablation, per-district "
     "behaviour, calibrated uncertainty and feature attribution. Chapter 8 "
     "discusses what the results mean, positions the work against the "
     "literature, states the threats to validity, sets out further work and "
     "concludes. The references follow, and then four appendices: individual "
     "contributions, configuration and code excerpts, extended result tables, "
     "and dashboard screenshots."),

    ("h2", "1.6 Summary"),
    ("p",
     "This chapter established that Sri Lanka has no pre-harvest yield "
     "forecasting capability for big onion, that the absence has concrete "
     "consequences for import planning and farmer welfare, and that the "
     "technical challenge lies not in the modelling techniques themselves but "
     "in making them work honestly at a sample size far below what the "
     "published literature assumes. The aim and six objectives were stated, and "
     "the proposed three-tier solution was described in terms of its users, "
     "inputs, outputs, process and technology. The next chapter surveys how "
     "others have approached crop yield prediction and identifies precisely "
     "where the gaps lie."),
]


# ============================================================================
# Chapter 2 — Review of others' work
# ============================================================================

CHAPTER_2 = [
    ("chapter", ("2", "Crop Yield Prediction: A Review of Others' Work")),

    ("h2", "2.1 Introduction"),
    ("p",
     "Chapter 1 established the problem: no pre-harvest yield forecast exists "
     "for big onion in Sri Lanka, and the data available to build one is far "
     "scarcer than what published crop-yield studies assume. This chapter "
     "reviews how others have attacked the yield prediction problem. It moves "
     "from classical machine learning through deep and hybrid architectures to "
     "mechanistic process-based models, then narrows to the Sri Lankan "
     "literature and to onion specifically, compares the approaches in a single "
     "table, and closes by naming the five gaps this project addresses."),

    ("h2", "2.2 Classical Machine Learning for Yield Prediction"),
    ("p",
     "The dominant paradigm in applied crop-yield prediction is supervised "
     "regression on tabular features derived from weather, remote sensing and "
     "management records. Jabed et al. [1] provide the most current "
     "comprehensive review of the field, surveying both machine learning and "
     "deep learning approaches across crops and geographies. Their synthesis "
     "reports that tree-based ensembles — Random Forest [17] and gradient "
     "boosting, particularly XGBoost [18] — are the most frequently deployed "
     "and, on tabular agricultural data, frequently the most accurate methods, "
     "with deep architectures gaining ground only where the input carries "
     "genuine spatial or temporal structure and the sample size is large."),
    ("p",
     "Chikwendu et al. [3] make the comparison explicit, benchmarking several "
     "regressors on the same crop-yield task and finding tree ensembles ahead "
     "of both linear models and shallow neural networks. The mechanism is well "
     "understood: bagged and boosted trees handle heterogeneous feature scales "
     "without preprocessing, capture threshold effects natural to biological "
     "response curves, are comparatively robust to irrelevant predictors, and "
     "do not need the sample sizes that gradient-based function approximators "
     "require to escape overfitting."),
    ("p",
     "Support Vector Regression appears throughout the same literature as a "
     "strong small-sample baseline. Its appeal in this domain is that its "
     "capacity is controlled by the regularisation constant and the epsilon-"
     "insensitive tube rather than by parameter count, which makes it "
     "structurally suited to short records. Wang et al. [7] provide an "
     "instructive comparison in which machine learning models built on "
     "meteorological features are benchmarked directly against a process-based "
     "crop model, and find the learned models competitive on in-sample years "
     "but weaker in extrapolation — an observation that motivates the hybrid "
     "approach adopted later in this project."),
    ("p",
     "Two methodological criticisms recur in this body of work and are directly "
     "relevant here. The first is evaluation design: a substantial fraction of "
     "published studies split their data at random into training and test "
     "partitions, which leaks information across the temporal boundary because "
     "neighbouring years share weather regimes and yield trends. The second is "
     "the absence of significance testing: models are ranked on a single "
     "held-out score with no assessment of whether the gap between first and "
     "second place is distinguishable from noise."),

    ("h2", "2.3 Deep Learning and Hybrid Architectures"),
    ("p",
     "Kamilaris and Prenafeta-Boldú [2] surveyed deep learning across "
     "agriculture and documented rapid adoption, with convolutional networks "
     "dominating image-based tasks such as disease detection and yield mapping "
     "from imagery. LeCun, Bengio and Hinton [20] give the underlying rationale "
     "for representation learning: with sufficient data, a deep network learns "
     "features that outperform hand-engineered ones. The qualifier — sufficient "
     "data — is the pivot on which this project turns."),
    ("p",
     "For yield in particular, recurrent architectures are the natural fit for "
     "the weather stream because growing-season weather is a sequence and "
     "because the effect of a rainfall or heat event depends on the "
     "phenological stage at which it occurs. The Long Short-Term Memory unit of "
     "Hochreiter and Schmidhuber [16] is the standard building block, its gated "
     "cell state allowing gradients to propagate across the length of a growing "
     "season without vanishing. Bidirectional variants process the sequence in "
     "both directions, which is legitimate here because the full season is "
     "observed before the prediction is issued."),
    ("p",
     "Rajpoot and Chandrakar [8] propose exactly the hybrid this project also "
     "explores: a convolutional branch over spatial agricultural data combined "
     "with an LSTM branch over the temporal stream, merged before a dense head. "
     "Their reported gains over single-modality baselines are the strongest "
     "published argument for the architecture. Kim and Soon [11] take a "
     "different deep route for an allium crop, applying a Neural Prophet "
     "formulation to estimate onion bulb weight, and demonstrate that "
     "decomposable time-series models can capture seasonal structure in this "
     "crop family."),
    ("p",
     "What is common to the successful deep results is scale. The hybrid "
     "architectures are validated on datasets with thousands to tens of "
     "thousands of records. None of the surveyed work establishes whether the "
     "architectural advantage survives when the training set is reduced by "
     "three orders of magnitude, which is the regime this project occupies. "
     "That question is left open in the literature, and answering it "
     "empirically is one of this project's contributions."),

    ("h2", "2.4 Mechanistic and Hybrid Process-Based Models"),
    ("p",
     "Independent of the machine learning tradition, agronomy has a long "
     "history of mechanistic crop models that encode the physiology of the "
     "water-limited yield response directly. The canonical formulation is the "
     "FAO Irrigation and Drainage Paper 33 water-production function of "
     "Doorenbos and Kassam [31], which relates the relative yield decrement to "
     "the relative evapotranspiration deficit through a crop-specific yield "
     "response factor. For onion that factor is approximately 1.1, meaning the "
     "crop is slightly more than proportionally sensitive to water deficit — "
     "onion is a shallow-rooted crop with a high sensitivity to stress during "
     "bulb initiation."),
    ("p",
     "Thermal time, or growing degree days, is the second pillar of the "
     "mechanistic tradition. McMaster and Wilhelm [32] set out the standard "
     "computation and its pitfalls, and the accumulation of degree days above a "
     "crop-specific base temperature remains the standard proxy for "
     "phenological progress. The virtue of these formulations for the present "
     "problem is that they encode knowledge which does not have to be learned "
     "from data. In a thirty-record dataset, every relationship that can be "
     "supplied a priori rather than estimated is a relationship that does not "
     "consume degrees of freedom."),
    ("p",
     "The synthesis of the two traditions is the hybrid or residual approach. "
     "Shahhosseini et al. [33] demonstrate that coupling a process-based crop "
     "model with machine learning improves corn yield prediction over either "
     "component alone: the mechanistic model supplies the physiologically "
     "constrained trend, and the learned component absorbs the systematic "
     "residual that the simplified physics cannot express. Wang et al. [7] "
     "reach a compatible conclusion from the opposite direction. This residual "
     "architecture is directly adopted in the present work and is one of its "
     "two central methodological novelties."),

    ("h2", "2.5 Yield Prediction Research in Sri Lanka"),
    ("p",
     "The Sri Lankan literature is overwhelmingly concerned with paddy. "
     "Amarasinghe et al. [5] present the most directly comparable study: "
     "weather-based, feature-engineered machine learning models for rice yield "
     "prediction, with careful attention to the construction of derived "
     "meteorological predictors. Wickramasinghe et al. [10] model the rice "
     "yield-climate relationship with both statistical and machine learning "
     "techniques and quantify the sensitivity of yield to individual climate "
     "variables. Both studies benefit from the crop-cutting survey record that "
     "exists for paddy and not for vegetables."),
    ("p",
     "On the remote sensing side, Herath et al. [12] extracted agricultural "
     "phenological parameters for Sri Lanka from MODIS NDVI time series, "
     "establishing that the satellite record is of sufficient quality to "
     "resolve the country's cultivation seasons. This is an important "
     "precondition for the present work: it confirms that the vegetation index "
     "signal over Sri Lankan cropland is usable, even though the study did not "
     "itself predict yield."),
    ("p",
     "Sutharsan and Yogendran [14] address onion in Sri Lanka, but for the red "
     "onion price series in the Jaffna district rather than for yield, "
     "identifying correlated price factors and applying several regressors to "
     "the forecasting task. Their work confirms that machine learning is "
     "already being applied to Sri Lankan allium value chains, while leaving "
     "the yield side of the problem untouched."),

    ("h2", "2.6 Onion-Specific Research"),
    ("p",
     "Onion-specific yield prediction work is sparse. Iqbal et al. [9] present "
     "the closest analogue, a supervised machine learning approach to "
     "predicting onion yield from Bangladeshi climate data. The setting is "
     "genuinely comparable — a South Asian monsoon climate, a smallholder "
     "production system, and a national import dependence — and the study "
     "establishes that climate-driven onion yield prediction is feasible. It "
     "does not, however, incorporate satellite vegetation indices, does not "
     "address a bimodal season structure, and reports a single train-test split "
     "without significance testing."),
    ("p",
     "The agronomic literature on the crop itself is more developed than the "
     "predictive literature. The Department of Agriculture's HORDI cultivation "
     "guidelines [6] document the crop calendar, water requirement, and "
     "critical growth stages for big onion in Sri Lankan conditions, and these "
     "guidelines directly informed the growing-season windows and the "
     "mechanistic backbone constants used in this project. FAOSTAT [13] "
     "provides the production and trade series against which national-level "
     "figures were cross-checked."),

    ("h2", "2.7 Comparison of Existing Approaches"),
    ("p",
     "Table 2.1 compares the most relevant prior approaches along the "
     "dimensions that matter for this project: the crop and region addressed, "
     "the modelling family used, the data streams consumed, the evaluation "
     "protocol adopted, and the principal limitation with respect to the "
     "present problem."),
    ("table", (
        ["Work", "Crop / Region", "Method", "Data used", "Evaluation", "Limitation here"],
        [
            ["Jabed et al. [1]", "Multiple / global", "Review of ML and DL", "Various",
             "Survey", "No small-sample guidance"],
            ["Chikwendu et al. [3]", "Multiple", "RF, XGBoost, SVR, ANN", "Weather, soil",
             "Random split", "Split leaks temporal information"],
            ["Kamilaris & Prenafeta-Boldú [2]", "Multiple / global", "DL survey", "Imagery",
             "Survey", "Assumes large datasets"],
            ["Rajpoot & Chandrakar [8]", "Cereals", "Hybrid CNN-LSTM", "Spatio-temporal",
             "Held-out split", "Not validated at small n"],
            ["Kim & Soon [11]", "Onion (bulb weight)", "Neural Prophet", "Time series",
             "Time-series split", "Bulb weight, not district yield"],
            ["Shahhosseini et al. [33]", "Corn / US", "Process model + ML", "Weather, soil, crop model",
             "Multi-year", "Requires full APSIM-class model"],
            ["Wang et al. [7]", "Cereals", "ML vs process-based", "Meteorological",
             "Multi-year", "No satellite stream"],
            ["Amarasinghe et al. [5]", "Rice / Sri Lanka", "Feature-engineered ML", "Weather",
             "Cross-validation", "Paddy has crop-cutting surveys"],
            ["Wickramasinghe et al. [10]", "Rice / Sri Lanka", "Statistical + ML", "Climate",
             "Cross-validation", "Rice only"],
            ["Herath et al. [12]", "General / Sri Lanka", "Phenology extraction", "MODIS NDVI",
             "Descriptive", "No yield model"],
            ["Iqbal et al. [9]", "Onion / Bangladesh", "Supervised ML", "Climate",
             "Single split", "No satellite, no season structure"],
            ["Sutharsan & Yogendran [14]", "Red onion / Sri Lanka", "Multiple regressors", "Price factors",
             "Held-out split", "Price, not yield"],
        ],
        "Table 2.1: Comparison of existing yield-prediction approaches",
    )),

    ("h2", "2.8 Research Gaps Identified"),
    ("p",
     "Five gaps emerge from the comparison in Table 2.1, and this project is "
     "constructed to address them."),
    ("p",
     "Gap 1 — No big onion yield prediction system exists for Sri Lanka. The "
     "Sri Lankan yield-prediction literature is paddy-centric [5], [10]; the "
     "one Sri Lankan onion study addresses price rather than yield [14]; and "
     "the one comparable onion yield study is Bangladeshi and climate-only "
     "[9]. No published work predicts big onion yield for Sri Lankan districts."),
    ("p",
     "Gap 2 — No guidance exists on model selection under severe data scarcity "
     "for vegetable yield. The reviews [1], [2] and the comparative studies [3] "
     "operate at sample sizes that make the deep-versus-classical question "
     "answerable in the conventional way. None of them tells a practitioner "
     "with thirty observations whether a deep architecture is worth attempting. "
     "A rigorous comparison at that sample size, with significance testing, is "
     "itself a contribution regardless of which family wins."),
    ("p",
     "Gap 3 — Mechanistic and learned components are rarely combined at this "
     "scale. Shahhosseini et al. [33] demonstrate the value of the hybrid "
     "approach, but their process component is a full crop-simulation model "
     "requiring extensive parameterisation and calibration data. Whether a "
     "lightweight closed-form mechanistic backbone — FAO-33 water response [31] "
     "combined with growing degree days [32] — provides the same benefit at a "
     "fraction of the modelling cost is untested for this crop and this region."),
    ("p",
     "Gap 4 — Bimodal monsoon seasonality is not represented architecturally. "
     "Published hybrid architectures [8] were designed for single-season "
     "systems and treat season, when present at all, as one more numeric "
     "column. No work explicitly injects a season indicator at a chosen depth "
     "of the network so that shared feature extractors are learned across "
     "seasons while season-specific baselines are learned by the head."),
    ("p",
     "Gap 5 — No decomposition of data-source value exists for vegetable yield "
     "in Sri Lanka. A practitioner deciding whether to invest in a satellite "
     "ingestion pipeline, a weather station network, or better yield "
     "record-keeping has no evidence base for the decision in this crop and "
     "region. A controlled ablation across data-source configurations supplies "
     "that evidence."),

    ("h2", "2.9 Summary"),
    ("p",
     "This chapter reviewed the work of others across four traditions: "
     "classical machine learning on tabular agricultural features, deep and "
     "hybrid sequence-plus-convolution architectures, mechanistic process-based "
     "crop modelling, and the Sri Lankan and onion-specific literature. The "
     "comparison in Table 2.1 showed that no existing work combines the crop, "
     "the region, the multi-source data integration and the evaluation rigour "
     "that this problem requires, and five specific research gaps were "
     "identified. The next chapter describes the technologies adapted to close "
     "those gaps and argues why each is appropriate to this problem in "
     "particular."),
]


# ============================================================================
# Chapter 3 — Technology adapted
# ============================================================================

CHAPTER_3 = [
    ("chapter", ("3", "Technologies Adapted for Data-Scarce Yield Prediction")),

    ("h2", "3.1 Introduction"),
    ("p",
     "Chapter 2 identified five gaps in the existing literature. This chapter "
     "sets out the technologies adapted to address them. The organising "
     "principle throughout is that every technology is justified against one "
     "specific difficulty of this problem — a sample size of a few dozen "
     "records, a bimodal season structure, a need for interpretability by "
     "non-specialist users, and a requirement that uncertainty be stated rather "
     "than implied. Technologies that are merely popular are not adopted."),

    ("h2", "3.2 Data Acquisition Technologies"),
    ("p",
     "The system consumes four data streams. Table 3.1 lists them with their "
     "sources, native resolution and role in the model."),
    ("table", (
        ["Stream", "Source", "Native grain", "Role"],
        [
            ["District yield and extent", "Department of Census and Statistics [4]; FAOSTAT [13]",
             "District, season, year", "Prediction target and yield-history predictors"],
            ["Daily weather", "NASA POWER reanalysis [26]; CHIRPS rainfall [25]",
             "Daily, ~0.5° and 0.05°", "Temperature, rainfall, humidity, solar radiation aggregates"],
            ["Vegetation indices", "MODIS MOD13 NDVI/EVI [15]; Sentinel-2 [27], via Google Earth Engine [23]",
             "16-day / 5-day composite, 250 m–10 m", "Canopy vigour, anomaly, growth-rate predictors"],
            ["Land surface temperature", "MODIS MOD11A1 [28], via Google Earth Engine [23]",
             "Daily, 1 km", "Day and night surface thermal regime"],
            ["Soil properties", "ISRIC SoilGrids250m [24]",
             "Static, 250 m", "pH, organic carbon, clay and sand fraction"],
        ],
        "Table 3.1: Data sources adopted by the system",
    )),
    ("p",
     "Google Earth Engine [23] is adopted for the satellite streams rather than "
     "direct scene download for a decisive practical reason: the full MODIS and "
     "Sentinel-2 archives over the four districts run to terabytes, whereas the "
     "quantity actually needed is a handful of spatially averaged index values "
     "per district per composite period. Earth Engine performs the spatial "
     "reduction server-side and returns a table of a few thousand rows, which "
     "makes the ingestion tractable on a laptop."),
    ("p",
     "NASA POWER [26] is adopted for meteorology in preference to ground "
     "station records because the station network in the dry-zone districts is "
     "sparse and its record has gaps, whereas the reanalysis product is "
     "spatially complete and temporally continuous over the full study period. "
     "CHIRPS [25] supplements it for rainfall specifically, since its infrared "
     "and station-blended construction is better validated for tropical "
     "precipitation than a pure reanalysis field. SoilGrids [24] supplies "
     "static soil properties; these do not vary within the study period and "
     "therefore serve as district-level constants."),

    ("h2", "3.3 Classical Machine Learning Technologies"),
    ("h3", "3.3.1 Random Forest"),
    ("p",
     "Random Forest [17] is adopted as the primary classical learner. Its "
     "suitability here rests on three properties. Bootstrap aggregation over "
     "decorrelated trees reduces variance, which matters most precisely when "
     "the training set is small and a single tree would be unstable. Recursive "
     "partitioning naturally represents the threshold and saturation effects "
     "that characterise biological response curves — yield rises with "
     "accumulated thermal time and then plateaus — without any transformation "
     "of the input. And the ensemble degrades gracefully in the presence of "
     "irrelevant predictors, which is a real risk when thirty-two features are "
     "offered to twenty-eight training records."),
    ("h3", "3.3.2 Gradient boosting"),
    ("p",
     "XGBoost [18] is adopted as the boosted counterpart. Where Random Forest "
     "reduces variance by averaging, boosting reduces bias by fitting "
     "successive learners to the residual. The regularised objective of XGBoost "
     "— explicit L1 and L2 penalties on leaf weights plus a complexity term on "
     "tree structure — is the property that makes it usable at this sample "
     "size, since unregularised boosting would drive the training residual to "
     "zero within a few dozen rounds. Shallow trees and a low learning rate are "
     "configured accordingly."),
    ("h3", "3.3.3 Support Vector Regression"),
    ("p",
     "Support Vector Regression is adopted as the third classical learner "
     "because its capacity control is structurally different from that of the "
     "tree ensembles. The epsilon-insensitive loss ignores residuals inside a "
     "tolerance band, and the solution depends only on the support vectors, so "
     "model complexity is governed by the regularisation constant rather than "
     "by the number of observations. Including a learner with an orthogonal "
     "inductive bias strengthens the comparison and supplies genuine diversity "
     "to the stacking layer."),

    ("h2", "3.4 Deep Learning Technologies"),
    ("p",
     "Four deep architectures are adopted, all implemented in TensorFlow/Keras "
     "[22]. The LSTM [16] processes the weather sequence over the growing "
     "season, its gated cell state retaining information about early-season "
     "conditions until the point at which yield is determined. The "
     "Bidirectional LSTM extends this by running a second pass in reverse; this "
     "is legitimate for post-season inference because the whole season is "
     "observed before a forecast is issued, and it allows a late-season "
     "observation to inform the representation of an early-season one."),
    ("p",
     "The one-dimensional convolutional network is adopted for the vegetation "
     "index sequence rather than the weather sequence. The distinction is "
     "deliberate: the informative content of an NDVI trajectory is its local "
     "shape — the steepness of green-up, the timing and height of the peak, the "
     "rate of senescence — and a convolutional filter bank is the natural "
     "detector for local shape, whereas a recurrent unit is the natural "
     "integrator for cumulative effect."),
    ("p",
     "The hybrid CNN-LSTM combines the two, following the architectural family "
     "of Rajpoot and Chandrakar [8] but with a modification specific to this "
     "problem: the season indicator is concatenated after both branches have "
     "completed feature extraction, immediately before the dense head. The "
     "consequence is that the convolutional and recurrent branches learn "
     "season-agnostic feature extractors, sharing all their parameters across "
     "both seasons and therefore across the whole dataset, while only the small "
     "dense head learns season-specific yield baselines. This is a data-"
     "efficiency argument, not merely an architectural preference, and it is "
     "the second novelty of the work. The design is described in detail in "
     "section 5.5 and illustrated in Figure 5.2."),
    ("p",
     "All four networks are deliberately small — the hybrid holds approximately "
     "45,000 parameters against the millions typical of image classifiers — and "
     "are regularised with dropout at twenty per cent and early stopping on a "
     "validation split. Even so, section 7.4 will show that at this sample size "
     "the deep family does not compete, and reporting that outcome honestly is "
     "part of the contribution."),

    ("h2", "3.5 Symbolic Regression"),
    ("p",
     "Symbolic regression is adopted to address a requirement that neither the "
     "tree ensembles nor the networks satisfy: producing a model that an "
     "agricultural officer can read, check against agronomic intuition, and "
     "compute by hand. Rather than fitting parameters within a fixed functional "
     "form, symbolic regression searches the space of mathematical expressions "
     "themselves using genetic programming [34], evolving a population of "
     "expression trees under a fitness pressure that balances accuracy against "
     "expression length."),
    ("p",
     "The gplearn implementation is used, restricted to a small function set — "
     "addition, subtraction, multiplication, protected division and square root "
     "— and to the five predictors that SHAP identifies as most influential. "
     "The restriction is essential: an unconstrained search over thirty-two "
     "predictors with a rich function set would produce an expression that fits "
     "twenty-eight points perfectly and generalises not at all. The resulting "
     "equation is reported in section 7.7 and served through the API so that "
     "the dashboard can display it alongside the numerical forecast."),

    ("h2", "3.6 Physics-Informed Residual Modelling"),
    ("p",
     "The physics-residual hybrid is the principal methodological technology "
     "adapted in this work, and it is adopted as a direct response to the "
     "sample-size problem. The argument is one of degrees of freedom. With "
     "twenty-eight training records, every relationship the model must "
     "discover from data consumes statistical budget that is not available. "
     "Any relationship that can instead be supplied from established agronomy "
     "is free."),
    ("p",
     "The mechanistic backbone is assembled from three established components. "
     "Thermal time is represented by a saturating function of accumulated "
     "growing degree days following McMaster and Wilhelm [32], expressing that "
     "the crop must accumulate heat to complete its cycle and that the benefit "
     "saturates once the requirement is met. Water limitation follows the "
     "FAO-33 water production function of Doorenbos and Kassam [31], applied "
     "through the standardised precipitation index as the deficit measure and "
     "using the published onion yield response factor of approximately 1.1. "
     "Heat stress is represented as a linear decrement in the count of days "
     "above the crop's critical temperature threshold."),
    ("p",
     "These three multiplicative factors are combined into a single "
     "physiological suitability term, which is then calibrated to the yield "
     "scale by a two-parameter linear fit — an intercept and a slope. Only "
     "those two parameters are estimated from data; the internal constants come "
     "from the agronomic literature. A Random Forest is then trained on the "
     "residual between the observed yield and this calibrated backbone, so that "
     "the learned component only has to model what the physics does not "
     "explain. This follows the residual-hybrid logic of Shahhosseini et al. "
     "[33] but uses a closed-form backbone rather than a full crop simulator, "
     "which is what makes it feasible at this data scale. The design is "
     "detailed in section 5.6 and its measured effect reported in section 7.5."),

    ("h2", "3.7 Ensemble Stacking"),
    ("p",
     "Stacked generalization, introduced by Wolpert [35], combines the "
     "predictions of several base learners through a meta-learner trained on "
     "their out-of-fold predictions. The technology is adopted here because the "
     "base learners have genuinely different inductive biases — a mechanistic "
     "backbone, two tree ensembles, a kernel method, four networks and a "
     "symbolic expression — and because such diversity is exactly the condition "
     "under which combination is expected to help."),
    ("p",
     "The meta-learner is deliberately constrained rather than free. Breiman "
     "[36] showed that stacking weights should be constrained to be "
     "non-negative to avoid the wild cancellation that unconstrained least "
     "squares produces on correlated base predictions. This project goes "
     "further and constrains the weights to the probability simplex — "
     "non-negative and summing to one — so that the combination is a convex "
     "blend. With twenty-eight observations and nine base models, an "
     "unconstrained meta-learner would have more freedom than the data can "
     "support; the simplex constraint reduces the effective degrees of freedom "
     "to a level the sample can bear."),
    ("p",
     "Three combiners are evaluated: an equal-weight mean, weights proportional "
     "to inverse validation RMSE, and the constrained convex fit. The "
     "comparison is not arbitrary. The forecast-combination puzzle — the "
     "persistent empirical finding that a simple equal-weight average often "
     "outperforms an optimally estimated weighting, because estimating the "
     "weights introduces more error than optimising them removes — is a "
     "well-documented phenomenon in the forecasting literature [37], [38]. "
     "Whether it holds in this setting is an empirical question answered in "
     "section 7.6."),

    ("h2", "3.8 Conformal Prediction and Explainability"),
    ("p",
     "A point forecast without an uncertainty statement is of limited use to "
     "someone sizing an import order. Split-conformal prediction [39], [40] is "
     "adopted to attach intervals because of one property that no alternative "
     "shares: it is distribution-free. It makes no assumption that residuals "
     "are Gaussian, or homoscedastic, or that the model is correctly specified. "
     "It requires only that the calibration and test data be exchangeable, and "
     "it then guarantees marginal coverage at the nominal level in finite "
     "samples. Given that the residual distributions here are visibly "
     "non-Gaussian and the sample is small, a parametric interval would be "
     "making assurances the data cannot support."),
    ("p",
     "The construction is simple: take the absolute residuals from the "
     "out-of-fold predictions, take their empirical quantile at the required "
     "level with the appropriate finite-sample correction, and use that "
     "quantile as the interval half-width. Section 7.10 reports the resulting "
     "half-widths and their empirical coverage, along with an honest discussion "
     "of what a calibration set of twenty-eight points can and cannot certify."),
    ("p",
     "For explanation, SHAP [19] is adopted. Its attributions are the Shapley "
     "values of a cooperative game in which the players are the features and "
     "the payoff is the prediction, which gives them a uniqueness property that "
     "heuristic importance measures lack: they are the only attribution "
     "satisfying local accuracy, missingness and consistency simultaneously. "
     "The TreeExplainer variant computes them exactly and in polynomial time "
     "for tree ensembles, which is what makes the method practical here."),

    ("h2", "3.9 Evaluation Technology: Leave-One-Year-Out Cross-Validation"),
    ("p",
     "The evaluation protocol is itself a technology choice, and arguably the "
     "most consequential one in this project. Leave-One-Year-Out "
     "cross-validation holds out all records from a single year, trains on the "
     "remaining years, predicts the held-out year, and rotates through every "
     "year in the record. The rationale is that a random split would place "
     "records from the same year on both sides of the boundary; because "
     "districts within a year share a weather regime, a monsoon anomaly and a "
     "national price environment, such a split lets the model see the answer "
     "for a year it is then asked to predict. Reported scores would be "
     "optimistic in a way that would not survive deployment."),
    ("p",
     "Hyperparameter selection is nested inside the outer fold: within each "
     "training partition, an inner search using a time-series-aware split "
     "chooses the configuration, and only then is the outer held-out year "
     "scored. This prevents the subtler leak in which the held-out year "
     "influences model selection even though it never enters model fitting."),
    ("p",
     "Model comparison uses the paired Wilcoxon signed-rank test [30] on "
     "per-record absolute residuals. The pairing is essential — the same records are "
     "predicted by every model, so a paired test has far more power than an "
     "unpaired comparison of aggregate scores — and the non-parametric form is "
     "appropriate because residual distributions at this sample size cannot be "
     "assumed normal."),

    ("h2", "3.10 Software and Tools"),
    ("p",
     "Table 3.2 lists the software adopted, with the role each plays. All are "
     "open-source, which matters for a system intended for a public-sector user "
     "with no software budget."),
    ("table", (
        ["Tool", "Version", "Role"],
        [
            ["Python", "3.12", "Implementation language for the pipeline and API"],
            ["pandas / NumPy", "current", "Data reconciliation, aggregation and array computation"],
            ["scikit-learn [21]", "1.5", "Random Forest, SVR, cross-validation, metrics, grid search"],
            ["XGBoost [18]", "2.x", "Regularised gradient boosting"],
            ["TensorFlow / Keras [22]", "2.16", "LSTM, BiLSTM, 1D-CNN and hybrid CNN-LSTM"],
            ["gplearn [34]", "0.4", "Genetic-programming symbolic regression"],
            ["SHAP [19]", "0.4x", "Exact tree-ensemble feature attribution"],
            ["SciPy", "current", "Wilcoxon signed-rank and paired t tests, optimisation"],
            ["Matplotlib / Seaborn", "current", "Figure generation"],
            ["Flask", "3.x", "REST serving layer"],
            ["Next.js / TypeScript", "16 / 5", "Decision-support dashboard"],
            ["Tailwind CSS", "4", "Dashboard styling"],
            ["Google Earth Engine [23]", "Python API", "Server-side satellite reduction"],
            ["Git", "current", "Version control and reproducibility"],
        ],
        "Table 3.2: Software and tools",
    )),

    ("h2", "3.11 Summary"),
    ("p",
     "This chapter set out the technologies adapted to the problem and, for "
     "each, the specific difficulty it addresses. Google Earth Engine and "
     "reanalysis products make multi-source data acquisition feasible on "
     "commodity hardware. Tree ensembles and Support Vector Regression supply "
     "small-sample-robust learners with diverse inductive biases. Four deep "
     "architectures test whether representation learning survives at this "
     "scale, with the hybrid CNN-LSTM's season-indicator injection designed "
     "specifically for the bimodal monsoon structure. Symbolic regression "
     "supplies a readable equation. The physics-residual hybrid substitutes "
     "established agronomy for data-hungry estimation. Constrained convex "
     "stacking combines the family without overfitting the combination. "
     "Split-conformal prediction attaches distribution-free intervals, SHAP "
     "supplies attributions, and Leave-One-Year-Out cross-validation with "
     "paired significance testing ensures the reported numbers are honest. The "
     "next chapter describes how these technologies are assembled into a "
     "working system."),
]


# ============================================================================
# Chapter 4 — Your approach
# ============================================================================

CHAPTER_4 = [
    ("chapter", ("4", "The Agro AI Approach")),

    ("h2", "4.1 Introduction"),
    ("p",
     "Chapter 3 described the technologies adapted to the problem individually. "
     "This chapter describes how they are assembled into a system that solves "
     "it. It states who the users are and what each needs, what the system "
     "consumes and produces, the nine-stage process by which one becomes the "
     "other, and the top-level architecture within which all of it sits. It "
     "closes with a walkthrough of a single prediction from request to response "
     "and a statement of the system's operating requirements."),

    ("h2", "4.2 Users"),
    ("p",
     "The system is built for four distinct user groups whose information needs "
     "differ substantially. Designing a single interface for all four would "
     "serve none of them, so the dashboard presents different views to "
     "different roles. Table 4.1 records the groups, their decisions and the "
     "system output each depends on."),
    ("table", (
        ["User group", "Decision they take", "Output they need", "Dashboard view"],
        [
            ["DCS statistical officers", "Validate and publish district yield estimates",
             "Point forecast plus interval, as a prior on field returns", "Prediction and map"],
            ["DoA / Ministry policy analysts", "Size and time import tenders",
             "National aggregate with uncertainty band", "Overview and map"],
            ["District agricultural officers", "Target extension and irrigation advice",
             "Per-district forecast with SHAP drivers", "Explainability and recommendation"],
            ["Researchers and students", "Assess method and reuse findings",
             "Model comparison, ablation, symbolic equation", "Admin and explainability"],
        ],
        "Table 4.1: User groups and their information needs",
    )),
    ("p",
     "A design consequence follows from this table. Two of the four groups are "
     "not machine learning specialists and will not accept a number without a "
     "reason for it. That is why explainability is treated as a functional "
     "requirement of the system rather than as an analytical extra, and why "
     "both SHAP attributions and the symbolic equation are served through the "
     "API rather than left in the analysis notebooks."),

    ("h2", "4.3 Inputs and Outputs"),
    ("p",
     "Table 4.2 states the system's inputs and outputs precisely. Inputs are "
     "listed at the grain at which the model consumes them, after the "
     "aggregation described in section 4.4."),
    ("table", (
        ["Direction", "Item", "Type", "Grain"],
        [
            ["Input", "District identifier", "Categorical (4 levels)", "Per record"],
            ["Input", "Season identifier", "Categorical (Yala / Maha)", "Per record"],
            ["Input", "Year", "Integer", "Per record"],
            ["Input", "Weather aggregates (9)", "Continuous", "Per district-season-year"],
            ["Input", "Vegetation and LST indices (11)", "Continuous", "Per district-season-year"],
            ["Input", "Yield history (5)", "Continuous", "Per district-season-year"],
            ["Input", "Soil properties (4)", "Continuous", "Per district (static)"],
            ["Input", "Interaction terms (3)", "Continuous", "Derived"],
            ["Output", "Point yield forecast", "Continuous, MT/Ha", "Per district-season-year"],
            ["Output", "Prediction interval", "Lower and upper bound, MT/Ha", "Per prediction"],
            ["Output", "SHAP attribution", "Ranked list of contributions", "Per prediction"],
            ["Output", "Symbolic equation", "Expression string", "Global"],
            ["Output", "Model comparison metrics", "RMSE, MAE, R², MAPE per model", "Global"],
        ],
        "Table 4.2: System inputs and outputs",
    )),

    ("h2", "4.4 Process: The Nine-Stage Pipeline"),
    ("p",
     "The transformation from raw source files to served artefacts proceeds "
     "through nine stages, shown in Figure 4.2 and described below. Every stage "
     "writes its output to disk, so the pipeline is restartable and every "
     "intermediate is inspectable."),
    ("p",
     "Stage 1 — Load and reconcile. Each raw source arrives on its own grain: "
     "weather is daily, vegetation indices are composite periods, soil is "
     "static, and yield is per season. The loader reads each, applies the "
     "growing-season window for the district and season, and reduces every "
     "stream to the common district-season-year key. Where a required stream is "
     "absent, a calibrated synthetic generator supplies a stand-in so that the "
     "pipeline remains executable end to end; this fallback is used only for "
     "architecture validation and is clearly separated from the real-data run."),
    ("p",
     "Stage 2 — Preprocess. Records are validated against expected ranges, "
     "impossible values are removed, missing values are imputed by district "
     "median, and the categorical district and season fields are encoded. The "
     "target is checked against published district yield ranges to catch unit "
     "errors, which are the most common failure mode in multi-source "
     "agricultural data."),
    ("p",
     "Stage 3 — Engineer features. Thirty-two predictors are derived across "
     "five groups: weather aggregates, vegetation dynamics, yield history, soil "
     "properties and cross-modal interactions. The interaction terms in "
     "particular encode agronomic hypotheses rather than statistical "
     "convenience, and are described in section 5.3."),
    ("p",
     "Stage 4 — Exploratory analysis. Distribution, time-series, correlation, "
     "seasonal and district-comparison plots are generated. This stage produces "
     "no model artefact but is retained in the pipeline because it is where "
     "data errors surface."),
    ("p",
     "Stage 5 — Train classical models. Random Forest, XGBoost and Support "
     "Vector Regression are trained under Leave-One-Year-Out cross-validation "
     "with nested hyperparameter search, and their out-of-fold predictions are "
     "recorded per record."),
    ("p",
     "Stage 6 — Train symbolic and physics-residual models. Symbolic regression "
     "evolves an expression over the top five predictors. The physics-residual "
     "hybrid calibrates its mechanistic backbone on the training partition of "
     "each fold and fits a Random Forest to the residual, under the same "
     "cross-validation."),
    ("p",
     "Stage 7 — Train deep models. LSTM, BiLSTM, 1D-CNN and the hybrid "
     "CNN-LSTM are each trained per fold with early stopping, and their "
     "learning curves and out-of-fold predictions are recorded."),
    ("p",
     "Stage 8 — Combine, calibrate and explain. The stacking layer fits its "
     "three combiners on out-of-fold predictions under a nested protocol; "
     "split-conformal quantiles are computed from the residuals; SHAP "
     "attributions are extracted from the best tree model; and the ablation "
     "study re-runs the protocol under six data-source configurations."),
    ("p",
     "Stage 9 — Compare and persist. All models are ranked on the shared "
     "metrics, paired significance tests are run, and the comparison table, "
     "summary findings, plots, fitted models and JSON artefacts are written for "
     "the serving layer."),
    ("fig", (f"{FIGDIR}/figure_4_2_pipeline_stages.png",
             "Figure 4.2: The nine-stage processing pipeline")),

    ("h2", "4.5 Top-Level System Architecture"),
    ("p",
     "The top level architecture of the proposed system comprises four modules: "
     "the data acquisition and integration module, the modelling and evaluation "
     "module, the serving module, and the presentation module. Figure 4.1 shows "
     "the interaction among these modules."),
    ("fig", (f"{FIGDIR}/figure_4_1_system_architecture.png",
             "Figure 4.1: Top-level architecture of the proposed system")),
    ("p",
     "The data acquisition and integration module is responsible for reading "
     "each external source, applying the season window, reducing to the common "
     "key and producing the analysis dataset. It writes a processed dataset to "
     "disk and does not communicate with any other module directly; the "
     "file is the interface. This decoupling is deliberate, because it allows "
     "the data component and the modelling component to be developed and tested "
     "independently by different group members."),
    ("p",
     "The modelling and evaluation module reads the processed dataset and is "
     "responsible for all training, cross-validation, combination, calibration, "
     "attribution and comparison. It writes fitted model files, an out-of-fold "
     "prediction record per model, a comparison table, calibration quantiles, "
     "attribution rankings and the summary of findings. It is the only module "
     "that performs learning."),
    ("p",
     "The serving module reads those artefacts at start-up and exposes them "
     "over HTTP. It performs no training. Its responsibilities are to validate "
     "an incoming feature payload, apply the same preprocessing the training "
     "pipeline applied, invoke the selected model, attach the conformal "
     "interval and attribution, and return a structured response. Keeping "
     "training and serving strictly separate means a model can be retrained "
     "without touching the service, and the service can be restarted without "
     "retraining."),
    ("p",
     "The presentation module is the dashboard. It consumes only the serving "
     "module's HTTP interface and holds no model logic. It renders the "
     "choropleth map of district forecasts, the prediction form with "
     "context-aware prefilling, the explainability view and the administrative "
     "model-comparison panel."),

    ("h2", "4.6 Walkthrough of a Single Prediction"),
    ("p",
     "To make the interaction concrete, consider a district agricultural "
     "officer requesting a forecast for Anuradhapura, Yala, in the current "
     "year. The dashboard first calls the context endpoint, which returns the "
     "most recent known values of every predictor for that district and season, "
     "so the officer is not asked to type thirty-two numbers. The officer "
     "adjusts any value they have better information about — perhaps this "
     "season's rainfall has been unusually low — and submits."),
    ("p",
     "The serving module receives the payload, validates that every required "
     "predictor is present and within its plausible range, assembles the "
     "feature vector in the exact column order the model was trained on, and "
     "invokes the selected model. It then looks up the conformal half-width for "
     "that model and constructs the interval, computes the SHAP attribution for "
     "this specific feature vector, and returns the point forecast, the "
     "interval, the ranked attribution and a provenance record stating which "
     "model produced the number and on which dataset it was trained. The "
     "dashboard renders the forecast with its interval and displays the three "
     "largest positive and negative attributions as the explanation."),

    ("h2", "4.7 System Requirements"),
    ("p",
     "Functionally, the system must produce a district-season yield forecast "
     "from a feature payload, attach a calibrated interval, explain the "
     "forecast, expose the comparison of candidate models, and provide "
     "context-aware prefill values for the input form."),
    ("p",
     "Non-functionally, four requirements shaped the design. Reproducibility: "
     "every random seed is fixed and every artefact is written to disk, so that "
     "a re-run reproduces the reported numbers exactly. Modest hardware: the "
     "full pipeline completes in approximately six minutes on a laptop with "
     "eight gigabytes of memory and no GPU. Interpretability: no forecast is "
     "served without an accompanying attribution. Honesty: no metric is "
     "reported without the evaluation protocol that produced it, and negative "
     "results are reported as prominently as positive ones."),

    ("h2", "4.8 Summary"),
    ("p",
     "This chapter described the approach: four user groups with distinct "
     "information needs, a precisely specified set of inputs and outputs, a "
     "nine-stage pipeline that transforms one into the other, and a four-module "
     "architecture in which data integration, modelling, serving and "
     "presentation are cleanly separated by file and HTTP interfaces. A single "
     "prediction was traced end to end, and the functional and non-functional "
     "requirements were stated. The next chapter opens each module and gives "
     "its internal design."),
]


# ============================================================================
# Chapter 5 — Analysis and Design
# ============================================================================

CHAPTER_5 = [
    ("chapter", ("5", "Analysis and Design of the Prediction System")),

    ("h2", "5.1 Introduction"),
    ("p",
     "Chapter 4 gave the top-level architecture and stated what each of the "
     "four modules is responsible for. This chapter opens those modules and "
     "gives their internal design: how data flows through the system, how the "
     "thirty-two predictors are constructed and why, how each model family is "
     "configured, how the mechanistic backbone is formulated, how the stacking "
     "layer is constrained, how uncertainty and explanation are produced, and "
     "how the serving and presentation tiers are structured."),

    ("h2", "5.2 Data Flow Design"),
    ("p",
     "Figure 5.1 shows the flow of data through the system, from the external "
     "sources on the left to the served artefacts on the right. Each arrow "
     "represents a file written by one component and read by the next; there "
     "are no in-memory hand-offs between the major stages. This is a "
     "reproducibility decision: any stage can be re-run in isolation against "
     "the persisted output of the stage before it."),
    ("fig", (f"{FIGDIR}/figure_5_1_data_flow.png",
             "Figure 5.1: Data flow through the prediction system")),
    ("p",
     "Three reconciliation problems are solved in the first transformation. "
     "The first is grain mismatch: weather arrives daily, vegetation indices "
     "arrive on composite periods, soil is static and yield is seasonal. All "
     "are reduced to one record per district, season and year by applying the "
     "growing-season month window and aggregating within it, using the mean for "
     "state variables such as temperature and the sum for flux variables such "
     "as rainfall."),
    ("p",
     "The second is the key mismatch. District names appear with different "
     "spellings and casings across sources, and the satellite export keys on "
     "geometry identifiers rather than names. A canonical district vocabulary "
     "is defined in configuration and every source is mapped onto it at load "
     "time, so that a silent join failure — which would manifest as missing "
     "predictors rather than as an error — cannot occur unnoticed."),
    ("p",
     "The third is the seasonal boundary. The Maha season spans the calendar "
     "year boundary, running from October to March, so a naive grouping by "
     "calendar year would split a single Maha season across two records. The "
     "season window is therefore defined as an explicit month list per season, "
     "and Maha records are attributed to the year in which the season begins."),

    ("h2", "5.3 Feature Engineering Design"),
    ("p",
     "Thirty-two predictors are constructed across five groups. Table 5.1 lists "
     "them with the agronomic rationale for each group."),
    ("table", (
        ["Group", "Count", "Predictors", "Rationale"],
        [
            ["Weather", "9",
             "season_avg_temp, season_total_rainfall, season_avg_humidity, "
             "season_avg_solar_rad, growing_degree_days, heat_stress_days, "
             "drought_index_spi, temp_range, max_daily_rainfall",
             "Thermal, water and radiation drivers of biomass accumulation"],
            ["Satellite", "11",
             "season_mean/max/min_ndvi, ndvi_std, ndvi_anomaly, time_to_peak_ndvi, "
             "ndvi_growth_rate, season_mean_evi, season_mean_ndwi, "
             "season_mean_lst_day, season_mean_lst_night",
             "Realised canopy vigour, phenological timing and surface thermal regime"],
            ["Historical", "5",
             "prev_season_yield, prev_year_yield, yield_3yr_avg, season_indicator, "
             "extent_prev_season",
             "District-level productivity baseline and season conditioning"],
            ["Soil", "4", "soil_ph, organic_carbon, clay_pct, sand_pct",
             "Static water-holding and nutrient-supply capacity"],
            ["Interaction", "3", "rainfall_x_ndvi, temp_x_humidity, ndvi_x_lst",
             "Encoded agronomic hypotheses about joint effects"],
        ],
        "Table 5.1: The thirty-two engineered predictors by group",
    )),
    ("h3", "5.3.1 Weather aggregates"),
    ("p",
     "Growing degree days accumulate the daily mean temperature above a "
     "crop-specific base over the season, following the standard formulation "
     "[32]. Heat stress days count the days on which the maximum exceeded the "
     "crop's critical threshold, capturing damage that a seasonal mean would "
     "average away. The standardised precipitation index expresses seasonal "
     "rainfall as a standardised anomaly against the district's own "
     "distribution, which is the form in which the FAO-33 water response "
     "function [31] is applied in section 5.6. Maximum daily rainfall is "
     "retained separately because a single intense event can cause lodging and "
     "waterlogging damage that the seasonal total conceals."),
    ("h3", "5.3.2 Vegetation dynamics"),
    ("p",
     "The vegetation group deliberately extracts the shape of the NDVI "
     "trajectory rather than only its level. The mean summarises overall "
     "vigour; the maximum locates the peak canopy; the minimum captures the "
     "worst point of the season; the standard deviation measures within-season "
     "variability. The anomaly expresses the season's mean against the "
     "district's own historical mean, which removes the persistent district "
     "effect arising from differences in soil and cropping intensity. Time to "
     "peak and growth rate encode phenological timing: a crop that greens up "
     "rapidly and peaks early behaves differently from one that develops "
     "slowly, even at the same peak level."),
    ("h3", "5.3.3 Interaction terms"),
    ("p",
     "The three interaction terms are the only features constructed from "
     "hypothesis rather than from direct measurement, and each encodes a "
     "specific agronomic claim. The rainfall-NDVI product expresses that "
     "rainfall is beneficial only when there is a canopy to use it; the same "
     "rainfall on bare soil is runoff. The temperature-humidity product is a "
     "proxy for evaporative demand and, jointly, for fungal disease pressure, "
     "since warm and humid conditions favour the pathogens that affect onion "
     "foliage. The NDVI-LST product captures whether a green canopy is also "
     "thermally stressed: a high vegetation index with a high surface "
     "temperature indicates a canopy under heat load, which is a different "
     "state from the same greenness at a moderate temperature."),
    ("h3", "5.3.4 Sequential representation for the deep models"),
    ("p",
     "The deep models require a sequence rather than a flat vector. A parallel "
     "representation is therefore constructed in which each record is expanded "
     "into a fixed-length sequence of monthly time steps across the growing "
     "season, with four weather channels per step and the vegetation index "
     "series aligned to the same axis. The static soil properties and the "
     "season indicator remain scalar and are injected at the dense head. This "
     "dual representation — tabular for the classical models, sequential for "
     "the deep ones — is what allows both families to be compared on identical "
     "underlying information."),

    ("h2", "5.4 Classical Model Design"),
    ("p",
     "Table 5.2 records the model inventory and the design rationale for each "
     "member. Nine predictors are trained in total, spanning four distinct "
     "modelling philosophies."),
    ("table", (
        ["Model", "Family", "Key design choice", "Why included"],
        [
            ["Random Forest", "Bagged trees", "200 trees, depth-limited, min leaf 2",
             "Variance reduction; robust small-sample baseline"],
            ["XGBoost", "Boosted trees", "Depth 3–5, lr 0.05, L1+L2 penalties",
             "Bias reduction under explicit regularisation"],
            ["SVR", "Kernel method", "RBF kernel, epsilon-insensitive loss",
             "Orthogonal inductive bias; capacity independent of n"],
            ["LSTM", "Recurrent", "64→32 units, dropout 0.2",
             "Temporal integration of weather sequence"],
            ["BiLSTM", "Recurrent", "Bidirectional 64→32",
             "Both-direction context; legitimate post-season"],
            ["1D-CNN", "Convolutional", "Filter bank over index sequence",
             "Local shape detection in NDVI trajectory"],
            ["Hybrid CNN-LSTM", "Two-branch", "CNN + LSTM branches, season injected at head",
             "Modality-appropriate extraction; season conditioning"],
            ["Symbolic regression", "Genetic programming", "5 predictors, restricted operators",
             "Human-readable closed-form equation"],
            ["Physics-residual", "Mechanistic + ML", "FAO-33/GDD backbone + RF on residual",
             "Substitutes agronomy for scarce degrees of freedom"],
        ],
        "Table 5.2: Model inventory and design rationale",
    )),
    ("p",
     "For the classical learners the design decisions that matter most are the "
     "capacity limits. Random Forest is configured with a minimum leaf size "
     "above one so that no leaf can be a single training record, which is the "
     "mechanism by which a forest memorises a small dataset. XGBoost is held to "
     "shallow trees and a low learning rate for the same reason, with both L1 "
     "and L2 penalties on leaf weights active. Support Vector Regression uses a "
     "radial basis kernel with the regularisation constant and epsilon selected "
     "inside the cross-validation fold rather than fixed by hand."),

    ("h2", "5.5 Deep Model Design and the Hybrid CNN-LSTM"),
    ("p",
     "The three single-branch networks share a common design skeleton: a "
     "sequence input, one or two recurrent or convolutional layers with "
     "dropout, a global pooling or final-state extraction, and a small dense "
     "head terminating in a single linear output. All are held small "
     "deliberately, on the order of ten to eighty thousand parameters, because "
     "the training set contains fewer records than a conventional network has "
     "units in one layer."),
    ("p",
     "The hybrid CNN-LSTM is the architectural contribution and its design is "
     "shown in Figure 5.2. Two branches process the two modalities in parallel. "
     "The convolutional branch consumes the vegetation index sequence, applying "
     "a filter bank that detects local trajectory shape — green-up steepness, "
     "peak sharpness, senescence rate — followed by pooling. The recurrent "
     "branch consumes the weather sequence, its gated cell state integrating "
     "the cumulative effect of temperature, rainfall, humidity and radiation "
     "across the season. Neither branch sees the other's modality."),
    ("fig", (f"{FIGDIR}/figure_5_2_cnn_lstm_hybrid.png",
             "Figure 5.2: Hybrid CNN-LSTM architecture with season-indicator injection")),
    ("p",
     "The design decision that distinguishes this architecture from the "
     "published family [8] is where the season indicator enters. It is not "
     "appended to the input sequences, and it is not used to select between two "
     "separately trained models. It is concatenated with the two branch outputs "
     "immediately before the dense head. The consequence is a specific division "
     "of labour: because the branches never see the season variable, they are "
     "forced to learn feature extractors that are valid for both seasons, and "
     "they therefore train on the entire dataset rather than on a per-season "
     "subset. Only the dense head, which holds a small fraction of the "
     "parameters, learns season-specific behaviour."),
    ("p",
     "The data-efficiency argument follows directly. Training separate "
     "per-season models would halve the effective sample for every parameter. "
     "Appending the season indicator to the input sequence would let the "
     "convolutional and recurrent filters specialise on season, dissipating the "
     "same advantage more subtly. Injecting at the head shares all the "
     "expensive representation learning while retaining the capacity to express "
     "a season-specific yield baseline. In a regime where the sample is the "
     "binding constraint, that division is the whole point."),

    ("h2", "5.6 Physics-Residual Hybrid Design"),
    ("p",
     "The physics-residual hybrid is a two-stage predictor. The first stage is "
     "a mechanistic backbone with no learned internal parameters; the second is "
     "a Random Forest trained on what the backbone leaves unexplained."),
    ("p",
     "The backbone computes three physiological limitation factors. The thermal "
     "factor is a saturating exponential in accumulated growing degree days, "
     "expressing that the crop must accumulate a heat requirement to complete "
     "its cycle and that further accumulation beyond that requirement confers "
     "no additional benefit; the characteristic scale is set at 1500 degree "
     "days, consistent with the published thermal requirement for the crop "
     "[32]. The water factor applies the FAO-33 production function [31] "
     "through the standardised precipitation index, using the published onion "
     "yield response factor of 1.1 so that a unit relative water deficit "
     "produces a slightly more than proportional relative yield loss, and "
     "clipping the result to the physically admissible interval. The heat "
     "factor applies a linear decrement of three per cent per day above the "
     "critical temperature threshold, also clipped."),
    ("p",
     "The three factors multiply into a single suitability term between zero "
     "and one. Because that term is dimensionless and the target is in metric "
     "tons per hectare, a two-parameter affine calibration maps one to the "
     "other. Those two parameters — an intercept and a slope — are the only "
     "quantities in the backbone estimated from data, and they are re-estimated "
     "on the training partition inside every cross-validation fold so that no "
     "information from the held-out year reaches the calibration."),
    ("p",
     "The second stage fits a Random Forest to the difference between the "
     "observed yield and the calibrated backbone prediction, using the full "
     "thirty-two-predictor vector. The final forecast is the sum of the two. "
     "The design intent is that the backbone carries the physiologically "
     "constrained component of the response — which does not have to be learned "
     "— and the forest models only the systematic departures arising from "
     "management, cultivar, pest pressure and everything else the simplified "
     "physics omits. Section 7.5 measures whether this intent is realised."),

    ("h2", "5.7 Stacking Layer Design"),
    ("p",
     "The stacking layer combines the nine base predictors. Its design has "
     "three deliberate constraints, each addressing a way in which naive "
     "stacking fails at this sample size."),
    ("p",
     "First, the meta-learner is fitted on out-of-fold predictions only. Each "
     "base model's prediction for a given record was produced by a version of "
     "that model which never saw the record, so the meta-learner is trained on "
     "predictions with realistic error, not on the optimistically small "
     "residuals a model produces on its own training data."),
    ("p",
     "Second, the weights are constrained to the probability simplex: "
     "non-negative and summing to one. Breiman [36] established the "
     "non-negativity requirement; the sum-to-one constraint is added here "
     "because it makes the combination a convex blend, guaranteeing that the "
     "stacked prediction lies within the range of the base predictions and "
     "cannot be driven outside it by the cancellation of large opposing "
     "weights. With nine base models and twenty-eight records, this reduction "
     "of effective degrees of freedom is not optional."),
    ("p",
     "Third, three combiners are computed rather than one, so that the "
     "forecast-combination puzzle [37], [38] can be tested rather than assumed. "
     "The equal-weight mean estimates nothing. The inverse-RMSE weighting "
     "estimates only a scalar reliability per model. The constrained convex fit "
     "estimates the full weight vector under the simplex constraint. If the "
     "puzzle holds in this setting, the mean will win; if the learned blend "
     "wins, it indicates the base models are diverse enough for estimation to "
     "pay. Section 7.6 reports which occurred."),

    ("h2", "5.8 Uncertainty and Explainability Design"),
    ("p",
     "The conformal layer takes the absolute out-of-fold residuals for a model, "
     "sorts them, and takes the empirical quantile at the level implied by the "
     "target coverage with the finite-sample correction that split-conformal "
     "theory requires [39], [40]. That single scalar becomes the interval "
     "half-width, applied symmetrically about the point forecast. The design is "
     "intentionally the simplest conformal variant: locally adaptive variants "
     "that widen the interval in hard regions require a second model to predict "
     "residual magnitude, and with twenty-eight calibration points such a model "
     "could not be fitted responsibly."),
    ("p",
     "The explanation layer uses SHAP TreeExplainer [19] on the best-performing "
     "tree model. Two artefacts are produced: a global ranking of mean absolute "
     "attribution across all records, which answers which predictors matter in "
     "general, and per-prediction attributions computed on demand at serving "
     "time, which answer why this particular forecast came out as it did. The "
     "second is what an agricultural officer actually needs, and it is why the "
     "explainer is loaded into the serving process rather than only run in the "
     "analysis pipeline."),

    ("h2", "5.9 Serving and Dashboard Design"),
    ("p",
     "The serving layer is designed around one rule: it never trains. It loads "
     "the persisted models and artefacts at start-up and thereafter only reads. "
     "This makes it stateless with respect to learning, which means it can be "
     "restarted freely, and it means a retraining run cannot corrupt a running "
     "service. Requests are validated against the expected predictor schema "
     "before reaching a model, and the feature vector is assembled in the exact "
     "column order used at training time, since a silent column reordering "
     "would produce plausible-looking but meaningless forecasts."),
    ("p",
     "Every response carries a provenance record naming the model that produced "
     "the forecast and the dataset variant it was trained on. This was added "
     "after an early integration problem in which dashboard figures could not "
     "be traced back to a pipeline run; making provenance part of the response "
     "contract removes the ambiguity permanently."),
    ("p",
     "The logical structure of the persisted data store is shown in Figure 5.3. "
     "The processed dataset is keyed on district, season and year; the "
     "out-of-fold prediction records share that key and add a model dimension; "
     "the comparison, calibration and attribution artefacts are keyed on model "
     "alone."),
    ("fig", (f"{FIGDIR}/figure_5_3_database_schema.png",
             "Figure 5.3: Logical data schema of the processed store")),
    ("p",
     "The dashboard is organised around the four user groups of Table 4.1. The "
     "overview presents national and district key figures with a choropleth "
     "map. The prediction view presents the context-prefilled form and the "
     "forecast with its interval. The explainability view presents the global "
     "attribution ranking and the symbolic equation. The recommendation view "
     "translates the forecast and its drivers into plain-language guidance. An "
     "administrative view presents the full model comparison for technical "
     "users. Internationalisation is included because the intended district-"
     "level users do not all work in English."),

    ("h2", "5.10 Summary"),
    ("p",
     "This chapter presented the internal design of every module. The data flow "
     "resolves grain, key and seasonal-boundary mismatches through file-"
     "mediated stages. Thirty-two predictors were designed across five groups "
     "with stated agronomic rationale, and a parallel sequential representation "
     "supports the deep models. The nine-model inventory was justified member "
     "by member, with detailed treatment of the hybrid CNN-LSTM's "
     "season-indicator injection and the physics-residual hybrid's mechanistic "
     "backbone. The stacking layer's three constraints, the conformal and SHAP "
     "designs, and the serving and dashboard structures were specified. The "
     "next chapter documents how this design was implemented."),
]


# ============================================================================
# Chapter 6 — Implementation
# ============================================================================

CHAPTER_6 = [
    ("chapter", ("6", "Implementation")),

    ("h2", "6.1 Introduction"),
    ("p",
     "Chapter 5 specified the design of each module. This chapter documents how "
     "that design was realised in software: the repository structure and "
     "tooling, then each module in turn, stating the algorithms, the "
     "configuration and the key implementation decisions. The correspondence "
     "between design modules and source files is maintained deliberately, so "
     "that a reader can move from a design section to the code that implements "
     "it without searching. Extended code excerpts appear in Appendix B."),

    ("h2", "6.2 Repository Layout and Tooling"),
    ("p",
     "The implementation is a Python package under a source directory, a "
     "single-entry orchestration script, a dashboard application, and separated "
     "directories for data and outputs. Table 6.1 maps each design module onto "
     "the file that implements it."),
    ("table", (
        ["Design module", "Source file", "Responsibility"],
        [
            ["Configuration", "src/config.py", "All hyperparameters, paths, feature groups, seeds"],
            ["Data acquisition", "src/data_loader.py", "Load sources, apply season window, reconcile keys"],
            ["Preprocessing", "src/preprocessor.py", "Validation, imputation, encoding"],
            ["Feature engineering", "src/feature_engineer.py", "Build the 32 predictors and sequences"],
            ["Exploratory analysis", "src/eda.py", "Distribution, correlation and seasonal plots"],
            ["Classical models", "src/ml_models.py", "RF, XGBoost, SVR under LOYO-CV"],
            ["Deep models", "src/dl_models.py", "LSTM, BiLSTM, 1D-CNN, hybrid CNN-LSTM"],
            ["Symbolic regression", "src/symbolic.py", "Genetic-programming equation search"],
            ["Physics-residual", "src/physics_residual.py", "Mechanistic backbone + residual learner"],
            ["Stacking", "src/stacking.py", "Three combiners on out-of-fold predictions"],
            ["Conformal", "src/conformal.py", "Split-conformal residual quantiles"],
            ["Explainability", "src/explainer.py", "SHAP TreeExplainer attributions"],
            ["Ablation", "src/ablation.py", "Six data-source configurations"],
            ["Evaluation", "src/evaluator.py", "Metrics, significance tests, final comparison"],
            ["Serving", "src/api.py", "REST endpoints over the persisted artefacts"],
            ["Orchestration", "main.py", "Stage sequencing and command-line flags"],
            ["Presentation", "dashboard/", "Next.js decision-support application"],
        ],
        "Table 6.1: Pipeline modules and their source files",
    )),
    ("p",
     "Two implementation conventions run through the whole codebase. The first "
     "is that all tunable quantities live in the configuration module and "
     "nowhere else, so that no hyperparameter is buried in a model file. The "
     "second is that the choice of dataset variant — the real collected data "
     "or the synthetic reference — is made through a single environment "
     "variable read at configuration time, which redirects every output path. "
     "The two variants therefore write to entirely separate directories and "
     "cannot contaminate each other, which is what allows synthetic "
     "architecture validation and real-data evaluation to coexist in one "
     "repository without ambiguity."),
    ("p",
     "The orchestration script exposes a flag per stage, so that during "
     "development an expensive stage can be skipped without editing code. A "
     "full real-data run is invoked with a single real-data flag and completes "
     "in approximately six minutes on a laptop."),

    ("h2", "6.3 Data Loading and Preprocessing"),
    ("p",
     "The loader reads the collected source files, each of which arrives on its "
     "own grain, and reduces them to the common key. Daily weather rows are "
     "filtered to the season month window and aggregated: means for state "
     "variables, sums for fluxes, counts for threshold-crossing events. "
     "Composite-period vegetation index rows are filtered to the same window "
     "and reduced to the mean, maximum, minimum, standard deviation and derived "
     "timing statistics. Soil properties, being static, are joined directly on "
     "district."),
    ("p",
     "The Maha boundary is handled by defining the season as an explicit month "
     "list and attributing a Maha record to its starting year, so that a season "
     "spanning the calendar boundary remains one record. District names are "
     "normalised against the canonical vocabulary in configuration at load "
     "time; a name that fails to map raises rather than silently dropping the "
     "row, because a silent drop would produce a smaller dataset with no "
     "indication that anything went wrong."),
    ("p",
     "Preprocessing validates each predictor against a plausible range, imputes "
     "the small number of remaining gaps by district median, and encodes the "
     "categorical fields. The season indicator is encoded as a binary variable "
     "and retained as a modelling feature rather than used only for grouping, "
     "because the deep architecture consumes it directly at its dense head."),
    ("p",
     "A synthetic generator is retained alongside the real loader. It produces "
     "a dataset calibrated to published district yield ranges and to the "
     "correlation structure expected between weather, vegetation indices and "
     "yield, from a fixed seed. Its role is strictly to validate that the "
     "pipeline and the model architectures function correctly end to end at a "
     "sample size where they can be expected to; it is never mixed with real "
     "data, and every number derived from it is labelled as such."),

    ("h2", "6.4 Feature Engineering"),
    ("p",
     "The feature engineering module builds the thirty-two predictors of Table "
     "5.1 and, in the same pass, the sequential representation the deep models "
     "require. Growing degree days accumulate the daily mean above the base "
     "temperature over the season window; heat stress days count exceedances of "
     "the critical maximum; the standardised precipitation index standardises "
     "seasonal rainfall against the district's own historical distribution."),
    ("p",
     "Yield-history predictors require care to avoid leakage. The previous "
     "season's yield, the previous year's yield and the three-year moving "
     "average are all computed by shifting within the district group so that a "
     "record's history contains only strictly earlier records. An unshifted "
     "rolling average would include the record's own target and would produce "
     "spectacular and entirely fictitious accuracy."),
    ("p",
     "The module returns four objects: the tabular predictor matrix, the target "
     "vector, the ordered feature-name list, and the sequential payload for the "
     "deep models. The feature-name list is not incidental — it is persisted "
     "and used by the serving layer to assemble incoming payloads in the exact "
     "training column order."),

    ("h2", "6.5 Classical Model Implementation"),
    ("p",
     "The classical trainer implements the nested cross-validation directly "
     "rather than relying on a library convenience wrapper, because the outer "
     "grouping is by year while the inner search must respect temporal order "
     "within the training partition. The outer loop iterates over the distinct "
     "years; for each, all records of that year form the test partition and the "
     "remainder the training partition. Within the training partition an inner "
     "grid search using a time-series split selects hyperparameters. The "
     "selected configuration is refitted on the full training partition and "
     "used to predict the held-out year."),
    ("p",
     "Reduced hyperparameter grids are used inside the inner loop, with the "
     "full grids reserved for the final refit. This is a runtime decision: the "
     "full grid inside a nested loop over every year would multiply training "
     "time by an order of magnitude for a selection that the reduced grid "
     "reaches in almost all folds."),
    ("p",
     "Every model writes an out-of-fold prediction record containing, for each "
     "row, the year, season, district, actual and predicted values. These "
     "records are the substrate for everything downstream — the significance "
     "tests, the stacking layer, the conformal calibration and the per-district "
     "analysis all read them rather than re-running the models."),

    ("h2", "6.6 Deep Model Implementation"),
    ("p",
     "The four networks are built with the Keras functional interface, which is "
     "required for the hybrid because it has two inputs. Each is trained under "
     "the same outer cross-validation as the classical models, with a "
     "validation split carved from the training partition for early stopping. "
     "Weights are reinitialised at the start of every fold; carrying weights "
     "across folds would leak information from previously held-out years into "
     "later ones."),
    ("p",
     "The hybrid's implementation follows the design of section 5.5 exactly: a "
     "convolutional stack over the vegetation input, a recurrent stack over the "
     "weather input, both reduced to fixed-length vectors, and then "
     "concatenation with the scalar season indicator before the dense head. "
     "Epoch count is capped during small-data runs, since with a training "
     "partition of two dozen records the networks reach their early-stopping "
     "criterion long before the nominal maximum."),
    ("p",
     "Figure 6.1 shows the training curve of the hybrid on the collected data. "
     "The behaviour it displays is itself a finding: the validation loss "
     "separates from the training loss early and does not recover, which is the "
     "signature of a model with more capacity than the sample can constrain. "
     "This is consistent with the quantitative outcome reported in section 7.4."),
    ("fig", (f"{REAL}/training/cnn_lstm_learning_curve.png",
             "Figure 6.1: Training curve of the hybrid CNN-LSTM on the collected data")),

    ("h2", "6.7 Symbolic Regression Implementation"),
    ("p",
     "The symbolic regression module runs a genetic-programming search [34] "
     "over expression trees. The search is restricted in three ways, all of "
     "which are necessary at this sample size. The predictor set is limited to "
     "the five ranked highest by SHAP; the function set is limited to addition, "
     "subtraction, multiplication, protected division and square root; and the "
     "fitness function includes a parsimony penalty on expression length. "
     "Without these restrictions the search reliably produces an expression "
     "that interpolates the training points and has no predictive content."),
    ("p",
     "The module writes both the raw evolved program, in terms of indexed "
     "variables, and a rendered form with the variable indices substituted by "
     "predictor names, along with the metrics achieved under the same "
     "cross-validation protocol as every other model. The rendered equation is "
     "served through a dedicated endpoint so the dashboard can display it."),

    ("h2", "6.8 Physics-Residual Implementation"),
    ("p",
     "The physics-residual module implements the two-stage design of section "
     "5.6. The backbone is a pure function of the predictor matrix with no "
     "fitted internal state: it computes the thermal, water and heat factors "
     "from growing degree days, the standardised precipitation index and heat "
     "stress days respectively, using the constants drawn from the agronomic "
     "literature [31], [32], and multiplies them into the suitability term."),
    ("p",
     "The affine calibration and the residual forest are both fitted inside "
     "every outer fold on the training partition only. The module additionally "
     "evaluates and persists the backbone in isolation, without the residual "
     "learner, so that the contribution of each stage can be separated. It also "
     "records the plain Random Forest score from the classical stage, which "
     "gives the with-and-without-backbone comparison reported in section 7.5. "
     "That three-way comparison — backbone alone, learner alone, and the hybrid "
     "— is the ablation that establishes whether the mechanistic prior earns "
     "its place."),
    ("p",
     "One implementation observation is recorded in the module's own output and "
     "is worth stating here: the heat stress day count is zero throughout the "
     "collected data, so the heat factor is inert and the backbone's signal "
     "comes entirely from thermal time and water. This does not invalidate the "
     "formulation — the factor would activate in a hotter season — but it means "
     "the measured benefit is attributable to two of the three components."),

    ("h2", "6.9 Stacking, Conformal and SHAP Implementation"),
    ("p",
     "The stacking module reads every base model's out-of-fold prediction "
     "record, aligns them on the district-season-year key, and fits the three "
     "combiners under a nested protocol in which the weights are estimated on "
     "training years only and applied to the held-out year. The convex "
     "combiner solves a constrained least-squares problem on the simplex; the "
     "inverse-RMSE combiner normalises reciprocal validation errors; the mean "
     "combiner assigns equal weights. All three write their own out-of-fold "
     "records in the same format as a base model, so they enter the final "
     "comparison on identical terms."),
    ("p",
     "The conformal module reads the out-of-fold records, computes absolute "
     "residuals, and takes the corrected empirical quantile at the level "
     "implied by the target coverage. It persists, per model, the quantile, the "
     "target and empirical coverage, and the calibration set size — the last of "
     "these being essential context for interpreting the coverage figure, as "
     "section 7.10 discusses."),
    ("p",
     "The explainability module runs SHAP TreeExplainer [19] on the best tree "
     "model, persists the ranked mean absolute attributions, and generates the "
     "summary, importance and dependence plots. It is run before the final "
     "comparison stage so that the summary of findings can name the top "
     "predictors, and its output feeds both the symbolic regression predictor "
     "selection and the dashboard's explainability view."),

    ("h2", "6.10 Ablation Study Implementation"),
    ("p",
     "The ablation module re-runs the complete evaluation protocol under six "
     "predictor configurations: weather only, satellite only, historical only, "
     "soil only, weather combined with satellite, and all sources. Each "
     "configuration is a strict subset of the full predictor list defined in "
     "configuration, so the experiment isolates the data source and holds "
     "everything else — model, protocol, seed — fixed. Results are written to a "
     "comparison table and a bar chart, and are reported in section 7.8."),

    ("h2", "6.11 Serving Layer and Dashboard"),
    ("p",
     "The serving layer loads the persisted models and artefacts at start-up "
     "and exposes the endpoints of Table 6.2. It performs no training and holds "
     "no mutable state beyond its loaded artefacts."),
    ("table", (
        ["Endpoint", "Method", "Purpose"],
        [
            ["/health", "GET", "Liveness check and loaded-artefact inventory"],
            ["/predict", "POST", "Point forecast, conformal interval, SHAP attribution, provenance"],
            ["/models/compare", "GET", "Full model comparison table"],
            ["/feature-importance", "GET", "Ranked global SHAP attributions"],
            ["/equation", "GET", "Rendered symbolic regression equation"],
            ["/context", "GET", "Prefill predictor values for a district, season and year"],
            ["/baseline", "GET", "Historical baseline yield for comparison"],
            ["/districts", "GET", "Districts, seasons and years available for selection"],
        ],
        "Table 6.2: REST endpoints exposed by the serving layer",
    )),
    ("p",
     "The prediction endpoint is the only one that computes. It validates the "
     "payload against the persisted feature-name list, assembles the vector in "
     "training column order, invokes the model, looks up the conformal "
     "half-width, computes the per-record SHAP attribution, and returns all of "
     "it with a provenance block naming the model and dataset variant."),
    ("p",
     "The dashboard is a Next.js application with locale-aware routing, "
     "consuming only these endpoints. Its views correspond to the user groups "
     "of Table 4.1: an overview with the district choropleth, a prediction form "
     "with context prefill, an explainability view showing attributions and the "
     "symbolic equation, and a recommendation view that renders the forecast "
     "and its drivers as plain-language guidance. Screenshots appear in "
     "Appendix D."),

    ("h2", "6.12 Summary"),
    ("p",
     "This chapter documented the implementation module by module, maintaining "
     "an explicit correspondence between design sections and source files. The "
     "central implementation concerns were preventing leakage — through shifted "
     "history features, per-fold refitting of every fitted quantity including "
     "the mechanistic calibration, and weight reinitialisation between folds — "
     "and maintaining strict separation between the real and synthetic dataset "
     "variants. The next chapter reports what the implemented system achieves "
     "when evaluated."),
]


# ============================================================================
# Chapter 7 — Evaluation and Results
# ============================================================================

CHAPTER_7 = [
    ("chapter", ("7", "Evaluation and Results")),

    ("h2", "7.1 Introduction"),
    ("p",
     "Chapter 6 documented the implemented system. This chapter reports what it "
     "achieves. It first characterises the dataset that was actually collected, "
     "because every result that follows must be read against its size. It then "
     "states the evaluation protocol and metrics, reports the model comparison, "
     "and answers the two design questions posed in Chapter 5: whether the "
     "mechanistic backbone earns its place, and whether stacking helps. It then "
     "reports the symbolic equation, the data-source ablation, per-district "
     "behaviour, calibrated uncertainty and feature attribution, and closes "
     "with the synthetic-data run that validates the architecture "
     "independently of the small-sample question."),
    ("p",
     "Results in sections 7.2 through 7.11 come exclusively from the real "
     "collected dataset. Section 7.12 alone reports synthetic-data numbers, and "
     "labels them as such throughout. The two are never mixed."),

    ("h2", "7.2 The Evaluation Dataset"),
    ("p",
     "The collected dataset contains twenty-eight seasonal records: four "
     "districts observed over seven consecutive years, all in the Yala season. "
     "Table 7.1 gives its composition and the distribution of the target."),
    ("table", (
        ["Property", "Value"],
        [
            ["Records", "28"],
            ["Districts", "Anuradhapura, Kurunegala, Matale, Polonnaruwa"],
            ["Years", "2019–2025 (7 years)"],
            ["Seasons", "Yala only"],
            ["Records per district", "7"],
            ["Records per year", "4"],
            ["Predictors engineered", "32"],
            ["Target mean", "16.39 MT/Ha"],
            ["Target standard deviation", "4.17 MT/Ha"],
            ["Target range", "8.50 – 24.06 MT/Ha"],
            ["District means", "Anuradhapura 18.11, Matale 16.63, Polonnaruwa 16.11, Kurunegala 14.70"],
        ],
        "Table 7.1: Composition of the collected evaluation dataset",
    )),
    ("p",
     "Three properties of this dataset govern the interpretation of everything "
     "that follows, and it is more useful to state them plainly at the outset "
     "than to discover them in the discussion."),
    ("p",
     "First, twenty-eight records against thirty-two predictors is a regime in "
     "which the number of candidate explanatory variables exceeds the number of "
     "observations. No learning algorithm can reliably identify which "
     "predictors matter under that ratio. This is not a defect in the "
     "modelling; it is a property of what data exists for this crop, and it is "
     "precisely the condition the project set out to work within rather than to "
     "wish away."),
    ("p",
     "Second, the collected record covers only the Yala season. The Maha season "
     "is represented in the system design, in the feature set and in the "
     "synthetic reference run, but not in the collected data. Consequently the "
     "hybrid CNN-LSTM's season-indicator injection — designed specifically for "
     "the bimodal structure — cannot be evaluated on real data, because the "
     "indicator is constant across every real record. Its architectural claim "
     "is therefore tested only on the synthetic reference in section 7.12, and "
     "this limitation is restated in section 8.5."),
    ("p",
     "Third, with seven years the Leave-One-Year-Out protocol produces seven "
     "folds of four records each. Each fold's training partition holds "
     "twenty-four records. Any model that requires more than a couple of dozen "
     "effective observations to fit its parameters is being asked to do "
     "something the data cannot support, and the results reflect that."),

    ("h2", "7.3 Evaluation Protocol and Metrics"),
    ("p",
     "Every model reported here was evaluated identically. The outer loop holds "
     "out one year at a time; hyperparameters are chosen by an inner "
     "time-series-aware search on the training partition; the selected "
     "configuration is refitted and used to predict the held-out year. Every "
     "fitted quantity — including the physics-residual model's affine "
     "calibration and the stacking layer's weights — is estimated inside the "
     "fold. The reported metrics are computed on the pooled out-of-fold "
     "predictions, so every one of the twenty-eight records contributes a "
     "prediction made by a model that never saw it."),
    ("p",
     "Four metrics are reported. Root mean squared error is in the units of the "
     "target and penalises large errors quadratically, which matters because a "
     "large error in an import-planning forecast is disproportionately costly. "
     "Mean absolute error is in the same units and is more interpretable as a "
     "typical miss. The coefficient of determination expresses the fraction of "
     "target variance explained relative to a constant-mean predictor; it is "
     "negative when a model performs worse than simply predicting the mean, "
     "which is a meaningful and frequently occurring outcome at this sample "
     "size. Mean absolute percentage error normalises the miss against the "
     "actual value."),
    ("p",
     "Model pairs are compared with the Wilcoxon signed-rank test on paired "
     "per-record absolute residuals, so that the comparison accounts for the "
     "fact that the same records are predicted by every model."),

    ("h2", "7.4 Model Comparison Results"),
    ("p",
     "Table 7.2 reports every model under the shared protocol, ordered by root "
     "mean squared error. Figure 7.1 presents the same comparison graphically."),
    ("table", (
        ["Model", "RMSE", "MAE", "R²", "MAPE (%)", "Train time (s)", "Parameters"],
        [
            ["PhysResidual", "3.9021", "3.3497", "0.0908", "23.32", "1.01", "—"],
            ["RandomForest", "4.0506", "3.3932", "0.0203", "23.44", "2.89", "—"],
            ["XGBoost", "4.0677", "3.4392", "0.0120", "23.76", "1.76", "—"],
            ["SVR", "4.1684", "3.4836", "−0.0375", "24.55", "0.03", "—"],
            ["StackConvex", "4.3237", "3.6222", "−0.1162", "24.36", "0.00", "—"],
            ["StackInvRMSE", "4.3261", "3.6694", "−0.1175", "23.28", "0.00", "—"],
            ["BiLSTM", "4.5186", "3.6261", "−0.2192", "23.33", "31.66", "77,601"],
            ["SymbolicRegression", "4.5823", "3.9126", "−0.2538", "27.19", "35.66", "—"],
            ["StackMean", "5.0621", "4.2961", "−0.5301", "25.39", "0.00", "—"],
            ["LSTM", "7.3132", "5.7093", "−2.1935", "33.30", "23.31", "30,625"],
            ["CNN_LSTM_Hybrid", "11.6126", "10.8517", "−7.0521", "64.47", "29.55", "44,929"],
            ["CNN", "11.6973", "10.7711", "−7.1700", "62.91", "19.24", "8,577"],
        ],
        "Table 7.2: Model comparison under Leave-One-Year-Out cross-validation",
    )),
    ("fig", (f"{REAL}/results/model_comparison_bar.png",
             "Figure 7.1: Model comparison on the collected dataset")),
    ("p",
     "The physics-residual hybrid is the strongest model, with a root mean "
     "squared error of 3.90 metric tons per hectare, a mean absolute error of "
     "3.35, a coefficient of determination of 0.091 and a mean absolute "
     "percentage error of 23.3 per cent. Random Forest follows at 4.05 and "
     "0.020, then XGBoost at 4.07 and 0.012. Support Vector Regression is "
     "marginally below the mean predictor at −0.038."),
    ("p",
     "These figures must be reported for what they are. An R² of 0.091 means "
     "the best model explains about nine per cent of the variance in district "
     "yield. The project set a target of 0.75 at proposal stage, and on the "
     "collected data that target is not met. Section 8.2 discusses at length "
     "why this is the expected outcome at twenty-eight records rather than a "
     "failure of the implementation, and section 7.12 demonstrates that the "
     "same code reaches 0.842 when the sample is adequate."),
    ("p",
     "The ordering of the model families is the more informative result. Every "
     "deep architecture falls below the constant-mean predictor, and the two "
     "convolutional models fail catastrophically, with coefficients of "
     "determination near −7 and mean absolute percentage errors above sixty per "
     "cent. The Wilcoxon signed-rank test on paired absolute residuals rejects "
     "the hypothesis that the deep family matches the classical family, with a "
     "p-value below 0.0001. The hybrid CNN-LSTM does not beat its standalone "
     "components; it sits between the CNN and the LSTM, and all three are far "
     "behind the tree ensembles."),
    ("p",
     "This is a negative result, and it is one of the project's substantive "
     "findings rather than an embarrassment to be minimised. The published "
     "literature that motivates hybrid deep architectures for yield prediction "
     "[8], [2] validates them at sample sizes three orders of magnitude larger. "
     "What Table 7.2 establishes is that the architectural advantage does not "
     "survive the reduction: at twenty-eight records, capacity is a liability "
     "and the correct choice for a practitioner in this position is a "
     "regularised classical learner, ideally one carrying a mechanistic prior. "
     "That is actionable guidance which the existing literature does not "
     "supply, and it answers Gap 2 of section 2.8 directly."),
    ("p",
     "Figures 7.2 and 7.3 show the actual-against-predicted scatter and the "
     "residual distribution for Random Forest, the best purely learned model. "
     "The scatter shows the characteristic regression-to-the-mean compression "
     "of a model working with weak signal: predictions cluster in a narrower "
     "band than the actuals, so high-yield records are under-predicted and "
     "low-yield records over-predicted. The residual distribution is centred "
     "near zero without pronounced skew, which indicates the errors are noise "
     "rather than systematic bias — the model is not wrong in a fixable "
     "direction, it is simply short of signal."),
    ("fig", (f"{REAL}/results/actual_vs_pred_rf.png",
             "Figure 7.2: Actual against predicted yield, Random Forest")),
    ("fig", (f"{REAL}/results/residuals_rf.png",
             "Figure 7.3: Residual distribution, Random Forest")),

    ("h2", "7.5 Does the Mechanistic Backbone Help?"),
    ("p",
     "Section 5.6 argued that supplying established agronomy rather than "
     "learning it should pay at this sample size. Table 7.3 tests that argument "
     "by separating the two stages of the physics-residual hybrid."),
    ("table", (
        ["Configuration", "RMSE", "MAE", "R²", "MAPE (%)"],
        [
            ["Mechanistic backbone alone (no learner)", "4.5241", "3.6576", "−0.2221", "25.13"],
            ["Random Forest alone (no backbone)", "4.0506", "3.3932", "0.0203", "23.44"],
            ["Physics-residual hybrid (backbone + learner)", "3.9021", "3.3497", "0.0908", "23.32"],
        ],
        "Table 7.3: Physics-residual with and without the mechanistic backbone",
    )),
    ("p",
     "The result is unambiguous in direction. The backbone alone is worse than "
     "predicting the mean, at −0.222, which is expected: a three-factor "
     "closed-form suitability function calibrated by two parameters cannot "
     "capture district-level yield on its own. The learner alone reaches 0.020. "
     "The combination reaches 0.091. Adding the mechanistic prior to the "
     "Random Forest improves the coefficient of determination by 0.070 and "
     "reduces root mean squared error by 0.15 metric tons per hectare, a "
     "relative error reduction of 3.7 per cent."),
    ("p",
     "The mechanism is worth stating precisely, because the improvement is not "
     "explained by the backbone being accurate. It is explained by the backbone "
     "changing what the learner has to do. Without it, the forest must discover "
     "the water-limitation and thermal-time relationships from twenty-four "
     "training records while simultaneously fitting everything else. With it, "
     "those relationships are supplied a priori from FAO-33 [31] and the "
     "standard degree-day formulation [32], and the forest's entire capacity is "
     "directed at the residual. In a sample-starved regime, a prior that is "
     "merely approximately right is worth more than the degrees of freedom it "
     "saves. This is the same logic Shahhosseini et al. [33] demonstrated with "
     "a full crop simulator, reproduced here with a closed-form backbone that "
     "costs three lines of arithmetic."),
    ("p",
     "One caveat is recorded honestly. The heat-stress-day count is zero "
     "throughout the collected Yala data, so the heat factor is inert and the "
     "measured benefit comes from the thermal-time and water components only. "
     "The heat factor would engage in a hotter season, but on this data it "
     "contributes nothing, and the improvement should be attributed to two of "
     "the three mechanistic components rather than all three."),

    ("h2", "7.6 Does Stacking Help?"),
    ("p",
     "Section 5.7 posed the forecast-combination question: does an estimated "
     "weighting beat a simple average, or does the well-documented "
     "forecast-combination puzzle [37], [38] hold here? Table 7.4 reports the "
     "three combiners and the weights the convex fit assigned."),
    ("table", (
        ["Combiner", "RMSE", "MAE", "R²", "Weighting rule"],
        [
            ["StackConvex", "4.3237", "3.6222", "−0.1162", "Least squares on the simplex"],
            ["StackInvRMSE", "4.3261", "3.6694", "−0.1175", "Proportional to inverse validation RMSE"],
            ["StackMean", "5.0621", "4.2961", "−0.5301", "Equal weights across all nine base models"],
        ],
        "Table 7.4: Stacking combiners and their learned weights",
    )),
    ("p",
     "Two findings follow. The first concerns the puzzle itself. The learned "
     "convex blend, at −0.116, clearly outperforms the equal-weight mean at "
     "−0.530. The forecast-combination puzzle does not hold in this setting. "
     "The explanation is visible in Table 7.2: the base pool contains models "
     "whose errors differ by a factor of three, and equal weighting therefore "
     "spends a ninth of its mass on each of the two convolutional models that "
     "score below −7. When base learners are of grossly unequal quality, even a "
     "crudely estimated weighting beats uniform averaging, because the "
     "estimation error the puzzle warns about is smaller than the error "
     "introduced by weighting a broken model equally with a good one."),
    ("p",
     "The convex fit allocated 0.399 to the physics-residual hybrid, 0.271 to "
     "XGBoost, 0.199 to the BiLSTM, 0.045 to Random Forest, 0.039 to Support "
     "Vector Regression, 0.027 to the symbolic model, 0.015 to the LSTM, 0.005 "
     "to the hybrid CNN-LSTM, and exactly zero to the CNN. The optimiser "
     "eliminated the worst model entirely and concentrated on the physics-"
     "residual hybrid — which is an independent confirmation of the section 7.5 "
     "result, arrived at by a completely different route. The non-trivial "
     "weight on the BiLSTM is also informative: although that model scores "
     "poorly alone, its errors are evidently decorrelated enough from the tree "
     "models to earn a place in the blend."),
    ("p",
     "The second finding is the one that matters for deployment. Every "
     "combiner, including the best, is worse than the single physics-residual "
     "hybrid at 0.091. Stacking does not help here. This is consistent with the "
     "sample-size argument that runs through the whole evaluation: the "
     "meta-learner must estimate a nine-dimensional weight vector from "
     "twenty-eight out-of-fold predictions, and even constrained to the simplex "
     "that estimation costs more than the diversification gains. The system "
     "therefore serves the physics-residual hybrid, not the stack. Reporting "
     "the stacking result as a negative finding, rather than quietly dropping "
     "it, is what allows the next researcher to know that this avenue was "
     "tested."),

    ("h2", "7.7 The Symbolic Equation"),
    ("p",
     "The genetic-programming search over the five highest-attribution "
     "predictors converged on the following closed-form expression for average "
     "yield in metric tons per hectare:"),
    ("code",
     "Yield  =  ( temp_x_humidity  x  prev_year_yield ) ^ (1/4)\n"
     "                +  3.251\n"
     "                -  drought_index_spi"),
    ("p",
     "Under the same cross-validation protocol this equation scores a root mean "
     "squared error of 4.58, a coefficient of determination of −0.254 and a "
     "mean absolute percentage error of 27.2 per cent. It is not competitive as "
     "a predictor, and it is not served as one."),
    ("p",
     "Its value is diagnostic and communicative. Structurally, the equation "
     "says three things that are agronomically sensible. Yield increases with "
     "the product of the temperature-humidity term and the previous year's "
     "yield, compressed through a fourth root — that is, it increases with "
     "favourable growing conditions combined with a district's demonstrated "
     "productivity, with strongly diminishing returns. Yield decreases with the "
     "drought index term. And a constant offset near 3.25 sets the baseline. "
     "That the evolutionary search, given free rein over expression structure, "
     "independently arrived at a form in which district history and moisture "
     "availability are the load-bearing terms corroborates the SHAP ranking of "
     "section 7.11, which was computed by an entirely unrelated method."),
    ("p",
     "For a district agricultural officer, an equation that can be read and "
     "checked against experience has a credibility that a forest of two hundred "
     "trees does not, even when the forest is more accurate. The equation is "
     "therefore served through its own endpoint and displayed in the "
     "explainability view alongside — never instead of — the point forecast "
     "from the deployed model."),

    ("h2", "7.8 Data-Source Ablation"),
    ("p",
     "The ablation study re-runs the full protocol under six predictor "
     "configurations, holding model, protocol and seed fixed so that only the "
     "data source varies. Table 7.5 and Figure 7.4 report the outcome."),
    ("table", (
        ["Configuration", "Predictors", "RMSE", "MAE", "R²"],
        [
            ["A — Weather only", "9", "5.4972", "4.6080", "−0.8044"],
            ["B — Satellite only", "11", "5.2825", "4.3860", "−0.6662"],
            ["C — Historical only", "5", "5.6024", "4.5058", "−0.8741"],
            ["D — Soil only", "4", "4.5877", "3.5251", "−0.2567"],
            ["E — Weather + Satellite", "20", "5.6643", "4.8029", "−0.9158"],
            ["F — All sources", "32", "4.2567", "3.5314", "−0.0819"],
        ],
        "Table 7.5: Data-source ablation results",
    )),
    ("fig", (f"{REAL}/results/ablation_comparison.png",
             "Figure 7.4: Data-source ablation on the collected dataset")),
    ("p",
     "Every single-source configuration performs worse than the constant-mean "
     "predictor, and the full configuration at −0.082 is the best of the six. "
     "The primary conclusion is therefore that no individual data stream "
     "carries the signal on its own at this sample size; only the combination "
     "approaches parity with the mean, and even then does not exceed it."),
    ("p",
     "Two secondary observations deserve comment. Soil alone, at −0.257, is the "
     "strongest single source despite having only four predictors, all of them "
     "static per district. This is almost certainly not a finding about soil "
     "science. Static per-district predictors act as a district identifier, and "
     "since districts differ systematically in mean yield — from 14.70 in "
     "Kurunegala to 18.11 in Anuradhapura — a model given only soil is "
     "effectively fitting district means. That is a real signal, but it is a "
     "baseline effect, not a soil effect, and it is important to say so rather "
     "than to report a spurious agronomic conclusion."),
    ("p",
     "The second observation is that combining weather with satellite, at "
     "−0.916, is worse than either alone. With twenty predictors and "
     "twenty-four training records per fold, adding features adds variance "
     "faster than it adds information. This is a textbook manifestation of the "
     "curse of dimensionality, made visible by the controlled design of the "
     "experiment, and it is direct evidence for the sample-size argument that "
     "the whole chapter has been building."),
    ("p",
     "For contrast, section 7.12 reports the same six experiments on the "
     "synthetic reference, where the sample is adequate. There the ordering is "
     "entirely different and interpretable: satellite alone reaches 0.802 and "
     "the full configuration 0.829. The comparison between the two ablation "
     "tables is itself an argument that what limits the real-data result is the "
     "sample, not the feature design."),

    ("h2", "7.9 Per-District Behaviour"),
    ("p",
     "Table 7.6 decomposes the physics-residual hybrid's out-of-fold errors by "
     "district."),
    ("table", (
        ["District", "n", "Mean actual (MT/Ha)", "RMSE", "MAE", "R²"],
        [
            ["Anuradhapura", "7", "18.11", "2.718", "2.176", "0.361"],
            ["Polonnaruwa", "7", "16.11", "3.828", "3.301", "0.220"],
            ["Matale", "7", "16.63", "4.779", "4.381", "0.023"],
            ["Kurunegala", "7", "14.70", "4.002", "3.540", "−1.183"],
        ],
        "Table 7.6: Per-district predictability",
    )),
    ("p",
     "Anuradhapura is the most predictable district at 0.361, and it is also "
     "the largest and most established big onion producing district, with the "
     "highest mean yield. Polonnaruwa follows at 0.220. Matale is essentially "
     "at the mean predictor. Kurunegala is much worse than the mean at −1.183, "
     "despite having a root mean squared error of 4.00 that is lower than "
     "Matale's 4.78."),
    ("p",
     "That apparent contradiction is instructive and should not be passed over. "
     "The coefficient of determination is normalised by each district's own "
     "target variance. Kurunegala has the lowest mean yield and the narrowest "
     "spread of the four, so a moderate absolute error consumes a large "
     "fraction of a small variance and produces a strongly negative score. "
     "Matale has a wider spread, so a larger absolute error still leaves the "
     "ratio near one. For an operational user the absolute error is the "
     "relevant quantity, and by that measure Kurunegala is predicted better "
     "than Matale. Reporting only the coefficient of determination would have "
     "given the opposite and misleading impression, which is why both are in "
     "the table."),
    ("p",
     "The practical implication is that a deployed system should not present a "
     "single national confidence statement. Anuradhapura forecasts warrant more "
     "weight than Matale forecasts, and the dashboard's per-district intervals "
     "are the mechanism by which that difference is communicated."),

    ("h2", "7.10 Calibrated Uncertainty"),
    ("p",
     "Split-conformal calibration [39], [40] was applied to the out-of-fold "
     "residuals of every model at a nominal ninety per cent coverage level. "
     "Table 7.7 reports the resulting interval half-widths."),
    ("table", (
        ["Model", "Half-width q (MT/Ha)", "Target coverage", "Empirical coverage", "Calibration n"],
        [
            ["PhysResidual", "6.852", "0.90", "1.00", "28"],
            ["RandomForest", "7.451", "0.90", "1.00", "28"],
            ["StackConvex", "7.799", "0.90", "1.00", "28"],
            ["SVR", "7.967", "0.90", "1.00", "28"],
            ["XGBoost", "8.025", "0.90", "1.00", "28"],
            ["StackInvRMSE", "8.077", "0.90", "1.00", "28"],
            ["SymbolicRegression", "8.734", "0.90", "1.00", "28"],
            ["StackMean", "9.477", "0.90", "1.00", "28"],
            ["BiLSTM", "10.951", "0.90", "1.00", "28"],
            ["LSTM", "17.284", "0.90", "1.00", "28"],
            ["CNN", "19.114", "0.90", "1.00", "28"],
            ["CNN_LSTM_Hybrid", "21.863", "0.90", "1.00", "28"],
        ],
        "Table 7.7: Split-conformal interval half-widths at ninety per cent",
    )),
    ("p",
     "The half-widths rank the models in the same order as the point-error "
     "metrics, which is the expected behaviour and a useful internal "
     "consistency check. The physics-residual hybrid produces the tightest "
     "interval at plus or minus 6.85 metric tons per hectare; the hybrid "
     "CNN-LSTM produces the widest at plus or minus 21.86, which on a target "
     "with a mean of 16.39 is an interval wider than the entire observed range "
     "and therefore operationally useless. Conformal calibration makes that "
     "uselessness explicit rather than allowing a confident-looking point "
     "forecast to conceal it, which is exactly what the method is for."),
    ("p",
     "The empirical coverage of 1.00 for every model requires honest comment "
     "and must not be read as a success. Coverage was measured on the same "
     "twenty-eight residuals used to compute the quantile, and with a "
     "calibration set that small the finite-sample correction in the "
     "split-conformal quantile is substantial: the ninetieth percentile of "
     "twenty-eight points, corrected, lands at or near the maximum observed "
     "residual, so by construction almost nothing falls outside. The theoretical "
     "guarantee — that marginal coverage is at least the nominal level under "
     "exchangeability — still holds, but it is a lower bound, and here the "
     "intervals are conservative rather than tight. A calibration set of a few "
     "hundred records would be needed before the empirical figure carried "
     "independent information. The correct reading of Table 7.7 is that the "
     "half-widths are trustworthy as an upper bound on uncertainty and that "
     "even the best of them, at plus or minus 6.85 on a mean of 16.39, is wide."),
    ("p",
     "Even so, a wide honest interval is more useful to an import planner than "
     "a narrow dishonest one. A forecast of 16 plus or minus 7 metric tons per "
     "hectare tells a planner to hedge; a forecast of 16 with no interval "
     "invites them not to."),

    ("h2", "7.11 Feature Attribution"),
    ("p",
     "SHAP attributions [19] were computed on the best tree model. Figure 7.5 "
     "shows the top-fifteen ranking by mean absolute attribution, Figure 7.6 "
     "the summary plot showing the direction of each predictor's effect, and "
     "Figure 7.7 the dependence plot for the highest-ranked predictor."),
    ("fig", (f"{REAL}/results/shap_importance.png",
             "Figure 7.5: SHAP mean absolute attribution, top fifteen predictors")),
    ("fig", (f"{REAL}/results/shap_summary.png",
             "Figure 7.6: SHAP summary plot")),
    ("p",
     "The temperature-humidity interaction dominates, with a mean absolute "
     "attribution of 1.404 — nearly three times the second-ranked predictor. "
     "The seasonal mean EVI follows at 0.484, then the drought index at 0.148, "
     "the rainfall-NDVI interaction at 0.141 and the previous year's yield at "
     "0.123. Below that the attributions decline smoothly through the "
     "temperature range, seasonal mean NDVI, maximum daily rainfall and the day "
     "and night land surface temperatures."),
    ("p",
     "Two things are notable. First, the top of the ranking is dominated by "
     "engineered interaction terms rather than by raw measurements. The "
     "temperature-humidity product and the rainfall-NDVI product were both "
     "constructed from agronomic hypothesis in section 5.3, and both outrank "
     "the raw variables they were built from. That is direct evidence that the "
     "feature engineering added information rather than merely reformatting it "
     "— which matters, because in a regime where the model cannot discover "
     "interactions from data, the interactions have to be supplied."),
    ("p",
     "Second, the ranking is agronomically coherent. Warm and humid conditions "
     "drive both evaporative demand and fungal pressure on onion foliage; "
     "canopy vigour as measured by EVI is the realised outcome of the growing "
     "season; moisture deficit and district productivity history complete the "
     "picture. A model whose top predictors were, say, sand fraction and solar "
     "radiation would warrant suspicion. This one does not."),
    ("fig", (f"{REAL}/results/shap_dependence_temp_x_humidity.png",
             "Figure 7.7: SHAP dependence for the temperature-humidity interaction")),
    ("p",
     "The dependence plot in Figure 7.7 shows how the attribution of the "
     "leading predictor varies with its own value, revealing the non-monotone "
     "response the tree ensemble learned. The full attribution ranking is "
     "tabulated in Appendix C."),
    ("p",
     "One caution applies to the whole section. Attributions computed on a "
     "model that explains nine per cent of variance describe what that model "
     "does, not necessarily what nature does. The ranking is a statement about "
     "the fitted function and should be read as a hypothesis about drivers to "
     "be confirmed on a larger record, not as an established agronomic finding."),

    ("h2", "7.12 Architecture Validation on Synthetic Data"),
    ("p",
     "Every result above is bounded by twenty-eight records. That raises a "
     "question the real data cannot answer: is the pipeline correct? A "
     "pipeline with a subtle defect — a misaligned join, a leaked target, a "
     "mis-specified architecture — would also produce near-zero coefficients of "
     "determination, and the two causes would be indistinguishable from the "
     "real-data results alone."),
    ("p",
     "To separate them, the identical code was run against a synthetic dataset "
     "of approximately 160 records generated from a fixed seed and calibrated "
     "to published district yield ranges and to the correlation structure "
     "expected between weather, vegetation indices and yield. The synthetic run "
     "shares every line of the pipeline with the real run; only the input "
     "differs. Table 7.8 reports the outcome, and Figure 7.8 shows it. These "
     "are synthetic numbers and are labelled as such; they are not claims about "
     "big onion yield in Sri Lanka."),
    ("table", (
        ["Model", "RMSE", "MAE", "R²", "MAPE (%)"],
        [
            ["RandomForest", "2.0677", "1.6824", "0.8421", "24.68"],
            ["SymbolicRegression", "2.0944", "1.6572", "0.8380", "23.01"],
            ["XGBoost", "2.3030", "1.8596", "0.8041", "26.59"],
            ["SVR", "2.8676", "2.2984", "0.6963", "33.81"],
            ["CNN", "4.4423", "3.6005", "0.2711", "35.49"],
            ["CNN_LSTM_Hybrid", "4.9434", "3.9557", "0.0974", "36.59"],
            ["BiLSTM", "5.1006", "4.0954", "0.0391", "66.27"],
            ["LSTM", "5.1478", "4.2112", "0.0212", "64.92"],
        ],
        "Table 7.8: Synthetic-data model comparison (architecture validation)",
    )),
    ("fig", (f"{SYNTH}/results/model_comparison_bar.png",
             "Figure 7.8: Model comparison on the synthetic reference dataset")),
    ("p",
     "On the synthetic reference the same Random Forest implementation reaches "
     "a coefficient of determination of 0.842 and a root mean squared error of "
     "2.07, comfortably exceeding the 0.75 target, and symbolic regression "
     "reaches 0.838. The synthetic ablation is likewise interpretable: "
     "satellite alone reaches 0.802, weather alone 0.256, historical alone "
     "0.471, soil alone −0.408, weather with satellite 0.809 and all sources "
     "0.829 — an ordering in which the satellite stream is clearly the "
     "highest-value source and combination helps rather than hurts."),
    ("p",
     "Three conclusions follow. The pipeline is correct: the same code that "
     "returns 0.020 on twenty-eight records returns 0.842 on a hundred and "
     "sixty, so the near-zero real-data scores are attributable to the sample, "
     "not to a defect. The feature design is sound: the ablation behaves as "
     "designed when the sample supports it. And the deep-versus-classical "
     "finding is robust rather than an artefact of extreme scarcity — even at "
     "160 records the classical models lead decisively, with the best deep "
     "model at 0.271 against Random Forest at 0.842. Deep architectures for "
     "this problem need far more data than either dataset provides."),

    ("h2", "7.13 Summary"),
    ("p",
     "This chapter evaluated the system on twenty-eight collected records "
     "spanning four districts and seven Yala seasons. The physics-residual "
     "hybrid is the best model at R² 0.091 and RMSE 3.90 MT/Ha; the "
     "proposal-stage target of 0.75 is not met on real data. The mechanistic "
     "backbone improves the coefficient of determination by 0.070 over the "
     "plain Random Forest, confirming that supplying agronomy beats learning "
     "it at this scale. Stacking does not help, though the learned convex blend "
     "clearly beats the equal-weight mean, so the forecast-combination puzzle "
     "does not hold here. Every deep architecture falls below the mean "
     "predictor, with the Wilcoxon test rejecting parity at p below 0.0001. The "
     "ablation shows no single data source suffices and that adding features "
     "can hurt. Per-district analysis shows Anuradhapura most predictable and "
     "Kurunegala least by R², with the ordering reversing under absolute error. "
     "Conformal intervals rank consistently with point errors but are "
     "conservative at this calibration size. SHAP places engineered interaction "
     "terms at the top of the ranking. The synthetic reference run reaches "
     "0.842 with identical code, establishing that the limiting factor is the "
     "sample rather than the implementation. The next chapter interprets these "
     "results and sets out what should follow."),
]


# ============================================================================
# Chapter 8 — Discussion and Conclusion
# ============================================================================

CHAPTER_8 = [
    ("chapter", ("8", "Discussion, Conclusion and Further Work")),

    ("h2", "8.1 Introduction"),
    ("p",
     "Chapter 7 reported what the system achieves. This chapter interprets "
     "those results, positions the work against the literature reviewed in "
     "Chapter 2, states the contributions the project makes, sets out honestly "
     "the threats to the validity of its conclusions, describes the further "
     "work that would follow, and concludes."),

    ("h2", "8.2 Interpretation of the Results"),
    ("h3", "8.2.1 On not meeting the accuracy target"),
    ("p",
     "The project proposal set a target coefficient of determination above "
     "0.75. On the collected data the best model reaches 0.091. It is worth "
     "being direct about what that means and what it does not."),
    ("p",
     "It does not mean the pipeline is defective. Section 7.12 established that "
     "the identical code reaches 0.842 when given an adequate sample. It does "
     "not mean the features are poorly designed; the same ablation that is "
     "uninterpretable on twenty-eight records behaves exactly as designed on a "
     "hundred and sixty. And it does not mean the evaluation is pessimistic by "
     "choice — it means the evaluation is honest. A random train-test split on "
     "twenty-eight records would have produced a far more flattering number, "
     "and that number would have been an artefact of records from the same year "
     "appearing on both sides of the split."),
    ("p",
     "What it does mean is that the target was set before the size of the "
     "obtainable record was known. Twenty-eight observations of a noisy "
     "biological process, against thirty-two candidate predictors, with the "
     "dominant sources of variation — cultivar choice, irrigation scheduling, "
     "fertiliser application, pest incidence, harvest timing — entirely "
     "unobserved, is not a setting in which ninety per cent of variance can be "
     "explained by weather and satellite proxies. The honest statement of the "
     "result is that the system explains about nine per cent of district yield "
     "variance and issues forecasts with a typical absolute miss of 3.35 metric "
     "tons per hectare, or 23.3 per cent of the actual value, and that this is "
     "what the available data supports."),
    ("p",
     "Whether that is useful depends on the alternative. The current practice "
     "it would replace is a subjective post-harvest field assessment with no "
     "quantified error at all. A pre-harvest forecast with a stated interval, "
     "even a wide one, is a different kind of object from an unquantified "
     "estimate arriving too late to act on."),
    ("h3", "8.2.2 On the deep learning result"),
    ("p",
     "The comprehensive failure of the deep family — every architecture below "
     "the mean predictor, the two convolutional models near R² of −7 — is the "
     "project's clearest empirical finding, and it is a negative one. The "
     "literature that motivated including them [2], [8], [20] is not wrong; it "
     "is validated in a regime this problem does not occupy. Representation "
     "learning trades sample efficiency for expressive power, and when the "
     "sample is twenty-four training records per fold, there is nothing to "
     "trade with."),
    ("p",
     "The finding survives a scale increase. At 160 synthetic records the "
     "classical models still lead decisively, 0.842 against 0.271 for the best "
     "deep model. This suggests the crossover point for this problem structure "
     "lies well beyond a few hundred records, which for district-level "
     "seasonal yield data means decades of additional record-keeping across "
     "many more districts. The actionable guidance for a practitioner facing a "
     "similar problem is therefore concrete: do not begin with a deep "
     "architecture, and do not interpret its failure as an implementation "
     "error."),
    ("h3", "8.2.3 On the mechanistic backbone"),
    ("p",
     "The physics-residual result — a 0.070 improvement in R² over the plain "
     "Random Forest, and independent confirmation through the convex stack "
     "assigning it the largest weight at 0.399 — is the project's clearest "
     "positive finding. Its interest lies in the mechanism rather than the "
     "magnitude. The backbone alone scores −0.222, so it is not a good "
     "predictor. It helps because it removes work from the learner: the "
     "water-limitation and thermal-time relationships come from FAO-33 [31] and "
     "the standard degree-day formulation [32] instead of being estimated from "
     "two dozen records."),
    ("p",
     "The generalisation is that in data-scarce agricultural prediction, "
     "domain knowledge should enter as model structure rather than as feature "
     "selection. Encoding an approximately correct physiological relationship "
     "as a fixed functional form buys more than adding another predictor "
     "column, because it does not consume degrees of freedom. Shahhosseini et "
     "al. [33] demonstrated this with a full crop simulator; this work shows "
     "that a three-factor closed form obtains a measurable part of the same "
     "benefit at a small fraction of the modelling cost."),
    ("h3", "8.2.4 On stacking and combination"),
    ("p",
     "That the learned convex blend beat the equal-weight mean by a wide margin "
     "— −0.116 against −0.530 — while both remained worse than the single best "
     "model is a coherent and instructive pair of results. The forecast-"
     "combination puzzle [37], [38] presumes base learners of broadly "
     "comparable quality, in which case estimating weights costs more than it "
     "gains. That presumption fails when the pool contains models scoring below "
     "−7, since uniform weighting then commits a ninth of the blend to each of "
     "them. Meanwhile, estimating nine weights from twenty-eight out-of-fold "
     "predictions is itself beyond what the sample supports, which is why no "
     "combiner beat the physics-residual hybrid alone. The practical lesson is "
     "to prune the base pool before combining, not to combine everything and "
     "hope the weights sort it out."),

    ("h2", "8.3 How This Work Differs from Others"),
    ("p",
     "Table 8.1 positions the work against the closest prior studies along the "
     "dimensions that distinguish it."),
    ("table", (
        ["Dimension", "Closest prior work", "What this work does differently"],
        [
            ["Crop and region", "Iqbal et al. [9] — onion, Bangladesh, climate only",
             "Big onion, four Sri Lankan districts, four integrated data streams"],
            ["Sri Lankan context", "Amarasinghe et al. [5]; Wickramasinghe et al. [10] — rice",
             "First yield-prediction system for a Sri Lankan vegetable crop"],
            ["Model comparison", "Chikwendu et al. [3] — random split, no significance test",
             "LOYO-CV with nested tuning and paired Wilcoxon testing"],
            ["Deep architecture", "Rajpoot & Chandrakar [8] — hybrid CNN-LSTM at large n",
             "Same family with season injection, and evidence it fails at small n"],
            ["Mechanistic hybrid", "Shahhosseini et al. [33] — full crop simulator + ML",
             "Closed-form FAO-33/GDD backbone + residual learner, measured ablation"],
            ["Combination", "Standard stacking practice",
             "Simplex-constrained convex blend with explicit puzzle benchmark"],
            ["Uncertainty", "Point forecasts, typical in the reviewed literature",
             "Distribution-free split-conformal intervals per model"],
            ["Interpretability", "Post-hoc importance where reported",
             "Exact SHAP attributions plus a served closed-form equation"],
            ["Data-source value", "Not decomposed for vegetables in this region",
             "Six-configuration controlled ablation, real and synthetic"],
        ],
        "Table 8.1: Positioning against the closest prior work",
    )),
    ("p",
     "The difference that matters most is one of posture rather than of "
     "technique. Much of the reviewed literature reports the best score its "
     "authors obtained. This work reports what a full family of methods "
     "achieves under one protocol, including the methods that failed and the "
     "combination strategies that did not pay, and states the sample-size "
     "conditions under which each conclusion holds. In a field where "
     "optimistic evaluation is common, that is a substantive difference."),

    ("h2", "8.4 Contributions of This Research"),
    ("p",
     "The project makes five contributions, each mapping to a gap identified in "
     "section 2.8."),
    ("p",
     "First, the first end-to-end yield prediction system for big onion in "
     "Sri Lanka, integrating district yield records, reanalysis weather, "
     "satellite vegetation and thermal indices and gridded soil properties into "
     "a reproducible pipeline that runs on commodity hardware and serves "
     "forecasts through a documented interface and a decision-support "
     "dashboard. This addresses Gap 1."),
    ("p",
     "Second, an empirical answer to the deep-versus-classical question in the "
     "severely data-scarce vegetable yield regime. Nine model families under "
     "one protocol with paired significance testing establish that classical "
     "regularised learners dominate and that deep architectures fail below the "
     "mean predictor, and the synthetic replication shows the finding is not an "
     "artefact of extreme scarcity. This addresses Gap 2."),
    ("p",
     "Third, a lightweight physics-residual hybrid that couples a closed-form "
     "FAO-33 and degree-day backbone [31], [32] to a learned residual, with a "
     "controlled three-way ablation demonstrating a 0.070 improvement in R² "
     "over the equivalent purely learned model, and independent corroboration "
     "from the stacking weights. This addresses Gap 3 and is the project's "
     "principal methodological novelty."),
    ("p",
     "Fourth, a hybrid CNN-LSTM architecture with season-indicator injection "
     "positioned after feature extraction, designed so that branch parameters "
     "are shared across seasons while only the dense head learns "
     "season-specific baselines. The design and its data-efficiency rationale "
     "are contributed; its empirical validation is incomplete because the "
     "collected data covers only one season, and this is stated as a limitation "
     "rather than glossed. This addresses Gap 4 partially."),
    ("p",
     "Fifth, a six-configuration controlled ablation quantifying data-source "
     "contribution for this crop and region, on both the real and the synthetic "
     "record, together with a constrained-stacking benchmark that tests the "
     "forecast-combination puzzle explicitly and distribution-free conformal "
     "intervals attached to every model. This addresses Gap 5 and supplies the "
     "methodological rigour that section 2.2 identified as frequently absent."),

    ("h2", "8.5 Threats to Validity and Limitations"),
    ("p",
     "Six limitations bound the conclusions, and stating them precisely is part "
     "of the contribution."),
    ("p",
     "Sample size. Twenty-eight records is the binding constraint on every "
     "quantitative result. All accuracy figures should be read as lower bounds "
     "on what the approach could achieve with a fuller record, and all "
     "comparative conclusions as holding specifically in this regime."),
    ("p",
     "Single season. The collected data covers Yala only. The season indicator "
     "is constant across every real record, so the hybrid architecture's "
     "central design claim cannot be tested on real data, and no conclusion "
     "about Maha behaviour is supported."),
    ("p",
     "Conformal calibration size. The empirical coverage of 1.00 reported in "
     "section 7.10 is an artefact of calibrating and measuring on the same "
     "twenty-eight residuals. The theoretical guarantee holds, but the "
     "intervals are conservative and the empirical figure carries no "
     "independent information."),
    ("p",
     "Unobserved drivers. Cultivar, irrigation scheduling, fertiliser regime, "
     "pest and disease incidence and harvest timing are all unobserved and all "
     "plausibly account for a substantial share of yield variance. No model "
     "built on weather, satellite and soil proxies alone can recover them, "
     "which places a ceiling on achievable accuracy that no amount of "
     "additional modelling effort will lift."),
    ("p",
     "Target quality. The district yield figures used as ground truth are "
     "themselves derived from subjective field assessment rather than from "
     "crop-cutting measurement [4]. Error in the target propagates directly "
     "into every reported metric, and part of the unexplained variance may be "
     "measurement error in the label rather than in the model."),
    ("p",
     "Spatial aggregation. Yield is modelled at district level, but cultivation "
     "within a district is heterogeneous in soil, irrigation access and "
     "management. A district-mean prediction cannot represent that "
     "heterogeneity, and satellite indices averaged over a district include "
     "substantial non-onion land cover."),

    ("h2", "8.6 Further Work"),
    ("p",
     "The single highest-value action is to extend the record. Every limitation "
     "in section 8.5 except the last two is a consequence of sample size. "
     "Extending backwards through the satellite archive to the early 2000s, "
     "adding the Maha season, and including secondary producing districts would "
     "plausibly bring the record to two or three hundred observations, which "
     "section 7.12 indicates is the region where the methods begin to work as "
     "designed."),
    ("p",
     "Second, restrict the satellite aggregation to cultivated onion extent "
     "rather than to whole districts. A crop mask derived from Sentinel-2 "
     "[27] classification would substantially raise the signal-to-noise ratio "
     "of every vegetation predictor, and this is likely the highest-value "
     "improvement obtainable without new ground data."),
    ("p",
     "Third, extend the mechanistic backbone. Given that the closed-form "
     "three-factor form already yields a measurable improvement, a fuller "
     "formulation — radiation-use efficiency, an explicit soil water balance, a "
     "phenology-stage-dependent water sensitivity following the full FAO-33 "
     "treatment [31] — is the natural next step and is likely to pay more than "
     "further work on the learned component."),
    ("p",
     "Fourth, incorporate management data. Even coarse district-level "
     "indicators of irrigation coverage, fertiliser distribution and cultivar "
     "share would address the unobserved-driver limitation directly, and these "
     "are collected administratively even where they are not published."),
    ("p",
     "Fifth, evaluate at operational lead time. All results here use predictors "
     "aggregated over the complete growing season, which is the post-season "
     "setting. An import planner needs a forecast four to eight weeks before "
     "harvest. Re-running the protocol with predictors truncated at successive "
     "points in the season would quantify the accuracy-versus-lead-time "
     "trade-off, which is the question an operational user would actually ask."),
    ("p",
     "Sixth, conduct a field validation with the intended users. The dashboard "
     "has been built but not evaluated with Department of Census and Statistics "
     "or district agricultural officers. Whether a forecast of 16 plus or minus "
     "7 metric tons per hectare changes any decision is an empirical question "
     "about users, not about models, and it has not yet been asked."),

    ("h2", "8.7 Conclusion"),
    ("p",
     "This project set out to build a pre-harvest yield forecasting capability "
     "for big onion in Sri Lanka, where none existed. It delivered a complete "
     "system: a reproducible multi-source data pipeline, thirty-two engineered "
     "predictors, nine model families evaluated under a single leakage-free "
     "protocol, a constrained combination layer, distribution-free uncertainty "
     "quantification, exact feature attribution, a REST serving interface and a "
     "decision-support dashboard."),
    ("p",
     "On the twenty-eight seasonal records that could be collected, the "
     "physics-residual hybrid is the best predictor, explaining nine per cent "
     "of district yield variance with a typical absolute error of 3.35 metric "
     "tons per hectare. The proposal's accuracy target of 0.75 was not met on "
     "real data, and the reason is the size of the available record rather than "
     "the construction of the system: identical code reaches 0.842 on an "
     "adequate sample."),
    ("p",
     "The research findings are more durable than the accuracy figure. Deep "
     "architectures fail comprehensively in this regime and the failure "
     "persists at a fivefold larger sample, which is guidance the existing "
     "literature does not provide. A lightweight mechanistic backbone drawn "
     "from established agronomy measurably improves a purely learned model, "
     "confirmed independently by the stacking weights, which argues that domain "
     "knowledge belongs in model structure rather than in feature lists when "
     "data is scarce. Estimated combination weights beat uniform averaging when "
     "base learners differ sharply in quality, but no combination beats the "
     "best single model when weights must be estimated from twenty-eight "
     "points. Engineered interaction terms outrank the raw measurements they "
     "were built from. And no single data stream suffices."),
    ("p",
     "The system as it stands is a working foundation with an honest account of "
     "what it can and cannot do. Its accuracy is bounded by an information "
     "constraint, not an engineering one, and the path to improving it — a "
     "longer record, a crop mask, a fuller mechanistic backbone, management "
     "covariates — is identified and concrete. For a crop on which national "
     "import decisions turn and for which no forecast currently exists, a "
     "calibrated and explainable pre-harvest estimate with a stated interval is "
     "a capability worth having, and this work establishes both that it can be "
     "built and what it will take to make it good."),

    ("h2", "8.8 Summary"),
    ("p",
     "This chapter interpreted the results of Chapter 7, positioned the work "
     "against the closest prior studies, stated five contributions mapped to "
     "the five gaps of section 2.8, set out six limitations that bound the "
     "conclusions, described six lines of further work in priority order, and "
     "concluded. The report's references and four appendices follow."),
]


ALL_CHAPTERS = [
    CHAPTER_1, CHAPTER_2, CHAPTER_3, CHAPTER_4,
    CHAPTER_5, CHAPTER_6, CHAPTER_7, CHAPTER_8,
]


# ============================================================================
# References — IEEE format (per the "Sample References, IEEE Format" handout).
#
# Entry style: author initials FIRST then surname; article/paper titles in
# double quotes; source, vol./no./pp. and year after; every entry ends with a
# period.
#
# Each item is (authoring_number, sort_key, ieee_text). The authoring number is
# what the prose above cites; the emitted number is assigned at build time by
# REFERENCE_ORDER, and the in-text citations are remapped to match. sort_key is
# given explicitly because IEEE initials-first names make the first-author
# surname impossible to parse reliably, and several entries have corporate
# authors.
#
# ORDERING NOTE: the Faculty guideline (Karunananda 2006, p.2) requires the list
# to be alphabetical by first-author surname; the IEEE handout numbers entries in
# order of first citation. Both cannot hold at once. REFERENCE_ORDER selects.
# ============================================================================

REFERENCE_ORDER = "alphabetical"   # "alphabetical" (Faculty guideline) | "citation" (strict IEEE)

REFERENCES = [
    (1, "Jabed", '[1] M. A. Jabed, M. R. Karim, M. S. Hossain, M. K. Hossain, M. M. Khan, and M. Begum, "Crop yield prediction in agriculture: a comprehensive review of machine learning and deep learning approaches, with insights for future research," Heliyon, vol. 10, no. 24, e40836, 2024.'),
    (2, "Kamilaris", '[2] A. Kamilaris and F. X. Prenafeta-Boldú, "Deep learning in agriculture: a survey," Computers and Electronics in Agriculture, vol. 147, pp. 70-90, 2018.'),
    (3, "Chikwendu", '[3] F. Chikwendu, A. Ahmed, and A. Ortega-Mansilla, "A comparative study of machine learning models in predicting crop yield," Discover Agriculture, Springer, 2025.'),
    (4, "Department of Census", '[4] Department of Census and Statistics Sri Lanka, Big Onion Survey Reports, Colombo, Sri Lanka, http://www.statistics.gov.lk, 2010-2025.'),
    (5, "Amarasinghe", '[5] A. Amarasinghe, P. De Silva, and K. Wijesinghe, "Advancing food sustainability: rice yield prediction in Sri Lanka using weather-based, feature-engineered machine learning models," Discover Applied Sciences, vol. 6, 603, 2024.'),
    (6, "Department of Agriculture", '[6] Department of Agriculture Sri Lanka, HORDI Crop - Big Onion: Cultivation Guidelines, Peradeniya, Sri Lanka, http://doa.gov.lk, n.d.'),
    (7, "Wang", '[7] Z. Wang, Y. Yan, Q. Lu, and P. Yang, "Machine learning crop yield models based on meteorological features and comparison with a process-based model," Artificial Intelligence for the Earth Systems, vol. 1, no. 4, pp. 1-18, 2022.'),
    (8, "Rajpoot", '[8] S. Rajpoot and O. Chandrakar, "A hybrid CNN-LSTM deep learning framework for enhanced crop yield prediction using spatial-temporal agricultural data," International Journal of Statistics and Applied Mathematics, vol. SP-10, no. 12, pp. 1-9, 2025.'),
    (9, "Iqbal", '[9] D. M. Iqbal, S. Hossain, M. S. Rahman, and R. Karim, "OnionBangla: a supervised machine learning approach for predicting onion yield using Bangladeshi climate data," in Proc. IEEE Int. Conf. Computing and Communication Informatics, 2023, pp. 178-185.'),
    (10, "Wickramasinghe", '[10] L. Wickramasinghe, J. A. Weliwita, and I. U. Ekanayake, "Modeling the relationship between rice yield and climate variables using statistical and machine learning techniques," Journal of Mathematics, vol. 2021, 1972927, 2021.'),
    (11, "Kim", '[11] W. Kim and B. M. Soon, "Advancing agricultural predictions: a deep learning approach to estimating bulb weight using the Neural Prophet model," Agronomy, vol. 13, no. 5, 1305, 2023.'),
    (12, "Herath", '[12] K. Herath, B. Perera, and S. Hewage, "Extraction of agricultural phenological parameters of Sri Lanka using MODIS NDVI time series data," Procedia Food Science, vol. 6, pp. 1248-1254, 2016.'),
    (13, "FAOSTAT", '[13] FAOSTAT, Food and Agriculture Statistics - Crops and Livestock Products, Food and Agriculture Organization of the United Nations, Rome, Italy, http://www.fao.org/faostat, 2024.'),
    (14, "Sutharsan", '[14] J. Sutharsan and S. Yogendran, "Red onion price factors correlation identification and price prediction using multiple machine learning models for the Jaffna district, Sri Lanka," in Proc. IEEE Conf. Computational Intelligence, 2023, pp. 412-419.'),
    (15, "MODIS Science Team", '[15] MODIS Science Team, MODIS Vegetation Index User Guide (MOD13 Series), NASA Goddard Space Flight Center, Greenbelt, MD, http://modis.gsfc.nasa.gov, 2019.'),
    (16, "Hochreiter", '[16] S. Hochreiter and J. Schmidhuber, "Long short-term memory," Neural Computation, vol. 9, no. 8, pp. 1735-1780, 1997.'),
    (17, "Breiman", '[17] L. Breiman, "Random forests," Machine Learning, vol. 45, no. 1, pp. 5-32, 2001.'),
    (18, "Chen", '[18] T. Chen and C. Guestrin, "XGBoost: a scalable tree boosting system," in Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, 2016, pp. 785-794.'),
    (19, "Lundberg", '[19] S. M. Lundberg and S.-I. Lee, "A unified approach to interpreting model predictions," in Advances in Neural Information Processing Systems 30, 2017, pp. 4765-4774.'),
    (20, "LeCun", '[20] Y. LeCun, Y. Bengio, and G. Hinton, "Deep learning," Nature, vol. 521, no. 7553, pp. 436-444, 2015.'),
    (21, "Pedregosa", '[21] F. Pedregosa, G. Varoquaux, A. Gramfort, and others, "Scikit-learn: machine learning in Python," Journal of Machine Learning Research, vol. 12, pp. 2825-2830, 2011.'),
    (22, "Abadi", '[22] M. Abadi, P. Barham, J. Chen, Z. Chen, A. Davis, and others, "TensorFlow: a system for large-scale machine learning," in Proc. 12th USENIX Symp. Operating Systems Design and Implementation, 2016, pp. 265-283.'),
    (23, "Gorelick", '[23] N. Gorelick, M. Hancher, M. Dixon, S. Ilyushchenko, D. Thau, and R. Moore, "Google Earth Engine: planetary-scale geospatial analysis for everyone," Remote Sensing of Environment, vol. 202, pp. 18-27, 2017.'),
    (24, "Hengl", '[24] T. Hengl, J. Mendes de Jesus, G. B. M. Heuvelink, and others, "SoilGrids250m: global gridded soil information based on machine learning," PLoS ONE, vol. 12, no. 2, e0169748, 2017.'),
    (25, "Funk", '[25] C. Funk, P. Peterson, M. Landsfeld, D. Pedreros, J. Verdin, and others, "The climate hazards infrared precipitation with stations - a new environmental record for monitoring extremes," Scientific Data, vol. 2, 150066, 2015.'),
    (26, "Stackhouse", '[26] P. W. Stackhouse, NASA POWER Project - Prediction of Worldwide Energy Resources, NASA Langley Research Center, Hampton, VA, http://power.larc.nasa.gov, n.d.'),
    (27, "Drusch", '[27] M. Drusch, U. Del Bello, S. Carlier, and others, "Sentinel-2: ESA\'s optical high-resolution mission for GMES operational services," Remote Sensing of Environment, vol. 120, pp. 25-36, 2012.'),
    (28, "Wan", '[28] Z. Wan, S. Hook, and G. Hulley, MOD11A1 MODIS/Terra Land Surface Temperature and Emissivity Daily L3 Global 1 km SIN Grid V006, NASA EOSDIS Land Processes DAAC, Sioux Falls, SD, 2015.'),
    (29, "Karunananda", '[29] A. S. Karunananda, "Guidelines for preparation of final reports," Faculty of Information Technology, Univ. of Moratuwa, Moratuwa, Sri Lanka, internal document, 2006.'),
    (30, "Wilcoxon", '[30] F. Wilcoxon, "Individual comparisons by ranking methods," Biometrics Bulletin, vol. 1, no. 6, pp. 80-83, 1945.'),
    (31, "Doorenbos", '[31] J. Doorenbos and A. H. Kassam, Yield Response to Water, FAO Irrigation and Drainage Paper 33. Rome, Italy: Food and Agriculture Organization of the United Nations, 1979.'),
    (32, "McMaster", '[32] G. S. McMaster and W. W. Wilhelm, "Growing degree-days: one equation, two interpretations," Agricultural and Forest Meteorology, vol. 87, no. 4, pp. 291-300, 1997.'),
    (33, "Shahhosseini", '[33] M. Shahhosseini, G. Hu, I. Huber, and S. V. Archontoulis, "Coupling machine learning and crop modeling improves crop yield prediction in the US Corn Belt," Scientific Reports, vol. 11, 1606, 2021.'),
    (34, "Koza", '[34] J. R. Koza, Genetic Programming: On the Programming of Computers by Means of Natural Selection. Cambridge, MA: MIT Press, 1992.'),
    (35, "Wolpert", '[35] D. H. Wolpert, "Stacked generalization," Neural Networks, vol. 5, no. 2, pp. 241-259, 1992.'),
    (36, "Breiman", '[36] L. Breiman, "Stacked regressions," Machine Learning, vol. 24, no. 1, pp. 49-64, 1996.'),
    (37, "Stock", '[37] J. H. Stock and M. W. Watson, "Combination forecasts of output growth in a seven-country data set," Journal of Forecasting, vol. 23, no. 6, pp. 405-430, 2004.'),
    (38, "Claeskens", '[38] G. Claeskens, J. R. Magnus, A. L. Vasnev, and W. Wang, "The forecast combination puzzle: a simple theoretical explanation," International Journal of Forecasting, vol. 32, no. 3, pp. 754-762, 2016.'),
    (39, "Vovk", '[39] V. Vovk, A. Gammerman, and G. Shafer, Algorithmic Learning in a Random World. New York, NY: Springer, 2005.'),
    (40, "Angelopoulos", '[40] A. N. Angelopoulos and S. Bates, "Conformal prediction: a gentle introduction," Foundations and Trends in Machine Learning, vol. 16, no. 4, pp. 494-591, 2023.'),
]


def ordered_references(citation_order=None):
    """Return REFERENCES in emission order.

    citation_order: list of authoring numbers in order of first appearance in
    the body text, supplied by the builder. Used only when REFERENCE_ORDER is
    "citation".
    """
    if REFERENCE_ORDER == "citation" and citation_order:
        rank = {n: i for i, n in enumerate(citation_order)}
        return sorted(REFERENCES, key=lambda r: rank.get(r[0], len(rank) + r[0]))
    # Breiman appears twice: break the tie on the authoring number so 2001
    # precedes 1996 deterministically rather than by list accident.
    return sorted(REFERENCES, key=lambda r: (r[1].lower(), r[0]))


def add_references(doc, heading_fn, para_fn, page_break_fn, body_font,
                   citation_order=None):
    """Emit the reference list in IEEE entry format.

    Per the IEEE handout's REFERENCE PAGE FORMAT: square brackets around the
    number, entries single-spaced internally with a blank line between them,
    each entry ending with a period.
    """
    heading_fn(doc, "References", level="chapter")
    ordering_note = (
        "sorted alphabetically by the surname of the first author, as required "
        "by the Faculty guideline [29]"
        if REFERENCE_ORDER == "alphabetical"
        else "numbered in order of first citation in the text, as required by "
             "the IEEE style"
    )
    para_fn(
        doc,
        "References are presented in IEEE format: author initials precede the "
        "surname, titles of articles and papers are given in double quotation "
        "marks, and each entry ends with a period. Citations in the body of the "
        "report use square-bracketed numbers. The list below is "
        + ordering_note
        + ", and every entry in it is cited at least once in the text.",
    )

    for i, (_num, _key, text) in enumerate(ordered_references(citation_order), start=1):
        body = text.split("] ", 1)[1] if "] " in text else text
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        p.paragraph_format.space_after = Pt(12)
        p.paragraph_format.left_indent = Inches(0.45)
        p.paragraph_format.first_line_indent = Inches(-0.45)
        run = p.add_run(f"[{i}] {body}")
        run.font.name = body_font
        run.font.size = Pt(12)
    page_break_fn(doc)


# ============================================================================
# Appendix A — Individual's Contribution to the Project (one full page each)
# ============================================================================

APPENDIX_A = [
    ("h1", "Appendix A"),
    ("h1", "Individual's Contribution to the Project"),
    ("p",
     "This appendix records the individual contribution of each group member, "
     "as required by the Faculty guideline [29]. Each member states their "
     "contribution, what they learned, the problems they encountered and how "
     "those problems were addressed."),
    ("pagebreak", None),

    ("h2", "Name of student: Arkam B.H.M. (214019K)"),
    ("p",
     "My contribution is the machine learning, deep learning and modelling "
     "research component, together with the serving layer. I designed and "
     "implemented the entire modelling pipeline: the three classical learners "
     "(Random Forest, XGBoost and Support Vector Regression), the four deep "
     "architectures (LSTM, Bidirectional LSTM, one-dimensional CNN and the "
     "hybrid CNN-LSTM with season-indicator injection), the symbolic "
     "regression model, and the physics-residual hybrid that proved to be the "
     "best-performing model on the collected data. I implemented the "
     "Leave-One-Year-Out cross-validation harness with nested hyperparameter "
     "search, the paired significance testing, the constrained convex stacking "
     "layer with its forecast-combination-puzzle benchmark, the split-conformal "
     "calibration, the SHAP explainability stage, the six-experiment ablation "
     "study, and the Flask REST serving layer with its eight endpoints."),
    ("p",
     "The two research contributions I consider most substantial are the "
     "physics-residual hybrid and the honest evaluation protocol. For the "
     "hybrid I formulated a mechanistic backbone from the FAO-33 water "
     "production function [31] and the standard growing-degree-day formulation "
     "[32], calibrated it inside each cross-validation fold with only two free "
     "parameters, and trained a Random Forest on the residual. The controlled "
     "three-way ablation in section 7.5 shows this lifts the coefficient of "
     "determination from 0.020 to 0.091, and the convex stacking weights "
     "independently assign it the largest share at 0.399. For the evaluation, "
     "I insisted on Leave-One-Year-Out cross-validation rather than a random "
     "split, because records from the same year share a weather regime and a "
     "random split would have produced a far more flattering and entirely "
     "misleading number."),
    ("p",
     "What I learned. Coming into this project I assumed that a more capable "
     "model would produce a better result, and that deep learning was the "
     "natural destination for a problem involving sequences and images. The "
     "data taught me otherwise. At twenty-eight records, every deep "
     "architecture I built performed worse than predicting the mean, while a "
     "three-line closed-form agronomic formula measurably improved the best "
     "learned model. I now understand that the binding constraint in applied "
     "machine learning is usually information, not capacity, and that the two "
     "highest-leverage activities are feature construction and evaluation "
     "design. I also learned how easily an evaluation can flatter a model, and "
     "how much discipline it takes to keep every fitted quantity — including a "
     "two-parameter calibration — inside the cross-validation fold."),
    ("p",
     "Problems encountered and how I addressed them. The first and largest was "
     "overfitting. My initial deep models achieved near-zero training error and "
     "catastrophic validation error. I addressed this by shrinking every "
     "architecture by an order of magnitude, adding dropout and early stopping, "
     "and ultimately by accepting and reporting the negative result rather than "
     "tuning until a favourable number appeared. The second was target leakage: "
     "my first yield-history features used an unshifted rolling average that "
     "included the record's own target, producing an implausible R² above 0.99. "
     "I found it by disbelieving the number and traced it to the missing shift. "
     "The third was combinatorial runtime, since nested cross-validation over "
     "nine models with full hyperparameter grids did not complete in reasonable "
     "time; I resolved this with reduced inner grids and full grids only at "
     "final refit. The fourth was reproducibility across dataset variants, "
     "which I solved by routing every output path through a single "
     "configuration-level variant switch so the real and synthetic runs cannot "
     "contaminate one another."),
    ("pagebreak", None),

    ("h2", "Name of student: Sharuja B. (214192G)"),
    ("p",
     "My contribution is the data engineering component: the acquisition, "
     "reconciliation, cleaning and feature construction that turns eight "
     "heterogeneous raw sources into the single analysis dataset every model in "
     "this report is trained on. I collected the district yield and extent "
     "records, assembled the daily weather series, extracted the vegetation "
     "index and land surface temperature composites through Google Earth Engine "
     "[23], and obtained the soil property layers [24]. I implemented the "
     "loader that applies the growing-season month window per district and "
     "season, the aggregation rules that reduce each stream to the common "
     "district-season-year key, the preprocessing and validation stage, and the "
     "feature engineering module that produces the thirty-two predictors of "
     "Table 5.1."),
    ("p",
     "Within feature engineering, the derived predictors were the part "
     "requiring most judgement. The growing degree days, heat stress day count "
     "and standardised precipitation index required deciding base and critical "
     "temperatures appropriate to big onion under Sri Lankan conditions, which "
     "I took from the Department of Agriculture cultivation guidelines [6]. The "
     "vegetation dynamics predictors — anomaly, time to peak and growth rate — "
     "required extracting trajectory shape rather than level. The three "
     "interaction terms were constructed from explicit agronomic hypotheses "
     "rather than from statistical convenience, and the SHAP results in section "
     "7.11 place two of them at the very top of the attribution ranking, which "
     "is the most direct validation of that design choice."),
    ("p",
     "What I learned. I learned that the majority of the effort in an applied "
     "machine learning project is spent before any model is trained, and that "
     "the quality of the dataset sets a ceiling that no modelling technique can "
     "raise. I learned to work with satellite data at scale through server-side "
     "reduction rather than local download, and I learned how much agronomic "
     "reading is required to construct a feature that means something — "
     "computing degree days is arithmetic, but choosing the base temperature is "
     "crop science."),
    ("p",
     "Problems encountered and how I addressed them. The most persistent was "
     "grain and key mismatch across sources: weather is daily, vegetation "
     "indices are composite periods, soil is static, yield is seasonal, and "
     "district names appear with different spellings and casings in every "
     "source. I addressed this by defining a canonical district vocabulary in "
     "configuration and mapping every source onto it at load time, and by "
     "making an unmappable name raise rather than silently drop the row, "
     "because a silent drop would have produced a smaller dataset with no "
     "indication of a problem. The second was the Maha season crossing the "
     "calendar year boundary, which a naive year grouping split into two "
     "records; I resolved it by defining the season as an explicit month list "
     "and attributing each record to its starting year. The third was cloud "
     "contamination in the optical satellite composites, addressed through "
     "quality-band filtering before aggregation. The fourth, and the one I "
     "could not solve, was the sheer scarcity of reliable district yield "
     "records — the collected dataset is twenty-eight rows because that is how "
     "many trustworthy records exist, and every limitation in section 8.5 "
     "traces back to it."),
    ("pagebreak", None),

    ("h2", "Name of student: Shathurya P. (214193K)"),
    ("p",
     "My contribution is the decision-support dashboard and the visualisation "
     "and interpretation layer through which every result in this report "
     "reaches its intended users. I designed and implemented the Next.js "
     "application with its locale-aware routing, and built the four views that "
     "correspond to the user groups of Table 4.1: the overview with the "
     "district choropleth map and key figures, the prediction view with the "
     "context-prefilled input form, the explainability view presenting SHAP "
     "attributions and the served symbolic equation, and the recommendation "
     "view that translates a forecast and its drivers into plain-language "
     "guidance. I also built the administrative model-comparison panel used by "
     "technical users."),
    ("p",
     "The design decision I consider most important is the context prefill. An "
     "early version of the prediction form required the user to enter all "
     "thirty-two predictors manually, which no district agricultural officer "
     "would ever do. Working with the serving layer, we added a context "
     "endpoint that returns the most recent known values for a district and "
     "season, so the officer adjusts only the values they have better "
     "information about. A second decision was to render the conformal interval "
     "as prominently as the point forecast rather than as a footnote, because a "
     "forecast of sixteen metric tons per hectare with an interval of plus or "
     "minus seven is a fundamentally different statement from sixteen alone, "
     "and the interface should not let a user miss that."),
    ("p",
     "What I learned. I learned that presenting a model's output honestly is a "
     "design problem as much as an engineering one. It would have been easy to "
     "build an interface that looked authoritative and confident, and it would "
     "have been misleading. I learned to read the model outputs well enough to "
     "represent them correctly — what a SHAP attribution actually claims, what "
     "a conformal interval does and does not guarantee, and why a negative "
     "coefficient of determination is a meaningful number rather than an error. "
     "I also learned front-end internationalisation, which mattered because the "
     "intended district-level users do not all work in English."),
    ("p",
     "Problems encountered and how I addressed them. The first was integration "
     "ambiguity: during development I could not tell which pipeline run a "
     "displayed figure came from, since the real and synthetic variants produce "
     "identically shaped artefacts. We resolved this by adding a provenance "
     "block to every API response naming the model and the dataset variant, and "
     "surfacing it in the interface. The second was rendering the district "
     "choropleth with only four districts, where a continuous colour scale "
     "reads as noise; I switched to a categorical scale anchored on the "
     "historical district means. The third was communicating uncertainty "
     "without alarming the user, which I addressed by pairing every interval "
     "with a short plain-language statement of what it means rather than "
     "presenting a bare numeric range. The fourth was that a locale switch "
     "initially lost the user's form state, resolved by lifting form state "
     "above the locale boundary in the routing structure."),
    ("pagebreak", None),

    ("table", (
        ["Component", "Arkam B.H.M.", "Sharuja B.", "Shathurya P."],
        [
            ["Literature review", "Modelling and evaluation", "Data sources and agronomy", "Visualisation and UX"],
            ["Data acquisition and integration", "—", "Primary", "—"],
            ["Preprocessing and feature engineering", "Review", "Primary", "—"],
            ["Classical and deep models", "Primary", "—", "—"],
            ["Symbolic and physics-residual models", "Primary", "Agronomic constants", "—"],
            ["Evaluation protocol and statistics", "Primary", "—", "—"],
            ["Stacking, conformal, SHAP", "Primary", "—", "Interpretation"],
            ["Ablation study", "Primary", "Configuration design", "—"],
            ["REST serving layer", "Primary", "—", "Contract review"],
            ["Dashboard", "API contract", "—", "Primary"],
            ["Final report", "Chapters 3, 5–8", "Chapters 1, 3, 5", "Chapters 4, 6"],
        ],
        "Table A.1: Distribution of individual contributions",
    )),
]


# ============================================================================
# Appendix B — Configuration and code excerpts
# ============================================================================

APPENDIX_B = [
    ("h1", "Appendix B"),
    ("h1", "Configuration and Code Excerpts"),
    ("p",
     "This appendix contains the configuration and implementation excerpts "
     "referred to in Chapter 6. It is cited from sections 6.2, 6.5, 6.6 and "
     "6.8."),

    ("h2", "B.1 Feature group definitions"),
    ("p",
     "The five predictor groups of Table 5.1 are declared once in the "
     "configuration module and consumed by the feature engineering, ablation "
     "and serving stages, so that a change to the predictor set propagates "
     "everywhere without edits elsewhere."),
    ("code",
     "WEATHER_FEATURES = [\n"
     "    'season_avg_temp', 'season_total_rainfall', 'season_avg_humidity',\n"
     "    'season_avg_solar_rad', 'growing_degree_days', 'heat_stress_days',\n"
     "    'drought_index_spi', 'temp_range', 'max_daily_rainfall',\n"
     "]\n"
     "\n"
     "SATELLITE_FEATURES = [\n"
     "    'season_mean_ndvi', 'season_max_ndvi', 'season_min_ndvi',\n"
     "    'ndvi_std', 'ndvi_anomaly', 'time_to_peak_ndvi', 'ndvi_growth_rate',\n"
     "    'season_mean_evi', 'season_mean_ndwi', 'season_mean_lst_day',\n"
     "    'season_mean_lst_night',\n"
     "]\n"
     "\n"
     "HISTORICAL_FEATURES = [\n"
     "    'prev_season_yield', 'prev_year_yield', 'yield_3yr_avg',\n"
     "    'season_indicator', 'extent_prev_season',\n"
     "]\n"
     "\n"
     "SOIL_FEATURES = ['soil_ph', 'organic_carbon', 'clay_pct', 'sand_pct']\n"
     "\n"
     "INTERACTION_FEATURES = ['rainfall_x_ndvi', 'temp_x_humidity', 'ndvi_x_lst']"),

    ("h2", "B.2 Season windows and evaluation constants"),
    ("p",
     "The season month windows encode the Maha boundary handling described in "
     "section 6.3. The random seed is fixed globally so that every reported "
     "number reproduces exactly."),
    ("code",
     "RANDOM_STATE = 42\n"
     "\n"
     "DISTRICTS = ['Matale', 'Anuradhapura', 'Polonnaruwa', 'Kurunegala']\n"
     "SEASONS   = ['Yala', 'Maha']\n"
     "TARGET_COLUMN = 'Avg_Yield_MT_per_Ha'\n"
     "\n"
     "YALA_MONTHS = [4, 5, 6, 7, 8]\n"
     "MAHA_MONTHS = [10, 11, 12, 1, 2, 3]   # crosses the calendar boundary\n"
     "\n"
     "SEQUENCE_LENGTH = 5      # monthly timesteps in the growing season\n"
     "DROPOUT_RATE    = 0.2\n"
     "TARGET_R2       = 0.75"),

    ("h2", "B.3 Leave-One-Year-Out evaluation harness"),
    ("p",
     "The outer loop of section 6.5. Every fitted quantity is estimated inside "
     "the fold; the held-out year influences neither fitting nor selection."),
    ("code",
     "def loyo_evaluate(model_factory, X, y, years, param_grid):\n"
     "    oof = []\n"
     "    for held_out in sorted(set(years)):\n"
     "        train_idx = years != held_out\n"
     "        test_idx  = years == held_out\n"
     "\n"
     "        # Inner, time-series-aware search on the TRAINING partition only.\n"
     "        search = GridSearchCV(\n"
     "            model_factory(),\n"
     "            param_grid,\n"
     "            cv=TimeSeriesSplit(n_splits=3),\n"
     "            scoring='neg_root_mean_squared_error',\n"
     "        )\n"
     "        search.fit(X[train_idx], y[train_idx])\n"
     "\n"
     "        best = search.best_estimator_\n"
     "        preds = best.predict(X[test_idx])\n"
     "        oof.append((held_out, y[test_idx], preds))\n"
     "    return pool(oof)"),

    ("h2", "B.4 Hybrid CNN-LSTM with season-indicator injection"),
    ("p",
     "The architecture of section 5.5 and Figure 5.2. The season indicator is "
     "concatenated after both branches have completed feature extraction, so "
     "the branches share parameters across seasons."),
    ("code",
     "veg_in     = Input(shape=(SEQUENCE_LENGTH, n_veg_channels))\n"
     "weather_in = Input(shape=(SEQUENCE_LENGTH, N_WEATHER_PER_STEP))\n"
     "season_in  = Input(shape=(1,))          # Yala = 1, Maha = 0\n"
     "\n"
     "# CNN branch — local shape of the vegetation trajectory\n"
     "c = Conv1D(32, 3, activation='relu', padding='same')(veg_in)\n"
     "c = Dropout(DROPOUT_RATE)(c)\n"
     "c = GlobalMaxPooling1D()(c)\n"
     "\n"
     "# LSTM branch — cumulative effect of the weather sequence\n"
     "l = LSTM(64, return_sequences=True)(weather_in)\n"
     "l = Dropout(DROPOUT_RATE)(l)\n"
     "l = LSTM(32)(l)\n"
     "\n"
     "# Season injected AFTER extraction, immediately before the dense head.\n"
     "merged = Concatenate()([c, l, season_in])\n"
     "h = Dense(DENSE_UNITS, activation='relu')(merged)\n"
     "out = Dense(1)(h)\n"
     "\n"
     "model = Model([veg_in, weather_in, season_in], out)"),

    ("h2", "B.5 Mechanistic backbone of the physics-residual hybrid"),
    ("p",
     "The closed-form backbone of section 5.6. Only the two affine calibration "
     "parameters are estimated from data; the internal constants come from "
     "FAO-33 [31] and the degree-day literature [32]."),
    ("code",
     "Ky_water         = 1.1      # FAO-33 onion yield response factor\n"
     "SPI_deficit_scale = 2.0\n"
     "K_heat           = 0.03     # per stress day\n"
     "GDD_scale        = 1500.0   # thermal requirement\n"
     "\n"
     "f_gdd   = 1.0 - np.exp(-gdd / GDD_scale)\n"
     "f_water = np.clip(1.0 - Ky_water * np.clip(-spi / SPI_deficit_scale, 0, 1), 0, 1)\n"
     "f_heat  = np.clip(1.0 - K_heat * heat_stress_days, 0, 1)\n"
     "\n"
     "suitability = f_gdd * f_water * f_heat        # dimensionless, in [0, 1]\n"
     "\n"
     "# Two-parameter affine calibration, refitted inside every LOYO fold.\n"
     "backbone = a + b * suitability\n"
     "\n"
     "# Stage two: learn only what the physics does not explain.\n"
     "residual_model.fit(X_train, y_train - backbone_train)\n"
     "prediction = backbone_test + residual_model.predict(X_test)"),

    ("h2", "B.6 Simplex-constrained stacking"),
    ("p",
     "The convex combiner of section 5.7. Weights are non-negative [36] and sum "
     "to one, so the blend cannot leave the range of the base predictions."),
    ("code",
     "def fit_convex_weights(P_train, y_train):\n"
     "    \"\"\"P_train: (n_rows, n_models) out-of-fold base predictions.\"\"\"\n"
     "    n_models = P_train.shape[1]\n"
     "\n"
     "    def objective(w):\n"
     "        return np.mean((P_train @ w - y_train) ** 2)\n"
     "\n"
     "    constraints = [{'type': 'eq', 'fun': lambda w: w.sum() - 1.0}]\n"
     "    bounds = [(0.0, 1.0)] * n_models        # non-negativity\n"
     "    w0 = np.full(n_models, 1.0 / n_models)  # start at the equal-weight mean\n"
     "\n"
     "    result = minimize(objective, w0, bounds=bounds, constraints=constraints)\n"
     "    return result.x"),

    ("h2", "B.7 Split-conformal calibration"),
    ("p",
     "The interval construction of section 5.8, with the finite-sample "
     "correction required by split-conformal theory [39], [40]."),
    ("code",
     "def conformal_halfwidth(residuals, alpha=0.10):\n"
     "    \"\"\"Distribution-free interval half-width at (1 - alpha) coverage.\"\"\"\n"
     "    r = np.sort(np.abs(residuals))\n"
     "    n = len(r)\n"
     "    k = int(np.ceil((n + 1) * (1 - alpha))) - 1   # finite-sample correction\n"
     "    k = min(k, n - 1)\n"
     "    return float(r[k])\n"
     "\n"
     "# Applied symmetrically about the point forecast:\n"
     "#     lower = prediction - q,  upper = prediction + q"),
]


# ============================================================================
# Appendix C — Extended result tables
# ============================================================================

APPENDIX_C = [
    ("h1", "Appendix C"),
    ("h1", "Extended Result Tables"),
    ("p",
     "This appendix contains the fold-by-fold and full-ranking tables referred "
     "to in sections 7.4, 7.9 and 7.11."),

    ("h2", "C.1 Fold-by-fold predictions of the best model"),
    ("p",
     "Table C.1 gives every out-of-fold prediction made by the physics-residual "
     "hybrid, the model deployed by the system. Each row was predicted by a "
     "model fitted without any record from that row's year."),
    ("table", (
        ["Year", "District", "Actual (MT/Ha)", "Predicted (MT/Ha)", "Absolute error"],
        [
            ["2019", "Anuradhapura", "18.96", "16.09", "2.86"],
            ["2020", "Anuradhapura", "11.31", "15.90", "4.59"],
            ["2021", "Anuradhapura", "16.25", "14.79", "1.46"],
            ["2022", "Anuradhapura", "18.28", "17.32", "0.96"],
            ["2023", "Anuradhapura", "18.85", "18.39", "0.46"],
            ["2024", "Anuradhapura", "19.77", "19.21", "0.56"],
            ["2025", "Anuradhapura", "23.33", "18.98", "4.35"],
            ["2019", "Kurunegala", "17.86", "11.69", "6.17"],
            ["2020", "Kurunegala", "10.06", "16.26", "6.21"],
            ["2021", "Kurunegala", "15.15", "17.04", "1.89"],
            ["2022", "Kurunegala", "13.75", "12.02", "1.73"],
            ["2023", "Kurunegala", "12.20", "16.51", "4.31"],
            ["2024", "Kurunegala", "18.05", "15.34", "2.71"],
            ["2025", "Kurunegala", "15.84", "17.61", "1.76"],
            ["2019", "Matale", "15.77", "12.15", "3.62"],
            ["2020", "Matale", "13.91", "16.94", "3.02"],
            ["2021", "Matale", "13.83", "19.12", "5.29"],
            ["2022", "Matale", "9.02", "15.51", "6.50"],
            ["2023", "Matale", "17.28", "16.32", "0.96"],
            ["2024", "Matale", "23.22", "16.36", "6.85"],
            ["2025", "Matale", "23.40", "18.98", "4.43"],
            ["2019", "Polonnaruwa", "8.50", "14.30", "5.80"],
            ["2020", "Polonnaruwa", "15.66", "17.84", "2.17"],
            ["2021", "Polonnaruwa", "16.76", "17.43", "0.66"],
            ["2022", "Polonnaruwa", "13.39", "16.81", "3.42"],
            ["2023", "Polonnaruwa", "17.33", "12.25", "5.08"],
            ["2024", "Polonnaruwa", "24.06", "19.02", "5.04"],
            ["2025", "Polonnaruwa", "17.04", "17.98", "0.93"],
        ],
        "Table C.1: Fold-by-fold errors for the physics-residual hybrid",
    )),
    ("p",
     "The table makes the compression noted in section 7.4 visible directly. "
     "The actual values span 8.50 to 24.06 metric tons per hectare, while the "
     "predictions span only 11.69 to 19.21 — the model retreats towards the "
     "mean because the signal available to it does not justify committing to "
     "the extremes. The largest errors occur precisely at the extremes: the "
     "8.50 record in Polonnaruwa in 2019 is over-predicted by 5.80, and the "
     "23.22 record in Matale in 2024 is under-predicted by 6.85."),

    ("h2", "C.2 Per-fold aggregate errors"),
    ("p",
     "Table C.2 aggregates the same predictions by held-out year. The "
     "coefficient of determination is not reported per fold because each fold "
     "contains only four records drawn from a single year, within which the "
     "target variance is small; normalising by that variance produces unstable "
     "values that carry no information."),
    ("table", (
        ["Held-out year", "n", "Mean actual (MT/Ha)", "RMSE", "MAE"],
        [
            ["2019", "4", "15.27", "4.821", "4.613"],
            ["2020", "4", "12.74", "4.285", "3.999"],
            ["2021", "4", "15.50", "2.920", "2.326"],
            ["2022", "4", "13.61", "3.802", "3.151"],
            ["2023", "4", "16.42", "3.373", "2.701"],
            ["2024", "4", "21.27", "4.472", "3.791"],
            ["2025", "4", "19.90", "3.259", "2.868"],
        ],
        "Table C.2: Per-fold aggregate errors for the physics-residual hybrid",
    )),
    ("p",
     "The two hardest folds are 2019 and 2024. The 2019 fold is the first year "
     "of the record, so the yield-history predictors are least populated for "
     "it. The 2024 fold has the highest mean actual yield of any year at 21.27, "
     "which places it in the region where the model's mean-reverting behaviour "
     "costs most."),

    ("h2", "C.3 Full SHAP attribution ranking"),
    ("p",
     "Table C.3 gives the complete top-fifteen mean absolute SHAP attribution "
     "ranking summarised in section 7.11 and plotted in Figure 7.5."),
    ("table", (
        ["Rank", "Predictor", "Group", "Mean |SHAP|"],
        [
            ["1", "temp_x_humidity", "Interaction", "1.4040"],
            ["2", "season_mean_evi", "Satellite", "0.4841"],
            ["3", "drought_index_spi", "Weather", "0.1478"],
            ["4", "rainfall_x_ndvi", "Interaction", "0.1410"],
            ["5", "prev_year_yield", "Historical", "0.1234"],
            ["6", "temp_range", "Weather", "0.1194"],
            ["7", "season_mean_ndvi", "Satellite", "0.0867"],
            ["8", "max_daily_rainfall", "Weather", "0.0824"],
            ["9", "season_mean_lst_night", "Satellite", "0.0790"],
            ["10", "season_mean_lst_day", "Satellite", "0.0756"],
            ["11", "ndvi_anomaly", "Satellite", "0.0746"],
            ["12", "prev_season_yield", "Historical", "0.0732"],
            ["13", "ndvi_growth_rate", "Satellite", "0.0710"],
            ["14", "season_total_rainfall", "Weather", "0.0702"],
            ["15", "yield_3yr_avg", "Historical", "0.0640"],
        ],
        "Table C.3: Full SHAP attribution ranking",
    )),
    ("p",
     "The group column makes the composition of the ranking visible. Two of the "
     "three engineered interaction terms occupy ranks one and four; the "
     "satellite group supplies six of the fifteen; weather supplies four and "
     "yield history three. No soil predictor reaches the top fifteen, which "
     "sits oddly beside the ablation result in section 7.8 where soil alone was "
     "the strongest single source — and reinforces the reading given there that "
     "soil was acting as a district identifier rather than contributing "
     "agronomic signal."),
]


# ============================================================================
# Appendix D — Dashboard screenshots
# ============================================================================

APPENDIX_D = [
    ("h1", "Appendix D"),
    ("h1", "Dashboard Screenshots"),
    ("p",
     "This appendix contains screenshots of the decision-support dashboard "
     "described in sections 5.9 and 6.11, one per view, corresponding to the "
     "user groups of Table 4.1."),

    ("h2", "D.1 Overview and district choropleth"),
    ("p",
     "The landing view presents national and district key figures alongside a "
     "choropleth map of the four producing districts, shaded by forecast yield. "
     "This is the view used by policy analysts sizing import requirements."),
    ("ph", "Overview page with key figures and district choropleth"),

    ("h2", "D.2 Prediction view"),
    ("p",
     "The prediction view presents the context-prefilled input form described "
     "in section 4.6, together with the point forecast and its conformal "
     "interval. The interval is rendered with the same prominence as the point "
     "estimate, for the reason given in Appendix A."),
    ("ph", "Prediction form with context prefill, forecast and conformal interval"),

    ("h2", "D.3 Explainability view"),
    ("p",
     "The explainability view presents the SHAP attribution for the current "
     "prediction, the global attribution ranking of Table C.3, and the served "
     "symbolic equation of section 7.7. This is the view used by district "
     "agricultural officers who need a reason as well as a number."),
    ("ph", "Explainability page with SHAP attributions and the symbolic equation"),

    ("h2", "D.4 Recommendation view"),
    ("p",
     "The recommendation view translates the forecast and its leading drivers "
     "into plain-language guidance, so that the system's output is actionable "
     "without requiring the reader to interpret an attribution plot."),
    ("ph", "Recommendation page with plain-language guidance"),

    ("h2", "D.5 Administrative model-comparison panel"),
    ("p",
     "The administrative panel presents the full model comparison of Table 7.2 "
     "in sortable form, together with the conformal half-widths of Table 7.7. "
     "It is intended for technical users and researchers."),
    ("ph", "Admin panel with sortable model comparison table"),
]


ALL_APPENDICES = [APPENDIX_A, APPENDIX_B, APPENDIX_C, APPENDIX_D]
