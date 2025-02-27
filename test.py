# 1. Figure out how to use API key from Google Studios
# 2. Using the API Key, and test out if it works
# 3. Once it works, Figure out how to read terminal outputs and store them as a variable (https://microsoft.github.io/vscode-essentials/en/10-create-an-extension.html)
# 4. With this variable the AI will try to fix the error and output it in the terminal
# 5. When it correctly outputs in the terminal


from google import genai


client = genai.Client(api_key="AIzaSyCQFYSOtcQ4XexFAY9MBbNQY3aHZeZbpYg")
response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain how AI works"
)
print(response.text)