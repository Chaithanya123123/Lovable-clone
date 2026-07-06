import os
from dotenv import load_dotenv
from langchain_groq.chat_models import ChatGroq

# Load environment variables (expects GROQ_API_KEY in .env)
load_dotenv()
api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables.")

# Initialize the Groq LLM
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.7, api_key=api_key)

def chat_loop():
    print("Chatbot is ready. Type your message and press Enter. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        try:
            response = llm.invoke(user_input)
            # The response from LangChain's ChatGroq is a Message object; extract content.
            if hasattr(response, "content"):
                answer = response.content
            else:
                answer = str(response)
            print(f"Bot: {answer}\n")
        except Exception as e:
            print(f"[ERROR] {e}\n")

if __name__ == "__main__":
    chat_loop()
