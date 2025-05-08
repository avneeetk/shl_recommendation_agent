import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv 
import google.generativeai as genai
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential



load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)


df=pd.read_csv('app/data/product_catalog.csv')



def combine_fields(row):
    return f"""
              Id:{row['id']}.
              Name:{row['assessment_name']}.
              URL:{row['url']}.
              Remote:{row['remote_testing']}.
              IRT:{row['adaptive_irt_support']}
              Type:{row['test_type']}.
             """

df['combined_text']=df.apply(combine_fields, axis=1)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1,min=4,max=10))

def get_embedding(text:str)-> list:
    """Get embedding with retry logic for API stability """

    try:
        result=genai.embed_content(
              model="models/text-embedding-004",
              content=text,
              task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embedding:{str(e)}")
        raise

embeddings=[]
failed_indices=[]
for idx, text in tqdm(enumerate(df["combined_text"]), total=len(df), desc="Generating embeddings"):
    try:
        embedding = get_embedding(text)
        embeddings.append(embedding)
    except:
        embeddings.append(None)  # Keep index alignment
        failed_indices.append(idx)
        continue

# Save the embeddings
try:
    embeddings_array = np.array(embeddings, dtype=object)
    np.save("app/data/embeddings.npy", embeddings_array)
    
    # Add embeddings to DataFrame (as list for CSV compatibility)
    df['embedding'] = embeddings
    df.to_csv("app/data/embeddings.csv", index=False)
    
    if failed_indices:
        print(f"Warning: Failed to generate embeddings for {len(failed_indices)} rows (indices: {failed_indices})")
    else:
        print("Successfully generated embeddings for all rows")
        
except Exception as e:
    print(f"Error saving embeddings: {str(e)}")
    raise