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
            },
            {
                'Chengyu 成语': '火上加油',
                'Pinyin': 'huo shang jia you',
                'Traduccion Literal': 'añadir aceite al fuego',
                'Significado Figurativo': 'empeorar una situación',
                'Equivalente en Venezolano': 'Echar leña al fuego',
                'Categoria': 'Conflictos',
                'Nivel de Dificultad': 'HSK7',
                'Frase de Ejemplo': '他本来就很生气，你这样说话是火上加油。'
            },
            {
                'Chengyu 成语': '入乡随俗',
                'Pinyin': 'ru xiang sui su',
                'Traduccion Literal': 'entrar pueblo seguir costumbres',
                'Significado Figurativo': 'adaptarse a las costumbres locales',
                'Equivalente en Venezolano': 'Donde fueres, haz lo que vieres',
                'Categoria': 'Adaptación',
                'Nivel de Dificultad': 'HSK7',
                'Frase de Ejemplo': '到了外国要入乡随俗，尊重当地的文化。'
            },
            {
                'Chengyu 成语': '班门弄斧',
                'Pinyin': 'ban men nong fu',
                'Traduccion Literal': 'mostrar hacha ante Lu Ban',
                'Significado Figurativo': 'mostrar habilidad ante un experto',
                'Equivalente en Venezolano': 'Cachicamo diciéndole a morrocoy conchudo',
                'Categoria': 'Humildad',
                'Nivel de Dificultad': 'HSK8',
                'Frase de Ejemplo': '在专家面前展示技术，这不是班门弄斧吗？'
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
                venezolano = self.get_column_value(opt, ['Equivalente en Venezolano', 'Equivalente', 'Refran'])
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
        """Comando /ayuda - Información de ayuda"""
        total_chengyus = len(self.df) if not self.df.empty else 0
        
        help_text = f"""
🇨🇳 *Ayuda - Bot de Chengyus* 🇻🇪

*Comandos disponibles:*
/start - Mensaje de bienvenida
/chengyu - Chengyu aleatorio con equivalente venezolano
/dia [1-{total_chengyus}] - Chengyu específico por número de día
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


