# Data Analysis

This directory contains data analysis scripts and notebooks for exploring GLP-1 medication outcomes from Reddit data.

## Structure

- `notebooks/` - Jupyter notebooks for interactive analysis
- `scripts/` - Python scripts for data processing and analysis
- `outputs/` - Generated charts, reports, and analysis results

## Setup

Analysis scripts use the same Python virtual environment as the data-ingestion app:

```bash
cd /Users/bryan/Github/which-glp
source venv/bin/activate
```

Required packages (already in requirements.txt):
- pandas
- numpy
- scipy
- statsmodels
- matplotlib
- seaborn
- psycopg2-binary
- python-dotenv
- jupyter

## Running Analyses

### Phase 1: Data Quality Assessment

```bash
cd /Users/bryan/Github/which-glp
python3 apps/data-analysis/scripts/data_quality_report.py
```

### Phase 2-5: Interactive Analysis

```bash
cd /Users/bryan/Github/which-glp
jupyter notebook apps/data-analysis/notebooks/glp1_trial_analysis.ipynb
```

## Analysis Plan

1. **Data Quality Assessment** - Assess completeness of extracted features
2. **Descriptive Statistics** - Weight loss by drug, timeframe, and starting weight
3. **Statistical Modeling** - Regression analysis with interaction terms
4. **Accessibility Analysis** - Insurance coverage and cost patterns
5. **Visualization & Reporting** - Charts and key findings summary
