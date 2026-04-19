import psutil
import time
import json
import ssl
import paho.mqtt.client as mqtt
from datetime import datetime, timezone

# ==========================================
# AWS IOT CORE AYARLARI (BURAYI KENDİNE GÖRE DOLDUR)
# ==========================================
AWS_ENDPOINT = "a2lywxj80mo8ua-ats.iot.eu-central-1.amazonaws.com" # Örn: a1b2c...-ats.iot.eu-central-1.amazonaws.com
CLIENT_ID = "mydev"
TOPIC = "sensor/metrikler" # Verilerin gönderileceği MQTT kanalı (topic)

# Sertifika dosya isimleri (Klasöründeki isimlerle BİREBİR aynı olmalı!)
ROOT_CA = "AmazonRootCA1.pem"
CERT_FILE = "d67ea99ff0e73dc598332c9f1c65bf4b0e7de1411a63a3c23c71d5d6462e22ef-certificate.pem.crt" # Kendi dosya adını kopyala yapıştır
KEY_FILE = "d67ea99ff0e73dc598332c9f1c65bf4b0e7de1411a63a3c23c71d5d6462e22ef-private.pem.key"      # Kendi dosya adını kopyala yapıştır
# ==========================================

# Bağlantı başarılı olduğunda çalışacak fonksiyon
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ AWS IoT Core'a başarıyla bağlanıldı!")
    else:
        print(f"❌ Bağlantı hatası, Kod: {rc}")

def get_system_metrics():
    # CPU ve RAM verilerini topla (Önceki kodun aynısı)
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    ram_usage = memory_info.percent
    free_ram_mb = round(memory_info.available / (1024 * 1024), 2)

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device_id": CLIENT_ID,
        "metrics": {
            "cpu_percent": cpu_usage,
            "ram_percent": ram_usage,
            "free_ram_mb": free_ram_mb
        }
    }
    return payload

if __name__ == "__main__":
    # MQTT İstemcisini oluştur ve ayarla
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=CLIENT_ID)
    client.on_connect = on_connect

    # Güvenli bağlantı (TLS/SSL) için sertifikaları yükle
    client.tls_set(ca_certs=ROOT_CA,
                   certfile=CERT_FILE,
                   keyfile=KEY_FILE,
                   cert_reqs=ssl.CERT_REQUIRED,
                   tls_version=ssl.PROTOCOL_TLSv1_2)

    # AWS'ye bağlan
    print("AWS'ye bağlanılıyor...")
    client.connect(AWS_ENDPOINT, 8883, 60) # MQTT over TLS portu 8883'tür
    client.loop_start() # Arka planda ağı dinlemeye başla

    print(f"Veriler '{TOPIC}' kanalına gönderiliyor. (Çıkış için CTRL+C)")
    
    try:
        while True:
            data = get_system_metrics()
            json_data = json.dumps(data)
            
            # Veriyi buluta fırlat
            client.publish(TOPIC, json_data, qos=1)
            print(f"📡 Gönderildi: {json_data}")
            
            time.sleep(1) # Saniyede 1 kez gönder
            
    except KeyboardInterrupt:
        print("\nİzleme durduruldu, bağlantı kesiliyor...")
        client.loop_stop()
        client.disconnect()