import pandas as pd
import numpy as np

#tracker data
df = pd.read_excel('/Users/meyhar/Documents/research/FDI_dataset_random_points_countries.xlsx')
print(df.head(10))

#adding data source column
df['Data Source'] = np.where(df['Investor'] == 'Asian Infrastructure Investment Bank', 'AIIB', 'Tracker')

#AIIB data
df2 = pd.read_excel('/Users/meyhar/Documents/research/aiib_detailed_scrape.xlsx')
print(df2.head(10))

#to identify which columns need to be merged from AIIB table to tracker
print(df.columns)
print(df2.columns)
df.columns = df.columns.str.strip()
df2.columns = df2.columns.str.strip()

#making AIIB projext title names consistent with tracker 
df2['title'] = df2['title'].str.replace(r'^.*?:\s*', '', regex= True)

#renaming columns in AIIB to align for merging 
df2= df2.rename(columns={
    'title': 'Project Name',
    'objective': 'Objective',
    'scraped_summary': 'Summary',
    'FINANCING TYPE': 'Financing Type',
})

#merging 
df_aiib = df[df['Investor'] == 'Asian Infrastructure Investment Bank']

merged_aiib = pd.merge(
    df_aiib,
    df2[['Project Name', 'Objective', 'Summary', 'Financing Type']],
    on = 'Project Name',
    how = 'left',
    suffixes = ('', '_df2')
)
aiib_matches = pd.merge(
    df_aiib,
    df2[['Project Name']],
    on = 'Project Name',
    how = 'inner'
)
print(f"Number of matching AIIB project titles: {len(aiib_matches)}")

for col in ['Objective', 'Summary', 'Financing Type']:
    merged_aiib[col] = merged_aiib[col].fillna(merged_aiib[f'{col}_df2'])
    merged_aiib.drop(columns=[f'{col}_df2'], inplace=True)
df_non_aiib = df[df['Investor'] != 'Asian Infrastructure Investment Bank']
df_updated = pd.concat([df_non_aiib, merged_aiib], ignore_index=True)

df_updated.to_excel('FDI_datatset.xlsx', index = False)