import os
import logging
import pandas as pd
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from threading import Thread
from flask import Flask

# Configurar logging para toda la app
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Servidor Flask mínimo para puerto dummy ---
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


class ChengyuBot:
    def __init__(self):
        """Inicializar el bot con prioridad en archivos Excel"""
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
                0,
                "Sheet1",
                "tabla_chengyus_completa_con_ref",
                "tabla-chengyus-completa",
                "Datos",
                "chengyus",
                "Data",
            ]

            for sheet in sheet_names:
                try:
                    df_test = pd.read_excel(
                        excel_file,
                        sheet_name=sheet,
                        engine="openpyxl"
                    )

                    if df_test.empty or len(df_test) < 10:
                        continue

                    if not self.validate_essential_columns(df_test):
                        continue

                    self.df = df_test
                    self.process_loaded_data()
                    logger.info(
                        f"✅ Excel cargado desde {excel_file}, hoja '{sheet}', {len(self.df)} chengyus"
                    )
                    return True

                except Exception as e:
                    logger.debug(f"Error con {excel_file}, hoja {sheet}: {e}")
                    continue

        logger.warning("❌ No se pudo cargar archivo Excel válido")
        return False
    
    def validate_essential_columns(self, df):
        chengyu_cols = ['Chengyu 成语', 'Chengyu', 'chengyu', 'CHENGYU']
        pinyin_cols = ['Pinyin', 'pinyin', 'PINYIN']
        venezolano_cols = ['Equivalente en Venezolano', 'Equivalente', 'Refran', 'Refrán', 'venezolano']
        has_chengyu = any(col in df.columns for col in chengyu_cols)
        has_pinyin = any(col in df.columns for col in pinyin_cols)
        has_venezolano = any(col in df.columns for col in venezolano_cols)
        return has_chengyu and (has_pinyin or has_venezolano)
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
        """Comando /start limpio sin información técnica"""
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

    # ... seguir con los demás métodos para los comandos /dia, /categorias, /hsk, /quiz, manejo de callbacks, ayuda, etc.

# Aquí continúa la función principal con la integración Flask + bot Telegram

def main():
    # Iniciar servidor flask en hilo aparte
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN no encontrado en variables de entorno")
        print("Error: Configura BOT_TOKEN en las variables de entorno")
        return
    
    logger.info("Iniciando bot de chengyus con prioridad Excel...")
    try:
        application = Application.builder().token(token).build()
        bot = ChengyuBot()
        
        application.add_handler(CommandHandler('start', bot.start))
        application.add_handler(CommandHandler('chengyu', bot.random_chengyu))
        # Agregar aquí todos los demás handlers /dia, /categorias, /hsk, /quiz, /ayuda, callbacks...
        
        logger.info("Bot configurado exitosamente")
        print("✅ Bot iniciado correctamente")
        
        application.run_polling()
    except Exception as e:
        logger.error(f"Error al iniciar bot: {e}")
        print(f"Error al iniciar bot: {e}")

if __name__ == "__main__":
    main()
