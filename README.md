# Brama przesuwna BFT — Home Assistant + ESPHome

Projekt sterowania bramą przesuwną BFT przez Home Assistant i sterownik ESP32.

## Wymagany sprzęt i oprogramowanie

### Sprzęt

- **Płytka sterująca: ESP32 Relay X4 (AC/DC)** — wymagana płytka używana w tym projekcie.
- **Napęd bramy: BFT DEIMOS ULTRA BT B 600** — konfiguracja referencyjna projektu.
- Połączenia sygnałów napędu z płytką muszą być wykonane zgodnie z osobną instrukcją okablowania, którą przygotujemy dla projektu. Nie podłączaj GPIO ESP32 bezpośrednio do obwodów napędu.

Nie zakładaj zgodności z innymi płytkami ani napędami bez sprawdzenia pinów, poziomów sygnałów i sposobu działania wejść.

### Home Assistant i ESPHome

Potrzebujesz działającego **Home Assistant** oraz dodatku **ESPHome** (ESPHome Device Builder) zainstalowanego w Home Assistant. Dodatek ESPHome ułatwia przygotowanie, kompilację i wgranie firmware na płytkę ESP32.

Nasza integracja **Brama przesuwna BFT** jest osobnym elementem. Instalowana przez HACS będzie udostępniać konfigurator projektu oraz kartę bramy do dashboardu Home Assistant. Nie zastępuje dodatku ESPHome.

## Instalacja integracji przez HACS — ręczne repozytorium

Repozytorium nie jest zgłaszane do oficjalnego katalogu HACS. Dodaj je ręcznie:

1. Otwórz **HACS → ⋮ → Custom repositories**.
2. W polu repozytorium wpisz `https://github.com/MarLip1981/Brama-przesuwna-BFT`.
3. Jako kategorię wybierz **Integration** i zatwierdź.
4. Znajdź „Brama przesuwna BFT” w HACS i zainstaluj.
5. Uruchom ponownie Home Assistant.
6. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację** i wybierz „Brama przesuwna BFT”.

## Firmware ESPHome — pobranie i wgranie ręczne

Firmware pozostaje plikiem projektu w tym repozytorium. Użytkownik pobiera go i wgrywa samodzielnie za pomocą dodatku ESPHome. Integracja HACS nie pobiera ani nie wgrywa firmware na ESP32.

1. Pobierz plik [firmware ESPHome](esphome/brama-wjazdowa.yaml) z repozytorium.
2. Przygotuj wymagane sekrety w `secrets.yaml` ESPHome:
   - `wifi_ssid`
   - `wifi_password`
   - `wifi_backup_ssid`
   - `wifi_backup_pass`
   - `brama_wjazdowa__encryption_key`
3. Otwórz dodatek ESPHome i dodaj/przygotuj konfigurację urządzenia na podstawie pobranego pliku.
4. Sprawdź konfigurację i wgraj firmware na ESP32 zgodnie z instrukcją ESPHome.

Dokładne kroki importu pliku do dodatku ESPHome dopracujemy w instrukcji instalacyjnej projektu.

## Karta dashboardu

Plik [karty Lovelace](lovelace/brama-wjazdowa.yaml) pozostaje dostępny w repozytorium. Docelowo karta będzie dostarczana i udostępniana w dashboardzie przez naszą integrację. Wymaga również niestandardowej karty `custom:button-card`. Konfigurator i automatyczne udostępnianie karty są jeszcze w trakcie przygotowania — obecna wersja repozytorium nie powinna być traktowana jako gotowy instalator.

## Ważne informacje o działaniu i bezpieczeństwie

1. Pozycja bramy jest szacowana na podstawie czasu ruchu; procent nie pochodzi z enkodera i może odbiegać od rzeczywistego położenia.
2. Sygnały SCA i fotokomórki wymagają prawidłowego dopasowania elektrycznego oraz bezpiecznej izolacji.
3. Projekt nie zastępuje fabrycznych zabezpieczeń napędu ani fotokomórki.
4. Pierwsze testy wykonuj przy zapewnionym dostępie do zatrzymania napędu, bez osób i przedmiotów w świetle bramy.
5. Przed podłączeniem przewodów sprawdź instrukcję konkretnego napędu i płytki. Schemat połączeń elektrycznych zostanie opisany osobno.

## Status projektu

Projekt jest rozwijany etapami. Obecna integracja HACS jest podstawą pod docelowy konfigurator i kartę dashboardu. Firmware jest instalowany ręcznie przez użytkownika za pomocą ESPHome.
