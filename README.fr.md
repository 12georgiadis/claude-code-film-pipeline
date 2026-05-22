# Piloting a Generative Cinépoème from Claude Code

**~12 heures, une seule session, un seul prompt window.**
Notes de méthode d'un cinéaste qui pilote toute la chaîne de production d'un court métrage IA depuis Claude Code (CLI Anthropic) et un Claude AI Project.

Le film lui-même n'est pas l'objet ici. La **méthode** l'est.

---

## Le setup

- **CLI Claude Code** (terminal mac) comme cockpit principal — tout passe par là : génération image, image-to-video, voice cloning, TTS, music, sound design, mix audio, montage ffmpeg, sous-titres, upload, envoi mail.
- **Claude AI Project** (web) comme **mémoire externe** : pitch, références, mood, EDLs des cinq monteurs convoqués comme agents (Murch, Marker, Schoonmaker, Pagh Andersen, Baxter). Le project agit comme la "bible" persistante que la CLI lit au démarrage.
- **Sous-agents** (`/agents`) pour les tâches qui nécessitent un contexte propre : un agent "analyse visuelle pool" (extraction frames + vision Claude), cinq agents "monteur" qui produisent chacun leur EDL distinct, un agent "audit pool" qui tag chaque plan FIDELE / BUG / DOUBLON.
- **Background tasks** (`run_in_background`) pour paralléliser génération + build + upload sans bloquer la conversation.

---

## La pipeline (ordre d'opération)

1. **Image source** — ChatGPT image (gpt-image-1) génère un pool de PNGs depuis prompts itératifs. Output : ~120 PNGs sur disque local.
2. **Upload CDN** — chaque PNG uploadée sur **fal storage** (gratuit, marche même quand le compte fal est locked pour génération — pratique). URL publique consommable par n'importe quelle plateforme i2v.
3. **Image-to-video** — Seedance 2.0 via deux plateformes en parallèle (fail vs win, voir plus bas).
4. **Voice cloning** — sample audio propre uploadé, voice_id généré, TTS avec ce voice_id. Le résultat dépasse de loin tout TTS générique disponible — c'est le **seul moyen** d'obtenir un timbre signature reconnaissable.
5. **Music** — drone ambient + hauntology + club, trois pistes générées séparément, mixées en couches.
6. **Mix audio live ffmpeg** — VO + drone + accents + club, ducking modéré via niveaux fixes (sidechain compress essayé puis simplifié).
7. **Montage ffmpeg** — `concat demuxer` pour hard cuts, `setpts` pour slow modéré, `minterpolate` pour smoothing.
8. **Sous-titres** — whisper.cpp local → SRT EN → traduction FR manuelle → ASS/SRT → burn via libass (requiert un build ffmpeg "full").
9. **Upload + envoi** — Google Drive via `gws` CLI, lien public, email envoyé via mail-cli depuis Claude Code.

---

## Voice cloning > TTS générique

Tous les TTS testés (ElevenLabs v3 avec tags `[breath]` `[tearful]`, voix posées Sarah / Matilda / River / Charlotte / Bianca / Alice) sonnent **"drama collégien"**. La voix porte mal le texte, l'oreille décroche.

**Voice cloning** d'une voix de cinéma (timbre signature, intonation reconnaissable, prosodie naturelle) sur 75 secondes de sample propre = changement de catégorie. Le clone reproduit ce que le TTS ne peut pas : la respiration entre phrases, le tell vocal, le grain.

Trois leçons :
- **Sample propre obligatoire** : un sample où la voix-cible parle avec une autre voix contamine le clone (il dérive vers une voix mixte / masculinisée). Toujours isoler un extrait monophonique.
- **Un seul clone pour tout le film** est meilleur que quatre clones mood-matched. Les changements de mood se font via paramètres de speed et prosodie naturelle, pas via mosaïque vocale.
- **Replicate `minimax/voice-cloning`** ou **fal MiniMax** : équivalents qualité, ~$3 le clone + $0.05 / 1k chars.

---

## Fails techniques

### fal.ai : compte locked malgré balance positive
Après top-up, le flag de lock côté infra n'est pas levé. Tickets support sans réponse. Storage continue à fonctionner (upload OK) mais génération bloquée. **Toute pipeline dépendante d'un seul provider est fragile.**

