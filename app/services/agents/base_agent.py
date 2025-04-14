from abc import ABC, abstractmethod
from typing import Any

class BaseAgent(ABC):
    layer: str = 'none'
    model: str = 'gpt-3.5-turbo'
    collection_name: str = ''
    temperature: float = 0.5

    @abstractmethod
    async def handle_request(self, user_input: str) -> str: 
        """Maneja la solicitud del usuario con contexto opcional"""

    def __str__(self) -> str:
        return f"BaseAgent(layer={self.layer}, model={self.model})"
    
    def update_database(self, new_data: str) -> str:
        """ 
            Uploads the given products to the vectorial base.
            Args: new_data (List[str]): A list of strings containing the product data.
            Returns: str: A message indicating that the vectorial base has been updated. 
        """
        return ""
    
    def search_context(self, query: str) -> str:        
        """ 
            Search in the vectorial base using embeddings         
            Args: query (str): The query to search in the vectorial base
            Returns: str: The results of the search
        """
        return ""