import argparse
import os
import sys
import uvicorn
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

def run_cli_mode(prompt: str):
    print("\n" + "="*60)
    print(f" Lovable Clone - Running in CLI Mode")
    print(f" Prompt: '{prompt}'")
    print("="*60 + "\n")
    
    from agent.graph import run_agent
    
    try:
        # Run agent synchronously
        result = run_agent(prompt)
        print("\n" + "="*60)
        print(" Application generated successfully in 'generated_project/' directory!")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n[ERROR] Generation failed: {e}", file=sys.stderr)
        sys.exit(1)

def run_ui_mode(host: str, port: int):
    print("\n" + "="*60)
    print(f" Lovable Clone Server starting at:")
    print(f" http://{host}:{port}")
    print(" Press Ctrl+C to stop the server.")
    print("="*60 + "\n")
    
    # Run uvicorn server
    uvicorn.run("agent_server:app", host=host, port=port, reload=True, log_level="info")

def main():
    parser = argparse.ArgumentParser(description="Lovable Clone - AI Web App Builder")
    parser.add_argument(
        "--prompt", 
        type=str, 
        help="Run generator directly from CLI with specified prompt"
    )
    parser.add_argument(
        "--ui", 
        action="store_true", 
        default=True,
        help="Start the interactive web dashboard (default)"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="127.0.0.1", 
        help="Host address for the web server"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port for the web server"
    )
    
    # If a prompt is explicitly passed, parse args to run CLI.
    # Otherwise, check if user runs standard python main.py without arguments.
    args, unknown = parser.parse_known_args()
    
    # If the user ran "python main.py prompt text here..." (without --prompt flag)
    # let's capture that and treat it as a prompt! This is extremely user-friendly.
    if not args.prompt and len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        args.prompt = " ".join(sys.argv[1:])
        
    if args.prompt:
        run_cli_mode(args.prompt)
    else:
        run_ui_mode(args.host, args.port)

if __name__ == "__main__":
    main()
