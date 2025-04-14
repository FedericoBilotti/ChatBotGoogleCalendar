from datetime import datetime
from typing import List
import json

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langchain_core.messages.tool import ToolCall
from langchain.schema import AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.services.i_singleton import ISingleton
from app.services.agents.base_agent import BaseAgent
from app.services.google_calendar_service import GoogleCalendarServiceController

class LanchainService(ISingleton):
    __instance = None

    def __init__(self):    
        if LanchainService.__instance is not None:
            raise Exception("Singleton was instanciated!")
        
        self._google_calendar = GoogleCalendarServiceController.get_instance()

    @staticmethod
    def get_instance():
        if LanchainService.__instance == None:            
            LanchainService.__instance = LanchainService()

        return LanchainService.__instance

    async def chat_with_functions(self, agent: BaseAgent, input_message: str, context_ai: str = "") -> str:
        system_content = await self.get_instruction(agent)
        
        if context_ai:
            system_content += "\n\nContexto:\n" + context_ai

        prompt1 = ChatPromptTemplate([("system", "{system}"), ("human", "{input}"),])
        
        llm = init_chat_model(agent.model, model_provider="openai", temperature=agent.temperature)
        tools = [self.add_event, self.get_events, self.delete_events]
        llm_with_tools = llm.bind_tools(tools)
        
        function_to_call = await (prompt1 | llm_with_tools).ainvoke({
            "system": system_content,
            "input":  input_message
        })

        functions: List[ToolCall] = []

        if isinstance(function_to_call, AIMessage):
            functions = function_to_call.tool_calls
        
        if len(functions) == 0:
            return function_to_call.content # type: ignore
        
        tool_results = self.call_function(functions)

        prompt2 = ChatPromptTemplate.from_messages([
                    ("system",    "{system}"),
                    ("assistant","{tool_results}"),
                    ("user",     "{input}")
               ])

        final: BaseMessage = await (prompt2 | llm).ainvoke({
            "system":       system_content,
            "tool_results": tool_results,
            "input":        input_message
        })

        return final.content # type: ignore

    def call_function(self, calls) -> str:
        tool_outputs = []
        for call in calls:
            name = call["name"]
            args = call["args"]

            if isinstance(args, str):
                args = json.loads(args)

            args.pop("self", None)

            if args is None:
                return "Error: No se encontraron argumentos"

            if name == "add_event":
                dic = { "description": args["description"], "start_datetime": args["start_datetime"], "end_datetime": args["end_datetime"] }
                res = self._google_calendar.add_event(dic)
            elif name == "get_events":
                target_date = args["target_date"]
                max_date = args["max_date"]
                max_events = args["max_events"]
                res = self._google_calendar.get_events(max_events, target_date, max_date)
            elif name == "delete_events":
                end_date = datetime.fromisoformat(args["end_date"])
                target_date = datetime.fromisoformat(args["target_date"])
                res = self._google_calendar.delete_events(target_date, end_date)
            else:
                res = f"Función desconocida: {name}"

            if isinstance(res, (list, dict)):
                res = json.dumps(res, ensure_ascii=False)
            tool_outputs.append(f"{name} → {res}")

        return "\n".join(tool_outputs)
    
    @tool
    def add_event(self, description: str, start_datetime: str, end_datetime: str) -> str:
        """Add an event to the Google Calendar. Requires description, start_datetime (ISO format), and end_datetime (ISO format)."""
        if not all(["description", "start_datetime", "end_datetime"]):
            return "Error: Faltan parámetros obligatorios (descripción, start_datetime, end_datetime)"
    
        return self._google_calendar.add_event({"description": description, "start_datetime": start_datetime, "end_datetime": end_datetime})
    
    @tool
    def delete_events(self, target_date: datetime, end_date: datetime) -> str:
        """Delete events from the Google Calendar. Requires target_date (ISO format), and end_date (ISO format)."""
        return self._google_calendar.delete_events(target_date, end_date)
    
    @tool
    def get_events(self, max_events: int, target_date: datetime, max_date: datetime) -> str:
        """Get events from the Google Calendar. Requires target_date (ISO format), and end_date (ISO format)."""
        return self._google_calendar.get_events(max_events, target_date, max_date)

    async def chat_with_database(self, agent: BaseAgent, input_message: str, context_ai: str = "") -> str:
        try:
            model = ChatOpenAI(
                    model=agent.model,
                    temperature=agent.temperature
                )

            prompt = ChatPromptTemplate([
                ("system", '{system}'),
                ("human", '{input}'),
            ])

            chain = prompt | model

            input_system: str = await self.get_instruction(agent)
            
            if(context_ai == ""):
                response = chain.invoke({
                    'system':  input_system,
                    'input': input_message
                })
            else:
                response = chain.invoke({
                    'system':  input_system.replace("{Context}", context_ai),
                    'input': input_message
                })
    
            return response.content # type: ignore
        
        except Exception as e:
            raise Exception(f"Error en LanchainService: {str(e)}")
        
    async def get_instruction(self, agent: BaseAgent) -> str:
        """Read the contents of the file that the agent needs, and return it as a string"""
        # If i have a database, i would ask to the database
        path: str = f"./app/services/agents/{agent.layer}/instruction.txt"
        with open(path, encoding="utf-8") as file:
            instruction = file.read()

        return instruction