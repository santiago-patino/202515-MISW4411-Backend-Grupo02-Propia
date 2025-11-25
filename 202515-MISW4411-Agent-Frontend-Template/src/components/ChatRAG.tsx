/**
 * @fileoverview ChatRAG Component
 * 
 * Componente de chat para el Agente RAG.
 * Se conecta al endpoint /ask_rag del backend según FRONTEND_INTEGRATION.md
 * 
 * @author Universidad de los Andes
 * @version 1.0.0
 */

import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github.css";

// Configuración de la aplicación
import { APP_CONFIG, getFullTitle, getRAGUrl, createRequestBody } from "../config/appConfig";

// Tipos para la API del Chat
import type { AskResponse } from "../types/rag";

import { useChatHistory, type ChatMessage } from "../hooks/useChatHistory";

/**
 * Componente de chat para el Agente RAG
 * 
 * Funcionalidades principales:
 * - Interfaz de chat conversacional con IA
 * - Renderizado de respuestas en Markdown con syntax highlighting
 * - Historial de conversación persistente
 * - Indicadores de carga y estado
 * - Scroll automático a nuevos mensajes
 * - Integración con endpoint /ask_rag
 * 
 * @returns JSX.Element
 */
export default function ChatRAG() {
  const { messages, addMessage, clearHistory } = useChatHistory({
    chatId: 'rag',
    initialMessage: {
      role: "bot",
      text: APP_CONFIG.INITIAL_BOT_MESSAGE,
    }
  });

  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const messagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesRef.current?.scrollTo({ top: messagesRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function onSend(e: React.FormEvent) {
    e.preventDefault();
    const q = msg.trim();
    if (!q) return;
  
    addMessage({ role: "user", text: q });
    setMsg("");
    setLoading(true);
  
    try {
      const url = getRAGUrl();
      
      console.log("🔗 [RAG] Enviando petición a:", url);
      
      const requestBody = createRequestBody(q);
      
      console.log("[RAG] Datos enviados:", requestBody);
      
      const res = await fetch(url, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json",
        },  
        body: JSON.stringify(requestBody),
      });
  
      console.log("📡 [RAG] Status de respuesta:", res.status, res.statusText);
  
      if (!res.ok) {
        const errorText = await res.text();
        console.error("[RAG] Error del backend:", errorText);
        
        // Manejar errores según el código de estado HTTP
        let errorMessage = "";
        
        switch (res.status) {
          case 404:
            errorMessage = "No se pudo encontrar el endpoint del Agente RAG.\n\n**Verifica que:**\n- El backend esté ejecutándose\n- El endpoint `/ask_rag` esté implementado\n- El contenedor Docker esté corriendo correctamente\n";
            break;
          case 500:
            errorMessage = "Error interno en el servidor del Agente RAG.\n\nEl backend encontró un error al procesar tu solicitud. Revisa los logs del backend para más detalles.";
            break;
          case 503:
            errorMessage = "El servicio del Agente RAG no está disponible temporalmente.\n\nEl backend puede estar sobrecargado o reiniciándose. Intenta nuevamente en unos momentos.";
            break;
          case 400:
            try {
              const errorData = JSON.parse(errorText);
              errorMessage = `Solicitud inválida: ${errorData.detail || "Error de validación"}`;
            } catch {
              errorMessage = "Solicitud inválida. Verifica el formato de tu pregunta.";
            }
            break;
          default:
            try {
              const errorData = JSON.parse(errorText);
              errorMessage = `Error ${res.status}: ${errorData.detail || errorText}`;
            } catch {
              errorMessage = `Error ${res.status}: ${res.statusText || "Error desconocido"}`;
            }
        }
        
        throw new Error(errorMessage);
      }
  
      const data: AskResponse = await res.json();
      console.log("[RAG] Respuesta exitosa:", data);
  
      addMessage({ role: "bot", text: data.answer || "(Sin respuesta)" });
      
    } catch (err) {
      console.error("[RAG] Error completo:", err);
      const errorMessage = err instanceof Error ? err.message : String(err);
      
      // Manejo de errores de red y específicos
      let userFriendlyMessage = errorMessage;
      
      if (errorMessage.includes("Failed to fetch") || errorMessage.includes("ERR_CONNECTION_REFUSED") || errorMessage.includes("ERR_NETWORK")) {
        userFriendlyMessage = "**No se pudo conectar con el backend**\n\n**Posibles causas:**\n- El backend no está ejecutándose\n- El contenedor Docker no está corriendo\n- El puerto 8000 no está disponible\n\n**Soluciones:**\n1. Verifica que el backend esté corriendo: `docker-compose ps`\n2. Inicia el backend: `docker-compose up -d`\n3. Revisa los logs: `docker-compose logs -f app`";
      } else if (errorMessage.includes("NetworkError") || errorMessage.includes("net::ERR")) {
        userFriendlyMessage = "Error de red. Verifica tu conexión a Internet y que el backend esté accesible en http://localhost:8000";
      }
      
      addMessage({
        role: "bot",
        text: userFriendlyMessage,
      });
    } finally {
      setLoading(false);
    }
  }

  return (
      <div className="pt-10 lg:pt-10 pb-8">
        {/* Título principal de la aplicación */}
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-3" style={{ color: '#306238' }}>
            {APP_CONFIG.PROJECT_NAME}
          </h1>
          
          {/* Información del grupo y participantes */}
          {(APP_CONFIG.GROUP_NUMBER || APP_CONFIG.STUDENT_NAMES) && (
            <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-4 mb-4 text-sm md:text-base" style={{ color: 'var(--text-secondary)' }}>
              {APP_CONFIG.GROUP_NUMBER && (
                <span className="px-3 py-1 rounded-full bg-gray-100 font-medium">
                  {APP_CONFIG.GROUP_NUMBER}
                </span>
              )}
              {APP_CONFIG.STUDENT_NAMES && (
                <span className="text-gray-600">
                  {APP_CONFIG.STUDENT_NAMES}
                </span>
              )}
            </div>
          )}
          
          <p className="text-lg md:text-xl" style={{ color: 'var(--text-secondary)' }}>
            {APP_CONFIG.DESCRIPTION}
          </p>
        </div>

        {/* Chat Container */}
        <div className="container mx-auto px-4 flex justify-center">
          <div className="w-full max-w-6xl bg-white border border-gray-200 rounded-xl overflow-hidden shadow-lg">
            

            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
              <h2 className="text-lg font-semibold text-gray-800">{APP_CONFIG.AGENT_RAG_TITLE}</h2>
              <button
                onClick={clearHistory}
                className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors duration-200"
                title="Limpiar conversación (mantiene mensaje inicial)"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Limpiar Conversación
              </button>
            </div>

            {/* Mensajes */}
            <div 
              ref={messagesRef}
              className="h-[550px] overflow-y-auto p-6 space-y-4 bg-gray-50"
            >
              {messages.map((m, i) => (
                <MessageBubble key={i} role={m.role} text={m.text} />
              ))}

              {loading && <MessageBubble role="bot" text="Recuperando información desde el RAG..." />}
            </div>

            {/* Input */}
            <form onSubmit={onSend} className="border-t border-gray-200 p-6 bg-white">
              <div className="flex gap-4">
                <input
                  value={msg}
                  onChange={(e) => setMsg(e.target.value)}
                  placeholder={APP_CONFIG.INPUT_PLACEHOLDER}
                  autoComplete="off"
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    color: 'var(--text-primary)'
                  }}
                />
                <button 
                  type="submit" 
                  disabled={loading || !msg.trim()}
                  className="px-8 py-3 text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 text-lg"
                  style={{
                    backgroundColor: '#306238'
                  }}
                  onMouseEnter={(e) => {
                    const target = e.target as HTMLButtonElement;
                    target.style.backgroundColor = '#2a5630';
                  }}
                  onMouseLeave={(e) => {
                    const target = e.target as HTMLButtonElement;
                    target.style.backgroundColor = '#306238';
                  }}
                >
                  {loading ? "Enviando…" : "Enviar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
  );
}



