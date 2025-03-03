import json
import re
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from utils.model import model_pipeline
from utils.logging_utils import logger

env = Environment(loader=FileSystemLoader("templates"))

class AvailabilityQuery(BaseModel):
    restaurant_name: Optional[str]
    date_time: Optional[str]
    num_people: Optional[int]

class AvailabilityResponse(BaseModel):
    restaurant_name: str
    date_time: str
    num_people: int
    available: bool
    message: str

class CheckAvailabilityService:
    def __init__(self, filename="knowledge_base/reservations.json"):
        self.filename = filename
        self._load_reservations()

    def _load_reservations(self):
        try:
            with open(self.filename, "r") as file:
                self.reservations = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.reservations = []

    @staticmethod
    def extract_availability_details(user_message: str) -> Optional[AvailabilityQuery]:
        template = env.get_template("check_availability.jinja2")
        prompt = template.render(user_message=user_message)
        
        model_output = model_pipeline(prompt, max_new_tokens=30, do_sample=False, temperature=0.1)[0]["generated_text"]
        
        try:
            matches = re.findall(r"\{[\s\S]*?\}", model_output)
            if not matches:
                raise ValueError("No JSON object found in model output.")
            
            json_str = matches[-1].strip()
            query_dict = json.loads(json_str)
            
            return AvailabilityQuery(**query_dict)
        except Exception as e:
            logger.error(f"Failed to parse availability details: {e}\nModel output: {model_output}")
            return None

    def check_availability(self, restaurant_name: str, date_time: str, num_people: int) -> AvailabilityResponse:
        requested_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M")

        # Assuming the restaurant has a max capacity of 50 per time slot
        max_capacity = 50
        booked_seats = sum(
            res["num_people"] for res in self.reservations
            if res["restaurant"] == restaurant_name and res["date_time"] == date_time
        )

        available_seats = max_capacity - booked_seats
        if available_seats >= num_people:
            return AvailabilityResponse(
                restaurant_name=restaurant_name,
                date_time=date_time,
                num_people=num_people,
                available=True,
                message=f"Yes! {restaurant_name} has {num_people} seats available on {date_time}."
            )
        else:
            return AvailabilityResponse(
                restaurant_name=restaurant_name,
                date_time=date_time,
                num_people=num_people,
                available=False,
                message=f"Sorry, {restaurant_name} does not have {num_people} seats available on {date_time}."
            )

    def process_request(self, user_message: str) -> AvailabilityResponse:
        details = self.extract_availability_details(user_message)
        if not details:
            return AvailabilityResponse(
                restaurant_name="Unknown",
                date_time="Unknown",
                num_people=0,
                available=False,
                message="Could not extract availability details. Please provide restaurant name, date-time, and number of people."
            )

        missing_fields = []
        if not details.restaurant_name:
            missing_fields.append("restaurant name")
        if not details.date_time:
            missing_fields.append("date and time")
        if not details.num_people:
            missing_fields.append("number of people")

        if missing_fields:
            return AvailabilityResponse(
                restaurant_name=details.restaurant_name or "Unknown",
                date_time=details.date_time or "Unknown",
                num_people=details.num_people or 0,
                available=False,
                message=f"Please provide the {', '.join(missing_fields)} to check availability."
            )

        try:
            formatted_date_time = datetime.strptime(details.date_time, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return AvailabilityResponse(
                restaurant_name=details.restaurant_name,
                date_time=details.date_time,
                num_people=details.num_people,
                available=False,
                message="Invalid date format. Please use YYYY-MM-DD HH:MM."
            )

        return self.check_availability(details.restaurant_name, formatted_date_time, details.num_people)
