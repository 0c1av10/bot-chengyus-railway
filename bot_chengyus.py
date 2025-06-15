import os
import logging
import pandas as pd
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ChengyuBot:
    def __init__(self):
        """Inicializar el bot con carga optimizada de CSV"""
        self.df = pd.DataFrame()
        self.categorias = []
        self.load_chengyus_data()
    
    def load_chengyus_data(self):
        """Cargar datos desde CSV con fallback a datos embebidos"""
        logger.info("🔄 Iniciando carga de datos...")
        
        # Estrategia 1: Cargar desde CSV (método principal)
        if self.load_from_csv():
            return
        
        # Estrategia 2: Intentar Excel como backup
        if self.load_from_excel_backup():
            return
        
        # Estrategia 3: Usar datos embebidos
        self.load_embedded_data()
    
    def load_from_csv(self):
        """Cargar datos desde archivo CSV"""
        try:
            csv_files = ['chengyus_data.csv', 'tabla-chengyus-completa.csv']
            
            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    logger.info(f"📂 Intentando cargar {csv_file}")
                    
                    # Intentar diferentes encodings
                    encodings = ['utf-8', 'utf-8-sig', 'latin-1']
                    
                    for encoding in encodings:
                        try:
                            self.df = pd.read_csv(csv_file, encoding=encoding)
                            
                            if not self.df.empty:
                                logger.info(f"✅ CSV cargado exitosamente: {len(self.df)} filas con encoding {encoding}")
                                self.process_loaded_data()
                                return True
                                
                        except UnicodeDecodeError:
                            logger.warning(f"⚠️ Error de encoding {encoding} para {csv_file}")
                            continue
                        except Exception as e:
                            logger.error(f"❌ Error al cargar {csv_file} con {encoding}: {e}")
                            continue
            
            logger.warning("❌ No se pudo cargar ningún archivo CSV")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error general al cargar CSV: {e}")
            return False
    
    def load_from_excel_backup(self):
        """Cargar desde Excel como backup"""
        try:
            if os.path.exists('tabla-chengyus-completa.xlsx'):
                logger.info("📂 Intentando Excel como backup...")
                self.df = pd.read_excel('tabla-chengyus-completa.xlsx', engine='openpyxl')
                
                if not self.df.empty:
                    logger.info(f"✅ Excel backup cargado: {len(self.df)} filas")
                    self.process_loaded_data()
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Error al cargar Excel backup: {e}")
            return False
    
    def process_loaded_data(self):
        """Procesar datos cargados"""
        try:
            # Limpiar datos
            self.df = self.df.dropna(how='all')  # Eliminar filas completamente vacías
            
            # Mostrar información de columnas
            logger.info(f"📋 Columnas encontradas: {list(self.df.columns)}")
            
            # Extraer categorías
            if 'Categoria' in self.df.columns:
                self.categorias = self.df['Categoria'].dropna().unique().tolist()
                logger.info(f"📚 Categorías encontradas: {len(self.categorias)}")
            else:
                logger.warning("⚠️ Columna 'Categoria' no encontrada")
                self.categorias = []
            
            # Verificar columnas esenciales
            required_cols = ['Chengyu 成语', 'Pinyin', 'Equivalente en Venezolano']
            missing_cols = [col for col in required_cols if col not in self.df.columns]
            
            if missing_cols:
                logger.warning(f"⚠️ Columnas faltantes: {missing_cols}")
            
        except Exception as e:
            logger.error(f"Error al procesar datos: {e}")
    
    def load_embedded_data(self):
        """Datos embebidos como último recurso"""
        logger.warning("🔄 Usando datos embebidos como fallback")
        
        embedded_data = [
            {
                'Dia del año': 1,
                'Chengyu 成语': '莫名其妙',
                'Pinyin': 'mo ming qi miao',
                'Traduccion Literal': 'sin nombre su misterio',
                'Significado Figurativo': 'algo inexplicable sin razón aparente',
                'Equivalente en Venezolano': '¡Esto no tiene nombre!',
                'Categoria': 'Confusión y Misterio',
                'Nivel de Dificultad': 'HSK6'
            },
            {
                'Dia del año': 2,
                'Chengyu 成语': '一举两得',
                'Pinyin': 'yi ju liang de',
                'Traduccion Literal': 'una acción dos ganancias',
                'Significado Figurativo': 'lograr dos objetivos con una sola acción',
                'Equivalente en Venezolano': 'Matar dos pájaros de un solo tiro',
                'Categoria': 'Eficiencia y Logro',
                'Nivel de Dificultad': 'HSK6'
            },
            {
                'Dia del año': 3,
                'Chengyu 成语': '火上加油',
                'Pinyin': 'huo shang jia you',
                'Traduccion Literal': 'añadir aceite al fuego',
                'Significado Figurativo': 'empeorar una situación',
                'Equivalente en Venezolano': 'Echar leña al fuego',
                'Categoria': 'Conflictos y Problemas',
                'Nivel de Dificultad': 'HSK7'
            }
        ]
        
        self.df = pd.DataFrame(embedded_data)
        self.process_loaded_data()
        logger.info(f"✅ Datos embebidos cargados: {len(self.df)} chengyus")
    
    def format_chengyu(self, row):
        """Formatear chengyu para mostrar"""
        try:
            chengyu = str(row.get('Chengyu 成语', 'N/A'))
            pinyin = str(row.get('Pinyin', 'N/A'))
            literal = str(row.get('Traduccion Literal', 'N/A'))
            significado = str(row.get('Significado Figurativo', 'N/A'))
            venezolano = str(row.get('Equivalente en Venezolano', 'N/A'))
            categoria = str(row.get('Categoria', 'N/A'))
            nivel = str(row.get('Nivel de Dificultad', 'N/A'))
            
            return f"""
🎋 *{chengyu}* ({pinyin})

📜 *Traducción literal:* {literal}
💡 *Significado:* {significado}

🇻🇪 *Equivalente venezolano:*
"_{venezolano}_"

📌 *Categoría:* {categoria}
🏮 *Nivel HSK:* {nivel}
            """
        except Exception as e:
            logger.error(f"Error al formatear chengyu: {e}")
            return "❌ Error al mostrar el chengyu."

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        data_status = f"✅ {len(self.df)} chengyus" if not self.df.empty else "❌ Sin datos"
        cat_status = f"✅ {len(self.categorias)} categorías" if self.categorias else "❌ Sin categorías"
        
        welcome_msg = f"""
🇨🇳 *Bot de Chengyus Chino-Venezolanos* 🇻🇪

¡Aprende expresiones idiomáticas chinas con sus equivalentes en refranes venezolanos!

📊 *Estado de datos:*
• Chengyus: {data_status}
• Categorías: {cat_status}

*Comandos disponibles:*
/chengyu - Obtén un chengyu aleatorio
/dia [1-50] - Chengyu específico por día
/categorias - Explora por categorías
/quiz - Test interactivo
/hsk [nivel] - Filtra por nivel HSK
/debug - Información de sistema
/ayuda - Muestra esta ayuda

¡Empieza tu aprendizaje cultural ahora!
        """
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')

    async def debug_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /debug"""
        debug_info = f"""
