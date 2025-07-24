// =================================================================
// ==      CLASIFICADOR DE INTENCIONES CON GEMINI                 ==
// =================================================================
// Este módulo utiliza Gemini para analizar el mensaje del usuario y
// decidir la mejor acción a tomar (usar RAG, una herramienta, etc.).
// =================================================================
import 'dotenv/config';
import { GoogleGenerativeAI } from '@google/generative-ai';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

export const classifyAndExtract = async (userMessage) => {
    const prompt = `
    Analiza el siguiente mensaje de un usuario que habla con una psicóloga experta en duelo animal.
    Tu tarea es clasificar la intención y decidir la acción más apropiada.
    Las acciones posibles son:
    1.  'use_rag': Si el usuario está expresando sentimientos, haciendo una pregunta general sobre el duelo, o iniciando una conversación. Esta es la opción por defecto.
    2.  'use_tool': Si el usuario pide explícitamente información sobre precios, servicios, o quiere agendar una cita.
    3.  'clarify': Si el mensaje es ambiguo o no se entiende.

    Si decides 'use_tool', también debes identificar el nombre de la herramienta y sus argumentos.
    Herramientas disponibles:
    -   'get_service_info': Proporciona detalles sobre los servicios. No necesita argumentos.
    -   'schedule_appointment': Inicia el proceso para agendar una cita. Argumentos: { "service_type": "inicial | seguimiento | paquete" }

    Finalmente, crea un resumen claro del mensaje del usuario para usarlo en la búsqueda RAG.

    Mensaje del usuario: "${userMessage}"

    Responde únicamente con un objeto JSON con la siguiente estructura:
    {
      "decision": "use_rag" | "use_tool" | "clarify",
      "tool_call": { "name": "nombre_de_la_herramienta", "arguments": { "arg1": "valor1" } } | null,
      "summary_for_rag": "Resumen del mensaje del usuario."
    }
    `;

    try {
        const result = await model.generateContent(prompt);
        const responseText = result.response.text();
        
        const jsonMatch = responseText.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
            return JSON.parse(jsonMatch[0]);
        }
        // Si Gemini no devuelve un JSON, usamos RAG como opción segura
        return { decision: 'use_rag', tool_call: null, summary_for_rag: userMessage };
    } catch (error) {
        console.error("Error en la clasificación con Gemini:", error);
        // En caso de error, siempre intentamos una respuesta conversacional
        return { decision: 'use_rag', tool_call: null, summary_for_rag: userMessage };
    }
};
