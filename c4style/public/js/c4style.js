(() => {
	"use strict";

	const defaults = {
		primary: "#714B67",
		accent: "#017E84",
		background: "#E5E8EB",
		fontSize: 14,
		radius: 6,
		density: "comfortable",
		workspaceWide: false,
		direction: "auto",
	};
	const presets = {
		c4style: { primary: "#714B67", accent: "#017E84", background: "#E5E8EB" },
		ocean: { primary: "#155E75", accent: "#0284C7", background: "#EAF2F8" },
		forest: { primary: "#365C46", accent: "#4F8A62", background: "#EEF3EE" },
		sunset: { primary: "#8B4A3C", accent: "#D47A45", background: "#F7F0E8" },
	};
	const user = frappe.session && frappe.session.user ? frappe.session.user : "Guest";
	const storageKey = `c4style.settings.${encodeURIComponent(user)}`;
	const boot = (frappe.boot && frappe.boot.c4style) || {};
	const siteSettings = { ...defaults, ...(boot.site || {}) };
	const originalDirection = document.documentElement.getAttribute("dir") || "ltr";
	let settings = { ...siteSettings, ...(boot.personal || {}) };

	function notifyStorageError(message) {
		frappe.msgprint({
			title: __("C4Style settings"),
			message: __(message),
			indicator: "orange",
		});
	}

	function isHexColor(value) {
		return typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value);
	}

	function readSettings() {
		let stored;
		try {
			stored = localStorage.getItem(storageKey);
		} catch (error) {
			notifyStorageError("Your browser could not read saved preferences. Defaults will be used.");
			return { ...defaults };
		}

		if (!stored) return { ...defaults };

		try {
			const parsed = JSON.parse(stored);
			if (
				!isHexColor(parsed.primary) ||
				!isHexColor(parsed.accent) ||
				!isHexColor(parsed.background) ||
				!Number.isFinite(parsed.fontSize) ||
				parsed.fontSize < 12 ||
				parsed.fontSize > 18 ||
				!Number.isFinite(parsed.radius) ||
				parsed.radius < 2 ||
				parsed.radius > 16 ||
				!["compact", "comfortable"].includes(parsed.density) ||
				typeof parsed.workspaceWide !== "boolean"
			) {
				throw new Error("Saved preferences do not match the supported settings.");
			}
			return { ...defaults, ...parsed };
		} catch (error) {
			notifyStorageError("Saved preferences could not be read and have been reset.");
			return { ...defaults };
		}
	}

	function saveSettings() {
		try {
			localStorage.setItem(storageKey, JSON.stringify(settings));
		} catch (error) {
			notifyStorageError("Your browser could not save preferences. Changes apply until you leave this page.");
		}
	}

	function applySettings() {
		const root = document.documentElement;
		root.setAttribute("dir", settings.direction === "auto" ? originalDirection : settings.direction);
		root.style.setProperty("--text-base", `${settings.fontSize}px`);
		root.style.setProperty("--btn-primary", settings.primary);
		root.style.setProperty("--primary", settings.primary);
		root.style.setProperty("--navbar-bg", settings.primary);
		root.style.setProperty("--secondary", settings.accent);
		root.style.setProperty("--btn-secondary", `color-mix(in srgb, ${settings.accent} 50%, transparent)`);
		root.style.setProperty("--sidebar-select-color", `color-mix(in srgb, ${settings.accent} 12%, transparent)`);
		root.style.setProperty("--table-border-color", `color-mix(in srgb, ${settings.primary} 25%, transparent)`);
		root.style.setProperty("--bg-color", settings.background);
		root.style.setProperty("--c4style-font-size", `${settings.fontSize}px`);
		root.style.setProperty("--c4style-radius", `${settings.radius}px`);
		document.body.classList.toggle("c4style-compact", settings.density === "compact");
		document.body.classList.toggle("c4style-workspace-wide", settings.workspaceWide);
	}

	function persistAndApply() {
		applySettings();
		saveSettings();
	}

	function settingsMarkup() {
		return `
			<section class="c4style-settings">
				<div class="c4style-settings__intro">
					<h2>${__("Make your workspace yours")}</h2>
					<p class="text-muted">${__("Choose colors and layout preferences. Preview changes, then save to your account. Administrators can publish shared site styling.")}</p>
				</div>
				<div class="c4style-settings__grid">
					<section class="c4style-settings__card">
						<h3>${__("Color theme")}</h3>
						<p class="c4style-settings__hint">${__("Start with a palette or fine-tune individual colors.")}</p>
						<div class="c4style-settings__presets">
							<button class="btn btn-default c4style-settings__preset" data-preset="c4style"><span class="c4style-settings__swatch" style="background:#714B67"></span>${__("C4Style")}</button>
							<button class="btn btn-default c4style-settings__preset" data-preset="ocean"><span class="c4style-settings__swatch" style="background:#155E75"></span>${__("Ocean")}</button>
							<button class="btn btn-default c4style-settings__preset" data-preset="forest"><span class="c4style-settings__swatch" style="background:#365C46"></span>${__("Forest")}</button>
							<button class="btn btn-default c4style-settings__preset" data-preset="sunset"><span class="c4style-settings__swatch" style="background:#8B4A3C"></span>${__("Sunset")}</button>
						</div>
						<label class="c4style-settings__color-row"><span>${__("Primary color")}</span><input type="color" data-setting="primary" aria-label="${__("Primary color")}"></label>
						<label class="c4style-settings__color-row"><span>${__("Accent color")}</span><input type="color" data-setting="accent" aria-label="${__("Accent color")}"></label>
						<label class="c4style-settings__color-row"><span>${__("Page background")}</span><input type="color" data-setting="background" aria-label="${__("Page background")}"></label>
					</section>
					<section class="c4style-settings__card">
						<h3>${__("Layout and density")}</h3>
						<p class="c4style-settings__hint">${__("Adjust the workspace width, text size, and control spacing.")}</p>
						<div class="c4style-settings__range-row">
							<label for="c4style-font-size">${__("Text size")}</label>
							<input id="c4style-font-size" type="range" min="12" max="18" step="1" data-setting="fontSize">
							<output data-value="fontSize"></output>
						</div>
						<div class="c4style-settings__range-row">
							<label for="c4style-radius">${__("Corner roundness")}</label>
							<input id="c4style-radius" type="range" min="2" max="16" step="1" data-setting="radius">
							<output data-value="radius"></output>
						</div>
						<div class="form-group">
							<label for="c4style-density">${__("Control spacing")}</label>
							<select id="c4style-density" class="form-control" data-setting="density">
								<option value="comfortable">${__("Comfortable")}</option>
								<option value="compact">${__("Compact")}</option>
							</select>
						</div>
						<label for="c4style-direction">${__("Text direction")}</label>
<select id="c4style-direction" class="form-control" data-setting="direction">
<option value="auto">${__("Follow system language")}</option>
<option value="ltr">${__("Left to right")}</option>
<option value="rtl">${__("Right to left")}</option></select>
<p role="status" aria-live="polite" data-save-status></p>
<div class="c4style-settings__actions">
<button class="btn btn-primary" data-action="save">${__("Save my preferences")}</button>
${boot.can_manage ? `<button class="btn btn-default" data-action="publish">${__("Apply style for all users")}</button>` : ""}
							<button class="btn btn-primary" data-action="workspace">
								<span data-workspace-icon aria-hidden="true"></span>
								<span data-workspace-label></span>
							</button>
							<button class="btn btn-default" data-action="reset">${__("Reset to defaults")}</button>
						</div>
					</section>
				</div>
			</section>`;
	}

	function refreshControls(container) {
		container.querySelectorAll("[data-setting]").forEach((control) => {
			const key = control.dataset.setting;
			control.value = settings[key];
			const output = container.querySelector(`[data-value="${key}"]`);
			if (output) output.textContent = `${settings[key]} px`;
		});
		const rtl = document.documentElement.dir === "rtl";
		container.querySelector("[data-workspace-icon]").textContent = settings.workspaceWide !== rtl ? "\u2190" : "\u2192";
		const label = settings.workspaceWide ? __("Narrow workspace") : __("Expand workspace");
		container.querySelector("[data-workspace-label]").textContent = label;
		const button = container.querySelector('[data-action="workspace"]');
		button.setAttribute("aria-label", label);
		button.setAttribute("aria-pressed", String(settings.workspaceWide));
	}

	function buildSettingsPage(wrapper) {
		const page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("C4Style Settings"),
			single_column: true,
		});
		page.main.html(settingsMarkup());
		const container = page.main.find(".c4style-settings")[0];
		refreshControls(container);

		container.addEventListener("input", (event) => {
			const control = event.target.closest("[data-setting]");
			if (!control) return;
			settings[control.dataset.setting] =
				control.type === "range" ? Number(control.value) : control.value;
			persistAndApply();
			refreshControls(container);
		});

		container.addEventListener("change", (event) => {
			const control = event.target.closest("[data-setting]");
			if (!control) return;
			settings[control.dataset.setting] =
				control.type === "range" ? Number(control.value) : control.value;
			persistAndApply();
			refreshControls(container);
		});

		container.addEventListener("click", (event) => {
			const presetButton = event.target.closest("[data-preset]");
			if (presetButton) {
				Object.assign(settings, presets[presetButton.dataset.preset]);
				persistAndApply();
				refreshControls(container);
				return;
			}

			const actionButton = event.target.closest("[data-action]");
			const action = actionButton ? actionButton.dataset.action : null;
			if (action === "save" || action === "publish") {
				const scope = action === "publish" ? "site" : "personal";
				const save = () => {
					actionButton.disabled = true;
					frappe.call({
						method: "c4style.settings.save_settings",
						args: { settings: JSON.stringify(settings), scope },
						callback: () => {
							container.querySelector("[data-save-status]").textContent = scope === "site"
								? __("Site style saved. Reload to receive changes. Personal preferences take priority.")
								: __("Preferences saved for your account.");
						},
						always: () => { actionButton.disabled = false; },
					});
				};
				if (scope === "site") frappe.confirm(__("Apply these colors, text size, spacing and corners as defaults for all users?"), save);
				else save();
				return;
			} else if (action === "workspace") {
				settings.workspaceWide = !settings.workspaceWide;
			} else if (action === "reset") {
				settings = { ...siteSettings };
			} else {
				return;
			}
			persistAndApply();
			refreshControls(container);
		});
	}

	function addToolbarLink() {
		const navbar = document.querySelector(".navbar .navbar-collapse") ||
			document.querySelector(".navbar .container-fluid") ||
			document.querySelector(".navbar");
		if (!navbar || navbar.querySelector("[data-c4style-settings-link]")) return;

		const button = document.createElement("button");
		button.type = "button";
		button.className = "btn btn-default btn-sm c4style-toolbar-link";
		button.dataset.c4styleSettingsLink = "true";
		button.textContent = __("Style settings");
		button.addEventListener("click", () => frappe.set_route("c4style-settings"));
		navbar.appendChild(button);
	}

	// Page events must be attached only after Frappe creates the page wrapper.
	// Pre-populating frappe.pages makes PageView skip its constructor entirely.
	frappe.c4style = frappe.c4style || {};
	frappe.c4style.build_settings_page = buildSettingsPage;

	settings = boot.site ? settings : readSettings();
	applySettings();

	if (document.body) {
		const observer = new MutationObserver(addToolbarLink);
		observer.observe(document.body, { childList: true, subtree: true });
		addToolbarLink();
	}
})();
