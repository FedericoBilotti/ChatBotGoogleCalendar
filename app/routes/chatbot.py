from fastapi import APIRouter, HTTPException
from app.models.chatbot import ChatRequest, ChatResponse
from app.services.chatbot_service import ChatbotService

router = APIRouter()
chatbot_service = ChatbotService()

@router.post("/chat")
async def chat(request: ChatRequest):
    response = await chatbot_service.get_response(request)
    return response