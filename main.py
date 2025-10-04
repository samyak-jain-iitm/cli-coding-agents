import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

# Initialize the FastAPI app
app = FastAPI()

# Set up CORS to allow all cross-origin GET requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["GET"], # Allows only GET method
    allow_headers=["*"],
)

@app.get("/task")
async def run_task(q: str):
    """
    Receives a task description, forwards it to the GitHub Copilot CLI,
    executes the suggested shell command, and returns the output.
    """
    agent_name = "copilot-cli"
    user_email = "25ds100005@ds.study.iitm.ac.in"
    
    # This is the command that will be executed in the shell.
    # It asks Copilot CLI to suggest a shell command for the query `q`
    # and then immediately executes that suggestion using a pipe `|` to `sh`.
    command = f'gh copilot suggest -t shell "{q}" | sh'
    
    agent_output = ""
    try:
        # Execute the command and capture the output
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120  # Add a timeout of 2 minutes
        )

        # Clean up the output
        if result.returncode == 0:
            # The stdout contains the result of the executed command
            agent_output = result.stdout.strip()
        else:
            # If there was an error, capture it
            agent_output = f"Error: {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        agent_output = "Error: The command timed out after 120 seconds."
    except Exception as e:
        agent_output = f"An unexpected error occurred: {str(e)}"

    # Construct the final JSON response
    response_data = {
        "task": q,
        "agent": agent_name,
        "output": agent_output,
        "email": user_email
    }
    
    return response_data

# Example of how to run this app locally:
# uvicorn main:app --reload