#!/usr/bin/env python3
"""
Prépare la galerie : relit les dossiers de visuels/, écrit manifeste.json (ce que la page
affiche) et refait ForgeMe-visuels.zip (tout télécharger d'un coup).

Usage : python3 generer.py
Ajouter un visuel = le déposer dans le bon dossier de visuels/, puis relancer.
L'ordre d'affichage suit le nom des fichiers (01-accueil.png, 02-taches.png…).
"""
import json
import os
import subprocess
import zipfile

RACINE = os.path.dirname(os.path.abspath(__file__))
VISUELS = os.path.join(RACINE, "visuels")
IMAGES = (".png", ".jpg", ".jpeg", ".webp")
VIDEOS = (".mp4", ".mov")
SECTIONS = ["captures", "affiches-16-9", "affiches-9-16", "mascotte", "icone"]


def dimensions(chemin):
    """Largeur et hauteur d'une image, par sips (macOS), sans dépendance."""
    try:
        sortie = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", chemin],
            capture_output=True, text=True, check=True,
        ).stdout
        valeurs = {}
        for ligne in sortie.splitlines():
            ligne = ligne.strip()
            if ligne.startswith("pixelWidth:"):
                valeurs["l"] = int(ligne.split(":")[1])
            elif ligne.startswith("pixelHeight:"):
                valeurs["h"] = int(ligne.split(":")[1])
        return valeurs.get("l"), valeurs.get("h")
    except Exception:
        return None, None


# Noms affichés quand le nom de fichier ne peut pas porter d'accent.
NOMS = {"aurevoir": "Au revoir", "debranche": "Débranché", "reveil": "Réveil", "coeur": "Cœur",
        "encourage": "Encourage", "fete": "Fête", "etonne": "Étonné", "inquiet": "Inquiet",
        "forgeme icone 1024": "Icône 1024 px"}


def libelle(nom):
    """« 02-mon-humeur.png » devient « Mon humeur »."""
    base = os.path.splitext(nom)[0]
    if base.replace("-", " ") in NOMS:
        return NOMS[base.replace("-", " ")]
    morceaux = base.split("-")
    if morceaux and morceaux[0].isdigit():
        morceaux = morceaux[1:]
    texte = " ".join(morceaux).replace("_", " ").strip()
    return texte[:1].upper() + texte[1:] if texte else base


def main():
    manifeste = {}
    for section in SECTIONS:
        dossier = os.path.join(VISUELS, section)
        os.makedirs(dossier, exist_ok=True)
        elements = []
        for nom in sorted(os.listdir(dossier)):
            if nom.startswith("."):
                continue
            chemin = os.path.join(dossier, nom)
            ext = os.path.splitext(nom)[1].lower()
            if ext in IMAGES:
                l, h = dimensions(chemin)
                elements.append({"fichier": f"visuels/{section}/{nom}", "nom": libelle(nom), "type": "image",
                                 "l": l, "h": h, "octets": os.path.getsize(chemin)})
            elif ext in VIDEOS:
                elements.append({"fichier": f"visuels/{section}/{nom}", "nom": libelle(nom), "type": "video",
                                 "octets": os.path.getsize(chemin)})
        manifeste[section] = elements

    zip_chemin = os.path.join(RACINE, "ForgeMe-visuels.zip")
    with zipfile.ZipFile(zip_chemin, "w", zipfile.ZIP_DEFLATED) as z:
        for section in SECTIONS:
            for el in manifeste[section]:
                z.write(os.path.join(RACINE, el["fichier"]), os.path.join("ForgeMe-visuels", section, os.path.basename(el["fichier"])))
    manifeste["zip"] = {"fichier": "ForgeMe-visuels.zip", "octets": os.path.getsize(zip_chemin)}

    with open(os.path.join(RACINE, "manifeste.json"), "w", encoding="utf-8") as f:
        json.dump(manifeste, f, ensure_ascii=False, indent=1)

    for section in SECTIONS:
        print(f"{section:15} {len(manifeste[section])} fichier(s)")
    print(f"zip            {manifeste['zip']['octets'] / 1e6:.1f} Mo")


if __name__ == "__main__":
    main()
