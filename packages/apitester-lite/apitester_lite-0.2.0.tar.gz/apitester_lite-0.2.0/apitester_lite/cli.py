import sys
from .core import run_test,create_test_interactively

def main():
    if len(sys.argv) < 2:
        print("""
    Usage:
    apitester-lite create
        → Launches an interactive wizard to generate a new test case JSON file.
        → You'll be prompted to enter the endpoint, method, request body, expected response, etc.
        → The test will be saved inside the `tests/` directory.

    apitester-lite run <test_file>
        → Runs an API test based on the specified JSON test file.
        → Example: apitester-lite run tests/test_post_users.json

    Description:
    apitester-lite is a lightweight CLI tool for testing REST APIs.
    You can create test definitions interactively and execute them using simple commands.

    Notes:
    - Ensure your endpoint (e.g., localhost:8080 etc or public API) is reachable.
    - The test JSON file should contain fields like method, URL, expected status, and optionally expected response content.

    """)
        return


    command = sys.argv[1]

    if command == "run":
        if len(sys.argv) < 3:
            print("❗Please specify the test file to run.")
            return
        run_test(sys.argv[2])

    elif command == "create":
        create_test_interactively()
    else:
        print("❗Unknown command. Use 'run' or 'create'.")

if __name__ == "__main__":
    main()
