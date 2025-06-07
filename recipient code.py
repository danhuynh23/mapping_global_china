import pandas as pd
from llama_cpp import Llama
from tqdm import tqdm
import re

df = pd.read_excel('/Users/meyhar/Documents/research/aiib_detailed_scrape.xlsx')
#print(df.head(10))
df = df[:10]

model_df = df[['APPROVAL YEAR', 'title', 'FINANCING AMOUNT', 'description']].copy()
model_df.columns = ['approval year', 'title', 'amount (usd million)', 'description']

model_df['amount (usd million)'] = model_df['amount (usd million)'].str.extract(r'USD(\d+)\s+million')
model_df['amount (usd million)'] = model_df['amount (usd million)'].astype('Int64')
model_df['description'] = model_df['description'].str.lower()
model_df['description'] = model_df['description'].apply(lambda x: re.sub(r'[^a-z0-9\s]', '', str(x)))
#print(model_df)

def prompt(row):
    return f"""
    Identify the direct recipient organization for this AIIB investment project. 
    Focus on the entity receiving the funds, not the investor (AIIB) or implementing agencies.

    PROJECT TITLE: {row['title']}
    DESCRIPTION: {row['description']}
    YEAR: {row['approval year']}
    AMOUNT: ${row['amount (usd million)']} million

    Instructions:
    1. Extract only the name of the primary recipient organization
    2. Focus on keywords like "government of", "ministry", "authority", "corporation"
    3. If the recipient isn't clear, respond with "UNKNOWN"
    4. Never include AIIB or Asian Infrastructure Investment Bank in your answer

    Examples of good responses:
    - Ministry of Transport, Kenya
    - National Power Corporation
    - UNKNOWN

    Recipient organization:
    """

model_df['prompt'] = model_df.apply(prompt, axis= 1)

llm = Llama(
    model_path= '/Users/meyhar/Documents/research/models/llama-2-7b-chat.Q4_K_M.gguf',
    n_ctx= 2048,              
    n_threads= 8,             
    n_gpu_layers= 1,          
    use_mlock= True,          
    verbose= False 
)

def query(prompt):
    try:
        output = llm.create_chat_completion(
            messages= [
                {"role": "system", "content": "You are an expert at extracting recipient organizations from project documents."},
                {"role": "user", "content": prompt}
            ],
            temperature= 0.2,
            max_tokens= 40,
            stop= ["\n", "###"] 
        )
        response = output["choices"][0]["message"]["content"].strip()
        response = response.split(',')[0]  # Take only first part if comma-separated
        if any(word in response.lower() for word in ["aiib", "unknown"]):
            return "UNKNOWN"
        return response[:100] 
    
    except Exception as e:
        print(f"Error: {e}")
        return "ERROR"

answers = []
out_path = 'recipient_results_checkpoint.csv'
for i, row in tqdm(model_df.iterrows(), total= len(model_df), desc= 'Generating responses'):
    prompt = row['prompt']
    answer = query(prompt)
    tqdm.write(f"→ {answer}")
    answers.append(answer)

    if (i+1)%3 == 0 or (i+1) == len(model_df):
        model_df.loc[:i, 'recipient'] = answers
        model_df.loc[:i].to_csv(out_path, index=False)

print(f"\nResults saved to {out_path}")