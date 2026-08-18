---
title: Species assessments
---

# Species assessments

Choose a location and forecast time to see SaltBytes' current species assessment.

~~~js
import * as Inputs from "@observablehq/inputs";
import {html} from "npm:htl";
import {formatTimestamp, locationName} from "./components/format.js";

const manifest = await FileAttachment("./data/manifest.json").json();
const locations = await FileAttachment("./data/locations.json").json();
const conditions = await FileAttachment("./data/conditions.json").json();
const query = new URLSearchParams(globalThis.location?.search ?? "");
const requestedLocation = query.get("location");
const initialLocation = locations.some((item) => item.location_id === requestedLocation)
  ? requestedLocation : locations[0].location_id;
~~~

~~~js
const locationId = view(Inputs.select(locations.map((item) => item.location_id), {
  label: "Location", format: (value) => locationName(value, locations), value: initialLocation
}));
~~~

~~~js
const locationRows = conditions.filter((row) => row.location_id === locationId);
~~~

~~~js
const requestedTime = query.get("forecast_time");
const initialTime = locationRows.some((row) => row.forecast_time === requestedTime)
  ? requestedTime : locationRows[0]?.forecast_time;
~~~

~~~js
const forecastTime = view(Inputs.select(locationRows.map((row) => row.forecast_time), {
  label: "Forecast time", format: (value) => formatTimestamp(value, manifest.display_timezone), value: initialTime
}));
~~~

~~~js
const selected = locationRows.find((row) => row.forecast_time === forecastTime);
const assessment = selected?.spanish_mackerel_conditions;
const available = assessment?.state === "available";
const labels = {seasonal_alignment:"Seasonal timing",thermal_context:"Water temperature",sound_side_location_context:"Sound-side location context",wind_fishability:"Wind",wave_fishability:"Waves",local_baitfish_presence:"Local baitfish presence",current_spanish_mackerel_presence:"Current Spanish mackerel presence",schools_within_casting_range:"Schools within casting range",nearshore_sst_accuracy_and_site_representativeness:"Nearshore water temperature accuracy and local representativeness"};
const sentenceLabels = {seasonal_alignment:"seasonal timing",thermal_context:"water temperature",sound_side_location_context:"sound-side location context",wind_fishability:"wind",wave_fishability:"waves"};
const confidenceLabels = {location_applicability_confidence:"Fit for this location",environmental_source_confidence:"Forecast data",seasonal_evidence_confidence:"Seasonal evidence",habitat_data_confidence:"Habitat information",fishability_data_confidence:"Fishing condition data",overall_interpretation_confidence:"Overall confidence"};
const bands = {very_limited_alignment:"Very limited forecast alignment",limited_alignment:"Limited forecast alignment",mixed_conditions:"Mixed forecast conditions",favorable_alignment:"Favorable forecast alignment",strong_alignment:"Strong forecast alignment"};
const items = (values) => values?.map((value) => labels[value] ?? value) ?? [];
const list = (values) => items(values).map((value) => html`<li>${value}</li>`);
const joinItems = (values) => values.length < 2 ? values[0] ?? "" : values.length === 2 ? `${values[0]} and ${values[1]}` : `${values.slice(0, -1).join(", ")}, and ${values.at(-1)}`;
const summary = (positiveFactors, limitingFactors) => {
  const describe = (factors) => factors?.map((factor) => sentenceLabels[factor] ?? labels[factor] ?? factor) ?? [];
  const positive = joinItems(describe(positiveFactors));
  const limiting = joinItems(describe(limitingFactors));
  const lead = (value) => value ? `${value[0].toUpperCase()}${value.slice(1)}` : "";
  const positiveVerb = positiveFactors?.length === 1 && positiveFactors[0] !== "wave_fishability" ? "supports" : "support";
  const limitingVerb = limitingFactors?.length === 1 && limitingFactors[0] !== "wave_fishability" ? "limits" : "limit";
  if (positive && limiting) return `${lead(positive)} ${positiveVerb} the assessment, while ${limiting} ${limitingVerb} it.`;
  if (positive) return `${lead(positive)} ${positiveVerb} the assessment.`;
  if (limiting) return `${lead(limiting)} ${limitingVerb} the assessment.`;
  return "The available forecast factors do not support a more specific summary.";
};
const confidence = (value) => value ? `${value[0].toUpperCase()}${value.slice(1)}` : "Unavailable";
const overall = assessment?.confidence?.find((item) => item.identifier === "overall_interpretation_confidence");
const details = ["overall_interpretation_confidence","seasonal_evidence_confidence","location_applicability_confidence","environmental_source_confidence","fishability_data_confidence","habitat_data_confidence"].map((identifier) => assessment?.confidence?.find((item) => item.identifier === identifier)).filter(Boolean);
const unavailableGroups = [
  {reasons:["location_not_applicable"], message:"This assessment is not available for this location and fishing context."},
  {reasons:["forecast_time_invalid","display_timezone_missing","display_timezone_invalid","local_forecast_date_unavailable"], message:"Required forecast timing information is unavailable."},
  {reasons:["weather_source_missing","weather_source_not_success","wind_speed_10m_missing","wind_speed_10m_invalid","wind_gusts_10m_missing","wind_gusts_10m_invalid"], message:"Required wind forecast data is unavailable."},
  {reasons:["wave_source_missing","wave_source_not_success","wave_height_missing","wave_height_invalid"], message:"Required wave forecast data is unavailable."},
  {reasons:["sst_source_missing","sst_source_not_success","sea_surface_temperature_missing","sea_surface_temperature_invalid"], message:"Required water temperature forecast data is unavailable."}
];
const unavailable = unavailableGroups.filter((group) => assessment?.unavailable_reasons?.some((reason) => group.reasons.includes(reason))).map((group) => group.message);
~~~

