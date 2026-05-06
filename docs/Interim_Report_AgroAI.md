

**Interim Report**

**Level 4**

**AI-Powered Harvest Yield Prediction**

**for Non-Cash Crops (Big Onion) in Sri Lanka**

Group Name: Agro AI

| 214019K | Arkam B.H.M. |
| :---: | :---- |
| 214192G | Sharuja B. |
| 214193K | Shathurya P. |

Supervised by: Dr. Firdhous M.F.M.

Faculty of Information Technology

University of Moratuwa

2026

**Abstract**

Agriculture remains the backbone of Sri Lanka’s rural economy, and big onion (Allium cepa) is a strategically important non-cash crop with an annual demand exceeding 200,000 metric tons. However, domestic production covers only a fraction of this demand, and no systematic yield estimation methodology exists for vegetable crops. This project addresses the problem of inaccurate and delayed big onion yield estimation by developing an AI-powered harvest yield prediction system.

The proposed system integrates multi-source data including historical yield records from the Department of Census and Statistics, satellite-derived vegetation indices (NDVI, EVI, NDWI) from MODIS and Sentinel-2 via Google Earth Engine, daily weather data from NASA POWER API, and soil characteristics from SoilGrids. The system targets four major big onion producing districts: Matale, Anuradhapura, Polonnaruwa, and Jaffna.

Machine learning models (Random Forest, XGBoost, SVR) and deep learning models (LSTM, CNN, hybrid CNN-LSTM) are implemented and compared for yield prediction accuracy. The system outputs predicted yield values per district and season, spatial yield maps, and confidence intervals through an interactive decision-support dashboard built with GeoPandas, Folium, and Plotly. Evaluation is conducted using RMSE, MAE, and R-squared metrics with Leave-One-Year-Out cross-validation. This interim report covers the literature survey, technology adaptation, system design, and early implementation progress.

**Table of Contents**

**List of Figures**

Figure 4.1 – High-Level System Architecture

Figure 4.2 – System Pipeline Stages

Figure 5.1 – Data Flow Diagram

Figure 5.2 – CNN-LSTM Hybrid Architecture

Figure 5.3 – Database Schema

**List of Tables**

Table 2.1 – Comparison of Existing Approaches

Table 3.1 – Data Sources and Details

Table 3.2 – Software and Tools

Table 5.1 – Feature Engineering Summary

Table 7.1 – Individual Contributions

# **Chapter 1 – Introduction**

## **1.1 Introduction**

Agriculture remains the backbone of Sri Lanka’s rural economy, directly influencing food security, employment generation, and national self-sufficiency targets. Among the non-cash crops cultivated across the island, big onion (Allium cepa) holds a strategically important position. Sri Lanka consumes approximately 200,000–220,000 metric tons of big onion annually, yet domestic production covers only a fraction of this demand, with the balance met through costly imports that drain foreign exchange reserves \[6\].

Accurate and timely yield prediction for big onion is essential for agricultural planning, import–export regulation, price stabilization, and disaster preparedness. However, current yield estimation methods for vegetable crops in Sri Lanka rely heavily on manual field surveys, consultation with agricultural officers, and post-harvest assessments \[4\]. Unlike paddy, there is no systematic crop-cutting survey methodology established for big onion or other vegetables, making yield forecasting an exercise in educated guesswork rather than data-driven analysis.

Recent advances in artificial intelligence, particularly machine learning (ML) and deep learning (DL), combined with the growing availability of satellite remote sensing data and open-access climate datasets, present an opportunity to develop cost-effective, data-driven yield prediction systems \[1, 2\]. This project addresses the problem of inaccurate and delayed big onion yield estimation by proposing an AI-powered harvest yield prediction system that integrates multi-source data for timely, scalable forecasts.

## **1.2 Background and Motivation**

Big onion cultivation in Sri Lanka is concentrated primarily in the Matale, Anuradhapura, Polonnaruwa, Puttalam, and Jaffna districts. The Matale District, particularly the Dambulla region, accounts for more than 50% of national big onion production \[6\]. Cultivation follows a seasonal pattern aligned with the country’s two monsoon-driven agricultural seasons: the Yala season (April–August) is the primary production period, while the Maha season (October–March) represents off-season cultivation. Yield variation between seasons is substantial, with peak-season yields in Matale averaging approximately 8,800 kg per acre compared to off-season yields of around 3,400 kg per acre \[4\].

