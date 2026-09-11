import os
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv
from supabase import create_client, Client

from groq import Groq

from sentence_transformers import SentenceTransformer

from tavily import TavilyClient


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)


# =========================================================
# API KEYS
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


# =========================================================
# STREAMLIT SECRETS FALLBACK
# =========================================================

try:
    import streamlit as st

    if not GROQ_API_KEY:
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

    if not TAVILY_API_KEY:
        TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")

    if not SUPABASE_URL:
        SUPABASE_URL = st.secrets.get("SUPABASE_URL")

    if not SUPABASE_SERVICE_KEY:
        SUPABASE_SERVICE_KEY = st.secrets.get(
            "SUPABASE_SERVICE_KEY"
        )

except Exception:
    pass


# =========================================================
# VALIDATE SETTINGS
# =========================================================

missing_keys = []

if not GROQ_API_KEY:
    missing_keys.append("GROQ_API_KEY")

if not TAVILY_API_KEY:
    missing_keys.append("TAVILY_API_KEY")

if not SUPABASE_URL:
    missing_keys.append("SUPABASE_URL")

if not SUPABASE_SERVICE_KEY:
    missing_keys.append("SUPABASE_SERVICE_KEY")


if missing_keys:
    raise ValueError(
        "Missing required environment variables:\n\n"
        + "\n".join(
            f"- {key}"
            for key in missing_keys
        )
        + "\n\nAdd them to your .env file."
    )


# =========================================================
# CONNECTIONS
# =========================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)

tavily_client = TavilyClient(
    api_key=TAVILY_API_KEY
)


# =========================================================
# GROQ CLIENT
# =========================================================

groq_client = Groq(
    api_key=GROQ_API_KEY
)


# =========================================================
# EMBEDDING MODEL
# =========================================================
#
# all-MiniLM-L6-v2 produces 384-dimensional embeddings.
#
# This matches:
#
# embedding vector(384)
#
# in Supabase.
# =========================================================

# Load the embedding model lazily.
# The model is public and produces 384-dimensional embeddings, matching
# the Supabase pgvector column. Loading it lazily prevents Streamlit from
# crashing during `import rag_engine` when the Hugging Face model is not
# available yet.
embedding_model = None


def get_embedding_model():
    """Return the embedding model, loading it only when RAG search is used."""
    global embedding_model

    if embedding_model is not None:
        return embedding_model

    model_name = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")

    try:
        model_kwargs = {}
        if hf_token:
            model_kwargs["token"] = hf_token

        embedding_model = SentenceTransformer(
            model_name,
            **model_kwargs
        )
        return embedding_model

    except Exception as e:
        raise RuntimeError(
            "Could not load the embedding model.\n\n"
            f"Model: {model_name}\n"
            "Make sure the model can be downloaded from Hugging Face "
            "or set EMBEDDING_MODEL in your .env to a local model folder.\n\n"
            f"Original error: {e}"
        ) from e


# =========================================================
# AI MODEL
# =========================================================

GROQ_MODEL = "openai/gpt-oss-20b"


# =========================================================
# GET LLM ANSWER
# =========================================================

