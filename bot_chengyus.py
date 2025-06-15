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
        try:
            # Intentar cargar el archivo Excel
            self.df = pd.read_excel('tabla-chengyus-completa.xlsx')
            print(f"Archivo Excel cargado exitosamente con {len(self.df)} chengyus")
            
            # Verificar columnas necesarias
            required_columns = ['Chengyu 成语', 'Pinyin', 'Traduccion Literal', 
                              'Significado Figurativo', 'Equivalente en Venezolano', 
                              'Categoria', 'Nivel de Dificultad']
            
            for col in required_columns:
                if col not in self.df.columns:
                    print(f"Advertencia: Columna '{col}' no encontrada")
            
            # Obtener categorías únicas
            self.categorias = self.df['Categoria'].dropna().unique().tolist() if 'Categoria' in self.df.columns else []
            
        except FileNotFoundError:
            print("Error: No se encontró el archivo tabla-chengyus-completa.xlsx")
            self.df = pd.DataFrame()
            self.categorias = []
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")
            self.df = pd.DataFrame()
            self.categorias = []
    
    def format_chengyu(self, row):
        """Formatear mensaje de chengyu con emojis"""
        try:
            chengyu = row.get('Chengyu 成语', 'N/A')
            pinyin = row.get('Pinyin', 'N/A')
            literal = row.get('Traduccion Literal', 'N/A')
            significado = row.get('Significado Figurativo', 'N/A')
            venezolano = row.get('Equivalente en Venezolano', 'N/A')
            categoria = row.get('Categoria', 'N/A')
            nivel = row.get('Nivel de Dificultad', 'N/A')
            
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
            print(f"Error al formatear chengyu: {e}")
            return "Error al mostrar el chengyu. Intenta de nuevo."

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        welcome_msg = """
🇨🇳 *Bot de Chengyus Chino-Venezolanos* 🇻🇪

¡Aprende expresiones idiomáticas chinas con sus equivalentes en refranes venezolanos!

*Comandos disponibles:*
/chengyu - Obtén un chengyu aleatorio
/dia [1-50] - Chengyu específico por día
/categorias - Explora por categorías
/quiz - Test interactivo
/hsk [nivel] - Filtra por nivel HSK
/ayuda - Muestra esta ayuda

¡Empieza tu aprendizaje cultural ahora!
        """
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')

    async def random_chengyu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /chengyu - Mostrar chengyu aleatorio"""
        if self.df.empty:
            await update.message.reply_text("❌ No hay chengyus disponibles")
            return
            
        try:
            chengyu = self.df.sample(1).iloc[0]
            await update.message.reply_text(self.format_chengyu(chengyu), parse_mode='Markdown')
        except Exception as e:
            print(f"Error en random_chengyu: {e}")
            await update.message.reply_text("❌ Error al obtener chengyu aleatorio")

    async def daily_chengyu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /dia [numero] - Chengyu por día"""
        if self.df.empty:
            await update.message.reply_text("❌ No hay chengyus disponibles")
            return
            
        try:
            if not context.args:
                await update.message.reply_text("❌ Uso correcto: /dia [número entre 1-50]")
                return
                
            day = int(context.args[0])
            if 1 <= day <= len(self.df):
                chengyu = self.df.iloc[day-1]
                await update.message.reply_text(self.format_chengyu(chengyu), parse_mode='Markdown')
            else:
                await update.message.reply_text(f"⚠️ El día debe estar entre 1 y {len(self.df)}")
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Uso correcto: /dia [número entre 1-50]")
        except Exception as e:
            print(f"Error en daily_chengyu: {e}")
            await update.message.reply_text("❌ Error al obtener chengyu del día")

    async def show_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /categorias - Mostrar categorías"""
        if not self.categorias:
            await update.message.reply_text("❌ No hay categorías disponibles")
            return
            
        try:
            keyboard = []
            for i, cat in enumerate(self.categorias[:20]):  # Limitar a 20 categorías
                keyboard.append([InlineKeyboardButton(cat, callback_data=f"cat_{i}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "📚 *Categorías disponibles:*\nElije una categoría:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error en show_categories: {e}")
            await update.message.reply_text("❌ Error al mostrar categorías")

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
                    await query.edit_message_text("❌ No hay chengyus en esta categoría")
            else:
                await query.edit_message_text("❌ Categoría no válida")
        except Exception as e:
            print(f"Error en category_handler: {e}")
            await query.edit_message_text("❌ Error al procesar categoría")

    async def hsk_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /hsk [nivel] - Filtrar por nivel HSK"""
        if self.df.empty:
            await update.message.reply_text("❌ No hay chengyus disponibles")
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
            print(f"Error en hsk_filter: {e}")
            await update.message.reply_text("❌ Error al filtrar por nivel HSK")

    async def quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /quiz - Quiz interactivo"""
        if self.df.empty or len(self.df) < 4:
            await update.message.reply_text("❌ No hay suficientes chengyus para el quiz")
            return
            
        try:
            # Seleccionar chengyu correcto
            correct = self.df.sample(1).iloc[0]
            
            # Seleccionar 3 opciones incorrectas
            wrong_options = self.df[self.df.index != correct.name].sample(3)
            
            # Mezclar opciones
            all_options = [correct] + wrong_options.to_dict('records')
            random.shuffle(all_options)
            
            # Crear teclado
            keyboard = []
            for i, opt in enumerate(all_options):
                venezolano = opt.get('Equivalente en Venezolano', 'N/A')
                keyboard.append([InlineKeyboardButton(
                    venezolano[:50] + "..." if len(venezolano) > 50 else venezolano,
                    callback_data=f"ans_{i}_{correct.name}"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            chengyu = correct.get('Chengyu 成语', 'N/A')
            pinyin = correct.get('Pinyin', 'N/A')
            
            await update.message.reply_text(
                f"❓ *Quiz:* ¿Cuál es el equivalente venezolano de:\n\n*{chengyu}* ({pinyin})?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error en quiz: {e}")
            await update.message.reply_text("❌ Error al crear quiz")

    async def answer_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejador de respuestas del quiz"""
        query = update.callback_query
        await query.answer()
        
        try:
            _, selected_idx, correct_idx = query.data.split('_')
            correct_row = self.df.loc[int(correct_idx)]
            
            if selected_idx == "0":  # Primera opción (correcta por diseño)
                msg = "✅ ¡Correcto! "
            else:
                msg = "❌ Incorrecto. "
                
            msg += f"La respuesta correcta es:\n{self.format_chengyu(correct_row)}"
            await query.edit_message_text(msg, parse_mode='Markdown')
        except Exception as e:
            print(f"Error en answer_handler: {e}")
            await query.edit_message_text("❌ Error al procesar respuesta")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /ayuda"""
        help_text = """