The motivation for this research stems from several converging factors: the strategic economic importance of big onion and the government’s policy objective of achieving self-sufficiency; the growing availability of open-source satellite data (MODIS, Sentinel-2) and climate datasets (NASA POWER, CHIRPS); the proven success of AI techniques in agricultural forecasting globally \[1, 2, 3\]; the absence of any existing AI-based yield prediction system for big onion in Sri Lanka; and the availability of DCS special survey data for big onion in key districts \[4\].

## **1.3 Aim and Objectives**

**Aim:** To design, develop, and evaluate an AI-powered system for predicting big onion harvest yield in Matale, Anuradhapura, Polonnaruwa, and Jaffna districts using machine learning, deep learning, and remote sensing technologies.

The specific objectives of this project are:

* To conduct a comprehensive study of big onion cultivation patterns, seasonal dynamics, and yield-influencing factors in Sri Lanka.

* To collect, integrate, and preprocess multi-source datasets including historical yield records, weather data, satellite-derived vegetation indices, and soil characteristics.

* To design and implement machine learning models (Random Forest, XGBoost, SVR) and deep learning models (LSTM, CNN) for yield prediction.

* To evaluate and compare model accuracy using RMSE, MAE, and R², and validate predictions against actual DCS survey data.

* To develop a visualization and decision-support dashboard that presents yield predictions as district-level spatial maps and seasonal forecasts.

## **1.4 Proposed Solution Overview**

The proposed solution is an intelligent yield prediction framework comprising four main components: (1) an automated data pipeline that collects and integrates satellite imagery, weather data, historical yield records, and soil characteristics; (2) a feature engineering module that extracts vegetation indices, computes derived climate features, and constructs a unified training dataset; (3) a predictive modelling engine that trains and compares ML and DL models; and (4) a visualization dashboard that presents district-level spatial yield predictions to agricultural stakeholders.

## **1.5 Structure of the Report**

The remainder of this report is organized as follows. Chapter 2 presents a review of existing research on crop yield prediction using ML/DL approaches. Chapter 3 describes the technologies adopted for this project. Chapter 4 details the system design and architecture. Chapter 5 provides the analysis and design of the proposed solution. Chapter 6 reports on the early implementation progress. Chapter 7 discusses the current status, limitations, and further work.

## **1.6 Summary**

This chapter introduced the problem of inaccurate big onion yield estimation in Sri Lanka, the motivation for an AI-based approach, and the project’s aim and objectives. The next chapter reviews existing literature on crop yield prediction.

# **Chapter 2 – Crop Yield Prediction: State of the Art**

## **2.1 Introduction**

This chapter reviews existing research on crop yield prediction using machine learning and deep learning techniques. The review covers global approaches, Sri Lankan studies, onion-specific research, and identifies the research gaps that this project addresses.

## **2.2 Machine Learning Approaches for Crop Yield Prediction**

Machine learning has been widely applied to crop yield prediction globally. Jabed et al. \[1\] conducted a comprehensive review of 115 papers and found that Random Forest, Support Vector Machine, and Artificial Neural Networks are the most commonly used ML algorithms, with temperature, soil type, and vegetation as the most utilized features. The study highlighted that models with more attributes do not consistently perform better, and feature selection depends on dataset availability.

A comparative study by Springer \[3\] tested RF, CNN, GBM, and Decision Trees for potato, maize, and cotton yield prediction. Random Forest achieved R² of 0.875 for potatoes, while XGBoost showed the lowest error for cotton, demonstrating that model performance varies by crop type.

## **2.3 Deep Learning Approaches**

Deep learning methods, particularly LSTM and CNN, have shown promise for capturing temporal and spatial patterns in agricultural data. Wang et al. \[7\] compared LSTM with attention against XGBoost and Random Forest for maize yield in the US Corn Belt and found that the LSTM-attention model explained 73% of spatiotemporal variance, outperforming other approaches. A hybrid CNN-LSTM framework \[8\] achieved R² of 0.92 for crop yield prediction, outperforming standalone LSTM, CNN, Random Forest, and SVR models. NDVI, rainfall, and temperature were identified as the most influential features.

