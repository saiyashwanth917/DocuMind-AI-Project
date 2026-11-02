import streamlit as st
from pathlib import Path
import uuid
from src.document_loader import extract_document
from src.rag_engine import retrieve, build_context
from src.ollama_client import generate, ollama_status, DEFAULT_MODEL

st.set_page_config(page_title="DocuMind AI", page_icon="🧠", layout="wide")

ROOT = Path(__file__).parent
UPLOAD_DIR = ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def init_state():
    defaults = {
        "documents": {}, "chunks": [], "messages": [],
        "active_ids": [], "model": DEFAULT_MODEL
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

st.markdown("""
<style>
.stApp {background:radial-gradient(circle at 8% 0%,rgba(112,75,190,.22),transparent 32%),#0c1020;}
.block-container{max-width:1450px;padding-top:1.5rem}
.hero{padding:1.5rem 1.8rem;border-radius:22px;background:linear-gradient(115deg,#292052,#17345a 68%,#124052);border:1px solid #51458a;margin-bottom:1rem}
.hero h1{color:white;margin:0;font-size:2.2rem}.hero p{color:#d9dcf5;margin:.4rem 0 0}
div[data-testid="stMetric"]{background:#171b30;border:1px solid #303754;padding:12px;border-radius:15px}
.stButton>button{border-radius:12px}
div[data-testid="stChatMessage"]{border:1px solid #303754;border-radius:15px;padding:12px}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🧠 DocuMind AI")
    st.caption("Your AI document companion")
    page = st.radio("Workspace", ["Chat with documents", "Document library", "AI tools", "Settings"])
    st.divider()
    st.caption("PDF · PPTX · DOCX")
    st.caption("Session-only chat; no chat database.")
    if st.button("Clear session and uploaded files", use_container_width=True):
        for path in UPLOAD_DIR.glob("*"):
            if path.is_file():
                try: path.unlink()
                except OSError: pass
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.markdown("""
<div class="hero">
<h1>🧠 DocuMind AI</h1>
<p>Ask questions about PDFs, PowerPoint presentations and Word documents — with source references.</p>
</div>
""", unsafe_allow_html=True)

status = ollama_status(st.session_state.model)
c1, c2, c3 = st.columns(3)
c1.metric("Documents in session", len(st.session_state.documents))
c2.metric("Text chunks", len(st.session_state.chunks))
c3.metric("Local AI", "Connected" if status["ok"] else "Not connected")

if page == "Chat with documents":
    left, right = st.columns([1, 1.65], gap="large")
    with left:
        st.subheader("① Upload documents")
        uploads = st.file_uploader("Choose files", type=["pdf", "pptx", "docx"], accept_multiple_files=True)
        if uploads and st.button("Process uploaded files", type="primary", use_container_width=True):
            progress = st.progress(0)
            for i, uploaded in enumerate(uploads):
                doc_id = uuid.uuid4().hex[:10]
                filename = Path(uploaded.name).name
                target = UPLOAD_DIR / f"{doc_id}_{filename}"
                target.write_bytes(uploaded.getvalue())
                try:
                    extracted = extract_document(target)
                    new_chunks = []
                    for record in extracted:
                        text = record["text"].strip()
                        words = text.split()
                        for start in range(0, len(words), 170):
                            piece = " ".join(words[max(0, start-25):start+170])
                            if len(piece.strip()) > 20:
                                new_chunks.append({
                                    "doc_id": doc_id, "filename": filename,
                                    "source": record["source"], "text": piece
                                })
                    if not new_chunks:
                        raise ValueError("No selectable text found. The file may be scanned or image-only.")
                    st.session_state.documents[doc_id] = {
                        "name": filename, "path": str(target), "chunks": len(new_chunks)
                    }
                    st.session_state.chunks.extend(new_chunks)
                    st.success(f"{filename}: extracted {len(new_chunks)} chunks.")
                except Exception as exc:
                    target.unlink(missing_ok=True)
                    st.error(f"Could not process {filename}: {exc}")
                progress.progress((i + 1) / len(uploads))
        st.subheader("② Choose sources")
        if st.session_state.documents:
            ids = list(st.session_state.documents)
            selected = st.multiselect(
                "Search in these documents",
                ids,
                default=st.session_state.active_ids or ids,
                format_func=lambda x: st.session_state.documents[x]["name"]
            )
            st.session_state.active_ids = selected
        else:
            st.info("Upload and process a document to begin.")
        st.subheader("③ Model")
        st.text_input("Ollama model name", key="model")
        st.caption("Default: qwen2.5:0.5b — a small model selected for low-memory computers.")
        if not status["ok"]:
            st.warning("Ollama is not responding. Install and start Ollama, then download the model. See README.")

    with right:
        st.subheader("Ask your documents")
        if not st.session_state.chunks:
            st.info("Your AI conversation will appear here after you process documents.")
        else:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            prompt = st.chat_input("Ask a question about your documents…")
            if prompt:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Finding evidence and asking the local AI model…"):
                        active = st.session_state.active_ids or list(st.session_state.documents)
                        matches = retrieve(prompt, st.session_state.chunks, active, top_k=3)
                        if not matches:
                            answer = "I couldn't find relevant information in the selected documents. Try another question or select more documents."
                        elif not status["ok"]:
                            answer = "I found relevant passages, but Ollama is not running. Start Ollama and try again.\n\n" + "\n\n".join(
                                f"**{m['filename']} — {m['source']}**\n\n> {m['text'][:500]}" for m in matches
                            )
                        else:
                            context = build_context(matches, max_chars=5000)
                            try:
                                answer = generate(prompt, context, st.session_state.model)
                                answer += "\n\n**Sources used:** " + "; ".join(
                                    f"{m['filename']} ({m['source']})" for m in matches
                                )
                            except Exception as exc:
                                answer = f"AI request failed: {exc}\n\nStart Ollama and check the model name in Settings."
                        st.markdown(answer)
                        if matches:
                            with st.expander("View retrieved source passages"):
                                for m in matches:
                                    st.markdown(f"**{m['filename']} · {m['source']}**")
                                    st.write(m["text"])
                st.session_state.messages.append({"role": "assistant", "content": answer})

elif page == "Document library":
    st.subheader("Your current-session documents")
    if not st.session_state.documents:
        st.info("No documents processed yet.")
    for doc_id, doc in list(st.session_state.documents.items()):
        with st.container(border=True):
            a, b, c = st.columns([3, 1, 1])
            a.markdown(f"**📄 {doc['name']}**")
            b.metric("Chunks", doc["chunks"])
            if c.button("Remove", key=f"remove_{doc_id}"):
                Path(doc["path"]).unlink(missing_ok=True)
                st.session_state.documents.pop(doc_id)
                st.session_state.chunks = [x for x in st.session_state.chunks if x["doc_id"] != doc_id]
                st.session_state.active_ids = [x for x in st.session_state.active_ids if x != doc_id]
                st.session_state.messages = []
                st.rerun()

elif page == "AI tools":
    st.subheader("Document AI tools")
    if not st.session_state.chunks:
        st.info("Process documents first.")
    else:
        ids = list(st.session_state.documents)
        chosen = st.multiselect("Select documents", ids, default=ids,
                                format_func=lambda x: st.session_state.documents[x]["name"])
        selected_chunks = [c for c in st.session_state.chunks if c["doc_id"] in chosen]
        tool = st.radio("Tool", ["Summarize documents", "Explain a concept", "Generate practice questions"], horizontal=True)
        if tool == "Explain a concept":
            topic = st.text_input("What should the AI explain?")
        elif tool == "Generate practice questions":
            count = st.slider("Number of questions", 3, 10, 5)
        if st.button("Run AI tool", type="primary"):
            passages = retrieve(" ".join(c["text"][:100] for c in selected_chunks[:3]), selected_chunks, chosen, top_k=5)
            if not passages:
                passages = selected_chunks[:5]
            context = build_context(passages, max_chars=5000)
            if not status["ok"]:
                st.error("Start Ollama before using AI tools.")
            else:
                if tool == "Summarize documents":
                    prompt = "Summarize the supplied document excerpts in clear sections. Keep important facts and cite source labels."
                elif tool == "Explain a concept":
                    prompt = f"Explain this concept in simple language, with an example, using only the supplied document excerpts: {topic}"
                else:
                    prompt = f"Create {count} multiple-choice questions from the supplied excerpts. Give four options, mark the correct answer, and explain briefly. Include source labels."
                with st.spinner("Generating with Ollama…"):
                    try:
                        st.markdown(generate(prompt, context, st.session_state.model))
                        st.caption("Generated from the retrieved passages. Verify important details against the source document.")
                    except Exception as exc:
                        st.error(str(exc))

elif page == "Settings":
    st.subheader("Setup and project notes")
    st.markdown("""
- Chat is temporary and is not saved to a database.
- Uploaded documents stay in `data/uploads` until you remove them or clear the session.
- Supported: `.pdf`, `.pptx`, `.docx`. Convert older `.ppt` and `.doc` files to modern formats.
- Current retrieval uses lightweight TF-IDF to reduce memory use on a 4 GB RAM computer.
- OCR for scanned/image-only documents is not enabled in this starter build.
- LoRA fine-tuning starter files are in the `training` folder. Run training in Google Colab, not on this 4 GB Windows computer.
""")
    st.markdown(f"**Ollama status:** {'Connected' if status['ok'] else 'Not connected'}")
    st.markdown("**Default model:** `qwen2.5:0.5b`")
