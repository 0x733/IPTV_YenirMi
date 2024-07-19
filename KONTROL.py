# ! Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli    import konsol
from Kekik        import satir_ekle
from cloudscraper import CloudScraper
from re           import compile, MULTILINE
from os           import remove

def iptv_parser(dosya_yolu:str) -> list[dict]:
    with open(dosya_yolu, "r", encoding="utf-8") as dosya:
        satirlar = dosya.readlines()

    extinf_re     = compile(r'#EXTINF:-1 tvg-name="([^"]+)"')
    url_re        = compile(r'^(https?://[^\s]+)', MULTILINE)
    user_agent_re = compile(r'#EXTVLCOPT:http-user-agent=(.*)')
    referer_re    = compile(r'#EXTVLCOPT:http-referrer=(.*)')

    kanallar     = []
    mevcut_kanal = {}

    for satir in satirlar:
        if satir.startswith("#EXTINF"):
            if match := extinf_re.search(satir):
                if mevcut_kanal:
                    kanallar.append(mevcut_kanal)

                mevcut_kanal = {"ad": match[1], "user-agent": None, "referer": None}

        elif satir.startswith("#EXTVLCOPT:http-user-agent"):
            if match := user_agent_re.search(satir):
                mevcut_kanal["user-agent"] = match[1]

        elif satir.startswith("#EXTVLCOPT:http-referrer"):
            if match := referer_re.search(satir):
                mevcut_kanal["referer"] = match[1]

        elif satir.startswith("http"):
            if match := url_re.search(satir):
                mevcut_kanal["yayin"] = match[0]
                kanallar.append(mevcut_kanal)
                mevcut_kanal = {}

    if mevcut_kanal:
        kanallar.append(mevcut_kanal)

    return kanallar

kanallar     = iptv_parser("Kanallar/KekikAkademi.m3u")
hata_bulundu = False

satir_ekle("HATALAR.md", """

***

> # [![Yayın Kontrolü](https://github.com/keyiflerolsun/IPTV_YenirMi/actions/workflows/Kontrol.yml/badge.svg)](https://github.com/keyiflerolsun/IPTV_YenirMi/actions/workflows/Kontrol.yml)
> ### [Kanallar/KekikAkademi.m3u](https://github.com/keyiflerolsun/IPTV_YenirMi/blob/main/Kanallar/KekikAkademi.m3u)

***

| AD | HATA | YAYIN |
|----|------|-------|

""".strip())

for kanal in kanallar:
    print("\n")
    konsol.log(f"[~] Kontrol Ediliyor : {kanal['ad']}")

    oturum = CloudScraper()

    if kanal["user-agent"]:
        oturum.headers.update({"User-Agent": kanal["user-agent"]})

    if kanal["referer"]:
        oturum.headers.update({"Referer": kanal["referer"]})

    try:
        istek = oturum.get(kanal['yayin'], timeout=5)
    except Exception as hata:
        konsol.log(f"[!] {type(hata).__name__} : {hata}")
        satir_ekle("HATALAR.md", f"|**{kanal['ad']}**|`{type(hata).__name__}`|*{kanal['yayin']}*|")
        hata_bulundu = True
        continue

    if istek.status_code == 200:
        konsol.log(f"[+] Kontrol Edildi   : {kanal['ad']}")
    else:
        konsol.log(f"[!] {istek.status_code} » {kanal['yayin']} » {kanal['ad']}")
        satir_ekle("HATALAR.md", f"|**{kanal['ad']}**|`{istek.status_code}`|*{kanal['yayin']}*|")
        hata_bulundu = True


if not hata_bulundu:
    remove("HATALAR.md")
    print("\n")
    konsol.log("[+] Hata Bulunamadı.")