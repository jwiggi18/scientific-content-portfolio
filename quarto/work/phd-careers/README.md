# Life Sciences PhD Careers Project

## Overview

This project analyzes early career outcomes for life sciences PhD recipients, with a focus on employment sector and job activities (e.g., teaching vs research).

The goal is to understand how closely doctoral training aligns with actual career outcomes.

## Research Questions

- What jobs do life sciences PhDs hold within 10 years of graduation?
- What proportion of PhDs are in teaching-focused roles?
- How do actual career outcomes compare to initial post-graduation plans?


## Data Organization

- `raw/`: Original downloaded data files and documentation
- `processed/`: Cleaned datasets used for analysis
- `docs/`: Codebooks, questionnaires, and technical documentation

## Workflow

1. Download and store raw data in `raw/`
2. Clean and recode variables using scripts in `scripts/`
3. Save processed datasets in `processed/`
4. Generate figures in `outputs/figures/`
5. Display results in Quarto project pages

## Dependencies
- pandas
- openpyxl (required for reading Excel files)

## Notes and Limitations

- Job activity categories require interpretation and are self-reported (e.g., defining "teaching-heavy")
- SED captures intended outcomes, not actual employment
- Differences in survey design across datasets may affect comparability