/* Brama przesuwna BFT — native Web Components, no Lit dependency. */
(() => {
const registerBramaCard = () => {
const ROLES = {
  status: { label: "Stan bramy", domains: ["sensor"], test: /dokladny stan bramy|dokladny stan|stan bramy|gate status/i },
  position: { label: "Pozycja bramy", domains: ["sensor"], test: /pozycja bramy|pozycja|position/i },
  main_button: { label: "Sterowanie bramą", domains: ["button"], test: /otworz zamknij brame|otworz zamknij|sterowanie brama|gate/i },
  pedestrian_button: { label: "Sterowanie furtką", domains: ["button"], test: /otworz jako furtke|furtk|pedestrian/i },
  photocell: { label: "Fotokomórka — wykrywanie przeszkody", domains: ["binary_sensor"], test: /fotokomorka.*przeszkoda|fotokomorka|photocell/i },
  manual_lock: { label: "Blokada zamknięcia — przekaźnik 3", domains: ["switch"], test: /blokada zamkniecia|relay 3|rele 3|przekaznik 3/i },
  gate_button_event: { label: "Ostatnie naciśnięcie przycisku bramy", domains: ["sensor"], test: /ostatnie nacisniecie przycisku bramy|zdarzenie przycisku bramy/i },
  wicket_button_event: { label: "Ostatnie naciśnięcie przycisku furtki", domains: ["sensor"], test: /ostatnie nacisniecie przycisku furtki|zdarzenie przycisku furtki/i },
  entrance_lighting: { label: "Oświetlenie wjazdu — przekaźnik 4", domains: ["switch"], test: /oswietlenie wjazdu|przekaznik 4|relay 4|rele 4/i },
};
const MODE_ENTITY = "binary_sensor.brama_przesuwna_bft_tryb_furtki";
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const normalize = (value) => String(value ?? "").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

class BramaPrzesuwnaBFTCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = null;
    this._hass = null;
    this._holdTimer = null;
    this._holdFired = false;
    this._mainHoldTimer = null;
    this._mainHoldFired = false;
    this._auxHoldTimer = null;
    this._auxHoldFired = false;
  }
  setConfig(config) {
    this._config = {
      name: config.name || "Brama wjazdowa",
      radio: { ...(config.radio || {}) },
      status_entity: config.status_entity || "",
      position_entity: config.position_entity || "",
      main_button: config.main_button || "",
      pedestrian_button: config.pedestrian_button || "",
      lamp_mode: config.lamp_mode || "integration",
    };
    this._render();
  }
  set hass(value) { this._hass = value; this._render(); }
  get hass() { return this._hass; }
  getCardSize() { return 3; }
  _entity(role) {
    const legacyKey = ({status:"status_entity",position:"position_entity",main_button:"main_button",pedestrian_button:"pedestrian_button",photocell:"photocell_entity",manual_lock:"manual_lock_entity",entrance_lighting:"entrance_lighting_entity",gate_button_event:"gate_button_event_entity",wicket_button_event:"wicket_button_event_entity"})[role];
    return this._config?.radio?.[role] || this._config?.[legacyKey] ||
      this._hass?.states?.[MODE_ENTITY]?.attributes?.entities?.[role] ||
      (role === "photocell" ? Object.keys(this._hass?.states || {}).find(id =>
        id.startsWith("binary_sensor.") && /fotokomorka.*przeszkoda|fotokomorka|photocell/i.test(id)) :
       role === "manual_lock" ? Object.keys(this._hass?.states || {}).find(id => {
         const state = this._hass.states[id];
         return id.startsWith("switch.") && /blokada zamkniecia|relay 3|rele 3|przekaznik 3/i.test(
           normalize([id, state?.attributes?.friendly_name].join(" ")));
       }) :
       role === "entrance_lighting" ? Object.keys(this._hass?.states || {}).find(id => {
         const state = this._hass.states[id];
         return id.startsWith("switch.") && /oswietlenie wjazdu|relay 4|rele 4|przekaznik 4/i.test(
           normalize([id, state?.attributes?.friendly_name].join(" ")));
       }) :
       role === "gate_button_event" || role === "wicket_button_event" ?
         Object.keys(this._hass?.states || {}).find(id => {
           const state = this._hass.states[id];
           return id.startsWith("sensor.") && ROLES[role].test.test(
             normalize([id, state?.attributes?.friendly_name].join(" ")));
         }) : "") || "";
  }
  _state(id) { return this._hass?.states?.[id]?.state; }
  _press(id) { if (id && this._hass) this._hass.callService("button", "press", { entity_id: id }); }
  _toggleSwitch(id) { if (id && this._hass) this._hass.callService("switch", "toggle", { entity_id: id }); }
  _mainDown(event) {
    this._mainHoldFired = false;
    clearTimeout(this._mainHoldTimer);
    const lockEntity = this._entity("manual_lock");
    if (!lockEntity) {
      console.warn("Brama BFT: nie przypisano encji przełącznika P3 — blokada zamknięcia nie może zostać przełączona.");
      return;
    }
    // Capture the pointer so a touch gesture remains attached to the main
    // button even if the finger drifts slightly while the user is holding it.
    if (event?.currentTarget && event.pointerId !== undefined) {
      try { event.currentTarget.setPointerCapture(event.pointerId); } catch (_) {}
    }
    this._mainHoldTimer = setTimeout(() => {
      this._mainHoldFired = true;
      this._toggleSwitch(lockEntity);
    }, 750);
  }
  _mainUp(event) {
    clearTimeout(this._mainHoldTimer);
    if (event?.currentTarget && event.pointerId !== undefined) {
      try {
        if (event.currentTarget.hasPointerCapture(event.pointerId)) {
          event.currentTarget.releasePointerCapture(event.pointerId);
        }
      } catch (_) {}
    }
  }
  // Long-pressing the wicket button toggles P4 only when lighting mode is enabled.
  _auxDown(event) {
    this._auxHoldFired = false;
    clearTimeout(this._auxHoldTimer);
    const lightEntity = this._entity("entrance_lighting");
    if (!lightEntity) return;
    if (event?.currentTarget && event.pointerId !== undefined) {
      try { event.currentTarget.setPointerCapture(event.pointerId); } catch (_) {}
    }
    this._auxHoldTimer = setTimeout(() => {
      this._auxHoldFired = true;
      this._toggleSwitch(lightEntity);
    }, 750);
  }
  _auxUp(event) {
    clearTimeout(this._auxHoldTimer);
    if (event?.currentTarget && event.pointerId !== undefined) {
      try {
        if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
      } catch (_) {}
    }
  }
  _bindActionButtons(pedestrianEnabled, lightingEnabled) {
    const main = this.shadowRoot.querySelector(".main");
    if (main) {
      main.addEventListener("pointerdown", e => { if (e.isPrimary !== false && e.button === 0) this._mainDown(e); });
      for (const event of ["pointerup","pointercancel"]) main.addEventListener(event, e => this._mainUp(e));
      main.addEventListener("click", e => {
        if (this._mainHoldFired) { this._mainHoldFired = false; e.preventDefault(); return; }
        this._press(this._entity("main_button"));
      });
    }
    if (pedestrianEnabled) {
      const button = this.shadowRoot.querySelector(".pedestrian");
      if (button) {
        if (lightingEnabled) {
          button.addEventListener("pointerdown", e => { if (e.isPrimary !== false && e.button === 0) this._auxDown(e); });
          for (const event of ["pointerup","pointercancel"]) button.addEventListener(event, e => this._auxUp(e));
        }
        button.addEventListener("click", e => {
          if (this._auxHoldFired) { this._auxHoldFired = false; e.preventDefault(); return; }
          this._press(/otwarta/i.test(this._state(this._entity("status")) || "") ? this._entity("main_button") : this._entity("pedestrian_button"));
        });
      }
    } else if (lightingEnabled) {
      this.shadowRoot.querySelector(".lighting")?.addEventListener("click", () => this._toggleSwitch(this._entity("entrance_lighting")));
    }
  }
  _moreInfo(id) {
    if (id) this.dispatchEvent(new CustomEvent("hass-more-info", {
      detail: { entityId: id }, bubbles: true, composed: true
    }));
  }
  _headerDown() {
    this._holdFired = false;
    clearTimeout(this._holdTimer);
    this._holdTimer = setTimeout(() => {
      this._holdFired = true;
      this._moreInfo(this._entity("position"));
    }, 600);
  }
  _headerUp() { clearTimeout(this._holdTimer); }
  _render() {
    if (!this._config || !this._hass) return;
    const mode = this._hass.states?.[MODE_ENTITY];
    const positionId = this._entity("position"), statusId = this._entity("status");
    const mainButton = this._entity("main_button"), pedestrianButton = this._entity("pedestrian_button");
    const photocellId = this._entity("photocell");
    const photocellDanger = this._state(photocellId) === "on";
    const manualLockId = this._entity("manual_lock");
    const manualLockActive = this._state(manualLockId) === "on";
    const entranceLightingId = this._entity("entrance_lighting");
    const entranceLightingActive = this._state(entranceLightingId) === "on";
    const gateButtonEvent = this._state(this._entity("gate_button_event"));
    const wicketButtonEvent = this._state(this._entity("wicket_button_event"));
    const eventLabel = value => {
      if (!value || ["unknown", "unavailable"].includes(value)) return "Brak danych";
      if (/dlug|dług/i.test(value)) return "Długie przytrzymanie";
      if (/krot|krót/i.test(value)) return "Krótkie naciśnięcie";
      return value;
    };
    const raw = this._state(positionId), n = Number(raw);
    const valid = raw !== undefined && !["unknown","unavailable"].includes(raw) && Number.isFinite(n);
    const pos = valid ? Math.max(0, Math.min(100, Math.round(n))) : 0;
    const status = this._state(statusId) || "Brak stanu";
    const moving = /otwieranie|zamykanie/i.test(status), open = /otwarta/i.test(status), closed = /zamknięta/i.test(status);
    let statusLabel = status;
    if (closed) statusLabel = "● Zamknięta";
    else if (open) statusLabel = "● Otwarta";
    else if (/otwieranie/i.test(status)) statusLabel = "● Otwieranie" + (valid ? " " + pos + "%" : "");
    else if (/zamykanie/i.test(status)) statusLabel = "● Zamykanie" + (valid ? " " + pos + "%" : "");
    else if (!status || ["unknown","unavailable","Brak stanu"].includes(status)) statusLabel = "Brak stanu";
    const direction = mode?.attributes?.opening_direction || "right";
    const pedestrianEnabled = mode?.state === "on" && Boolean(pedestrianButton);
    // P4 is presented as driveway lighting only after explicit opt-in in the integration options.
    const lightingEnabled = mode?.attributes?.entrance_lighting_enabled === true && Boolean(entranceLightingId);
    const auxiliaryMode = pedestrianEnabled ? "pedestrian" : lightingEnabled ? "lighting" : "none";
    // Rebind the wicket long-press handler when P4 lighting is enabled or disabled.
    const actionConfigKey = auxiliaryMode + ":" + (lightingEnabled ? "light" : "no-light");
    const auxiliaryMarkup = pedestrianEnabled
      ? `<button class="pedestrian"><ha-icon icon="mdi:walk"></ha-icon><span>${pedestrianLabel}</span></button>`
      : lightingEnabled ? `<button class="lighting"><ha-icon icon="mdi:lightbulb"></ha-icon><span>Oświetlenie wjazdu: ${entranceLightingActive ? "WŁ." : "WYŁ."}</span></button>` : "";
    // Labels and actions follow the original YAML card state machine.
    const mainLabel = moving ? "Brama - Stop" : open ? "Brama - Zamknij" :
      closed ? "Brama - Otwórz" : "Brama - Steruj";
    const pedestrianLabel = open ? "Furtka - Zamknij" : "Furtka - Otwórz";
    const closing = /zamykanie/i.test(status);
    const configuredLampMode = this._config.lamp_mode || "integration";
    const lampMode = configuredLampMode === "integration"
      ? (mode?.attributes?.lamp_mode || "auto") : configuredLampMode;
    const shift = 1.9 * pos, lamp = moving || open;
    const lampBlink = moving && (lampMode === "always_blink" ||
      (lampMode !== "no_blink" && closing));
    // The card is re-rendered on Home Assistant state updates. Keep the
    // beacon's 1-second blink cycle aligned to a stable clock phase.
    const lampBlinkPhase = (Date.now() % 1000) / 1000;
    const statusClass = moving ? "moving" : open ? "open" : closed ? "closed" : "";
    if (this.shadowRoot.querySelector(".head")) {
      const statusNode = this.shadowRoot.querySelector(".status");
      statusNode.textContent = statusLabel;
      statusNode.className = "status " + statusClass;
      this.shadowRoot.querySelector(".gate-leaf").setAttribute("transform", "translate(" + shift + ",0)");
      const beacon = this.shadowRoot.querySelector(".beacon-emission");
      beacon.style.opacity = lamp ? "1" : "0";
      beacon.classList.toggle("beacon-blink", lampBlink);
      this.shadowRoot.querySelector(".main span").textContent = mainLabel;
      const actions = this.shadowRoot.querySelector(".actions");
      if (actions.dataset.auxiliaryMode !== actionConfigKey) {
        actions.innerHTML = `<button class="main"><ha-icon icon="mdi:gate"></ha-icon><span>${mainLabel}</span></button>${auxiliaryMarkup}`;
        actions.dataset.auxiliaryMode = actionConfigKey;
        this._bindActionButtons(pedestrianEnabled, lightingEnabled);
      }
      actions.style.gridTemplateColumns = auxiliaryMode === "none" ? "1fr" : "1fr 1fr";
      const mainLabelNode = actions.querySelector(".main span");
      if (mainLabelNode) mainLabelNode.textContent = mainLabel;
      const auxiliaryLabelNode = actions.querySelector(".pedestrian span, .lighting span");
      if (auxiliaryLabelNode) auxiliaryLabelNode.textContent = pedestrianEnabled ? pedestrianLabel : `Oświetlenie wjazdu: ${entranceLightingActive ? "WŁ." : "WYŁ."}`;
      const lightGlow = this.shadowRoot.querySelector(".entrance-light-emission");
      if (lightGlow) lightGlow.style.display = lightingEnabled && entranceLightingActive ? "inline" : "none";
      const warning = this.shadowRoot.querySelector(".photocell-warning");
      if (warning) warning.style.display = (photocellDanger || manualLockActive) ? "inline" : "none";
      const manualLabel = this.shadowRoot.querySelector(".manual-lock-label");
      if (manualLabel) manualLabel.style.display = manualLockActive ? "block" : "none";
      const gateEventNode = this.shadowRoot.querySelector(".gate-button-event");
      const wicketEventNode = this.shadowRoot.querySelector(".wicket-button-event");
      if (gateEventNode) gateEventNode.textContent = "Przycisk bramy: " + eventLabel(gateButtonEvent);
      if (wicketEventNode) wicketEventNode.textContent = "Przycisk furtki: " + eventLabel(wicketButtonEvent);
      const warningLabel = this.shadowRoot.querySelector(".photocell-warning");
      if (warningLabel) warningLabel.setAttribute("aria-label", manualLockActive ? "Ręczna blokada zamknięcia" : "Fotokomórka wykryła przeszkodę");
      return;
    }
    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;color:var(--primary-text-color)}
        ha-card{display:block;padding:12px;overflow:hidden;border-radius:22px;background:var(--ha-card-background,var(--card-background-color));box-shadow:var(--ha-card-box-shadow,none)}
        .head{display:flex;justify-content:space-between;align-items:center;gap:8px;cursor:pointer;user-select:none;padding:4px}
        h2{font-size:20px;margin:0;font-weight:600}.status{font-size:14px;font-weight:500;text-align:right;white-space:nowrap}
        .status.closed{color:#42c878}.status.open{color:#ff4545;font-weight:800;text-shadow:0 0 8px rgba(255,50,50,.65)}.status.moving{color:#ffbd4a}
        .manual-lock-label{display:${manualLockActive ? "block" : "none"};margin:2px 4px 6px;text-align:center;color:#ff4545;font-size:13px;font-weight:900;letter-spacing:.055em;text-shadow:0 0 5px rgba(255,35,35,.65),0 0 11px rgba(255,35,35,.35);animation:manualLockPulse 1.5s ease-in-out infinite}
        .button-events{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin:6px 3px 2px;color:var(--secondary-text-color);font-size:11px;text-align:center}
        .button-events span{padding:5px 3px;border-radius:8px;background:var(--secondary-background-color)}
        @keyframes manualLockPulse{0%,100%{opacity:1;text-shadow:0 0 5px rgba(255,35,35,.65),0 0 11px rgba(255,35,35,.35)}50%{opacity:.62;text-shadow:0 0 2px rgba(255,35,35,.35)}}
        .scene{width:100%;margin:0;overflow:hidden}svg{display:block;width:100%;height:155px}
        .gate-leaf{transition:transform 1.05s linear}
        .beacon-emission{transition:opacity .2s ease}
        .beacon-blink{animation:beaconBlink 1s steps(1,end) infinite}
        @keyframes beaconBlink{0%,49.999%{opacity:0}50%,100%{opacity:1}}
        .actions{display:grid;grid-template-columns:${auxiliaryMode === "none" ? "1fr" : "1fr 1fr"};gap:8px;margin-top:8px}
        button{touch-action:none;-webkit-user-select:none;user-select:none;min-height:48px;border:0;border-radius:16px;padding:14px;background:var(--secondary-background-color);color:var(--primary-text-color);font:inherit;font-weight:600;cursor:pointer}
        button.main{color:#429ee8}
        button.pedestrian{color:#39b982}
        button.lighting{color:#e7b84b}
        button ha-icon{--mdc-icon-size:28px;flex:0 0 auto}
        button{display:flex;align-items:center;justify-content:center;gap:9px}
      </style>
      <ha-card>
        <div class="head" role="button" tabindex="0"><h2>${esc(this._config.name)}</h2><div class="status ${statusClass}">${esc(statusLabel)}</div></div>
        <div class="scene">
          <svg viewBox="0 0 400 155" width="100%" height="155" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Brama wjazdowa">
            <defs>
              <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#607984" stop-opacity=".08"/><stop offset="100%" stop-color="#182b35" stop-opacity=".25"/></linearGradient>
              <linearGradient id="gateFill" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#465b65"/><stop offset="50%" stop-color="#80949d"/><stop offset="100%" stop-color="#465b65"/></linearGradient>
              <radialGradient id="lampOuterGlow"><stop offset="0%" stop-color="#ffd77a" stop-opacity=".30"/><stop offset="42%" stop-color="#ffbd4d" stop-opacity=".20"/><stop offset="100%" stop-color="#ff9f24" stop-opacity="0"/></radialGradient><radialGradient id="lampLight"><stop offset="0%" stop-color="#ffe3a0" stop-opacity=".34"/><stop offset="48%" stop-color="#ffc15e" stop-opacity=".17"/><stop offset="100%" stop-color="#ffad35" stop-opacity="0"/></radialGradient>
              <filter id="lampDiffusion" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="7"/></filter>
              <radialGradient id="pillarLight"><stop offset="0%" stop-color="#ffe6a0" stop-opacity=".65"/><stop offset="55%" stop-color="#ffc65e" stop-opacity=".28"/><stop offset="100%" stop-color="#ffb52e" stop-opacity="0"/></radialGradient>
            </defs>
            <g transform="${direction === "left" ? "translate(400 0) scale(-1 1)" : ""}"><rect x="2" y="2" width="396" height="150" rx="12" fill="url(#sky)"/>
            <path d="M5 130 H395" stroke="#637983" stroke-width="2" opacity=".7"/><path d="M5 141 H395" stroke="#637983" stroke-width="1" opacity=".22"/>
            <g fill="#637983" stroke="#344953" stroke-width="1"><rect x="5" y="47" width="30" height="11" rx="1"/><rect x="5" y="63" width="30" height="11" rx="1"/><rect x="5" y="79" width="30" height="11" rx="1"/><rect x="5" y="95" width="30" height="11" rx="1"/><rect x="298" y="47" width="97" height="11" rx="1"/><rect x="298" y="63" width="97" height="11" rx="1"/><rect x="298" y="79" width="97" height="11" rx="1"/><rect x="298" y="95" width="97" height="11" rx="1"/></g>
            <rect x="34" y="30" width="17" height="100" rx="2" fill="#9aa8ad" stroke="#637983" stroke-width="2"/><path d="M32 30 H53" stroke="#d0d8db" stroke-width="4"/>
            <rect x="279" y="30" width="19" height="100" rx="2" fill="#9aa8ad" stroke="#637983" stroke-width="2"/><path d="M277 30 H300" stroke="#d0d8db" stroke-width="4"/>
            <g class="entrance-light-emission" style="display:${lightingEnabled && entranceLightingActive ? "inline" : "none"}"><ellipse cx="42.5" cy="38" rx="34" ry="42" fill="url(#pillarLight)"/><ellipse cx="288.5" cy="38" rx="36" ry="43" fill="url(#pillarLight)"/><circle cx="42.5" cy="34" r="3.5" fill="#fff0b1"/><circle cx="288.5" cy="34" r="3.5" fill="#fff0b1"/></g>
            <path d="M281 30 V22 Q281 10 288.5 10 Q296 10 296 22 V30 Z"
                  fill="#596a70" stroke="#46565e" stroke-width="1.5"/>
            <g class="beacon-emission ${lampBlink ? "beacon-blink" : ""}" style="opacity:${lamp ? "1" : "0"};animation-delay:${lampBlink ? "-" + lampBlinkPhase.toFixed(3) + "s" : "0s"}">
              <ellipse cx="288.5" cy="27" rx="49" ry="39" fill="url(#lampOuterGlow)" filter="url(#lampDiffusion)"/><ellipse cx="288.5" cy="27" rx="31" ry="25" fill="url(#lampLight)" filter="url(#lampDiffusion)"/>
              <path d="M284 23 V17 Q288.5 12 293 17 V23 Z" fill="#fff0b1"/>
            </g><rect x="280" y="29" width="17" height="4" rx="1" fill="#637983"/>
            <g class="gate-leaf" transform="translate(${shift},0)">
              <rect x="51" y="44" width="228" height="83" fill="url(#gateFill)" stroke="#344953" stroke-width="2"/>
              <path d="M57 49V113 M71.5 49V113 M86 49V113 M100.5 49V113 M115 49V113 M129.5 49V113 M144 49V113 M158.5 49V113 M173 49V113 M187.5 49V113 M202 49V113 M216.5 49V113 M231 49V113 M245.5 49V113 M260 49V113 M274.5 49V113" stroke="#8fa2aa" stroke-width="9" stroke-linecap="butt"/>
              <path d="M57 49V113 M71.5 49V113 M86 49V113 M100.5 49V113 M115 49V113 M129.5 49V113 M144 49V113 M158.5 49V113 M173 49V113 M187.5 49V113 M202 49V113 M216.5 49V113 M231 49V113 M245.5 49V113 M260 49V113 M274.5 49V113" stroke="#425760" stroke-width="1.4" fill="none"/>
              <rect x="51" y="114" width="228" height="6" fill="#344953"/><rect x="51" y="122" width="228" height="5" fill="#526872"/>
              <path d="M279 44 L355 101 L355 127 L279 127 Z" fill="#536a74" fill-opacity=".7" stroke="#344953" stroke-width="3"/><path d="M286 54 L344 101 M286 73 L324 101" stroke="#91a3ab" stroke-width="3" opacity=".75"/>
            </g>
            <!-- Stylizowany napęd BFT DEIMOS ULTRA BT B600: obudowa, logo i dolny panel ULTRA -->
            <g transform="translate(303 94)">
              <path d="M4 6 Q4 2 9 1 L25 1 Q30 2 30 7 L30 29 L4 29 Z"
                    fill="#172b49" stroke="#52647b" stroke-width="1.2"/>
              <path d="M7 5 Q8 3 11 3 H24 Q27 3 28 6 V24 H7 Z"
                    fill="#203958" stroke="#314d6c" stroke-width=".7"/>
              <rect x="15" y="7" width="8" height="5" rx="1" fill="#d9272e" stroke="#f05a5f" stroke-width=".45"/>
              <text x="19" y="10.8" text-anchor="middle" font-size="3.2" font-weight="700" fill="#fff">BFT</text>
              <path d="M4 23 H30 V29 Q30 32 27 32 H7 Q4 32 4 29 Z" fill="#aeb7bd" stroke="#d2d8dc" stroke-width=".7"/>
              <rect x="8" y="24" width="18" height="5.5" rx=".8" fill="#bd202b" stroke="#e35a60" stroke-width=".5"/>
              <text x="13.6" y="27.7" text-anchor="middle" font-size="3.1" font-weight="700" fill="#fff">ULTRA</text>
              <circle cx="23.2" cy="26.8" r="1.45" fill="#c5cbd0" stroke="#5b6268" stroke-width=".45"/>
              <path d="M6 32 H29" stroke="#64717b" stroke-width="1"/>
            </g>
            <g class="photocell-warning" transform="translate(174.5 79)" aria-label="${manualLockActive ? "Ręczna blokada zamknięcia" : "Fotokomórka wykryła przeszkodę"}" style="display:${photocellDanger || manualLockActive ? "inline" : "none"}"><path d="M0 -17 L19 16 H-19 Z" fill="#ffd21f" stroke="#171717" stroke-width="2.2" stroke-linejoin="round"/><path d="M0 -7 V5" stroke="#171717" stroke-width="3.5" stroke-linecap="round"/><circle cx="0" cy="10" r="1.9" fill="#171717"/></g>
            </g>
          </svg>
        </div>
        <div class="manual-lock-label" role="status" style="display:${manualLockActive ? "block" : "none"}">RĘCZNA BLOKADA ZAMKNIĘCIA</div>
        <div class="button-events" aria-live="polite">
          <span class="gate-button-event">Przycisk bramy: ${esc(eventLabel(gateButtonEvent))}</span>
          <span class="wicket-button-event">Przycisk furtki: ${esc(eventLabel(wicketButtonEvent))}</span>
        </div>
        <div class="actions" data-auxiliary-mode="${auxiliaryMode}"><button class="main"><ha-icon icon="mdi:gate"></ha-icon><span>${mainLabel}</span></button>${auxiliaryMarkup}</div>
      </ha-card>`;
    const head = this.shadowRoot.querySelector(".head");
    head.addEventListener("pointerdown", () => this._headerDown());
    for (const event of ["pointerup","pointerleave","pointercancel"]) head.addEventListener(event, () => this._headerUp());
    head.addEventListener("click", () => { if (this._holdFired) { this._holdFired = false; return; } this._moreInfo(this._entity("status")); });
    head.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); this._moreInfo(this._entity("status")); } });
    this._bindActionButtons(pedestrianEnabled, lightingEnabled);
  }
  static getConfigElement() { return document.createElement("brama-przesuwna-bft-card-editor"); }
  static getStubConfig() { return {}; }
}

class BramaPrzesuwnaBFTCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = { name:"Brama wjazdowa", radio:{} };
    this._hass = null;
    this._loading = false;
    this._deviceName = "Nie wykryto sterownika";
    this._registriesLoaded = false;
  }
  setConfig(config) {
    this._config = { name:"Brama wjazdowa", ...config, radio:{...(config?.radio || {})} };
    this._render();
  }
  set hass(value) {
    this._hass = value;
    if (value && !this._registriesLoaded) {
      this._registriesLoaded = true;
      this._autoDetect();
    }
    this._render();
  }
  get hass() { return this._hass; }
  _fire() {
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail:{config:this._config}, bubbles:true, composed:true
    }));
  }
  _norm(v) {
    return String(v||"").normalize("NFKD").replace(/[\u0300-\u036f]/g,"")
      .toLowerCase().replace(/[^a-z0-9]+/g," ").trim();
  }
  async _autoDetect() {
    if (this._loading || !this._hass) return;
    this._loading = true; this._render();
    try {
      const [devices, entities] = await Promise.all([
        this._hass.callWS({type:"config/device_registry/list"}),
        this._hass.callWS({type:"config/entity_registry/list"})
      ]);
      const entityRows = entities || [];
      const candidates = (devices || []).map(d => {
        const owned = entityRows.filter(e => e.device_id === d.id ||
          (e.config_entry_id && (d.config_entries || []).includes(e.config_entry_id)));
        const meta = this._norm([d.manufacturer,d.model,d.name,d.name_by_user,
          ...(d.identifiers || []).flat(), ...(d.connections || []).flat()].join(" "));
        const entityText = this._norm(owned.map(e => [e.entity_id,e.original_name,e.name].join(" ")).join(" "));
        const hasStatus = /dokladny stan bramy/.test(entityText);
        const hasPosition = /pozycja bramy/.test(entityText);
        const hasMain = /otworz zamknij brame/.test(entityText);
        const hasPedestrian = /otworz jako furtke/.test(entityText);
        const isESPHome = owned.some(e => e.platform === "esphome");
        const exactProject = /marlip1981|brama przesuwna bft/.test(meta);
        const explicitBFT = /bft|deimos/.test(meta);
        const entityFingerprint = isESPHome && ((hasStatus && hasPosition) ||
          (hasMain && hasPedestrian) || (hasStatus && hasMain && hasPosition));
        let score = 0;
        if (exactProject) score += 100;
        if (explicitBFT) score += 40;
        if (entityFingerprint) score += 60;
        if (hasStatus) score += 12;
        if (hasPosition) score += 12;
        if (hasMain) score += 8;
        if (hasPedestrian) score += 8;
        if (isESPHome) score += 5;
        return {device:d,owned,score,eligible:exactProject || (explicitBFT && isESPHome) || entityFingerprint};
      }).filter(c => c.eligible).sort((a,b) => b.score-a.score);
      const candidate = candidates[0];
      if (!candidate) {
        this._deviceName = "Nie wykryto sterownika BFT. Wymagane są dane projektu BFT lub charakterystyczny zestaw encji ESPHome.";
        return;
      }
      if (candidates.length > 1 && candidates[0].score === candidates[1].score) {
        this._deviceName = "Wykryto kilka możliwych sterowników BFT. Wybierz encje ręcznie.";
        return;
      }
      this._deviceName = candidate.device.name_by_user || candidate.device.name || "Sterownik bramy BFT";
      for (const [role, rule] of Object.entries(ROLES)) {
        if (this._config.radio[role]) continue;
        const match = candidate.owned.find(e => rule.domains.includes(e.entity_id.split(".")[0]) &&
          rule.test.test(this._norm([e.entity_id,e.original_name,e.name].join(" "))));
        if (match) this._config.radio[role] = match.entity_id;
      }
      this._fire();
    } catch(err) {
      console.warn("Brama BFT: nie udało się pobrać rejestrów HA", err);
      this._deviceName = "Błąd odczytu rejestru urządzeń HA. Możesz ponowić wykrywanie.";
    } finally {
      this._loading = false;
      this._render();
    }
  }
  _set(key,value) {
    this._config = {...this._config,radio:{...this._config.radio,[key]:value}};
    this._fire(); this._render();
  }
  _options(role) {
    const domains = ROLES[role].domains;
    return Object.values(this._hass?.states || {})
      .filter(s => domains.includes(s.entity_id.split(".")[0]))
      .sort((a,b) => a.entity_id.localeCompare(b.entity_id));
  }
  _render() {
    if (!this.shadowRoot) return;
    const options = role => this._options(role).map(s =>
      `<option value="${esc(s.entity_id)}" ${this._config.radio[role]===s.entity_id?"selected":""}>${esc(s.attributes?.friendly_name||s.entity_id)} — ${esc(s.entity_id)}</option>`
    ).join("");
    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;color:var(--primary-text-color)}.field{display:block;margin:12px 0}
        label{display:block;margin-bottom:5px;color:var(--secondary-text-color)}
        select,input{box-sizing:border-box;width:100%;padding:10px;color:var(--primary-text-color);background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:8px;font:inherit}
        button{padding:10px 14px;border:0;border-radius:8px;background:var(--secondary-background-color);color:var(--primary-text-color);font:inherit;cursor:pointer}
        button:disabled{opacity:.5}.hint{color:var(--secondary-text-color);font-size:12px}
      </style>
      <p class="hint">${this._loading?"Wykrywanie sterownika i encji…":esc(this._deviceName)}</p>
      <div class="field"><button class="detect" ${this._loading?"disabled":""}>Wykryj sterownik ponownie</button></div>
      ${Object.entries(ROLES).map(([role,meta])=>`
        <div class="field"><label>${meta.label}</label><select data-role="${role}">
          <option value="">— wybierz encję —</option>${options(role)}
        </select></div>`).join("")}
      <p class="hint">Najpierw wybierz sterownik i sprawdź przypisane encje. Automatyczne przypisanie dotyczy wyłącznie encji sterownika BFT; listy pozwalają też wskazać je ręcznie. Fizyczne przyciski bramy i furtki rozróżniają krótkie naciśnięcie oraz długie przytrzymanie; karta pokazuje ostatnio rozpoznane zdarzenie, jeśli firmware udostępnia odpowiednie sensory.</p>
      <div class="field"><label>Nazwa karty</label><input class="name" value="${esc(this._config.name||"")}"></div>
      <div class="field"><label>Tryb lampki na tej karcie</label><select class="lamp-mode">
        <option value="integration" ${(!this._config.lamp_mode || this._config.lamp_mode==="integration")?"selected":""}>Użyj ustawienia integracji</option>
        <option value="auto" ${this._config.lamp_mode==="auto"?"selected":""}>Automatyczny — miga podczas zamykania</option>
        <option value="always_blink" ${this._config.lamp_mode==="always_blink"?"selected":""}>Zawsze miga podczas ruchu bramy</option>
        <option value="no_blink" ${this._config.lamp_mode==="no_blink"?"selected":""}>Bez migania — świeci ciągle podczas ruchu</option>
      </select></div>
`;
    this.shadowRoot.querySelector(".name")?.addEventListener("change", e => {
      this._config = {...this._config,name:e.target.value}; this._fire();
    });
    this.shadowRoot.querySelector(".lamp-mode")?.addEventListener("change", e => {
      this._config = {...this._config,lamp_mode:e.target.value}; this._fire(); this._render();
    });
    this.shadowRoot.querySelector(".detect")?.addEventListener("click", () => this._autoDetect());
    this.shadowRoot.querySelectorAll("select[data-role]").forEach(el =>
      el.addEventListener("change", e => this._set(e.target.dataset.role,e.target.value)));
  }
}

if (!customElements.get("brama-przesuwna-bft-card")) customElements.define("brama-przesuwna-bft-card", BramaPrzesuwnaBFTCard);
if (!customElements.get("brama-przesuwna-bft-card-editor")) customElements.define("brama-przesuwna-bft-card-editor", BramaPrzesuwnaBFTCardEditor);
window.customCards = window.customCards || [];
if (!window.customCards.some(card => card.type === "brama-przesuwna-bft-card")) {
  window.customCards.push({
    type: "brama-przesuwna-bft-card",
    name: "Brama przesuwna BFT",
    description: "Karta sterowania bramą i furtką.",
    preview: false,
    getEntitySuggestion: (hass, entityId) => {
      const state = hass?.states?.[entityId];
      const label = state?.attributes?.friendly_name || "";
      const searchable = normalize(`${entityId} ${label}`);
      const isGateEntity = Object.values(ROLES).some(role => role.test.test(searchable));
      if (!isGateEntity) return null;
      return {
        config: { type: "custom:brama-przesuwna-bft-card" },
      };
    },
  });
}
};

// add_extra_js_url modules can run before HA replaces the native registry with
// its scoped-registry polyfill. Waiting only for window.load is not sufficient:
// the app entrypoint is itself loaded asynchronously. Detect the final registry,
// then wait for HA's root element before defining this card.
const registerAfterHomeAssistantReady = async () => {
  const initialRegistry = window.customElements;
  await new Promise((resolve) => {
    const checkRegistry = () => {
      const registry = window.customElements;
      if (registry !== initialRegistry || registry.get("home-assistant")) {
        resolve();
        return;
      }
      window.setTimeout(checkRegistry, 25);
    };
    checkRegistry();
  });

  await window.customElements.whenDefined("home-assistant");
  registerBramaCard();
};

const scheduleRegistration = () => {
  registerAfterHomeAssistantReady().catch((error) => {
    console.error("Brama przesuwna BFT: nie udało się zarejestrować karty", error);
  });
};

if (document.readyState === "complete") {
  window.setTimeout(scheduleRegistration, 0);
} else {
  window.addEventListener("load", scheduleRegistration, { once: true });
}
})();