## **2.4 Crop Yield Prediction in Sri Lanka**

Research on AI-based crop yield prediction in Sri Lanka is limited and focuses exclusively on paddy. Amarasinghe et al. \[5\] used weather-based feature-engineered ML models for rice yield prediction in two Sri Lankan districts (1982–2019) and demonstrated that engineered climate features improve prediction accuracy. Wickramasinghe et al. \[10\] modeled the relationship between rice yield and climate variables using statistical and ML techniques. Herath et al. \[12\] extracted paddy phenological parameters using 16 years of MODIS NDVI time series data. However, no study has applied ML/DL to vegetable crop yield prediction in Sri Lanka.

## **2.5 Onion-Specific Research**

Published research on onion yield prediction is extremely limited globally. Iqbal et al. \[9\] developed OnionBangla, using Gradient Boosting, XGBoost, and Random Forest for onion yield prediction in Bangladesh with climate data, achieving 94% accuracy. However, this study used only weather-based tabular features without satellite data or deep learning. Kim and Soon \[11\] predicted onion bulb weight in Korea using the Neural Prophet model. In the Sri Lankan context, only onion price prediction has been attempted, with AR, LSTM, and Random Forest models applied to red onion prices in the Jaffna district \[14\].

## **2.6 Research Gaps Identified**

Based on the literature review, the following research gaps have been identified:

* No AI-based yield prediction system exists for any vegetable crop in Sri Lanka — all studies focus on paddy.

* No systematic yield estimation methodology for vegetables — DCS relies on eye estimation for big onion.

* Existing Sri Lankan studies use single data sources (weather only) — no multi-source fusion combining satellite, weather, soil, and historical yield data.

* No district-level spatial yield mapping for vegetables — current studies produce only national-level predictions.

* No ML vs. DL comparison for vegetable crops in tropical monsoon climates.

## **2.7 Comparison of Existing Approaches**

Table 2.1 summarizes the comparison of existing approaches and highlights how this project differs.

| Study | Crop | Country | Methods | Data Sources | Limitation |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Amarasinghe et al. \[5\] | Rice | Sri Lanka | RF, XGBoost | Weather only | No satellite, no DL, rice only |
| OnionBangla \[9\] | Onion | Bangladesh | RF, XGBoost, GB | Weather only | No satellite, no DL |
| Wang et al. \[7\] | Maize | USA | LSTM, XGBoost, RF | Weather \+ soil | No satellite indices |
| CNN-LSTM \[8\] | General | Global | CNN-LSTM hybrid | Satellite \+ weather | Cereal crops, temperate climate |
| This Project | Big Onion | Sri Lanka | RF, XGBoost, SVR, LSTM, CNN, CNN-LSTM | Satellite \+ weather \+ soil \+ historical yield | First for vegetable crop in Sri Lanka |

Table 2.1: Comparison of Existing Approaches

## **2.8 Summary**

This chapter reviewed existing crop yield prediction approaches and identified five key research gaps. No published study applies ML/DL to big onion yield prediction using multi-source data in Sri Lanka. The next chapter describes the technologies adopted to address these gaps.

# **Chapter 3 – Technologies Adopted for Big Onion Yield Prediction**

## **3.1 Introduction**

The previous chapter identified the research gaps in crop yield prediction for vegetable crops. This chapter describes the technologies adopted to address these gaps, covering data sources, machine learning and deep learning frameworks, remote sensing tools, and visualization technologies.

## **3.2 Data Sources and Collection Technologies**

The system integrates data from multiple sources as summarized in Table 3.1.

