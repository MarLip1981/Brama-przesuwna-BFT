<div align="center">

<img src="icon.svg" alt="Napęd BFT DEIMOS ULTRA BT B" width="150">

# Brama przesuwna BFT

**Home Assistant + ESPHome · integracja i karta Lovelace dla napędu BFT**

[Repozytorium](https://github.com/MarLip1981/Brama-przesuwna-BFT) · [Zgłaszanie problemów](https://github.com/MarLip1981/Brama-przesuwna-BFT/issues)

</div>

Projekt umożliwia sterowanie bramą przesuwną BFT z poziomu Home Assistant za pomocą sterownika **ESP32 Relay X4 (AC/DC)**. Repozytorium zawiera firmware ESPHome, niestandardową integrację Home Assistant, automatycznie rejestrowaną kartę Lovelace oraz instrukcję uruchomienia.

Projekt referencyjny został przygotowany dla napędu **BFT DEIMOS ULTRA BT B 600**. Nie zakładaj zgodności z innymi napędami lub płytkami bez sprawdzenia elektryki i logiki wejść.

## Co zawiera projekt

### Firmware ESPHome
- Sterowanie wejściem napędu przez przekaźnik 1 — impuls 500 ms.
- Sterowanie funkcją furtki / częściowego otwarcia przez przekaźnik 2 — impuls 500 ms.
- Odczyt sygnału SCA i prezentowanie stanu bramy.
- Odczyt fotokomórki przez odizolowane wejście GPIO23.
- Szacowanie położenia skrzydła w procentach na podstawie czasu przejazdu.
- Ręczna kalibracja czasu pełnego zamykania oraz okresowa kalibracja tygodniowa.
- Możliwość zmiany czasu przejazdu i restartu sterownika z Home Assistant.
- Odczyt siły sygnału Wi-Fi.

### Integracja Home Assistant
- Wykrywanie sterownika ESPHome na podstawie identyfikatora projektu firmware.
- Konfiguracja i korekta przypisanych encji bez edytowania `configuration.yaml`.
- Ustawienie kierunku przesuwania bramy — w lewo lub w prawo, patrząc od strony posesji.
- Włączanie lub wyłączanie przycisku furtki.
- Globalne ustawienie trybu lampki na karcie.
- Powiadomienia po osiągnięciu stanu „Otwarta” lub „Zamknięta”.
- Automatyczna rejestracja karty Lovelace i udostępnienie jej w wyborze kart.

### Karta Lovelace
- Rysunek bramy z animacją przesuwania skrzydła i wizualizacją napędu.
- Status bramy oraz szacowana pozycja.
- Sterowanie bramą i — opcjonalnie — furtką.
- Kierunek ruchu ustawiany w integracji.
- Lampka z trzema trybami efektu: automatyczny, zawsze migający lub bez migania.
- Żółty znak ostrzegawczy na rysunku, widoczny wyłącznie wtedy, gdy fotokomórka zgłasza przeszkodę.
- Automatyczne wykrywanie sterownika i encji w edytorze karty, z możliwością ręcznej korekty.
- Możliwość nadpisania trybu lampki tylko dla konkretnej karty.

## Wymagany sprzęt i oprogramowanie

### Sprzęt
- Napęd bramy **BFT DEIMOS ULTRA BT B 600** — instalacja referencyjna.
- Sterownik **ESP32 Relay X4 (AC/DC)**.
- Fotokomórka napędu i odpowiedni, bezpiecznie odizolowany tor sygnałowy do GPIO23.
- Home Assistant z działającą integracją ESPHome.

### Oprogramowanie
- Home Assistant.
- ESPHome Device Builder / dodatek ESPHome — do kompilowania i wgrywania firmware.
- HACS — do instalacji integracji Brama przesuwna BFT.

Integracja HACS i firmware ESPHome to dwa osobne elementy. Integracja nie wgrywa firmware na ESP32.

## Uruchomienie — od zera

Zalecana kolejność: najpierw przygotuj i uruchom sterownik ESPHome, a dopiero potem dodaj integrację Home Assistant. Integracja wyszukuje urządzenie, które już jest widoczne w Home Assistant.

### 1. Przygotuj firmware ESPHome

Plik firmware znajduje się tutaj:

[`esphome/brama-wjazdowa.yaml`](esphome/brama-wjazdowa.yaml)

1. Pobierz plik i dodaj go do ESPHome Device Builder.
2. Przygotuj w ESPHome plik `secrets.yaml` z wymaganymi wpisami:

   ```yaml
   wifi_ssid: "NAZWA_GLOWNEJ_SIECI_WIFI"
   wifi_password: "HASLO_GLOWNEJ_SIECI_WIFI"
   wifi_backup_ssid: "NAZWA_ZAPASOWEJ_SIECI_WIFI"
   wifi_backup_pass: "HASLO_ZAPASOWEJ_SIECI_WIFI"
   brama_wjazdowa__encryption_key: "KLUCZ_API_ESPHome"
   ```

   Wygeneruj prawidłowy klucz szyfrowania API ESPHome — nie używaj dosłownie tekstu przykładowego.
3. Sprawdź konfigurację i skompiluj firmware.
4. Wgraj firmware na ESP32 Relay X4.
5. Dodaj urządzenie do Home Assistant przez integrację ESPHome, jeśli nie zostało dodane automatycznie.
6. Sprawdź, czy urządzenie jest dostępne i czy jego encje pojawiły się w Home Assistant.

Firmware identyfikuje projekt jako `MarLip1981.BramaPrzesuwnaBFT`. Ten znacznik jest wykorzystywany przy wykrywaniu sterownika.

### 2. Zainstaluj integrację przez HACS

Repozytorium jest przeznaczone do instalacji jako własne repozytorium HACS. Nie jest zgłaszane do oficjalnego katalogu HACS.

1. Otwórz **HACS → ⋮ → Repozytoria niestandardowe**.
2. Wklej adres:

   `https://github.com/MarLip1981/Brama-przesuwna-BFT`

3. Wybierz kategorię **Integration** i zatwierdź.
4. Wyszukaj **Brama przesuwna BFT** i zainstaluj integrację.
5. Uruchom ponownie Home Assistant.

### 3. Dodaj integrację

1. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację**.
2. Wyszukaj **Brama przesuwna BFT**.
3. Integracja wyszuka sterownik ESPHome oznaczony identyfikatorem projektu BFT.
4. Wybierz wykryty sterownik.
5. Sprawdź przypisane encje i w razie potrzeby popraw ich wybór.

Wymagane role:
- **Stan bramy** — encja tekstowa z aktualnym stanem.
- **Pozycja bramy** — sensor procentowego położenia.
- **Sterowanie bramą** — przycisk wywołujący cykl otwierania/zamykania.

Encja sterowania furtką jest opcjonalna. Jeśli jej nie używasz, przycisk furtki pozostanie wyłączony.

### 4. Skonfiguruj ustawienia integracji

Po dodaniu integracji otwórz jej **Konfiguruj** / **Opcje**. Ustawienia są podzielone na sekcje:

**Wykrywanie urządzenia i encje**
- ponowny wybór sterownika ESPHome;
- sprawdzenie i korekta przypisania encji.

**Karta i działanie bramy**
- włączenie lub wyłączenie przycisku furtki;
- kierunek przesuwania skrzydła — lewo/prawo, patrząc od strony posesji;
- globalny tryb lampki na rysunku karty:
  - **Automatyczny** — podczas zamykania miga naprzemiennie 0,5 s OFF / 0,5 s ON; podczas otwierania świeci ciągle;
  - **Zawsze miga** — miga podczas ruchu bramy;
  - **Bez migania** — świeci ciągle podczas ruchu.
  
Po zatrzymaniu i zamknięciu bramy światło na karcie gaśnie. Jest to efekt wizualny karty — ustawienie nie steruje fizyczną lampą napędu.

**Powiadomienia**
- niezależne włączenie powiadomienia po otwarciu i zamknięciu;
- wybór jednej lub kilku usług powiadomień `notify` dostępnych w Home Assistant.

Powiadomienie jest wysyłane po utrzymaniu końcowego stanu przez 2 sekundy. Stany pośrednie nie wywołują powiadomień. Domyślnie powiadomienia są wyłączone. Domyślnym odbiorcą jest `notify.cala_rodzina`; można wybrać inne dostępne usługi w ustawieniach.

### 5. Dodaj kartę do dashboardu

Integracja automatycznie rejestruje zasób JavaScript karty. Nie trzeba ręcznie dodawać zasobu Lovelace ani instalować `custom:button-card`.

1. Otwórz dashboard Home Assistant i przejdź do edycji.
2. Wybierz **Dodaj kartę**.
3. Wyszukaj kartę **Brama przesuwna BFT** i dodaj ją.
4. Otwórz edytor karty i sprawdź wykryty sterownik oraz przypisane encje.
5. Ustaw nazwę karty.
6. Wybierz tryb lampki:
   - **Użyj ustawienia integracji** — karta korzysta z ustawienia globalnego;
   - albo wybierz jeden z trzech trybów tylko dla tej karty.
7. Zapisz kartę.

Edytor karty automatycznie wyszukuje również encję fotokomórki. Jeżeli zostanie wykryta niewłaściwa encja, można poprawić przypisanie w edytorze. Nie trzeba ręcznie wpisywać identyfikatorów encji, jeśli automatyczne wykrywanie działa prawidłowo.

Integracja udostępnia kartę w pickerze, ale nie dodaje jej samodzielnie do istniejącego dashboardu.

## Obsługa karty

- Nagłówek pokazuje aktualny status bramy.
- Krótkie kliknięcie nagłówka otwiera szczegóły encji stanu bramy.
- Przytrzymanie nagłówka otwiera szczegóły encji pozycji.
- Główny przycisk służy do sterowania bramą; opis przycisku zmienia się zależnie od stanu.
- Przycisk furtki pojawia się tylko wtedy, gdy tryb furtki jest włączony i przypisana jest odpowiednia encja.
- Skrzydło na rysunku przesuwa się zgodnie z odczytywaną pozycją i ustawionym kierunkiem.
- Gdy fotokomórka wykryje przeszkodę (stan encji `on`), na środku rysunku między słupkami pojawia się żółty trójkąt z wykrzyknikiem. Po ustąpieniu przeszkody znak znika.

**Ważne:** karta prezentuje stan przekazywany przez Home Assistant. Nie zastępuje fabrycznych zabezpieczeń napędu ani fizycznej fotokomórki.

## Funkcje firmware i encje ESPHome

Firmware udostępnia między innymi:

| Funkcja | Nazwa encji (domyślna) |
|---|---|
| Stan bramy | `sensor.brama_wjazdowa_dokladny_stan_bramy` |
| Pozycja bramy | `sensor.brama_wjazdowa_pozycja_bramy` |
| Sterowanie bramą | `button.brama_wjazdowa_otworz_zamknij_brame` |
| Sterowanie furtką | `button.brama_wjazdowa_otworz_jako_furtke` |
| Kalibracja czasu | `button.brama_wjazdowa_kalibruj_czas_zamykania` |
| Fotokomórka | `binary_sensor.brama_wjazdowa_fotokomorka_przeszkoda` |
| Czas przejazdu | `number.brama_wjazdowa_czas_przejazdu_bramy` |
| Restart sterownika | `button.brama_wjazdowa_restart_esp32_brama_wjazdowa` |
| Połączenie ESPHome | `binary_sensor.brama_wjazdowa_status_polaczenia_bramy` |
| Sygnał Wi-Fi | `sensor.brama_wjazdowa_sygnal_wifi_bramy` |

Home Assistant może nadać encjom inne identyfikatory, jeśli wcześniej zmieniono ich nazwy. W takim przypadku korzystaj z encji widocznych w swoim systemie i popraw przypisania w edytorze karty.

### Pozycja i kalibracja

Pozycja bramy jest obliczana na podstawie czasu ruchu i nie pochodzi z enkodera. Wartość procentowa jest estymacją, a nie pomiarem położenia z dokładnością do milimetra.

- Domyślny czas pełnego przejazdu wynosi 17 sekund.
- Czas można skorygować encją liczbową w Home Assistant.
- Ręczna kalibracja wykonuje pełny cykl otwarcia i zamknięcia, aby zmierzyć czas zamykania.
- Firmware ustawia również znacznik kalibracji tygodniowej w poniedziałek o 03:00. Pomiar zostanie zapisany przy kolejnym kwalifikującym się pełnym zamknięciu.
- Przejazd z wykrytą przeszkodą nie jest używany do aktualizacji czasu kalibracji.

## Połączenia elektryczne — instalacja referencyjna

Poniższe przypisania dotyczą płytki ESP32 Relay X4 (AC/DC) i napędu BFT DEIMOS ULTRA BT B 600. Przed wykonaniem prac odłącz zasilanie i sprawdź oznaczenia zacisków w instrukcji konkretnej wersji napędu.

### Sterowanie przekaźnikami

| ESP32 Relay X4 | GPIO | Zacisk napędu BFT | Funkcja |
|---|---:|---:|---|
| Przekaźnik 1 — COM | 32 | 60 | Wspólny styk sterowania |
| Przekaźnik 1 — NO | 32 | 61 | Impuls sterujący bramą |
| Przekaźnik 2 — COM | 33 | 60 | Wspólny styk drugiego wejścia |
| Przekaźnik 2 — NO | 33 | 62 | Impuls funkcji furtki / częściowego otwarcia |
| Przekaźniki 3 i 4 | 25 / 26 | — | Rezerwa |

Przekaźniki 1 i 2 działają jako styki bezpotencjałowe. Firmware generuje impuls o długości 500 ms. Nie doprowadzaj napięcia zasilającego ESP32 do zacisków sterujących napędu.

### Odczyt stanu SCA

| ESP32 Relay X4 | GPIO | Zacisk napędu BFT |
|---|---:|---:|
| GND | GND | 26 |
| Wejście sygnałowe | 22 | 27 |

Wyjście AUX napędu musi być skonfigurowane jako bezpotencjałowy sygnał stanu bramy (SCA). Nie podłączaj do GPIO22 sygnału z napięciem.

### Fotokomórka

Sygnał fotokomórki jest odczytywany przez wejście **GPIO23**. Pomiędzy obwodem napędu/fotokomórki a ESP32 musi być zastosowane odpowiednie odizolowanie elektryczne — zgodnie z wykonaną instalacją i parametrami zastosowanego elementu pośredniczącego.

**Nie podłączaj napięcia 24 V ani zacisków napędu bezpośrednio do GPIO ESP32.** Przed zmianą okablowania sprawdź rodzaj sygnału, napięcia i sposób izolacji. Wejście w firmware ma podciąganie `INPUT_PULLUP` i odwróconą logikę.

## Bezpieczeństwo i ograniczenia

1. Projekt nie zastępuje fabrycznej centrali, zabezpieczeń przeciążeniowych, fotokomórki ani innych wymaganych zabezpieczeń napędu.
2. Znak ostrzegawczy na karcie jest wyłącznie wizualną informacją o stanie encji fotokomórki. Nie jest niezależnym zabezpieczeniem.
3. Procentowa pozycja skrzydła jest estymowana czasowo; może odbiegać od rzeczywistego położenia.
4. Sygnały SCA i fotokomórki muszą być prawidłowo dopasowane elektrycznie i odizolowane od GPIO.
5. Nie wykonuj prac przy przewodach ani zaciskach przy zasilonym napędzie. W razie wątpliwości skorzystaj z pomocy osoby z odpowiednimi kwalifikacjami.
6. Pierwsze uruchomienie i próby ruchu wykonuj z dobrą widocznością bramy, bez ludzi, zwierząt i przedmiotów w świetle ruchu skrzydła.

## Struktura repozytorium

- `esphome/brama-wjazdowa.yaml` — firmware sterownika ESP32.
- `custom_components/brama_przesuwna_bft/` — integracja Home Assistant, konfigurator, sensory i frontend.
- `custom_components/brama_przesuwna_bft/www/brama-przesuwna-bft-card.js` — karta Lovelace i jej edytor.
- `lovelace/brama-wjazdowa.yaml` — archiwalna wersja karty YAML; wymaga `custom:button-card`.
- `icon.svg` — grafika napędu BFT używana jako logo repozytorium.

## Wersja

Aktualna wersja integracji i karty: **1.13.7**.

## Zgłaszanie problemów

Jeżeli coś nie działa, dołącz:
- wersję Home Assistant;
- wersję integracji;
- nazwę i model sterownika ESPHome;
- stan odpowiednich encji (bez haseł i kluczy);
- fragment logu z momentu wystąpienia problemu.

Nie publikuj w zgłoszeniu pliku `secrets.yaml`, klucza API ESPHome, haseł Wi-Fi ani innych danych dostępowych.
