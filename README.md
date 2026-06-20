# Trusted Agents website prototype

Eerste lokale prototype voor `trustedagents.nl`.

## Bestanden
- `index.html` — self-contained HTML/CSS prototype
- `DEPLOYMENT_AUTOMATION.md` — blauwdruk voor betaalde onboarding, Hetzner/Hostinger-keuze en provisioning

## Uitgangspunten
- Originele positionering voor `trustedagents.nl`: hero, trust badges, sectoren, agent-uitleg, use cases, producten/prijzen, deploy-flow, security/data, CTA.
- Geen overname van externe teksten, branding, assets of logo’s.
- Naast Hermes wordt OpenClaw als conversatie-/kanaallaag aangeboden voor Telegram en WhatsApp.
- `Deploy je agent` is uitgewerkt als eerste commerciële flow: intake → private workspace → Telegram/WhatsApp koppeling → human approval.
- Modeltoegang uitgelegd: Anthropic API-key, OpenRouter API-key en ChatGPT/OpenAI Codex OAuth als drie mogelijke routes; sleutels/tokens horen in de private agent-workspace, niet in de website.
- Project Taxi wordt publiek alleen abstract geframed: onder Oplossingen blijft `Geheugensteun` als brede categorie staan; de detailsectie `In ontwikkeling` is onder embargo en bevat geen leesbare werkwijze, scenario’s, namen of projectgeheimen.
- Deploymentopties toegevoegd en aangescherpt tot drie pakketten: `Managed Agent` (€29/maand per bot), `Private Agent Server` (dedicated, vanaf €79/maand) en `Bring your own` (eigen cloud/VPS/Mac met setup + beheer). Hetzner is voorkeursroute voor automatische provisioning; Hostinger blijft optioneel/affiliate.
- Positionering aangescherpt naar Nederlandse MKB-bedrijven, met Bernard Donners geïntroduceerd als Lector AI aan TIO Business School in Amsterdam en Groningen en verwijzing naar bernarddonners-ai.nl.
- Sectie `Voorwaarden & privacy` toegevoegd met voorwaarden/privacytekst en een expliciete `Ik begrijp dat...` verantwoord-gebruik box.
  - AI als General Purpose Technology
  - waarde komt na de hype / reis geen sprint
  - kritisch denken i.p.v. alleen output produceren
  - “Niet alles wat technologisch kan is ook maatschappelijk gewenst”
  - Bernard als AI-ervaringsdeskundige/docent-context

## Nog nodig van Bernard
1. Definitieve domeinkeuze en domeinregistratie: `trustedagents.nl`.
2. Definitief e-mailadres: bv. `info@trustedagents.nl` of `bernard@trustedagents.nl`.
3. Prijsstrategie: wel/geen maandprijzen tonen in eerste versie.
4. Eerste 2-3 echte cases/proof-points.
5. Welke sectoren eerst: onderwijs, zorg/welzijn, MKB, verenigingen, juridisch/bestuur?
6. Juridische/security claims die we hard kunnen maken: hostingpartij, EU-locatie, backups, logging, verwerkersovereenkomst.
7. Of de site Nederlands-only start of direct NL/EN.

## Volgende stap
Visueel reviewen en daarna iteratie 2 maken: meer premium, scherper gericht op Nederlands MKB en persoonlijker rond Bernard.
