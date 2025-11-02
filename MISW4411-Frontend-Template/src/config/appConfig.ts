// ========================================
// CONFIGURACIÓN DE LA APLICACIÓN
// ========================================
// Archivo para que los estudiantes modifiquen

export const APP_CONFIG = {
  // ========== INFORMACIÓN DEL PROYECTO ==========
  // Cambiar por el nombre de su proyecto o grupo
  PROJECT_NAME: "Asistente Inteligente MISW4411",
  
  // Número del grupo (opcional)
  GROUP_NUMBER: null, // Ejemplo: "Grupo 5" o null
  
  // Nombre(s) del/los estudiante(s) (opcional)
  STUDENT_NAMES: null, // Ejemplo: "Seneca Uniandes - Aura Uniandes" o null
  
  // ========== DESCRIPCIÓN ==========
  DESCRIPTION: "Pregúntame sobre el curso o temas relacionados con Grandes Modelos de Lenguaje",
  
  // ========== CONFIGURACIÓN DEL CHAT ==========
  // Mensaje inicial del bot
  INITIAL_BOT_MESSAGE: "Hola 👋 Soy el **Asistente Inteligente MISW4411**. Pregúntame sobre el curso o temas relacionados con **Grandes Modelos de Lenguaje**.\n\n",
  
  // Placeholder del input
  INPUT_PLACEHOLDER: "Escribe tu pregunta sobre el curso MISW4411...",
  
  // ========== CONFIGURACIÓN DEL BACKEND ==========
  // URL del backend - usa automáticamente el mismo host actual con puerto 8000
  BACKEND_URL: (() => {
    if (typeof window === 'undefined') return "http://127.0.0.1:8000";
    // Usar el mismo host/protocolo actual pero con puerto 8000
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:8000`;
  })(),
  
  // Endpoint de la API
  API_ENDPOINT: "/api/v1/ask",
  
  // Parámetros por defecto para el RAG
  DEFAULT_TOP_K: 5,
  DEFAULT_COLLECTION: "test_collection",
  
  // ========== OPCIONES AVANZADAS DE RAG SEMANA 3 ==========
  // Activar/desactivar reranking de documentos recuperados
  USE_RERANKING: false,
  
  // Activar/desactivar reescritura de consultas con LLM
  USE_QUERY_REWRITING: false,
  
  // Forzar reconstrucción del índice en cada consulta
  FORCE_REBUILD: false,
  
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
 * Obtiene la URL base del backend (sin endpoints)
 */
export const getBaseUrl = (): string => {
  return APP_CONFIG.BACKEND_URL;
};

/**
 * Genera la URL completa del backend
 */
export const getBackendUrl = (): string => {
  return `${APP_CONFIG.BACKEND_URL}${APP_CONFIG.API_ENDPOINT}`;
};

/**
 * Genera el cuerpo de la petición al backend
 * Los estudiantes pueden modificar qué parámetros se envían al API editando APP_CONFIG
 */
export const createRequestBody = (question: string) => {
  return {
    question,
    top_k: APP_CONFIG.DEFAULT_TOP_K,
    collection: APP_CONFIG.DEFAULT_COLLECTION,
    force_rebuild: APP_CONFIG.FORCE_REBUILD,
    use_reranking: APP_CONFIG.USE_RERANKING,
    use_query_rewriting: APP_CONFIG.USE_QUERY_REWRITING,
  };
};
