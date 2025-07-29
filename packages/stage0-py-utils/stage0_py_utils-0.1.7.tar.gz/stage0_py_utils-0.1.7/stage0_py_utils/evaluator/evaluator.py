import os
import re

import ollama
from stage0_py_utils.echo.message import Message

import logging
logger = logging.getLogger(__name__)

class Evaluator:
    """
    Evaluate the LLM replies to a set of test conversations. 
    Each conversation is built up one message at a time, and at each "assistant" message 
    a LLM reply is created and compared against the message from the test conversation. 
    
    Grading a response against an expected value is done by a separate grading LLM, with an 
    engineered prompt that compares an expected value with a given value and grades how
    "alike" they are as a number between 0 and 1. 
    
    Parameters
    name: Configuration name
    model: LLM Model Name for evaluation
    grade_model: LLM Model for grading responses
    grade_prompt_files: A list of csv file names found in the input_folder/grader folder
    grade_prompt: Array of LLM messages used as the prompt for grading a reply. 
            These can be loaded with a Evaluator.loader.load_messages(grade_prompt_files).
    prompt_files: A list of csv file names in the input_folder/prompts folder. 
    prompts: Array of LLM messages used as an engineered prompt at the beginning of each test conversation. 
            These can be loaded with an Evaluator.loader.load_formatted_messages(prompt_files)
    conversations: A dictionary of filename.csv entries, with Array of LLM messages to be evaluated.
            These can be loaded with Evaluator.loader.load_formatted_conversations(test_conversation_files)
    """
    def __init__(self, name=None, model=None, grade_model=None, grade_prompt_files=None, grade_prompt=None, prompt_files=None, prompt=None, conversations=None):
        """ """
        self.name = name
        self.model = model
        self.grade_model = grade_model
        self.grade_prompt_files = grade_prompt_files
        self.grade_prompt = grade_prompt    
        self.prompt_files = prompt_files
        self.prompt = prompt
        self.conversations = conversations  
        logger.info(f"Evaluator {self.name} Initialized")

    def evaluate(self):
        """Evaluate the conversations and report the grades"""
        grades = {}
        for name, conversation in self.conversations.items():
            logger.info(f"{self.name} Grading {name}")
            grades[name] = self.grade_conversation(conversation)
        return grades

    def grade_conversation(self, conversation=[]):
        messages = self.prompt[:]
        grades = []
        for message in conversation:
            messages.append(message)
            if message["role"] == "user":
                reply, latency = self.chat(messages=messages)
            elif message["role"] == "assistant":
                expected=message["content"]
                given=reply["content"]
                grade = self.grade_reply(expected=expected, given=given)
                grades.append({
                    "expected":expected, 
                    "given":given, 
                    "latency":latency, 
                    "grade":grade
                })
                logger.info(f"Graded Answer {len(grades)}")
        return grades
        
    def grade_reply(self, expected=None, given=None):
        # Use LLM model with grading prompts to grade message
        messages = self.grade_prompt[:]
        messages.append({"role":"user", "content": f"Given:\n{given}\nExpected:\n{expected}"})
        reply, latency = self.chat(model=self.grade_model, messages=messages)
        content = reply["content"]
        grade = None
        try:
            match = re.search(r"the grade is (\d+(\.\d+)?)", content, re.IGNORECASE)
            if match:
                grade = float(match.group(1)) 
        except Exception:
            logger.warning(f"Grader didn't return a valid float: {content}")
            grade = None
        return grade
    
    def chat(self, model=None, messages=None):
        # Get chat response to conversation
        # use ollama.chat(model=self.model, messages=messages)
        # return a LLM Message dict (role, content)
        model = model or self.model
        logger.debug(f"Chat Request model {model}, message: {messages[len(messages)-1]}")
        reply = ollama.chat(model=model, messages=messages)
        logger.debug(f"Chat reply {reply.message.content}")
        latency = reply.total_duration
        response = {
            "role":reply.message.role, 
            "content":reply.message.content
        }
        return response, latency
        