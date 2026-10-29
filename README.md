# Brama przesuwna BFT — Home Assistant + ESPHome

Projekt sterowania bramą przesuwną przez ESP32 Relay X4 i Home Assistant.

## Instalacja integracji przez HACS (ręczne repozytorium)

Repozytorium **nie jest zgłaszane do oficjalnego katalogu HACS**. Dodaj je ręcznie:

1. Otwórz **HACS → ⋮ → Custom repositories**.
2. W polu repozytorium wpisz `https://github.com/MarLip1981/Brama-przesuwna-BFT`.
3. Jako kategorię wybierz **Integration** i zatwierdź.
4. Znajdź „Brama przesuwna BFT” w HACS i zainstaluj.
5. Uruchom ponownie Home Assistant.
6. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację** i wybierz „Brama przesuwna BFT”.

**Uwaga:** obecna integracja HACS jest szkieletem instalacyjnym. Nie konfiguruje jeszcze napędu ani nie wgrywa firmware. Właściwy konfigurator i instalator dodamy w następnym etapie.

## Pliki projektu

- [Firmware ESPHome](esphome/brama-wjazdowa.yaml) — wgrywany osobno na ESP32.
- [Karta Lovelace](lovelace/brama-wjazdowa.yaml) — dodawana osobno do pulpitu Home Assistant.
- [Integracja Home Assistant](custom_components/brama_przesuwna_bft/) — instalowana przez HACS.

## Testowana konfiguracja

- Napęd: **BFT DEIMOS ULTRA BT B 600**.
- Płytka: **ESP32 Relay X4 (AC/DC)**.
- Firmware: ESPHome.
- Karta Lovelace: `custom:button-card` (wymaga zainstalowanej karty Button Card).

Nie zakładaj zgodności z każdym napędem. Przed montażem sprawdź instrukcję konkretnego napędu i parametry elektryczne. Nie podłączaj GPIO ESP32 bezpośrednio do obwodów napędu.

## Wymagane sekrety ESPHome

W pliku `secrets.yaml` ESPHome ustaw:

- `wifi_ssid`
- `wifi_password`
- `wifi_backup_ssid`
- `wifi_backup_pass`
- `brama_wjazdowa__encryption_key`

## Ważne informacje o bezpieczeństwie

1. Sprawdź mapowanie pinów i logikę wejść na swojej płytce.
2. Pozycja bramy jest szacowana na podstawie czasu ruchu; procent nie pochodzi z enkodera i może odbiegać od rzeczywistego położenia.
3. Wejścia SCA i fotokomórki wymagają prawidłowego, bezpiecznego dopasowania sygnałów.
4. Projekt nie zastępuje fabrycznych zabezpieczeń napędu ani fotokomórki.
5. Pierwsze testy wykonuj przy zapewnionym dostępie do zatrzymania napędu, bez osób i przedmiotów w świetle bramy.

## Status

Projekt jest rozwijany etapami. Konfigurator i instalator automatyzujący przygotowanie ESPHome oraz karty Lovelace nie są jeszcze dostępne.
