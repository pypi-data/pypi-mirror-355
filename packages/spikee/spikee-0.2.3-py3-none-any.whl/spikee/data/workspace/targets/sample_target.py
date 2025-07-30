"""
sample_target.py

This is an example target for spikee that returns a pre-canned (mock) response. 
Use it as a template for writing real targets that call APIs or local models.

Usage:
    1. Place this file in your local `targets/` folder.
    2. Run the spikee test command, pointing to this target, e.g.:
         spikee test --dataset datasets/example.jsonl --target sample_target

Explanation:
    - For typical LLM completion, return a string that represents the model's response.
    - For guardrail usage (boolean success criteria), return True or False:
        * True indicates the attack was successful (guardrail bypassed).
        * False indicates the guardrail blocked the attack.
"""

import os
from dotenv import load_dotenv

# Load environment variables, if you need them (e.g., for API keys).
load_dotenv()

def process_input(input_text, system_message=None, logprobs=False):
    """
    Mock target function required by spikee.

    This function simulates an LLM or guardrail by returning a fixed response.
    In a real target:
      - You might instantiate a model client here (e.g., OpenAI, Azure, etc.)
      - You'd pass `input_text` (and optionally `system_message`) to the model or guardrail
      - Return one of the following:
          1) A string for standard "canary" success criteria
             (The plugin checks whether the "canary" word is in your response to measure success)
          2) A boolean for "boolean" success criteria (True = guardrail bypassed, False = blocked)

    Args:
        input_text (str): The main prompt or text to be processed.
        system_message (str, optional): A system or meta-prompt, if applicable.

    Returns:
        str or bool:
            - String if you're simulating an LLM response.
            - Boolean if you're simulating a guardrail result (True => attack successful).
    """

    # Optionally handle system_message, if your target needs it
    if system_message:
        # Possibly combine it with input_text, log it, or parse it further
        pass

    # Return a pre-canned response to mimic an LLM answer (string)
    # or you could return True / False to simulate a guardrail decision.
    mock_response = "Hello! I am a mock LLM."

    return mock_response
