import os
import stratdev

def authenticate_alpaca():
    env_path = stratdev.__file__[:-11] + 'backend'
    backend_files = [f for f in os.listdir(env_path)]

    if env_path and '.env' in backend_files:
        print('.env file found, stratdev ready to use')
        return

    try:
        api_key = input("Enter alpaca-py API key: ")
        secret_key = input("Enter alpaca-py SECRET key: ")

        with open (env_path + '/.env', 'w') as f:
            f.write(f'API_KEY={api_key}\n')
            f.write(f'SECRET_KEY={secret_key}\n')

        print('.env file created successfully')

    except Exception:
        print(f'Error creating .env file')