### PiAPI : User-Agent ban + limite 2 jobs concurrents
- ffmpeg CLI puis `urllib.request` Python = User-Agent `Python-urllib` blacklisté par Cloudflare → HTTP 403 systématique. Patch : header `User-Agent: Mozilla/5.0...`.
- Plan basique de PiAPI = limite **2 tâches actives** en même temps. Le launcher doit submit, attendre fin, submit suivant. Pour 17 plans à 2-3 min chacun, ça donne ~40 min de queue.
- Zombie tasks bloquent les slots (`pending` jamais résolu) — il faut un endpoint DELETE pour cancel.

### Krea expose Seedance via UI mais pas via MCP
Le MCP officiel Krea n'expose que Seedance 1.0. La version 2.0 n'est accessible que via l'interface web — donc utilisable depuis Claude Code uniquement via **Playwright / Browser Use** (automation web), pas via CLI directe. Ralentit la pipeline.

### Le looping vidéo ffmpeg = fausses répétitions perçues
Pour matcher la durée de la VO quand le matériel image manquait, j'ai bouclé la vidéo (`-stream_loop -1`). Catastrophe : le spectateur voit les premiers plans réapparaître = lecture comme "répétitions volontaires" cassées. Solution propre : **augmenter le slowdown global** ou **ajouter du matériel**, pas boucler.

### Mapping prompt ↔ image incorrect
Quand on identifie 17 timestamps PNG via un batch Read rapide, on confond facilement des cadres similaires. Un prompt "main mécanique top-down sur yeux" appliqué à une image qui contient en réalité "Mira allongée sur alligator" produit une hallucination mixte. **Audit visuel obligatoire** : extraire une frame de chaque plan, lire avec un agent vision, tagger.

### libass manquant dans le binaire ffmpeg brew par défaut
`brew install ffmpeg` (8.x) n'inclut pas `libass` — donc le filter `subtitles=*.srt` retourne `No option name near`. Il faut `ffmpeg-full` qui compile avec `--enable-libass`. Symptôme trompeur : ffmpeg "marche" pour tout sauf le burn de subs.

### Whisperx → erreur import transformers
`whisperx` se casse régulièrement sur le `Wav2Vec2ForCTC` import quand transformers se met à jour. Fallback : **whisper.cpp** via `whisper-cli` (Apple Silicon natif, modèle GGUF).

---

## Wins techniques

- **Background tasks parallèles** : 4 builds ffmpeg en parallèle + batch PiAPI + 5 agents monteur en simultané, sans bloquer la session principale.
- **Sub-agents pour analyse visuelle** : un agent dédié extrait les frames de 50+ rushes, les analyse avec vision Claude, écrit un audit MD avec tags FIDELE/BUG/DOUBLON. Économise 30+ min de revue manuelle.
- **Mix audio en passe unique** : `ffmpeg -i vo -i drone -i disaster -i club -filter_complex "amix=inputs=4..."` produit le mix complet en un seul process.
- **Pivot inter-provider sans perte** : storage CDN sur fal (gratuit) + génération sur PiAPI (compte indépendant), les URLs publiques fonctionnent quelle que soit la plateforme i2v consommatrice.
- **Email + Drive depuis CLI** : `gws drive +upload` + `mail-cli` = lien public Drive généré + email envoyé aux destinataires en deux commandes.

---

## Wins artistiques

- **Council de monteurs** : pousser cinq agents-monteurs (Murch / Marker / Schoonmaker / Pagh Andersen / Baxter) à proposer chacun leur EDL distinct sur le même pool révèle des **désaccords structurels** qui sont le sujet même du film (par exemple : Schoonmaker valorise les plans aquarium néon comme onirisme, Pagh Andersen les bannit comme mirages capitalistes). Ce désaccord devient matière de montage.
- **Voice-clonage d'un timbre signature** (vs TTS générique) déplace la matière d'un side-project amateur à un projet qui peut tenir devant un comité de programmation.
- **Ralenti modéré 1.5-1.8x** sur plans contemplatifs = signature visuelle subtile, onirique, sans devenir "slow-motion publicitaire".
- **Sous-titres FR brûlés** transforme un objet bilingue/anglophone en objet français recevable par les programmations francophones.

