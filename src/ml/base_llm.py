from abc import ABC, abstractmethod
from typing import Optional
import instructor

from src.domain.news_analysis import NewsAnalysis

class BaseLLMEngine(ABC):
    system_prompt: str
    temperature: float
    model_name: str
    client: instructor.Instructor

    @abstractmethod
    def extract_news(self, text_to_analyze: str) -> Optional[NewsAnalysis]:
        ...