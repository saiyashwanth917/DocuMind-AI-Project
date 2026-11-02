# DocuMind AI — RAG + Ollama starter

This project is configured for a Windows computer with **4 GB system RAM**. It uses a small local model and lightweight TF-IDF retrieval to keep memory use lower.

## What is included

- Upload multiple `.pdf`, `.pptx`, `.docx` documents.
- Extract PDF page text, PowerPoint slide text, Word paragraphs and tables.
- Retrieve relevant passages from selected documents.
- Send those passages to a local Ollama model to generate natural answers.
- Show source filename and page/slide/paragraph labels.
- AI tools for summaries, simple explanations and multiple-choice questions.
- No chat-history database. Messages live in the current Streamlit session only.
- A future LoRA/QLoRA training starter in `training/` for Google Colab.

## Important limitations

1. **Small local model:** Qwen2.5 0.5B is a lightweight compromise, not ChatGPT-level capability. It can make mistakes. Check citations and source passages.
2. **4 GB RAM:** This is very limited. Close other programs before running. Ollama may use CPU if your NVIDIA GPU has insufficient VRAM. GPU model and VRAM are unknown.
3. **Scanned PDFs:** OCR is not included yet. Image-only PDFs need a later OCR/Tesseract integration.
4. **Legacy Office:** `.ppt` and `.doc` are not supported directly. Save them as `.pptx` and `.docx`.
5. **Fine-tuning:** Do not fine-tune on this 4 GB PC. Use a GPU runtime in Colab. The included script is a starter example and may need adjustment for current package versions and runtime constraints.
6. **Training data:** The included two examples are placeholders only. They are not enough to produce a useful fine-tuned model.
7. **Privacy:** Files are stored in `data/uploads` until removed or cleared. Ollama runs locally; document excerpts are sent to the local Ollama service, not a hosted AI API.

## A. Install Python and VS Code

Install Python 3.10 or newer and VS Code. Open this folder in VS Code and select **Terminal → New Terminal**.

## B. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If activation is blocked in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Install Python packages:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## C. Install Ollama and download the small model

1. Install Ollama for Windows from https://ollama.com/download/windows
2. Open a **new** VS Code terminal after installation.
3. Download the model:

```powershell
ollama pull qwen2.5:0.5b
```

4. Test the model:

```powershell
ollama run qwen2.5:0.5b
```

Type `Hello` and check that it responds. Type `/bye` to exit the model prompt. Ollama normally runs its local API at `http://localhost:11434`.

If the model is slow or Windows runs out of memory, close other apps. Do not try a larger model on this 4 GB system yet.

## D. Start DocuMind AI

In the activated VS Code terminal:

```powershell
streamlit run app.py
```

Open the local URL Streamlit prints, usually `http://localhost:8501`.

## E. Use the application

1. Select **Chat with documents**.
2. Upload PDF, PPTX or DOCX files.
3. Click **Process uploaded files**.
4. Select the documents to search.
5. Ask a question. The app retrieves relevant text and sends it to Ollama.
6. Check the source labels and open **View retrieved source passages** to verify the answer.

## F. Fine-tuning later

Read `training/README.md`. Fine-tuning is a separate phase. The recommended path is LoRA/QLoRA on a GPU-enabled Google Colab runtime, then export the trained adapter for Ollama. RAG continues to provide the content from each newly uploaded file; fine-tuning teaches response behavior and format.

## Troubleshooting

- `ollama` is not recognized: finish installing Ollama, close and reopen the terminal.
- Ollama not connected in app: check Ollama is running and visit `http://localhost:11434` in your browser.
- Model not found: run `ollama pull qwen2.5:0.5b`.
- Out of memory: close browsers and other programs; the PC has only 4 GB RAM.
- No PDF text: likely scanned; OCR is not included in this version.
- Import errors: activate `.venv` and run `pip install -r requirements.txt` again.

## Project layout

```text
DocuMind-AI-Advanced/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/config.toml
├── data/uploads/
├── src/
│   ├── document_loader.py
│   ├── pdf_loader.py
│   ├── word_loader.py
│   ├── ppt_loader.py
│   ├── rag_engine.py
│   └── ollama_client.py
└── training/
    ├── README.md
    ├── train.jsonl
    └── train_lora_colab.py
```
