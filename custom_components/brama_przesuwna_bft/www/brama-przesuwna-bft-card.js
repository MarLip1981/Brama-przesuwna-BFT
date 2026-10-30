import { LitElement, html, css } from "lit";

const PROJECT_MANUFACTURER = "MarLip1981";
const PROJECT_MODEL = "BramaPrzesuwnaBFT";
const ROLES = {
  status: { label: "Stan bramy", domains: ["sensor"], test: /dokladny stan bramy|dokladny stan|stan bramy|gate status/i },
  position: { label: "Pozycja bramy", domains: ["sensor"], test: /pozycja bramy|pozycja|position/i },
  main_button: { label: "Sterowanie bramą", domains: ["button"], test: /otworz zamknij brame|otworz zamknij|sterowanie brama|gate/i },
  pedestrian_button: { label: "Sterowanie furtką", domains: ["button"], test: /otworz jako furtke|furtk|pedestrian/i },
};
const DEFAULTS = {
  status: "sensor.brama_wjazdowa_dokladny_stan_bramy",
  position: "sensor.wjazd_brama_wjazdowa_pozycja_bramy",
  main_button: "button.wjazd_brama_wjazdowa_otworz_zamknij_brame",
  pedestrian_button: "button.wjazd_brama_wjazdowa_otworz_jako_furtke",
};
const MODE_ENTITY = "binary_sensor.brama_przesuwna_bft_tryb_furtki";

class BramaPrzesuwnaBFTCard extends LitElement {
  static properties = { hass: {}, _config: {} };
  static styles = css`
    :host { display:block; }
    ha-card { padding:16px; overflow:hidden; }
    .head { display:flex; justify-content:space-between; align-items:center; gap:12px; cursor:pointer; }
    h2 { font-size:20px; margin:0; }
    .status { font-weight:600; text-align:right; }
    .scene { margin:12px 0; padding:12px; border-radius:12px; background:var(--ha-card-background,var(--card-background-color)); border:1px solid var(--divider-color); }
    .track { height:12px; border-radius:8px; background:var(--disabled-color); overflow:hidden; margin-top:10px; }
    .position { height:100%; background:var(--primary-color); transition:width .3s ease; }
    .track.right .position { margin-left:auto; }
    .meta { color:var(--secondary-text-color); font-size:13px; margin-top:5px; }
    .actions { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
    .actions.single { grid-template-columns:1fr; }
    button { min-height:48px; border:0; border-radius:14px; padding:10px; background:var(--primary-color); color:var(--text-primary-color); font:inherit; font-weight:600; cursor:pointer; }
    button.secondary { background:var(--secondary-background-color); color:var(--primary-text-color); }
    button:disabled { opacity:.45; cursor:not-allowed; }
  `;
  setConfig(config) {
    this._config = { name: config.name || "Brama wjazdowa", radio: { ...(config.radio || {}) },
      status_entity: config.status_entity || "", position_entity: config.position_entity || "",
      main_button: config.main_button || "", pedestrian_button: config.pedestrian_button || "" };
  }
  getCardSize() { return 3; }
  _entity(role) { return this._config?.radio?.[role] || this._config?.[({status:"status_entity",position:"position_entity",main_button:"main_button",pedestrian_button:"pedestrian_button"})[role]] || DEFAULTS[role]; }
  _state(id) { return this.hass?.states?.[id]?.state; }
  _press(id) { if (id && this.hass) this.hass.callService("button", "press", { entity_id: id }); }
  _moreInfo(id) { if (id) this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId: id }, bubbles: true, composed: true })); }
  _headerDown() { this._holdFired = false; clearTimeout(this._holdTimer); this._holdTimer = setTimeout(() => { this._holdFired = true; this._moreInfo(this._entity("position")); }, 600); }
  _headerUp() { clearTimeout(this._holdTimer); }
  _headerClick() { if (this._holdFired) { this._holdFired = false; return; } this._moreInfo(this._entity("status")); }
  render() {
    if (!this._config || !this.hass) return html``;
    const mode = this.hass.states?.[MODE_ENTITY];
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
    return html`
      <ha-card>
        <div class="head" @pointerdown=${() => this._headerDown()} @pointerup=${() => this._headerUp()} @pointerleave=${() => this._headerUp()} @pointercancel=${() => this._headerUp()} @click=${() => this._headerClick()}>
          <h2>${this._config.name}</h2><div class="status">${status}${moving && pos !== null ? html` · ${pos}%` : ""}</div>
        </div>
        <div class="scene">
          <div>Pozycja bramy: <strong>${pos === null ? "brak danych" : `${pos}%`}</strong></div>
          <div class="track ${direction === "right" ? "right" : "left"}"><div class="position" style="width:${pos ?? 0}%"></div></div>
          <div class="meta">Kierunek otwierania: ${direction === "right" ? "w prawo" : "w lewo"} (patrząc od strony podwórka). Pozycja szacowana na podstawie czasu ruchu.</div>
        </div>
        <div class="actions ${pedestrianEnabled ? "" : "single"}">
          <button @click=${() => this._press(mainButton)}>${mainLabel}</button>
          ${pedestrianEnabled ? html`<button class="secondary" @click=${() => this._press(pedestrianButton)}>Otwórz furtkę</button>` : ""}
        </div>
      </ha-card>`;
  }
  static getConfigElement() { return document.createElement("brama-przesuwna-bft-card-editor"); }
  static getStubConfig() { return {}; }
}

