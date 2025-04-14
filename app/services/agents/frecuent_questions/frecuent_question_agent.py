from typing import Any, Dict, List
from chromadb import Client, QueryResult
from chromadb.config import Settings
from langchain.schema import Document
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from app.services.agents.base_agent import BaseAgent
from app.services.langchain_service import LanchainService 

class FrecuentQuestionAgent(BaseAgent):
    layer: str = 'frecuent_questions'
    collection_name: str = 'frecuent_collection'
    
    def __init__(self):
        self.chroma_client = Client(Settings(chroma_server_host="localhost", chroma_server_http_port="8000"))
        self.collection = self.chroma_client.get_or_create_collection(name=self.collection_name)
        self.langchain_service = LanchainService.get_instance()
        
    async def handle_request(self, input_text: str) -> str: 
        context_ai = self.search_context(input_text)

        content: str = await self.search_response_in_database(input_text, context_ai) # type: ignore
        return content        
    
    async def update_database(self, new_data: str) -> str:

        documents = [Document(page_content=new_data,metadata={"id": "1"})]

        self.collection.add(
            ids=["1"],  
            documents=documents[0].page_content,
            metadatas=documents[0].metadata
        )
    
        return "Vectorial base updated."

    def search_context(self, query: str):
        results = self.collection.query(
            query_texts=[query],
            n_results = 1
        )

        return results
    
    async def search_response_in_database(self, input_text: str, context_ai: QueryResult) -> str:
        if context_ai['documents'] == None or context_ai['documents'] == []:
            return "No se encontraron respuestas"

        list_context = [
            doc + "\n"
            for doc_list in context_ai['documents']
            for doc in doc_list
        ]

        concatenated_docs = "".join(list_context)
        respuesta = await self.langchain_service.chat_with_database(self, input_text, concatenated_docs)        
        return respuesta