from dotenv import load_dotenv
import os
from src.helper import download_embeddings, load_pdf_files, filter_to_minimal_docs, text_split
from pinecone import Pinecone
from pinecone import ServerlessSpec 
from langchain_pinecone import PineconeVectorStore

load_dotenv()


PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if PINECONE_API_KEY is not None:
	os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

if GOOGLE_API_KEY is not None:
	os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


extracted_data=load_pdf_files(data='data/')
filter_data = filter_to_minimal_docs(extracted_data)
text_chunks=text_split(filter_data)

embeddings = download_embeddings()

pinecone_api_key = PINECONE_API_KEY
pc = Pinecone(api_key=pinecone_api_key)



index_name = "medical-chatbot-project"

if not pc.has_index(index_name):
    pc.create_index(
        name=index_name,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )


index = pc.Index(index_name)


from langchain_pinecone import PineconeVectorStore

if index.describe_index_stats()["total_vector_count"] == 0:
    print("Index empty → adding documents")
    
    docsearch = PineconeVectorStore.from_documents(
        documents=text_chunks,
        embedding=embeddings,
        index_name=index_name
    )
else:
    print("✅ Index already populated → loading existing index")
    
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
