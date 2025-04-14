import os
import openai
from dotenv import load_dotenv, find_dotenv
from app.services.agents.base_agent import BaseAgent
from app.models.chatbot import ChatRequest, ChatResponse
from app.services.agents.factory_agents import FactoryAgents
load_dotenv(find_dotenv())

class ChatbotService:
    def __init__(self):
        load_dotenv()
        self.factory_agents = FactoryAgents()
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    async def get_response(self, request: ChatRequest) -> ChatResponse:  
        agent: BaseAgent | None = self.factory_agents.get_agent('question_evaluator')
        
        if agent == None:
            return ChatResponse(chat_id = request.chat_id, response = "No puedo manejar ese tipo de preguntas")

        response_question_evaluator: str = await agent.handle_request(request.message)
        layer: str = response_question_evaluator # type: ignore -> Siempre va a devolver un str el agent "question_evaluator"

        if response_question_evaluator == "n/a":
            return ChatResponse(chat_id = request.chat_id, response = "No puedo manejar ese tipo de preguntas")
    
        agent = self.factory_agents.get_agent(layer)

        if agent == None:
            return ChatResponse(chat_id = request.chat_id, response = "No puedo manejar ese tipo de preguntas")
        
        response: str = await agent.handle_request(request.message)
        return ChatResponse(chat_id = request.chat_id, response = response)


    def upload_database(self, layer: str) -> str:
        data: str = ""

        if(layer == 'frecuent_questions'):
            file_path = "./app/services/data/frecuent-question-information.txt"
            with open(file_path, "r", encoding="utf-8") as file:
                data = file.read()

        agent: BaseAgent | None = self.factory_agents.get_agent(layer)

        if agent is None:
            return "Agent not found"
                
        return agent.update_database(data)