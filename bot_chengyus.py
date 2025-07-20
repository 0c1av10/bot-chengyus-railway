import os
import logging
import asyncio                     
import aiohttp                     
import pandas as pd
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from threading import Thread
from flask import Flask

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Servidor Flask mínimo para puerto dummy
flask_app = Flask(__name__)

@flask_app.route("/")
def health_check():
    return "Bot is running", 200

@flask_app.route("/health")
def health():
    return {"status": "ok", "uptime": "running"}, 200

def run_flask():
    port = int(os.getenv("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, debug=False)
KEEPALIVE_URL = os.getenv(
    "KEEPALIVE_URL", "https://bot-chengyus-railway.onrender.com/"
)
INTERVAL = 10 * 60  # 10 minutos


async def keep_alive():
    """Hace un ping HTTP cada 10 minutos para evitar hibernación."""
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await session.get(KEEPALIVE_URL, timeout=10)
            except Exception:
                pass
            await asyncio.sleep(INTERVAL)


class ChengyuBot:
    def __init__(self):
        """Inicialización y carga de datos"""
        self.df = pd.DataFrame()
        self.categorias = []
        self.data_source = "ninguno"
        self.load_chengyus_data()

    def load_chengyus_data(self):
        logger.info("🔄 Iniciando carga de datos desde Excel...")
        if self.load_excel_files():
            self.data_source = "Excel"
            return
        if self.load_csv_fallback():
            self.data_source = "CSV backup"
            return
        logger.warning("⚠️ Usando datos embebidos limitados")
        self.load_embedded_data()
        self.data_source = "embebidos"

    def load_excel_files(self):
        excel_files = [
            "tabla-chengyus-completa.xlsx",
            "tabla chengyus completa.xlsx",
            "chengyus.xlsx",
            "chengyus_data.xlsx",
            "data.xlsx",
        ]
        for excel_file in excel_files:
            if not os.path.exists(excel_file):
                continue
            logger.info(f"📂 Intentando cargar {excel_file}")
            sheet_names = [
                0, "Sheet1", "tabla_chengyus_completa_con_ref",
                "tabla-chengyus-completa", "Datos", "chengyus", "Data"
            ]
            for sheet in sheet_names:
                try:
                    df_test = pd.read_excel(
                        excel_file, sheet_name=sheet, engine="openpyxl")
                    if df_test.empty or len(df_test) < 10:
                        continue
                    if not self.validate_essential_columns(df_test):
                        continue
                    self.df = df_test
                    self.process_loaded_data()
                    logger.info(f"✅ Excel cargado: {len(self.df)} chengyus desde {excel_file}, hoja {sheet}")
                    return True
                except Exception as e:
                    logger.debug(f"Error con {excel_file} hoja {sheet}: {e}")
                    continue
        logger.warning("❌ No se pudo cargar archivo Excel válido")
        return False

    def validate_essential_columns(self, df):
        chengyu_cols = ["Chengyu 成语", "Chengyu", "chengyu", "CHENGYU"]
        pinyin_cols = ["Pinyin", "pinyin", "PINYIN"]
        venezolano_cols = [
            "Equivalente en Venezolano",
            "Equivalente",
            "Refran",
            "Refrán",
            "venezolano",
        ]
        has_chengyu = any(col in df.columns for col in chengyu_cols)
        has_pinyin = any(col in df.columns for col in pinyin_cols)
        has_venezolano = any(col in df.columns for col in venezolano_cols)
        return has_chengyu and (has_pinyin or has_venezolano)
    def load_csv_fallback(self):
        csv_files = [
            "tabla chengyus completa.csv",
            "chengyus_data.csv",
            "tabla-chengyus-completa.csv",
            "chengyus.csv",
        ]
        for csv_file in csv_files:
            if not os.path.exists(csv_file):
                continue
            logger.info(f"📂 Intentando CSV fallback: {csv_file}")
            encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
            for encoding in encodings:
                try:
                    df_test = pd.read_csv(csv_file, encoding=encoding)
                    if df_test.empty or len(df_test) < 10:
                        continue
                    if not self.validate_essential_columns(df_test):
                        continue
                    self.df = df_test
                    self.process_loaded_data()
                    logger.info(f"✅ CSV fallback cargado: {len(self.df)} chengyus")
                    return True
                except Exception:
                    continue
        return False

    def process_loaded_data(self):
        try:
            self.df = self.df.dropna(how="all")
            column_mapping = {
                "chengyu": "Chengyu 成语",
                "CHENGYU": "Chengyu 成语",
                "Chengyu": "Chengyu 成语",
                "pinyin": "Pinyin",
                "PINYIN": "Pinyin",
                "traduccion literal": "Traduccion Literal",
                "Traducción Literal": "Traduccion Literal",
                "literal": "Traduccion Literal",
                "significado figurativo": "Significado Figurativo",
                "Significado": "Significado Figurativo",
                "significado": "Significado Figurativo",
                "equivalente en venezolano": "Equivalente en Venezolano",
                "equivalente": "Equivalente en Venezolano",
                "refran": "Equivalente en Venezolano",
                "refrán": "Equivalente en Venezolano",
                "venezolano": "Equivalente en Venezolano",
                "categoria": "Categoria",
                "categoría": "Categoria",
                "category": "Categoria",
                "tema": "Categoria",
                "nivel de dificultad": "Nivel de Dificultad",
                "nivel": "Nivel de Dificultad",
                "hsk": "Nivel de Dificultad",
                "HSK": "Nivel de Dificultad",
                "frase de ejemplo": "Frase de Ejemplo",
                "ejemplo": "Frase de Ejemplo",
                "frase": "Frase de Ejemplo",
            }
            for old_name, new_name in column_mapping.items():
                if old_name in self.df.columns and new_name not in self.df.columns:
                    self.df.rename(columns={old_name: new_name}, inplace=True)
            logger.info(f"📋 Columnas normalizadas: {list(self.df.columns)}")
            logger.info(f"📊 Total de chengyus procesados: {len(self.df)}")
            if "Categoria" in self.df.columns:
                self.categorias = self.df["Categoria"].dropna().unique().tolist()
                logger.info(f"📚 Categorías encontradas: {len(self.categorias)}")
            else:
                self.categorias = ["General"]
            if not self.df.empty:
                logger.info(f"🔍 Muestra de datos: {self.df.head(1).to_dict('records')}")
        except Exception as e:
            logger.error(f"Error procesando datos: {e}")

    def format_chengyu(self, row):
        try:
            chengyu = self.get_column_value(row, ["Chengyu 成语", "Chengyu", "chengyu"])
            pinyin = self.get_column_value(row, ["Pinyin", "pinyin"])
            literal = self.get_column_value(row, ["Traduccion Literal", "literal"])
            significado = self.get_column_value(
                row, ["Significado Figurativo", "Significado", "significado"]
            )
            venezolano = self.get_column_value(
                row, ["Equivalente en Venezolano", "Equivalente", "venezolano"]
            )
            categoria = self.get_column_value(row, ["Categoria", "categoria"])
            nivel = self.get_column_value(row, ["Nivel de Dificultad", "Nivel", "HSK"])
            ejemplo = self.get_column_value(row, ["Frase de Ejemplo", "Ejemplo", "frase"])

            formatted_text = f"""
🎋 *{chengyu}* ({pinyin})

📜 *Traducción literal:* {literal}
💡 *Significado:* {significado}

🇻🇪 *Equivalente venezolano:*
"_{venezolano}_"
"""
            if ejemplo and ejemplo != "N/A" and ejemplo.strip():
                formatted_text += f"""
📝 *Ejemplo en chino:*
{ejemplo}
"""

            formatted_text += f"""
📌 *Categoría:* {categoria}
🏮 *Nivel HSK:* {nivel}
            """
            return formatted_text
        except Exception as e:
            logger.error(f"Error formateando chengyu: {e}")
            return "❌ Error al mostrar el chengyu. Intenta con otro comando."

    def get_column_value(self, row, possible_columns):
        for col in possible_columns:
            if col in row and pd.notna(row.get(col)):
                value = str(row.get(col)).strip()
                if value and value != "nan":
                    return value
        return "N/A"

    def load_embedded_data(self):
        embedded_data = [
            {
                "Dia del año": 1,
                "Chengyu 成语": "莫名其妙",
                "Pinyin": "mo ming qi miao",
                "Traduccion Literal": "sin nombre su misterio",
                "Significado Figurativo": "algo inexplicable sin razón aparente",
                "Equivalente en Venezolano": "¡Esto no tiene nombre!",
                "Categoria": "Confusión y Misterio",
                "Nivel de Dificultad": "HSK6",
                "Frase de Ejemplo": "他的行为莫名其妙，让大家都很困惑。",
            },
            {
                "Dia del año": 2,
                "Chengyu 成语": "一举两得",
                "Pinyin": "yi ju liang de",
                "Traduccion Literal": "una acción dos ganancias",
                "Significado Figurativo": "lograr dos objetivos con una sola acción",
                "Equivalente en Venezolano": "Matar dos pájaros de un solo tiro",
                "Categoria": "Eficiencia y Logro",
                "Nivel de Dificultad": "HSK6",
                "Frase de Ejemplo": "学习中文既能提高语言能力，又能了解文化，真是一举两得。",
            },
            {
                "Dia del año": 3,
                "Chengyu 成语": "火上加油",
                "Pinyin": "huo shang jia you",
                "Traduccion Literal": "añadir aceite al fuego",
                "Significado Figurativo": "empeorar una situación",
                "Equivalente en Venezolano": "Echar leña al fuego",
                "Categoria": "Conflictos",
                "Nivel de Dificultad": "HSK7",
                "Frase de Ejemplo": "他本来就很生气，你这样说话是火上加油。",
            },
        ]
        self.df = pd.DataFrame(embedded_data)
        self.process_loaded_data()
        logger.info(f"✅ Datos embebidos cargados: {len(self.df)} chengyus")
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start para iniciar conversación"""
        welcome_msg = """
🇨🇳 *Bot de Chengyus Chino-Venezolanos* 🇻🇪

¡Aprende expresiones idiomáticas chinas con sus equivalentes en refranes venezolanos!

*Comandos disponibles:*
/chengyu - Obtén un chengyu aleatorio
/dia [1-50] - Chengyu específico por día
/categorias - Explora por categorías
/quiz - Test interactivo de práctica
/hsk [HSK6/HSK7/HSK8/HSK9] - Filtrar por nivel
/ayuda - Muestra esta ayuda

¡Empieza tu aprendizaje cultural ahora! 🎓
"""
        await update.message.reply_text(welcome_msg, parse_mode="Markdown")

    async def random_chengyu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /chengyu para obtener un chengyu aleatorio"""
        if self.df.empty:
            await update.message.reply_text(
                "❌ Servicio temporalmente no disponible. Intenta más tarde."
            )
            return
        try:
            chengyu = self.df.sample(1).iloc[0]
            await update.message.reply_text(
                self.format_chengyu(chengyu), parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error en random_chengyu: {e}")
            await update.message.reply_text("❌ Error al obtener chengyu. Inténtalo de nuevo.")

    async def daily_chengyu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /dia [número] para chengyu del día"""
        if self.df.empty:
            await update.message.reply_text(
                "❌ Servicio temporalmente no disponible. Intenta más tarde."
            )
            return
        try:
            if not context.args:
                await update.message.reply_text(f"❌ Uso correcto: /dia [número 1-{len(self.df)}]")
                return
            dia = int(context.args[0])
            if 1 <= dia <= len(self.df):
                chengyu = self.df.iloc[dia - 1]
                await update.message.reply_text(
                    self.format_chengyu(chengyu), parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(f"⚠️ El día debe estar entre 1 y {len(self.df)}")
        except (ValueError, IndexError):
            await update.message.reply_text(f"❌ Uso correcto: /dia [número 1-{len(self.df)}]")
        except Exception as e:
            logger.error(f"Error en daily_chengyu: {e}")
            await update.message.reply_text("❌ Error al obtener el chengyu del día.")

    async def show_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /categorias para mostrar categorías disponibles"""
        if not self.categorias:
            await update.message.reply_text("❌ No hay categorías disponibles.")
            return
        try:
            teclado = [
                [InlineKeyboardButton(cat, callback_data=f"cat_{i}")]
                for i, cat in enumerate(self.categorias[:20])  # Limitar a 20 categorías
            ]
            reply_markup = InlineKeyboardMarkup(teclado)
            await update.message.reply_text(
                "📚 *Categorías disponibles:*\nSelecciona una categoría:",
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Error en show_categories: {e}")
            await update.message.reply_text("❌ Error al mostrar categorías.")

    async def category_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejador para respuesta de botones de categorías"""
        query = update.callback_query
        await query.answer()
        try:
            idx = int(query.data.split("_")[1])
            if idx < len(self.categorias):
                categoria = self.categorias[idx]
                df_cat = self.df[self.df["Categoria"] == categoria]
                if not df_cat.empty:
                    chengyu = df_cat.sample(1).iloc[0]
                    await query.edit_message_text(
                        f"📖 *Categoría: {categoria}*\n\n{self.format_chengyu(chengyu)}",
                        parse_mode="Markdown",
                    )
                else:
                    await query.edit_message_text("❌ No hay chengyus en esa categoría.")
            else:
                await query.edit_message_text("❌ Categoría no válida.")
        except Exception as e:
            logger.error(f"Error en category_handler: {e}")
            await query.edit_message_text("❌ Error al procesar la categoría.")
    async def hsk_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /hsk [nivel] filtra chengyus por nivel HSK"""
        if self.df.empty:
            await update.message.reply_text(
                "❌ Servicio temporalmente no disponible. Intenta más tarde."
            )
            return
        try:
            if not context.args:
                await update.message.reply_text(
                    "ℹ️ Niveles disponibles: HSK6, HSK7, HSK8, HSK9\nEjemplo: /hsk HSK7"
                )
                return
            nivel_input = context.args[0].upper().replace(" ", "")
            niveles_validos = ["HSK6", "HSK7", "HSK8", "HSK9"]
            if nivel_input not in niveles_validos:
                await update.message.reply_text(f"❌ Niveles válidos: {', '.join(niveles_validos)}")
                return

            columnas_nivel = [
                "Nivel de Dificultad",
                "Nivel de Dificulatad",
                "Nivel",
                "HSK",
                "level",
                "Level",
            ]
            filtf = pd.DataFrame()
            for col in columnas_nivel:
                if col in self.df.columns:
                    serie = self.df[col].astype(str).str.replace(" ", "").str.upper()
                    filtf = self.df[serie == nivel_input]
                    if not filtf.empty:
                        break

            if filtf.empty:
                await update.message.reply_text(f"❌ No hay chengyus de nivel {nivel_input}.")
                return
            
            respuesta = f"🎓 *Todos los Chengyus nivel {nivel_input}* 🏮\n\n"
            for _, row in filtf.iterrows():
                chengyu = self.get_column_value(row, ["Chengyu 成语", "Chengyu"])
                pinyin = self.get_column_value(row, ["Pinyin", "pinyin"])
                nivel = self.get_column_value(row, ["Nivel de Dificultad", "Nivel", "HSK"])
                respuesta += f"• {chengyu} ({pinyin}) - [{nivel}]\n"
            
            # Telegram límite es 4096 chars, dividimos si hace falta
            for part in [respuesta[i : i + 4000] for i in range(0, len(respuesta), 4000)]:
                await update.message.reply_text(part, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error en hsk_filter: {e}")
            await update.message.reply_text(f"❌ Error al filtrar nivel HSK: {e}")

    async def quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /quiz para prueba interactiva"""
        if self.df.empty or len(self.df) < 4:
            await update.message.reply_text("❌ Quiz temporalmente no disponible. Intenta más tarde.")
            return
        try:
            correcto = self.df.sample(1).iloc[0]
            opciones_erroneas = self.df[self.df.index != correcto.name].sample(3)
            todas_opciones = [correcto] + opciones_erroneas.to_dict("records")
            random.shuffle(todas_opciones)
            index_correcto = None
            for i, opt in enumerate(todas_opciones):
                if (
                    self.get_column_value(opt, ["Chengyu 成语", "Chengyu"])
                    == self.get_column_value(correcto, ["Chengyu 成语", "Chengyu"])
                ):
                    index_correcto = i
                    break
            
            teclado = []
            for i, opt in enumerate(todas_opciones):
                texto = self.get_column_value(opt, ["Equivalente en Venezolano", "Equivalente"])
                muestra = texto[:45] + "..." if len(texto) > 45 else texto
                teclado.append(
                    [InlineKeyboardButton(muestra, callback_data=f"ans_{i}_{index_correcto}_{correcto.name}")]
                )
            reply_markup = InlineKeyboardMarkup(teclado)
            chengyu = self.get_column_value(correcto, ["Chengyu 成语", "Chengyu"])
            pinyin = self.get_column_value(correcto, ["Pinyin", "pinyin"])
            await update.message.reply_text(
                f"❓ *Quiz:* ¿Cuál es el equivalente venezolano de:\n\n*{chengyu}* ({pinyin})?",
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Error en quiz: {e}")
            await update.message.reply_text("❌ Error al crear el quiz.")

    async def answer_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejador de respuestas para el quiz"""
        query = update.callback_query
        await query.answer()
        try:
            partes = query.data.split("_")
            elegido = int(partes[1])
            correcto = int(partes[2])
            idx_real = int(partes[3])
            fila_correcta = self.df.loc[idx_real]
            if elegido == correcto:
                msg = "✅ ¡Correcto! "
            else:
                msg = "❌ Incorrecto. "
            msg += f"La respuesta correcta es:\n{self.format_chengyu(fila_correcta)}"
            await query.edit_message_text(msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error en answer_handler: {e}")
            await query.edit_message_text("❌ Error al procesar la respuesta.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        texto_ayuda = """
🇨🇳 *Ayuda - Bot de Chengyus* 🇻🇪

*Comandos:*
/start - Mensaje de bienvenida
/chengyu - Chengyu aleatorio
/dia [1-50] - Chengyu por número
/categorias - Explorar categorías
/hsk [HSK6-9] - Filtrar por nivel
/quiz - Quiz interactivo
/ayuda - Mostrar esta ayuda

*Ejemplos:*
`/dia 15` - Chsngyu del día 15
`/hsk HSK7` - Chengyus nivel HSK7

Los chengyus son expresiones idiomáticas chinas de 4 caracteres con gran significado cultural.

¡Disfruta aprendiendo! 🎓
"""
        await update.message.reply_text(texto_ayuda, parse_mode="Markdown")
def main():
    # Arrancar servidor Flask en hilo separado para puerto dummy
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Cargar token del bot de variable de entorno
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN no encontrado en variables de entorno")
        print("Error: Configura BOT_TOKEN en variables de entorno")
        return

    logger.info("Iniciando bot de chengyus con prioridad en Excel, CSV y embebidos.")

    try:
        # Construir la aplicación del bot
        application = Application.builder().token(token).build()
        bot = ChengyuBot()

        # Agregar handlers de comandos
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("chengyu", bot.random_chengyu))
        application.add_handler(CommandHandler("dia", bot.daily_chengyu))
        application.add_handler(CommandHandler("categorias", bot.show_categories))
        application.add_handler(CommandHandler("hsk", bot.hsk_filter))
        application.add_handler(CommandHandler("quiz", bot.quiz))
        application.add_handler(CommandHandler("ayuda", bot.help_command))

        # Agregar handlers para botones interactivos
        application.add_handler(CallbackQueryHandler(bot.category_handler, pattern=r"^cat_"))
        application.add_handler(CallbackQueryHandler(bot.answer_handler, pattern=r"^ans_"))

        logger.info("Bot configurado exitosamente, iniciando polling...")
        print("✅ Bot iniciado correctamente")

        # Ejecutar bot con polling
        application.run_polling()

    except Exception as e:
        logger.error(f"Error al iniciar bot: {e}")
        print(f"Error al iniciar bot: {e}")


if __name__ == "__main__":
    main()


