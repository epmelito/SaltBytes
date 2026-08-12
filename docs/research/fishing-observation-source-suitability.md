# Initial fishing-observation source suitability assessment

## Status

Completed bounded research, assessed 2026-08-12. This is frozen source-suitability research for later work, not legal advice, permanent authorization, production configuration, or an observation requirements contract. Terms, robots policies, ownership, publication methods, and access conditions can change.

## Purpose and classification posture

This assessment evaluates initial candidates under SaltBytes' current posture: low-frequency retrieval, discrete factual extraction, attribution, no access-control circumvention, and current noncommercial/public-project use where that qualification applies.

| Classification | Meaning |
| --- | --- |
| Green | A reasonable candidate for later bounded production ingestion under the current posture. |
| Yellow | A material uncertainty or dependency risk must be resolved or consciously accepted before production ingestion. |
| Red | SaltBytes should not build automated production ingestion around the source under the reviewed conditions. |

Green is conditional and dated; it is not permanent approval. `robots.txt` is a crawler-policy signal, not complete legal authorization or automatically a technical access control. Public visibility alone does not make a source Green. Terms and robots evidence require separate consideration.

The related [fishing observation contract trial](fishing-observation-contract-trial.md) governs report and assertion evidence boundaries. This assessment does not approve a collector, schema, scheduling, storage, or final source-risk process.

## Classification summary

