import requests

DEFAULT_MODEL = "qwen2.5:0.5b"
OLLAMA_API = "http://localhost:11434"

def ollama_status(model=DEFAULT_MODEL):
    try:
        response = requests.get(f"{OLLAMA_API}/api/tags", timeout=2)
        response.raise_for_status()
        names = [m.get("name", "") for m in response.json().get("models", [])]
        model_present = any(name == model or name.startswith(model + ":") for name in names)
        return {"ok": True, "model_present": model_present, "models": names}
    except requests.RequestException:
        return {"ok": False, "model_present": False, "models": []}

def generate(question, context, model=DEFAULT_MODEL):
    prompt = f"""You are DocuMind AI, a careful document assistant.
Answer the user's question using ONLY the document excerpts below.
Explain clearly and naturally. Use simple language when appropriate.
If the excerpts do not contain the answer, say that the documents do not provide enough information.
Do not invent facts. Refer to source labels such as [Source: filename — Page 3] when supporting claims.

DOCUMENT EXCERPTS:
{context}

USER QUESTION:
{question}
"""
    response = requests.post(
        f"{OLLAMA_API}/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.2, "num_ctx": 2048, "num_predict": 450}
        },
        timeout=180
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()
