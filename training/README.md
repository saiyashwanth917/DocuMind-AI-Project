# DocuMind AI — future LoRA fine-tuning

**Do not run model training on the 4 GB RAM Windows computer.** Use a GPU runtime in Google Colab. Your NVIDIA GPU's VRAM is not yet known, so local training feasibility cannot be assessed from the GPU brand alone.

## What fine-tuning changes

Fine-tuning teaches a model how to respond (for example: clear explanations, structured summaries, MCQ formatting). RAG still retrieves facts from each newly uploaded PDF/Word/PowerPoint file. Do not fine-tune again for every uploaded document.

## Colab steps

1. Open Google Colab: https://colab.research.google.com/
2. Create a notebook and choose **Runtime → Change runtime type → T4 GPU** if available.
3. Upload `train.jsonl` and `train_lora_colab.py` from this folder, or put them in Google Drive.
4. Run the script after installing the packages in the notebook.
5. Download the saved adapter folder. This is an experimental starter recipe; Colab GPU availability and package versions can change.

## Dataset format

`train.jsonl` contains one JSON object per line with a `text` field. Add many high-quality examples of the desired assistant behavior. Do not put private documents or copyrighted material in a training set unless you have permission.

## Deploying the adapter

The adapter produced by PEFT is not automatically an Ollama model. To deploy it, merge it with the base model, convert/export it to a compatible GGUF file using llama.cpp, create an Ollama Modelfile, then run `ollama create documind-custom -f Modelfile`. Keep the base model and adapter licenses in mind.
