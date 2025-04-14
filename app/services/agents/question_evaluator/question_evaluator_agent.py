from app.services.agents.base_agent import BaseAgent
from app.services.langchain_service import LanchainService
from app.services.agents.base_agent import BaseAgent

class QuestionEvaluatorAgent(BaseAgent):    
    layer = 'question_evaluator'
    
    def __init__(self):
        self.langchain_service = LanchainService.get_instance()

    async def handle_request(self, user_input: str) -> str:
        respuesta = await self.langchain_service.chat_with_database(self, user_input, "")
        return respuesta