| Source | Classification | Material suitability finding |
| --- | --- | --- |
| [Jennette's Pier](#jennettes-pier) | Green, current posture | Exact-site first-party observations through NC Aquariums. |
| [NCDMF reports](#ncdmf-recreational-fishing-reports) | Green, current posture | Regional and fishing-mode evidence, not exact-site evidence. |
| [Bogue Inlet Pier](#bogue-inlet-pier) | Green | First-party exact-site reports and curated Catch Board evidence. |
| [Tradewinds / Ocracoke](#tradewinds--ocracoke) | Green | First-party reports with useful local and catch-context facts. |
| [Ocean Isle Beach Pier](#ocean-isle-beach-pier) | Green | First-party current fishing-report surface. |
| [Sunset Beach Pier](#sunset-beach-pier) | Yellow | Crawler-policy evidence is unresolved in the reviewed environment. |
| [Little Bridge reporting](#little-bridge-reporting) | Yellow overall | Structured trial path depends on a Red publisher path. |
| [Frisco Rod & Gun](#frisco-rod--gun-comparison-case) | Red | Published terms restrict automated and systematic retrieval. |

## Source assessments

### Jennette's Pier

**Classification: Green, current posture.** A direct first-party reporting path exists through NC Aquariums, so Outer Banks This Week need not be the primary production dependency. The reports provide strong exact-site fishing observations. The reviewed [robots policy](https://www.ncaquariums.com/robots.txt) returned HTTP 200; its general `User-agent: *` policy restricts administrative or system paths but does not disallow ordinary public content, and specifies `Crawl-delay: 30`. It separately blocks many explicitly named AI or scraper agents, so this is not universal permission for every named agent.

[NC.gov terms](https://www.nc.gov/disclaimer-terms-use) permit copying and distribution of non-image information for noncommercial use with attribution. The current noncommercial posture is supportable; commercial use requires source re-review. Photographs and expressive article content are not interchangeable with discrete catch facts.

- [NC Aquariums](https://www.ncaquariums.com/)
- [NC Aquariums robots policy](https://www.ncaquariums.com/robots.txt)
- [NC.gov terms](https://www.nc.gov/disclaimer-terms-use)

### NCDMF recreational fishing reports

**Classification: Green, current posture.** The North Carolina Division of Marine Fisheries is a first-party authoritative state source. Its reports provide regional and fishing-mode information, not exact-site evidence. DMF describes them as compiled from port-agent observations and angler interviews, with weekly reporting during the active season.

The reviewed [robots policy](https://www.deq.nc.gov/robots.txt) returned HTTP 200. Ordinary public report paths were not disallowed, while administrative, user, search, core, profile, and similar system paths were restricted. The same [NC.gov noncommercial-use limitation](https://www.nc.gov/disclaimer-terms-use) applies, so commercial use requires re-review. Regional evidence strength and production suitability remain separate concepts.

- [NCDMF recreational fishing reports](https://www.deq.nc.gov/about/divisions/marine-fisheries/public-information-and-education/coastal-fishing-information/recreational-fishing-reports)
- [DEQ robots policy](https://www.deq.nc.gov/robots.txt)
- [NC.gov terms](https://www.nc.gov/disclaimer-terms-use)

### Bogue Inlet Pier

**Classification: Green.** Bogue Inlet Pier publishes direct first-party fishing reports and Catch Board pages with high-value exact-site factual catch evidence. Catch Board entries are curated highlight evidence, not catch-frequency evidence. The reviewed [robots policy](https://www.bogueinletpier.com/robots.txt) returned HTTP 200; `User-agent: *` disallows `/wp-admin/` and permits `/wp-admin/admin-ajax.php`, while ordinary report content is not disallowed.

The bounded review found no published site terms creating an additional automated-access prohibition. That absence is not affirmative permission. Under the current low-frequency, factual-extraction, attribution, and no-circumvention posture, no material blocker was identified. Names, photographs, and expressive prose are not ingestion targets merely because they accompany catch facts.

- [Fishing reports](https://www.bogueinletpier.com/fishing-reports/)
- [2026 Catch Board](https://www.bogueinletpier.com/2026-catch-board/)
- [Robots policy](https://www.bogueinletpier.com/robots.txt)

### Tradewinds / Ocracoke

**Classification: Green.** Direct first-party public fishing-report pages can preserve useful ramp, surf, sound, date, species, size, quantity, and catch-context facts. Outer Banks This Week need not be the primary dependency. The reviewed [robots policy](https://tradewindstackle.com/robots.txt) returned HTTP 200 and specifies a crawl delay of three seconds, restrictions on calendar or event actions and `/cdn-cgi`, and `Disallow: /*?` for query-string URLs. Later retrieval must remain on clean ordinary public report URLs and must not route around those restrictions.

OneBoat is identified as the site designer, but the bounded evidence does not justify automatically applying [OneBoat terms](https://oneboat.com/terms-use) to the Tradewinds first-party site. That is a bounded inference, not a legal conclusion.

- [Fishing reports](https://tradewindstackle.com/fishing-reports/)
- [Robots policy](https://tradewindstackle.com/robots.txt)
- [OneBoat terms](https://oneboat.com/terms-use)

### Ocean Isle Beach Pier

**Classification: Green.** Ocean Isle Beach Pier has a direct first-party public surface with current fishing reports. The reviewed [robots policy](https://oibpier.com/robots.txt) returned HTTP 200 and states `User-Agent: *`, `Allow: /`, `Disallow: /preview-times`, and `Disallow: /api/`. Later collection must use ordinary published report content; the API restriction is not an invitation to discover or work around that endpoint. The bounded review found no additional published restriction creating a material blocker under the current posture.

- [Pier reports](https://oibpier.com/pier)
- [Robots policy](https://oibpier.com/robots.txt)

### Sunset Beach Pier

**Classification: Yellow.** Sunset Beach Pier has extremely high data value: its public daily-report archive visibly spans many years and can preserve report-day context separately from prior-day catch facts. Its structured format is unusually useful for historical analysis. However, the reviewed [robots policy](https://apps.sunsetbeachpier.com/robots.txt) could not be retrieved from the project's manual Windows check because the TLS trust relationship failed:

> The underlying connection was closed: Could not establish trust relationship for the SSL/TLS secure channel.

The crawler-policy question is therefore unresolved in the actual execution environment. The blog is hosted through Doteasy; the reviewed hosted-blog agreement did not establish a clear SaltBytes-specific permission or prohibition for factual extraction. Absence of a clear prohibition does not make it Green, and the TLS failure does not make it Red. High data value does not override unresolved production suitability.

- [Daily-report archive](https://apps.sunsetbeachpier.com/Blog/)
- [Robots policy](https://apps.sunsetbeachpier.com/robots.txt)

### Little Bridge reporting

**Classification: Yellow overall; Outer Banks This Week production path: Red.** Little Bridge is strategically valuable sound-side observational evidence. Fishing Unlimited has a first-party public site and report product, but the reviewed first-party surface was broader Outer Banks or audio-style reporting, not the structured dated Little Bridge text used in the normalization trial. Those structured reports were published through Outer Banks This Week, creating a publisher and dependency concern.

The reviewed [Fishing Unlimited robots endpoint](https://www.fishingunlimited.net/robots.txt) returned HTTP 404, which is neither explicit permission nor prohibition. [Outer Banks This Week robots](https://outerbanksthisweek.com/robots.txt) returned HTTP 200 with `Crawl-delay: 10` and many restricted system paths; the relevant public content surface was not generally disallowed. However, [OneBoat terms](https://oneboat.com/terms-use) governing that content platform create a material reuse and dependency problem for automated production ingestion. Robots evidence does not override that concern.

Little Bridge remains Yellow as a source objective. The Outer Banks This Week production path is Red under the reviewed conditions. A viable direct first-party Little Bridge path may change that result.

- [Fishing Unlimited report](https://www.fishingunlimited.net/fishing-report.html)
- [Fishing Unlimited robots endpoint](https://www.fishingunlimited.net/robots.txt)
- [Outer Banks This Week](https://outerbanksthisweek.com/)
- [Outer Banks This Week robots policy](https://outerbanksthisweek.com/robots.txt)
- [OneBoat terms](https://oneboat.com/terms-use)

### Frisco Rod & Gun comparison case

**Classification: Red.** This is a bounded comparison case, not an initial primary candidate. It has high fishing-data value, but its published [terms of service](https://friscorodandgun.com/terms-of-service/) expressly prohibit or restrict automated or non-human access, systematic retrieval or database creation, scraping or data-mining tools, and commercial exploitation without permission. SaltBytes should not build automated production ingestion around it under those reviewed terms. It can remain a manual research source unless the terms or permission status materially changes.

## Cross-source conclusions

The strongest plausible initial production candidates are Jennette's Pier, Bogue Inlet Pier, Tradewinds / Ocracoke, and Ocean Isle Beach Pier for exact or local evidence, plus NCDMF recreational fishing reports for regional authoritative evidence. Sunset Beach Pier and Little Bridge should remain on hold before automation.

Source usefulness is not production suitability. SaltBytes should preserve attribution and provenance, extract discrete factual observations rather than articles, photographs, or substantial expressive text, and avoid bypassing login, paywall, CAPTCHA, IP block, or other technical access controls. Source loss should degrade observational evidence rather than collapse the product. Written permission from every public source is not a prerequisite for the current research or development posture.

A commercial launch requires a bounded re-review of applicable source terms and use conditions, especially for NC government sources. These classifications are not professional legal advice and do not manufacture certainty where published terms, robots behavior, or ownership relationships remain unresolved.
