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
        """Inicializar el bot con carga específica del CSV"""
        self.df = pd.DataFrame()
        self.categorias = []
        self.data_source = "ninguno"
        self.load_chengyus_data()
    
    def load_chengyus_data(self):
        """Cargar datos priorizando el archivo específico"""
        logger.info("🔄 Iniciando carga de datos...")
        
        # Prioridad 1: Archivo específico del usuario
        if self.load_specific_csv():
            self.data_source = "CSV específico"
            return
        
        # Prioridad 2: Otros archivos CSV
        if self.load_fallback_csv():
            self.data_source = "CSV alternativo"
            return
        
        # Prioridad 3: Excel backup
        if self.load_from_excel():
            self.data_source = "Excel backup"
            return
        
        # Último recurso: datos embebidos
        logger.warning("⚠️ Usando datos embebidos limitados")
        self.load_embedded_data()
        self.data_source = "embebidos"
    
    def load_specific_csv(self):
        """Cargar específicamente 'tabla chengyus completa.csv'"""
        target_file = "tabla chengyus completa.csv"
        
        try:
            if not os.path.exists(target_file):
                logger.warning(f"❌ No se encontró {target_file}")
                return False
            
            logger.info(f"📂 Cargando archivo específico: {target_file}")
            
            # Probar múltiples encodings para máxima compatibilidad
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    # Intentar cargar con diferentes separadores
                    separators = [',', ';', '\t']
                    
                    for sep in separators:
                        try:
                            df_test = pd.read_csv(target_file, encoding=encoding, sep=sep)
                            
                            # Validar que el archivo tiene datos válidos
                            if df_test.empty:
                                continue
                            
                            if len(df_test) < 10:  # Mínimo 10 filas
                                continue
                            
                            # Verificar columnas esenciales (buscar variaciones)
                            essential_found = False
                            chengyu_cols = ['Chengyu 成语', 'Chengyu', 'chengyu', 'CHENGYU']
                            
                            for col in chengyu_cols:
                                if col in df_test.columns:
                                    essential_found = True
                                    break
                            
                            if not essential_found:
                                continue
                            
                            # Archivo válido encontrado
                            self.df = df_test
                            self.process_loaded_data()
                            logger.info(f"✅ Archivo específico cargado exitosamente: {len(self.df)} chengyus con encoding {encoding} y separador '{sep}'")
                            return True
                            
                        except Exception as e:
                            continue
                    
                except Exception as e:
                    continue
            
            logger.error(f"❌ No se pudo cargar {target_file} con ningún encoding/separador")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error general cargando {target_file}: {e}")
            return False
    
    def load_fallback_csv(self):
        """Cargar otros archivos CSV como fallback"""
        fallback_files = [
            'chengyus_data.csv',
            'tabla-chengyus-completa.csv',
            'chengyus.csv',
            'data.csv'
        ]
        
        for csv_file in fallback_files:
            if os.path.exists(csv_file):
                try:
                    logger.info(f"📂 Intentando archivo fallback: {csv_file}")
                    
                    encodings = ['utf-8', 'utf-8-sig', 'latin-1']
                    for encoding in encodings:
                        try:
                            df_test = pd.read_csv(csv_file, encoding=encoding)
                            if not df_test.empty and len(df_test) >= 10:
                                self.df = df_test
                                self.process_loaded_data()
                                logger.info(f"✅ Fallback CSV cargado: {len(self.df)} chengyus")
                                return True
                        except:
                            continue
                except:
                    continue
        
        return False
    
    def load_from_excel(self):
        """Cargar desde Excel como último backup"""
        try:
            excel_files = ['tabla-chengyus-completa.xlsx', 'chengyus.xlsx']
            
            for excel_file in excel_files:
                if os.path.exists(excel_file):
                    try:
                        df_test = pd.read_excel(excel_file, engine='openpyxl')
                        if not df_test.empty and len(df_test) >= 10:
                            self.df = df_test
                            self.process_loaded_data()
                            logger.info(f"✅ Excel backup cargado: {len(self.df)} chengyus")
                            return True
                    except:
                        continue
            return False
        except:
            return False
    
    def process_loaded_data(self):
        """Procesar datos cargados con detección automática de columnas"""
        try:
            # Limpiar datos
            self.df = self.df.dropna(how='all')
            
            # Normalizar nombres de columnas - buscar variaciones comunes
            column_mapping = {
                # Variaciones de Chengyu
                'chengyu': 'Chengyu 成语',
                'CHENGYU': 'Chengyu 成语',
                'Chengyu': 'Chengyu 成语',
                
                # Variaciones de Pinyin
                'pinyin': 'Pinyin',
                'PINYIN': 'Pinyin',
                
                # Variaciones de Equivalente
                'equivalente': 'Equivalente en Venezolano',
                'refran': 'Equivalente en Venezolano',
                'refrán': 'Equivalente en Venezolano',
                'venezolano': 'Equivalente en Venezolano',
                
                # Variaciones de Categoría
                'categoria': 'Categoria',
                'categoría': 'Categoria',
                'category': 'Categoria',
                'tema': 'Categoria'
            }
            
            # Aplicar mapeo de columnas
            for old_name, new_name in column_mapping.items():
                if old_name in self.df.columns and new_name not in self.df.columns:
                    self.df.rename(columns={old_name: new_name}, inplace=True)
            
            logger.info(f"📋 Columnas después del mapeo: {list(self.df.columns)}")
            logger.info(f"📊 Total de filas procesadas: {len(self.df)}")
            
            # Extraer categorías
            categoria_cols = ['Categoria', 'Category', 'Categoría', 'Tema']
            for col in categoria_cols:
                if col in self.df.columns:
                    self.categorias = self.df[col].dropna().unique().tolist()
                    logger.info(f"📚 Categorías encontradas: {len(self.categorias)}")
                    break
            
            if not self.categorias:
                self.categorias = ['General']
            
        except Exception as e:
            logger.error(f"Error procesando datos: {e}")
    
    def format_chengyu(self, row):
        """Formatear chengyu con detección automática de columnas"""
        try:
            # Buscar información en diferentes columnas posibles
            chengyu = self.get_column_value(row, ['Chengyu 成语', 'Chengyu', 'chengyu'])
            pinyin = self.get_column_value(row, ['Pinyin', 'pinyin'])
            literal = self.get_column_value(row, ['Traduccion Literal', 'Literal', 'traduccion'])
            significado = self.get_column_value(row, ['Significado Figurativo', 'Significado', 'significado'])
            venezolano = self.get_column_value(row, ['Equivalente en Venezolano', 'Equivalente', 'Refran', 'venezolano'])
            categoria = self.get_column_value(row, ['Categoria', 'Category', 'categoria'])
            nivel = self.get_column_value(row, ['Nivel de Dificultad', 'Nivel', 'HSK', 'nivel'])
            ejemplo = self.get_column_value(row, ['Frase de Ejemplo', 'Ejemplo', 'ejemplo', 'frase'])
            
            # Formato base
            formatted_text = f"""
🎋 *{chengyu}* ({pinyin})

📜 *Traducción literal:* {literal}
💡 *Significado:* {significado}

🇻🇪 *Equivalente venezolano:*
"_{venezolano}_"
"""
            
            # Agregar ejemplo si existe
            if ejemplo and ejemplo != 'N/A' and ejemplo.strip():
                formatted_text += f"""
📝 *Ejemplo en chino:*
{ejemplo}
"""
            
            # Agregar metadatos
            formatted_text += f"""
📌 *Categoría:* {categoria}
🏮 *Nivel HSK:* {nivel}
            """
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formateando chengyu: {e}")
            return "❌ Error al mostrar el chengyu."
    
    def get_column_value(self, row, possible_columns):
        """Obtener valor de la primera columna disponible"""
        for col in possible_columns:
            if col in row and pd.notna(row.get(col)):
                return str(row.get(col))
        return 'N/A'
    
    def load_embedded_data(self):
        """Datos embebidos como último recurso"""
        embedded_data = [
            {
                'Chengyu 成语': '莫名其妙',
                'Pinyin': 'mo ming qi miao',
                'Traduccion Literal': 'sin nombre su misterio',
                'Significado Figurativo': 'algo inexplicable sin razón aparente',
                'Equivalente en Venezolano': '¡Esto no tiene nombre!',
                'Categoria': 'Confusión y Misterio',
                'Nivel de Dificultad': 'HSK6',
                'Frase de Ejemplo': '他的行为莫名其妙，让大家都很困惑。'
            },
            {
                'Chengyu 成语': '一举两得',
                'Pinyin': 'yi ju liang de',
                'Traduccion Literal': 'una acción dos ganancias',
                'Significado Figurativo': 'lograr dos objetivos con una sola acción',
                'Equivalente en Venezolano': 'Matar dos pájaros de un solo tiro',
                'Categoria': 'Eficiencia y Logro',
                'Nivel de Dificultad': 'HSK6',
                'Frase de Ejemplo': '学习中文既能提高语言能力，又能了解文化，真是一举两得。'
            }
        ]
        
        self.df = pd.DataFrame(embedded_data)
        self.process_loaded_data()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start con información de estado"""
        total_chengyus = len(self.df) if not self.df.empty else 0
        
        welcome_msg = f"""
🇨🇳 *Bot de Chengyus Chino-Venezolanos* 🇻🇪

¡Aprende expresiones idiomáticas chinas con sus equivalentes en refranes venezolanos!

📊 *Disponibles:* {total_chengyus} chengyus
📂 *Fuente:* {self.data_source}

*Comandos disponibles:*
/chengyu - Obtén un chengyu aleatorio
/dia [1-{total_chengyus}] - Chengyu específico por día
/categorias - Explora por categorías
/quiz - Test interactivo de práctica
/hsk [HSK6/HSK7/HSK8/HSK9] - Filtra por nivel
/ayuda - Muestra esta ayuda

¡Empieza tu aprendizaje cultural ahora! 🎓
        """
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    
    # [Resto de métodos del bot sin cambios: random_chengyu, daily_chengyu, etc.]

def main():
    """Función principal"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN no encontrado en variables de entorno")
        return
    
    try:
        application = Application.builder().token(token).build()
        bot = ChengyuBot()
        
        # Agregar handlers
        application.add_handler(CommandHandler('start', bot.start))
        # [Agregar resto de handlers...]
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Error al iniciar bot: {e}")

if __name__ == '__main__':
    main()
