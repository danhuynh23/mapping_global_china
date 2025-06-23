"""THIS CODE TESTS TIME RESPONSE AND OLLAMA RESPONSES.
IT DOESN’T TRANSFER AI-GENERATED INFO TO ANOTHER DOCUMENT,
IT ONLY PRINTS TO TERMINAL AND EXPORTS CSV OUTSIDE CONTAINER.
"""

import pandas as pd
import ollama
from tqdm import tqdm
import os
import requests

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(SCRIPT_DIR, "test_table.xlsx")
MODEL = "llama3:instruct"
SEARXNG_URL = "http://localhost:8888/search"  # Change port if needed
CSV_OUTPUT_PATH = "/scratch/dsh400/output/searx_results.csv"  # Outside container
searx_context_map = {}

# Load data
try:
    df = pd.read_excel(EXCEL_FILE)
    required_cols = ['Investor', 'Recipient', 'Recipient Country', 'Year', 'Sector', 'Amount (US$ mn)']
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Missing columns: {missing}")
except Exception as e:
    print(f"Error reading file: {e}")
    exit()


# Query SearxNG for context
def get_search_context(row):
    try:
        query = f"{row['Investor']} investment in {row['Recipient']} {row['Recipient Country']} {row['Year']} {row['Sector']}"
        params = {
            "q": query,
            "format": "json",
            "language": "en",
            "api": "1"
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; ollama-bot/1.0)"
        }
        response = requests.get(SEARXNG_URL, params=params, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"SearxNG HTTP error for row {row.name}: {response.status_code}")
            return None

        results = response.json().get("results", [])
        if not results or all(len(r.get("content", "")) < 50 for r in results):
            return None

        context = " | ".join([r.get("title", "") + ": " + r.get("content", "") for r in results[:3]])
        searx_context_map[row.name] = context  # <-- Save per row index
        return context.strip()

    except Exception as e:
        print(f"SearxNG error for row {row.name}: {e}")
        return None




# Generate prompt with optional context
def generate_investment_description(row):
    context = get_search_context(row)

    base_prompt = (
        f"Provide a brief description (max 5 lines) about the investment of {row['Investor']} in {row['Recipient']}, "
        f"{row['Recipient Country']} in {row['Year']} in the {row['Sector']} sector valued at "
        f"{row['Amount (US$ mn)']} million USD. Focus on key facts and significance. Use only factual information."
    )

    if not context:
        print(f"No Searx context for row {row.name}, generating from base prompt only.")
        full_prompt = base_prompt
    else:
        full_prompt = f"{context}\n\n{base_prompt}"

    try:
        response = ollama.generate(
            model=MODEL,
            prompt=full_prompt,
        )
        reply = response['response'].strip()
        if reply.lower().startswith("here is a brief description") or len(reply) < 30:
            print(f"Detected fallback response on row {row.name}, re-running with no context.")
            response = ollama.generate(
                model=MODEL,
                prompt=base_prompt,
            )
            reply = response['response'].strip()

        return reply.split('\n')[0].strip()
    except Exception as e:
        print(f"Error in row {row.name}: {e}")
        return None




# Main processing
print("Starting description generation...")
results = []
for idx, row in tqdm(df.iterrows(), total=min(10, len(df))):  # Limit to 10 rows
    description = generate_investment_description(row)
    df.at[idx, "Generated Description"] = description
    if description:
        print(f"\nRow {idx + 1}:")
        print(description)

context_out_path = os.path.join(SCRIPT_DIR, "searx_context_output.csv")
pd.DataFrame.from_dict(searx_context_map, orient='index', columns=["SearxNG Context"]).to_csv(context_out_path)
print(f"\nSaved SearxNG context output to {context_out_path}")

# Save to CSV outside the container
os.makedirs(os.path.dirname(CSV_OUTPUT_PATH), exist_ok=True)
df.to_csv(CSV_OUTPUT_PATH, index=False)
print(f"\nProcess completed! Results saved to: {CSV_OUTPUT_PATH}")