| Data Type | Source | Resolution/Details | Access Method |
| :---- | :---- | :---- | :---- |
| Historical Yield | DCS Big Onion Surveys | District-level, by season | PDF reports from statistics.gov.lk |
| National Production | FAOSTAT | Country-level, 1961–present | CSV download from fao.org/faostat |
| Weather Data | NASA POWER API | 0.5° grid, daily | Free REST API, no key required |
| Rainfall | CHIRPS via GEE | 5km, daily | Google Earth Engine |
| Vegetation Indices | MODIS MOD13Q1 via GEE | 250m, 16-day composites | Google Earth Engine |
| High-Res Imagery | Sentinel-2 via GEE | 10m multispectral | Google Earth Engine |
| Soil Data | SoilGrids | 250m, static | REST API from rest.isric.org |
| Land Surface Temp | MODIS LST via GEE | 1km, 8-day | Google Earth Engine |

Table 3.1: Data Sources and Details

## **3.3 Machine Learning Technologies**

Three machine learning algorithms are employed as baseline models. Random Forest is a bagging ensemble method that handles noisy agricultural data and provides feature importance rankings \[1\]. XGBoost is a gradient boosting method that achieves high accuracy on structured tabular data through regularization and second-order optimization \[3\]. Support Vector Regression uses kernel functions to model non-linear relationships between weather variables and yield.

## **3.4 Deep Learning Technologies**

Long Short-Term Memory (LSTM) networks are used to capture temporal dependencies in weather time-series data over the growing season. LSTM’s gating mechanism (forget, input, output gates) enables the model to selectively retain important information across the 4–5 month cultivation period \[7\]. Convolutional Neural Networks (CNN) are used to extract spatial features from satellite-derived vegetation index maps, detecting spatial patterns in crop health across districts \[8\]. A hybrid CNN-LSTM architecture is designed to fuse spatial satellite features with temporal weather patterns for improved prediction accuracy.

## **3.5 Remote Sensing and Geospatial Technologies**

Google Earth Engine provides planetary-scale analysis of satellite data. The project uses the GEE JavaScript API in the Code Editor and the Python API (earthengine-api) for automated data extraction \[12\]. Vegetation indices computed include NDVI (Normalized Difference Vegetation Index), EVI (Enhanced Vegetation Index), and NDWI (Normalized Difference Water Index). GeoPandas, Rasterio, and Folium are used for spatial processing and visualization.

## **3.6 Software and Tools**

| Category | Tools |
| :---- | :---- |
| Programming Language | Python 3.10+ |
| ML Libraries | Scikit-learn, XGBoost |
| DL Frameworks | TensorFlow / Keras |
| Geospatial | GeoPandas, Rasterio, Folium, Shapely |
| Satellite Data | Google Earth Engine Python/JS API |
| Data Processing | Pandas, NumPy, SciPy |
| Visualization | Matplotlib, Seaborn, Plotly |
| Interpretability | SHAP (SHapley Additive exPlanations) |
| Web Framework | Flask / FastAPI |
| Frontend | React / Next.js |
| Version Control | Git and GitHub |

Table 3.2: Software and Tools

## **3.7 Summary**

This chapter described the technologies adopted for the project, covering data sources, ML/DL algorithms, remote sensing tools, and software frameworks. These technologies are appropriate because they are freely available, well-documented, and have been proven effective in agricultural yield prediction research \[1, 5, 8\]. The next chapter presents the system design and architecture.

# **Chapter 4 – AI-Powered Big Onion Yield Prediction: System Approach**

## **4.1 Introduction**

The previous chapter described the technologies adopted for the project. This chapter presents how these technologies are applied to solve the big onion yield prediction problem, describing the system approach in terms of users, inputs, outputs, and the processing pipeline.

## **4.2 Users**

The system targets four primary user groups: (1) Department of Census and Statistics officers who require yield estimates for national statistics; (2) Department of Agriculture policy planners who regulate big onion imports; (3) district agricultural officers who advise farmers on cultivation planning; and (4) agricultural researchers studying crop-climate relationships.

## **4.3 Inputs and Outputs**

**Inputs:** Weather data (rainfall, temperature, humidity, solar radiation) from NASA POWER API; satellite vegetation indices (NDVI, EVI, NDWI) from MODIS and Sentinel-2 via Google Earth Engine; historical yield records from DCS big onion survey reports; soil characteristics (pH, organic carbon, clay percentage) from SoilGrids.

