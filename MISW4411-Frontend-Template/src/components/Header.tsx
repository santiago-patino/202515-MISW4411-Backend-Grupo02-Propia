/**
 * @fileoverview Header Component
 * 
 * Cabecera principal de la aplicación con navegación entre pestañas.
 * Incluye el título de la aplicación, botones de navegación y el centro de notificaciones.
 * Utiliza animaciones de Framer Motion para transiciones suaves.
 * 
 * @author Universidad de los Andes
 * @version 1.0.0
 */

import { motion } from 'framer-motion';
import NotificationCenter from './NotificationCenter';

type HeaderProps = {
  tab: 'chat' | 'uploader';
  setTab: (tab: 'chat' | 'uploader') => void;
};

/**
 * Cabecera de la aplicación
 * 
 * Funcionalidades principales:
 * - Navegación entre pestañas (Chat y Cargar Documentos)
 * - Título dinámico de la aplicación
 * - Centro de notificaciones integrado
 * - Diseño responsivo y fijo en la parte superior
 * - Animaciones de entrada y transiciones suaves
 * - Estilo consistente con la identidad visual del proyecto
 * 
 * @param tab - Pestaña actualmente activa
 * @param setTab - Función para cambiar la pestaña activa
 * @returns JSX.Element
 */
const Header = ({ tab, setTab }: HeaderProps) => {
  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
      style={{
        backgroundColor: '#2baae2',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      <div className="container-custom">
        <div className="flex items-center justify-between h-20 lg:h-24">
          {/* Logo Izquierdo */}
          <div className="flex items-center gap-4">
            <img 
              src="/assets/MisoLogo.png" 
              alt="MISO Logo" 
              className="h-12 md:h-14 lg:h-16 object-contain"
            />

            {/* Botones de tabs */}
            <nav className="flex gap-2">
              <button
                onClick={() => setTab('chat')}
                className={`px-3 py-1.5 rounded text-sm font-medium ${
                  tab === 'chat'
                    ? 'bg-white text-[#2baae2]'
                    : 'bg-[#1f8cbf] text-white hover:bg-[#18739d]'
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setTab('uploader')}
                className={`px-3 py-1.5 rounded text-sm font-medium ${
                  tab === 'uploader'
                    ? 'bg-white text-[#2baae2]'
                    : 'bg-[#1f8cbf] text-white hover:bg-[#18739d]'
                }`}
              >
                Cargar Documentos
              </button>
            </nav>
          </div>

          {/* Logo Derecho y Notificaciones */}
          <div className="flex items-center gap-4">
            <NotificationCenter />
            <img 
              src="/assets/UniandesDISCLogo.png" 
              alt="Universidad de los Andes Facultad Logo" 
              className="h-12 md:h-14 lg:h-16 object-contain"
            />
          </div>
        </div>
      </div>
    </motion.header>
  );
};

export default Header;
