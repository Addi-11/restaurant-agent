import json
import re
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from pydantic import BaseModel, ValidationError
from typing import Optional
from utils.model import model_pipeline
from utils.logging_utils import logger
from utils.knowledge_base import reservation_kb

env = Environment(loader=FileSystemLoader("templates"))


class ReservationQuery(BaseModel):
    restaurant_name: Optional[str]
    num_people: Optional[int]
    date_time: Optional[str]


# Query and response can be same here
class ReservationResponse(BaseModel):
    restaurant_name: Optional[str]
    num_people: Optional[int]
    date_time: Optional[str]
    message: str


class ReserveRestaurantService:
    # TODO: filename is temporary to mock the service flow
    def __init__(self, filename="knowledge_base/reservations.json"):
        self.filename = filename
        self._load_reservations()

    @staticmethod
    def extract_reservation_details(user_message: str) -> Optional[ReservationQuery]:
        template = env.get_template("reserve_restaurant.jinja2")
        prompt = template.render(user_message=user_message)

        model_output = model_pipeline(
            prompt, max_new_tokens=30, do_sample=False, temperature=0.1
        )[0]["generated_text"]

        try:
            matches = re.findall(r"\{[\s\S]*?\}", model_output)
            if not matches:
                raise ValueError("No JSON object found in model output.")

            json_str = matches[-1].strip()
            query_dict = json.loads(json_str)

            return ReservationQuery(**query_dict)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(
                f"Failed to parse reservation details: {e}\nModel output: {model_output}"
            )
            return None

    def _load_reservations(self):
        try:
            with open(self.filename, "r") as file:
                self.reservations = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.reservations = []

    def _save_reservations(self):
        with open(self.filename, "w") as file:
            json.dump(self.reservations, file, indent=4)

    def reserve_table(self, restaurant_name: str, num_people: int, date_time: str):
        try:
            booking_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M")

            reservation = {
                "restaurant": restaurant_name,
                "num_people": num_people,
                "date_time": booking_time.strftime("%Y-%m-%d %H:%M"),
                "booking_id": len(self.reservations) + 1,
            }

            self.reservations.append(reservation)
            self._save_reservations()

            return ReservationResponse(
                restaurant_name=restaurant_name,
                num_people=num_people,
                date_time=booking_time.strftime("%Y-%m-%d %H:%M"),
                message=f"Table booked at {restaurant_name} for {num_people} people on {date_time}.",
            )
        except Exception as e:
            return ReservationResponse(message=f"Error: {str(e)}")

    def process_request(self, user_message: str) -> ReservationResponse:
        details = self.extract_reservation_details(user_message)

        if not details:
            return ReservationResponse(
                message="Could not extract reservation details. Please provide restaurant name, number of people, and date-time."
            )

        missing_fields = []
        if not details.restaurant_name:
            missing_fields.append("restaurant name")
            logger.info("Reserve Restaurant missing restaurant name")
        if not details.num_people:
            missing_fields.append("number of people")
            logger.info("Reserve Restaurant missing number of people")
        if not details.date_time:
            missing_fields.append("date and time")
            logger.info("Reserve Restaurant missing date and time")

        if missing_fields:
            return ReservationResponse(
                message=f"Please provide the {', '.join(missing_fields)} to proceed with the reservation."
            )

        try:
            booking_time = datetime.strptime(
                details.date_time, "%Y-%m-%d %H:%M"
            ).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return ReservationResponse(
                message="Invalid date format. Please use YYYY-MM-DD HH:MM."
            )

        return self.reserve_table(
            details.restaurant_name, details.num_people, booking_time
        )
