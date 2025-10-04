import subprocess
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import google.generativeai as genai

# --- Configure Logging and Google AI ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The client will automatically look for the GOOGLE_API_KEY environment variable
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    # CORRECTED: Switched to the universally stable 'gemini-pro' model
    model = genai.GenerativeModel('gemini-pro')
except KeyError:
    logger.error("GOOGLE_API_KEY not found in environment variables.")
    model = None
except Exception as e:
    logger.error(f"Error configuring Google AI: {e}")
    model = None

# Initialize the FastAPI app
app = FastAPI()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/task")
async def run_task(q: str):
    """
    Receives a task, uses the Google Gemini API to generate a shell command,
    executes it safely, and returns the output.
    """
    # Updated agent name to reflect the model change
    agent_name = "gemini-pro"
    user_email = "25ds1000058@ds.study.iitm.ac.in"
    agent_output = ""
    command_to_run = ""

    if not model:
        agent_output = "Error: The generative model is not configured. Check the server's GOOGLE_API_KEY."
    else:
        try:
            # 1. Ask the Gemini API to generate a shell command
            prompt = f"Based on the following request, provide a single, runnable shell command and nothing else. Do not add explanations, markdown, or any other text. Request: '{q}'"
            
            response = model.generate_content(prompt)
            
            # Extract the pure command from the API response and clean it
            command_to_run = response.text.strip()
            if command_to_run.startswith("```"):
                lines = command_to_run.split('\n')
                if len(lines) > 1:
                    command_to_run = '\n'.join(lines[1:-1]).strip()
                else: # Handle case of ```command``` on one line
                    command_to_run = command_to_run.strip('`').strip()


            logger.info(f"Generated command: {command_to_run}")

            # 2. Execute the generated command
            if command_to_run:
                result = subprocess.run(
                    command_to_run,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    agent_output = result.stdout.strip()
                else:
                    agent_output = f"Error executing command.\nSTDOUT:\n{result.stdout.strip()}\n\nSTDERR:\n{result.stderr.strip()}"
            else:
                agent_output = "Error: The model did not return a valid command."

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            agent_output = f"An unexpected error occurred: {str(e)}"

    # Construct the final JSON response
    response_data = {
        "task": q,
        "agent": agent_name,
        "generated_command": command_to_run,
        "output": agent_output,
        "email": user_email
    }
    
    return response_data

