import os
import logging
import pandas as pd
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configurar logging detallado
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ChengyuBot:
    def __init__(self):
        """Inicializar el bot con manejo robusto de archivos"""
        self.df = pd.DataFrame()
        self.categorias = []
        self.load_chengyus_data()
    
    def debug_file_system(self):
        """Función de debug para verificar el sistema de archivos"""
        try:
            current_dir = os.getcwd()
            files_available = os.listdir('.')
            excel_exists = os.path.exists('tabla-chengyus-completa.xlsx')
            
            logger.info(f"📂 Directorio actual: {current_dir}")
            logger.info(f"📁 Archivos disponibles: {files_available}")
            logger.info(f"🔍 Existe Excel: {excel_exists}")
            
            if excel_exists:
                file_size = os.path.getsize('tabla-chengyus-completa.xlsx')
                logger.info(f"📊 Tamaño del archivo Excel: {file_size} bytes")
            
            # Verificar si existe versión CSV
            csv_exists = os.path.exists('chengyus_data.csv')
            logger.info(f"🔍 Existe CSV alternativo: {csv_exists}")
            
        except Exception as e:
            logger.error(f"Error en debug del sistema de archivos: {e}")
    
    def load_chengyus_data(self):
        """Cargar datos de chengyus con múltiples estrategias de fallback"""
        # Debug del sistema de archivos
        self.debug_file_system()
        
        # Estrategia 1: Intentar cargar Excel principal
        if self.try_load_excel():
            return
        
        # Estrategia 2: Intentar cargar CSV alternativo
        if self.try_load_csv():
            return
        
        # Estrategia 3: Usar datos embebidos como último recurso
        self.load_embedded_data()
    
    def try_load_excel(self):
        """Intentar cargar archivo Excel con diferentes métodos"""
        try:
            if not os.path.exists('tabla-chengyus-completa.xlsx'):
                logger.warning("❌ Archivo Excel no encontrado")
                return False
            
            # Intentar con diferentes engines y hojas
            engines = ['openpyxl', 'xlrd']
            sheet_names = [0, 'tabla_chengyus_completa_con_ref', 'Sheet1']
            
            for engine in engines:
                for sheet in sheet_names:
                    try:
                        self.df = pd.read_excel('tabla-chengyus-completa.xlsx', 
                                              engine=engine, sheet_name=sheet)
                        if not self.df.empty:
                            logger.info(f"✅ Excel cargado con engine {engine}, hoja {sheet}: {len(self.df)} filas")
                            self.process_loaded_data()
                            return True
                    except Exception as sheet_error:
                        logger.warning(f"Error con engine {engine}, hoja {sheet}: {sheet_error}")
                        continue
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error general al cargar Excel: {e}")
            return False
    
    def try_load_csv(self):
        """Intentar cargar archivo CSV alternativo"""
        try:
            if os.path.exists('chengyus_data.csv'):
                self.df = pd.read_csv('chengyus_data.csv', encoding='utf-8')
                logger.info(f"✅ CSV cargado: {len(self.df)} filas")
                self.process_loaded_data()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error al cargar CSV: {e}")
            return False
    
    def load_embedded_data(self):
        """Cargar datos embebidos como último recurso"""
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
            },
            {
                'Dia del año': 4,
                'Chengyu 成语': '入乡随俗',
                'Pinyin': 'ru xiang sui su',
                'Traduccion Literal': 'entrar al pueblo seguir costumbres',
                'Significado Figurativo': 'adaptarse a las costumbres locales',
                'Equivalente en Venezolano': 'Donde fueres, haz lo que vieres',
                'Categoria': 'Adaptación Cultural',
                'Nivel de Dificultad': 'HSK7'
            },
            {
                'Dia del año': 5,
                'Chengyu 成语': '班门弄斧',
                'Pinyin': 'ban men nong fu',
                'Traduccion Literal': 'mostrar hacha ante Lu Ban',
                'Significado Figurativo': 'mostrar habilidad ante un experto',
                'Equivalente en Venezolano': 'Cachicamo diciéndole a morrocoy conchudo',
                'Categoria': 'Humildad y Presunción',
                'Nivel de Dificultad': 'HSK8'
            }
        ]
        
        self.df = pd.DataFrame(embedded_data)
        self.process_loaded_data()
        logger.info(f"✅ Datos embebidos cargados: {len(self.df)} chengyus")
    
    def process_loaded_data(self):
        """Procesar datos cargados y extraer categorías"""
        try:
            # Verificar columnas necesarias
            required_columns = ['Chengyu 成语', 'Pinyin', 'Traduccion Literal', 
                              'Significado Figurativo', 'Equivalente en Venezolano', 
                              'Categoria', 'Nivel de Dificultad']
            
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            if missing_columns:
                logger.warning(f"⚠️ Columnas faltantes: {missing_columns}")
            
            # Extraer categorías únicas
            if 'Categoria' in self.df.columns:
                self.categorias = self.df['Categoria'].dropna().unique().tolist()
                logger.info(f"📚 Categorías encontradas: {len(self.categorias)}")
            else:
                self.categorias = []
                logger.warning("⚠️ No se encontró columna 'Categoria'")
            
            # Mostrar información de columnas disponibles
            logger.info(f"📋 Columnas disponibles: {list(self.df.columns)}")
            
        except Exception as e:
            logger.error(f"Error al procesar datos: {e}")
    
    def format_chengyu(self, row):
        """Formatear mensaje de chengyu con manejo robusto de errores"""
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
            return "❌ Error al mostrar el chengyu. Datos no disponibles."

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start con información de diagnóstico"""
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
        """Comando /debug para información del sistema"""
        debug_info = f"""
