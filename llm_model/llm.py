import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

llm_model = ChatOpenAI(
    model="gpt-4.1-mini",
    # model="gpt-5-nano", reasoning model
    api_key=OPENAI_API_KEY,
)

