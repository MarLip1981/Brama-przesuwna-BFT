/* Brama przesuwna BFT — native Web Components, no Lit dependency. */
const ROLES = {
  status: { label: "Stan bramy", domains: ["sensor"], test: /dokladny stan bramy|dokladny stan|stan bramy|gate status/i },
  position: { label: "Pozycja bramy", domains: ["sensor"], test: /pozycja bramy|pozycja|position/i },
  main_button: { label: "Sterowanie bramą", domains: ["button"], test: /otworz zamknij brame|otworz zamknij|sterowanie brama|gate/i },
  pedestrian_button: { label: "Sterowanie furtką", domains: ["button"], test: /otworz jako furtke|furtk|pedestrian/i },
};
const MODE_ENTITY = "binary_sensor.brama_przesuwna_bft_tryb_furtki";
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

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
    const pos = valid ? Math.max(0, Math.min(100, Math.round(n))) : null;
    const status = this._state(statusId) || "Brak stanu";
    const moving = /otwieranie|zamykanie/i.test(status), open = /otwarta/i.test(status), closed = /zamknięta/i.test(status);
    const pedestrianEnabled = mode?.state === "on" && Boolean(pedestrianButton);
    const direction = mode?.attributes?.opening_direction || "right";
    const mainLabel = open ? "Zamknij bramę" : closed ? "Otwórz bramę" : "Steruj bramą";
    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;color:var(--primary-text-color)}
        ha-card{display:block;padding:16px;overflow:hidden;background:var(--ha-card-background,var(--card-background-color));border-radius:var(--ha-card-border-radius,12px);box-shadow:var(--ha-card-box-shadow,none)}
        .head{display:flex;justify-content:space-between;align-items:center;gap:12px;cursor:pointer;user-select:none}
        h2{font-size:20px;margin:0;font-weight:500}.status{font-weight:600;text-align:right}
        .scene{margin:12px 0;padding:12px;border-radius:12px;background:var(--ha-card-background,var(--card-background-color));border:1px solid var(--divider-color)}
        .meta{color:var(--secondary-text-color);font-size:13px;margin-top:5px}
        .actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}.actions.single{grid-template-columns:1fr}
        button{min-height:48px;border:0;border-radius:14px;padding:10px;background:var(--primary-color);color:var(--text-primary-color);font:inherit;font-weight:600;cursor:pointer}
        button.secondary{background:var(--secondary-background-color);color:var(--primary-text-color)}
      </style>
      <ha-card>
        <div class="head" role="button" tabindex="0">
          <h2>${esc(this._config.name)}</h2><div class="status">${esc(status)}${moving && pos !== null ? ` · ${pos}%` : ""}</div>
        </div>
        <div class="scene">
          <div>Pozycja bramy: <strong>${pos === null ? "brak danych" : pos + "%"}</strong></div>
          <div class="meta">Kierunek otwierania: ${direction === "right" ? "w prawo" : "w lewo"} (patrząc od strony podwórka). Pozycja szacowana na podstawie czasu ruchu.</div>
        </div>
        <div class="actions ${pedestrianEnabled ? "" : "single"}">
          <button class="main">${mainLabel}</button>
          ${pedestrianEnabled ? '<button class="secondary pedestrian">Otwórz furtkę</button>' : ""}
        </div>
      </ha-card>`;
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
  });
}
