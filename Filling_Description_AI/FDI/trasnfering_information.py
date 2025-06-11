
"""THIS IS A CODE TO TRANSFER THE INFORMATION OF THE FIRST 10 LINES AND THE 6 FIRST COLUMNS
OF THE FDI_dataset DOCUMENT TO A test_table FILE, SO WE CAN TEST THE INPUTS BETTER
"""


import pandas as pd


# File paths
source_path = r'C:\Users\lucas\Desktop\FDI_dataset.xlsx'
destination_path = r'C:\Users\lucas\Desktop\test_table.xlsx'

try:
    # Readthe first 10 rows and first 6 columns from the source file
    source_data = pd.read_excel(source_path).iloc[:10, :6]

    # Verify column names
    print("Columns to be transferred:")
    print(source_data.columns.tolist())

    # Save to destination file (overwrites existing content)
    source_data.to_excel(destination_path, index=False)

    print("\nOperation completed successfully!")
    print(f"Transferred {len(source_data)} rows and {len(source_data.columns)} columns")
    print(f"Updated file saved to: {destination_path}")

    # Show preview of transferred data
    print("\nPreview of transferred data:")
    print(source_data)

except FileNotFoundError:
    print("Error: Source file not found. Please check the file path.")
except Exception as e:
    print(f"An error occurred: {str(e)}")