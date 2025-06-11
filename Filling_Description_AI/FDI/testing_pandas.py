"""THIS IS A CODE TO CHECK IF THE INFORMATION OF THE TEST TABLE IS STORED CORRECTLY
"""

import pandas as pd

# File path
file_path = r'C:\Users\lucas\Desktop\test_table.xlsx'

try:
    # Read the Excel file
    fdi_data = pd.read_excel(file_path)

    # Extract the necessary columns
    years = fdi_data['Year'].tolist() if 'Year' in fdi_data.columns else []
    investors = fdi_data['Investor'].tolist() if 'Investor' in fdi_data.columns else []
    recipients = fdi_data['Recipient'].tolist() if 'Recipient' in fdi_data.columns else []
    recipient_countries = fdi_data['Recipient Country'].tolist() if 'Recipient Country' in fdi_data.columns else []
    sectors = fdi_data['Sector'].tolist() if 'Sector' in fdi_data.columns else []

    # Verify if data was extracted correctly
    print(f"Years: {years[:5]}... (total: {len(years)})")
    print(f"Investors: {investors[:5]}... (total: {len(investors)})")
    print(f"Recipients: {recipients[:5]}... (total: {len(recipients)})")
    print(f"Recipient countries: {recipient_countries[:5]}... (total: {len(recipient_countries)})")
    print(f"Sectors: {sectors[:5]}... (total: {len(sectors)})")

except FileNotFoundError:
    print("Error: File not found. Please check the file path and name.")
except Exception as e:
    print(f"An error occurred: {e}")