import os
from enum import StrEnum
 
class Collection_Type(StrEnum):
    MANUAL = "Manual"
    SYNC = "Sync"
    DRIVE = "Google Drive"
    CODE = "Code Repository"

collections_path = os.path.join("data", "collections.json")
chroma_db_path = os.path.join("data", "chroma_db")
openai_api_key = os.environ.get("OPENAI_API_KEY")

character_splitter_chunk_size = 2000
character_splitter_chunk_overlap = 400

embedding_api_chunk_limit = 50