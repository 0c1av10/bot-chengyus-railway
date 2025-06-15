import os
import logging
import pandas as pd
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configurar logging solo para desarrollo (no visible para usuarios)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ChengyuBot:
    def __init__(self):
        """Inicializar el bot con carga optimizada de datos"""
        self.df = pd.DataFrame()
        self.categorias = []
        self.data_loaded = False
        self.load_chengyus_data()
    
    def load_chengyus_data(self):
        """Cargar datos con múltiples estrategias de fallback"""
        # Intentar cargar CSV primero
        if self.load_from_csv():
            self.data_loaded = True
            return
        
        # Fallback a Excel si existe
        if self.load_from_excel():
            self.data_loaded = True
            return
        
        # Último recurso: datos embebidos
        self.load_embedded_data()
        self.data_loaded = True
    
    def load_from_csv(self):
        """Cargar desde archivo CSV"""
        try:
            csv_files = ['chengyus_data.csv', 'tabla-chengyus-completa.csv']
            
            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    encodings = ['utf-8', 'utf-8-sig', 'latin-1']
                    
                    for encoding in encodings:
                        try:
                            self.df = pd.read_csv(csv_file, encoding=encoding)
                            if not self.df.empty and len(self.df.columns) > 5:
                                self.process_loaded_data()
                                logger.info(f"CSV cargado exitosamente: {len(self.df)} filas")
                                return True
                        except:
                            continue
            return False
        except:
            return False
    
    def load_from_excel(self):
        """Cargar desde Excel como backup"""
        try:
            if os.path.exists('tabla-chengyus-completa.xlsx'):
                self.df = pd.read_excel('tabla-chengyus-completa.xlsx', engine='openpyxl')
                if not self.df.empty:
                    self.process_loaded_data()
                    logger.info(f"Excel cargado: {len(self.df)} filas")
                    return True
            return False
        except:
            return False
    
    def load_embedded_data(self):
        """Datos embebidos para funcionamiento básico"""
        logger.info("Usando datos embebidos como fallback")
        
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
                'Categoria': 'Conflictos',
                'Nivel de Dificultad': 'HSK7'
            },
            {
                'Dia del año': 4,
                'Chengyu 成语': '入乡随俗',
                'Pinyin': 'ru xiang sui su',
                'Traduccion Literal': 'entrar pueblo seguir costumbres',
                'Significado Figurativo': 'adaptarse a las costumbres locales',
                'Equivalente en Venezolano': 'Donde fueres, haz lo que vieres',
                'Categoria': 'Adaptación',
                'Nivel de Dificultad': 'HSK7'
            },
            {
                'Dia del año': 5,
                'Chengyu 成语': '班门弄斧',
                'Pinyin': 'ban men nong fu',
                'Traduccion Literal': 'mostrar hacha ante Lu Ban',
                'Significado Figurativo': 'mostrar habilidad ante un experto',
                'Equivalente en Venezolano': 'Cachicamo diciéndole a morrocoy conchudo',
                'Categoria': 'Humildad',
                'Nivel de Dificultad': 'HSK8'
            }
        ]
        
        self.df = pd.DataFrame(embedded_data)
        self.process_loaded_data()
    
    def process_loaded_data(self):
        """Procesar y validar datos cargados"""
        try:
            # Limpiar datos vacíos
            self.df = self.df.dropna(how='all')
            
            # Extraer categorías
            if 'Categoria' in self.df.columns:
                self.categorias = self.df['Categoria'].dropna().unique().tolist()
            else:
                self.categorias = []
        except Exception as e:
            logger.error(f"Error procesando datos: {e}")
    
    def format_chengyu(self, row):
        """Formatear chengyu para mostrar al usuario"""
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
            logger.error(f"Error formateando chengyu: {e}")
            return "❌ Error al mostrar el chengyu. Intenta con otro comando."

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Mensaje de bienvenida limpio"""
        welcome_msg = """
🇨🇳 *Bot de Chengyus Chino-Venezolanos* 🇻🇪

¡Aprende expresiones idiomáticas chinas con sus equivalentes en refranes venezolanos!

*Comandos disponibles:*
/chengyu - Obtén un chengyu aleatorio
/dia [1-50] - Chengyu específico por día
/categorias - Explora por categorías
/quiz - Test interactivo de práctica
/hsk [HSK6/HSK7/HSK8/HSK9] - Filtra por nivel
/ayuda - Muestra esta ayuda

