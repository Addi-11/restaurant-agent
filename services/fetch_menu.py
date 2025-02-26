import re
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field
from typing import Optional
from utils.knowledge_base import restaurant_kb, menu_kb
from utils.model import model_pipeline
from utils.logging_utils import logger

env = Environment(loader=FileSystemLoader("templates"))


class ModelMenuResponse(BaseModel):
    restaurant_name: Optional[str] = Field(
        None, description="Extracted restaurant name"
    )
    confidence: float = Field(..., description="Confidence score for tool calling")
    error: Optional[str] = Field(None, description="Error message")


class MenuResponse(BaseModel):
    restaurant_name: str
    menu: list


class FetchMenuService:
    @staticmethod
    def fetch_restaurant_id(restaurant_name):
        for restaurant in restaurant_kb:
            if restaurant["name"].lower() == restaurant_name.lower():
                return restaurant["restaurant_id"]

        return None

    @staticmethod
    def fetch_menu(restaurant_id):
        for items in menu_kb:
            if items["restaurant_id"] == restaurant_id:
                return items["menu"]

        return None

    @staticmethod
    def call_model(user_message):
        template = env.get_template("fetch_menu.jinja2")
        prompt = template.render(user_message=user_message)

        model_response = model_pipeline(prompt)[0]["generated_text"]

        matches = re.findall(
            r"Assistant:\s*(.+?)\s*\(confidence:\s*([\d.]+)\)", model_response
        )
        if matches:
            restaurant_name, confidence_score = matches[-1]
            confidence_score = float(confidence_score)

            logger.info(
                f"Extracted Restaurant Name: {restaurant_name}, Confidence: {confidence_score}"
            )

            return ModelMenuResponse(
                restaurant_name=restaurant_name.strip(), confidence=confidence_score
            )

        return ModelMenuResponse(
            error="Could not extract restaurant name", confidence=0.0
        )

    @classmethod
    def process_request(self, user_message):
        model_response = self.call_model(user_message)

        if model_response.error:
            return {"error": model_response.error}

        restaurant_id = self.fetch_restaurant_id(model_response.restaurant_name)
        if not restaurant_id:
            return {"error": "Restaurant not found in database"}

        menu = self.fetch_menu(restaurant_id)
        return MenuResponse(restaurant_name=model_response.restaurant_name, menu=menu)