**Outputs:** Predicted big onion yield values (MT/ha) per district and season; district-level spatial yield prediction maps; confidence intervals for predictions; season-over-season comparison reports; model performance metrics dashboard.

## **4.4 System Pipeline**

The system follows a five-stage pipeline as described below. Figure 4.2 illustrates the flow between stages.

**Stage 1 – Data Acquisition:** Automated collection of satellite imagery via Google Earth Engine Python API, weather data via NASA POWER REST API, and manual collection of historical yield records from DCS publications.

**Stage 2 – Data Preprocessing:** Cleaning, handling missing values, temporal alignment of multi-source data to match Maha/Yala cultivation seasons, and normalization.

**Stage 3 – Feature Engineering:** Extraction of vegetation indices from satellite imagery, computation of derived climate features (cumulative rainfall, growing degree days, drought indices), and integration of soil characteristics.

**Stage 4 – Model Training and Evaluation:** Training of ML models (Random Forest, XGBoost, SVR) and DL models (LSTM, CNN, hybrid CNN-LSTM) on the integrated feature set, with hyperparameter optimization and cross-validation.

**Stage 5 – Visualization and Reporting:** Development of an interactive decision-support dashboard with yield prediction outputs, SHAP-based feature explanation visualizations, district-level spatial yield maps, and seasonal comparison charts.

## **4.5 High-Level System Architecture**

Figure 4.1 shows the high-level architecture of the proposed system, which comprises three main modules: (1) Data Pipeline Module (Sharuja B.) responsible for data acquisition, preprocessing, and feature engineering; (2) ML/DL Prediction Module (Arkam B.H.M.) responsible for model training, evaluation, and API serving; and (3) Visualization and Dashboard Module (Shathurya P.) responsible for spatial mapping, dashboard development, and user-facing interfaces.

\[Figure 4.1: High-Level System Architecture – to be inserted\]

## **4.6 Summary**

This chapter presented the system approach including users, inputs, outputs, and the five-stage processing pipeline. The next chapter provides detailed analysis and design of each module.

# **Chapter 5 – Analysis and Design of the Yield Prediction System**

## **5.1 Introduction**

This chapter provides the detailed analysis and design of the proposed yield prediction system. It covers the data flow design, feature engineering strategy, model architectures, and the dashboard design.

## **5.2 Data Flow Design**

Figure 5.1 shows the data flow diagram of the system. Data flows from four external sources through the automated pipeline into a PostgreSQL database, which feeds the ML/DL models. Model predictions are served via a REST API to the frontend dashboard.

\[Figure 5.1: Data Flow Diagram – to be inserted\]

## **5.3 Feature Engineering Design**

Table 5.1 summarizes the features engineered from each data source.

| Category | Features | Source |
| :---- | :---- | :---- |
| Weather | Season avg temp, total rainfall, avg humidity, solar radiation, growing degree days, heat stress days, drought index (SPI), temp range | NASA POWER |
| Satellite | Season mean/max/min NDVI, NDVI std, NDVI anomaly, time-to-peak NDVI, NDVI growth rate, mean EVI, mean NDWI | MODIS, Sentinel-2 |
| Historical | Previous season yield, previous year yield, 3-year moving average, season indicator (Yala=1, Maha=0) | DCS Surveys |
| Soil | Soil pH, organic carbon, clay percentage, sand percentage | SoilGrids |
| Interaction | Rainfall × NDVI, temperature × humidity | Derived |

Table 5.1: Feature Engineering Summary

## **5.4 ML Model Design (Arkam B.H.M.)**

Three ML models are designed with the following hyperparameter search spaces:

**Random Forest:** n\_estimators \[100, 200, 500\], max\_depth \[5, 10, 20, None\], min\_samples\_split \[2, 5, 10\]. Evaluated using GridSearchCV with Leave-One-Year-Out cross-validation.

**XGBoost:** learning\_rate \[0.01, 0.05, 0.1\], max\_depth \[3, 5, 7\], n\_estimators \[100, 300, 500\], subsample \[0.7, 0.8, 1.0\], reg\_alpha \[0, 0.1, 1\].

