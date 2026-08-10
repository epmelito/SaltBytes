import {mkdir, readFile, writeFile} from "node:fs/promises";
import {dirname, resolve} from "node:path";

import {themeBootstrapScript, themeControlMarkup} from "../theme.js";

const outputPath = resolve(process.argv[2] ?? "../site/index.html");
const themeCss = await readFile(new URL("../src/saltbytes-theme.css", import.meta.url), "utf8");

const document = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SaltBytes</title>
  <style>${themeCss}</style>
  <script>${themeBootstrapScript}</script>
</head>
<body class="saltbytes-landing">
  <main class="saltbytes-landing-main">
    <div class="saltbytes-landing-toolbar">${themeControlMarkup}</div>
    <p class="eyebrow">North Carolina shore forecasts</p>
    <h1>SaltBytes</h1>
    <p class="intro">SaltBytes brings upcoming coastal forecast conditions and the product health behind them into one clear public experience.</p>
    <nav aria-label="Primary reporting destinations">
      <a class="destination" href="dashboard/conditions">
        <p class="destination-label">For anglers and coastal visitors</p>
        <strong>Coastal conditions</strong>
        <span>Explore upcoming wind, waves, sea surface temperature, tides, and available Spanish mackerel conditions at North Carolina shore locations.</span>
      </a>
      <a class="destination" href="dashboard/pipeline-monitoring">
        <p class="destination-label">For product and technical review</p>
        <strong>Operations and product health</strong>
        <span>Review pipeline status, forecast revisions, and the sources behind the published data.</span>
      </a>
    </nav>
    <p class="secondary">Static reports: <a href="conditions/">Conditions report</a><a href="operations/">Operations report</a></p>
  </main>
</body>
</html>
`;

await mkdir(dirname(outputPath), {recursive: true});
await writeFile(outputPath, document, "utf8");
console.log(`landing_page=${outputPath}`);
