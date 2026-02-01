from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

from src.helper import download_embeddings
from src.prompt import system_prompt

from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# ------------------ APP SETUP ------------------

app = Flask(__name__)
CORS(app)

load_dotenv()

# ------------------ ENV VARIABLES ------------------

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("❌ PINECONE_API_KEY not found in .env")

if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found in .env")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# ------------------ VECTOR STORE ------------------

index_name = "medical-chatbot-project"

embeddings = download_embeddings()

vectorstore = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

# ------------------ LLM + RAG ------------------

llm = ChatGoogleGenerativeAI(
    model="models/gemini-flash-latest",
    temperature=0.2
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}")
    ]
)

document_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, document_chain)

# ------------------ ROUTES ------------------

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "Backend is running"}), 200


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)

    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400

    user_message = data["message"]
    print("User:", user_message)

    try:
        response = rag_chain.invoke({"input": user_message})
        answer = response.get("answer", "Sorry, I couldn't generate a response.")

        print("Bot:", answer)
        return jsonify({"answer": answer})

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"error": "Internal server error"}), 500


# ------------------ RUN ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
