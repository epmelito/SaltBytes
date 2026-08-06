export default {
  title: "SaltBytes",
  root: "src",
  output: "dist",
  style: "style.css",
  header: "<div class=\"shell-header\"><a class=\"shell-home\" href=\"https://epmelito.github.io/SaltBytes/\" target=\"_self\">SaltBytes</a><span>North Carolina coastal forecasts and product health</span></div>",
  pages: [
    {
      name: "Coastal conditions",
      pages: [
        {name: "Conditions", path: "/conditions"}
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