~~~js
display(html`<section class="conditions-context" aria-label="Assessment context"><p class="conditions-eyebrow">Coastal forecast</p><h2>${locationName(locationId, locations)}</h2><p><strong>Selected time:</strong> ${formatTimestamp(forecastTime, manifest.display_timezone)}</p></section>`);
~~~

## Spanish mackerel assessment

~~~js
display(available ? html`<section class="conditions-assessment">
  <div><p class="conditions-eyebrow">Spanish mackerel forecast</p><h3>${bands[assessment.score_band] ?? "Forecast assessment available"}</h3><p class="assessment-summary">${summary(assessment.positive_factors, assessment.limiting_factors)}</p></div>
  <div class="assessment-support"><div><span class="detail-label">Score</span><strong class="assessment-score">${assessment.score} / 100</strong></div><div><span class="detail-label">Overall confidence</span><strong>${confidence(overall?.state)}</strong></div></div>
  <p class="assessment-limitation">This assessment does not estimate fish presence, catch likelihood, or safety.</p>
  ${items(assessment.positive_factors).length || items(assessment.limiting_factors).length ? html`<div class="assessment-highlights">${items(assessment.positive_factors).length ? html`<div><span class="detail-label">Most helpful now</span><p>${items(assessment.positive_factors).slice(0,2).join(", ")}</p></div>` : null}${items(assessment.limiting_factors).length ? html`<div><span class="detail-label">Main limitation</span><p>${items(assessment.limiting_factors).slice(0,1).join(", ")}</p></div>` : null}</div>` : null}
  ${items(assessment.unknown_factors).filter((item) => item !== labels.nearshore_sst_accuracy_and_site_representativeness).length ? html`<section class="assessment-unknowns"><h4>What SaltBytes cannot observe</h4><ul>${list(assessment.unknown_factors.filter((item) => item !== "nearshore_sst_accuracy_and_site_representativeness"))}</ul></section>` : null}
  <details><summary>Assessment factors and confidence</summary><div class="assessment-details">${items(assessment.positive_factors).length ? html`<div><h4>Supporting conditions</h4><ul>${list(assessment.positive_factors)}</ul></div>` : null}${items(assessment.limiting_factors).length ? html`<div><h4>Limiting conditions</h4><ul>${list(assessment.limiting_factors)}</ul></div>` : null}<div><h4>Confidence in this assessment</h4><dl class="confidence-values">${details.map((item) => html`<div><dt>${confidenceLabels[item.identifier]}</dt><dd>${confidence(item.state)}</dd></div>`)}</dl></div></div></details>
</section>` : html`<section class="conditions-assessment conditions-assessment-unavailable"><p class="conditions-eyebrow">Spanish mackerel forecast</p><h3>Assessment unavailable</h3>${unavailable.map((message) => html`<p>${message}</p>`)}<p class="assessment-limitation">This assessment does not estimate fish presence, catch likelihood, or safety.</p></section>`);
~~~
