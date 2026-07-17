[English](README.md) · **Français**

# Piloter une production de film générative depuis Claude Code

Notes de méthode d'un cinéaste (Ismaël Joffroy Chandoutis) qui pilote toute la chaîne de production d'un court métrage génératif depuis un cockpit Claude Code CLI + une salle d'écriture Claude AI Project.

🇬🇧 [English version](./README.md)

> Le film en lui-même n'est pas l'objet ici. La **méthode** l'est. Le repo s'adresse aux cinéastes, ingénieurs IA, et chercheurs qui se demandent comment un artiste peut garder l'ownership de sa vision tout en déléguant l'exécution à une équipe d'agents.

---

## 1. La mission

L'idée préexistait. Contraintes de temps dures :

- **48h pleines** pour écrire le texte (voix off narrative long-format, en FR, ensuite traduite en EN pour le voice cloning).
- **24h pleines** pour produire le film : génération image, voice cloning, image-to-video, musique, sound design, mix audio, montage, sous-titres, upload, livraison à un lieu.

Un cinéaste. Un Mac. Une deadline de vernissage non négociable.

Ces notes ne racontent pas une histoire propre. Elles racontent **ce qui s'est vraiment passé** : 60% de la valeur est venue de la méthode, 40% du crisis management. Les deux sont documentés.

---

## 2. L'architecture mentale (corrigée)

Deux instances Claude distinctes, deux objectifs distincts.

### Claude AI Project (web) = La salle d'écriture — **48h, texte seulement**

- Deux fenêtres navigateur ouvertes en parallèle.
- **Head** : un Claude qui juge, critique, structure. Lit un fragment, dit ce qui manque, ce qu'il faut couper, ce qui est vrai.
- **Arms** : un Claude qui écrit, drafte, étend. Reçoit l'instruction de Head et génère.
- Le cinéaste est le **standard téléphonique** entre Head et Arms. Jamais écrire et juger dans la même session — splitter.
- Le pane "knowledge" du Project porte la bible (pitch, références, mood, drafts antérieurs) pour que les deux fenêtres partagent le state.

### Claude Code CLI (terminal) = Le studio de production — **24h, tout le reste**

- Pas un setup spécifique au film. Le cinéaste arrive avec un **harnais** — sa config filmmaker générale : CLAUDE.md global, skills custom, registre d'agents, MCPs, alias shell. Le studio sert pour n'importe quel film, pas que celui-ci.
- Fournit une exécution multi-agents : un agent director (la vision du cinéaste), une équipe de sub-agents spécialisés (worldbuilder, storyboard, generation director, editor council, audio engineer, audit, delivery).
- Switcher entre Claude Project (web) et Claude Code (CLI) **change le type de réponse qu'on obtient**. Le Claude web est plus réflexif, plus critique, plus lent. Le Claude CLI est plus exécutif, plus shell-aware, accepte plus d'outils latéraux. Savoir quand switcher, c'est la moitié de la méthode.

### Pourquoi le split

- Le Project garde le texte inviolable ; la CLI ne modifie jamais la narration source.
- La CLI consomme le texte en input — en lecture seule.
- L'itération sur le texte se fait dans le Project, l'itération sur la production se fait dans la CLI. Jamais de cross-contamination.

### Sélection du mode cognitif dans Claude Code

- **Adaptive think mode** quand il y a ambiguïté / problème créatif ouvert.
- **Off-think mode** quand on conduit une pipeline déterministe (ffmpeg, file ops, transcodage). Plus rapide.
- **Sonnet** pour les flow rapides, les gros sub-agents parallèles, les tâches throughput-bound.
- **Opus** pour le council (analyse multi-perspective du montage), l'agent auteur, la synthèse finale. Tâches quality-bound.

C'est pas optionnel. Mauvais mode = minutes perdues par tour × centaines de tours = heures perdues.

---

## 3. L'équipe d'agents

Claude Code comme atelier multi-agents. Chaque sub-agent a son propre contexte, prompt, et tool-set. L'orchestrateur (toi dans la session CLI principale) délègue les préoccupations, attend les résultats, intègre.

| Agent | Rôle | Quand invoqué | Output |
|---|---|---|---|
| **Director (master)** | Porte la vision du cinéaste. Route. Dit oui/non. | Toujours (session principale). | Décisions. |
| **Worldbuilder** | Génère character sheets, locations, props, palettes de couleur, moodboards. | Pré-prod. | Bibliothèque d'assets. |
| **Storyboard** | Génère vignettes avec captions pour chaque beat. | Pré-prod. | Storyboard.md + image refs. |
| **Asset Manager** | Upload sur CDN, organise le pool, déduplique, tag. | Tout du long. | Asset index. |
| **Generation Director** | Choisit modèle + résolution + mode par plan selon budget/cible qualité. | Par plan. | Plan de génération JSON. |
| **Editor Council** | 5 personas monteurs nommés (Murch, Marker, Schoonmaker, Pagh Andersen, Baxter) produisant des EDLs parallèles. | Phase montage. | 5 EDLs distincts. |
| **Edit Engineer** | Build le vrai montage depuis l'EDL choisi via ffmpeg. | Montage. | montage.mp4. |
| **Audio Engineer** | Sélection musique, mix, mastering. | Post-prod. | audio.m4a. |
| **Subtitle Engineer** | Transcript Whisper → traduction → burn ASS. | Post-prod. | subs.srt + mp4 burné. |
| **Audit (QA)** | Quality check par plan, détection d'hallucinations, détection de doublons. | Par asset généré. | MD tag (FIDELE/BUG/DOUBLON). |
| **Delivery** | Upload, lien partage, composition + envoi email. | Fin. | Email envoyé. |
| **Cost Tracker** | Surveille la dépense sur toutes les plateformes ; alerte sur seuil. | Tout du long. | Budget log. |

