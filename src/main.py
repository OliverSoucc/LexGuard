import mlflow
from src.agents.graph import lexguard_app
from src.config import MLFLOW_TRACKING_URI, EXPERIMENT_CHAT, RESEARCHER_MODEL_NAME

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment(EXPERIMENT_CHAT)
mlflow.langchain.autolog()


def chat():
    print("\n" + "=" * 60)
    print("🏛️ Welcome to LexGuard - Agentic AI Compliance")
    print(f"🧠 Model Active: {RESEARCHER_MODEL_NAME.split('/')[-1]}")
    print("Type 'exit' or 'quit' to close.")
    print("=" * 60 + "\n")

    while True:
        user_input = input("👤 USER: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break

        print("\n" + "-" * 60)

        initial_state = {
            "question": user_input,
            "context": "",
            "draft_answer": "",
            "critique": "",
            "status": "",
            "retry_count": 0,
            "is_safe": True
        }

        final_state = lexguard_app.invoke(initial_state)

        print("\n" + "=" * 60)
        print(f"🤖 LEXGUARD FINAL ANSWER (Generated after {final_state['retry_count']} iterations):")
        print(final_state['draft_answer'])
        print("=" * 60 + "\n")


if __name__ == "__main__":
    chat()