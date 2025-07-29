import ollama

class OllamaLLMClient:
    """_summary_
    Wrapper for the ollama Library for chat function
    """
    def __init__(self, base_url="http://localhost:11434", model="llama3.2:latest"):
        """
        Initializes the LLMClient to communicate with an Ollama server.
        
        :param base_url: URL of the Ollama API server.
        :param model: Default model to use.
        """
        self.base_url = base_url
        self.model = model
        self.ollama_client = ollama.Client(host=base_url)

    def chat(self, messages: list):
        """
        Sends a chat message to the LLM and returns the response.
        
        :messages: An array of messages passed to the model.
        :return: LLM-generated response
        """

        return self.ollama_client.chat(model=self.model, messages=messages)