function MessageBubble({ role, text }: { role: ChatMessage['role']; text: string }) {
  const isUser = role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {/* Avatar */}
      {!isUser && (
        <div 
          className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-sm flex-shrink-0"
          style={{ backgroundColor: '#306238' }}
        >
          🤖
        </div>
      )}

      {/* Burbuja */}
      <div className={`max-w-md lg:max-w-2xl px-4 py-3 rounded-lg ${
        isUser 
          ? "text-white" 
          : "bg-white border border-gray-200 text-gray-800"
      }`}
      style={isUser ? { backgroundColor: '#306238' } : {}}
      >
        {isUser ? (
          <span className="text-sm">{text}</span>
        ) : (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={{
                a: (props) => <a {...props} target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-700" />,
                p: (props) => <p {...props} className="mb-2 last:mb-0" />,
                ul: (props) => <ul {...props} className="mb-2 last:mb-0 pl-6 list-disc" style={{ listStyleType: 'disc' }} />,
                ol: (props) => <ol {...props} className="mb-2 last:mb-0 pl-6 list-decimal" style={{ listStyleType: 'decimal' }} />,
                li: (props) => <li {...props} className="mb-1 list-item" style={{ display: 'list-item' }} />,
                strong: (props) => <strong {...props} className="font-semibold" />,
                em: (props) => <em {...props} className="italic" />,
                code: (props) => {
                  const { className, children, ...rest } = props;
                  const isInline = !className;
                  return isInline ? (
                    <code 
                      {...rest}
                      className="bg-gray-100 text-gray-800 px-1 py-0.5 rounded text-xs font-mono"
                    >
                      {children}
                    </code>
                  ) : (
                    <code {...rest} className={className}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {text}
            </ReactMarkdown>
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center text-gray-600 font-semibold text-sm flex-shrink-0">
          👤
        </div>
      )}
    </div>
  );
}

