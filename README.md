## Setup

```bash
git clone <https://github.com/annikaljy/dsa4264/>
cd dsa4264
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Place `DSA4264 Data/` folder in project root.

## Notebooks

**Run in order:**

1. `system_wide_analysis.ipynb`
2. `employable_degrees.ipynb`
3. `zoom_in_analysis.ipynb`

**Do NOT run (outputs saved to Google Drive):**
- `bertopic_combined.ipynb`
- `embeddings.ipynb`

## Web App
To run:
```bash
docker compose up --build
```
Once the containers are healthy, the services are available at:
- Frontend UI: http://localhost:3000
- Backend API: http://localhost:8000

To stop:
``` bash
docker compose down
```
Add -d to either command to run in the background.

## Technical Report

View at: [Report](https://annikaljy.github.io/dsa4264/)
