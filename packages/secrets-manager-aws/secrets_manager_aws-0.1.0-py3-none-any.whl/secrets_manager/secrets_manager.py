import argparse
import boto3
import os
import tempfile
import subprocess
from botocore.exceptions import ClientError

class SecretsManager:
    def __init__(self, environment, service_name):
        self.environment = environment.upper()
        self.service_name = service_name.upper()
        self.prefix = f"/{self.environment}/{self.service_name}/"
        self.client = boto3.client("secretsmanager")

    def validate_inputs(self):
        """Validate environment and service name."""
        if not self.environment or not self.service_name:
            raise ValueError("Environment and service name cannot be empty.")
        if "/" in self.environment or "/" in self.service_name:
            raise ValueError("Environment and service name cannot contain '/'.")

    def list_secrets(self):
        """List all secrets with the given prefix."""
        secrets = []
        try:
            paginator = self.client.get_paginator("list_secrets")
            for page in paginator.paginate():
                for secret in page["SecretList"]:
                    if secret["Name"].startswith(self.prefix):
                        secrets.append(secret["Name"])
            print(secrets)
        except ClientError as e:
            raise Exception(f"Failed to list secrets: {e}")
        return secrets

    def get_secret_value(self, secret_name):
        """Get the value of a secret."""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return response.get("SecretString", "")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return None
            raise Exception(f"Failed to get secret {secret_name}: {e}")

    def create_temp_env_file(self):
        """Create a temporary .env file with secrets and return its path."""
        secrets = self.list_secrets()
        if not secrets:
            print(f"No secrets found for {self.prefix}. Would you like to create new secrets? (y/n): ")
            response = input().strip().lower()
            if response != 'y':
                raise Exception("No secrets exist and user chose not to create new ones.")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            for secret_name in sorted(secrets):
                secret_value = self.get_secret_value(secret_name)
                if secret_value is not None:
                    # Extract the secret name part after the prefix
                    secret_key = secret_name[len(self.prefix):]
                    f.write(f"{secret_key}={secret_value}\n")
            return f.name

    def open_editor(self, file_path):
        """Open the file in vim."""
        editor = "vim"
        try:
            subprocess.run([editor, file_path], check=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to open vim: {e}")
        except FileNotFoundError:
            raise Exception("Vim editor not found. Please ensure vim is installed.")

    def update_secrets_from_file(self, file_path):
        """Update Secrets Manager based on the .env file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Temporary secrets file {file_path} does not exist.")

        # Read secrets from .env file
        secrets_data = {}
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if not key.isupper():
                        raise ValueError(f"Secret name {key} must be in all caps.")
                    secrets_data[key] = value

        # Get existing secrets in Secrets Manager
        existing_secrets = set(self.list_secrets())
        new_secrets = set()

        # Add or update secrets
        for secret_key, secret_value in secrets_data.items():
            secret_name = f"{self.prefix}{secret_key}"
            new_secrets.add(secret_name)
            try:
                if secret_name in existing_secrets:
                    # Update existing secret
                    self.client.update_secret(
                        SecretId=secret_name,
                        SecretString=str(secret_value)
                    )
                    print(f"Updated secret: {secret_name}")
                else:
                    # Create new secret
                    self.client.create_secret(
                        Name=secret_name,
                        SecretString=str(secret_value)
                    )
                    print(f"Created secret: {secret_name}")
            except ClientError as e:
                print(f"Failed to process secret {secret_name}: {e}")

        # Delete secrets that are in Secrets Manager but not in the file
        for secret_name in existing_secrets - new_secrets:
            try:
                self.client.delete_secret(
                    SecretId=secret_name,
                    ForceDeleteWithoutRecovery=True
                )
                print(f"Deleted secret: {secret_name}")
            except ClientError as e:
                print(f"Failed to delete secret {secret_name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Manage secrets in AWS Secrets Manager.")
    parser.add_argument("-e", "--environment", required=True, help="Environment (e.g., dev, prod)")
    parser.add_argument("-s", "--servicename", help="Service name (e.g., myapp); defaults to current folder name")
    args = parser.parse_args()

    # Use current folder name if servicename is not provided
    service_name = args.servicename if args.servicename else os.path.basename(os.getcwd())

    try:
        manager = SecretsManager(args.environment, service_name)
        manager.validate_inputs()

        # Create temporary .env file
        temp_file_path = manager.create_temp_env_file()
        try:
            print(f"Opening vim to modify secrets for {manager.prefix}...")
            manager.open_editor(temp_file_path)
            print("Processing changes...")
            manager.update_secrets_from_file(temp_file_path)
            print("Secrets Manager updated successfully.")
        finally:
            # Delete the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                print(f"Deleted temporary file: {temp_file_path}")

    except Exception as e:
        # Ensure temporary file is deleted on error
        temp_file_path = locals().get("temp_file_path")
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"Deleted temporary file due to error: {temp_file_path}")
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