🔧 *Información de Debug:*

📊 *Datos cargados:*
• Chengyus: {len(self.df)}
• Categorías: {len(self.categorias)}
• Columnas: {len(self.df.columns) if not self.df.empty else 0}

📁 *Sistema de archivos:*
• CSV existe: {os.path.exists('chengyus_data.csv')}
• Excel existe: {os.path.exists('tabla-chengyus-completa.xlsx')}
• Directorio: {os.getcwd()}

📋 *Columnas disponibles:*
{list(self.df.columns) if not self.df.empty else 'Sin columnas'}
        """
        await update.message.reply_text(debug_info, parse_mode='Markdown')

    # Resto de métodos del bot (random_chengyu, daily_chengyu, etc.)
    # [Incluye aquí todos los demás métodos que ya tenías funcionando]

def main():
    """Función principal"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("❌ BOT_TOKEN no encontrado")
        return
    
    logger.info("🚀 Iniciando bot de chengyus...")
    
    try:
        application = Application.builder().token(token).build()
        bot = ChengyuBot()
        
        # Agregar handlers
        application.add_handler(CommandHandler('start', bot.start))
        application.add_handler(CommandHandler('debug', bot.debug_command))
        # [Agregar todos los demás handlers]
        
        logger.info("✅ Bot configurado exitosamente")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Error al iniciar bot: {e}")

if __name__ == '__main__':
    main()