---

## Comparaison : faire le montage avec ffmpeg vs piloter un NLE

### Option A — ffmpeg uniquement (cette pipeline)

**Pour :**
- Pas de licence, pas de GUI, scriptable à l'infini.
- Reproductible : le même script produit le même montage avec un seed différent.
- Background tasks parallèles : 4 montages en simultané, impossible dans un NLE.
- Aucune dépendance à un Mac avec GPU performant — passe partout, même sur un Mac mini.
- Coût zéro.

**Contre :**
- Pas de visualisation timeline. On compose à l'aveugle.
- Itérations lentes : chaque changement de durée d'un plan = re-render complet.
- Pas de morph cut, pas de stabilisation, pas de masking automatique.
- Audio mix limité à `amix` + `sidechaincompress` — pas d'EQ visuelle, pas de spatialisation aisée.
- Subtitle styling difficile sans libass + ASS bien formé.

### Option B — Piloter Final Cut Pro depuis Claude Code

Existe : **SpliceKit** (in-process dylib JSON-RPC injecté dans FCP), accessible via MCP. Méthode utilisée par certains cinéastes "AI-native". Permet à Claude Code d'ouvrir un projet FCP, blade, déplacer des clips, ajouter des effets, exporter.

**Pour :**
- Visualisation timeline native.
- Effets / color grade / masks / morph cuts professionnels.
- Audio mix puissant via plugins FCP.
- Burn subs natif via captions générées dans FCP.
- Workflow connu de la post-prod cinéma.

**Contre :**
- FCP doit tourner en parallèle, consomme RAM / GPU sur le même Mac.
- Le MCP SpliceKit nécessite un setup spécifique, peut casser sur les mises à jour FCP.
- Pas reproductible : un projet FCP n'est pas re-runable depuis un script comme un .sh ffmpeg.
- Coût licence FCP.

### Option C — Piloter DaVinci Resolve depuis Claude Code

DaVinci Resolve expose une API Python officielle (`DaVinciResolveScript`). Permet : ouvrir projet, importer clips, créer timeline, blade, effets, color, deliver.

**Pour :**
- API officielle stable, documentée.
- Color grading de référence (Resolve est le standard cinéma).
- Fusion intégré pour les compositing complexes.
- Free tier puissant.

**Contre :**
- API Python à appeler depuis Claude Code = encore une indirection.
- Workflow GUI lourd, Resolve consomme énormément de RAM / GPU.
- Lente à boot, pas adaptée aux itérations rapides.

### Option D — Piloter Premiere Pro depuis Claude Code

Existe via **Adobe MCP** ("adb-mcp", 5 servers : Photoshop / Premiere / InDesign / After Effects / Illustrator). Premiere accessible via UXP scripts depuis Claude Code.

**Pour :**
- Workflow professionnel familier.
- ExtendScript / UXP riche, beaucoup de fonctions exposées.
- Intégration After Effects pour VFX.

**Contre :**
- Adobe = abonnement.
- Premiere notoirement instable sur projets longs.
- L'API UXP est moins mature que celle de Resolve / SpliceKit FCP.

### Option E — CapCut / iMovie / InVideo

CapCut : pas d'API publique sérieuse. Pilotage via UI automation (Playwright sur app web).
iMovie : AppleScript limité, pas pour le pro.
InVideo : SaaS web, automatisable via Playwright, mais limites de durée / résolution / watermark sur free tier.

**Verdict : utiles seulement si on a besoin de génération de templates volumineux ou social media output, pas pour un cinépoème.**

---

## Comparaison plateformes IA génération

