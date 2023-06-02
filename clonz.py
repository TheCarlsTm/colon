import telebot
from telebot import types
import re
import time
import os
import threading

TOKEN = '6095765483:AAGn-ikZSvWRqV3Kuz_bCfDwTjaHF38Mpto'  # Reemplaza con tu token
bot = telebot.TeleBot(TOKEN)

registered_channels = ['-1001643794396','-1001384173139','-1001339656665' ,'-1001735089981', '-1001708014764', '-1001550114413', '-1001293467532','-1001729255456','-1001323217412', '-1001654756572', '-1001693592291', '-1001448130319', '-1001202486065', '-1001805608452', '-1001334284915', '-1001422245653', '-1001771407582', '-1001451765721']  # Coloca aquí los IDs de los canales registrados
post_buttons = []  # Lista para almacenar los botones del post
custom_post_caption = None  # Variable para almacenar la descripción personalizada del comando /post
custom_post_photo = None  # Variable para almacenar la imagen personalizada del comando /post
custom_post_video = None  # Variable para almacenar el video personalizado del comando /post
sent_messages = {}  # Diccionario para almacenar los mensajes enviados a cada canal

# Verifica que el mensaje provenga del usuario autorizado
def is_authorized_user(message):
    authorized_user_id = '1133837923'  # Reemplaza con el ID del usuario autorizado
    return str(message.from_user.id) == authorized_user_id

# Comando /start
@bot.message_handler(commands=['start'])
def start(message):
    if is_authorized_user(message):
        welcome_message = '''
¡Bienvenido al <b>Bot de Publicación</b>!

Este bot te permite enviar mensajes personalizados a canales registrados. Puedes utilizar los siguientes comandos:
        
- /post: Envía un mensaje personalizado a todos los canales registrados.
- /setbutton {texto - enlace}: Agrega un botón al mensaje personalizado.
- /send : con este comando podras enviar el post personalizado pre configurado que hiciste al principio. ( Si le agregas un numero de lado se borrara el post automaticamente al pasar el tiempo )
-- Ejemplo: /Send 60s (1 minuto)

¡Comienza utilizando /post para crear un mensaje personalizado!

 <b>Powered by Bot incognito</b>
'''
        bot.send_message(chat_id=message.chat.id, text=welcome_message, parse_mode='HTML')
    else:
        bot.reply_to(message, "⛔️ No estás autorizado para usar este bot.")

# Comando /post
@bot.message_handler(commands=['post'])
def post_to_channels(message):
    if is_authorized_user(message):
        if len(registered_channels) == 0:
            bot.reply_to(message, "🤷‍♂️ No hay canales registrados.")
            return

        global custom_post_caption, custom_post_photo, custom_post_video
        custom_post_caption = None
        custom_post_photo = None
        custom_post_video = None

        msg = bot.reply_to(message, "✏️ Envía la descripción del post (puedes utilizar formato HTML)")
        bot.register_next_step_handler(msg, process_post_caption)
    else:
        bot.reply_to(message, "⛔️ No estás autorizado para usar este comando.")

# Función para procesar la descripción del post
def process_post_caption(message):
    global custom_post_caption
    custom_post_caption = message.text

    msg = bot.reply_to(message, "📸 Envía una imagen o video adjunto (opcional). Si no deseas adjuntar una imagen o video, simplemente envía el mensaje sin adjuntos.")
    bot.register_next_step_handler(msg, process_post_media)

# Función para procesar la imagen o video del post
def process_post_media(message):
    global custom_post_caption, custom_post_photo, custom_post_video

    if message.photo:
        custom_post_photo = message.photo[-1].file_id
    elif message.video:
        custom_post_video = message.video.file_id

    bot.reply_to(message, "✅ El post ha sido configurado correctamente.")

# Comando /setbutton
@bot.message_handler(commands=['setbutton'])
def set_post_button(message):
    if is_authorized_user(message):
        buttons_text = message.text.replace('/setbutton', '').strip()

        if not buttons_text:
            bot.reply_to(message, "Por favor, proporciona los textos de los botones.")
            return

        buttons = buttons_text.split('\n')
        post_buttons.clear()

        for button in buttons:
            button_parts = button.split('-')
            if len(button_parts) >= 2:
                button_text = button_parts[0].strip()
                button_link = '-'.join(button_parts[1:]).strip()
                post_buttons.append({'text': button_text, 'link': button_link})

        reply_text = "Los botones han sido establecidos:\n"
        for button in post_buttons:
            reply_text += f"\n- Texto: {button['text']}, Enlace: {button['link']}"

        bot.reply_to(message, reply_text)
    else:
        bot.reply_to(message, "⛔️ No estás autorizado para usar este comando.")

# Comando /send
@bot.message_handler(commands=['send'])
def send_custom_post(message):
    if is_authorized_user(message):
        if custom_post_caption is None:
            bot.reply_to(message, "No hay un mensaje personalizado. Utiliza el comando /post para crear uno.")
            return

        send_post_to_channels(message)
    else:
        bot.reply_to(message, "⛔️ No estás autorizado para usar este comando.")

# Función para enviar el mensaje personalizado a los canales registrados
def send_post_to_channels(message):
    global custom_post_caption, custom_post_photo, custom_post_video

    threads = []
    for channel_id in registered_channels:
        thread = threading.Thread(target=send_post_to_channel, args=(channel_id,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    timeout = extract_timeout_from_command(message.text)
    if timeout is not None:
        delete_post_from_channels(timeout)

def send_post_to_channel(channel_id):
    global custom_post_caption, custom_post_photo, custom_post_video

    if custom_post_photo is not None:
        sent_message = bot.send_photo(chat_id=channel_id, photo=custom_post_photo, caption=custom_post_caption, parse_mode='HTML', reply_markup=create_inline_keyboard())
    elif custom_post_video is not None:
        sent_message = bot.send_video(chat_id=channel_id, video=custom_post_video, caption=custom_post_caption, parse_mode='HTML', reply_markup=create_inline_keyboard())
    else:
        sent_message = bot.send_message(chat_id=channel_id, text=custom_post_caption, parse_mode='HTML', reply_markup=create_inline_keyboard())

    if sent_message and sent_message.message_id:
        sent_messages[channel_id] = sent_message.message_id

def delete_post_from_channels(timeout):
    global custom_post_photo

    time.sleep(timeout)
    for channel_id, message_id in sent_messages.items():
        bot.delete_message(chat_id=channel_id, message_id=message_id)

def extract_timeout_from_command(command):
    time_regex = re.compile(r"/send\s+(\d+)s", re.IGNORECASE)
    match = time_regex.search(command)
    if match:
        timeout = int(match.group(1))
        return timeout
    return None

def create_inline_keyboard():
    inline_keyboard = types.InlineKeyboardMarkup()

    for button in post_buttons:
        if button['link'].startswith("http://") or button['link'].startswith("https://"):
            inline_keyboard.add(types.InlineKeyboardButton(text=button['text'], url=button['link']))
        else:
            inline_keyboard.add(types.InlineKeyboardButton(text=button['text'], callback_data=button['link']))

    return inline_keyboard

bot.polling()