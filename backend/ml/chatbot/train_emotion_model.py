import os
import numpy as np
import evaluate
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)

# 1. Configuration
BASE_MODEL = "j-hartmann/emotion-english-distilroberta-base"
SAVE_PATH = "./ml/chatbot/trained_model/"
DATASET_NAME = "go_emotions"

# We will map to 7 core emotions
LABEL_LIST = ["anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral"]
label2id = {label: i for i, label in enumerate(LABEL_LIST)}
id2label = {i: label for label, i in label2id.items()}

# 2. Load Tokenizer & Model
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

model = AutoModelForSequenceClassification.from_pretrained(
    BASE_MODEL,
    num_labels=len(LABEL_LIST),
    id2label=id2label,
    label2id=label2id,
    ignore_mismatched_sizes=True
)

# 3. Load Dataset
dataset = load_dataset(DATASET_NAME)

# GoEmotions has 27 labels → map to our 7
goemotions_labels = dataset["train"].features["labels"].feature.names

# Mapping GoEmotions → our labels
mapping = {
    "anger": "anger",
    "annoyance": "anger",
    "disapproval": "anger",

    "disgust": "disgust",

    "fear": "fear",
    "nervousness": "fear",

    "joy": "joy",
    "amusement": "joy",
    "approval": "joy",
    "gratitude": "joy",
    "love": "joy",
    "optimism": "joy",
    "relief": "joy",
    "pride": "joy",
    "excitement": "joy",
    "caring": "joy",
    "desire": "joy",

    "sadness": "sadness",
    "disappointment": "sadness",
    "grief": "sadness",
    "remorse": "sadness",
    "embarrassment": "sadness",

    "surprise": "surprise",
    "realization": "surprise",
    "confusion": "surprise",
    "curiosity": "surprise",

    "neutral": "neutral"
}

# 4. Preprocess Labels
def map_labels(example):
    if len(example["labels"]) == 0:
        example["label"] = label2id["neutral"]
        return example

    # take first label (simplification)
    original_label = goemotions_labels[example["labels"][0]]

    mapped = mapping.get(original_label, "neutral")
    example["label"] = label2id[mapped]

    return example

dataset = dataset.map(map_labels)

# 5. Tokenization
def preprocess_function(examples):
    return tokenizer(examples["text"], truncation=True)

tokenized_ds = dataset.map(preprocess_function, batched=True)

# Remove unnecessary columns
tokenized_ds = tokenized_ds.remove_columns(["text", "labels"])

# 6. Data Collator
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# 7. Metrics
metric = evaluate.load("accuracy")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)

# 8. Training Arguments
training_args = TrainingArguments(
    output_dir="./ml/training_results",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    logging_dir="./logs",
)

# 9. Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_ds["train"],
    eval_dataset=tokenized_ds["validation"],
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# 10. Train
print("Training emotion model (GoEmotions)...")
trainer.train()

# 11. Save Model
if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)

trainer.save_model(SAVE_PATH)
tokenizer.save_pretrained(SAVE_PATH)

print(f"Model saved at {SAVE_PATH}")