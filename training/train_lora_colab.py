# Run this script in a GPU-enabled Google Colab runtime, not on a 4 GB RAM PC.
# Colab cell setup:
# !pip install -q transformers datasets accelerate peft bitsandbytes

import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig,
    TrainingArguments, Trainer, DataCollatorForLanguageModeling
)
from peft import LoraConfig, prepare_model_for_kbit_training, get_peft_model

BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
DATA_FILE = "train.jsonl"
OUTPUT_DIR = "documind-qwen-lora"

if not torch.cuda.is_available():
    raise RuntimeError("Select a GPU runtime in Google Colab: Runtime > Change runtime type > T4 GPU.")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=bnb_config,
    device_map="auto",
)
model.config.use_cache = False
model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

dataset = load_dataset("json", data_files=DATA_FILE, split="train")

def tokenize(batch):
    result = tokenizer(batch["text"], truncation=True, max_length=512)
    result["labels"] = result["input_ids"].copy()
    return result

tokenized = dataset.map(tokenize, batched=True, remove_columns=dataset.column_names)
args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_train_epochs=3,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=5,
    save_strategy="epoch",
    report_to="none",
    optim="paged_adamw_8bit",
    gradient_checkpointing=True,
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=tokenized,
    data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
)
trainer.train()
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"LoRA adapter saved to: {OUTPUT_DIR}")