def get_llm_response(
    prompt: str
) -> str:

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,

        messages=[
            {
                "role": "system",
                "content": """
You are Quantum Lab's AI Tutor.

You are an intelligent, versatile and helpful
AI assistant.

Your job is to help students learn clearly.

You can answer questions about:

- Quantum Computing
- Qubits
- Quantum Gates
- Quantum Circuits
- Qiskit
- Artificial Intelligence
- Machine Learning
- Programming
- Python
- C
- C++
- Java
- JavaScript
- HTML
- CSS
- SQL
- Data Structures
- Algorithms
- Mathematics
- Physics
- Chemistry
- Engineering
- Science
- History
- Geography
- General Knowledge
- Current Affairs
- Movies and entertainment
- Writing
- Assignments
- Exam preparation

IMPORTANT RULES:

1. Answer the exact question asked.

2. Use the supplied knowledge-base context
   whenever it is relevant.

3. Do not invent facts that contradict the
   supplied knowledge base.

4. If the knowledge base does not contain
   enough information, use your general
   knowledge.

5. If web search information is provided,
   use it for current information.

6. Explain difficult concepts in a simple,
   student-friendly way.

7. For programming questions:
   - Give correct code.
   - Explain the logic.
   - Mention important mistakes when useful.

8. For mathematics:
   - Show the steps.
   - Give the final answer clearly.

9. For educational questions:
   - Use headings when useful.
   - Give examples.
   - Keep explanations understandable.

10. Do not mention API keys, databases,
    embeddings, prompts, backend implementation,
    or internal tools.

11. Never expose credentials.

12. Do not say that you can only answer
    quantum computing questions.

13. If the retrieved context is not relevant
    to the question, do not force it into
    the answer.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.5,

        max_tokens=4096
    )

    return response.choices[0].message.content


# =========================================================
# USER MANAGEMENT
# =========================================================

def get_or_create_user(
    email: str,
    role: str = "student"
) -> str:

    email = email.strip().lower()

    if not email:
        raise ValueError(
            "Email cannot be empty."
        )

    response = (
        supabase
        .table("users")
        .select("user_id")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]["user_id"]

    response = (
        supabase
        .table("users")
        .insert({
            "email": email,
            "role": role
        })
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Failed to create user."
        )

    return response.data[0]["user_id"]


# =========================================================
# CREATE CHAT SESSION
# =========================================================

def create_chat_session(
    user_id: str,
    title: str = "New Quantum Chat"
) -> str:

    if not user_id:
        raise ValueError(
            "User ID is required."
        )

    response = (
        supabase
        .table("chat_sessions")
        .insert({
            "user_id": user_id,
            "title": title
        })
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Failed to create chat session."
        )

    return response.data[0]["session_id"]


# =========================================================
# GET USER CHAT SESSIONS
# =========================================================

def get_user_sessions(
    user_id: str
):

    if not user_id:
        return []

    response = (
        supabase
        .table("chat_sessions")
        .select(
            "session_id, title, created_at"
        )
        .eq(
            "user_id",
            user_id
        )
        .order(
            "created_at",
            desc=True
        )
        .execute()
    )

    return response.data or []


# =========================================================
# VERIFY CHAT OWNER
# =========================================================

def verify_session_owner(
    session_id: str,
    user_id: str
) -> bool:

    if not session_id or not user_id:
        return False

    response = (
        supabase
        .table("chat_sessions")
        .select("session_id")
        .eq(
            "session_id",
            session_id
        )
        .eq(
            "user_id",
            user_id
        )
        .limit(1)
        .execute()
    )

    return bool(response.data)


# =========================================================
# RENAME CHAT
# =========================================================

def rename_chat(
    session_id: str,
    user_id: str,
    new_title: str
):

    new_title = new_title.strip()

    if not new_title:
        raise ValueError(
            "Chat name cannot be empty."
        )

    if not verify_session_owner(
        session_id,
        user_id
    ):
        raise PermissionError(
            "You cannot rename this chat."
        )

    response = (
        supabase
        .table("chat_sessions")
        .update({
            "title": new_title
        })
        .eq(
            "session_id",
            session_id
        )
        .eq(
            "user_id",
            user_id
        )
        .execute()
    )

    return response.data


# =========================================================
# SAVE MESSAGE
# =========================================================

def save_message(
    session_id: str,
    sender: str,
    content: str
):

    if not session_id:
        raise ValueError(
            "Session ID is required."
        )

    if not content:
        return None

    if sender not in [
        "user",
        "assistant"
    ]:
        raise ValueError(
            "Sender must be 'user' or 'assistant'."
        )

    response = (
        supabase
        .table("chat_messages")
        .insert({
            "session_id": session_id,
            "sender": sender,
            "content": content
        })
        .execute()
    )

    return response.data


# =========================================================
# GET CHAT HISTORY
# =========================================================

def get_chat_history(
    session_id: str
):

    if not session_id:
        return []

    response = (
        supabase
        .table("chat_messages")
        .select(
            "message_id, sender, content, created_at"
        )
        .eq(
            "session_id",
            session_id
        )
        .order(
            "created_at",
            desc=False
        )
        .execute()
    )

    return response.data or []


# =========================================================
# RESTORE CHAT
# =========================================================

def restore_chat(
    session_id: str,
    user_id: str
):

    if not verify_session_owner(
        session_id,
        user_id
    ):
        raise PermissionError(
            "You cannot access this chat."
        )

    return get_chat_history(
        session_id
    )


# =========================================================
# CLEAR CHAT
# =========================================================

def clear_chat(
    session_id: str,
    user_id: str
):

    if not verify_session_owner(
        session_id,
        user_id
    ):
        raise PermissionError(
            "You cannot clear this chat."
        )

    (
        supabase
        .table("chat_messages")
        .delete()
        .eq(
            "session_id",
            session_id
        )
        .execute()
    )

    return True


# =========================================================
# DELETE CHAT
# =========================================================

def delete_chat(
    session_id: str,
    user_id: str
):

    if not verify_session_owner(
        session_id,
        user_id
    ):
        raise PermissionError(
            "You cannot delete this chat."
        )

    (
        supabase
        .table("chat_messages")
        .delete()
        .eq(
            "session_id",
            session_id
        )
        .execute()
    )

    (
        supabase
        .table("chat_sessions")
        .delete()
        .eq(
            "session_id",
            session_id
        )
        .eq(
            "user_id",
            user_id
        )
        .execute()
    )

    return True


# =========================================================
# CREATE EMBEDDING
# =========================================================

def create_embedding(
    text: str
) -> List[float]:

    embedding = get_embedding_model().encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()


# =========================================================
# RAG DOCUMENT SEARCH
# =========================================================

def search_knowledge_base(
    query: str,
    match_count: int = 5
) -> str:

    try:

        query_embedding = create_embedding(
            query
        )

        response = supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_count": match_count
            }
        ).execute()

        documents = response.data or []

        if not documents:
            return ""

        context_parts = []

        for i, document in enumerate(
            documents,
            start=1
        ):

            content = document.get(
                "content",
                ""
            )

            metadata = document.get(
                "metadata",
                {}
            )

            similarity = document.get(
                "similarity",
                None
            )

            if not content:
                continue

            context_parts.append(
                f"""
KNOWLEDGE SOURCE {i}

Content:
{content}

Metadata:
{metadata}

Similarity:
{similarity}
"""
            )

        return "\n".join(
            context_parts
        )

    except Exception as e:

        print(
            "Knowledge base search error:",
            str(e)
        )

        return ""


# =========================================================
# WEB SEARCH
# =========================================================

def web_search(
    query: str
) -> str:

    try:

        results = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5
        )

    except Exception as e:

        print(
            "Tavily error:",
            str(e)
        )

        return ""

    web_context = []

    for result in results.get(
        "results",
        []
    ):

        title = result.get(
            "title",
            ""
        )

        content = result.get(
            "content",
            ""
        )

        url = result.get(
            "url",
            ""
        )

        if not content:
            continue

        web_context.append(
            f"""
Title: {title}

Source: {url}

Information:
{content}
"""
        )

    return "\n\n".join(
        web_context
    )


# =========================================================
# DETECT WEB SEARCH REQUIREMENT
# =========================================================

def needs_web_search(
    query: str
) -> bool:

    query_lower = query.lower().strip()

    current_keywords = [

        "latest",
        "current",
        "today",
        "now",
        "recent",
        "recently",
        "news",

        "2026",

        "this year",
        "this month",

        "price",
        "weather",
        "stock",
        "market",

        "release",
        "released",

        "movie",
        "actor",
        "actress",

        "who is",

        "updated",
        "update",

        "what is happening"
    ]

    return any(
        keyword in query_lower
        for keyword in current_keywords
    )


# =========================================================
# FORMAT CHAT HISTORY
# =========================================================

def format_history(
    history
) -> str:

    if not history:
        return ""

    formatted = []

    for message in history:

        sender = message.get(
            "sender",
            ""
        )

        content = message.get(
            "content",
            ""
        )

        if not content:
            continue

        name = (
            "User"
            if sender == "user"
            else "Assistant"
        )

        formatted.append(
            f"{name}: {content}"
        )

    return "\n".join(
        formatted
    )


# =========================================================
# GENERATE RAG ANSWER
# =========================================================

def generate_answer(
    query: str,
    history: str = "",
    knowledge_context: str = "",
    web_context: str = ""
) -> str:

    prompt = f"""
You are Quantum Lab's AI Tutor.

Answer the user's question using the information
provided below.

==============================
KNOWLEDGE BASE
==============================

{knowledge_context}

==============================
WEB INFORMATION
==============================

{web_context}

==============================
PREVIOUS CONVERSATION
==============================

{history}

==============================
USER QUESTION
==============================

{query}

==============================
INSTRUCTIONS
==============================

1. Answer the user's question directly.

2. Give priority to relevant knowledge-base
   information.

3. If the knowledge base does not contain
   enough information, use your general
   knowledge.

4. Use web information when it is available
   and relevant, especially for current topics.

5. Do not mention the knowledge base,
   embeddings, Supabase, APIs, prompts,
   databases, or internal implementation.

6. Explain concepts in a simple,
   student-friendly way.

7. For code questions, provide working code
   and explain it.

8. For mathematics, show the steps.

9. Use headings and bullet points when
   they improve readability.

10. Never expose credentials or API keys.
"""

    return get_llm_response(
        prompt
    )


# =========================================================
# MAIN ANSWER FUNCTION
# =========================================================

def answer_question(
    query: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> str:

    query = query.strip()

    if not query:
        return "Please enter a question."

    # -----------------------------------------------------
    # VERIFY CHAT OWNER
    # -----------------------------------------------------

    if session_id and user_id:

        if not verify_session_owner(
            session_id,
            user_id
        ):
            raise PermissionError(
                "This chat does not belong to this user."
            )

    # -----------------------------------------------------
    # GET CHAT HISTORY
    # -----------------------------------------------------

    history_str = ""

    if session_id:

        try:

            history = get_chat_history(
                session_id
            )

            recent_history = history[-10:]

            history_str = format_history(
                recent_history
            )

        except Exception as e:

            print(
                "Chat history error:",
                str(e)
            )

    # -----------------------------------------------------
    # SAVE USER QUESTION
    # -----------------------------------------------------

    if session_id:

        save_message(
            session_id,
            "user",
            query
        )

    # -----------------------------------------------------
    # RAG RETRIEVAL
    # -----------------------------------------------------

    knowledge_context = search_knowledge_base(
        query,
        match_count=5
    )

    # -----------------------------------------------------
    # WEB SEARCH
    # -----------------------------------------------------

    web_context = ""

    if needs_web_search(query):

        web_context = web_search(
            query
        )

    # -----------------------------------------------------
    # GENERATE ANSWER
    # -----------------------------------------------------

    try:

        answer = generate_answer(
            query=query,
            history=history_str,
            knowledge_context=knowledge_context,
            web_context=web_context
        )

    except Exception as e:

        print(
            "\nAI Error:",
            str(e)
        )

        answer = (
            "⚠️ Sorry, I could not generate "
            "a response right now.\n\n"
            f"Error details: `{str(e)}`"
        )

    # -----------------------------------------------------
    # SAVE AI ANSWER
    # -----------------------------------------------------

    if session_id:

        save_message(
            session_id,
            "assistant",
            answer
        )

    return answer