class BramaPrzesuwnaBFTCardEditor extends LitElement {
  static properties = { hass: {}, _config: {}, _loading: {state:true}, _deviceName: {state:true} };
  static styles = css`
    :host { display:block; } .field { display:block; margin:12px 0; }
    label { display:block; margin-bottom:5px; color:var(--secondary-text-color); }
    select,input { box-sizing:border-box; width:100%; padding:10px; color:var(--primary-text-color); background:var(--card-background-color); border:1px solid var(--divider-color); border-radius:8px; }
    .hint { color:var(--secondary-text-color); font-size:12px; }
  `;
  constructor() { super(); this._config = { name:"Brama wjazdowa", radio:{} }; this._loading=false; this._deviceName="Nie wykryto sterownika"; this._registriesLoaded=false; }
  setConfig(config) { this._config = { name:"Brama wjazdowa", ...config, radio:{...(config?.radio || {})} }; }
  set hass(hass) { this._hass=hass; if (hass && !this._registriesLoaded) { this._registriesLoaded=true; this._autoDetect().then(()=>this.requestUpdate()); } }
  get hass() { return this._hass; }
  _fire() { this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:this._config},bubbles:true,composed:true})); }
  _norm(v) { return String(v||"").normalize("NFKD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim(); }
  async _autoDetect() {
    this._loading=true; this.requestUpdate();
    try {
      const [devices, entities] = await Promise.all([
        this._hass.callWS({type:"config/device_registry/list"}),
        this._hass.callWS({type:"config/entity_registry/list"})
      ]);
      const device = (devices||[]).find(d => String(d.manufacturer||"").toLowerCase()===PROJECT_MANUFACTURER.toLowerCase() &&
        this._norm(d.model)===this._norm(PROJECT_MODEL));
      if (!device) { this._deviceName="Nie znaleziono urządzenia MarLip1981.BramaPrzesuwnaBFT"; return; }
      this._deviceName=device.name_by_user || device.name || "Brama przesuwna BFT";
      const owned=(entities||[]).filter(e=>e.device_id===device.id && e.platform==="esphome");
      for (const [role, rule] of Object.entries(ROLES)) {
        if (this._config.radio[role]) continue;
        const match=owned.find(e => rule.domains.includes(e.entity_id.split(".")[0]) &&
          rule.test.test(this._norm([e.entity_id,e.original_name,e.name].join(" "))));
        if (match) this._config.radio[role]=match.entity_id;
      }
      this._fire();
    } catch(err) { console.warn("Brama BFT: nie udało się pobrać rejestrów HA",err); this._deviceName="Błąd odczytu rejestru urządzeń HA"; }
    finally { this._loading=false; this.requestUpdate(); }
  }
  _set(key,value) { this._config={...this._config,radio:{...this._config.radio,[key]:value}}; this._fire(); }
  _options(role) {
    const domains=ROLES[role].domains;
    return Object.values(this._hass?.states||{}).filter(s=>domains.includes(s.entity_id.split(".")[0]))
      .sort((a,b)=>a.entity_id.localeCompare(b.entity_id));
  }
  render() {
    if (!this._config) return html``;
    return html`<div class="field"><label>Nazwa karty</label><input .value=${this._config.name||""} @change=${e=>{this._config={...this._config,name:e.target.value};this._fire();}}></div>
      <p class="hint">${this._loading?"Wykrywanie sterownika i encji…":this._deviceName}</p>
      ${Object.entries(ROLES).map(([role,meta])=>html`<div class="field"><label>${meta.label}</label>
        <select .value=${this._config.radio[role]||""} @change=${e=>this._set(role,e.target.value)}>
          <option value="">— wybierz encję —</option>
          ${this._options(role).map(s=>html`<option value=${s.entity_id}>${s.attributes?.friendly_name||s.entity_id} — ${s.entity_id}</option>`)}
        </select></div>`)}
      <p class="hint">Automatyczne przypisanie dotyczy wyłącznie encji sterownika BFT. Listy pozwalają też wskazać ręcznie dowolną encję właściwej domeny.</p>`;
  }
}

if (!customElements.get("brama-przesuwna-bft-card")) customElements.define("brama-przesuwna-bft-card",BramaPrzesuwnaBFTCard);
if (!customElements.get("brama-przesuwna-bft-card-editor")) customElements.define("brama-przesuwna-bft-card-editor",BramaPrzesuwnaBFTCardEditor);
window.customCards=window.customCards||[];
if (!window.customCards.some(c=>c.type==="brama-przesuwna-bft-card")) window.customCards.push({type:"brama-przesuwna-bft-card",name:"Brama przesuwna BFT",description:"Karta sterowania bramą i furtką."});
