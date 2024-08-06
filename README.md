# On the Reruns of GitHub Actions Workflows

This repository contains the code and the dataset of our paper "On the Reruns of GitHub Actions Workflows".

- **Part_1_Empirical** includes the source code for the empirical study on GitHub workflow reruns. (Section IV)
- **Part_2_Flakiness** contains the source code for the case study analyzing workflow execution flakiness. (Section V)
- **Part_3_ML-based_models** provides the implementation of ML-based models used for predicting workflow outcomes. (Section VI)
- **data** folder contains our dataset, which consists of the raw data of the repositories extracted from github, and the dataframes generated during our study.
- **plots** folder contains plots generated during the qualitative analysis conducted in our study.
- **tools** folder contains our self-implemented Python tools used in the study.

The Excel file "Flakiness in workflow&job reruns.xlsx" demonstrates the 100 workflow and job reruns that we manually analyzed in Section 5, "Flakiness of Workflow Executions." Note that by default, only three months of workflow run logs can be tracked on GitHub. As a result, most of the logs within the links shown in the file are now untraceable. However, similar symptoms can persist in the workflows' later executions.