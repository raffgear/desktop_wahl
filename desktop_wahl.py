import os
import json
import time
import re
import threading
import pyperclip
import keyboard
import customtkinter as ctk
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import tkinter.messagebox as msgbox
import tkinter as tk

SETTINGS_FILE = 'settings.json'
# phone_pattern = re.compile(r'(\+?\d[\d\s()-]{5,}\d)')
# phone_pattern = re.compile(r'(\+?\d[\d\s().-]{5,}\d)')
phone_pattern = re.compile(r'(\+?\d[\d\s()./\-]{5,}\d)')   #funktioniert


class DesktopDialerApp:
    def __init__(self):
        self.settings = {}
        self.listener_thread = None
        self.icon = None       
        self.load_settings()
        self.waiting_time = self.settings.get('waiting_time', 3000)

    def to_e164(self, number, default_country_code="49"):
        """
        Wandelt eine Rufnummer ins E.164-Format um.
        Entfernt alle Nicht-Ziffern, ersetzt führende 0 durch Landesvorwahl.
        """

        number = number.strip()
        
        print(f"Ursprüngliche Nummer: {number}")
        
       
        # Wenn Nummer mit + beginnt: alles außer + und Ziffern entfernen
        if number.startswith("+"):
            digits = "+" + re.sub(r'\D', '', number)
            return digits
        # Wenn Nummer mit 00 beginnt: ersetze 00 durch +
        elif number.startswith("00"):
            digits = "+" + re.sub(r'\D', '', number[2:])
            return digits
        # Wenn Nummer mit 0 beginnt: ersetze führende 0 durch +49 (oder anderes Land)
        elif number.startswith("0"):
            digits = re.sub(r'\D', '', number)
            return "+" + default_country_code + digits[1:]
        # Sonst: nur Ziffern, mit +
        else:
            digits = re.sub(r'\D', '', number)
            return "+" + digits
        


    def call_number(self, number):
        #nummer = re.sub(r'\D', '', number)
        tel_link = 'tel:' + self.to_e164(number)
        print(f"Rufe an: {self.to_e164(number)}")

        win = ctk.CTk()
        win.title("Anruf")
        win.resizable(False, False)
        win.attributes('-topmost', True)

        win.update_idletasks()
        width, height = 400, 120
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

        label = ctk.CTkLabel(win, text=f"Rufe an: {self.to_e164(number)}", font=("Calibri", 24))
        label.pack(pady=10)
        countdown_label = ctk.CTkLabel(win, text="", font=("Calibri", 18))
        countdown_label.pack(pady=5)
        btn = ctk.CTkButton(win, text="Abbrechen", command=lambda: (win.destroy(), print("Abgebrochen.")))
        btn.pack(pady=5)

        # Countdown-Logik
        seconds = max(1, self.waiting_time // 1000)
        def update_countdown(sec_left):
            if not win.winfo_exists():
                return
            if sec_left > 0:
                countdown_label.configure(text=f"Wählen in {sec_left} Sekunden...")
                win.after(1000, update_countdown, sec_left - 1)
            else:
                countdown_label.configure(text="Wähle jetzt...")
                win.after(300, do_call)  # kleiner Puffer für Anzeige

        def do_call():
            if win.winfo_exists():
                win.destroy()
                try:
                    os.startfile(tel_link)
                except Exception as e:
                    print("Fehler beim Öffnen des tel-Links:", e)

        update_countdown(seconds)
        win.mainloop()

    def process_clipboard(self):
        time.sleep(0.2)
        content = pyperclip.paste()
        match = phone_pattern.search(content)
        if match:
            self.call_number(match.group(1))
        else:
            print("Keine Telefonnummer gefunden.")

    def on_hotkey(self):
        keyboard.press_and_release('ctrl+c')
        self.process_clipboard()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {}

    def save_settings(self):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f)

    def ask_for_hotkey(self):
        ctk.set_appearance_mode("light")
        win = ctk.CTk()
        win.title("Einstellungen")
        # win.geometry("300x250")

        # Bildschirmgröße ermitteln
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()

        # Fenstergröße definieren
        window_width = 300
        window_height = 250

        # Position berechnen
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        # Fensterposition setzen
        win.geometry(f"{window_width}x{window_height}+{x}+{y}")











        label = ctk.CTkLabel(win, text="Neue Tastenkombination eingeben\n(z. B. strg+y):")
        
        label.pack(pady=10)

        entry = ctk.CTkEntry(win)
        entry.insert(0, self.settings.get('hotkey',""))
        entry.pack(pady=5)
        #entry.focus()
        label2 = ctk.CTkLabel(win, text="Pause vor dem Öffnen des tel-Links in ms\n(z.B. 2000):")
        label2.pack(pady=10)

        entry2 = ctk.CTkEntry(win)
        entry2.insert(0, str(self.waiting_time))
        entry2.pack(pady=5)

        def confirm():
            hotkey = entry.get().strip()
            timeout_str = entry2.get().strip()
            if hotkey:
                self.settings['hotkey'] = hotkey
            if timeout_str.isdigit():
                self.waiting_time = int(timeout_str)
                self.settings['waiting_time'] = self.waiting_time
            self.save_settings()
            win.destroy()

        ctk.CTkButton(win, text="Speichern", command=confirm).pack(pady=10)
        win.mainloop()

    def change_hotkey(self):
        try:
            keyboard.remove_hotkey(self.settings['hotkey'])
        except:
            pass
        self.ask_for_hotkey()
        keyboard.add_hotkey(self.settings['hotkey'], self.on_hotkey)
        print(f"Neuer Hotkey: {self.settings['hotkey']}")

    
    def create_image(self):
        size = 200
        image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)

        # Wählscheibe-Kreis
        center = (size // 2, size // 2)
        radius = 80
        draw.ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius], fill='red', outline='white')

        # Fingerloch
        finger_hole_radius = 10
        draw.ellipse([center[0] - finger_hole_radius, center[1] - finger_hole_radius, center[0] + finger_hole_radius, center[1] + finger_hole_radius], fill='black')

        # Zahlen auf der Wählscheibe
        numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        for i, number in enumerate(numbers):
            angle = 2 * 3.14159265359 * i / 10
            x = center[0] + int((radius - 20) * 3.14159265359 * 2 / 3) * 3.14159265359 * 2 / 3
            y = center[1] + int((radius - 20) * 3.14159265359 * 2 / 3) * 3.14159265359 * 2 / 3
            draw.text((x, y), number, fill='black')

        return image

    def on_exit(self, icon, item):
        icon.stop()
        os._exit(0)

    def hilfe(self, icon, item):
        msgbox.showinfo("Hilfe", "Drücke die eingestellte Tastenkombination, um die markierte Telefonnummer zu wählen.\n\n"
                                      "Die Wartezeit vor dem Wählen und die Tastenkombination können in den Einstellungen angepasst werden.")

    def run(self):
        # Hotkey prüfen und ggf. neu abfragen
        while True:
            hotkey = self.settings.get('hotkey')
            try:
                if not hotkey:
                    raise ValueError("Kein Hotkey gesetzt.")
                keyboard.add_hotkey(hotkey, self.on_hotkey)
                break
            except Exception as e:
                print(f"Ungültiger Hotkey: {hotkey}. Bitte neu eingeben.")
                self.ask_for_hotkey()
                self.save_settings()

        self.listener_thread = threading.Thread(target=keyboard.wait, daemon=True)
        self.listener_thread.start()

        # Tray-Menü
        self.icon = Icon("Telefonwahl")
        self.icon.icon = self.create_image()
        self.icon.menu = Menu(
            MenuItem(f"Hilfe", self.hilfe),
            MenuItem(f"Einstellungen", lambda icon, item: self.change_hotkey()),
            MenuItem('Beenden', self.on_exit)
        )
        self.icon.run()

if __name__ == '__main__':
    app = DesktopDialerApp()
    app.run()