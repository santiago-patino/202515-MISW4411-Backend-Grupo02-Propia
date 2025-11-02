/**
 * @fileoverview FileUploader Component
 * 
 * Componente para la carga de documentos desde URL al sistema RAG.
 * Permite configurar parámetros de procesamiento, chunking y embeddings.
 * El sistema descarga automáticamente todos los documentos disponibles en la URL.
 * 
 * @author Universidad de los Andes
 * @version 1.0.0
 */

import { useState, useEffect, useRef } from "react";
import { useNotifications } from '../contexts/NotificationContext';

// Tipos de estrategias de chunking
type ChunkingStrategy = "recursive_character" | "fixed_size" | "semantic" | "document_structure" | "linguistic_units";

/**
 * Componente para cargar documentos desde URL
 * 
 * Funcionalidades principales:
 * - Configuración de parámetros de chunking (tamaño, overlap)
 * - Selección de estrategia de chunking
 * - Selección de modelo de embeddings
 * - Configuración de opciones de procesamiento
 * - Validación de entrada y notificaciones en tiempo real
 * - Polling automático para verificar estado del procesamiento
 * 
 * @param baseUrl - URL base del backend (por defecto: http://localhost:8000)
 * @returns JSX.Element
 */
export default function URLUploader({ baseUrl = "http://localhost:8000" }: URLUploaderProps) {
  const { addNotification, updateNotification } = useNotifications();
  
  // Referencias para mantener valores actualizados en el polling
  const updateNotificationRef = useRef(updateNotification);
  const addNotificationRef = useRef(addNotification);
  const collectionNameRef = useRef("");
  
  const [input, setInput] = useState("");
  const [collectionName, setCollectionName] = useState("test_collection");
  
  // Estados de chunking
  const [chunkingStrategy, setChunkingStrategy] = useState<ChunkingStrategy>("recursive_character");
  const [chunkSize, setChunkSize] = useState(1000);
  const [chunkOverlap, setChunkOverlap] = useState(200);
  const [separators, setSeparators] = useState<string[]>([". ", ", ", "\n\n", "\n", " ", ""]);
  const [lengthFunction, setLengthFunction] = useState<"character_count" | "token_count">("character_count");
  
  // Estados de procesamiento
  const [maxFileSizeMb, setMaxFileSizeMb] = useState(50);
  const [timeoutPerFile, setTimeoutPerFile] = useState(300);
  
  // Estados de embeddings
  const [embeddingModel, setEmbeddingModel] = useState("embedding-001");
  const [batchSize, setBatchSize] = useState(90);
  const [retryAttempts, setRetryAttempts] = useState(3);

  // Estados de secciones colapsables
  const [showChunkingAdvanced, setShowChunkingAdvanced] = useState(false);
  const [showEmbeddingAdvanced, setShowEmbeddingAdvanced] = useState(false);
  const [showProcessingOptions, setShowProcessingOptions] = useState(false);

  // Estados locales removidos - ahora usamos solo notificaciones globales
  const [processingId, setProcessingId] = useState<string | null>(null);
  
  // Actualizar referencias cuando cambien los valores
  useEffect(() => {
    updateNotificationRef.current = updateNotification;
    addNotificationRef.current = addNotification;
    collectionNameRef.current = collectionName;
  }, [updateNotification, addNotification, collectionName]);

  // Ref para mantener el polling estable
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Determinar si la estrategia usa chunk_size
  const strategyUsesChunkSize = (strategy: ChunkingStrategy): boolean => {
    return !["semantic", "document_structure"].includes(strategy);
  };

  // Obtener descripción de la estrategia
  const getStrategyDescription = (strategy: ChunkingStrategy): string => {
    const descriptions: Record<ChunkingStrategy, string> = {
      "recursive_character": "Divide documentos respetando párrafos, oraciones y palabras",
      "fixed_size": "Divide documentos en chunks de tamaño fijo",
      "semantic": "Divide documentos según cambios de significado (más lento, mejor calidad)",
      "document_structure": "Divide según headers y estructura del documento",
      "linguistic_units": "Divide según unidades lingüísticas (oraciones, párrafos)"
    };
    return descriptions[strategy];
  };

  const validateConfig = (): string | null => {
    if (!/^[a-zA-Z0-9_-]+$/.test(collectionName)) return "collection_name solo puede contener letras, números, guiones y guiones bajos";
    
    // Validar chunk_size y chunk_overlap solo si la estrategia los usa
    if (strategyUsesChunkSize(chunkingStrategy)) {
      if (chunkSize < 100 || chunkSize > 5000) return "chunk_size debe estar entre 100 y 5000";
      if (chunkOverlap < 0 || chunkOverlap >= chunkSize) return "chunk_overlap debe ser >= 0 y menor que chunk_size";
    }
    
    if (maxFileSizeMb < 1 || maxFileSizeMb > 1000) return "max_file_size_mb debe estar entre 1 y 1000";
    if (timeoutPerFile < 30 || timeoutPerFile > 3600) return "timeout_per_file_seconds debe estar entre 30 y 3600";
    if (batchSize < 1 || batchSize > 1000) return "batch_size debe estar entre 1 y 1000";
    if (retryAttempts < 1 || retryAttempts > 10) return "retry_attempts debe estar entre 1 y 10";
    if (!embeddingModel.trim()) return "Debe especificar un modelo de embeddings";
    if (!input || !/^https?:\/\//.test(input)) return "Debes ingresar una URL válida que empiece con http o https";
    return null;
  };

  const handleSubmit = async () => {
    const configError = validateConfig();
    if (configError) {
      addNotification({
        type: 'error',
        title: 'Error de Validación',
        message: configError,
        autoClose: false
      });
      return;
    }

    // Construir chunking_config dinámicamente según la estrategia
    const chunking_config: any = {
      chunking_strategy: chunkingStrategy,
    };

    // Solo incluir chunk_size y chunk_overlap si la estrategia los usa
    if (strategyUsesChunkSize(chunkingStrategy)) {
      chunking_config.chunk_size = chunkSize;
      chunking_config.chunk_overlap = chunkOverlap;
    }

    // Agregar campos opcionales según la estrategia
    if (chunkingStrategy === "recursive_character") {
      chunking_config.separators = separators;
      chunking_config.keep_separator = true;
      chunking_config.strip_whitespace = true;
    }
    
    if (chunkingStrategy === "fixed_size") {
      chunking_config.length_function = lengthFunction;
    }

    const body = {
      source_url: input,
      collection_name: collectionName,
      chunking_config,
      processing_options: {
        file_extensions: ["pdf", "txt", "docx", "md", "csv", "xlsx"],
        max_file_size_mb: maxFileSizeMb,
        extract_metadata: true,
        preserve_formatting: false,
        timeout_per_file_seconds: timeoutPerFile,
      },
      embedding_config: {
        model: embeddingModel,
        batch_size: batchSize,
        retry_attempts: retryAttempts,
      },
    };

    try {
      const res = await fetch(`${baseUrl}/api/v1/documents/load-from-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || data.message || "Error al procesar");
      }

      const notificationId = addNotification({
        type: 'processing',
        title: 'Procesamiento Iniciado',
        message: `Cargando documentos desde URL: ${input}`,
        processingId: data.processing_id,
        autoClose: false
      });

      setProcessingId(data.processing_id);
      localStorage.setItem(`processing_id_${data.processing_id}`, data.processing_id);
      localStorage.setItem(`notification_id_${data.processing_id}`, notificationId);
      setInput("");
    } catch (err: any) {
      addNotification({
        type: 'error',
        title: 'Error al Iniciar Procesamiento',
        message: err.message,
        autoClose: false
      });
    }
  };

  // Polling para consultar estado del procesamiento
  useEffect(() => {
    // Limpiar polling anterior si existe
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    
    if (!processingId) {
      return;
    }
    
    const executePolling = async () => {
      try {
        const res = await fetch(`${baseUrl}/api/v1/documents/load-from-url/${processingId}`);
        const data = await res.json();
        const notificationId = localStorage.getItem(`notification_id_${processingId}`);
        
        if (data.success === false) {
          if (notificationId) {
            updateNotificationRef.current(notificationId, {
              type: 'error',
              title: 'Error en Procesamiento',
              message: data.error || data.message || 'Error desconocido en el procesamiento',
              autoClose: false
            });
          }
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          setProcessingId(null);
          return true;
          
        } else if (data.success === true) {
          if (notificationId) {
            updateNotificationRef.current(notificationId, {
              type: 'success',
              title: 'Procesamiento Completado',
              message: `Documentos cargados exitosamente en la colección "${collectionNameRef.current}"`,
              autoClose: true,
              duration: 10000
            });
          }
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          setProcessingId(null);
          return true;
          
        } else {
          return false;
        }
      } catch (err: any) {
        addNotificationRef.current({
          type: 'warning',
          title: 'Error de Red',
          message: `No se pudo verificar el estado del procesamiento: ${err.message}`,
          processingId: processingId,
          autoClose: false
        });
        return false;
      }
    };

    executePolling().then((shouldStop) => {
      if (shouldStop) {
        return;
      }
      
      pollingIntervalRef.current = setInterval(executePolling, 5000);
    });
    
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [processingId]);

  return (
    <div className="mx-auto w-full max-w-3xl rounded-lg border bg-white p-6 shadow-md space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-center">Configurar carga de documentos</h2>
        <p className="text-sm text-gray-600 text-center mt-2">Las notificaciones de progreso aparecerán en el panel de notificaciones 🔔</p>
      </div>

      {/* SECCIÓN 1: Configuración de Documentos */}
      <div className="border rounded-lg p-4 bg-gray-50">
        <h3 className="text-md font-semibold mb-3 text-gray-800">Configuración de Documentos</h3>
        
        <label className="block text-sm font-medium mb-3">
          URL del documento
          <input
            type="url"
            placeholder="https://..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="mt-1 w-full rounded border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
          />
        </label>

        <label className="block text-sm font-medium">
          Nombre colección
          <input
            value={collectionName}
            onChange={(e) => setCollectionName(e.target.value)}
            className="mt-1 w-full rounded border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
          />
        </label>
      </div>

      {/* SECCIÓN 2: Estrategia de Chunking */}
      <div className="border rounded-lg p-4 bg-gray-50">
        <h3 className="text-md font-semibold mb-3 text-gray-800">Estrategia de Chunking</h3>
        
        <label className="block text-sm font-medium mb-3">
          Estrategia
          <select
            value={chunkingStrategy}
            onChange={(e) => setChunkingStrategy(e.target.value as ChunkingStrategy)}
            className="mt-1 w-full rounded border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
          >
            <option value="recursive_character">Recursive Character</option>
            <option value="fixed_size">Fixed Size</option>
            <option value="semantic">Semantic</option>
            <option value="document_structure">Document Structure</option>
            <option value="linguistic_units">Linguistic Units</option>
          </select>
          <p className="text-xs text-gray-600 mt-1 italic">{getStrategyDescription(chunkingStrategy)}</p>
        </label>

        {/* Campos dinámicos según estrategia */}
        {strategyUsesChunkSize(chunkingStrategy) ? (
          <div className="grid grid-cols-2 gap-4 mb-3">
            <label className="text-sm font-medium">
              Chunk size
              <input
                type="number"
                min={100}
                max={5000}
                value={chunkSize}
                onChange={(e) => setChunkSize(Number(e.target.value))}
                className="mt-1 w-full rounded border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
              />
            </label>
            <label className="text-sm font-medium">
              Chunk overlap
              <input
                type="number"
                min={0}
                max={chunkSize - 1}
                value={chunkOverlap}
                onChange={(e) => setChunkOverlap(Number(e.target.value))}
                className="mt-1 w-full rounded border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
              />
            </label>
          </div>
        ) : (
          <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-3">
            <p className="text-sm text-blue-800">
              {chunkingStrategy === "semantic" 
                ? "ℹ️ Esta estrategia usa embeddings semánticos, no requiere tamaños fijos"
                : "ℹ️ Esta estrategia usa la estructura del documento (headers, secciones)"}
            </p>
          </div>
        )}

        {/* Subsección Avanzada */}
        <div className="mt-3">
          <button
            onClick={() => setShowChunkingAdvanced(!showChunkingAdvanced)}
            className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            {showChunkingAdvanced ? "▼" : "▶"} Opciones avanzadas
          </button>
          
          {showChunkingAdvanced && (
            <div className="mt-3 pl-4 border-l-2 border-blue-300 space-y-3">
              {chunkingStrategy === "recursive_character" && (
                <label className="block text-sm font-medium">
                  Separadores (uno por línea)
                  <textarea
                    value={separators.join("\n")}
                    onChange={(e) => setSeparators(e.target.value.split("\n"))}
                    className="mt-1 w-full rounded border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                    rows={4}
                    placeholder="Ingrese un separador por línea"
                  />
                  <p className="text-xs text-gray-500 mt-1">Por defecto: párrafo doble, párrafo simple, espacio</p>
                </label>
              )}
              
              {chunkingStrategy === "fixed_size" && (
                <label className="block text-sm font-medium">
                  Función de longitud
                  <select
                    value={lengthFunction}
                    onChange={(e) => setLengthFunction(e.target.value as "character_count" | "token_count")}
                    className="mt-1 w-full rounded border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="character_count">Contar caracteres</option>
                    <option value="token_count">Contar tokens</option>
                  </select>
                </label>
              )}
            </div>
          )}
        </div>
      </div>

      {/* SECCIÓN 3: Configuración de Embeddings */}
      <div className="border rounded-lg p-4 bg-gray-50">
        <h3 className="text-md font-semibold mb-3 text-gray-800">Configuración de Embeddings</h3>
        
        <label className="block text-sm font-medium mb-3">
          Modelo de embeddings
          <select
            value={embeddingModel}
            onChange={(e) => setEmbeddingModel(e.target.value)}
            className="mt-1 w-full rounded border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
          >
            <option value="embedding-001">embedding-001</option>
            <option value="embedding-002">embedding-002</option>
          </select>
        </label>

        {/* Subsección Avanzada */}
        <div>
          <button
            onClick={() => setShowEmbeddingAdvanced(!showEmbeddingAdvanced)}
            className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            {showEmbeddingAdvanced ? "▼" : "▶"} Opciones avanzadas
          </button>
          
          {showEmbeddingAdvanced && (
            <div className="mt-3 pl-4 border-l-2 border-blue-300">
              <div className="grid grid-cols-2 gap-4">
                <label className="text-sm font-medium">
                  Batch size
                  <input
                    type="number"
                    min={1}
                    max={1000}
                    value={batchSize}
                    onChange={(e) => setBatchSize(Number(e.target.value))}
                    className="mt-1 w-full rounded border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </label>
                <label className="text-sm font-medium">
                  Retry attempts
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={retryAttempts}
                    onChange={(e) => setRetryAttempts(Number(e.target.value))}
                    className="mt-1 w-full rounded border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </label>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* SECCIÓN 4: Opciones de Procesamiento */}
      <div className="border rounded-lg p-4 bg-gray-50">
        <button
          onClick={() => setShowProcessingOptions(!showProcessingOptions)}
          className="w-full flex items-center justify-between text-md font-semibold text-gray-800"
        >
          <span>Opciones de Procesamiento</span>
          <span className="text-blue-600">{showProcessingOptions ? "▼" : "▶"}</span>
        </button>
        
        {showProcessingOptions && (
          <div className="mt-3 grid grid-cols-2 gap-4">
            <label className="text-sm font-medium">
              Max file size (MB)
              <input
                type="number"
                min={1}
                max={1000}
                value={maxFileSizeMb}
                onChange={(e) => setMaxFileSizeMb(Number(e.target.value))}
                className="mt-1 w-full rounded border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
              />
            </label>
            <label className="text-sm font-medium">
              Timeout por archivo (s)
              <input
                type="number"
                min={30}
                max={3600}
                value={timeoutPerFile}
                onChange={(e) => setTimeoutPerFile(Number(e.target.value))}
                className="mt-1 w-full rounded border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
              />
            </label>
          </div>
        )}
      </div>

      {/* Botón de envío */}
      <button
        onClick={handleSubmit}
        className="w-full rounded px-4 py-3 text-white font-medium hover:bg-blue-700 transition-colors"
        style={{
          backgroundColor: '#2baae2'
        }}
        onMouseEnter={(e) => {
          const target = e.target as HTMLButtonElement;
          target.style.backgroundColor = '#1e90c7';
        }}
        onMouseLeave={(e) => {
          const target = e.target as HTMLButtonElement;
          target.style.backgroundColor = '#2baae2';
        }}
      >
        Cargar Documentos
      </button>
    </div>
  );
}

// Tipos
export type URLUploaderProps = {
  baseUrl?: string;
};
