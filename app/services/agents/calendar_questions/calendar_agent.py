from app.services.agents.base_agent import BaseAgent
from app.services.langchain_service import LanchainService 

class CalendarAgent(BaseAgent):
    layer: str = 'calendar_questions'
    collection: str = 'calendar-collection'
    temperature = 0.2

    def __init__(self):
        self.langchain_service = LanchainService.get_instance()

    async def handle_request(self, user_input: str) -> str:
        response = await self.langchain_service.chat_with_functions(self, user_input, "")    
        return response