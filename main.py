import requests
from bs4 import BeautifulSoup
import re
import time
import random
import smtplib
from email.message import EmailMessage
import os
import getpass
from datetime import datetime

os.system("cls" if os.name == "nt" else "clear")

def inputları_al():
    global takip_url,gonderici_mail,mail_sifresi,alici_mail,sıklık_derecesi
    takip_url = input("Takip edilecek ürünün Trendyol URL'sini girin : ").strip()
    gonderici_mail = input("Mail bildirimi için Gönderici Mail girin : ").strip()
    mail_sifresi = getpass.getpass("Gönderici Mail'in şifresini girin : ")
    alici_mail = input("Bildirim alıcak Mail`i girin : ").strip()
    print("\n Kontrol sıklığı seçin : ")
    print("1- Seyrek (10-12dk)\n2- Normal (5-7dk)\n3- Sık (3-4dk)\n4- Çok Sık (30sn-1dk)\n")
    print("Not : Kısa beklemelerde bot olarak algılanma riski fazladır")
    print("Not : Extra Anti-Bot bekleme süresi vardır.(2sn-34sn)\n")
    try:
        sıklık_derecesi = int(input("Seçeneğin Numarasını Girin : "))
    except ValueError:
        sıklık_derecesi = 0

    if sıklık_derecesi not in [1,2,3,4]:
        print("Yanlış Seçenek Seçtiniz. Otomatik olarak `2- Normal` ayarlandı.")
        sıklık_derecesi = 2

inputları_al()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def log_kaydet(mesaj):
    zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("gecmis.txt", "a", encoding="utf-8") as dosya:
        dosya.write(f"[{zaman}] {mesaj}\n")

def mail_gonder(baslik, icerik):
    try:
        msg = EmailMessage()
        msg.set_content(icerik)
        msg['Subject'] = baslik
        msg['From'] = gonderici_mail
        msg['To'] = alici_mail

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gonderici_mail, mail_sifresi)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Mail gönderilemedi: {e}")
        log_kaydet(f"Mail Hatası: {e}")

def fiyat_metnini_sayiya_cevir(fiyat_metni):
    if not fiyat_metni:
        return None
    temiz_metin = re.sub(r"[^\d,\.]", "", fiyat_metni)
    temiz_metin = temiz_metin.replace(".", "").replace(",", ".")
    try:
        return float(temiz_metin)
    except ValueError:
        return None

def canli_fiyat_cek():
    try:
        response = requests.get(takip_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, f"Siteye erişilemiyor (Status: {response.status_code})"

        soup = BeautifulSoup(response.content, "html.parser")
        
        fiyat_elementi = (
            soup.find(class_="new-price") or 
            soup.find(class_="discounted") or 
            soup.find(class_="prc-dsc")
        )
        
        if not fiyat_elementi:
            for div in soup.find_all(["span", "div"]):
                if "TL" in div.text and len(div.text.strip()) < 15:
                    fiyat_elementi = div
                    break

        if fiyat_elementi:
            fiyat_metni = fiyat_elementi.text.strip()
            sayisal = fiyat_metnini_sayiya_cevir(fiyat_metni)
            if sayisal:
                return sayisal, None

        return None, "Fiyat etiketi veya formatı çözülemedi."

    except Exception as e:
        return None, f"Bağlantı hatası: {e}"

son_fiyat = None
hata_sayaci = 0

baslangic_msg = "Canlı Takip Başlatıldı. Arka planda çalışıyor..."
print(baslangic_msg)
log_kaydet(baslangic_msg)

while True:
    fiyat, hata = canli_fiyat_cek()
    zaman_damgasi = time.strftime("%H:%M:%S")

    if hata:
        hata_sayaci += 1
        log_msg = f"HATA ({hata_sayaci}/3): {hata}"
        print(f"[{zaman_damgasi}] {log_msg}")
        log_kaydet(log_msg)
        
        if hata_sayaci == 3:
            mail_gonder("SİSTEM UYARISI", "Trendyol yapısı değişti veya erişim engellendi. Kodun güncellenmesi gerekebilir!")
    else:
        hata_sayaci = 0
        log_msg = f"Kontrol Edildi. Anlık Fiyat: {fiyat} TL"
        print(f"[{zaman_damgasi}] {log_msg}")
        log_kaydet(log_msg)

        if son_fiyat is None:
            son_fiyat = fiyat
            log_kaydet(f"Başlangıç fiyatı kaydedildi: {son_fiyat} TL")
        else:
            if fiyat < son_fiyat:
                fark = son_fiyat - fiyat
                msg = f"Fiyat {son_fiyat} TL -> {fiyat} TL seviyesine düştü!\nKazanç: {fark:.2f} TL"
                print(f"İNDİRİM: {msg}")
                mail_gonder("İNDİRİM YAKALANDI!", msg)
                log_kaydet(f"İndirim Bildirimi Gönderildi: {msg}")
                son_fiyat = fiyat
            elif fiyat > son_fiyat:
                log_kaydet(f"Fiyat yükseldi: {son_fiyat} -> {fiyat} TL")
                mail_gonder("Fiyat Yükseldi", f"Fiyat {son_fiyat} TL -> {fiyat} TL seviyesine yükseldi.")
                son_fiyat = fiyat

    if sıklık_derecesi == 1:
        cooldown = random.randint(600,720)
    elif sıklık_derecesi == 2:
        cooldown = random.randint(300,420)
    elif sıklık_derecesi == 3:
        cooldown = random.randint(180,240)
    elif sıklık_derecesi == 4:
        cooldown = random.randint(30,60)
    print(f"Bir sonraki kontrol için {cooldown}sn ({cooldown/60:.2f} dk) bekleniyor...")
    time.sleep(cooldown)
    extra_cooldown = random.randint(2,34)
    if extra_cooldown > 0:
        print(f"> Anti Bot bekleme süresi: {extra_cooldown}sn...")
        time.sleep(extra_cooldown)