¡Empieza tu aprendizaje cultural ahora! 🎓
        """
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')

    async def random_chengyu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /chengyu - Mostrar chengyu aleatorio"""
        if self.df.empty:
            await update.message.reply_text("❌ Servicio temporalmente no disponible. Intenta más tarde.")
            return
            
        try:
            chengyu = self.df.sample(1).iloc[0]
            await update.message.reply_text(self.format_chengyu(chengyu), parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error en random_chengyu: {e}")
            await update.message.reply_text("❌ Error al obtener chengyu. Intenta de nuevo.")

    async def daily_chengyu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /dia [numero] - Chengyu específico por día"""
        if self.df.empty:
            await update.message.reply_text("❌ Servicio temporalmente no disponible. Intenta más tarde.")
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
        except (ValueError, IndexError):
            await update.message.reply_text(f"❌ Uso correcto: /dia [número entre 1-{len(self.df)}]")
        except Exception as e:
            logger.error(f"Error en daily_chengyu: {e}")
            await update.message.reply_text("❌ Error al obtener chengyu del día.")

    async def show_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /categorias - Mostrar categorías disponibles"""
        if not self.categorias:
            await update.message.reply_text("❌ No hay categorías disponibles en este momento.")
            return
            
        try:
            keyboard = []
            for i, cat in enumerate(self.categorias[:20]):  # Máximo 20 categorías
                keyboard.append([InlineKeyboardButton(cat, callback_data=f"cat_{i}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"📚 *Categorías disponibles:*\nElije una categoría para explorar:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error en show_categories: {e}")
            await update.message.reply_text("❌ Error al mostrar categorías.")

    async def category_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejador de selección de categoría"""
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
                    await query.edit_message_text("❌ No hay chengyus disponibles en esta categoría.")
            else:
                await query.edit_message_text("❌ Categoría no válida.")
        except Exception as e:
            logger.error(f"Error en category_handler: {e}")
            await query.edit_message_text("❌ Error al procesar categoría.")

    async def hsk_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /hsk [nivel] - Filtrar por nivel HSK"""
        if self.df.empty:
            await update.message.reply_text("❌ Servicio temporalmente no disponible. Intenta más tarde.")
            return
            
        try:
            if not context.args:
                await update.message.reply_text("ℹ️ Niveles disponibles: HSK6, HSK7, HSK8, HSK9\nEjemplo: /hsk HSK7")
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
                    await update.message.reply_text(f"❌ No hay chengyus disponibles de nivel {level}.")
            else:
                await update.message.reply_text("❌ Niveles válidos: HSK6, HSK7, HSK8, HSK9")
        except Exception as e:
            logger.error(f"Error en hsk_filter: {e}")
            await update.message.reply_text("❌ Error al filtrar por nivel HSK.")

    async def quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /quiz - Quiz interactivo"""
        if self.df.empty or len(self.df) < 4:
            await update.message.reply_text("❌ Quiz temporalmente no disponible. Intenta más tarde.")
            return
            
        try:
            # Seleccionar chengyu correcto
            correct = self.df.sample(1).iloc[0]
            
            # Seleccionar 3 opciones incorrectas
            wrong_options = self.df[self.df.index != correct.name].sample(3)
            
            # Crear opciones mezcladas
            all_options = [correct] + wrong_options.to_dict('records')
            random.shuffle(all_options)
            
            # Encontrar índice correcto
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
            await update.message.reply_text("❌ Error al crear quiz.")

    async def answer_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejador de respuestas del quiz"""
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
            await query.edit_message_text("❌ Error al procesar respuesta.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /ayuda - Información de ayuda"""
        help_text = """
🇨🇳 *Ayuda - Bot de Chengyus* 🇻🇪

*Comandos disponibles:*
/start - Mensaje de bienvenida
/chengyu - Chengyu aleatorio con equivalente venezolano
/dia [1-50] - Chengyu específico por número de día
/categorias - Explorar chengyus por categorías temáticas
/hsk [HSK6/HSK7/HSK8/HSK9] - Filtrar por nivel de dificultad
/quiz - Quiz interactivo de práctica
/ayuda - Esta ayuda

*Ejemplos de uso:*
`/dia 15` - Muestra el chengyu del día 15
`/hsk HSK7` - Muestra chengyus de nivel HSK7

*¿Qué son los chengyus?*
Los chengyus son expresiones idiomáticas chinas de 4 caracteres que contienen sabiduría popular y referencias culturales.

¡Aprende expresiones chinas con sabiduría venezolana! 🎓
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Función principal"""
    # Obtener token de variable de entorno
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN no encontrado en variables de entorno")
        print("Error: Configura BOT_TOKEN en las variables de entorno")
        return
    
    logger.info("Iniciando bot de chengyus...")
    
    try:
        # Crear aplicación
        application = Application.builder().token(token).build()
        bot = ChengyuBot()
        
        # Agregar handlers de comandos
        application.add_handler(CommandHandler('start', bot.start))
        application.add_handler(CommandHandler('chengyu', bot.random_chengyu))
        application.add_handler(CommandHandler('dia', bot.daily_chengyu))
        application.add_handler(CommandHandler('categorias', bot.show_categories))
        application.add_handler(CommandHandler('hsk', bot.hsk_filter))
        application.add_handler(CommandHandler('quiz', bot.quiz))
        application.add_handler(CommandHandler('ayuda', bot.help_command))
        
        # Handlers para botones interactivos
        application.add_handler(CallbackQueryHandler(bot.category_handler, pattern=r"^cat_"))
        application.add_handler(CallbackQueryHandler(bot.answer_handler, pattern=r"^ans_"))
        
        logger.info("Bot configurado exitosamente")
        print("✅ Bot iniciado correctamente")
        
        # Ejecutar bot en modo polling
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Error al iniciar bot: {e}")
        print(f"Error al iniciar bot: {e}")

if __name__ == '__main__':
    main()