| Plateforme | Image | i2v | Voice clone | Music | CLI/API | Notes |
|---|---|---|---|---|---|---|
| **fal.ai** | Flux, etc. | Seedance 2 | MiniMax | Stable Audio | API riche | Compte fragile (lock même avec balance positive) |
| **Replicate** | Flux | Seedance 1 Pro | MiniMax | Lyria, ACE | API stable | Plus cher mais reliable |
| **PiAPI** | — | Seedance 2 | — | — | API Cloudflare WAF, limite 2 jobs concurrents | User-Agent ban |
| **Krea** | Krea models | Seedance 2 (UI only) | — | — | MCP expose Seedance 1 seulement | Playwright pour Seedance 2 |
| **ChatGPT image (gpt-image-1)** | OK | — | — | — | API via OpenAI | Référence pour pool d'images |
| **Higgsfield** | — | i2v | — | — | CLI ? | Pas testé cette session, intérêt à vérifier |
| **ElevenLabs** | — | — | Voice clone + Music | Music v3 | API stable | TTS générique pas convaincant pour cinéma |
| **MiniMax** | — | — | speech-02-hd | Music v2.6 | Via fal ou Replicate | Best voice clone testé |
| **Suno** | — | — | — | Music | API | Pas exploré cette session |

**Recommandation pratique** : utiliser **fal storage** pour CDN public (free, fiable même compte locked), **PiAPI ou Replicate** pour la génération principale (deux providers en backup), **MiniMax via Replicate** pour le voice cloning, **Lyria via Replicate ou ElevenLabs Music** pour la musique. Ne JAMAIS dépendre d'un seul provider.

---

## Lessons learned

1. **Voice cloning > TTS** pour tout projet narratif sérieux. Le passage n'est pas optionnel.
2. **Storage CDN public séparé du compte de génération** = résilience.
3. **Audit visuel automatisé** des rushes avant montage = gain de temps massif.
4. **Sub-agents pour les tâches spécialisées** (analyse, EDL, audit) plutôt qu'un mega-prompt monolithique.
5. **Background tasks parallèles** pour tout ce qui peut tourner pendant que tu réfléchis.
6. **Ne pas boucler la vidéo pour matcher l'audio** — préférer slow modéré ou plus de matériel.
7. **ffmpeg pour itérer vite, NLE pour finaliser** si la complexité visuelle l'exige.
8. **Toujours valider visuellement chaque plan généré** avant intégration — l'IA hallucine régulièrement et les bugs visuels (yo-yo dans pod, croix dans le ciel, smartphones en 2095) sont récurrents.
9. **Préparer chaque email envoyé en montrant le draft complet à l'auteur** avant tout envoi — la pipeline en CLI peut envoyer instantanément, c'est précisément pour ça qu'on doit s'imposer un check humain.

---

## Outils utilisés (résumé)

**CLI / dev** : Claude Code (Anthropic), `gh`, `gws`, `mail-cli`, `gdrive`, `rclone`, `whisper-cli` (whisper.cpp), `ffmpeg`, `ffmpeg-full` (libass), `python3`, `curl`.

**Plateformes IA** : ChatGPT (image), fal.ai (storage + i2v + clone, lockable), Replicate (i2v + clone + music, reliable), PiAPI (i2v Seedance 2, Cloudflare-protégé), Krea (i2v via web), ElevenLabs (TTS + music), MiniMax (voice clone).

**Modèles** : Seedance 2.0 (i2v ByteDance), MiniMax speech-02-hd (voice clone), Lyria 2 / Stable Audio 2.5 (music), Whisper small (transcription).

**MCPs notables** : Adobe (Photoshop / Premiere / AE / Illustrator / InDesign), SpliceKit (FCP), Playwright, Pinecone, clipboard-vision, comfyui, Krea, Beeper, Postiz.

**Process** : sub-agents Claude Code (monteurs convoqués, analyse pool, audit), background tasks, Claude AI Project (mémoire externe pitch + EDLs + références).

---

## Coda

Ce repo est une note de méthode, pas un kit de production clé-en-main. Chaque film a sa propre pipeline. L'enseignement central de cette session : **piloter une chaîne de production complète depuis Claude Code est possible et fluide pour un cinéaste qui sait ce qu'il veut**, à condition d'accepter trois compromis :

- Itérations lentes vs NLE pour ajustements fins
- Aucune visualisation timeline pendant le montage ffmpeg
- Dépendance sur des plateformes externes fragiles (lock, rate limits, API change)

Le gain : reproductibilité, parallélisation, traçabilité, et surtout — **rester dans un seul environnement mental** pendant 12 heures de production, sans context-switch entre 6 logiciels.

---

*Notes prises le lendemain d'une session de ~12h ; à compléter sur d'autres projets.*
