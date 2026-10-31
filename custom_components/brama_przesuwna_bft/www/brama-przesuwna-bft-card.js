/* Brama przesuwna BFT — native Web Components, no Lit dependency. */
(() => {
const registerBramaCard = () => {
const ROLES = {
  status: { label: "Stan bramy", domains: ["sensor"], test: /dokladny stan bramy|dokladny stan|stan bramy|gate status/i },
  position: { label: "Pozycja bramy", domains: ["sensor"], test: /pozycja bramy|pozycja|position/i },
  main_button: { label: "Sterowanie bramą", domains: ["button"], test: /otworz zamknij brame|otworz zamknij|sterowanie brama|gate/i },
  pedestrian_button: { label: "Sterowanie furtką", domains: ["button"], test: /otworz jako furtke|furtk|pedestrian/i },
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
  }
  setConfig(config) {
    this._config = {
      name: config.name || "Brama wjazdowa",
      radio: { ...(config.radio || {}) },
      status_entity: config.status_entity || "",
      position_entity: config.position_entity || "",
      main_button: config.main_button || "",
      pedestrian_button: config.pedestrian_button || "",
    };
    this._render();
  }
  set hass(value) { this._hass = value; this._render(); }
  get hass() { return this._hass; }
  getCardSize() { return 3; }
  _entity(role) {
    const legacyKey = ({status:"status_entity",position:"position_entity",main_button:"main_button",pedestrian_button:"pedestrian_button"})[role];
    return this._config?.radio?.[role] || this._config?.[legacyKey] ||
      this._hass?.states?.[MODE_ENTITY]?.attributes?.entities?.[role] || "";
  }
  _state(id) { return this._hass?.states?.[id]?.state; }
  _press(id) { if (id && this._hass) this._hass.callService("button", "press", { entity_id: id }); }
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
    // Labels and actions follow the original YAML card state machine.
    const mainLabel = moving ? "Brama - Stop" : open ? "Brama - Zamknij" :
      closed ? "Brama - Otwórz" : "Brama - Steruj";
    const pedestrianLabel = open ? "Furtka - Zamknij" : "Furtka - Otwórz";
    const shift = 1.9 * pos * (direction === "right" ? 1 : -1), lamp = moving || open;
    const statusClass = moving ? "moving" : open ? "open" : closed ? "closed" : "";
    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;color:var(--primary-text-color)}
        ha-card{display:block;padding:12px;overflow:hidden;border-radius:22px;background:var(--ha-card-background,var(--card-background-color));box-shadow:var(--ha-card-box-shadow,none)}
        .head{display:flex;justify-content:space-between;align-items:center;gap:8px;cursor:pointer;user-select:none;padding:4px}
        h2{font-size:20px;margin:0;font-weight:600}.status{font-size:14px;font-weight:500;text-align:right;white-space:nowrap}
        .status.closed{color:#42c878}.status.open{color:#ff4545;font-weight:800;text-shadow:0 0 8px rgba(255,50,50,.65)}.status.moving{color:#ffbd4a}
        .scene{width:100%;margin:0;overflow:hidden}svg{display:block;width:100%;height:155px}
        .gate-leaf{transition:transform 1.05s linear}.lamp-glow{opacity:${lamp ? "1" : "0"};transition:opacity .45s ease}
        .actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}
        button{min-height:48px;border:0;border-radius:16px;padding:14px;background:var(--secondary-background-color);color:var(--primary-text-color);font:inherit;font-weight:600;cursor:pointer}
        button.main{color:#429ee8}
        button.pedestrian{color:#39b982}
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
              <linearGradient id="lampLight" x1="0" y1="0" x2=".8" y2="1"><stop offset="0%" stop-color="#fff0b1" stop-opacity=".38"/><stop offset="45%" stop-color="#ffbd58" stop-opacity=".17"/><stop offset="100%" stop-color="#ff9d28" stop-opacity="0"/></linearGradient>
              <filter id="lampDiffusion" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="7"/></filter>
            </defs>
            <rect x="2" y="2" width="396" height="150" rx="12" fill="url(#sky)"/>
            <path d="M5 130 H395" stroke="#637983" stroke-width="2" opacity=".7"/><path d="M5 141 H395" stroke="#637983" stroke-width="1" opacity=".22"/>
            <g fill="#637983" stroke="#344953" stroke-width="1"><rect x="5" y="47" width="30" height="11" rx="1"/><rect x="5" y="63" width="30" height="11" rx="1"/><rect x="5" y="79" width="30" height="11" rx="1"/><rect x="5" y="95" width="30" height="11" rx="1"/><rect x="298" y="47" width="97" height="11" rx="1"/><rect x="298" y="63" width="97" height="11" rx="1"/><rect x="298" y="79" width="97" height="11" rx="1"/><rect x="298" y="95" width="97" height="11" rx="1"/></g>
            <rect x="34" y="30" width="17" height="100" rx="2" fill="#9aa8ad" stroke="#637983" stroke-width="2"/><path d="M32 30 H53" stroke="#d0d8db" stroke-width="4"/>
            <rect x="279" y="30" width="19" height="100" rx="2" fill="#9aa8ad" stroke="#637983" stroke-width="2"/><path d="M277 30 H300" stroke="#d0d8db" stroke-width="4"/>
            <g class="lamp-glow"><path d="M288 20 C275 28 263 37 252 48 C242 58 233 70 224 82 C247 75 266 63 279 48 C286 39 290 29 288 20Z" fill="url(#lampLight)" filter="url(#lampDiffusion)"/></g>
            <path d="M281 30 V22 Q281 10 288.5 10 Q296 10 296 22 V30 Z" fill="${lamp ? "#ffad35" : "#687780"}" stroke="${lamp ? "#ffca75" : "#46565e"}" stroke-width="1.5"/>
            <path d="M284 23 V17 Q288.5 12 293 17 V23 Z" fill="${lamp ? "#fff0b1" : "#839097"}" opacity="${lamp ? "1" : ".45"}"/><rect x="280" y="29" width="17" height="4" rx="1" fill="#637983"/>
            <g class="gate-leaf" transform="translate(${shift},0)">
              <rect x="51" y="44" width="228" height="83" fill="url(#gateFill)" stroke="#344953" stroke-width="2"/>
              <path d="M57 49V113 M71.5 49V113 M86 49V113 M100.5 49V113 M115 49V113 M129.5 49V113 M144 49V113 M158.5 49V113 M173 49V113 M187.5 49V113 M202 49V113 M216.5 49V113 M231 49V113 M245.5 49V113 M260 49V113 M274.5 49V113" stroke="#8fa2aa" stroke-width="9" stroke-linecap="round"/>
              <path d="M57 49V113 M71.5 49V113 M86 49V113 M100.5 49V113 M115 49V113 M129.5 49V113 M144 49V113 M158.5 49V113 M173 49V113 M187.5 49V113 M202 49V113 M216.5 49V113 M231 49V113 M245.5 49V113 M260 49V113 M274.5 49V113" stroke="#425760" stroke-width="1.4" fill="none"/>
              <rect x="51" y="114" width="228" height="6" fill="#344953"/><rect x="51" y="122" width="228" height="5" fill="#526872"/>
              <path d="M279 44 L355 101 L355 127 L279 127 Z" fill="#536a74" fill-opacity=".7" stroke="#344953" stroke-width="3"/><path d="M286 54 L344 101 M286 73 L324 101" stroke="#91a3ab" stroke-width="3" opacity=".75"/>
            </g>
            <!-- Napęd zachowuje oryginalne położenie i wymiary; jest tylko rysowany po skrzydle -->
            <g><rect x="290" y="108" width="24" height="19" rx="3" fill="#263943" stroke="#71858e" stroke-width="1.5"/><path d="M295 114 H309 M295 119 H309" stroke="#84969d" stroke-width="1.5"/></g>
          </svg>
        </div>
        <div class="actions"><button class="main"><ha-icon icon="mdi:gate"></ha-icon><span>${mainLabel}</span></button><button class="pedestrian"><ha-icon icon="mdi:walk"></ha-icon><span>${pedestrianLabel}</span></button></div>
      </ha-card>`;
    const head = this.shadowRoot.querySelector(".head");
    head.addEventListener("pointerdown", () => this._headerDown());
    for (const event of ["pointerup","pointerleave","pointercancel"]) head.addEventListener(event, () => this._headerUp());
    head.addEventListener("click", () => { if (this._holdFired) { this._holdFired = false; return; } this._moreInfo(this._entity("status")); });
    head.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); this._moreInfo(this._entity("status")); } });
    this.shadowRoot.querySelector(".main").addEventListener("click", () => this._press(mainButton));
    this.shadowRoot.querySelector(".pedestrian").addEventListener("click", () =>
      this._press(open ? mainButton : pedestrianButton));
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
      <div class="field"><label>Nazwa karty</label><input class="name" value="${esc(this._config.name||"")}"></div>
      <p class="hint">${this._loading?"Wykrywanie sterownika i encji…":esc(this._deviceName)}</p>
      <div class="field"><button class="detect" ${this._loading?"disabled":""}>Wykryj sterownik ponownie</button></div>
      ${Object.entries(ROLES).map(([role,meta])=>`
        <div class="field"><label>${meta.label}</label><select data-role="${role}">
          <option value="">— wybierz encję —</option>${options(role)}
        </select></div>`).join("")}
      <p class="hint">Automatyczne przypisanie dotyczy wyłącznie encji sterownika BFT. Listy pozwalają też wskazać ręcznie dowolną encję właściwej domeny.</p>`;
    this.shadowRoot.querySelector(".name")?.addEventListener("change", e => {
      this._config = {...this._config,name:e.target.value}; this._fire();
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
