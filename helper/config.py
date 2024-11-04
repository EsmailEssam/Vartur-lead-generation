import os
from openai import OpenAI
from dotenv import load_dotenv


# Load the Key token
_ = load_dotenv(override=True)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)