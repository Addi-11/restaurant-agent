import json
import re
from jinja2 import Environment, FileSystemLoader
from utils.knowledge_base import restaurant_kb
from utils.logging_utils import logger
from pydantic import BaseModel
from typing import Optional, List
from utils.model import model_pipeline

env = Environment(loader=FileSystemLoader("templates"))


class SearchCriteria(BaseModel):
    cuisine: Optional[str]
    location: Optional[str]
    ambience: Optional[str]
    food_choice: Optional[str]
    price_range: Optional[str]


class SearchRestaurantResponse(BaseModel):
    restaurants: List[dict]
    message: Optional[str] = None


class SearchRestaurantService:

    @staticmethod
    def extract_json(model_output: str):
        try:
            matches = re.findall(r"\{[\s\S]*?\}", model_output)
            if not matches:
                raise ValueError("No JSON object found in model output.")

            json_str = matches[-1].strip()  # Take the last JSON block
            return json.loads(json_str)  # Parse JSON

        except Exception as e:
            logger.error(
                f"Failed to parse JSON from model output: {e}\nModel output: {model_output}"
            )
            return None

    def extract_search_criteria(self, user_message: str) -> Optional[SearchCriteria]:
        template = env.get_template("search_criteria.jinja2")
        prompt = template.render(user_message=user_message)
        # logger.info(f"Extract Search Criteria Prompt:\n{prompt}")

        model_output = model_pipeline(
            prompt, max_new_tokens=50, do_sample=False, temperature=0.1
        )[0]["generated_text"]
        # logger.info(f"Raw search criteria output: {model_output}")

        json_data = self.extract_json(model_output)
        if json_data is None:
            return None

        try:
            criteria = SearchCriteria(**json_data)
            logger.info(f"Extracted Search Criteria: {criteria.json()}")
            return criteria
        except Exception as e:
            logger.error(f"Failed to parse search criteria: {e}")
            return None

    def filter_restaurants(self, criteria: SearchCriteria) -> List[dict]:
        results = []
        for restaurant in restaurant_kb:
            matched = False

            if criteria.cuisine:
                if criteria.cuisine.lower() in restaurant.get("cuisine", "").lower():
                    matched = True

            if criteria.location:
                if criteria.location.lower() in restaurant.get("location", "").lower():
                    matched = True

            if criteria.ambience:
                if criteria.ambience.lower() in restaurant.get("ambience", "").lower():
                    matched = True

            if matched:
                results.append(restaurant)

        return results

    def process_request(self, user_message: str) -> SearchRestaurantResponse:

        criteria = self.extract_search_criteria(user_message)
        if criteria is None:
            return SearchRestaurantResponse(
                restaurants=[],
                message="Could not extract search criteria from your query.",
            )

        results = self.filter_restaurants(criteria)
        if not results:
            return SearchRestaurantResponse(
                restaurants=[], message="Sorry, no restaurants match your criteria."
            )
        else:
            return SearchRestaurantResponse(
                restaurants=results,
                message=f"Found {len(results)} restaurants matching your criteria.",
            )
