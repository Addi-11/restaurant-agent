import re
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field
from typing import Optional
from utils.knowledge_base import restaurant_kb, menu_kb
from utils.model import model_pipeline
from utils.logging_utils import logger

env = Environment(loader=FileSystemLoader("templates"))

class GenerateResponseService:
    @staticmethod
    def call_model(user_message):
        template = env.get_template("conversation_prompt.jinja2")
        prompt = template.render(user_message=user_message)
        
        model_response = model_pipeline(prompt)[0]["generated_text"]
        return model_response

    @classmethod
    def process_request(self, user_message):
        model_response = self.call_model(user_message)
        return model_response

