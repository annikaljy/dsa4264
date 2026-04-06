# MOE Course–Career Alignment Tool

Paste any job ad (MyCareersFuture link or raw text) → get the top 10 most relevant NUS degree programmes and modules instantly.

**No jobs dataset needed** — matching is done purely by cosine similarity between the job description and your pre-computed module embeddings.

---

## How it works

```
Job ad text
    ↓  MPNet embed  (all-mpnet-base-v2)
Job vector (768-dim)
    ↓  cosine similarity
vs every module vector in all_nus_modules_embedded.parquet
    ↓  aggregate by course (avg + max similarity)
Top 10 degree programmes + top 10 individual modules
```

---

## Project structure

```
moe_app/
├── docker-compose.yml
├── README.md
├── data/                          ← PUT YOUR FILES HERE
│   └── all_nus_modules_embedded.parquet
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── index.html
    └── Dockerfile
```

---

## Step 1 — Add your data

Copy **one file** from your Colab into `moe_app/data/`:

```
data/
└── all_nus_modules_embedded.parquet    ← from Cell 8 of your notebook
```

That's it. No jobs parquet, no BERTopic model needed.

---

## Step 2 — Run

```bash
cd moe_app
docker compose up --build
```

First build: ~5–8 min (downloads Python packages + PyTorch).
Subsequent starts: ~30 seconds (model loads into memory).

---

## Step 3 — Open

Frontend: **http://localhost:3000**
API health: http://localhost:8000/health

---

## Usage

### Paste MCF Link
Copy any URL from https://www.mycareersfuture.gov.sg and paste it in.
The backend calls the MCF public API to extract the job title, description and skills.

### Paste Job Text
Switch to the "Paste Job Text" tab and paste the description directly.
Useful for jobs from LinkedIn, company websites, or any non-MCF source.

---

## Adding SMU / SUTD modules

Run Cells 7–8 of your notebook against an SMU/SUTD module CSV, then concatenate:

```python
import pandas as pd
nus  = pd.read_parquet("all_nus_modules_embedded.parquet")
smu  = pd.read_parquet("smu_modules_embedded.parquet")
sutd = pd.read_parquet("sutd_modules_embedded.parquet")
combined = pd.concat([nus, smu, sutd], ignore_index=True)
combined.to_parquet("data/all_nus_modules_embedded.parquet")
```

Then restart: `docker compose restart backend`

---

## Stop

```bash
docker compose down
```
