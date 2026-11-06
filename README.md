<div align="center">

<img src="icon.svg" alt="Napęd BFT DEIMOS ULTRA BT B" width="150">

# Brama przesuwna BFT

**Home Assistant + ESPHome · integracja i karta Lovelace dla napędu BFT**

[Repozytorium](https://github.com/MarLip1981/Brama-przesuwna-BFT) · [Zgłaszanie problemów](https://github.com/MarLip1981/Brama-przesuwna-BFT/issues)

</div>

Projekt tworzy kompletny system integracji bramy przesuwnej z **Home Assistant**: od sterownika opartego na ESP32 i firmware ESPHome, przez natywną integrację z konfiguracją graficzną, aż po autorską, animowaną kartę Lovelace. Umożliwia sterowanie bramą i funkcją furtki, prezentację stanu oraz szacowanej pozycji skrzydła, wizualizację fotokomórki, konfigurację kierunku ruchu, sygnalizacji świetlnej i powiadomień.

Punktem odniesienia projektu jest napęd **BFT DEIMOS ULTRA BT B 600** oraz sterownik **ESP32 Relay X4 (AC/DC)**. Zasady adaptacji do innych napędów i ograniczenia kompatybilności opisano w osobnej sekcji.

## Co zawiera projekt

### Firmware ESPHome
- Sterowanie wejściem napędu przez przekaźnik 1 — impuls 500 ms.
- Sterowanie funkcją furtki / częściowego otwarcia przez przekaźnik 2 — impuls 500 ms.
- Odczyt sygnału SCA i prezentowanie stanu bramy.
- Odczyt fotokomórki przez odizolowane wejście GPIO23.
- Szacowanie położenia skrzydła w procentach na podstawie czasu przejazdu.
- Ręczna kalibracja czasu pełnego zamykania oraz okresowa kalibracja tygodniowa.
- Możliwość zmiany czasu przejazdu i restartu sterownika z Home Assistant.
- Obsługa dwóch fizycznych przycisków: krótkie naciśnięcie steruje odpowiednim wejściem BFT, a długie przytrzymanie przełącza przekaźnik P3 lub P4.
- Rozpoznawanie długiego przytrzymania po 1,5 s; impuls sterujący jest wysyłany dopiero po puszczeniu przycisku, więc długie przytrzymanie nie wywołuje przypadkowego ruchu bramy.
- Publikowanie ostatniego rozpoznanego rodzaju naciśnięcia obu przycisków do Home Assistant. Sensory zdarzeń przyjmują wartości „Krótkie naciśnięcie” albo „Długie przytrzymanie”; aktualizują się po rozpoznaniu zdarzenia, a nie w trakcie trzymania przycisku.
- Odczyt siły sygnału Wi-Fi.

### Integracja Home Assistant
- Wykrywanie sterownika ESPHome na podstawie identyfikatora projektu firmware.
- Graficzna konfiguracja urządzenia i przypisanych encji.
- Ustawienie kierunku przesuwania bramy — w lewo lub w prawo, patrząc od strony posesji.
- Włączanie lub wyłączanie przycisku furtki.
- Globalne ustawienie trybu lampki na karcie.
- Powiadomienia po osiągnięciu stanu „Otwarta” lub „Zamknięta”.
- Automatyczna rejestracja karty Lovelace i udostępnienie jej w wyborze kart.

### Karta Lovelace
- Szczegółowa, animowana wizualizacja bramy, skrzydła, słupków, napędu i lampki sygnalizacyjnej.
- Animacja ruchu skrzydła zsynchronizowana z procentową pozycją przekazywaną przez ESPHome.
- Obsługa obu kierunków przesuwu: w lewo i w prawo. Kierunek jest pobierany z konfiguracji integracji, a karta odpowiednio odwraca całą scenę i animację, zachowując prawidłową orientację wizualizacji.
- Status bramy oraz szacowana pozycja.
- Sterowanie bramą i — opcjonalnie — furtką.
- Kierunek ruchu i orientacja animacji zgodne z ustawieniem integracji.
- Lampka z trzema trybami efektu: automatyczny, zawsze migający lub bez migania.
- Żółty znak ostrzegawczy na rysunku, widoczny wyłącznie wtedy, gdy fotokomórka zgłasza przeszkodę.
- Ręczna blokada zamknięcia obsługiwana przez przekaźnik 3 ESPHome: przytrzymanie głównego przycisku karty przez 0,75 s przełącza blokadę. Aktywna blokada pokazuje trójkąt ostrzegawczy na grafice bramy oraz czerwony, pulsujący napis „RĘCZNA BLOKADA ZAMKNIĘCIA” pod grafiką. Krótkie kliknięcia nadal realizują standardową sekwencję sterowania centrali BFT.
- Panel diagnostyczny pokazujący ostatnie rozpoznane naciśnięcie fizycznego przycisku bramy i furtki (krótkie lub długie), o ile firmware udostępnia odpowiednie sensory.
- Automatyczne wykrywanie sterownika i encji w edytorze karty, z możliwością ręcznej korekty.
- Możliwość nadpisania trybu lampki tylko dla konkretnej karty.

## Kompatybilność i możliwość adaptacji

Projekt został opracowany i zweryfikowany w konfiguracji referencyjnej z napędem **BFT DEIMOS ULTRA BT B 600** oraz sterownikiem **ESP32 Relay X4 (AC/DC)**. Można wykorzystać go jako bazę do integracji innych bram przesuwnych, o ile centrala napędu udostępnia odpowiednie wejścia sterujące i sygnały stanu, a zastosowany sterownik ESP32 można bezpiecznie dopasować do tych obwodów.

Przy adaptacji do innego modelu bramy należy samodzielnie:
- przeanalizować schemat elektryczny i instrukcję konkretnej centrali;
- ustalić funkcje zacisków sterujących, wyjść statusowych i fotokomórki;
- zweryfikować napięcia, polaryzację, typ wyjść oraz dopuszczalne obciążenia;
- dobrać odpowiednie przekaźniki, separację galwaniczną i układy wejściowe;
- dostosować firmware ESPHome oraz przypisanie encji do rzeczywistego okablowania;
- wykonać testy działania i zabezpieczeń przed normalnym użytkowaniem.

**Nie należy kopiować połączeń z tabeli BFT do innej centrali bez niezależnej weryfikacji.** Różnice między modelami, wersjami płyt sterujących i konfiguracją zacisków mogą być istotne. Wszelkie prace elektryczne wykonuj zgodnie z dokumentacją producenta i zasadami bezpieczeństwa.

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

Firmware ESPHome i integracja Home Assistant pełnią odrębne role: firmware obsługuje wejścia/wyjścia sterownika, a integracja wykrywa urządzenie, udostępnia jego funkcje i konfiguruje kartę.

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

Repozytorium dodaje się w HACS jako niestandardowe źródło integracji.

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

Integracja rejestruje zasób JavaScript karty w Home Assistant i udostępnia ją w natywnym pickerze Lovelace.

1. Otwórz dashboard Home Assistant i przejdź do edycji.
2. Wybierz **Dodaj kartę**.
3. Wyszukaj kartę **Brama przesuwna BFT** i dodaj ją.
4. Otwórz edytor karty i sprawdź wykryty sterownik oraz przypisane encje.
5. Ustaw nazwę karty.
6. Wybierz tryb lampki:
   - **Użyj ustawienia integracji** — karta korzysta z ustawienia globalnego;
   - albo wybierz jeden z trzech trybów tylko dla tej karty.
7. Zapisz kartę.

Edytor karty automatycznie wyszukuje również encję fotokomórki. W razie potrzeby przypisanie każdej roli można skorygować ręcznie, wybierając encję z listy.

Po dodaniu karty do dashboardu jej ustawienia i przypisania encji można ponownie edytować z poziomu konfiguratora.

## Podgląd karty

Poniżej znajduje się przykładowy wygląd karty w Home Assistant.

<p align="center">
  <img src="Screenshot_20261101_180959_Home%20Assistant.jpg" alt="Karta sterowania bramą przesuwną w Home Assistant — widok zamkniętej bramy z przyciskami sterowania" width="100%">
</p>

## Obsługa karty

Karta łączy panel sterowania z animowaną wizualizacją mechaniki bramy. Ruch skrzydła jest przedstawiany płynnie na podstawie aktualizowanej pozycji procentowej. Konfiguracja kierunku w integracji określa również stronę, w którą skrzydło odsuwa się na rysunku — **lewo i prawo są obsługiwane jako dwa warianty tej samej sceny**.

- Nagłówek pokazuje aktualny status bramy.
- Krótkie kliknięcie nagłówka otwiera szczegóły encji stanu bramy.
- Przytrzymanie nagłówka otwiera szczegóły encji pozycji.
- Krótkie kliknięcie głównego przycisku steruje bramą; opis przycisku zmienia się zależnie od stanu.
- Przytrzymanie głównego przycisku przez 0,75 s przełącza ręczną blokadę zamknięcia (przekaźnik 3). Funkcja wymaga przypisanej encji przełącznika; karta wykrywa ją po nazwie „Blokada zamknięcia” lub pozwala wybrać ręcznie w edytorze.
- Aktywna blokada wyświetla trójkąt ostrzegawczy na grafice i czerwony pulsujący napis pod grafiką. Jest to osobny stan od rzeczywistej przeszkody fotokomórki. Krótkie naciśnięcia głównego przycisku nie zmieniają działania standardowej sekwencji BFT; wyłącznie przytrzymanie przez 0,75 s przełącza przekaźnik 3.
- Przycisk furtki pojawia się tylko wtedy, gdy tryb furtki jest włączony i przypisana jest odpowiednia encja.
- Gdy fotokomórka wykryje przeszkodę (stan encji `on`), na środku rysunku między słupkami pojawia się żółty trójkąt z wykrzyknikiem. Po ustąpieniu przeszkody znak znika.

**Ważne:** karta prezentuje stan przekazywany przez Home Assistant. Nie zastępuje fabrycznych zabezpieczeń napędu ani fizycznej fotokomórki.


## Funkcje firmware i encje ESPHome

Firmware udostępnia między innymi:

| Funkcja | Nazwa encji w ESPHome | Domena |
|---|---|---|
| Stan bramy | Dokładny stan bramy | `text_sensor` → `sensor` w HA |
| Pozycja bramy | Pozycja bramy | `sensor` |
| Sterowanie bramą | Otwórz / Zamknij bramę | `button` |
| Sterowanie furtką | Otwórz jako furtkę | `button` |
| Kalibracja czasu | Kalibruj czas zamykania | `button` |
| Fotokomórka | Fotokomórka — przeszkoda | `binary_sensor` |
| Czas przejazdu | Czas przejazdu bramy | `number` |
| Restart sterownika | Restart ESP32 — brama wjazdowa | `button` |
| Połączenie ESPHome | Status połączenia bramy | `binary_sensor` |
| Sygnał Wi-Fi | Sygnał WiFi bramy | `sensor` |
| Ostatnie naciśnięcie przycisku bramy | Ostatnie naciśnięcie przycisku bramy | `sensor` |
| Ostatnie naciśnięcie przycisku furtki | Ostatnie naciśnięcie przycisku furtki | `text_sensor` → `sensor` w HA |

Sensory zdarzeń fizycznych przycisków:
- `sensor.brama_wjazdowa_ostatnie_nacisniecie_przycisku_bramy` — ostatnie zdarzenie przycisku bramy.
- `sensor.brama_wjazdowa_ostatnie_nacisniecie_przycisku_furtki` — ostatnie zdarzenie przycisku furtki.
- Wartość **„Krótkie naciśnięcie”** oznacza, że po puszczeniu przycisku firmware wykonał standardowy impuls odpowiednio P1 (brama) lub P2 (furtka).
- Wartość **„Długie przytrzymanie”** oznacza przytrzymanie przez co najmniej 1,5 s i przełączenie odpowiednio P3 (blokada zamknięcia) lub P4 (oświetlenie). Długie przytrzymanie nie powinno wywołać impulsu P1/P2.
- Sensor przechowuje ostatnio rozpoznane zdarzenie — nie jest licznikiem naciśnięć ani bieżącym stanem przycisku.

**Uwaga dotycząca wersji:** obsługa tych zdarzeń i wejść fizycznych jest przygotowana w firmware 1.1.1. Plik `esphome/brama-wjazdowa.yaml` w gałęzi `main` nadal ma wersję 1.0.0; aktualizacja firmware do repozytorium nastąpi dopiero po walidacji i potwierdzeniu działania na sterowniku.

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

| Kanał przekaźnika | GPIO sterujące | Styk COM → BFT | Styk NO → BFT | Funkcja |
|---|---:|---:|---:|---|
| Przekaźnik 1 | GPIO32 | 60 | 61 | Impuls sterujący bramą |
| Przekaźnik 2 | GPIO33 | 60 | 62 | Impuls funkcji furtki / częściowego otwarcia |
| Przekaźnik 3 | GPIO25 | — | — | Ręczna blokada zamknięcia |
| Przekaźnik 4 | GPIO26 | — | — | Własny — dowolne zastosowanie |

GPIO steruje przekaźnikiem na płytce ESP32 Relay X4. Do centrali BFT podłączane są bezpotencjałowe styki COM i NO przekaźnika, a nie samo GPIO.

Przekaźniki 1 i 2 działają jako styki bezpotencjałowe. Firmware generuje impuls o długości 500 ms. Nie doprowadzaj napięcia zasilającego ESP32 do zacisków sterujących napędu.

### Fizyczne przyciski ścienne

| Funkcja | GPIO ESP32 | Działanie |
|---|---:|---|
| Przycisk bramy | GPIO18 | Krótko: impuls P1; długo (1,5 s): przełączenie P3 — blokada zamknięcia |
| Przycisk furtki | GPIO17 | Krótko: impuls P2; długo (1,5 s): przełączenie P4 — oświetlenie |

Wejścia przycisków są przeznaczone do pracy jako styki zwierające GPIO do GND z podciąganiem `INPUT_PULLUP`. Nie doprowadzaj do nich napięcia z centrali BFT. GPIO17 i GPIO18 są przypisaniami projektowymi, które należy potwierdzić na konkretnej wersji płytki ESP32 Relay X4 przed lutowaniem przewodów. Przycisk furtki zachowuje równoległe, bezpośrednie połączenie z centralą BFT jako niezależną drogę awaryjną; piloty również pozostają podłączone bezpośrednio do centrali.

### Odczyt stanu SCA

| Połączenie | Zacisk napędu BFT | Funkcja |
|---|---:|---|
| GND sterownika ESP32 | 26 | Wspólny punkt odniesienia |
| GPIO22 | 27 | Sygnał SCA |

Wyjście AUX napędu musi być skonfigurowane jako bezpotencjałowy sygnał stanu bramy (SCA). Do GPIO22 nie wolno doprowadzać napięcia z wyjścia, które nie jest zgodne elektrycznie z wejściem ESP32.

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

Aktualna wersja integracji i karty: **1.14.3**.

Wersja 1.14.3 dodaje opcjonalne wykorzystanie przekaźnika P4 do oświetlenia wjazdu. Funkcję włącza się w ustawieniach integracji; karta pokazuje oświetlenie na słupkach i odpowiedni przycisk zależnie od tego, czy użytkownik korzysta z furtki.

## Zgłaszanie problemów

Jeżeli coś nie działa, dołącz:
- wersję Home Assistant;
- wersję integracji;
- nazwę i model sterownika ESPHome;
- stan odpowiednich encji (bez haseł i kluczy);
- fragment logu z momentu wystąpienia problemu.

Nie publikuj w zgłoszeniu pliku `secrets.yaml`, klucza API ESPHome, haseł Wi-Fi ani innych danych dostępowych.
