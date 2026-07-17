# Phone_pay-data-analysis_Guvi
Phone_pay  Insights
# PhonePe Pulse Analytics & Market Intelligence Pipeline 📊📱

A comprehensive, production-ready data engineering and business intelligence platform designed to process, model, and visualize PhonePe's transactional, user, and insurance ecosystems. This pipeline transforms multi-dimensional data from the PhonePe Pulse repository into optimized relational database structures to drive strategic business decisions.

---

## 🏗️ System Architecture & Data Flow

## 🗄️ Database Architecture & Schema Design

The extracted data is organized into three analytical granularities (Aggregated, Map, and Top) and stored inside a relational database system (MySQL/PostgreSQL):

### 1. Aggregated Tables
*   **`Aggregated_user`**: Holds time-series aggregated user-related data, tracking user growth and engagement over years and quarters.
*   **`Aggregated_transaction`**: Contains macro-level aggregated transactional metrics, summarizing total counts and monetary values across distinct payment categories.
*   **`Aggregated_insurance`**: Stores summarized insurance-focused metrics to monitor aggregate policy volume and premium distributions.

### 2. Map Tables
*   **`Map_user`**: Houses geo-spatial user mapping information, linking subscriber footprints explicitly to localized territorial units.
*   **`Map_map`**: Holds spatial mapping matrices detailing total transaction values and volumes explicitly cross-referenced at State and District levels.
*   **`Map_insurance`**: Includes geo-spatial mapping configurations tracking the absolute volume and scale of insurance coverage adoption across administrative borders.

### 3. Top Tables
*   **`Top_user`**: Tracks user leaderboards, identifying highest-density user concentrations across temporal slices.
*   **`Top_map`**: Contains transaction and user totals for peak-performing geographic intersections, ranking the top-performing States, Districts, and PIN codes.
*   **`Top_insurance`**: Lists competitive ranking totals and breakdowns across leading insurance categories and localized distribution hotspots.

---

## 🛠️ Tech Stack & Dependencies

*   **Database Management:** MySQL / PostgreSQL
*   **Data Processing & ETL:** Python 3.10+, Pandas, SQLAlchemy
*   **Dashboard Application:** Streamlit
*   **Data Source:** [PhonePe Pulse Data Repository](https://github.com)

---

## ⚙️ Pipeline Execution Blueprint

### Step 1: Clone and Extract Data
The ingestion script automatically forks or clones the official data repository and reads the deep nested directory tree structure containing the localized JSON files.

### Step 2: Database Setup & Migration
Execute your database setup scripts to initialize the structural tables. Below is a sample migration outline for the relational engine:

```sql
-- Example Schema for Aggregated Transaction Data
CREATE TABLE Aggregated_transaction (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state VARCHAR(100),
    year INT,
    quarter INT,
    transaction_type VARCHAR(100),
    transaction_count BIGINT,
    transaction_amount DOUBLE
);
```

### Step 3: Run the Ingestion Pipeline
Execute the main ingestion pipeline to parse the nested JSON documents, clean data types, calculate derived KPIs, and stream the clean data frames into your relational database:

```bash
python src/pipeline_etl.py
```

### Step 4: Launch the Streamlit
Once the database pipelines are filled, boot up the interactive analytical engine layer:

```bash
streamlit run app.py
```

---
