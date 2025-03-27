import os
import json
from cryptography.fernet import Fernet

# Function to generate a key for encryption
def generate_key():
    return Fernet.generate_key()

# Function to load or create a key for encryption
def load_key():
    if os.path.exists("password_manager.key"):
        with open("password_manager.key", "rb") as key_file:
            return key_file.read()
    else:
        key = generate_key()
        with open("password_manager.key", "wb") as key_file:
            key_file.write(key)
        return key

# Encrypt password before saving
def encrypt_password(password, key):
    f = Fernet(key)
    encrypted_password = f.encrypt(password.encode())
    return encrypted_password.decode() # This fixes the binary bytes to JSON issue

# Decrypt password when retrieving
def decrypt_password(encrypted_password, key):
    f = Fernet(key)
    decrypted_password = f.decrypt(encrypted_password.encode())
    return decrypted_password.decode() ####

# Function to save password to the file
def save_password(service, password, key):
    encrypted_password = encrypt_password(password, key)
    
    if os.path.exists("passwords.json"):
        with open("passwords.json", "r") as file:
            data = json.load(file)
    else:
        data = {}
    
    data[service] = encrypted_password
    
    with open("passwords.json", "w") as file:
        json.dump(data, file, indent=4)
    
    print(f"Password for {service} saved successfully!")

# Function to retrieve password from the file
def retrieve_password(service, key):
    if os.path.exists("passwords.json"):
        with open("passwords.json", "r") as file:
            data = json.load(file)
        
        if service in data:
            encrypted_password = data[service]
            decrypted_password = decrypt_password(encrypted_password, key)
            print(f"Password for {service}: {decrypted_password}")
        else:
            print(f"No password found for {service}.")
    else:
        print("No passwords saved yet.")

# Main function to interact with the password manager
def main():
    key = load_key()

    while True:
        print("\nPassword Manager")
        print("1. Save Password")
        print("2. Retrieve Password")
        print("3. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            service = input("Enter the service name: ")
            password = input("Enter the password: ")
            save_password(service, password, key)
        elif choice == '2':
            service = input("Enter the service name to retrieve password: ")
            retrieve_password(service, key)
        elif choice == '3':
            print("Exiting password manager.")
            break
        else:
            print("Invalid option, please try again.")

if __name__ == "__main__":
    main()