**SVR:** kernel \[rbf, linear, poly\], C \[0.1, 1, 10, 100\], gamma \[scale, auto, 0.01, 0.1\].

## **5.5 DL Model Design (Arkam B.H.M.)**

The LSTM architecture consists of 2 LSTM layers (64 and 32 units), a Dropout layer (rate 0.2), a Dense layer (16 units, ReLU activation), and an output Dense layer (1 unit). Input shape is (5, N) representing 5 months of N weather features. The model uses Adam optimizer with learning rate 0.001 and ReduceLROnPlateau scheduling.

The hybrid CNN-LSTM architecture (Figure 5.2) comprises two parallel branches: a CNN branch that processes season-aggregated satellite index features through Conv1D layers to extract spatial patterns, and an LSTM branch that processes monthly weather sequences to capture temporal dependencies. Both branch outputs are concatenated and fed through fully connected layers for final yield prediction.

\[Figure 5.2: CNN-LSTM Hybrid Architecture – to be inserted\]

## **5.6 Data Pipeline Design (Sharuja B.)**

The automated data pipeline connects to Google Earth Engine API for satellite data extraction, NASA POWER API for weather data retrieval, and processes DCS survey reports. Extracted data is stored in a PostgreSQL database with a schema designed for temporal alignment by district, year, and season (Figure 5.3). The pipeline includes automated feature engineering, data validation checks, and scheduled execution via cron jobs.

\[Figure 5.3: Database Schema – to be inserted\]

## **5.7 Dashboard Design (Shathurya P.)**

The web dashboard is developed using a React/Next.js frontend integrated with a Flask/FastAPI backend. The interface includes a district selection module for Matale, Anuradhapura, Polonnaruwa, and Jaffna, along with a season selector for Yala and Maha cultivation periods. A prediction panel displays the estimated crop yield along with associated confidence levels.

Visualization components include a district-level choropleth map implemented using Leaflet/Mapbox, and interactive charts for seasonal yield comparisons. The system also integrates Explainable AI (XAI) using SHAP to present feature-level contributions, enabling users to understand how each input variable influences the final prediction. Additionally, an administrative panel is provided to display model performance metrics and feature importance analysis for interpretability and monitoring purposes.

## **5.8 Summary**

This chapter provided the detailed analysis and design of all system components including feature engineering, ML/DL model architectures, the data pipeline, and the dashboard. The next chapter reports on early implementation progress.

# **Chapter 6 – Early Implementation Progress**

## **6.1 Introduction**

This chapter reports on the implementation progress achieved during the first half of the project period, covering data collection, preprocessing, and initial model development.

## **6.2 Data Collection Progress**

Historical yield data has been collected from DCS big onion survey reports for the period 2004–2023, covering four districts across both Yala and Maha seasons. FAOSTAT national-level onion production data has been downloaded for the period 2000–2023. A Google Earth Engine JavaScript script has been developed and tested to extract MODIS NDVI/EVI time series, Sentinel-2 NDVI/NDWI monthly composites, CHIRPS rainfall aggregates, MODIS Land Surface Temperature, and SMAP soil moisture data for all target districts. NASA POWER API weather data has been retrieved for all four district coordinates.

## **6.3 Data Preprocessing Progress**

Multi-source data has been merged into a unified dataset aligned by district, year, and season. Missing value handling has been implemented using temporal interpolation for satellite indices and forward-fill for weather gaps. Cloud-contaminated satellite pixels have been masked using MODIS QA bands and Sentinel-2 Scene Classification Layer. Seasonal aggregation has been completed, converting monthly data to Yala-season (April–August) and Maha-season (October–March) averages.

## **6.4 Initial Model Development**

Baseline Random Forest and XGBoost models have been implemented and tested on the integrated dataset. Preliminary results show R² values in the range of 0.55–0.70 before hyperparameter tuning, indicating that the multi-source features contain predictive information. LSTM model architecture has been defined and initial training experiments conducted. Feature importance analysis using XGBoost built-in importance suggests that cumulative rainfall, season-mean NDVI, and previous-season yield are the top predictive features.

## **6.5 Summary**

