
# Nöbetçi Eczane Home Assistant Entegrasyonu

<p align="left">
  <img src="https://raw.githubusercontent.com/home-assistant/brands/58d28a95484f3f9208ed1c4968886ac6d2c435bd/custom_integrations/nobetci_eczane/logo%402x.png" alt="Blynk Logo" width="300"/>
</p>

Türkiye genelinde il ve ilçe bazlı nöbetçi eczaneleri Home Assistant arayüzünüzde gösteren özel bir entegrasyondur. Eczane adı, adresi ve iletişim bilgileri gibi verilere kolayca erişebilirsiniz.

## Özellikler

- Şehir ve ilçe seçimine göre güncel nöbetçi eczane bilgisi
- Eczanelerin adı, adresi ve telefon numarası
- Home Assistant sensör desteği
- Otomatik günlük veri güncelleme

## Ön Koşul

Bu entegrasyonu kullanabilmek için [https://www.nosyapi.com/api/nobetci-eczane](https://www.nosyapi.com/api/nobetci-eczane) adresinden ücretsiz veya ücretli bir API anahtarı (apikey) almalısınız.  
API anahtarınızı aldıktan sonra yapılandırma sırasında girmeniz gerekmektedir.

## Kurulum

[![Home Assistant ile HACS üzerinden bu entegrasyonu ekle](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Korkuttum&repository=nobetci_eczane&category=integration)

### Yöntem 1: HACS ile Kolay Kurulum (Önerilir)

1. [HACS](https://hacs.xyz/) eklentisinin Home Assistant’ınızda kurulu olduğundan emin olun.
2. Sol menüden **HACS**'a girin.
3. Sağ üstteki üç noktaya tıklayın, **Özel Depolar** seçeneğini seçin.
4. Bu depo adresini ekleyin:  
   `https://github.com/Korkuttum/nobetci_eczane`  
   ve kategori olarak **Integration** seçin.
5. **Ekle** (ADD) butonuna basın.
6. “Nöbetçi Eczane” entegrasyonunu bulun, yükleyin ve Home Assistant’ı yeniden başlatın.

### Yöntem 2: Manuel Kurulum

Tüm dosyaları Home Assistant ayar klasörünüzde  
`custom_components/nobetci_eczane`  
klasörüne yükleyin. Kurulumdan sonra Home Assistant’ı yeniden başlatın.

## Yapılandırma

Kurulum sonrası Home Assistant arayüzünde:

1. **Ayarlar > Cihazlar & Servisler > Entegrasyon ekle** adımlarını izleyin.
2. “Nöbetçi Eczane” entegrasyonunu aratın ve ekleyin.
3. API anahtarınızı (apikey) girin.
4. İl ve ilçe bilgisini girin (TR haritasındaki isimlerle uyumlu şekilde).
5. Kaydedin. Girdiğiniz bölgeye ait güncel nöbetçi eczane bilgileri sensörlerde görünecektir.

## Dosya Yapısı

```
custom_components/
  └── nobetci_eczane/
      ├── __init__.py
      ├── config_flow.py
      ├── const.py
      ├── il-ilce.json
      ├── manifest.json
      ├── sensor.py
      └── translations/
          └── tr.json
```

## Katkı ve Geri Bildirim

Hata bildirimi, öneri ve katkılarınız için GitHub üzerinde issue açabilir veya pull request gönderebilirsiniz.

## Lisans

Bu proje MIT lisansı ile lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasını inceleyiniz.

---

**Uyarı:** Bu entegrasyon tamamen topluluk projesidir ve herhangi bir kurum/kuruluş ile resmi bir bağı yoktur. Kamuya açık verileri kullanır ve “olduğu gibi” sunulur.
