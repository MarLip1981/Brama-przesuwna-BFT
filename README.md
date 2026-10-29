# Brama przesuwna BFT — Home Assistant + ESPHome

Sterowanie bramą przesuwną przez ESP32 Relay X4 i Home Assistant.

## Status projektu

To pierwsza wersja robocza projektu oparta na działającej instalacji użytkownika. Testowana konfiguracja:
- napęd: **BFT DEIMOS ULTRA BT B 600**;
- płytka: **ESP32 Relay X4 (AC/DC)**;
- firmware: ESPHome;
- interfejs: karta Lovelace oparta na `custom:button-card`.

Nie zakładaj zgodności z każdym napędem. Sterownik bramy musi obsługiwać wejście impulsowe/przyciskowe. Sposób podłączenia zależy od konkretnego napędu; przed montażem sprawdź jego instrukcję i parametry elektryczne. Nie podłączaj GPIO ESP32 bezpośrednio do obwodów napędu.

## Pliki

- [Firmware ESPHome](esphome/brama-wjazdowa.yaml)
- [Karta Lovelace](lovelace/brama-wjazdowa.yaml)

Konfigurator i instalator zostaną dodane w kolejnych etapach.

## Ważne przed użyciem

1. Uzupełnij wymagane sekrety w pliku `secrets.yaml` ESPHome:
   - `wifi_ssid`
   - `wifi_password`
   - `wifi_backup_ssid`
   - `wifi_backup_pass`
   - `api_encryption_key`
2. Sprawdź mapowanie pinów i logikę wejść na swojej płytce.
3. Firmware szacuje pozycję na podstawie czasu ruchu. Procent nie pochodzi z enkodera i może odbiegać od rzeczywistego położenia.
4. Wejścia SCA i fotokomórki wymagają prawidłowego, bezpiecznego dopasowania sygnałów. Projekt nie zastępuje zabezpieczeń napędu.
5. Najpierw testuj przy zapewnionym bezpiecznym dostępie do zatrzymania napędu i bez osób ani przedmiotów w świetle bramy.

## Encje Home Assistant

Karta w tej wersji korzysta z encji tworzonych przez konfigurację ESPHome. Jeśli zmienisz nazwę urządzenia lub encji, dostosuj identyfikatory w YAML karty.

## Licencja

Licencja projektu nie została jeszcze określona.
