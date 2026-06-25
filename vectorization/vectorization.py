import json
import requests
import psycopg2
from tqdm import tqdm
from pgvector.psycopg2 import register_vector

conn = psycopg2.connect(
    host="localhost",
    database="polarisLex",
    user="dinky",
    password="abcd1234",
    port=5433
)

register_vector(conn)

cursor = conn.cursor()


with open("IT_ACT_POLARISLEX_MERGED.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)

# print(dataset)

sections = dataset["sections"]

for section in tqdm(sections):

    text = section["retrieval_text"]

  
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={
            "model": "nomic-embed-text",
            "prompt": text
        }
    )

    embedding = response.json()["embedding"]

    cursor.execute(
        """
        INSERT INTO legal_documents_vectorization (data, embedding)
        VALUES (%s, %s)
        """,
        (
            json.dumps(section),
            embedding
        )
    )

conn.commit()

cursor.close()
conn.close()

print("Done!")