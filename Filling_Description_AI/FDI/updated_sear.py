import pandas as pd
import ollama
import requests
from tqdm import tqdm
import os
import re
import json

# Settings
MODEL = "llama3:instruct"
SEARXNG_URL = "http://localhost:8888/search"
INPUT_FILE = "FDI_dataset.xlsx"
OUTPUT_FILE = "FDI_dataset_with_summaries.xlsx"
SEARX_CONTEXT_LOG = "searx_context_output.csv"

# Load data
try:
    df = pd.read_excel(INPUT_FILE)
    required_cols = ['Investor', 'Recipient', 'Recipient Country', 'Year', 'Sector', 'Amount (US$ mn)']
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Missing columns: {missing}")
except Exception as e:
    print(f"Error reading file: {e}")
    exit()

# Filter rows to only 'Tracker' data
tracker_df = df[df['Data Source'] == 'Tracker'].copy()
searx_context_map = {}

# SearxNG context fetcher
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
        searx_context_map[row.name] = context
        return context.strip()

    except Exception as e:
        print(f"SearxNG error for row {row.name}: {e}")
        return None

# Extract JSON block safely from a noisy reply
def extract_json(reply):
    try:
        match = re.search(r"\{.*\}", reply, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            raise ValueError("No JSON object found in reply")
    except Exception as e:
        raise ValueError(f"Failed to extract JSON: {e}")

# Generate values from Ollama
def generate_fields(row):
    context = get_search_context(row)
    base_prompt = (
        f"Provide a brief investment summary (max 5 lines), and identify the recipient type (e.g., government, private firm, SOE) and investment objective for the following deal:\n"
        f"Investor: {row['Investor']}\n"
        f"Recipient: {row['Recipient']}\n"
        f"Country: {row['Recipient Country']}\n"
        f"Year: {row['Year']}\n"
        f"Sector: {row['Sector']}\n"
        f"Amount: {row['Amount (US$ mn)']} million USD\n"
        f"Return JSON format with fields: summary, recipient_type, objective."
    )
    full_prompt = base_prompt if not context else f"{context}\n\n{base_prompt}"

    try:
        response = ollama.generate(model=MODEL, prompt=full_prompt)
        reply = response['response'].strip()
        try:
            parsed = extract_json(reply)
            return parsed.get("summary"), parsed.get("recipient_type"), parsed.get("objective")
        except Exception as parse_error:
            print(f"JSON parse error on row {row.name}: {parse_error}\nRaw reply: {reply}")
            return None, None, None
    except Exception as e:
        print(f"Error generating fields for row {row.name}: {e}")
        return None, None, None

# Main loop for rows with 'Tracker' only
print("Generating description, recipient type, and objective for 'Tracker' rows...")
for idx, row in tqdm(tracker_df.iterrows(), total=len(tracker_df)):
    summary, recipient_type, objective = generate_fields(row)
    df.at[idx, "Summary"] = summary
    df.at[idx, "Recipient Type"] = recipient_type
    df.at[idx, "Objective"] = objective

# Save outputs
pd.DataFrame.from_dict(searx_context_map, orient='index', columns=["SearxNG Context"]).to_csv(SEARX_CONTEXT_LOG)
df.to_excel(OUTPUT_FILE, index=False)
print(f"Descriptions saved to {OUTPUT_FILE}\nSearx context log saved to {SEARX_CONTEXT_LOG}")
