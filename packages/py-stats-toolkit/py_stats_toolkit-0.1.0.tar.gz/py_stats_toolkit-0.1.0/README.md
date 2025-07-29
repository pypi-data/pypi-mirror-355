# 🎯 Optimiseur Génétique Euromillions

Ce projet vise à générer des grilles optimisées pour l'Euromillions en combinant :
- Statistiques avancées (fréquences, entropie, fractales, etc.)
- Modules catégorisés (fondamentaux, cycliques, génétiques, probabilistes, topologiques)
- Algorithme génétique auto-adaptatif
- Moteur de prédiction entièrement automatisé

## 📦 Installation

```bash
python install.py
```

Cela :
- Crée les dossiers nécessaires
- Organise les fichiers selon l'architecture du projet

## 🚀 Lancement du moteur

### Option 1 — Grille + Fichier

```bash
./launch_prediction.sh
```

> Sauvegarde dans `strategie_euromillions_force.json`

### Option 2 — Grille + Affichage immédiat

```bash
./launch_and_print.sh
```

> Affiche la grille dans le terminal

## 📁 Structure du projet

```
📦 /core
  ├─ prediction_engine.py
  ├─ trainer.py
  ├─ rules.py
  ├─ ...
📦 /modules
  ├─ fondamentaux/
  ├─ cycliques/
  ├─ génétiques/
  ├─ probabilistes/
  ├─ topologiques/
📦 /data
  ├─ euromillions2.csv
📄 install.py
📄 launch_prediction.sh
📄 launch_and_print.sh
📄 README.md
```

## 🔒 .gitignore

Seuls les fichiers suivants sont **conservés** dans le dépôt :
- `README.md`
- `install.py`
- `launch_*.sh`
- Fichiers sources dans `/core/` et `/modules/`

## 📚 Dépendances

Ce projet utilise la bibliothèque `py-stats-toolkit` pour les analyses statistiques et l'optimisation génétique. Pour l'installer :

```bash
pip install py-stats-toolkit
```

## 📝 Licence

MIT License

# 📊 Py-Stats-Toolkit

Une bibliothèque Python complète pour l'analyse statistique avancée et le traitement des données.

## 🚀 Utilisation

```python
from py_stats_toolkit import StatisticalAnalyzer

# Créer un analyseur statistique
analyzer = StatisticalAnalyzer()

# Analyser vos données
results = analyzer.analyze(data)
```

## 📁 Structure du projet

```
📦 /py_stats_toolkit
  ├─ __init__.py
  ├─ core/
  ├─ modules/
  ├─ utils/
📦 /tests
📦 /docs
📦 /examples
```

## 📚 Dépendances

- pandas >= 1.3.0
- numpy >= 1.20.0
- matplotlib >= 3.4.0
- scipy >= 1.7.0
- scikit-learn >= 0.24.0

## 🛠️ Développement

Pour installer les dépendances de développement :

```bash
pip install -e ".[dev]"
```

## 📝 Licence

MIT License

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📞 Support

Pour toute question ou problème, veuillez ouvrir une issue sur GitHub.
