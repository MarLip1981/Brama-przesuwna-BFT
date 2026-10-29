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

Integracja zawiera własną kartę Lovelace i próbuje automatycznie dodać jej zasób JavaScript do zasobów Home Assistant po skonfigurowaniu integracji. Następnie w edytorze dashboardu dodaj kartę **Brama przesuwna BFT** z wyboru kart. Karta nie wymaga `custom:button-card`.

Karta ma domyślne identyfikatory encji zgodne z firmware tego projektu. Jeżeli zmienisz nazwę urządzenia lub identyfikatory encji w ESPHome, można je poprawić w edytorze karty. Integracja nie wstawia automatycznie karty do istniejącego dashboardu — nie zmienia samodzielnie układu pulpitu użytkownika.

Dotychczasowy plik [karty Lovelace w YAML](lovelace/brama-wjazdowa.yaml) również pozostaje dostępny w repozytorium, ale ta starsza wersja wymaga niestandardowej karty `custom:button-card`.

## Połączenia elektryczne — ustalenia dla instalacji referencyjnej

Poniższe połączenia opisują instalację z napędem BFT DEIMOS ULTRA BT B 600 i płytką ESP32 Relay X4 (AC/DC). Przed wykonaniem prac odłącz zasilanie napędu i zweryfikuj oznaczenia na swojej wersji płyty.

### Sterowanie wejściami napędu

| Element ESP32 Relay X4 | Zacisk napędu BFT | Funkcja |
|---|---:|---|
| Przekaźnik 1 — COM | 60 | Wspólny styk sterowania przyciskiem |
| Przekaźnik 1 — NO | 61 | Impuls sterujący bramą |
| Przekaźnik 2 — COM | 60 | Wspólny styk drugiego wejścia |
| Przekaźnik 2 — NO | 62 | Impuls sterujący funkcją furtki / częściowego otwarcia |
| Przekaźnik 1 i 2 — NC | — | Nie podłączać |

Przekaźniki pracują jako styki bezpotencjałowe, równolegle do odpowiednich wejść sterujących. Nie doprowadzaj do zacisków 60–62 napięcia zasilającego płytkę ESP32.

### Odczyt stanu bramy — AUX/SCA

| Płytka ESP32 Relay X4 | Zacisk napędu BFT |
|---|---:|
| GND | 26 |
| GPIO22 | 27 |

Wyjście AUX napędu musi być skonfigurowane jako **bezpotencjałowy sygnał stanu bramy (SCA)**. Nie może podawać napięcia na GPIO22. Przed podłączeniem sprawdź konfigurację AUX i instrukcję napędu. Nie używaj wyjścia z napięciem jako bezpośredniego sygnału logicznego ESP32.

### Fotokomórka — jeszcze niepodłączona

Planowane jest użycie dodatkowego przekaźnika: jego cewka będzie podłączona do zacisków 70 i 72 napędu, na których według założeń tej instalacji pojawia się 24 V po naruszeniu fotokomórki. Styki COM i NO tego przekaźnika mają przekazać wyłącznie odizolowany sygnał do wejścia GPIO23.

**Nie podłączaj zacisków 70–72 bezpośrednio do ESP32.** Przed realizacją trzeba potwierdzić rodzaj napięcia na 70–72, parametry cewki przekaźnika oraz sposób podłączenia styków do wejścia płytki. Fotokomórka nie jest jeszcze częścią uruchomionej instalacji.

Schemat graficzny zostanie dodany po ukończeniu i sprawdzeniu dokumentacji połączeń.

## Ważne informacje o działaniu i bezpieczeństwie

1. Pozycja bramy jest szacowana na podstawie czasu ruchu; procent nie pochodzi z enkodera i może odbiegać od rzeczywistego położenia.
2. Sygnały SCA i fotokomórki wymagają prawidłowego dopasowania elektrycznego oraz bezpiecznej izolacji.
3. Projekt nie zastępuje fabrycznych zabezpieczeń napędu ani fotokomórki.
4. Pierwsze testy wykonuj przy zapewnionym dostępie do zatrzymania napędu, bez osób i przedmiotów w świetle bramy.
5. Przed podłączeniem przewodów sprawdź instrukcję konkretnego napędu i płytki. Schemat połączeń elektrycznych zostanie opisany osobno.

## Status projektu

Integracja ma podstawowy przepływ konfiguracji, serwuje własną kartę Lovelace i podejmuje próbę automatycznej rejestracji jej zasobu. Konfigurator jest na tym etapie podstawowy; nie wykrywa jeszcze automatycznie urządzenia ESPHome ani nie weryfikuje połączeń z napędem. Firmware pozostaje pobierany i wgrywany ręcznie przez użytkownika za pomocą dodatku ESPHome.