Data collection and preprocessing are substantially complete. Initial ML models show promising preliminary results. The next phase focuses on deep learning model implementation, hyperparameter tuning, ensemble methods, and dashboard development.

# **Chapter 7 – Discussion and Further Work**

## **7.1 Introduction**

This chapter discusses the current status, how the proposed solution differs from existing work, challenges encountered, and the plan for the remaining project period.

## **7.2 How This Work Differs from Others**

This project differs from existing work in five key ways. First, it is the first AI-powered yield prediction system for big onion in South Asia. Second, it integrates four data streams (satellite, weather, soil, historical yield) that have never been combined for a vegetable crop. Third, it provides a systematic ML vs. DL comparison for vegetable yield prediction with scarce data. Fourth, it produces district-level spatial predictions rather than national aggregates. Fifth, it addresses an institutional gap by providing a cost-effective alternative to manual yield estimation for vegetables.

## **7.3 Challenges Encountered**

The primary challenge is data scarcity — only approximately 160 data points are available (4 districts × 2 seasons × 20 years). This limits deep learning model complexity and requires careful regularization. Additionally, DCS big onion survey data is published as PDF reports, requiring manual extraction into structured formats. Cloud contamination in satellite imagery creates gaps that require temporal interpolation.

## **7.4 Further Work Plan**

The remaining work for the second half of the project includes:

* Complete LSTM, CNN, and hybrid CNN-LSTM model implementation and hyperparameter tuning.

* Conduct comprehensive ML vs. DL model comparison with statistical significance testing.

* Perform SHAP-based feature importance analysis and ablation study.

* Implement stacking ensemble combining best ML and DL models.

* Develop the Flask/FastAPI backend API for model serving.

* Build the React/Next.js frontend dashboard with spatial visualization.

* Conduct spatial error analysis and early prediction feasibility study.

* Perform user testing with agricultural stakeholders.

* Prepare final documentation and project demonstration.

## **7.5 Summary**

This project has made significant progress in data collection, preprocessing, and initial model development. The multi-source data integration framework is operational, and preliminary ML results are promising. The remaining work focuses on DL model development, ensemble methods, dashboard implementation, and comprehensive evaluation.

# **References**

\[1\] M. A. Jabed et al., “Crop yield prediction in agriculture: A comprehensive review of ML and DL approaches, with insights for future research,” Heliyon, vol. 10, no. 24, e40836, 2024\.

\[2\] A. Kamilaris and F. X. Prenafeta-Boldú, “Deep learning in agriculture: A survey,” Computers and Electronics in Agriculture, vol. 147, pp. 70–90, 2018\.

\[3\] F. Chikwendu et al., “A comparative study of machine learning models in predicting crop yield,” Discover Agriculture, Springer, 2025\.

\[4\] Department of Census and Statistics Sri Lanka, “Big Onion Survey Reports,” 2010–2025. Available: https://www.statistics.gov.lk

\[5\] A. Amarasinghe et al., “Advancing food sustainability: rice yield prediction in Sri Lanka using weather-based, feature-engineered ML models,” Discover Applied Sciences, vol. 6, 603, 2024\.

\[6\] Department of Agriculture Sri Lanka, “HORDI Crop – Big Onion: Cultivation Guidelines,” Available: https://doa.gov.lk

\[7\] Z. Wang et al., “Machine Learning Crop Yield Models Based on Meteorological Features and Comparison with a Process-Based Model,” Artificial Intelligence for the Earth Systems, vol. 1, no. 4, 2022\.

\[8\] S. Rajpoot and O. Chandrakar, "A hybrid CNN-LSTM deep learning framework for enhanced crop yield prediction using spatial-temporal agricultural data," Int. J. Statistics and Applied Mathematics, vol. SP-10, no. 12, pp. 1–9, 2025\.

doi: 10.22271/maths.2025.v10.i12Sa.2200

\[9\] D. M. Iqbal et al., “OnionBangla: A Supervised ML Approach for Predicting Onion Yield using Bangladeshi Climate Data,” in Proc. IEEE ICCCI, 2023\.

\[10\] L. Wickramasinghe et al., “Modeling the relationship between rice yield and climate variables using statistical and ML techniques,” J. Mathematics, 2021\.

