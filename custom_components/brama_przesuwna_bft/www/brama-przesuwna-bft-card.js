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
    const pedestrianEnabled = mode?.state === "on" && Boolean(pedestrianButton);
    const direction = mode?.attributes?.opening_direction || "right";
    const mainLabel = open ? "Zamknij bramę" : closed ? "Otwórz bramę" : "Steruj bramą";
    const slide = (direction === "right" ? 1 : -1) * pos * 1.42;
    const lampOn = moving || open;
    const statusClass = moving ? "moving" : open ? "open" : closed ? "closed" : "";
    this.shadowRoot.innerHTML = \`
      <style>
        :host{display:block;color:var(--primary-text-color)}
        ha-card{display:block;padding:16px;overflow:hidden;background:var(--ha-card-background,var(--card-background-color));border-radius:var(--ha-card-border-radius,12px);box-shadow:var(--ha-card-box-shadow,none)}
        .head{display:flex;justify-content:space-between;align-items:center;gap:12px;cursor:pointer;user-select:none}
        h2{font-size:20px;margin:0;font-weight:500}.status{font-weight:600;text-align:right;display:flex;align-items:center;gap:8px}
        .dot{width:9px;height:9px;border-radius:50%;display:inline-block;background:var(--secondary-text-color)}
        .status.closed .dot{background:#43a047}.status.open .dot{background:#e53935;box-shadow:0 0 8px #e5393580}
        .status.moving .dot{background:#ffb300;box-shadow:0 0 8px #ffb30080}
        .scene{margin:12px 0 10px;padding:5px 0 0;border-radius:12px;background:var(--secondary-background-color);border:1px solid var(--divider-color);overflow:hidden}
        svg{display:block;width:100%;height:auto;max-height:230px}
        .gate-leaf{transform:translateX(\${slide}px);transition:transform 1.2s cubic-bezier(.2,.75,.25,1)}
        .lamp-glow{opacity:\${lampOn ? ".95" : "0"};transition:opacity .45s ease}
        .lamp-core{fill:\${lampOn ? "#ffd56a" : "#9a6b20"};transition:fill .35s ease}
        .meta{color:var(--secondary-text-color);font-size:13px;margin:5px 2px 9px}
        .actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}.actions.single{grid-template-columns:1fr}
        button{min-height:48px;border:0;border-radius:14px;padding:10px;background:var(--primary-color);color:var(--text-primary-color);font:inherit;font-weight:600;cursor:pointer}
        button.secondary{background:var(--secondary-background-color);color:var(--primary-text-color)}
      </style>
      <ha-card>
        <div class="head" role="button" tabindex="0">
          <h2>\${esc(this._config.name)}</h2>
          <div class="status \${statusClass}"><span class="dot"></span><span>\${esc(status)}\${moving && valid ? \` · \${pos}%\` : ""}</span></div>
        </div>
        <div class="scene">
          <svg viewBox="0 0 400 190" role="img" aria-label="Ilustracja bramy przesuwnej z napędem BFT">
            <defs>
              <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#aeb5b8"/><stop offset="1" stop-color="#747d82"/></linearGradient>
              <linearGradient id="gateFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#59636a"/><stop offset=".5" stop-color="#303a40"/><stop offset="1" stop-color="#1e272c"/></linearGradient>
              <linearGradient id="motorBody" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#42494d"/><stop offset=".45" stop-color="#202629"/><stop offset="1" stop-color="#101416"/></linearGradient>
              <linearGradient id="ground" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#737b7d"/><stop offset="1" stop-color="#444b4d"/></linearGradient>
              <linearGradient id="lampBeam" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffd978" stop-opacity=".5"/><stop offset=".6" stop-color="#ffca55" stop-opacity=".17"/><stop offset="1" stop-color="#ffbf42" stop-opacity="0"/></linearGradient>
              <filter id="softSpill" x="-80%" y="-100%" width="260%" height="300%"><feGaussianBlur stdDeviation="8"/></filter>
              <filter id="lampBloom" x="-150%" y="-150%" width="400%" height="400%"><feGaussianBlur stdDeviation="3"/></filter>
              <filter id="motorShadow" x="-30%" y="-30%" width="160%" height="180%"><feGaussianBlur stdDeviation="3"/></filter>
              <clipPath id="sceneClip"><rect width="400" height="190" rx="10"/></clipPath>
            </defs>
            <g clip-path="url(#sceneClip)">
              <rect width="400" height="190" fill="#899397"/>
              <path d="M0 142H400V190H0Z" fill="url(#ground)"/><path d="M0 142H400" stroke="#c0c6c7" stroke-opacity=".5" stroke-width="2"/>
              <g class="lamp-glow">
                <path d="M43 49 C66 52 87 67 104 89 C117 106 128 120 144 137 C119 132 96 121 77 105 C58 89 47 70 43 49Z" fill="url(#lampBeam)" filter="url(#softSpill)"/>
                <path d="M45 48 C64 56 82 69 97 88 C108 102 119 117 128 128" fill="none" stroke="#ffd36a" stroke-opacity=".3" stroke-width="12" stroke-linecap="round" filter="url(#lampBloom)"/>
              </g>
              <path d="M0 74H400V112H0Z" fill="url(#wall)" opacity=".48"/>
              <path d="M18 43H65V151H18Z" fill="#687277"/><path d="M22 47H61V146H22Z" fill="url(#wall)"/>
              <path d="M330 43H378V151H330Z" fill="#687277"/><path d="M334 47H374V146H334Z" fill="url(#wall)"/>
              <path d="M14 40H68V49H14Z M326 40H382V49H326Z" fill="#d0d4d4"/>
              <path d="M62 145H344" stroke="#1c2428" stroke-width="5"/>
              <g class="gate-leaf">
                <rect x="62" y="65" width="267" height="78" rx="1" fill="url(#gateFill)" stroke="#172024" stroke-width="2"/>
                <path d="M70 68V140 M84 68V140 M98 68V140 M112 68V140 M126 68V140 M140 68V140 M154 68V140 M168 68V140 M182 68V140 M196 68V140 M210 68V140 M224 68V140 M238 68V140 M252 68V140 M266 68V140 M280 68V140 M294 68V140 M308 68V140 M322 68V140" stroke="#899398" stroke-opacity=".38" stroke-width="2"/>
                <path d="M62 65H329 M62 143H329" stroke="#b2b9bb" stroke-opacity=".42" stroke-width="2"/>
                <path d="M62 65L79 78V130L62 143Z" fill="#202a2f" opacity=".8"/>
              </g>
              <!-- stationary foreground BFT DEIMOS ULTRA operator -->
              <ellipse cx="310" cy="157" rx="39" ry="7" fill="#101516" opacity=".45" filter="url(#motorShadow)"/>
              <path d="M280 111L289 102Q292 99 299 99H330Q337 99 340 106L346 119V151Q346 157 340 159H289Q281 158 280 151Z" fill="#111719" stroke="#080c0d" stroke-width="2"/>
              <path d="M284 111L292 104Q295 102 301 102H328Q334 102 337 108L342 120V148Q342 153 337 154H290Q285 153 284 148Z" fill="url(#motorBody)" stroke="#566065" stroke-width="1"/>
              <path d="M290 108H328Q332 108 335 113L338 119H288Z" fill="#525b60" opacity=".42"/>
              <path d="M287 121H339V146Q339 150 334 150H292Q287 150 287 146Z" fill="#202629" stroke="#0b1012" stroke-width="1"/>
              <path d="M294 111H326Q330 111 330 115V119H294Z" fill="#b8bec0" opacity=".92"/>
              <text x="312" y="118" text-anchor="middle" font-size="8" font-weight="800" fill="#b51f2b" letter-spacing="1">BFT</text>
              <path d="M294 126H331V141H294Z" fill="#252c30" stroke="#687176" stroke-width=".8"/><path d="M298 129H327V136H298Z" fill="#a71f2b"/>
              <text x="312.5" y="134.5" text-anchor="middle" font-size="5.8" font-weight="800" fill="#f2eeee" letter-spacing=".8">ULTRA</text>
              <circle cx="333" cy="143" r="3.1" fill="#aeb5b7" stroke="#080c0d" stroke-width="1"/><path d="M332 141L334 145" stroke="#333a3d" stroke-width="1"/>
              <path d="M280 151H346V157H280Z" fill="#171d20"/><path d="M286 157H340L336 162H291Z" fill="#343c40"/>
              <!-- beacon -->
              <path d="M35 37H49V45H35Z" fill="#343c3f"/>
              <rect x="34" y="27" width="16" height="12" rx="3" fill="#333b3e" stroke="#171d20" stroke-width="1.5"/>
              <rect x="36" y="29" width="12" height="7" rx="2" class="lamp-core"/>
              <path d="M36 38H48" stroke="#111719" stroke-width="1.5"/><path d="M31 42H53" stroke="#252d30" stroke-width="2"/>
              <text x="200" y="178" text-anchor="middle" font-size="9" fill="#f0f2f2" opacity=".75">BRAMA PRZESUWNA</text>
            </g>
          </svg>
        </div>
        <div class="meta">Pozycja bramy: <strong>\${valid ? pos + "%" : "brak danych"}</strong> · Kierunek: \${direction === "right" ? "w prawo" : "w lewo"} (od strony podwórka)</div>
        <div class="actions \${pedestrianEnabled ? "" : "single"}">
          <button class="main">\${mainLabel}</button>
          \${pedestrianEnabled ? '<button class="secondary pedestrian">Otwórz furtkę</button>' : ""}
        </div>
      </ha-card>\`;
    const head = this.shadowRoot.querySelector(".head");
    head.addEventListener("pointerdown", () => this._headerDown());
    for (const event of ["pointerup","pointerleave","pointercancel"]) head.addEventListener(event, () => this._headerUp());
    head.addEventListener("click", () => {
      if (this._holdFired) { this._holdFired = false; return; }
      this._moreInfo(this._entity("status"));
    });
    head.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); this._moreInfo(this._entity("status")); }
    });
    this.shadowRoot.querySelector(".main").addEventListener("click", () => this._press(mainButton));
    this.shadowRoot.querySelector(".pedestrian")?.addEventListener("click", () => this._press(pedestrianButton));
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
