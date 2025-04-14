from app.services.agents.base_agent import BaseAgent
from app.services.agents.question_evaluator.question_evaluator_agent import QuestionEvaluatorAgent
from app.services.agents.frecuent_questions.frecuent_question_agent import FrecuentQuestionAgent
from app.services.agents.calendar_questions.calendar_agent import CalendarAgent

class FactoryAgents():
    def __init__(self):        
        self.agents_dict: dict[str, BaseAgent] = {
            'question_evaluator': QuestionEvaluatorAgent(),
            'frecuent_questions': FrecuentQuestionAgent(),
            'calendar_questions': CalendarAgent()
        }

    def get_agent(self, agent_name: str = 'question_evaluator') -> BaseAgent | None:
        agent = self.agents_dict.get(agent_name, None)

        if agent is None:
            raise Exception('Agent not found in factory')

        return agent