**Choix de design critique** : les sub-agents ont un **contexte isolé**. Ils ne voient pas la conversation entière, ils voient seulement leur brief. Ça évite le context bleed et force l'orchestrateur à écrire des briefs propres — c'est la discipline qui fait marcher le système.

---

## 4. Méthodologie de worldbuilding

Voici l'ordre d'opérations qui a émergé. Chaque étape a un livrable.

### Étape 1 — Texte (dans Claude AI Project, 48h)
- VO narrative long-format, voix = la protagoniste ou un narrateur à la troisième personne.
- Output : `script.md` (dans le pane knowledge de Claude Project).

### Étape 2 — Palette de couleurs
- 3-5 tons dominants + 1-2 couleurs accent.
- Approche : demander à l'agent worldbuilder de proposer des palettes depuis le mood du script, puis valider via recherche d'images de référence.
- Output : `palette.md` avec hex codes + images de référence.

### Étape 3 — Character sheets (LoRA training data)
- 5-10 angles par personnage principal (face, 3/4, profil, dos, gros plan, plein pied, états expressifs).
- Approche : Krea 2 avec seed cohérent + prompt personnage, puis itération angle par angle. Optionnel : entraîner un LoRA sur les 5-10 images via Flux 2 / Z Image / Krea 2 LoRA training. Le LoRA devient l'identité stable du personnage à travers toutes les générations suivantes.
- Output : `characters/<name>/sheet_*.png` + `characters/<name>/lora.safetensors` (optionnel).

