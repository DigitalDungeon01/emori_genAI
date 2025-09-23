from main_graph.main_graph import create_main_graph
from shared.state import MainState

def interactive_chat():
    app = create_main_graph()
    
    print("Mental Health Chat Companion - Emori")
    print("Enter 'quit' to exit\n")
    
    while True:
        user_id = input("Enter your user ID (MongoDB ObjectId): ")
        if user_id.lower() == 'quit':
            break
            
        user_query = input("Enter your message: ")
        if user_query.lower() == 'quit':
            break
        
        try:
            result = app.invoke({
                "user_query": user_query,
                "user_id": user_id
            })
            
            print(f"\nEmori: {result.get('answer', 'No response generated')}")
            
            if result.get('warning_text'):
                print(f"\nAlert: {result.get('warning_text')}")
            
            if result.get('calc_result'):
                print(f"Risk Score: {result.get('calc_result', 0):.2f}")
            
            print("-" * 50)
            
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")

if __name__ == "__main__":
    interactive_chat()