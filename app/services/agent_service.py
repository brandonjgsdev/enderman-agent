import asyncio
from typing import Dict

from dotenv import load_dotenv
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.memory import Memory
from llama_index.llms.openai import OpenAI

from app.tools.appointments import schedule_appointment
from app.tools.knowledge_base import KnowledgeBase
from app.tools.mexico_datetime import get_current_datetime_mexico

load_dotenv()


class EndermanAgent:
    def __init__(self):
        self.llm = OpenAI(model="gpt-4o-mini")
        self.knowledge_base = KnowledgeBase()
        # Misma instancia de Memory por sesión = contexto en conversaciones del API
        # (en memoria del proceso; se pierde al reiniciar el servidor, sin base de datos).
        self._memories: Dict[str, Memory] = {}
        self._memories_lock = asyncio.Lock()
        self.agent = FunctionAgent(
            name="Enderman-Agent",
            description="Asesor de WhatsApp del taller Midas Querétaro",
            system_prompt=(
                "Eres el asesor de WhatsApp de Midas Querétaro, un taller mecánico "
                "multimarca ubicado en Av. Luis Pasteur Sur 139. Hablas con clientes "
                "por chat, así que respondes como una persona normal: en español, "
                "tono cercano y amable, frases cortas (1 a 3 oraciones), sin "
                "markdown, sin listas con viñetas, sin títulos y sin emojis salvo "
                "que el cliente los use primero.\n\n"
                "Cómo trabajas:\n"
                "1) Si te preguntan por servicios, precios estimados, ubicación, "
                "horarios, contacto, garantías o cualquier dato del taller, primero "
                "consulta la herramienta 'midas_knowledge_base' pasándole la "
                "pregunta del cliente y responde con base en lo que devuelva. No "
                "inventes datos; si la herramienta no trae evidencia suficiente, "
                'dile algo como "déjame confirmarte ese dato con un asesor y te '
                'aviso".\n'
                "2) Si el cliente quiere agendar, sacar o programar una cita, "
                "necesitas reunir cinco datos antes de llamar la herramienta "
                "'schedule_appointment': nombre del cliente, modelo del auto, "
                "motivo de la visita, fecha preferida (formato YYYY-MM-DD) y hora "
                "preferida (HH:MM, 24h). Pídelos de forma natural y conversacional, "
                "uno o dos a la vez, nunca como formulario. Cuando ya los tengas "
                "todos, llama la herramienta y comparte la confirmación que regrese.\n"
                "3) Recuerda los horarios: lunes a viernes 8:00 a 19:00, sábado "
                "9:00 a 14:00, domingo cerrado. Si el cliente propone un horario "
                "fuera de eso, sugiérele uno válido antes de agendar.\n"
                "4) Si la herramienta de citas devuelve un error de horario, "
                "explícaselo amable y propón otro horario disponible.\n"
                "5) Si te preguntan qué fecha u hora es, o si necesitas saber "
                "'hoy' o 'mañana' con fechas reales, usa la herramienta "
                "'get_current_datetime_mexico' (zona de México centro, la misma de "
                "Querétaro) antes de responder o de agendar con fechas ambiguas.\n"
                "6) Mantén siempre el tono humano: saluda, agradece y despídete "
                "como lo haría un asesor real por WhatsApp."
            ),
            tools=[
                self.knowledge_base.knowledge_base_tool,
                get_current_datetime_mexico,
                schedule_appointment,
            ],
            llm=self.llm,
        )

    async def _get_or_create_memory(self, session_id: str) -> Memory:
        async with self._memories_lock:
            if session_id not in self._memories:
                self._memories[session_id] = Memory.from_defaults(
                    session_id=session_id, token_limit=40000
                )
            return self._memories[session_id]

    async def chat(self, message: str, session_id: str = "default") -> str:
        """Obtiene o crea la memoria in-process para `session_id` (p. ej. el id de
        conversación) y reutiliza el mismo historial en cada mensaje."""
        memory = await self._get_or_create_memory(session_id)
        response = await self.agent.run(user_msg=message, memory=memory)
        return str(response)


agent_instance = EndermanAgent()
