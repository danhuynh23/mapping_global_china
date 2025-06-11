"""THIS CODE CALLS THE GEMINI AI TO SEND IT A PROMPT USING THE
INFORMATION OF THE COLUMNS OF THE 'test_table' DOCUMENT AND PUT THE RESULTS
OF THE AI IN THE COLUMN 'DESCRIPTION', IMPORTING TO A DOCUMENT CALLED
'test_table_with_description'
"""

import pandas as pd
import google.generativeai as genai
from tqdm import tqdm

# Gemini configuration with API key and model
genai.configure(api_key='put_the_API_key')
MODEL_NAME = '(put a model that is available on the listing_models_available)'


# Function to generate investment descriptions
def generate_investment_description(row):
    prompt = f"""Generate a concise 4-line description in English about {row['Investor']}'s investment in {row['Recipient']}, 
    {row['Recipient Country']} in {row['Year']} in the {row['Sector']} sector. 
    Include only factual information without additional commentary."""

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error processing row {row.name}: {str(e)}")
        return "Description unavailable"


# Excel file processing function
def process_excel_file(input_file, output_file):
    try:
        # Load data
        df = pd.read_excel(input_file)

        # Check required columns
        required_cols = ['Year', 'Investor', 'Recipient', 'Recipient Country', 'Sector']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")

        # Process each row
        print(f"\nProcessing {len(df)} investments...")
        df['Description'] = ""  # Initialize column

        for idx, row in tqdm(df.iterrows(), total=len(df)):
            df.at[idx, 'Description'] = generate_investment_description(row)

        # Save results
        df.to_excel(output_file, index=False)
        print(f"\nSuccess! Processed {len(df)} rows.")
        print(f"Saved to: {output_file}")

        return True

    except Exception as e:
        print(f"\nError: {str(e)}")
        return False


# Main execution
if __name__ == "__main__":
    input_path = r'C:\Users\lucas\Desktop\test_table.xlsx'
    output_path = r'C:\Users\lucas\Desktop\test_table_with_descriptions.xlsx'

    print("=== Gemini Investment Description Generator ===")
    print(f"Model: {MODEL_NAME}")
    print(f"Input file: {input_path}")

    process_excel_file(input_path, output_path)