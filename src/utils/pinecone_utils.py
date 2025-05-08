from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import time

# Load env variables
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PINECONE_DIM = int(os.getenv("PINECONE_DIM", 768))

if not all([PINECONE_API_KEY, PINECONE_INDEX_NAME]):
    raise ValueError("Missing required Pinecone environment variables.")

# Init Pinecone (v3+ style)
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if it doesn't exist
if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=PINECONE_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")  # serverless region!
    )
    # Optional wait loop
    while True:
        status = pc.describe_index(PINECONE_INDEX_NAME).status
        if status['ready']:
            break
        print("Waiting for Pinecone index to be ready...")
        time.sleep(2)

# Connect to the index
index = pc.Index(PINECONE_INDEX_NAME)

# Load data
df = pd.read_csv("app/data/embeddings.csv")
embeddings = np.load("app/data/embeddings.npy", allow_pickle=True)

# Format vectors for upsert
to_upsert = [
    (
        str(row["id"]),
        embedding.tolist(),
        {
            "name": row["assessment_name"],
            "url": row["url"],
            "remote": row["remote_testing"],
            "irt": row["adaptive_irt_support"],
            "type": row["test_type"]
        }
    )
    for row, embedding in zip(df.to_dict("records"), embeddings)
]

# Upsert to Pinecone
index.upsert(vectors=to_upsert)
print(f"✅ Upserted {len(to_upsert)} vectors to Pinecone.")
