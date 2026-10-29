import { LitElement, html, css } from "https://unpkg.com/lit@3/index.js?module";

const DOMAIN = "brama_przesuwna_bft";
const DEFAULT_POSITION = "sensor.wjazd_brama_wjazdowa_pozycja_bramy";
const DEFAULT_STATUS = "sensor.brama_wjazdowa_dokladny_stan_bramy";
const DEFAULT_MAIN = "button.brama_wjazdowa_otworz_zamknij_brame";
const DEFAULT_PEDESTRIAN = "button.brama_wjazdowa_otworz_jako_furtke";

class BramaPrzesuwnaBFTCard extends LitElement {
  static properties = { hass: {}, _config: {} };

  static styles = css`
    :host { display:block; }
    ha-card { padding:16px; overflow:hidden; }
    .head { display:flex; justify-content:space-between; align-items:center; gap:12px; }
    h2 { font-size:20px; margin:0; }
    .status { font-weight:600; text-align:right; }
    .scene { margin:12px 0; padding:12px; border-radius:12px; background:var(--ha-card-background,var(--card-background-color)); border:1px solid var(--divider-color); }
    .track { height:12px; border-radius:8px; background:var(--disabled-color); overflow:hidden; margin-top:10px; }
    .position { height:100%; background:var(--primary-color); transition:width .3s ease; }
    .meta { color:var(--secondary-text-color); font-size:13px; margin-top:5px; }
    .actions { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
    button { min-height:48px; border:0; border-radius:14px; padding:10px; background:var(--primary-color); color:var(--text-primary-color); font:inherit; font-weight:600; cursor:pointer; }
    button.secondary { background:var(--secondary-background-color); color:var(--primary-text-color); }
    button:disabled { opacity:.45; cursor:not-allowed; }
  `;

  setConfig(config) {
    this._config = {
      name: config.name || "Brama wjazdowa",
      position_entity: config.position_entity || DEFAULT_POSITION,
      status_entity: config.status_entity || DEFAULT_STATUS,
      main_button: config.main_button || DEFAULT_MAIN,
      pedestrian_button: config.pedestrian_button || DEFAULT_PEDESTRIAN,
    };
  }

  getCardSize() { return 3; }

  _state(entityId) { return this.hass?.states?.[entityId]?.state; }

  _press(entityId) {
    if (!entityId || !this.hass) return;
    this.hass.callService("button", "press", { entity_id: entityId });
  }

  render() {
    if (!this._config || !this.hass) return html``;
    const raw = this._state(this._config.position_entity);
    const n = Number(raw);
    const valid = raw !== undefined && !["unknown", "unavailable"].includes(raw) && Number.isFinite(n);
    const pos = valid ? Math.max(0, Math.min(100, Math.round(n))) : null;
    const status = this._state(this._config.status_entity) || "Brak stanu";
    const moving = /otwieranie|zamykanie/i.test(status);
    const open = /otwarta/i.test(status);
    const closed = /zamknięta/i.test(status);
    const mainLabel = moving ? "Stop" : open ? "Zamknij bramę" : closed ? "Otwórz bramę" : "Steruj bramą";
    return html`
      <ha-card>
        <div class="head"><h2>${this._config.name}</h2><div class="status">${status}${moving && pos !== null ? html` · ${pos}%` : ""}</div></div>
        <div class="scene">
          <div>Pozycja bramy: <strong>${pos === null ? "brak danych" : `${pos}%`}</strong></div>
          <div class="track"><div class="position" style="width:${pos ?? 0}%"></div></div>
          <div class="meta">Pozycja szacowana na podstawie czasu ruchu.</div>
        </div>
        <div class="actions">
          <button @click=${() => this._press(this._config.main_button)}>${mainLabel}</button>
          <button class="secondary" @click=${() => this._press(this._config.pedestrian_button)}>${open ? "Zamknij / steruj" : "Otwórz furtkę"}</button>
        </div>
      </ha-card>
    `;
  }

  static getConfigElement() {
    return document.createElement("brama-przesuwna-bft-card-editor");
  }

  static getStubConfig() { return {}; }
}

class BramaPrzesuwnaBFTCardEditor extends LitElement {
  static properties = { hass: {}, _config: {} };
  setConfig(config) { this._config = { ...config }; }
  static styles = css`:host { display:block; } .field { display:block; margin:12px 0; } label { display:block; margin-bottom:5px; color:var(--secondary-text-color); } input { box-sizing:border-box; width:100%; padding:10px; color:var(--primary-text-color); background:var(--card-background-color); border:1px solid var(--divider-color); border-radius:8px; }`;
  _change(key, ev) {
    const value = ev.target.value.trim();
    this._config = { ...this._config, [key]: value };
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
  }
  render() {
    if (!this._config) return html``;
    const fields = [
      ["name", "Nazwa karty", "Brama wjazdowa"],
      ["position_entity", "Encja pozycji", DEFAULT_POSITION],
      ["status_entity", "Encja stanu", DEFAULT_STATUS],
      ["main_button", "Przycisk bramy", DEFAULT_MAIN],
      ["pedestrian_button", "Przycisk furtki", DEFAULT_PEDESTRIAN],
    ];
    return html`<div>${fields.map(([key, label, fallback]) => html`<div class="field"><label>${label}</label><input .value=${this._config[key] || fallback} @change=${ev => this._change(key, ev)} /></div>`)}</div>`;
  }
}
customElements.define("brama-przesuwna-bft-card", BramaPrzesuwnaBFTCard);
customElements.define("brama-przesuwna-bft-card-editor", BramaPrzesuwnaBFTCardEditor);
window.customCards = window.customCards || [];
window.customCards.push({ type: "brama-przesuwna-bft-card", name: "Brama przesuwna BFT", description: "Karta sterowania bramą i furtką." });
