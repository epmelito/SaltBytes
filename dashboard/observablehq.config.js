import {themeControlMarkup, themeHeadMarkup} from "./theme.js";

export default {
  title: "SaltBytes",
  root: "src",
  output: "dist",
  style: "style.css",
  head: themeHeadMarkup,
  home: "SaltBytes",
  header: `<div class="shell-header"><div class="shell-brand"><a class="shell-home" href="https://epmelito.github.io/SaltBytes/" target="_self">SaltBytes</a><span class="shell-tagline">North Carolina coastal forecasts and product health</span></div>${themeControlMarkup}</div>`,
  pages: [
    {
      name: "Coastal conditions",
      pages: [
        {name: "Conditions", path: "/conditions"},
        {name: "Species assessments", path: "/species-assessments"}
      ]
    },
    {
      name: "Operations and product health",
      pages: [
        {name: "Pipeline monitoring", path: "/pipeline-monitoring"},
        {name: "Forecast revisions", path: "/forecast-revisions"},
        {name: "Forecast sources", path: "/data-provenance"}
      ]
    }
  ],
  toc: false,
  pager: false,
  footer: "SaltBytes publishes forecasts and tide predictions, not observations or fishing advice."
};
