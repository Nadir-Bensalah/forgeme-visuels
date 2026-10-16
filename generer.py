#!/usr/bin/env python3
"""
Prépare la galerie : relit les dossiers de visuels/, fabrique des aperçus légers pour la page
(apercus/), écrit manifeste.json (ce que la page affiche) et refait ForgeMe-visuels.zip.

Usage : python3 generer.py
Ajouter un visuel = le déposer dans le bon dossier de visuels/, puis relancer.
L'ordre d'affichage suit le nom des fichiers (01-accueil.png, 02-taches.png…).
Les fichiers d'origine, en pleine définition, restent ceux qu'on télécharge.
"""
import json
import os
import subprocess
import zipfile

RACINE = os.path.dirname(os.path.abspath(__file__))
VISUELS = os.path.join(RACINE, "visuels")
APERCUS = os.path.join(RACINE, "apercus")
IMAGES = (".png", ".jpg", ".jpeg", ".webp")
VIDEOS = (".mp4", ".mov")

# Dossier : (taille maximale de l'aperçu en pixels, fond transparent à garder)
SECTIONS = {
    "captures": (900, False),
    "affiches-4-5": (1100, False),
    "affiches-9-16": (900, False),
    "affiches-16-9": (1600, False),
    "mascotte": (520, True),
    "badges": (520, True),
    "exploits": (420, True),
    "icones-app": (420, False),
    "planches": (2000, False),
}

# Noms affichés quand le nom de fichier ne peut pas porter d'accent.
NOMS = {
    "aurevoir": "Au revoir", "debranche": "Débranché", "reveil": "Réveil", "coeur": "Cœur",
    "taches moins de chaos": "Tâches, moins de chaos", "rituels du temps pour vous": "Rituels, du temps pour vous",
    "objectifs petits pas": "Objectifs, petits pas", "recompenses chaque progres": "Récompenses, chaque progrès",
    "decouvrir telechargez forgeme": "Découvrir, téléchargez ForgeMe", "le canape magnetique": "Le canapé magnétique",
    "la pluie de taches": "La pluie de tâches", "demarrer": "Démarrer", "regulier": "Régulier",
    "liberer": "Libérer", "creneau": "Créneau",
    "maitre": "Maître", "legende": "Légende",
    "etincelle": "Étincelle", "journee parfaite": "Journée parfaite", "leve tot": "Lève-tôt",
    "batisseur": "Bâtisseur", "rituel 30": "Rituel 30 jours", "premiere idee": "Première idée",
    "memoire": "Mémoire",
    "noel": "Noël", "ete": "Été", "ramadan aid": "Ramadan / Aïd", "saint valentin": "Saint-Valentin",
    "icones app": "Icônes de l'app", "badges progression": "Badges de progression",
    "banniere google play": "Bannière Google Play", "apercus app": "Aperçus de l'app",
    "ecran de demarrage 4k": "Écran de démarrage 4K",
}


def dimensions(chemin):
    """Largeur et hauteur d'une image, par sips (macOS), sans dépendance."""
    try:
        sortie = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", chemin],
                                capture_output=True, text=True, check=True).stdout
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


def libelle(nom):
    """« 02-mon-humeur.png » devient « Mon humeur »."""
    base = os.path.splitext(nom)[0]
    morceaux = base.split("-")
    if morceaux and morceaux[0].isdigit():
        morceaux = morceaux[1:]
    cle = " ".join(morceaux).replace("_", " ").strip().lower()
    if cle in NOMS:
        return NOMS[cle]
    return cle[:1].upper() + cle[1:] if cle else base


def apercu(section, nom, chemin, taille, transparent):
    """Aperçu léger (JPEG, ou PNG si le fond est transparent), refait seulement si besoin."""
    dossier = os.path.join(APERCUS, section)
    os.makedirs(dossier, exist_ok=True)
    base = os.path.splitext(nom)[0]
    sortie = os.path.join(dossier, base + (".png" if transparent else ".jpg"))
    if not os.path.exists(sortie) or os.path.getmtime(sortie) < os.path.getmtime(chemin):
        commande = ["sips", "-Z", str(taille)]
        if not transparent:
            commande += ["-s", "format", "jpeg", "-s", "formatOptions", "82"]
        subprocess.run(commande + [chemin, "--out", sortie], capture_output=True, check=True)
    return os.path.relpath(sortie, RACINE)


def main():
    manifeste = {}
    attendus = set()
    for section, (taille, transparent) in SECTIONS.items():
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
                ap = apercu(section, nom, chemin, taille, transparent)
                attendus.add(os.path.join(RACINE, ap))
                elements.append({"fichier": f"visuels/{section}/{nom}", "apercu": ap, "nom": libelle(nom),
                                 "type": "image", "l": l, "h": h, "octets": os.path.getsize(chemin)})
            elif ext in VIDEOS:
                elements.append({"fichier": f"visuels/{section}/{nom}", "nom": libelle(nom), "type": "video",
                                 "octets": os.path.getsize(chemin)})
        manifeste[section] = elements

    # Aperçus dont l'original a disparu.
    for racine, _, fichiers in os.walk(APERCUS):
        for f in fichiers:
            p = os.path.join(racine, f)
            if p not in attendus:
                os.remove(p)

    zip_chemin = os.path.join(RACINE, "ForgeMe-visuels.zip")
    with zipfile.ZipFile(zip_chemin, "w", zipfile.ZIP_STORED) as z:
        for section in SECTIONS:
            for el in manifeste[section]:
                z.write(os.path.join(RACINE, el["fichier"]),
                        os.path.join("ForgeMe-visuels", section, os.path.basename(el["fichier"])))
    manifeste["zip"] = {"fichier": "ForgeMe-visuels.zip", "octets": os.path.getsize(zip_chemin)}

    with open(os.path.join(RACINE, "manifeste.json"), "w", encoding="utf-8") as f:
        json.dump(manifeste, f, ensure_ascii=False, indent=1)

    for section in SECTIONS:
        print(f"{section:15} {len(manifeste[section])} fichier(s)")
    print(f"zip            {manifeste['zip']['octets'] / 1e6:.1f} Mo")


if __name__ == "__main__":
    main()
