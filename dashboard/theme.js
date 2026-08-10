export const themeControlMarkup = `
<div class="saltbytes-theme-control" data-saltbytes-theme-control role="group" aria-label="Theme">
  <span class="saltbytes-theme-options">
    <button type="button" data-saltbytes-theme-choice="system" aria-pressed="false">System</button>
    <button type="button" data-saltbytes-theme-choice="light" aria-pressed="false">Light</button>
    <button type="button" data-saltbytes-theme-choice="dark" aria-pressed="false">Dark</button>
  </span>
</div>`;

export const themeBootstrapScript = String.raw`(() => {
  const storageKey = "saltbytes-theme";
  const validPreferences = new Set(["light", "dark", "system"]);
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  let preference = "system";

  try {
    const stored = window.localStorage.getItem(storageKey);
    if (validPreferences.has(stored)) preference = stored;
  } catch {
    preference = "system";
  }

  const resolvedTheme = () => preference === "system"
    ? media.matches ? "dark" : "light"
    : preference;

  const syncControls = () => {
    document.querySelectorAll("[data-saltbytes-theme-choice]").forEach((control) => {
      const selected = control.dataset.saltbytesThemeChoice === preference;
      control.setAttribute("aria-pressed", String(selected));
    });
  };

  const syncSidebarHome = () => {
    const sidebarHome = [...document.querySelectorAll("#observablehq-sidebar a")].find(
      (anchor) => anchor.textContent.trim() === "SaltBytes"
    );
    if (!sidebarHome) return;
    sidebarHome.href = "https://epmelito.github.io/SaltBytes/";
    sidebarHome.target = "_self";
  };

  const disableHeadingPermalinks = () => {
    document.querySelectorAll('#observablehq-main :is(h2, h3) > a[href^="#"]').forEach((anchor) => {
      anchor.removeAttribute("href");
      anchor.tabIndex = -1;
      anchor.dataset.saltbytesHeadingAnchor = "true";
    });
  };

  const applyTheme = () => {
    const resolved = resolvedTheme();
    document.documentElement.dataset.saltbytesTheme = resolved;
    document.documentElement.dataset.saltbytesThemePreference = preference;
    document.documentElement.style.colorScheme = resolved;
    syncControls();
  };

  const setPreference = (value) => {
    preference = validPreferences.has(value) ? value : "system";
    try {
      window.localStorage.setItem(storageKey, preference);
    } catch {
      // persistence is optional when storage is unavailable
    }
    applyTheme();
  };

  document.addEventListener("click", (event) => {
    const control = event.target.closest?.("[data-saltbytes-theme-choice]");
    if (control) setPreference(control.dataset.saltbytesThemeChoice);
  });

  media.addEventListener("change", () => {
    if (preference === "system") applyTheme();
  });

  const syncShell = () => {
    syncControls();
    syncSidebarHome();
    disableHeadingPermalinks();
  };

  const observer = new MutationObserver((records) => {
    if (records.some((record) => record.addedNodes.length > 0)) syncShell();
  });
  observer.observe(document.documentElement, {childList: true, subtree: true});

  window.SaltBytesTheme = {applyTheme, setPreference};
  applyTheme();
  syncShell();
})();`;

export const themeHeadMarkup = `<script>${themeBootstrapScript}</script>`;