🇨🇳 *Ayuda - Bot de Chengyus* 🇻🇪

*Comandos disponibles:*
/start - Mensaje de bienvenida
/chengyu - Chengyu aleatorio
/dia [1-50] - Chengyu específico
/categorias - Explorar por categorías
/hsk [HSK6/HSK7/HSK8/HSK9] - Filtrar por nivel
/quiz - Quiz interactivo
/ayuda - Esta ayuda

*Ejemplos de uso:*
`/dia 15` - Muestra el chengyu del día 15
`/hsk HSK7` - Muestra chengyus de nivel HSK7

¡Aprende expresiones chinas con sabiduría venezolana!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Función principal"""
    # Obtener token de variable de entorno
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Error: BOT_TOKEN no encontrado en variables de entorno")
        return
    
    # Crear aplicación
    application = Application.builder().token(token).build()
    bot = ChengyuBot()
    
    # Agregar handlers
    application.add_handler(CommandHandler('start', bot.start))
    application.add_handler(CommandHandler('chengyu', bot.random_chengyu))
    application.add_handler(CommandHandler('dia', bot.daily_chengyu))
    application.add_handler(CommandHandler('categorias', bot.show_categories))
    application.add_handler(CommandHandler('hsk', bot.hsk_filter))
    application.add_handler(CommandHandler('quiz', bot.quiz))
    application.add_handler(CommandHandler('ayuda', bot.help_command))
    
    # Handlers para botones
    application.add_handler(CallbackQueryHandler(bot.category_handler, pattern=r"^cat_"))
    application.add_handler(CallbackQueryHandler(bot.answer_handler, pattern=r"^ans_"))
    
    print("Bot iniciado. Presiona Ctrl+C para detener.")
    
    # Ejecutar bot
    application.run_polling()

if __name__ == '__main__':
    main()
