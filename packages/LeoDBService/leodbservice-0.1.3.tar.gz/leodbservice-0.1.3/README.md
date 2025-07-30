# Leo Database Setup Service

Service de configuration des schémas de base de données PostgreSQL pour l'Assistant Exécutif Leo.

## Description

Ce service Python a pour mission de créer le schéma ainsi que l'ensemble des tables nécessaires pour qu'un nouvel utilisateur puisse utiliser son Assistant Exécutif Leo. Il s'agit d'un service web exposant une API protégée, qui sera uniquement accédée par le service de configuration de Leo.

## Fonctionnalités principales

- Création dynamique de schémas PostgreSQL pour chaque utilisateur
- Vérification de l'existence d'un schéma
- Création des tables manquantes dans le schéma
- API RESTful sécurisée

## Architecture

Le projet suit une architecture en couches :
- `/api` : Couche API (FastAPI)
- `/core` : Couche cœur de l'application
- `/db` : Couche d'accès à la base de données
- `/utils` : Utilitaires et fonctions d'aide
- `/tests` : Tests automatisés

## Prérequis

- Python 3.10+
- PostgreSQL 14+
- Docker (optionnel)

## Installation

1. Cloner le dépôt
```bash
git clone [url-du-repo]
cd LeoDBSetup
```

2. Créer et activer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows, utilisez: venv\Scripts\activate
```

3. Installer les dépendances
```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement
```bash
cp .env.example .env
# Modifier le fichier .env avec vos valeurs
```

## Utilisation

Pour exécuter le service en mode développement :
```bash
uvicorn main:app --reload
```

## Documentation

La documentation de l'API sera disponible à l'adresse `http://localhost:8000/docs` une fois le service lancé.

## Tests

Pour exécuter les tests :
```bash
pytest
```

## Contributeurs

- [Votre nom]

## Licence

Propriétaire - Tous droits réservés
