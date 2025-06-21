import os
import logging
import pandas as pd
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Configuración de logging para debug
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

class ChengyuBot:
    def __init__(self):
        """Inicializa el bot cargando datos y configurando categorías"""  
        self.df = pd.DataFrame([])  
        self.categorias = []  
        self.load_chengyus_data()  

    def load_chengyus_data(self):
        """
        Carga los chengyus desde Excel (.xlsx) o CSV (.csv),
        con fallback a datos embebidos si ambos fallan.
        """
        # Prioriza Excel
        excel_file = "tabla-chengyus-completa.xlsx"  
        if os.path.exists(excel_file):
            try:
                df = pd.read_excel(excel_file, engine="openpyxl")  
                if len(df) >= 10:
                    self.df = df.dropna(how="all")  
                    self.normalize_columns()  
                    logger.info(f"Datos cargados desde Excel: {len(self.df)} filas")  
                    return
            except Exception as e:
                logger.warning(f"Error leyendo Excel '{excel_file}': {e}")

        # Fallback a CSV
        csv_file = "tabla chengyus completa.csv"  
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file, encoding="utf-8")  
                if len(df) >= 10:
                    self.df = df.dropna(how="all")  
                    self.normalize_columns()  
                    logger.info(f"Datos cargados desde CSV: {len(self.df)} filas")  
                    return
            except Exception as e:
                logger.warning(f"Error leyendo CSV '{csv_file}': {e}")

        # Último recurso: datos embebidos
        self.df = pd.DataFrame([
            {
                "Chengyu 成语": "雪中送炭",
                "Pinyin": "xuě zhōng sòng tàn",
                "Traduccion Literal": "enviar carbón en la nieve",
                "Significado Figurativo": "auxiliar en momentos críticos",
                "Frase de Ejemplo": "朋友雪中送炭，让我渡过难关。",
                "Equivalente en Venezolano": "Amigo en la necesidad, amigo de verdad",
                "Categoria": "Mutua Ayuda",
                "Nivel de Dificultad": "HSK6",
            },
        ])
        self.normalize_columns()  
        logger.info("Datos embebidos cargados como último recurso")

    def normalize_columns(self):
        """
        Normaliza nombres de columnas clave a formatos esperados
        y extrae la lista de categorías.
        """
        mapping = {
            "chengyu": "Chengyu 成语",
            "pinyin": "Pinyin",
            "traduccion literal": "Traduccion Literal",
            "significado figurativo": "Significado Figurativo",
            "frase de ejemplo": "Frase de Ejemplo",
            "equivalente en venezolano": "Equivalente en Venezolano",
            "nivel de dificultad": "Nivel de Dificultad",
            "categoria": "Categoria",
        }
        for old, new in mapping.items():
            if old in self.df.columns and new not in self.df.columns:
                self.df.rename(columns={old: new}, inplace=True)

        # Extrae categorías únicas
        if "Categoria" in self.df.columns:
            self.categorias = self.df["Categoria"].dropna().unique().tolist()  
            logger.info(f"Categorías encontradas: {len(self.categorias)}")  

    def format_chengyu(self, row):
        """
        Formatea un chengyu completo con:
        - Traducción literal  
        - Significado figurado  
        - Ejemplo en chino  
        - Equivalente en venezolano  
        - Categoría y nivel HSK  
        """
        c       = row.get("Chengyu 成语", "N/A")  
        p       = row.get("Pinyin", "N/A")  
        literal = row.get("Traduccion Literal", "N/A")  
        sig     = row.get("Significado Figurativo", "N/A")  
        ejemplo = row.get("Frase de Ejemplo", "").strip()  
        ev      = row.get("Equivalente en Venezolano", "N/A")  
        cat     = row.get("Categoria", "N/A")  
        lvl     = row.get("Nivel de Dificultad", "N/A")  

        text = (
            f"🎋 *{c}* ({p})\n\n"
            f"📜 *Traducción literal:* {literal}\n"
            f"💡 *Significado:* {sig}\n"
        )
        if ejemplo:
            text += f"📝 *Ejemplo en chino:* {ejemplo}\n\n"
        else:
            text += "\n"
        text += (
            f"🇻🇪 _{ev}_\n"
            f"📌 *Categoría:* {cat}\n"
            f"🏮 *Nivel HSK:* {lvl}"
        )
        return text

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /start: Mensaje de bienvenida limpio sin mostrar estado técnico.
        """
        msg = (
            "🌐 *Bot de Chengyus Chino-Venezolanos*\n\n"
            "Comandos disponibles:\n"
            "/chengyu    – Muestra un chengyu aleatorio\n"
            "/dia [1-50] – Chengyu por número de día\n"
            "/categorias – Explora por categorías\n"
            "/hsk [HSK6–HSK9] – Lista todos los chengyus de un nivel\n"
            "/quiz       – Prueba interactiva\n"
            "/ayuda      – Este mensaje"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def chengyu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /chengyu: Selecciona y muestra un chengyu aleatorio.
        """
        if self.df.empty:
            await update.message.reply_text("Servicio no disponible.")
            return
        row = self.df.sample(1).iloc[0]
        await update.message.reply_text(self.format_chengyu(row), parse_mode="Markdown")

    async def daily(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /dia [n]: Muestra el chengyu correspondiente al día n.
        """
        if self.df.empty:
            await update.message.reply_text("Servicio no disponible.")
            return
        try:
            idx = int(context.args[0]) - 1
            row = self.df.iloc[idx]
            await update.message.reply_text(self.format_chengyu(row), parse_mode="Markdown")
        except:
            await update.message.reply_text("Uso: /dia [1-50]")

    async def categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /categorias: Despliega botones con cada categoría disponible.
        """
        if not self.categorias:
            await update.message.reply_text("No hay categorías.")
            return
        buttons = [
            [InlineKeyboardButton(cat, callback_data=f"cat_{i}")]
            for i, cat in enumerate(self.categorias)
        ]
        await update.message.reply_text(
            "Seleccione una categoría:", 
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def category_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Manejador de selección de categoría por botón.
        """
        idx = int(update.callback_query.data.split("_")[1])
        cat = self.categorias[idx]
        df_cat = self.df[self.df["Categoria"] == cat]
        row = df_cat.sample(1).iloc[0]
        await update.callback_query.edit_message_text(
            self.format_chengyu(row), parse_mode="Markdown"
        )

    async def hsk_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /hsk [nivel]: Lista todos los chengyus del nivel solicitado.
        Maneja formatos "HSK6" o "HSK 6" sin etiquetas extras.
        """
        if self.df.empty:
            await update.message.reply_text("Servicio no disponible.")
            return
        if not context.args:
            await update.message.reply_text("Uso: /hsk HSK6 (o HSK 6)", parse_mode="Markdown")
            return

        # Normalizar entrada sin espacios
        lvl_in = context.args[0].upper().replace(" ", "")
        valid = ["HSK6", "HSK7", "HSK8", "HSK9"]
        if lvl_in not in valid:
            await update.message.reply_text("Niveles válidos: HSK6–HSK9", parse_mode="Markdown")
            return

        # Filtrar DataFrame normalizado
        col = "Nivel de Dificultad"
        ser = (
            self.df[col]
            .astype(str)
            .str.replace(" ", "")
            .str.upper()
        )
        df_lvl = self.df[ser == lvl_in]
        if df_lvl.empty:
            await update.message.reply_text(f"No hay chengyus de nivel {lvl_in}.", parse_mode="Markdown")
            return

        # Construir lista completa
        lines = [f"🎓 *Nivel {lvl_in}* 🏮"]
        for _, r in df_lvl.iterrows():
            c, p = r.get("Chengyu 成语"), r.get("Pinyin")
            lines.append(f"• {c} ({p})")
        lines.append(f"\nTotal: {len(df_lvl)}")
        msg = "\n".join(lines)

        # Dividir mensaje si excede límite de Telegram
        for chunk in [msg[i : i + 4000] for i in range(0, len(msg), 4000)]:
            await update.message.reply_text(chunk, parse_mode="Markdown")

    async def quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /quiz: Presenta un chengyu y opciones de refrán venezolano.
        """
        if len(self.df) < 4:
            await update.message.reply_text("Quiz no disponible.")
            return
        corr = self.df.sample(1).iloc[0]
        wrongs = self.df[self.df.index != corr.name].sample(3)
        opts = [corr] + wrongs.to_dict("records")
        random.shuffle(opts)

        kb = [
            [
                InlineKeyboardButton(
                    self.get_column_value(o, ["Equivalente en Venezolano"])[:30],
                    callback_data=f"ans_{i}_{opts.index(corr)}_{corr.name}"
                )
            ]
            for i, o in enumerate(opts)
        ]
        await update.message.reply_text(
            f"❓ *Quiz:* ¿Cuál es el equivalente venezolano de *{corr['Chengyu 成语']}*?",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown",
        )

    async def answer_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Manejador de respuestas del quiz con retroalimentación.
        """
        query = update.callback_query
        await query.answer()
        _, sel, corr, idx = query.data.split("_")
        row = self.df.loc[int(idx)]
        text = ("✅ ¡Correcto!" if sel == corr else "❌ Incorrecto!") + "\n\n"
        text += self.format_chengyu(row)
        await query.edit_message_text(text, parse_mode="Markdown")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /ayuda: Lista los comandos disponibles.
        """
        msg = (
            "📖 *Ayuda - Bot de Chengyus*\n"
            "/start – Inicio\n"
            "/chengyu – Aleatorio\n"
            "/dia [1-50] – Chengyu por día\n"
            "/categorias – Temas\n"
            "/hsk [HSK6–9] – Listar todos por nivel\n"
            "/quiz – Prueba interactiva\n"
            "/ayuda – Este mensaje"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    def get_column_value(self, row, cols):
        """
        Obtiene el primer valor no nulo para las columnas indicadas.
        """
        for c in cols:
            if c in row and pd.notna(row[c]):
                return str(row[c])
        return "N/A"

def main():
    """Configura y arranca el bot."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN no configurado")
        return

    app = Application.builder().token(token).build()
    bot = ChengyuBot()

    # Registro de comandos
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("chengyu", bot.chengyu))
    app.add_handler(CommandHandler("dia", bot.daily))
    app.add_handler(CommandHandler("categorias", bot.categories))
    app.add_handler(CommandHandler("hsk", bot.hsk_filter))
    app.add_handler(CommandHandler("quiz", bot.quiz))
    app.add_handler(CommandHandler("ayuda", bot.help_command))

    # Handlers de botones
    app.add_handler(CallbackQueryHandler(bot.category_handler, pattern=r"^cat_"))
    app.add_handler(CallbackQueryHandler(bot.answer_handler, pattern=r"^ans_"))

    logger.info("Bot iniciado correctamente")
    app.run_polling()

if __name__ == "__main__":
    main()
