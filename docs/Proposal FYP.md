

**Project Proposal**  
**Level 4**

**AI Powered Harvest Yield Prediction for Non-Cash Crops((Big Onion) in Sri Lanka** 

Group Name: Agro AI

Faculty of Information Technology  
University of Moratuwa   
2026

**Project Proposal**

**Level 4**

**AI Powered Harvest Yield Prediction for Non-Cash Crops((Big Onion) in Sri Lanka** 

Group Name: Agro AI

Group Members

| Index No | Name |
| :---- | :---- |
| 214019K | Arkam B.H.M. |
| 214192G | Sharuja B. |
| 214193K | Shathurya P. |

Supervisor: Dr.Firdhous M.F.M.

Faculty of Information Technology  
University of Moratuwa   
2026

**Contents**

Page

[**1\. Introduction	3**](#introduction)

[**2\. Background & Motivation	3**](#background-&-motivation)

[**3\. Problem in Brief	4**](#problem-in-brief)

[**4\. Aim & Objectives	5**](#aim-&-objectives)

[**5\. Proposed Solution	5**](#proposed-solution)

[**6\. Resource Requirements	7**](#resource-requirements)

[**7\. References	9**](#references)

[**8\. Appendix	9**](#appendix)

1. # **Introduction** {#introduction}

     
   Agriculture remains the backbone of Sri Lanka’s rural economy, directly influencing food security, employment generation, and national self-sufficiency targets. Among the non-cash crops cultivated across the island, big onion (Allium cepa) holds a strategically important position. Sri Lanka consumes approximately 200,000 \- 220,000 metric tons of big onion annually, yet domestic production covers only a fraction of this demand, with the balance met through costly imports that drain foreign exchange reserves.  
   Accurate and timely yield prediction for big onions is essential for agricultural planning, import \- export regulation, price stabilization, and disaster preparedness. However, current yield estimation methods for vegetable crops in Sri Lanka rely heavily on manual field surveys, consultation with agricultural officers, and post-harvest assessments. Unlike paddy, there is no systematic crop-cutting survey methodology established for big onions or other vegetables, making yield forecasting an exercise in educated guesswork rather than data-driven analysis.  
   This research addresses the problem of inaccurate and delayed paddy yield estimation by proposing an AI-powered harvest yield prediction system. The proposed solution integrates machine learning and deep learning techniques with weather data, satellite imagery, and historical yield records to provide a timely, scalable, and data-driven yield prediction framework.

2. # **Background & Motivation** {#background-&-motivation}

   Big onion (Allium cepa) is a vital horticultural crop in Sri Lanka, both economically and nutritionally. Introduced by the British in 1855, commercial cultivation expanded under the Department of Agriculture during the 1950s. Today, cultivation is concentrated in the Matale, Anuradhapura, Polonnaruwa, Puttalam, and Jaffna districts, with the Matale District \- particularly the Dambulla region- accounting for over 50% of national production and acting as the primary supply hub.  
     
   Big onion cultivation follows a seasonal pattern aligned with the country’s two monsoon-driven agricultural seasons. The Yala season (April–August) is the primary production period, benefiting from drier conditions in the intermediate and dry zones. In contrast, the Maha season (October–March) represents off-season cultivation, often in districts like Hambantota. Yield variation between seasons is substantial: peak-season yields in Matale average approximately 8,800 kg per acre, while off-season yields may drop to around 3,400 kg per acre due to unfavorable weather conditions.  
     
   Despite its importance, reliable yield forecasting for big onion faces significant challenges. Unlike paddy, which is surveyed systematically through crop-cutting surveys conducted by the Department of Census and Statistics (DCS) over 4,000 tracts per season, no equivalent structured methodology exists for horticultural crops. Yield estimates for highland crops are often based on consultations with agricultural officers or visual estimations, creating a large information gap. This methodological gap presents an opportunity for Artificial Intelligence (AI) and data-driven approaches that can leverage satellite imagery, climate records, and other alternative datasets to improve yield prediction.  
     
   The motivation for this research stems from:  
* The strategic economic importance of big onions and the government’s policy objective of achieving self-sufficiency in production.  
* The growing availability of open-source satellite data (e.g., MODIS, Sentinel-2) and climate datasets (e.g., NASA POWER, CHIRPS), along with accessible AI development tools, making data-driven yield prediction feasible and cost-effective.  
* Proven success of AI techniques in agricultural forecasting worldwide, including LSTM networks for time-series weather analysis and CNNs for spatial satellite image interpretation.  
* The absence of any existing AI-based yield prediction system specifically tailored for big onions in Sri Lanka, highlighting a clear research gap.  
* The availability of DCS special survey data for big onions in key districts (Matale, Anuradhapura, Polonnaruwa), providing ground-truth records for model training and validation.  
    
  This research is feasible due to the accessibility of open-source datasets, advanced AI tools, and the research team’s expertise in data analytics and machine learning. By addressing the lack of accurate, early-season, and scalable yield predictions for big onion, this study aims to support informed decision-making for farmers, policymakers, and supply chain stakeholders.

3. # **Problem in Brief** {#problem-in-brief}

   Current big onion yield estimation in Sri Lanka suffers from several fundamental limitations. Unlike paddy, there is no systematic methodology such as crop-cutting surveys for big onions, and yield estimates largely rely on subjective assessments by agricultural officers. This leads to inconsistent and often inaccurate predictions.  
     
   Moreover, yield and production information is typically available only during or after harvest, preventing farmers, policymakers, and import regulators from making proactive decisions. Traditional methods also fail to incorporate real-time environmental data, such as satellite-based vegetation observations, climate records, and soil conditions, all of which critically influence crop performance.  
     
   As a result, agricultural authorities face challenges in planning import restrictions to protect local farmers, while farmers lack early guidance on expected yields that could inform resource allocation, cultivation practices, and marketing strategies.  
     
   This project addresses these limitations by developing an AI-powered yield prediction system for big onions, capable of providing accurate, early-season forecasts across the major producing districts, thereby supporting timely and informed decision-making for all stakeholders.

4. # **Aim & Objectives** {#aim-&-objectives}

   **Aim**  
     
   The aim of this project is to design, develop, and evaluate an AI-powered system for predicting big onion harvest yield in the major producing districts of Sri Lanka (Matale, Anuradhapura, Polonnaruwa, and Jaffna) using machine learning, deep learning, and remote sensing technologies.  
     
   **Objectives**  
     
* To conduct a comprehensive study of big onion cultivation patterns, seasonal dynamics, and yield-influencing factors in Sri Lanka.  
* To collect, integrate, and preprocess multi-source datasets including historical yield records, weather data, satellite-derived vegetation indices, and soil characteristics.  
* To design and implement machine learning models (Random Forest, XGBoost, SVR) and deep learning models (LSTM, CNN) for yield prediction.  
* To evaluate and compare model accuracy using appropriate metrics (RMSE, MAE, R²) and validate predictions against actual DCS survey data.  
* To develop a visualization and decision-support interface that presents yield predictions as district-level spatial maps and seasonal forecasts.  
* To prepare comprehensive documentation and final project reporting.


5. # **Proposed Solution** {#proposed-solution}

   **5.1 AI-Based Big onions Yield Prediction System:**  
   The proposed solution is an intelligent yield prediction framework that combines multi-source agricultural data with state-of-the-art AI techniques to generate early-season big onion yield predictions for target districts. The system follows a modular architecture comprising four main components: data acquisition and integration, feature engineering, predictive modelling, and visualization and reporting.  
     
   **5.2 Technology Adopted:**

* Machine Learning: Random Forest, XGBoost, and Support Vector Regression (SVR) for baseline tabular prediction.  
* Deep Learning: Long Short-Term Memory (LSTM) networks for temporal weather and yield patterns; Convolutional Neural Networks (CNN) for spatial satellite imagery features.  
* Remote Sensing and Geospatial Analysis: Google Earth Engine for satellite data extraction; GeoPandas and Rasterio for spatial processing.  
* Python-based AI Ecosystem: Scikit-learn, TensorFlow/PyTorch, Pandas, NumPy for model development and data processing.


  **5.3 Data Sources**


| Data Type | Source | Details |
| :---- | :---- | :---- |
| Historical Yield Data | DCS Big Onion Survey Reports | District-level extent, production, and yield by season (Maha/Yala) for Matale, Anuradhapura, Polonnaruwa |
| National Production Data | FAOSTAT | Country-level onion production/yield from 1961 onwards |
| Weather Data | NASA POWER API | Daily rainfall, temperature (min/max), solar radiation, humidity for target coordinates |
| Rainfall Data | CHIRPS via Google Earth Engine | Gridded rainfall at 5km resolution |
| Vegetation Indices | MODIS (MOD13Q1) via GEE | NDVI, EVI at 250m resolution, 16-day composites |
| High-Resolution Imagery | Sentinel-2 via GEE | 10m multispectral imagery for NDVI, NDWI computation |
| Soil Data | SoilGrids (soilgrids.org) | Soil type, organic carbon, pH, texture at 250m |
| Agricultural Statistics | DOA AgStat Handbook | Cost of cultivation, extent, and production of vegetables |


  **5.4 System Pipeline**


  The system pipeline consists of the following stages:

  Stage 1 – Data Acquisition: Automated collection of satellite imagery via Google Earth Engine Python API, weather data via NASA POWER REST API, and manual collection of historical yield records from DCS publications.


  Stage 2 – Data Preprocessing: Cleaning, handling missing values, temporal alignment of multi-source data to match Maha/Yala cultivation seasons, and normalization.

  Stage 3 – Feature Engineering: Extraction of vegetation indices (NDVI, EVI, NDWI) from satellite imagery, computation of derived climate features (cumulative rainfall, growing degree days, drought indices), and integration of soil characteristics.

  Stage 4 – Model Training and Evaluation: Training of ML models (Random Forest, XGBoost, SVR) and DL models (LSTM, CNN) on the integrated feature set, with hyperparameter optimization and cross-validation.

  Stage 5 – Visualization and Reporting: Generation of district-level spatial yield prediction maps, seasonal comparison charts, and a decision-support dashboard for agricultural authorities.


  **5.5 Inputs, Outputs, and Users**


* Inputs: Weather data (rainfall, temperature, humidity, solar radiation), satellite vegetation indices (NDVI, EVI, NDWI), historical yield records, soil characteristics.  
* Outputs: Predicted big onion yield values (kg/ha) per district and season, spatial yield maps, confidence intervals, and season-over-season comparison reports.  
* Users: Department of Census and Statistics, Department of Agriculture, agricultural policy planners, district agricultural officers, and researchers.  
    
  **5.6 Feasibility**  
    
  The system is feasible due to the availability of free satellite data through Google Earth Engine, open-access climate data through NASA POWER, published big onion survey reports from DCS, and a mature open-source AI ecosystem in Python. The research team has the technical capability in data analytics, machine learning, and geospatial analysis required to design, implement, and evaluate the proposed system.


6. # **Resource Requirements** {#resource-requirements}

   Hardware Resources  
* Laptop/Desktop computers with minimum 16GB RAM and dedicated GPU (for deep learning model training).  
* GPU-enabled cloud computing (Google Colab Pro / AWS EC2 instances) for intensive model training.  
* External storage device (minimum 500GB) for satellite imagery and dataset storage.


  Software Resources

* Python programming language  
* Jupyter Notebook / Jupyter Lab  
* Anaconda / Conda environment  
* Scikit-learn  
* TensorFlow / PyTorch  
* GeoPandas  
* Rasterio  
* Matplotlib  
* Seaborn  
    
  Data Resources  
* Historical big onion yield datasets from DCS special surveys (2010–2025).  
* Weather and climate datasets from NASA POWER and CHIRPS.  
* Satellite imagery: MODIS MOD13Q1 (NDVI/EVI), Sentinel-2 (multispectral).  
* Soil data from SoilGrids and FAO Digital Soil Map.  
* Agricultural statistics from DOA AgStat Handbook and Central Bank Annual Reports.  
    
  Platforms and Services  
* Google Earth Engine (satellite data extraction and processing).  
* Google Colab Pro (GPU-accelerated model training).  
* Cloud storage (Google Drive / AWS S3) for dataset management.  
* GitHub (version control and collaboration).  
    
  Human Resources  
* Research supervisor: Dr. Firdhous M.F.M.  
* Academic journals and publications for literature review.  
* Department of Census and Statistics (for big onion survey data).  
* Department of Agriculture, Horticultural Crop Research and Development Institute (HORDI).  
* Sri Lanka Department of Meteorology (for supplementary weather data).

7. # **References** {#references}

   \[1\] FAO, Crop Yield Forecasting and Climate Risk Management, Food and Agriculture Organization of the United Nations, 2020\.

   \[2\] P. Kamilaris and F. X. Prenafeta-Boldú, “Deep learning in agriculture: A survey,” Computers and Electronics in Agriculture, vol. 147, pp. 70–90, 2018\.

   

   \[3\] MODIS Science Team, MODIS Vegetation Index User Guide, NASA, 2019\.

   

   \[4\] Department of Census and Statistics Sri Lanka, "Paddy Statistics and Big Onion Survey Reports," 2010–2025. Available: https://www.statistics.gov.lk

   

   \[5\] A. Amarasinghe et al., "Advancing food sustainability: a case study on improving rice yield prediction in Sri Lanka using weather-based, feature-engineered machine learning models," Discover Applied Sciences, vol. 6, 603, 2024\.

   

   \[6\] Department of Agriculture Sri Lanka, "HORDI Crop – Big Onion: Cultivation Guidelines," Available: [https://doa.gov.lk](https://doa.gov.lk)

   

   \[7\] M. Özdogan and X. Wang et al., "Field-Scale Rice Area and Yield Mapping in Sri Lanka with Optical Remote Sensing and Limited Training Data," World Bank Policy Research Working Paper, 2025\.

   

   \[8\] FAOSTAT, "Food and Agriculture Statistics – Crops and Livestock Products," Available: https://www.fao.org/faostat

   

   

   

   

   

   

   

   

   

   

   

   

   

   

   

   

8. # **Appendix** {#appendix}

   8.1 Plan of Action  
   

| Activity | Timeline |
| :---- | :---- |
| Literature review, requirement analysis, and identification of data sources | Weeks 1- 4 |
| Data acquisition including historical yield data, satellite imagery, and weather data collection | Weeks 5 \- 8 |
| Data preprocessing, feature engineering, and construction of integrated dataset | Weeks 7 \- 12 |
| Implementation of machine learning models (Random Forest, XGBoost, SVR) | Weeks 9 \- 12 |
| Development of deep learning models (LSTM, CNN) and model comparison | Weeks 11–16 |
| System integration, visualization development, and dashboard implementation | Weeks 13 \- 16 |
| Model evaluation, validation against DCS data, and result analysis | Weeks 15–18 |
| Final documentation, presentation preparation, and submission | Weeks 17–20 |

   

   						

   8.2 Individual Scope and Responsibilities

   

   Member 1: Arkam B.H.M. (214019K)  
   Role: Machine Learning, Deep Learning, and Modeling Research

   Arkam B.H.M. is responsible for the design, implementation, and evaluation of machine learning and deep learning models for big onion yield prediction. The technical scope includes developing baseline machine learning models such as Random Forest, XGBoost, and Support Vector Regression, followed by the implementation of advanced deep learning models including Long Short-Term Memory (LSTM) networks and Convolutional Neural Networks (CNN). The member will conduct model training, hyperparameter tuning, performance comparison, and evaluation using standard metrics such as RMSE, MAE, and R², with the objective of identifying the most accurate predictive model or ensemble.  
   	In addition to the implementation tasks, this role includes a significant research component focusing on the comparative analysis of machine learning and deep learning approaches in the context of agricultural yield prediction. This involves investigating the effectiveness of different algorithms when applied to multi-source agricultural datasets, as well as exploring hybrid modeling techniques that combine spatial and temporal features. The research further examines the impact of model optimization strategies, including hyperparameter tuning and ensemble learning, on prediction accuracy. The outcomes of this work will contribute to the model development and evaluation sections of the final report.

   

   Member 2: Sharuja B. (214192G)

   Role: Data Engineering, Feature Engineering, and Data-Centric Research

   Sharuja B. is responsible for the acquisition, integration, preprocessing, and management of multi-source datasets required for the yield prediction system. The technical responsibilities include collecting historical yield data, extracting satellite-derived vegetation indices (NDVI, EVI, NDWI) using Google Earth Engine, and obtaining weather and soil data from relevant sources. The member will perform data cleaning, handle missing values, and ensure temporal alignment of datasets according to cultivation seasons. Furthermore, this role involves designing and implementing feature engineering processes, including the computation of derived variables such as cumulative rainfall, growing degree days, and drought-related indices, ultimately constructing a unified dataset suitable for model training.

   The research contribution associated with this role focuses on understanding the influence of different data sources and engineered features on crop yield prediction accuracy. This includes analyzing the contribution of satellite-based vegetation indices, climatic variables, and soil characteristics to the predictive performance of the models. Additionally, the research investigates data quality challenges, such as missing values and inconsistencies across datasets, and evaluates methods for effective data preprocessing and integration. The findings will provide insights into feature importance and data-driven optimization strategies, contributing to the data methodology and analysis sections of the project.

   

   Member 3: Shathurya P. (214193K)

   Role: System Integration, Visualization, and Decision-Support Research

   Shathurya P. is responsible for the design and development of the system architecture, as well as the implementation of visualization and user interaction components of the yield prediction system. The technical scope includes developing an interactive dashboard that presents predicted yield values, spatial distribution maps, and seasonal comparisons using geospatial and visualization tools such as GeoPandas, Folium, and Plotly. This role also involves integrating the trained predictive models into the system backend, ensuring seamless data flow between components, and supporting end-to-end system functionality. Additionally, the member will participate in system validation, testing, and refinement to ensure accuracy and usability.

   The research component of this role focuses on the design and evaluation of decision-support systems in the agricultural domain. This includes studying effective visualization techniques for presenting complex AI-driven predictions to non-technical stakeholders, such as policymakers and agricultural officers. The research also explores how interactive dashboards and spatial visualizations can enhance decision-making processes. Furthermore, usability evaluation methods, including user testing and feedback analysis, will be applied to assess the effectiveness of the system interface. The outcomes of this research will contribute to the system design, visualization, and user evaluation sections of the final report.

   

   8.3 Expected Deliverables

   

* A trained and validated AI model (or ensemble) for big onion yield prediction achieving competitive accuracy (target R² \> 0.75).  
* An integrated multi-source dataset combining historical yield, weather, satellite, and soil data for the target districts.  
* District-level spatial yield prediction maps for both Maha and Yala seasons.  
* An interactive decision-support dashboard for agricultural authorities.  
* A comprehensive final project report with complete methodology, results, and analysis.  
* A project presentation and demonstration.  
    
  