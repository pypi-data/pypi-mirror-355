import subprocess
from MultiProdigy.agents.agent_base import BaseAgent
from MultiProdigy.schemas.schemas import Message

class OllamaAgent(BaseAgent):
    def __init__(self, runtime):
        super().__init__("OllamaAgent", runtime)

    def handle_message(self, message: Message) -> str:
        print(f"[OllamaAgent] Received: {message.content}")

        command = [
            "ollama",
            "run",
            "tinylama",
            "--quiet",
            "--prompt",
            message.content
        ]

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',    # fix here: specify utf-8 decoding
                errors='replace'     # replace undecodable chars instead of crashing
            )
            output = result.stdout.strip()

            if not output:
                output = "[OllamaAgent] No output from ollama subprocess"

            print(f"[OllamaAgent] Output: {output}")
            return output

        except Exception as e:
            error_msg = f"[OllamaAgent] Exception: {str(e)}"
            print(error_msg)
            return error_msg

