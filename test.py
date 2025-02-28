#I am in branch Extension

# 1. Figure out how to use API key from Google Studios
# 2. Using the API Key, and test out if it works
# 3. Once it works, Figure out how to read terminal outputs and store them as a variable (https://microsoft.github.io/vscode-essentials/en/10-create-an-extension.html)
# 4. With this variable the AI will try to fix the error and output it in the terminal
# 5. When it correctly outputs in the terminal

import os
from google import genai
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()
api = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key = api)
response = client.models.generate_content(
    model="gemini-2.0-flash-lite", contents="Explain how AI works" #Input error code and ask how to solve it
)
print(response.text)