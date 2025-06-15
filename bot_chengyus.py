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
        """Inicializar el bot con prioridad en archivos Excel"""
        self.df = pd.DataFrame()
        self.categorias = []
        self.data_source = "ninguno"
        self.load_chengyus_data()
    
    def load_chengyus_data(self):
        """Cargar datos priorizando archivos Excel"""
        logger.info("🔄 Iniciando carga de datos desde Excel...")
        
        # Prioridad 1: Archivos Excel específicos
        if self.load_excel_files():
            self.data_source = "Excel"
            return
        
        # Prioridad 2: Archivos CSV como fallback
        if self.load_csv_fallback():
            self.data_source = "CSV backup"
            return
        
        # Último recurso: datos embebidos
        logger.warning("⚠️ Usando datos embebidos limitados")
        self.load_embedded_data()
        self.data_source = "embebidos"
    
    def load_excel_files(self):
        """Cargar archivos Excel con múltiples estrategias"""
        # Lista de archivos Excel a intentar
        excel_files = [
            'tabla-chengyus-completa.xlsx',
            'tabla chengyus completa.xlsx',
            'chengyus.xlsx',
            'chengyus_data.xlsx',
            'data.xlsx'
        ]
        
        for excel_file in excel_files:
            if not os.path.exists(excel_file):
                continue
            
            logger.info(f"📂 Intentando cargar {excel_file}")
            
            # Probar diferentes hojas de cálculo
            sheet_names = [
                0,  # Primera hoja por defecto
                'Sheet1',
                'tabla_chengyus_completa_con_ref',
                'tabla-chengyus-completa',
                'Datos',
                'chengyus',
                'Data'
            ]
            
            for sheet in sheet_names:
                try:
                    # Intentar cargar con openpyxl (mejor para .xlsx)
                    df_test = pd.read_excel(
                        excel_file, 
                        sheet_name=sheet, 
                        engine='openpyxl'
                    )
                    
                    # Validar datos
                    if df_test.empty:
                        continue
                    
                    if len(df_test) < 10:  # Mínimo 10 chengyus
                        continue
                    
                    # Verificar columnas esenciales
                    essential_found = self.validate_essential_columns(df_test)
                    if not essential_found:
                        continue
                    
                    # Archivo Excel válido encontrado
                    self.df = df_test
                    self.process_loaded_data()
                    logger.info(f"✅ Excel cargado exitosamente: {len(self.df)} chengyus desde {excel_file}, hoja '{sheet}'")
                    return True
                    
                except Exception as e:
                    logger.debug(f"Error con {excel_file}, hoja {sheet}: {e}")
                    continue
        
        logger.warning("❌ No se pudo cargar ningún archivo Excel válido")
        return False
    
    def validate_essential_columns(self, df):
        """Validar que el DataFrame tenga columnas esenciales"""
        # Buscar variaciones de columnas de chengyu
        chengyu_cols = ['Chengyu 成语', 'Chengyu', 'chengyu', 'CHENGYU']
        pinyin_cols = ['Pinyin', 'pinyin', 'PINYIN']
        venezolano_cols = [
            'Equivalente en Venezolano',
            'Equivalente',
            'Refran',
            'Refrán',
            'venezolano'
        ]
        
        has_chengyu = any(col in df.columns for col in chengyu_cols)
        has_pinyin = any(col in df.columns for col in pinyin_cols)
        has_venezolano = any(col in df.columns for col in venezolano_cols)
        
        return has_chengyu and (has_pinyin or has_venezolano)
    
    def load_csv_fallback(self):
        """Cargar CSV como fallback si Excel falla"""
        csv_files = [
            'tabla chengyus completa.csv',
            'chengyus_data.csv',
            'tabla-chengyus-completa.csv',
            'chengyus.csv'
        ]
        
        for csv_file in csv_files:
            if not os.path.exists(csv_file):
                continue
                
            try:
                logger.info(f"📂 Intentando CSV fallback: {csv_file}")
                
                # Probar múltiples encodings
                encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
                
                for encoding in encodings:
                    try:
                        df_test = pd.read_csv(csv_file, encoding=encoding)
                        
                        if not df_test.empty and len(df_test) >= 10:
                            essential_found = self.validate_essential_columns(df_test)
                            if essential_found:
                                self.df = df_test
                                self.process_loaded_data()
                                logger.info(f"✅ CSV fallback cargado: {len(self.df)} chengyus")
                                return True
                    except:
                        continue
            except:
                continue
        
        return False
    
    def process_loaded_data(self):
        """Procesar datos con normalización de columnas"""
        try:
            # Limpiar filas completamente vacías
            self.df = self.df.dropna(how='all')
            
            # Normalizar nombres de columnas
            column_mapping = {
                # Variaciones de Chengyu
                'chengyu': 'Chengyu 成语',
                'CHENGYU': 'Chengyu 成语',
                'Chengyu': 'Chengyu 成语',
                
                # Variaciones de Pinyin
                'pinyin': 'Pinyin',
                'PINYIN': 'Pinyin',
                
                # Variaciones de Traducción Literal
                'traduccion literal': 'Traduccion Literal',
                'Traducción Literal': 'Traduccion Literal',
                'literal': 'Traduccion Literal',
                
                # Variaciones de Significado
                'significado figurativo': 'Significado Figurativo',
                'Significado': 'Significado Figurativo',
                'significado': 'Significado Figurativo',
                
                # Variaciones de Equivalente Venezolano
                'equivalente en venezolano': 'Equivalente en Venezolano',
                'equivalente': 'Equivalente en Venezolano',
                'refran': 'Equivalente en Venezolano',
                'refrán': 'Equivalente en Venezolano',
                'venezolano': 'Equivalente en Venezolano',
                
                # Variaciones de Categoría
                'categoria': 'Categoria',
                'categoría': 'Categoria',
                'category': 'Categoria',
                'tema': 'Categoria',
                
                # Variaciones de Nivel
                'nivel de dificultad': 'Nivel de Dificultad',
                'nivel': 'Nivel de Dificultad',
                'hsk': 'Nivel de Dificultad',
                'HSK': 'Nivel de Dificultad',
                
                # Variaciones de Ejemplo
                'frase de ejemplo': 'Frase de Ejemplo',
                'ejemplo': 'Frase de Ejemplo',
                'frase': 'Frase de Ejemplo'
            }
            
            # Aplicar normalización
            for old_name, new_name in column_mapping.items():
                if old_name in self.df.columns and new_name not in self.df.columns:
                    self.df.rename(columns={old_name: new_name}, inplace=True)
            
            logger.info(f"📋 Columnas normalizadas: {list(self.df.columns)}")
            logger.info(f"📊 Total de chengyus procesados: {len(self.df)}")
            
            # Extraer categorías únicas
            if 'Categoria' in self.df.columns:
                self.categorias = self.df['Categoria'].dropna().unique().tolist()
                logger.info(f"📚 Categorías encontradas: {len(self.categorias)}")
            else:
                self.categorias = ['General']
            
            # Mostrar muestra de los primeros datos
            if not self.df.empty:
                logger.info(f"🔍 Muestra de datos: {self.df.head(1).to_dict('records')}")
            
        except Exception as e:
            logger.error(f"Error procesando datos: {e}")
    
    def format_chengyu(self, row):
        """Formatear chengyu con búsqueda flexible de columnas"""
        try:
            # Obtener valores usando función helper
            chengyu = self.get_column_value(row, ['Chengyu 成语', 'Chengyu', 'chengyu'])
            pinyin = self.get_column_value(row, ['Pinyin', 'pinyin'])
            literal = self.get_column_value(row, ['Traduccion Literal', 'literal'])
            significado = self.get_column_value(row, ['Significado Figurativo', 'Significado', 'significado'])
            venezolano = self.get_column_value(row, ['Equivalente en Venezolano', 'Equivalente', 'venezolano'])
            categoria = self.get_column_value(row, ['Categoria', 'categoria'])
            nivel = self.get_column_value(row, ['Nivel de Dificultad', 'Nivel', 'HSK'])
            ejemplo = self.get_column_value(row, ['Frase de Ejemplo', 'Ejemplo', 'frase'])
            
            # Construir mensaje formateado
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
            return "❌ Error al mostrar el chengyu. Intenta con otro comando."
    
    def get_column_value(self, row, possible_columns):
        """Buscar valor en múltiples columnas posibles"""
        for col in possible_columns:
            if col in row and pd.notna(row.get(col)):
                value = str(row.get(col)).strip()
                if value and value != 'nan':
                    return value
        return 'N/A'
    
    def load_embedded_data(self):
        """Datos embebidos con ejemplos completos"""
        embedded_data = [
            {
                'Dia del año': 1,
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
                'Dia del año': 2,
                'Chengyu 成语': '一举两得',
                'Pinyin': 'yi ju liang de',
                'Traduccion Literal': 'una acción dos ganancias',
                'Significado Figurativo': 'lograr dos objetivos con una sola acción',
                'Equivalente en Venezolano': 'Matar dos pájaros de un solo tiro',
                'Categoria': 'Eficiencia y Logro',
                'Nivel de Dificultad': 'HSK6',
                'Frase de Ejemplo': '学习中文既能提高语言能力，又能了解文化，真是一举两得。'
            },
            {
                'Dia del año': 3,
                'Chengyu 成语': '火上加油',
                'Pinyin': 'huo shang jia you',
                'Traduccion Literal': 'añadir aceite al fuego',
                'Significado Figurativo': 'empeorar una situación',
                'Equivalente en Venezolano': 'Echar leña al fuego',
                'Categoria': 'Conflictos',
                'Nivel de Dificultad': 'HSK7',
                'Frase de Ejemplo': '他本来就很生气，你这样说话是火上加油。'
            }
        ]
        
        self.df = pd.DataFrame(embedded_data)
        self.process_loaded_data()
        logger.info(f"✅ Datos embebidos cargados: {len(self.df)} chengyus")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start optimizado para Excel"""
        total_chengyus = len(self.df) if not self.df.empty else 0
        
        welcome_msg = f"""
