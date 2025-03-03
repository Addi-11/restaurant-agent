import re
from jinja2 import Environment, FileSystemLoader
from services.fetch_menu import FetchMenuService
from services.search_restaurant import SearchRestaurantService
from services.fetch_price import FetchPriceService
from services.reserve_restaurant import ReserveRestaurantService
from services.check_availability import CheckAvailabilityService
from utils.model import model_pipeline
from utils.logging_utils import logger

env = Environment(loader=FileSystemLoader("templates"))

# INTENT-SERVICE MAPPING
INTENT_TO_SERVICE = {
    "fetch_menu": FetchMenuService,
    "reserve_restaurant": ReserveRestaurantService,
    "check_availability": CheckAvailabilityService,
    "search_restaurant": SearchRestaurantService,
    "fetch_price": FetchPriceService,
}


def detect_intent(user_message):
    template = env.get_template("classify_intent.jinja2")
    prompt = template.render(user_message=user_message)

    model_response = model_pipeline(prompt, do_sample=False, temperature=0.1)[0][
        "generated_text"
    ]
    lines = model_response.strip().split("\n")

    for line in reversed(lines):
        match = re.search(r"Intent:\s*([\w_]+)\s+Confidence:\s*([\d.]+)", line)
        if match:
            intent = match.group(1)
            confidence = float(match.group(2))
            logger.info(f"Extracted Intent: {intent}, Confidence: {confidence}")
            if confidence > 0.9:
                return intent

    logger.info("Default Intent Extracted.")
    return "general_response"


def generate_final_response(user_message, conversation_history, tool_result):
    context = "\n".join(
        [
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in conversation_history
        ]
    )
    template = env.get_template("generate_response.jinja2")
    prompt = template.render(
        conversation=context, user_message=user_message, tool_result=tool_result
    )

    raw_response = model_pipeline(
        prompt, max_new_tokens=200, do_sample=True, temperature=0.7
    )[0]["generated_text"]
    marker = "Final Assistant Response:"
    if marker in raw_response:
        final_response = raw_response.split(marker, 1)[1].strip()
    else:
        final_response = raw_response.strip()
    final_response = " ".join(final_response.split())
    return final_response


def process_chat(user_message, conversation_history):
    logger.info(f"User Query: {user_message}")
    intent = detect_intent(user_message)
    tool_result = None

    if intent in INTENT_TO_SERVICE and intent != "general_response":
        service = INTENT_TO_SERVICE[intent]()
        tool_result = service.process_request(user_message)
        logger.info(f"Tool result: {tool_result}")

    final_response = generate_final_response(
        user_message, conversation_history, tool_result
    )
    return final_response