\[11\] W. Kim and B. M. Soon, “Advancing Agricultural Predictions: A Deep Learning Approach to Estimating Bulb Weight Using Neural Prophet Model,” Agronomy, vol. 13, no. 5, 2023\.

\[12\] K. Herath et al., “Extraction of Agricultural Phenological Parameters of Sri Lanka Using MODIS NDVI Time Series Data,” Procedia Food Science, vol. 6, 2016\.

\[13\] FAOSTAT, “Food and Agriculture Statistics – Crops and Livestock Products,” Available: https://www.fao.org/faostat

\[14\] “Red onion price factors correlation identification and price prediction using multiple ML models for Jaffna district Sri Lanka,” in Proc. IEEE Conf., 2023\.

\[15\] MODIS Science Team, “MODIS Vegetation Index User Guide,” NASA, 2019\.

# **Appendix A – Individual’s Contribution to the Project**

## **Arkam B.H.M. (214019K)**

My individual contribution to the project focuses on the Machine Learning, Deep Learning, and Modelling Research component. During the first half of the project, I conducted a comprehensive literature review covering over 20 research papers on ML/DL approaches for crop yield prediction, identifying the key research gaps that our project addresses. I implemented baseline machine learning models including Random Forest, XGBoost, and SVR using scikit-learn and xgboost libraries, achieving preliminary R² values of 0.55–0.70 on the integrated dataset.

I designed the LSTM architecture (2 layers, 64/32 units) and began initial training experiments with weather time-series data. I also designed the hybrid CNN-LSTM architecture for spatial-temporal feature fusion. Key challenges I encountered include preventing overfitting with limited training data, which I addressed by using shallow architectures, dropout regularization, and Leave-One-Year-Out cross-validation. I learned that for small agricultural datasets, feature engineering is often more impactful than model complexity. My remaining work includes completing the DL model implementation, conducting the ML vs. DL comparative analysis, performing SHAP-based feature importance analysis, and building the Flask/FastAPI backend API for model serving.

## **Sharuja B. (214192G)**

My individual contribution focuses on Data Engineering, Feature Engineering, and Data-Centric Research. During the first half, I collected historical big onion yield data from DCS survey reports (2004–2023) by manually extracting tables from PDF publications into structured CSV format. I developed a Google Earth Engine JavaScript script that automates extraction of MODIS NDVI/EVI time series, Sentinel-2 indices, CHIRPS rainfall, MODIS LST, and SMAP soil moisture for all four target districts.

I implemented the NASA POWER API data retrieval pipeline using Python requests library for all district coordinates, and collected soil data from SoilGrids REST API. I designed and executed the data preprocessing workflow including temporal alignment to Maha/Yala seasons, cloud masking for satellite data, missing value imputation, and normalization. I engineered over 25 derived features including growing degree days, cumulative rainfall, NDVI anomaly, and season-integrated vegetation indices. A key challenge was aligning data from different temporal resolutions (daily weather, 16-day satellite, seasonal yield). My remaining work includes the NDVI vs. EVI vs. NDWI comparison study, growth stage analysis, MODIS vs. Sentinel-2 resolution comparison, and building the automated database pipeline.

## **Shathurya P. (214193K)**

My individual contribution focuses on System Integration, Visualization, and Decision-Support Research. During the first half, I designed the overall system architecture defining the interaction between the data pipeline, ML/DL model engine, and visualization dashboard. I created wireframes for the interactive dashboard and began prototyping the frontend using React with Leaflet for choropleth mapping.

I conducted preliminary spatial analysis of prediction results using GeoPandas and Folium, generating district-level test visualizations for Matale, Anuradhapura, and Polonnaruwa. I also researched ensemble fusion strategies (stacking, weighted averaging, blending) for combining outputs from multiple models. A key challenge was designing a dashboard interface that presents complex AI predictions in a way accessible to non-technical agricultural stakeholders. My remaining work includes completing the React/Next.js dashboard, implementing the stacking ensemble model, conducting spatial error analysis, performing early prediction feasibility analysis, deploying the system to the cloud, and conducting user testing with 5–10 participants.