🇨🇳 *Bot de Chengyus Chino-Venezolanos* 🇻🇪

¡Aprende expresiones idiomáticas chinas con sus equivalentes en refranes venezolanos!


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
    
    async def random_chengyu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /chengyu - Chengyu aleatorio"""
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
        """Comando /dia [numero] - Chengyu por día"""
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
        """Comando /categorias - Navegación por categorías"""
        if not self.categorias:
            await update.message.reply_text("❌ No hay categorías disponibles en este momento.")
            return
            
        try:
            keyboard = []
            for i, cat in enumerate(self.categorias[:20]):  # Máximo 20 categorías
                keyboard.append([InlineKeyboardButton(cat, callback_data=f"cat_{i}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"📚 *Categorías disponibles ({len(self.categorias)}):*\nElije una categoría para explorar:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error en show_categories: {e}")
            await update.message.reply_text("❌ Error al mostrar categorías.")

    async def category_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejador para botones de categorías"""
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
                if self.get_column_value(opt, ['Chengyu 成语', 'Chengyu']) == self.get_column_value(correct, ['Chengyu 成语', 'Chengyu']):
                    correct_index = i
                    break
            
            # Crear teclado de opciones
            keyboard = []
            for i, opt in enumerate(all_options):
                venezolano = self.get_column_value(opt, ['Equivalente en Venezolano', 'Equivalente'])
                display_text = venezolano[:45] + "..." if len(venezolano) > 45 else venezolano
                keyboard.append([InlineKeyboardButton(
                    display_text,
                    callback_data=f"ans_{i}_{correct_index}_{correct.name}"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            chengyu = self.get_column_value(correct, ['Chengyu 成语', 'Chengyu'])
            pinyin = self.get_column_value(correct, ['Pinyin', 'pinyin'])
            
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
        """Comando /ayuda"""
        total_chengyus = len(self.df) if not self.df.empty else 0
        
        help_text = f"""
🇨🇳 *Ayuda - Bot de Chengyus* 🇻🇪

*Comandos disponibles:*
/start - Mensaje de bienvenida
/chengyu - Chengyu aleatorio con equivalente venezolano
/dia [1-{total_chengyus}] - Chengyu específico por número
/categorias - Explorar por categorías temáticas
/hsk [HSK6/HSK7/HSK8/HSK9] - Filtrar por nivel
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
    
    logger.info("Iniciando bot de chengyus con prioridad Excel...")
    
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
        
        # Ejecutar bot
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Error al iniciar bot: {e}")
        print(f"Error al iniciar bot: {e}")

if __name__ == '__main__':
    main()
