// ========================================
// CONFIGURACIÓN DE LA APLICACIÓN
// ========================================
// Archivo para que los estudiantes modifiquen

export const APP_CONFIG = {
  // ========== INFORMACIÓN DEL PROYECTO ==========
  // Cambiar por el nombre de su proyecto o grupo
  PROJECT_NAME: "Asistente de Convocatorias MinCiencias",
  
  // Número del grupo (opcional)
  GROUP_NUMBER: "Grupo 2", // Ejemplo: "Grupo 5" o null
  
  // Nombre(s) del/los estudiante(s) (opcional)
  STUDENT_NAMES: "Edna Katherine Conde Vega - Santiago Patiño Hernandez", // Ejemplo: "Seneca Uniandes - Aura Uniandes" o null
  
  // ========== DESCRIPCIÓN ==========
  DESCRIPTION: "Pregúntame sobre convocatorias, requisitos y oportunidades del Ministerio de Ciencia, Tecnología e Innovación",
  
  // ========== CONFIGURACIÓN DEL CHAT ==========
  // Mensaje inicial del bot
  INITIAL_BOT_MESSAGE: "¡Hola! 👋 Soy tu **Asistente de Convocatorias MinCiencias**.\n\nEstoy especializado en ayudarte a encontrar información sobre las **convocatorias del Ministerio de Ciencia, Tecnología e Innovación de Colombia (MinCiencias)**.\n\n**Puedo responder preguntas sobre:**\n\n📢 **Convocatorias**\n- Listar convocatorias existentes\n- Criterios de elegibilidad\n\n📅 **Fechas importantes**\n- Fechas de apertura\n- Fechas de cierre\n\n💵 **Información financiera**\n- Recursos disponibles\n\n**¿Qué convocatoria del MinCiencias te interesa?** 🎯\n",
  
  // Placeholder del input
  INPUT_PLACEHOLDER: "Pregunta sobre convocatorias del MinCiencias...",
  
  // ========== CONFIGURACIÓN DE AGENTES ==========
  // Título del Agente RAG
  AGENT_RAG_TITLE: "Agente RAG - Convocatorias MinCiencias",
  
  // Título del Agente Especializado
  AGENT_SPECIALIZED_TITLE: "Agente Especializado - Convocatorias MinCiencias",
  
  // Placeholder del input para Agente Especializado
  AGENT_SPECIALIZED_INPUT_PLACEHOLDER: "Consulta sobre convocatorias, requisitos o información específica...",
  
  // ========== CONFIGURACIÓN DEL BACKEND ==========
  // URL del backend (Docker container en localhost:8000)
  BACKEND_URL: "http://35.208.246.124:8000",
  
  // Endpoints de la API
  RAG_ENDPOINT: "/ask_rag",
  CUSTOM_ENDPOINT: "/ask_custom",
  
};

// ========================================
// FUNCIONES AUXILIARES
// ========================================
// No modificar estas funciones

/**
 * Genera el título completo de la aplicación
 * Incluye nombre del proyecto, grupo y estudiantes si están definidos
 */
export const getFullTitle = (): string => {
  let title = APP_CONFIG.PROJECT_NAME;
  
  if (APP_CONFIG.GROUP_NUMBER) {
    title += ` - ${APP_CONFIG.GROUP_NUMBER}`;
  }
  
  if (APP_CONFIG.STUDENT_NAMES) {
    title += ` - ${APP_CONFIG.STUDENT_NAMES}`;
  }
  
  return title;
};

/**
 * Genera la URL completa del endpoint RAG
 */
export const getRAGUrl = (): string => {
  return `${APP_CONFIG.BACKEND_URL}${APP_CONFIG.RAG_ENDPOINT}`;
};

/**
 * Genera la URL completa del endpoint Custom/Especializado
 */
export const getCustomUrl = (): string => {
  return `${APP_CONFIG.BACKEND_URL}${APP_CONFIG.CUSTOM_ENDPOINT}`;
};

/**
 * Genera el cuerpo de la petición al backend según FRONTEND_INTEGRATION.md
 * Ambos endpoints esperan el mismo formato: { "question": "..." }
 */
export const createRequestBody = (question: string) => {
  return {
    question,
    collection: "test_collection"
  };
};
