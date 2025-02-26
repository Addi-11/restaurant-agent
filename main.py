import json
import re
import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field
from typing import Optional

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Load the model pipeline
model_id = "meta-llama/Llama-3.1-8B"
pipeline = pipeline("text-generation", model=model_id, model_kwargs={"torch_dtype": torch.bfloat16}, device_map="auto")

# Initialize the jinja2 environment
env = Environment(loader=FileSystemLoader("templates"))

# Load Knowledge Bases
with open("knowledge_base/restaurant_db.json", "r") as f:
    restaurant_kb = json.load(f)

with open("knowledge_base/menu.json", "r") as f:
    menu_kb = json.load(f)

# Maintain chat context
chat_history = []

class ModelMenuResponse(BaseModel):
    restaurant_name: Optional[str] = Field(None, description="Extracted restaurant name")
    confidence: float = Field(..., description="Confidence score for tool calling")
    error: Optional[str] = Field(None, description="Error message")

class MenuResponse(BaseModel):
    restaurant_name: str
    menu: list

def fetch_restaurant_id(restaurant_name):
    for restaurant in restaurant_kb:
        if restaurant["name"].lower() == restaurant_name.lower():
            return restaurant["restaurant_id"]

    return None

def fetch_menu(restaurant_id):
    for ids in menu_kb:
        if ids["restaurant_id"] == restaurant_id:
            return ids["menu"]
      
    return {"error": "Restaurant not found"}

def call_model_menu(user_message):
    template = env.get_template("fetch_menu.jinja2")
    prompt = template.render(user_message=user_message)

    print("Prompt", prompt)
    model_response = pipeline(prompt)[0]['generated_text']
    print("Model Response: ", model_response)

    # extract model name and confidence score
    matches = re.findall(r'Response:\s*(.+?)\s*\(confidence:\s*([\d.]+)\)', model_response)
    if matches:
        restaurant_name, confidence_score = matches[-1]  # Get the last response
        confidence_score = float(confidence_score)

        return ModelMenuResponse(
            restaurant_name=restaurant_name.strip(),
            confidence=confidence_score
        )

    return ModelMenuResponse(error="Could not extract restaurant name", confidence=0.0)

def process_menu_request(req):
    model_response = call_model_menu(req)

    if model_response.error:
        return {"error": model_response.error}

    restaurant_id = fetch_restaurant_id(model_response.restaurant_name)
    if not restaurant_id:
        return {"error": "Restaurant not found in database"}

    menu = fetch_menu(restaurant_id)
    return MenuResponse(restaurant_name=model_response.restaurant_name, menu=menu)

def process_chat(user_message):
    chat_history.append({"user": user_message})
    
    model_response = call_model_menu(user_message)
    
    if model_response.error:
        response = {"error": model_response.error}
    else:
        restaurant_id = fetch_restaurant_id(model_response.restaurant_name)
        if not restaurant_id:
            response = {"error": "Restaurant not found in database"}
        else:
            menu = fetch_menu(restaurant_id)
            response = {"restaurant": model_response.restaurant_name, "menu": menu}

    chat_history.append({"assistant": response})
    return response