🔧 *Información de Debug:*

📊 *Datos cargados:*
• Chengyus: {len(self.df)}
• Categorías: {len(self.categorias)}
• Columnas: {len(self.df.columns) if not self.df.empty else 0}

📁 *Sistema de archivos:*
• Excel existe: {os.path.exists('tabla-chengyus-completa.xlsx')}
• CSV existe: {os.path.exists('chengyus_data.csv')}
• Directorio: {os.getcwd()}

📋 *Columnas disponibles:*
{list(self.df.columns) if not self.df.empty else 'Sin columnas'}
        """
        await update.message.reply_text(debug_info, parse_mode='Markdown')

    async def random_chengyu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /chengyu con mejor manejo de errores"""
        if self.df.empty:
            await update.message.reply_text("❌ No hay chengyus disponibles. Usa /debug para más información.")
            return
            
        try:
            chengyu = self.df.sample(1).iloc[0]
            await update.message.reply_text(self.format_chengyu(chengyu), parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error en random_chengyu: {e}")
            await update.message.reply_text(f"❌ Error al obtener chengyu aleatorio: {str(e)}")

    async def daily_chengyu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /dia con validación mejorada"""
        if self.df.empty:
            await update.message.reply_text("❌ No hay chengyus disponibles. Usa /debug para más información.")
            return
            
        try:
            if not context.args:
                await update.message.reply_text(f"❌ Uso correcto: /dia [número entre 1-{len(self.df)}]")
                return
                
            day = int(context.args[0])
            if 1 <= day <= len(self.df):
                chengyu = self.df.iloc[day-1]
                await update.message.reply_text(self.format_chengyu(chengyu), parse_mode='Markdown')
            else:
                await update.message.reply_text(f"⚠️ El día debe estar entre 1 y {len(self.df)}")
        except (ValueError, IndexError) as e:
            await update.message.reply_text(f"❌ Uso correcto: /dia [número entre 1-{len(self.df)}]")
        except Exception as e:
            logger.error(f"Error en daily_chengyu: {e}")
            await update.message.reply_text(f"❌ Error al obtener chengyu del día: {str(e)}")

    async def show_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /categorias con validación"""
        if not self.categorias:
            await update.message.reply_text("❌ No hay categorías disponibles. Usa /debug para más información.")
            return
            
        try:
            keyboard = []
            for i, cat in enumerate(self.categorias[:20]):  # Limitar a 20 categorías
                keyboard.append([InlineKeyboardButton(cat, callback_data=f"cat_{i}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"📚 *Categorías disponibles ({len(self.categorias)}):*\nElije una categoría:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error en show_categories: {e}")
            await update.message.reply_text(f"❌ Error al mostrar categorías: {str(e)}")

    async def category_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejador de selección de categoría mejorado"""
        query = update.callback_query
        await query.answer()
        
        try:
            category_index = int(query.data.split('_')[1])
            if category_index < len(self.categorias):
                category = self.categorias[category_index]
                filtered = self.df[self.df['Categoria'] == category]
                
                if not filtered.empty:
                    chengyu = filtered.sample(1).iloc[0]
                    await query.edit_message_text(
                        f"📖 *Categoría: {category}*\n{self.format_chengyu(chengyu)}",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(f"❌ No hay chengyus en la categoría '{category}'")
            else:
                await query.edit_message_text("❌ Categoría no válida")
        except Exception as e:
            logger.error(f"Error en category_handler: {e}")
            await query.edit_message_text(f"❌ Error al procesar categoría: {str(e)}")

    async def hsk_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /hsk con mejor validación"""
        if self.df.empty:
            await update.message.reply_text("❌ No hay chengyus disponibles. Usa /debug para más información.")
            return
            
        try:
            if not context.args:
                await update.message.reply_text("ℹ️ Niveles disponibles: HSK6, HSK7, HSK8, HSK9")
                return
                
            level = context.args[0].upper()
            valid_levels = ['HSK6', 'HSK7', 'HSK8', 'HSK9']
            
            if level in valid_levels:
                filtered = self.df[self.df['Nivel de Dificultad'] == level]
                if not filtered.empty:
                    chengyu = filtered.sample(1).iloc[0]
                    await update.message.reply_text(
                        f"🎓 *Nivel {level}*\n{self.format_chengyu(chengyu)}",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(f"❌ No hay chengyus de nivel {level}")
            else:
                await update.message.reply_text("❌ Niveles válidos: HSK6, HSK7, HSK8, HSK9")
        except Exception as e:
            logger.error(f"Error en hsk_filter: {e}")
            await update.message.reply_text(f"❌ Error al filtrar por nivel HSK: {str(e)}")

    async def quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /quiz con validación robusta"""
        if self.df.empty:
            await update.message.reply_text("❌ No hay chengyus disponibles para el quiz. Usa /debug para más información.")
            return
            
        if len(self.df) < 4:
            await update.message.reply_text("❌ Se necesitan al menos 4 chengyus para el quiz.")
            return
            
        try:
            # Seleccionar chengyu correcto
            correct = self.df.sample(1).iloc[0]
            
            # Seleccionar 3 opciones incorrectas
            wrong_options = self.df[self.df.index != correct.name].sample(3)
            
            # Crear opciones
            all_options = [correct] + wrong_options.to_dict('records')
            random.shuffle(all_options)
            
            # Encontrar índice de la respuesta correcta
            correct_index = None
            for i, opt in enumerate(all_options):
                if opt.get('Chengyu 成语') == correct.get('Chengyu 成语'):
                    correct_index = i
                    break
            
            # Crear teclado
            keyboard = []
            for i, opt in enumerate(all_options):
                venezolano = str(opt.get('Equivalente en Venezolano', 'N/A'))
                display_text = venezolano[:45] + "..." if len(venezolano) > 45 else venezolano
                keyboard.append([InlineKeyboardButton(
                    display_text,
                    callback_data=f"ans_{i}_{correct_index}_{correct.name}"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            chengyu = str(correct.get('Chengyu 成语', 'N/A'))
            pinyin = str(correct.get('Pinyin', 'N/A'))
            
            await update.message.reply_text(
                f"❓ *Quiz:* ¿Cuál es el equivalente venezolano de:\n\n*{chengyu}* ({pinyin})?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error en quiz: {e}")
            await update.message.reply_text(f"❌ Error al crear quiz: {str(e)}")

    async def answer_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejador de respuestas del quiz mejorado"""
        query = update.callback_query
        await query.answer()
        
        try:
            parts = query.data.split('_')
            selected_idx = int(parts[1])
            correct_idx = int(parts[2])
            correct_row_idx = int(parts[3])
            
            correct_row = self.df.loc[correct_row_idx]
            
            if selected_idx == correct_idx:
                msg = "✅ ¡Correcto! "
            else:
                msg = "❌ Incorrecto. "
                
            msg += f"La respuesta correcta es:\n{self.format_chengyu(correct_row)}"
            await query.edit_message_text(msg, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error en answer_handler: {e}")
            await query.edit_message_text(f"❌ Error al procesar respuesta: {str(e)}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /ayuda actualizado"""
        help_text = f"""
🇨🇳 *Ayuda - Bot de Chengyus* 🇻🇪

📊 *Estado actual:*
• Chengyus: {len(self.df)}
• Categorías: {len(self.categorias)}

*Comandos disponibles:*
/start - Mensaje de bienvenida
/chengyu - Chengyu aleatorio
/dia [1-{len(self.df) if not self.df.empty else 50}] - Chengyu específico
/categorias - Explorar por categorías
/hsk [HSK6/HSK7/HSK8/HSK9] - Filtrar por nivel
/quiz - Quiz interactivo
/debug - Información del sistema
/ayuda - Esta ayuda

*Ejemplos de uso:*
`/dia 15` - Muestra el chengyu del día 15
`/hsk HSK7` - Muestra chengyus de nivel HSK7

¡Aprende expresiones chinas con sabiduría venezolana!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Función principal con manejo robusto de errores"""
    # Verificar token
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("❌ BOT_TOKEN no encontrado en variables de entorno")
        print("❌ ERROR: BOT_TOKEN no configurado")
        return
    
    logger.info("🚀 Iniciando bot de chengyus...")
    
    # Crear aplicación
    try:
        application = Application.builder().token(token).build()
        bot = ChengyuBot()
        
        # Agregar handlers
        application.add_handler(CommandHandler('start', bot.start))
        application.add_handler(CommandHandler('chengyu', bot.random_chengyu))
        application.add_handler(CommandHandler('dia', bot.daily_chengyu))
        application.add_handler(CommandHandler('categorias', bot.show_categories))
        application.add_handler(CommandHandler('hsk', bot.hsk_filter))
        application.add_handler(CommandHandler('quiz', bot.quiz))
        application.add_handler(CommandHandler('debug', bot.debug_command))
        application.add_handler(CommandHandler('ayuda', bot.help_command))
        
        # Handlers para botones
        application.add_handler(CallbackQueryHandler(bot.category_handler, pattern=r"^cat_"))
        application.add_handler(CallbackQueryHandler(bot.answer_handler, pattern=r"^ans_"))
        
        logger.info("✅ Bot configurado exitosamente")
        print("✅ Bot iniciado. Presiona Ctrl+C para detener.")
        
        # Ejecutar bot
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Error al iniciar bot: {e}")
        print(f"❌ ERROR al iniciar bot: {e}")

if __name__ == '__main__':
    main()

