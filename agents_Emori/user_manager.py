import sys
import os
sys.path.append('/app')

from services.crud import create_mental_health_db
from config import get_database_config
from bson import ObjectId

def create_user():
    name = input("Enter user name: ")
    
    try:
        config = get_database_config()
        with create_mental_health_db(config["connection"], config["database"]) as db:
            new_user = db.create_user(name)
            user_id = str(new_user["_id"])
            print(f"User created successfully!")
            print(f"User ID: {user_id}")
            print(f"Name: {name}")
            return user_id
    except Exception as e:
        print(f"Failed to create user: {e}")
        return None

def delete_user():
    """Delete a user by ObjectId"""
    user_id = input("Enter user ID to delete: ")
    
    try:
        with create_mental_health_db("mongodb://host.docker.internal:27017/") as db:
            success = db.delete_user(user_id)
            if success:
                print(f"User {user_id} deleted successfully!")
            else:
                print(f"User {user_id} not found or could not be deleted.")
    except Exception as e:
        print(f"Failed to delete user: {e}")
        
def delete_database():
    """Delete the entire mental_health_db database"""
    confirm = input("Are you sure you want to delete the entire database? (type 'yes'): ")
    if confirm.lower() == 'yes':
        try:
            with create_mental_health_db("mongodb://host.docker.internal:27017/") as db:
                db.client.drop_database("mental_health_db")
                print("Database 'mental_health_db' deleted successfully")
        except Exception as e:
            print(f"Failed to delete database: {e}")
    else:
        print("Database deletion cancelled")

def main_menu():
    print("Mental Health Chat - User Manager")
    print("1. Create new user")
    print("2. Delete user") 
    print("3. Delete entire database")
    print("4. Exit")
    
    while True:
        choice = input("\nSelect option (1-4): ")
        
        if choice == "1":
            create_user()
        elif choice == "2":
            delete_user()
        elif choice == "3":
            delete_database()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please select 1-3.")

if __name__ == "__main__":
    main_menu()