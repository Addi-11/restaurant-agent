import json
import re
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from typing import Optional, List
from utils.model import model_pipeline
from utils.logging_utils import logger
from utils.knowledge_base import menu_kb

env = Environment(loader=FileSystemLoader("templates"))


class PriceQuery(BaseModel):
    dish_name: str
    restaurant_name: Optional[str] = None


class FetchPriceResponse(BaseModel):
    dish_name: str
    price: Optional[float] = None
    restaurant_name: Optional[str] = None
    message: Optional[str] = None


class FetchPriceService:

    @staticmethod
    def extract_dish_query(user_message: str) -> Optional[PriceQuery]:
        template = env.get_template("fetch_price.jinja2")
        prompt = template.render(user_message=user_message)

        model_output = model_pipeline(
            prompt, max_new_tokens=30, do_sample=False, temperature=0.1
        )[0]["generated_text"]

        try:
            matches = re.findall(r"\{[\s\S]*?\}", model_output)
            if not matches:
                raise ValueError("No JSON object found.")
            json_str = matches[-1].strip()
            query_dict = json.loads(json_str)
            return PriceQuery(**query_dict)
        except Exception as e:
            logger.error(
                f"Failed to parse dish price query: {e}\nModel output: {model_output}"
            )
            return None

    def process_request(self, user_message: str) -> FetchPriceResponse:
        query = self.extract_dish_query(user_message)
        if not query:
            return FetchPriceResponse(
                dish_name="", message="Could not extract dish details from query."
            )

        found = []
        for restaurant in menu_kb:
            restaurant_name = restaurant.get("name", "")
            for dish in restaurant.get("menu", []):
                if query.dish_name.lower() in dish.get("dish_name", "").lower():
                    found.append(
                        {
                            "restaurant_name": restaurant_name,
                            "dish_name": dish.get("dish_name"),
                            "price": dish.get("price"),
                        }
                    )

        if not found:
            return FetchPriceResponse(
                dish_name=query.dish_name, message="Dish not found in any restaurant."
            )

        # TODO: for simplicity first price is returned
        result = found[0]
        return FetchPriceResponse(
            dish_name=result["dish_name"],
            price=result["price"],
            restaurant_name=result["restaurant_name"],
            message="Dish found.",
        )
