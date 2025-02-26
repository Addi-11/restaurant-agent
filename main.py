import re
from jinja2 import Environment, FileSystemLoader
from services.fetch_menu import FetchMenuService
from services.generate_response import GenerateResponseService
from utils.model import model_pipeline
from utils.logging_utils import logger

env = Environment(loader=FileSystemLoader("templates"))

# INTENT-SERVICE MAPPING
INTENT_TO_SERVICE = {
    "fetch_menu": FetchMenuService,
    # "reserve_restaurant":
    # "check_availability":
    # "search_restaurant":
    "generate_reponse": GenerateResponseService
}


def detect_intent(user_message):
    template = env.get_template("classify_intent.jinja2")
    prompt = template.render(user_message=user_message)

    model_response = model_pipeline(prompt)[0]["generated_text"]
    logger.info(f"Model raw response: {model_response}")
    match = re.search(r"Intent:\s*(\w+)\s+Confidence:\s*([\d.]+)", model_response)

    if match:
        intent = match.group(1)
        confidence = float(match.group(2))
        logger.info(f"Extracted Intent: {intent}, Confidence: {confidence}")
        if confidence > 0.7:
            return intent

    logger.info("Switching to default intent.")
    return "generate_reponse"


def process_chat(user_message):
    intent = detect_intent(user_message)
    service = INTENT_TO_SERVICE[intent]()
    return service.process_request(user_message)
