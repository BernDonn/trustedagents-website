# Session TrustedAgents

## Doel van deze sessie
Trusted Agents verder uitwerken als professionele website en propositie voor Nederlandse MKB-klanten, inclusief:
- AI-agent diensten
- veilige deployment
- juridische bescherming
- privacy/AVG-positionering
- Bernard als Lector AI bij TIO Business School Amsterdam en Groningen
- onboarding-app testen
- eerste Hetzner-structuur voorbereiden

## Kernbesluiten

### Positionering
- Merk/domein: **Trusted Agents** / `trustedagents.nl`
- Doelgroep: **Nederlandse MKB-bedrijven**
- Geen EU-brede of institutionele positionering
- Bernard profileren als **Lector AI** bij TIO Business School Amsterdam en Groningen
- Publieke site mag **Trustable** of `trustable.nl` **niet** noemen

### Productstructuur
- **Hermes** = managed AI agents
- **OpenClaw** = open-source / self-hosting framework
- Snelle kanalen voor deployment:
  - Telegram bot
  - WhatsApp Business API

### Publieke framing en embargo
- Project Taxi / geheugensteun publiek alleen **abstract** benoemen
- Geen publieke verwijzingen naar:
  - Alzheimer / dementie
  - Adriaan
  - concrete scenario’s, namen of workflows
- Framing blijft: rust, regie, overzicht, dagelijkse ondersteuning

### Model- en toegangsstrategie
- Ondersteunde routes op de site:
  - Anthropic API
  - OpenRouter API
  - ChatGPT / OpenAI Codex OAuth
- API-keys horen alleen in private config, environment of workspace
- Niet op de website, niet in README, niet in screenshots of logs

### Hostingrichting
- Mogelijke draaiplekken benoemd:
  - eigen Mac
  - Mac mini
  - VPS / Hostinger
- GitHub Pages / gratis hosting was eerste publicatiepad; Vercel bleef optie
- Hostinger affiliate-programma heeft voorkeur boven referral zodra concreet inzetbaar

### Juridisch en risico-afdekking
Toegevoegd of besloten:
- Algemene Voorwaarden
- Privacybeleid
- prominente checkbox met strekking: gebruiker begrijpt zelf verantwoordelijk te blijven
- Website moet professioneel ogen; geen tekst van het type “jurist moet hier nog naar kijken”

## Wat inhoudelijk is uitgewerkt op de website

### Website-secties en inhoud
Toegevoegd of aangescherpt:
- Hermes en OpenClaw productcards
- “Deploy je agent” sectie
- modelkeuze en toegang
- hostingsectie
- juridische sectie
- MKB-positionering
- Bernard-profiel met verwijzing naar `bernarddonners-ai.nl`
- abstracte mensgerichte ondersteuning / geheugensteun-card
- embargo-sectie voor gevoelige pilotdetails

### Vormgeving
- Typografie aangepast richting **Hanken Grotesk**
- Navigatie verbeterd tegen overflow
- Mobiele/kleinere schermweergave aangepast

### Opschoning publieke inhoud
Bevestigd verwijderd uit publieke/source-teksten:
- Trustable-verwijzingen
- Europese/institutionele positionering
- ongewenste termen rond dementie/Alzheimer
- concrete pilotdetails en namen

## Relevante commits uit de sessie
- `0bed176` — Add OpenClaw and deploy agent flow
- `9db28f7` — Explain model access options
- `804bb26` — Add memory support pilot and hosting options
- `52ad29c` — Prepare Hostinger partner discount wording
- `749823b` — Embargo detailed memory support pilot text
- `6f12fca` — Align typography with Trustable style
- `92ba02a` — Refocus site on Dutch SME positioning
- `d8dca4f` — Add Hetzner managed node scaffold
- `7fc5d28` — Add one-command onboarding demo runner

## Onboarding-app: wat gebeurde er

### Probleem
Bij het testen van de onboarding-app was het shell-commando aan elkaar geplakt, waardoor het pad fout werd gelezen.

Concreet patroon:
- `cd .../apps/onboarding`
- en `source .venv/bin/activate`

waren onbedoeld aan elkaar geplakt, waardoor iets in de vorm van `onboardingsource` ontstond.

### Oplossing
- Commando’s apart uitvoeren of met scheidingstekens
- Virtualenv opnieuw gebruiken
- Package opnieuw installeren
- Eenvoudiger startpad toegevoegd via een one-command demo runner

### Resultaat
- import werkte weer
- tests liepen groen
- er is een eenvoudiger startscript toegevoegd voor lokaal testen
- Bernard heeft bevestigd dat de demo is getest en dat zowel **Onboarding** als **Admin** werken

## Hetzner / infrastructuur

### Wat is opgezet
Er is een eerste scaffold aangemaakt voor een managed-node opzet in:
- `infra/hetzner/`

Met onder andere:
- provider/versions-configuratie
- variabelen
- hoofdconfiguratie
- outputs
- cloud-init template
- voorbeeld tfvars
- lokale checkscript
- `.gitignore` voor state/secrets/private keys

### Wat bewust nog niet is gedaan
- geen echte VPS aangemaakt
- geen apply uitgevoerd
- geen productie-omgeving gestart

### Advies dat uit de sessie kwam
- eerste managed node in **CX32-klasse**
- voorlopig begrenzen op ongeveer **10 betalende bots**
- backups aan
- staging en productie scheiden
- zwaardere klanten later eventueel dedicated

## Security- en werkafspraken
- Secrets nooit in chat, repo, screenshots of logs laten terugkomen
- Tokens altijd behandelen als geheim, ook als tijdelijk
- Voor Terraform/Hetzner is export via environment variabele de juiste route
- Bij terminalwerk opdrachten scheiden met nieuwe regels of `&&`

## Belangrijke projectbestanden
- `README.md`
- `DEPLOYMENT_AUTOMATION.md`
- `index.html`
- `apps/onboarding/README.md`
- `infra/hetzner/README.md`
- `infra/hetzner/NEXT_STEPS_STAGING.md`

## Openstaande punten / vervolg
1. Eventueel legal-wijzigingen nog nalopen op commitstatus
2. Publicatiepad kiezen: GitHub Pages of Vercel
3. Domeinkoppeling voor `trustedagents.nl`
4. Eventuele e-mailsetup voor Trusted Agents
5. Hostinger affiliate-verwerking zodra definitief
6. Verdere uitwerking meertaligheid indien gewenst
7. Verdere uitwerking managed-agent pricing / VPS-model
8. Echte staging of productie-apply pas na expliciet akkoord en veilige tokenconfiguratie

## Bron van deze samenvatting
Samengesteld uit de relevante Trusted Agents-passages uit eerdere Hermes-sessiegeschiedenis, vooral een sessie die nu nog de titel **“Duitse e-mail aan Sixt Düsseldorf”** draagt maar later Trusted Agents-werk bevat.