### Étape 4 — Locations / décors
- 3-5 vues clés par location (plan d'établissement large, moyen, gros, variation lumière, variation heure-du-jour).
- Approche : GPT Image 2 pour les locations héros (suivi de prompt précis), Krea 2 pour les variations ambiantes / atmosphériques.
- Output : `locations/<name>/view_*.png`.

### Étape 5 — Props / artefacts
- Photos de référence des objets clés (l'enceinte, l'urne, le portable, l'artefact qui motorise l'intrigue).
- Même approche que les locations.
- Output : `props/<name>.png`.

### Étape 6 — Storyboard vignettes
- 1-3 vignettes par beat. Un beat = une phrase ou un paragraphe du script.
- Chaque vignette a : caption (ce qui se passe) + image de référence (still généré) + direction caméra (statique / drift lent / pan) + durée cible + cue audio + tag de palette.
- Approche : un sub-agent dédié `storyboard` lit le script + l'output du worldbuilder, propose les vignettes, génère des draft images via Krea 2.
- Output : `storyboard.md` + `storyboard/<beat_id>_v*.png`.

### Étape 7 — Expansion du pool de génération
- Chaque vignette du storyboard donne 3-5 images source alternatives (cadrages différents, variations de lumière).
- Ce pool existe pour donner du choix au monteur, pas pour diluer.
- Approche : batch Krea 2 + GPT Image 2 pour les plans héros uniquement.
- Output : `pool/<beat_id>_v*.png` (typiquement 100-200 PNGs pour un film de 10 min).

### Étape 8 — Génération image-to-video
- 80% du pool : LTX 2.3 (rapide, local ou via fal, $0.02-0.05 par plan en cloud, $0 en local).
- 20% (plans héros, les 15-20 moments visibles "clés") : Seedance 2 Pro 1080p ($0.65-1.04 par plan).
- Mode : image-to-video (i2v). Le PNG drive la frame 0 ; le prompt drive le mouvement. Ça préserve la direction artistique du worldbuilder.
- Output : `rushes/<beat_id>.mp4` (chacun 4-8s).

### Étape 9 — Audit + sélection
- Sub-agent audit extrait une frame à mi-durée de chaque rush, lit avec vision, tag FIDELE / BUG / DOUBLON.
- Les bugs (hallucinations : bras en trop, smartphones dans un monde post-2090, croix qui apparaissent dans des ciels) partent en quarantaine.
- Les doublons (duplicats visuels de la même scène) sont dédupliqués en gardant le meilleur.
- Output : `audit.md` + `pool_validated/` + `pool_quarantine/`.

### Étape 10 — Montage + mix + subs + livraison
- L'editor council produit 5 EDLs en parallèle.
- Le director choisit un EDL ou compose une synthèse.
- L'edit engineer build le master via ffmpeg.
- L'audio engineer mixe VO + drone + accents + tracks spotlight.
- Le subtitle engineer génère SRT, traduit, brûle.
- Le delivery agent upload, génère le lien, drafte l'email, attend la confirmation du cinéaste, envoie.

---

## 5. La stratégie 80/20 de sélection de modèle

Règle empirique : cheap/fast pour **80% d'itération**, premium pour **20% final**.

### Génération d'image

| Cas d'usage | 80% (draft, itérer, moodboard) | 20% (final, héros) |
|---|---|---|
| **Moodboard concept** | Krea 2 (style Midjourney, rapide) | — |
| **Character sheets** | Krea 2 avec seed | GPT Image 2 pour les portraits clés |
| **Locations** | Krea 2 | GPT Image 2 (prompt précis) |
| **Vignettes storyboard** | Krea 2 batch | GPT Image 2 pour les 5-10 stills héros |
| **Données d'entraînement LoRA** | Pipelines Flux 2 / Z Image / Krea 2 LoRA | — |
| **Édition d'image (inpaint, modifier)** | Gemini 2.x / 3.x Flash "nano banana" (édition multimodale) | Photoshop manuel si besoin |

**Pourquoi ce split** : Krea 2 atteint le sweet spot vitesse-qualité-coût — parfait pour les 100-200 images source que tu vas générer. GPT Image 2 (sorti début 2026) suit fidèlement les prompts complexes et excelle aux compositions avec texte ou layouts spatiaux précis — à réserver aux 5-10 plans héros où la fidélité de prompt compte.

**Gemini Flash "nano banana"** : le mode d'édition d'image multimodale est ce qui se rapproche le plus d'un "Photoshop light" via API. À utiliser pour : inpaint d'objets indésirables, ajustement de dominante couleur sur un asset isolé, restyling de la tenue d'un personnage sans regénérer le plan entier.

### Image-to-video

| Cas d'usage | 80% (itération, pool, rushes) | 20% (plans héros finaux) |
|---|---|---|
| **i2v général** | **LTX 2.3** (open source Lightricks, local ou hosted) | **Seedance 2 Pro** |
| **Transitions first-last frame** | LTX 2.3 conditional input | Seedance 2 (mode first_last_frames) |
| **Plans longs (>8s)** | Hunyuan Video (local) ou Wan Video 2.1 | Seedance 2 Pro |
| **High-motion / action** | LTX 2.3 (bon sur le motion) | Seedance 2 Pro 30fps |
| **Cinématique atmosphérique** | LTX 2.3 | Seedance 2 Pro |

**Économie résolution / FPS (référence Seedance 2)** :

| Résolution | FPS | Coût / sec | Cas d'usage |
|---|---|---|---|
| 480p | 24 | $0.06 | Test uniquement |
| 720p | 24 | **$0.10 (fast)** | Pre-viz, rushes |
| 1080p | 24 | **$0.13 (pro)** | Final |
| 1440p+ | 30 | $0.20+ | Cinéma héros only |

**Arbre de décision t2v vs i2v vs v2v** :
- **i2v** = défaut. L'image fixe la frame 0 → préserve la direction artistique → cohérence entre plans.
- **t2v** = seulement pour abstrait / transitionnel / non-character. Risque : drift d'hallucination.
- **v2v** = transfert de style sur footage existant. À utiliser rarement (Runway Gen-4 v2v, Pika, etc.). Cher et délicat.

**Recommandation** : i2v par défaut, t2v seulement quand le prompt texte EST le plan entier (ex. morphs abstraits de logo), v2v presque jamais.

### Voix

- **TTS générique** (voix ElevenLabs, OpenAI TTS) = **ne pas utiliser pour cinéma narratif**. Sonne comme une intro de podcast au mieux. Le voice cloning est la seule voie viable pour le cinéma d'auteur.
- **Voice cloning** : MiniMax `speech-02-hd` via Replicate (`minimax/voice-cloning` → `minimax/speech-02-hd`). ~$3 clone + $0.05 / 1k chars. Sample clean 75s obligatoire.
- **ADR / foley / SFX** : ElevenLabs SFX (text-to-audio pour effets sonores non musicaux).
- **Leçon critique** : UN seul clone pour tout le film. Les shifts de mood viennent du paramètre `speed` + prosodie naturelle, pas d'une mosaïque de clones mood-matched (testé, sonne comme plusieurs personnes).

### Musique

| Cas d'usage | Modèle | Provider | Notes |
|---|---|---|---|
| **Drone / ambient bed** | Lyria 2 | Replicate | Meilleur pour pads tenus, tension cinéma |
| **Hauntology / synthwave** | ElevenLabs Music v3 | ElevenLabs | Bon contrôle de genre |
| **Score / orchestral** | MiniMax Music v2.6 | Replicate | Correct pour cues courts |
| **Club / dance** | ElevenLabs Music v3 | ElevenLabs | Utiliser avec low-pass pour "muffled / heard from outside" |
| **Stable Audio 2.5** | — | fal | Testé, plus faible que Lyria pour le drone |

Layer 2-4 tracks pour la richesse. Drone constant bas (-22 à -28 dB), accents ponctuels mid, club seulement sur scènes spectacle.

### Mix audio

**Pourquoi ffmpeg et pas Logic Pro / Audacity / Pro Tools** :

| | ffmpeg | Logic Pro | Audacity | Pro Tools |
|---|---|---|---|---|
| Scriptable | ✅ Full | Partial (AppleScript / Scripter MIDI) | Partial (Nyquist) | Limité |
| Reproductible | ✅ Même script = même output | ❌ Fichier projet requis | ❌ | ❌ |
| Runs parallèles | ✅ N background processes | ❌ Single instance | ❌ | ❌ |
| License | Free | $200 | Free | $600+/an |
| Mix multi-track | ✅ `amix=inputs=4` | ✅ Mixer visuel | Limité | ✅ Best |
| EQ visuelle / spatial | ❌ | ✅ | Partiel | ✅ |
| Reverb GPU-accelerated | ❌ | ✅ | ❌ | ✅ |
| Sidechain compress | ✅ `sidechaincompress` | ✅ | ❌ | ✅ |

**Verdict** : ffmpeg pour **l'itération** (60+ variantes de mix dans une journée, chacune en 30 secondes). Logic Pro pour **mastering final** si le projet exige du travail spatial / mastering que ffmpeg ne peut pas faire. Pour un court cinépoème en stéréo propre, ffmpeg seul suffit et est largement plus rapide.

### Montage

**Pourquoi ffmpeg et pas Premiere / FCP / Resolve / CapCut** : voir la section comparaison dédiée plus bas.

**Réponse courte** : ffmpeg pour **itérer en sprint**. NLE pour **finaliser** si la complexité visuelle l'exige (color grade, masking, morph cuts). En sprint 24h, ffmpeg gagne.

### Sous-titres

- **whisper.cpp** (`whisper-cli`) pour la transcription EN (local, Apple Silicon natif, modèle GGUF).
- Traduction FR manuelle ou assistée LLM en préservant les timestamps SRT.
- Convertir en `.ass` (SubStation Alpha) pour le contrôle de style.
- Burner via **ffmpeg-full** avec libass activé. Le ffmpeg brew par défaut **n'inclut pas libass** — fail silencieux. `brew install ffmpeg-full`.

---

## 6. Algorithmes de ralenti comparés

Quand ta timeline vidéo est trop courte et qu'il faut étirer un plan ou construire un pacing contemplatif :

| Algorithme | Qualité | Vitesse | Coût | Notes |
|---|---|---|---|---|
| **setpts (duplication de frame)** | Basse (jerky au-delà de 1.5x) | Rapide | Free | À utiliser uniquement pour stretches subtils 1.05-1.2x |
| **minterpolate mci** (ffmpeg motion-compensated interp) | Moyenne | Lent en CPU | Free | Choix par défaut pour ralenti modéré 1.4-2x |
| **RIFE** (NCNN GPU) | Haute | Rapide en GPU | Free | Meilleur open-source, demande setup ncnn ou vapoursynth |
| **FILM** (Google) | Haute | Moyenne | Free | Modèle TF, résultats paper-grade |
| **Topaz Video AI** | Très haute | Lent | $300/an | Commercial, niveau marketing |
| **Twixtor** | Très haute | Lent | $300+ | Plugin AE / Premiere, référence ground truth pour slow-mo |

**Pour cette pipeline** : `minterpolate mci` pour ralenti modéré (1.4-2x), `setpts` pour subtil (1.1-1.2x). RIFE pour plans héros où on peut consommer du temps GPU.

```bash
# minterpolate slow 1.8x avec motion-compensated interpolation
ffmpeg -i in.mp4 -vf "setpts=1.8*PTS,minterpolate=fps=30:mi_mode=mci" out.mp4
```

---

## 7. Choix du format d'édition (EDL vs FCPXML vs OTIO)

| Format | Forces | Cas d'usage |
|---|---|---|
| **EDL (CMX 3600)** | Texte plain, 50 ans d'adoption industrie, trivial à parser, lisible humain, compatible ffmpeg (via traduction concat demuxer) | Quand tes agents monteurs doivent sortir des cuts structurés qu'un script peut consommer. **Utilisé dans ce repo.** |
| **FCPXML** | Métadonnées riches, Apple-native, supporte markers / effets / multi-track | Handoff vers Final Cut Pro pour finalisation. Chemin SpliceKit MCP. |
| **OTIO (OpenTimelineIO)** | Standard ouvert, pont multi-NLE (FCP / Resolve / Premiere lisent tous), lib Python | Interop multi-NLE, future-proofing. |
| **AAF** | Standard industrie pour le haut de gamme | Pipelines Avid. Lourd. |

**Pourquoi ce repo utilise un EDL-like JSON** : chaque agent monteur sort une liste de `[plan_id, durée, position]` entrées triviale pour le build script à consommer. Portable vers OTIO en une passe Python.

---

## 8. Analyse de coût : local vs commercial

### Investissement hardware one-time (pipeline local)

| Item | Coût |
|---|---|
| Mac M-series (M3/M4 Pro/Max, 36GB+ RAM) | $2500-5000 |
| SSD externe 4TB | $300-500 |
| Monitoring audio (casque) | $200-500 |
| **Total** | **$3000-6000 une fois** |

### Coût par film — stack 100% local

| Composant | Outil | Coût |
|---|---|---|
| Image gen | Flux Schnell / Krea local | $0 (électricité) |
| LoRA training | kohya / OneTrainer local | $0 |
| Image edit | InvokeAI / Gemini Flash local-ish | $0 |
| i2v | LTX 2.3 local (ComfyUI) | $0 |
| Voice clone | XTTSv2 / OpenVoice / Tortoise | $0 (qualité sous MiniMax) |
| Musique | MusicGen local | $0 (qualité sous Lyria/ElevenLabs) |
| Montage | ffmpeg | $0 |
| Transcription | whisper.cpp | $0 |
| **Par film** | | **~$0 + électricité** |

### Coût par film — stack 100% commercial (~10 min film, ~80 plans)

| Composant | Outil | Estimation |
|---|---|---|
| Image gen (200 PNGs) | Krea 2 + GPT Image 2 | $15-40 |
| LoRA training (1-2 personnages) | Krea 2 LoRA / Flux fal | $5-15 |
| i2v héros (15 plans Seedance 2 Pro 1080p 6s) | Replicate / PiAPI | $12 |
| i2v rushes (65 plans LTX 2.3 fast 720p 5s) | fal / Replicate | $13 |
| Voice clone | Replicate MiniMax | $5 |
| Musique (3 tracks) | Lyria / ElevenLabs | $10-20 |
| Storage CDN | fal storage | $0 |
| Transcription | whisper.cpp local | $0 |
| **Par film** | | **~$60-110** |

### Recommandation hybride (l'approche de ce repo)

| Phase | Stack | Justification |
|---|---|---|
| Moodboard / 100 draft images | Krea 2 cloud | Vitesse > coût |
| LoRA training | Krea 2 / Flux fal | Évite le setup GPU local |
| i2v rushes (80% des plans) | LTX 2.3 (local si possible, fal sinon) | Itération pas chère |
| i2v héros (20% des plans) | Seedance 2 Pro via Replicate ou PiAPI | Qualité best-in-class |
| Voice cloning | MiniMax via Replicate | Stable, $3 + $5 |
| Musique | Lyria + ElevenLabs Music | Mix sources |
| Montage / mix / subs | ffmpeg-full local | Free, scriptable |
| **Total par film** | | **~$40-80** |

**60-80% d'économies vs all-commercial**, et tu gardes la vitesse du cloud pour les moments où elle compte.

---

## 9. Pourquoi ffmpeg et pas un NLE (étendu)

### Option A — ffmpeg uniquement (cette pipeline)

**Pour :**
- Pas de licence, scriptable, runs parallèles, reproductible (même script = même output sous réserve d'input déterministe).
- Tourne sur Mac mini, pas de dépendance GPU.
- Background tasks : 4 builds de montage en parallèle impossible dans un NLE.

**Contre :**
- Pas de visualisation timeline → composition à l'aveugle.
- Itération lente sur changement de durée de plan (re-render complet).
- Pas de morph cut, pas d'auto-stabilisation, pas de masking, pas de reverb GPU.
- Le styling de sous-titres demande libass + ASS bien formé.

### Option B — Piloter Final Cut Pro depuis Claude Code

Via **SpliceKit** (dylib JSON-RPC in-process, injection in-FCP) → exposé MCP.

**Pour :**
- Visualisation timeline native, color grade, masks, morph cuts, plugins audio.
- Burn de sous-titres natif via captions FCP.

**Contre :**
- RAM/GPU de FCP sur le même Mac.
- Setup SpliceKit spécifique, peut casser sur les updates FCP.
- Pas reproductible (projet FCP ≠ script).

### Option C — Piloter DaVinci Resolve depuis Claude Code

Via **API Python officielle DaVinciResolveScript**.

**Pour :**
- API documentée stable.
- Référence color grading (Resolve = standard cinéma).
- Compositing Fusion.
- Free tier puissant.

**Contre :**
- GUI lourde, boot lent.
- Indirection API Python.

### Option D — Piloter Premiere Pro depuis Claude Code

Via **Adobe MCP** (5 servers : Photoshop / Premiere / AE / Illustrator / InDesign), scripts UXP.

**Pour :**
- Workflow pro, intégration AE.
- UXP / ExtendScript riche.

**Contre :**
- Abonnement Adobe.
- API UXP moins mature que Resolve / SpliceKit.
- Instabilité Premiere sur projets longs.

### Option E — CapCut / iMovie / InVideo

- CapCut : UI automation via Playwright sur app web. Pas d'API sérieuse.
- iMovie : AppleScript limité, pas pro-grade.
- InVideo : SaaS web, Playwright-automatable mais free tier limité.

**Verdict** : utiles pour templates social media volume, pas pour un cinépoème.

### Quand switcher de ffmpeg vers NLE

- Color grading exige une pipeline LUT + 10-bit + look development → **Resolve**.
- VFX lourds / compositing / motion graphics → **AE via Adobe MCP**.
- Audio spatial / Dolby Atmos → **Logic Pro** ou **Pro Tools** (handoff via OMF ou AAF).
- Vitesse pure et reproductibilité en sprint → **ffmpeg**.

---

## 10. Comparaison : plateformes IA de génération (mai 2026)

| Plateforme | Image | i2v | Voice clone | Music | CLI/API | Notes 2026 |
|---|---|---|---|---|---|---|
| **fal.ai** | Flux, etc. | Seedance 2 / LTX 2.3 | MiniMax | Stable Audio | SDK Python riche | Lock de compte fragile ; storage marche même locké |
| **Replicate** | Flux | Seedance 1/2, LTX | MiniMax | Lyria, ACE | API stable | Plus cher mais reliable |
| **PiAPI** | — | Seedance 2 | — | — | REST API derrière Cloudflare WAF, limite 2 jobs concurrents | UA ban sur python-urllib |
| **Krea** | Krea 2, Flux 2, Z Image, LoRA training | Seedance 2 (UI uniquement) | — | — | MCP expose Seedance 1 ; Playwright pour v2 | Meilleur canvas web pour AI moodboarding |
| **ChatGPT image (GPT Image 2)** | OK, prompt-faithful | — | — | — | API OpenAI | Plans héros, composition précise |
| **Gemini Flash "nano banana"** | Édition multimodale | — | — | — | API Google | Meilleur "Photoshop-light" via API |
| **Higgsfield** | — | i2v avec contrôle de motion | — | — | API + CLI | Fort sur motion personnage / danse |
| **Hailuo (MiniMax)** | — | i2v / t2v | speech-02-hd | Music v2.6 | API direct ou via Replicate | Référence voice clone |
| **Runway Gen-4** | — | i2v / t2v / v2v | — | — | API | Référence v2v, cher |
| **LumaLabs (Dream Machine + Ray 2)** | — | i2v avec contrôles caméra | — | — | API | Camera control via prompt est fort |
| **OpenAI Sora (API)** | — | t2v principalement | — | — | API access limité | Haute qualité mais t2v-first |
| **LTX 2.3 (Lightricks)** | — | i2v open-source | — | — | Hugging Face / ComfyUI local | **Défaut pour 80% itération** |
| **Hunyuan Video (Tencent)** | — | t2v / i2v open | — | — | HF / ComfyUI local | Capacité plans longs |
| **Wan Video 2.1 (Alibaba)** | — | i2v open | — | — | HF / ComfyUI local | Fort sur mains et visages |
| **CogVideoX** | — | i2v / t2v open | — | — | HF / ComfyUI local | Léger |
| **Pika** | — | i2v | — | — | API | Généraliste, qualité moyenne |
| **ElevenLabs** | — | — | Voice clone, SFX, Music v3 | Music v3 | API stable | Meilleur écosystème audio |
| **Suno** | — | — | — | Music | API | Meilleure génération de chanson si tu veux du vocal |
| **MusicGen / AudioCraft (Meta)** | — | — | — | Music | HF local | Musique locale gratuite |

**Recommandation pratique** : ne jamais dépendre d'un seul provider. La pipeline décrite dans ce repo tourne sur **fal (storage) + Replicate (génération + voice clone) + Krea 2 (moodboard) + LTX 2.3 (rushes i2v) + Seedance 2 Pro (plans héros) + ElevenLabs (musique + SFX) + whisper.cpp (transcription) + ffmpeg-full (montage)**.

---

## 11. Taxonomie d'assets worldbuilding (ce que tu génères avant de couper)

La bibliothèque d'assets dont un film a besoin **avant que le montage puisse commencer** :

```
project/
├── script.md                           # le texte (depuis Claude Project)
├── palette.md                          # 3-5 dominants + 1-2 accents
├── characters/
│   └── <name>/
│       ├── sheet_front.png             # character sheet, 5-10 angles
│       ├── sheet_3q.png
│       ├── sheet_profile.png
│       ├── sheet_back.png
│       ├── sheet_close.png
│       ├── sheet_full.png
│       ├── sheet_expressive_*.png
│       └── lora.safetensors            # LoRA optionnel pour identité stable
├── locations/
│   └── <name>/
│       ├── view_wide.png               # establishing
│       ├── view_medium.png
│       ├── view_close.png
│       ├── view_night.png
│       └── view_dawn.png
├── props/
│   └── <name>.png                      # référence pour chaque objet clé
├── storyboard.md                       # vignettes + captions par beat
├── storyboard/
│   └── beat_001_v1.png                 # vignette images, 1-3 par beat
├── pool/                               # images source final-grade pour i2v
│   └── beat_001_v*.png                 # 3-5 alternatives par vignette
├── rushes/                             # outputs i2v
│   └── beat_001.mp4
├── audit.md                            # tagging FIDELE/BUG/DOUBLON
├── pool_validated/
├── pool_quarantine/
├── voice/
│   ├── sample_clean.wav                # sample propre 75s pour clone
│   ├── vo.mp3                          # VO générée
│   └── vo_segments/                    # cuts par segment si besoin
├── music/
│   ├── drone.wav
│   ├── accents.mp3
│   └── club.mp3
├── edl/
│   ├── murch.md                        # monteur #1
│   ├── marker.md                       # monteur #2
│   ├── schoonmaker.md                  # monteur #3
│   ├── pagh_andersen.md                # monteur #4
│   └── baxter.md                       # monteur #5
├── subs/
│   ├── vo.srt                          # whisper.cpp EN
│   └── vo_fr.srt                       # FR traduit
├── builds/
│   ├── V0.1_murch.mp4
│   ├── V0.2_marker.mp4
│   └── V1.0_final.mp4
└── delivery/
    ├── master_h264.mp4
    └── email_draft.md
```

Chaque étape a un livrable. Chaque livrable a sa place. L'agent orchestrateur lit et écrit à travers cet arbre.

---

## 12. Edit grammar : teach l'agent TA signature

Les personas monteurs génériques (Murch, Marker, etc.) te donnent une grammaire cinéma générique. Pas **ta** grammaire. Le workaround pas cher en sprint : les invoquer comme "council" pour la diversité de perspective, puis laisser le director agent synthétiser.

La vraie solution : **donner à manger tes films passés à un modèle vision et extraire ta signature**.

Ce repo inclut (ou inclura) `ISMAEL_EDIT_GRAMMAR.md` — une synthèse de 4 films du cinéaste (Maalbeek, Swatted, Ondes Noires, Rewild) analysés via **Gemini 2.x/3.x Pro** input vidéo multimodal. L'output :

- Durée moyenne de plan par film et à travers le corpus
- Types de raccords et leur distribution
- Patterns d'offset image-son
- Effets refusés (ce que ce cinéaste ne fait JAMAIS)
- Plans tenus long (ce qu'il tient 20+ secondes et pourquoi)
- Motifs visuels et cadrages récurrents
- Tendances de couleur
- Patterns de plan de fermeture

Ce document devient une **bible** injectée dans Claude Code via `CLAUDE.md` (niveau projet) ou un skill custom. Chaque futur film que l'agent aide à construire suivra cette grammaire par défaut, avec le cinéaste qui override au cas par cas.

**C'est la méta-méthode** : l'agent n'apprend pas ta grammaire en chattant avec toi. Il l'apprend en se faisant montrer ton œuvre.

> Si tu n'as pas de corpus encore — emprunte. Choisis 3-5 cinéastes dont tu admires la grammaire, donne à manger à Gemini, extrais, mixe, override. L'agent produira dans cette grammaire mixée jusqu'à ce que tu aies tes propres films à lui donner à manger.

---

## 13. Voice cloning > TTS (étendu)

Chaque TTS générique testé (ElevenLabs v3 avec tags `[breath]` `[tearful]`, voix posées Sarah / Matilda / River / Charlotte / Bianca / Alice) sonnait **"drama collégien"**. La voix portait mal le texte — l'oreille décrochait.

Voice cloning d'une voix de cinéma sur 75s de sample propre = changement de catégorie. Le clone reproduit ce que le TTS ne peut pas : le souffle, le tell vocal, le grain, la prosodie.

**Trois leçons dures** :
- **Sample propre obligatoire**. Un sample où la voix cible parle avec une autre voix contamine le clone (il dérive vers une voix moyenne mixte/masculinisée). Toujours isoler un extrait monophonique d'un moment où seule la cible parle.
- **Un seul clone pour tout le film** bat quatre clones mood-matched. Les shifts de mood viennent du paramètre `speed` + prosodie naturelle, pas d'une mosaïque vocale.
- **Replicate `minimax/voice-cloning` → `minimax/speech-02-hd`** : leader qualité à fin mai 2026. ~$3 clone + $0.05/1k chars. Alternative : fal `MiniMax`, qualité équivalente.

---

## 14. Fails techniques (catalogués)

### fal.ai : compte locké malgré balance positive
Top-up appliqué → flag de lock pas cleared infra-side. Storage continue à marcher mais génération bloquée. La dépendance single-provider est fragile.

### PiAPI : ban User-Agent + limite 2 jobs concurrents
- `Python-urllib` User-Agent → HTTP 403 systématique (Cloudflare WAF). Patch : header `User-Agent: Mozilla/5.0...`.
- Plan basique cap dur **2 tâches actives**. Le launcher doit submit-attendre-submit. Pour 17 plans × 2-3 min : ~40 min de queue.
- Zombie pending tasks bloquent les slots ; utiliser endpoint DELETE pour cancel.

### Krea expose Seedance via UI mais pas via MCP
Le MCP Krea officiel expose seulement Seedance 1.0. v2.0 uniquement via UI web → utilisable depuis Claude Code uniquement via **Playwright / Browser Use** automation, pas via CLI directe.

### Video looping = fausses répétitions perçues
Looper (`-stream_loop -1`) pour matcher la durée VO → le spectateur voit les premiers plans réapparaître = perçu comme répétitions intentionnelles cassées. **Ne pas looper. Ralentir plus. Ajouter de la matière.**

### Mapping prompt ↔ image mismatch
Identification rapide en batch des timestamps PNG → frames similaires confondues → mauvais prompt appliqué à la mauvaise image → hallucination IA par-dessus le mismatch. **L'audit visuel (extract frame + read with vision agent + tag) est obligatoire** avant intégration.

### libass manquant dans le ffmpeg brew par défaut
`brew install ffmpeg` (8.x) ship **sans libass** → le filter `subtitles=*.srt` retourne `No option name near`. Installer `ffmpeg-full` pour le support libass. Symptôme trompeur : ffmpeg marche pour tout sauf le burn de subs.

### Whisperx → erreur import transformers
`whisperx` casse régulièrement sur l'import `Wav2Vec2ForCTC` quand transformers update. Fallback : **whisper.cpp** via `whisper-cli` (Apple Silicon natif, modèle GGUF).

### Ban Cloudflare 1010
Les APIs Cloudflare-protégées (PiAPI, d'autres) bannent les signatures de requête sans User-Agent navigateur. Toujours set un UA navigateur réaliste quand on scripte du HTTP outbound depuis Python.

### Truncation audio par défaut (-shortest)
`ffmpeg -shortest` tronque l'audio à la durée vidéo la plus courte — kill silencieux de la VO quand video < audio. Solution : drop `-shortest`, use `-t <vo_duration>`, ou étendre la vidéo via slowdown / matière supplémentaire.

### Facteur slow mal calibré
Premier essai : slow 1.4x → vidéo 4-5 min pour 9:53 VO → 4+ min de frame frozen à la fin. Leçon dure : pre-compute la durée naturelle totale du pool, dérive le facteur slow nécessaire, valide avant d'encoder.

---

## 15. Wins techniques (catalogués)

- **Background tasks parallèles** : 4 builds de montage + génération PiAPI + 5 agents monteurs simultanément. Le flag `run_in_background` de la CLI est l'unique activateur.
- **Sub-agents pour analyse visuelle** : un sub-agent `audit` extrait les frames de 50+ rushes, lit avec vision, écrit un MD tagué en 6 min. ~30 min sauvées par cycle d'audit.
- **Single-pass 4-layer audio mix** : `ffmpeg -i vo -i drone -i accents -i club -filter_complex "amix=inputs=4..."` en un seul process.
- **Pivot inter-provider sans perte** : CDN storage sur fal (gratuit, ne lock pas avec le compte de génération) + génération sur provider indépendant → URLs portables entre services.
- **Email + Drive depuis CLI** : `gws drive +upload` + `mail-cli` → lien public + email envoyé en deux commandes.
- **Whisper.cpp Apple Silicon natif** : plus rapide que whisper-x Python, pas d'enfer de dépendances Python, ggml-small.bin = 488MB et qualité acceptable pour transcription VO.

---

## 16. Wins artistiques

- **L'editor council fait émerger des désaccords structurels** qui sont le sujet du film (Schoonmaker valorise le néon aquarium comme onirique ; Pagh Andersen le bannit comme mirage capitaliste). Le désaccord devient matière de montage.
- **Voice-cloning d'un timbre signature** déplace le travail d'amateur à programmable-par-comité.
- **Slow modéré 1.5-1.8x** sur plans contemplatifs = signature visuelle subtile, onirique, sans tomber dans le "slow-mo publicitaire".
- **Sous-titres FR brûlés** transforment un objet bilingue/anglophone en objet français recevable pour la programmation francophone.
- **La contrainte 24h** comme moteur créatif (pas le temps de second-guesser, plus de temps pour l'instinct) — mais attention au tunnel cognitif (voir limites plus bas).

---

## 17. Limites honnêtes de cette méthode

Une note de méthode est malhonnête si elle vend le rêve. Les limites dures :

- **60% de la valeur est venue de la méthode, 40% du crisis management.** Ce repo documente les deux mais si tu traites le crisis management comme méthode, tu vas planter.
- **Bugs livrés non vus**. Le sprint 24h force à shipper des objets que tu n'as pas pleinement validés. La pipeline peut produire un MP4 final avec un smartphone halluciné en 2095 que personne n'a vu. Planifier un cycle de review post-livraison, ne pas prétendre que le final-on-deadline est le final-final.
- **Editor council = prothèse intellectuelle, pas vrai mécanisme de décision**. Dans la chaleur d'un sprint, tu vas écarter le monteur dont la grammaire diverge le plus de la tienne ("il est fou, on n'écoute pas"). Le council légitime tes intuitions existantes plus qu'il ne te challenge. Pour l'utiliser comme vrai challenger, il faut honorer l'EDL dissident même quand ça fait mal.
- **Pas de pause cognitive pendant un sprint 24h = effet tunnel**. Tu fais des décisions de process, pas des décisions créatives. Les décisions créatives ont été prises avant (pendant les 48h de texte), ou seront prises post-hoc (pendant la réflexion du projet suivant). Un sprint 24h c'est de l'exécution, pas de la création. Ne pas confondre.
- **Non-déterminisme IA**. La "reproductibilité" de la pipeline est partielle — même script, mêmes prompts, mêmes seeds où applicable, mais les modèles i2v drift entre runs. Le même film exact ne peut pas être fait deux fois. Planifier la variance, pas la reproductibilité.
- **Single-provider single-point-of-failure**. La session a failli mourir quand fal a lock le compte en pleine production. Toujours avoir un provider de backup warmed up avant d'en avoir besoin.
- **Coût de l'enveloppe CLI**. Les sessions Claude Code multi-heures consomment des tokens. Sonnet flow + Opus council = plusieurs dollars par session. L'estimation "$60-110 par film" n'inclut pas les tokens Claude (~$20-50 pour une session 24h). À factoriser.

---

## 18. Lessons learned (consolidées)

1. **Split two-mind writer** (Head + Arms dans deux fenêtres Claude Project) > une fenêtre qui fait les deux.
2. **La CLI Claude est ton studio**, pas ton écrivain. Garder le texte inviolable dans le Project.
3. **Voice cloning > TTS** pour tout projet narratif. Pas optionnel.
4. **CDN Storage séparé du compte de génération** = résilience.
5. **Stratégie 80/20 model** : cheap+fast pour 80% itération, premium pour 20% final.
6. **Sub-agents > prompts monolithiques** pour les tâches spécialisées.
7. **Background tasks parallèles** pour tout ce qui peut tourner pendant que tu réfléchis.
8. **Audit avant d'intégrer** — chaque asset généré est validé visuellement.
9. **Ne pas looper la vidéo** — ralentir modérément ou générer plus.
10. **ffmpeg pour itérer vite, NLE pour finaliser** si nécessaire.
11. **Montrer chaque draft d'email avant envoi** — la CLI envoie instantanément, c'est précisément pour ça qu'un checkpoint humain est obligatoire.
12. **Donner à manger les films passés à un modèle vision** pour extraire ta grammaire. L'agent doit apprendre de ton œuvre, pas de tes chats.
13. **Coût local vs commercial** : l'hybride gagne. Local pour itérer, commercial pour les moments héros.
14. **Honorer la deadline comme contrainte, pas comme loi**. Un film livré avec bugs est pire qu'un film livré demain.

---

## 19. Tools summary (mai 2026)

**CLI / dev** : Claude Code (Anthropic), `gh`, `gws`, `mail-cli` (custom), `gdrive`, `rclone`, `whisper-cli` (whisper.cpp), `ffmpeg`, `ffmpeg-full` (libass), `gemini` CLI, `python3`, `curl`, `playwright`.

**Plateformes IA** : fal.ai (storage + i2v + clone, fragile), Replicate (i2v + clone + music, reliable), PiAPI (Seedance 2 i2v, Cloudflare-protégé), Krea 2 (moodboard + LoRA, web-first), ChatGPT (image), Gemini (édition image + analyse vidéo), ElevenLabs (TTS + music + SFX), MiniMax (voice clone via Replicate ou fal), LumaLabs (i2v alt), Higgsfield (i2v motion-controlled), Runway (v2v).

**Modèles (mai 2026)** : Seedance 2.0 Pro / Fast (ByteDance i2v), LTX 2.3 (Lightricks open i2v), Hunyuan Video (Tencent open), Wan Video 2.1 (Alibaba open), Flux 2 / Z Image (open image gen + LoRA), GPT Image 2 (OpenAI), Krea 2 (Krea native), MiniMax `speech-02-hd` (voice clone), Lyria 2 (music), ElevenLabs Music v3, Whisper small (transcribe), Gemini 2.5 / 3.x Pro (analyse multimodale).

**MCPs notables** : Adobe (Photoshop / Premiere / AE / Illustrator / InDesign), SpliceKit (FCP), Blender, Playwright, Pinecone, clipboard-vision, ComfyUI, Krea, Beeper, Postiz.

**Personas sub-agents (dans Claude Code)** : Director, Worldbuilder, Storyboard, Asset Manager, Generation Director, Editor Council (5 personas), Audio Engineer, Subtitle Engineer, Audit, Delivery, Cost Tracker.

---

## 20. Coda

Ce n'est pas un kit clé-en-main. Chaque film a sa propre pipeline. Le takeaway : **piloter une chaîne de production complète depuis Claude Code est faisable et fluide pour un cinéaste qui sait ce qu'il veut**, à condition d'accepter trois trade-offs :

- Itération de fine-tuning plus lente qu'un NLE.
- Pas de visualisation timeline native pendant le montage ffmpeg.
- Dépendance sur des plateformes externes fragiles (locks, rate limits, API changes, model rotations).

Le gain : **reproductibilité, parallélisme, traçabilité**, et surtout — **rester dans un seul environnement mental** pendant un sprint, sans context-switch entre 6 applications. Le cinéaste reste dans la tête où le film vit.

Le pari plus profond : **l'équipe d'agents va devenir ton studio**. Worldbuilder, Storyboard, Generation Director, Editor Council, Audio Engineer — chacun un agent spécialiste qui apprend ta grammaire à travers plusieurs projets. Le prochain sprint sera 18h au lieu de 24h. Celui d'après 12h. Le texte (la seule chose qui ne peut pas être automatisée) garde ses 48h.

Ce qui est délégué, ce qui reste tien, devient la prochaine question politique du cinéma.

---

*Voir aussi : [`ISMAEL_EDIT_GRAMMAR.md`](./ISMAEL_EDIT_GRAMMAR.md) (work in progress, extrait de Maalbeek / Swatted / Ondes Noires / Rewild via Gemini multimodal). [`scripts/`](./scripts) pour les bouts runnables.*

*Notes prises le lendemain d'un sprint ~24h ; étendues ensuite à tête reposée.*
