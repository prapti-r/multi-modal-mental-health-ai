"""
Train a CNN facial emotion classifier on FER2013.
"""

import argparse
import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, f1_score
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
import torchvision.models as models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_CKPT_OUT = Path(__file__).parent.parent / "checkpoints" / "cnn_fer2013"

# FER2013 label taxonomy
FER2013_LABELS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
LABEL2ID = {l: i for i, l in enumerate(FER2013_LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

# matches DeepFace output labels
FER2013_COLLAPSE: dict[str, str] = {
    "angry":    "anger",
    "disgust":  "anger",
    "fear":     "anxiety",
    "happy":    "positive",
    "sad":      "sadness",
    "surprise": "neutral",
    "neutral":  "neutral",
}

# Image dimensions 
IMG_SIZE = 48


# Dataset

class FER2013Dataset(Dataset):
    """
    Loads FER2013 from the Kaggle CSV format.
    """

    def __init__(
        self,
        csv_path: Path,
        split: str = "Training",
        augment: bool = False,
    ):
        import pandas as pd
        from torchvision import transforms
        from PIL import Image

        df = pd.read_csv(csv_path)
        df = df[df["Usage"] == split].reset_index(drop=True)

        logger.info(f"FER2013 {split}: {len(df)} samples.")

        self.labels = df["emotion"].values.astype(np.int64)

        self.raw_pixels = [np.fromstring(p, sep=" ", dtype=np.uint8).reshape(48, 48) 
            for p in df["pixels"]
        ]

        base_transforms = [
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.Lambda(lambda x: x.convert("RGB")), # Grayscale to RGB (3 identical channels)
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]) # ImageNet Stats
        ]

        # Parse pixel strings → (N, 1, 48, 48) float32 tensors normalised to [-1, 1]
        # pixels = np.array(
        #     [np.fromstring(p, sep=" ", dtype=np.float32) for p in df["pixels"]],
        #     dtype=np.float32,
        # )
        # # Instead of (1, 48, 48), make it (3, 48, 48)
        # pixels = pixels.repeat(1, 3, 1, 1)
        # pixels = pixels.reshape(-1, 1, IMG_SIZE, IMG_SIZE) / 127.5 - 1.0
        # self.images = torch.tensor(pixels)

        # Augmentation pipeline for training set
        if augment:
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(15),
                transforms.Resize((224, 224)),
                transforms.Lambda(lambda x: x.convert("RGB")),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:
            self.transform = transforms.Compose(base_transforms)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int):
        img = self.raw_pixels[idx]
        label = self.labels[idx]
        if self.transform:
            img = self.transform(img)
        return img, label


# Model 


class FerResNetClassifier(nn.Module):
    """
    Uses pre-trained weights from ImageNet to give the model a 'head start'.
    """
    def __init__(self, n_classes: int = 7):
        super().__init__()
        
        # Load the pre-trained ResNet18 'Engine'
        # 'DEFAULT' uses the best available pre-trained weights
        self.backbone = models.resnet18(weights='DEFAULT')
        
        # Fix the Input Layer
        # ResNet expects 3 colors (RGB), but FER2013 is Grayscale (1 channel).
        # change the first layer to accept 1 channel.
        #self.backbone.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        
        # Fix the Output Layer
        # ResNet18 originally has 1000 classes. change it to your 7 emotions.
        num_ftrs = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(num_ftrs, n_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


# Training loop 

def train(
    fer2013_csv: Path,
    epochs: int = 60,
    batch_size: int = 64,
    learning_rate: float = 1e-3,
) -> None:

    if not fer2013_csv.exists():
        raise FileNotFoundError(
            f"FER2013 CSV not found at {fer2013_csv}. "
            "Download from: https://www.kaggle.com/datasets/msambare/fer2013"
        )

    # Datasets
    train_ds = FER2013Dataset(fer2013_csv, split="Training",   augment=True)
    val_ds = FER2013Dataset(fer2013_csv, split="PublicTest", augment=False)

    # Class weights — FER2013 is heavily imbalanced (happy >> disgust)
    class_weights_arr = compute_class_weight(
        "balanced",
        classes=np.unique(train_ds.labels),
        y=train_ds.labels,
    )
    class_weights = torch.tensor(class_weights_arr, dtype=torch.float)
    logger.info(
        f"Class weights: "
        f"{ {FER2013_LABELS[i]: round(w, 3) for i, w in enumerate(class_weights_arr)} }"
    )

    # Weighted sampler
    sample_weights = torch.tensor([class_weights_arr[y] for y in train_ds.labels])
    sampler = WeightedRandomSampler(
        sample_weights, num_samples=len(train_ds), replacement=True
    )

    train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler,  num_workers=2)
    val_loader = DataLoader(val_ds,   batch_size=batch_size * 2, shuffle=False, num_workers=2)

    # Model, loss, optimizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = FerResNetClassifier(n_classes=len(FER2013_LABELS)).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_f1 = 0.0
    patience_left = 10

    logger.info(f"Training FER2013 CNN on {device} — {epochs} epochs max.")

    for epoch in range(1, epochs + 1):
        # Train 
        model.train()
        train_loss, correct, total = 0.0, 0, 0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            logits = model(imgs)
            loss = criterion(logits, labels)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item()
            correct += (logits.argmax(dim=1) == labels).sum().item()
            total += labels.size(0)

        train_acc = correct / total

        # Validate 
        model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for imgs, labels in val_loader:
                preds = model(imgs.to(device)).argmax(dim=1).cpu().tolist()
                all_preds += preds
                all_labels += labels.tolist()

        macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
        scheduler.step()

        logger.info(
            f"Epoch {epoch:03d}/{epochs}  "
            f"loss={train_loss/len(train_loader):.4f}  "
            f"train_acc={train_acc:.3f}  "
            f"val_macro_f1={macro_f1:.4f}"
        )

        if macro_f1 > best_f1:
            best_f1 = macro_f1
            patience_left = 10
            _CKPT_OUT.mkdir(parents=True, exist_ok=True)
            torch.save(model, _CKPT_OUT / "model.pt")
            logger.info(f"  ✓ Best F1={best_f1:.4f} — checkpoint saved.")
        else:
            patience_left -= 1
            if patience_left == 0:
                logger.info("Early stopping triggered.")
                break

    # Final classification report
    best_model = torch.load(_CKPT_OUT / "model.pt", map_location="cpu", weights_only=False)    
    best_model.eval()
    all_preds = []
    with torch.no_grad():
        for imgs, labels in val_loader:
            all_preds += best_model(imgs).argmax(dim=1).tolist()

    logger.info(f"\nBest val macro-F1: {best_f1:.4f}")
    logger.info(
        "\n" + classification_report(
            all_labels, all_preds, target_names=FER2013_LABELS, zero_division=0
        )
    )
    logger.info(f"Model saved to: {_CKPT_OUT / 'model.pt'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train CNN on FER2013.")
    parser.add_argument("--fer2013_csv", type=Path, required=True,
                        help="Path to fer2013.csv from Kaggle.")
    parser.add_argument("--epochs",     type=int,   default=60)
    parser.add_argument("--batch_size", type=int,   default=64)
    parser.add_argument("--lr",         type=float, default=1e-3)
    args = parser.parse_args()

    train(
        fer2013_csv=args.fer2013_csv,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
    )