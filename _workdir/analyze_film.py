#!/usr/bin/env python3
"""Analyse d'un film via Gemini File API multimodal.

Usage : python3 analyze_film.py <video_path> <film_name> <output_md> [model]
"""
import os
import sys
import time
from pathlib import Path
from google import genai
from google.genai import types

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-pro-preview")

PROMPT = """Tu es un analyste de montage cinéma expert. Voici le film "{title}" d'Ismaël Joffroy Chandoutis (cinéaste documentariste expérimental français, né 1988, Paris). Ton job : extraire sa GRAMMAIRE DE MONTAGE — pas le contenu narratif, mais sa SIGNATURE formelle, ce qui fait qu'un assistant IA pourrait monter "à sa façon".

Regarde le film en entier, observe précisément le découpage, les coupes, le son, les motifs.

Produis l'analyse structurée suivante en markdown :

# {title} ({year}) — Analyse de grammaire de montage

## 1. DURÉES DE PLAN
- Durée moyenne estimée d'un plan (en secondes)
- Plan le plus court / plus long observé
- Distribution (uniforme, polarisée, etc.)
- Tendance globale : compression (cuts rapides) ou tenue (plans longs)
- Évolution sur la durée du film (accélère, ralentit, alterne ?)

## 2. TYPES DE RACCORDS
- Hard cuts vs fondus (proportions)
- Fondus au noir / fondus enchaînés (présents ? absents ?)
- Match cuts (sur le mouvement, sur l'objet, sur la couleur)
- Jump cuts assumés ?
- Raccords sonores (le son précède ou prolonge l'image ?)
- Y a-t-il un usage de split edit / L-cut / J-cut systématique ?

## 3. RAPPORT VOIX / IMAGE
- Voix off (off, in, interview), nature du dispositif
- Offset précis voix-image : la voix arrive-t-elle AVANT ou APRÈS l'image qu'elle commente ? De combien (en secondes) ?
- Silences (présents, durée, fonction)
- Asynchronisme assumé ou synchronisme ?

## 4. RYTHMIQUE
- Pulse régulier ou irrégulier
- Accélérations (où, comment)
- Effets tunnel / boucles / répétitions
- Y a-t-il un mouvement "respiratoire" (inspire/expire) sur la longueur ?

## 5. MOTIFS VISUELS
- Plans qui reviennent (objets, lieux, surfaces)
- Cadres récurrents (focales, angles, profondeur)
- Palettes de couleurs dominantes
- Textures (numérique, archive, grain, low-res, surveillance, jeu vidéo, 3D, etc.)
- Sources d'images (archive, captation, image générée, screenshot, etc.)

## 6. SON DESIGN
- Couches sonores typiques (drone, foley, ambient, musique)
- Présence/absence de musique
- Texture du drone (basse, aigu, bruité, modulé)
- Silences (totalité du film "plein de son" ou "creusé") ?
- Rapport voix / ambiance / musique

## 7. CE QU'IL REFUSE
- Effets bannis (zoom, ralenti, accélération ?)
- Plans absents (visages frontaux ? talking heads ? grand plans larges ?)
- Esthétiques évitées (documentaire TV ? broadcast ? clip ?)
- Procédés qu'il pourrait utiliser mais qu'il s'interdit

## 8. CE QU'IL TIENT LONG
- Quel type de plan tient longtemps (paysage, détail, écran, abstraction) ?
- Sur quoi finit le film (image type, durée du dernier plan) ?
- Y a-t-il un plan "pivot" qui dure plus que les autres ?

## 9. SIGNATURE
- 3 à 5 caractéristiques qui font qu'on reconnaît immédiatement un film d'Ismaël Joffroy Chandoutis
- Formulées comme des règles formelles (pas des thèmes)
- Reproductibles par un autre éditeur si on les suivait à la lettre

## 10. NOTES SUPPLÉMENTAIRES
- Tout détail formel important non couvert ci-dessus
- Hypothèses sur les choix de montage si quelque chose surprend

Sois précis et concret. Donne des timecodes ou des descriptions de plans précises quand c'est utile. N'extrapole pas sur le sens — reste sur la FORME.
"""


def main():
    if len(sys.argv) < 4:
        print("usage: analyze_film.py <video_path> <film_title> <year> <output_md>")
        sys.exit(1)

    video_path = Path(sys.argv[1])
    title = sys.argv[2]
    year = sys.argv[3]
    output_md = Path(sys.argv[4])

    if not video_path.exists():
        print(f"ERROR: {video_path} not found", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    print(f"[{title}] Upload {video_path.name} ({video_path.stat().st_size/1024/1024:.1f}MB)...", flush=True)
    t0 = time.time()
    uploaded = client.files.upload(file=str(video_path))
    print(f"[{title}] Uploaded: {uploaded.name} ({time.time()-t0:.0f}s)", flush=True)

    # Poll for ACTIVE state
    while True:
        f = client.files.get(name=uploaded.name)
        state = getattr(f, "state", None)
        state_name = getattr(state, "name", str(state)) if state else "UNKNOWN"
        print(f"[{title}] state={state_name}", flush=True)
        if state_name == "ACTIVE":
            break
        if state_name == "FAILED":
            print(f"ERROR: upload failed", file=sys.stderr)
            sys.exit(1)
        time.sleep(8)

    prompt_text = PROMPT.format(title=title, year=year)

    print(f"[{title}] Sending prompt to {MODEL}...", flush=True)
    t0 = time.time()
    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(file_data=types.FileData(file_uri=uploaded.uri, mime_type=uploaded.mime_type)),
                    types.Part(text=prompt_text),
                ],
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=8192,
        ),
    )
    print(f"[{title}] Got response ({time.time()-t0:.0f}s)", flush=True)

    text = response.text or ""
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(text, encoding="utf-8")
    print(f"[{title}] Written: {output_md}  ({len(text)} chars)", flush=True)

    # Cleanup
    try:
        client.files.delete(name=uploaded.name)
        print(f"[{title}] Deleted uploaded file", flush=True)
    except Exception as e:
        print(f"[{title}] Cleanup warning: {e}", flush=True)


if __name__ == "__main__":
    main()
