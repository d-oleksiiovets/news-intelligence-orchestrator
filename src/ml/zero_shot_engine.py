from pathlib import Path
from typing import Union, List

import torch
from transformers import pipeline

from src.config.logger import StatusLog

CACHE_DIR = Path(__file__).parent.parent.parent / "models/cache" 

class ZeroShotEngine:
    def __init__(self, config: dict):
        model_id = config.get("zero_shot_model", "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli")
        self.batch_size = config.get("zero_shot_batch_size", 128)
        self.categories = config.get("categories", [])

        self.classifier = None

        self.category_map = {}
        self.candidate_labels = []
        self.hypothesis_template = "This news article is about {}."

        self._prepare_categories(self.categories)
        self._initialize_model(model_id)

    def _initialize_model(self, model_id: str):
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if device == "cuda" else torch.float32

            StatusLog.info(f"Loading zero-shot model '{model_id}' on {device}...")
            self.classifier = pipeline(
                "zero-shot-classification", 
                model=model_id,
                device=device,
                torch=dtype,
                model_kwargs={"cache_dir": CACHE_DIR}
            )
            StatusLog.success(f"Model ({model_id}) loaded successfully.")

        except Exception as e:
            StatusLog.fail(f"Critical error during model loading: {str(e)}")
            self.classifier = None

    def _prepare_categories(self, categories: list):
        if not categories:
            raise ValueError("Config error: 'categories' is missing or empty")
        
        for item in categories:
            for category_name, category_data in item.items():
                model_label = category_data["model_label"]
                threshold = category_data["threshold"]

                self.category_map[model_label] = {
                    "category_name": category_name,
                    "threshold": threshold
                }
                self.candidate_labels.append(model_label)
                
        if not self.candidate_labels:
             StatusLog.fail("No candidate labels found in configuration!")

    def predict(self, input_data: Union[str, List[str]]) -> Union[List[str], List[List[str]]]:
        if not self.classifier:
            StatusLog.fail("Engine not initialized. Cannot predict.")
            return []

        is_single = isinstance(input_data, str)
        texts = [input_data] if is_single else input_data

        if not texts:
            return []

        StatusLog.info("Running categories model prediction...")
        results = self.classifier(
            texts,
            candidate_labels=self.candidate_labels,
            hypothesis_template=self.hypothesis_template,
            batch_size=self.batch_size,
            multi_label=True,
            truncation=True
        )

        passed_categories = []

        for res in results:
            current_passed = []
            for label, score in zip(res["labels"], res["scores"]):
                info = self.category_map[label]
                if score >= info["threshold"]:
                    current_passed.append(info["category_name"])

            if current_passed:
                passed_categories.append(current_passed)
            else:
                passed_categories.append(["ignored"])

        StatusLog.success("Categories prediction finished successfully.")
        return passed_categories[0] if is_single else passed_categories