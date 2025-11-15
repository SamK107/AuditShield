#!/usr/bin/env python
"""
Script pour générer la structure hiérarchique du projet en format Markdown.
"""
import os
from pathlib import Path

def should_ignore(path_str, path_obj):
    """Détermine si un chemin doit être ignoré."""
    # Ignorer l'environnement virtuel à la racine
    if path_obj.name == 'Active-le' and path_obj.parent.name == 'auditshield':
        return True
    
    ignore_patterns = [
        '__pycache__',
        '.pyc',
        '.pyo',
        '.pyd',
        '.git',
        'node_modules',
        '.venv',
        'venv',
        'site-packages',
        'staticfiles',  # Fichiers générés
        '.gz',  # Fichiers compressés
        '.bak.',
        '.bak_',
        'backup-',
        'db_stable.sqlite3',
    ]
    
    path_str_lower = path_str.lower()
    for pattern in ignore_patterns:
        if pattern in path_str_lower:
            return True
    
    # Ignorer les fichiers de sauvegarde
    if any(x in path_str for x in ['.bak', 'backup', '.tmp']):
        return True
    
    return False

def get_tree_structure(root_dir, prefix="", max_depth=None, current_depth=0):
    """Génère la structure hiérarchique récursive."""
    lines = []
    root_path = Path(root_dir)
    
    if not root_path.exists():
        return lines
    
    # Obtenir les éléments triés (dossiers d'abord, puis fichiers)
    try:
        items = sorted(root_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    except PermissionError:
        return lines
    
    for i, item in enumerate(items):
        if should_ignore(str(item), item):
            continue
        
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        lines.append(f"{prefix}{current_prefix}{item.name}")
        
        if item.is_dir() and (max_depth is None or current_depth < max_depth):
            extension = "    " if is_last else "│   "
            sub_lines = get_tree_structure(
                item, 
                prefix + extension, 
                max_depth, 
                current_depth + 1
            )
            lines.extend(sub_lines)
    
    return lines

def main():
    """Point d'entrée principal."""
    # Répertoire racine du projet
    project_root = Path(__file__).parent.parent
    auditshield_dir = project_root / "auditshield"
    
    if not auditshield_dir.exists():
        auditshield_dir = project_root
    
    output_file = auditshield_dir / "PROJECT_STRUCTURE.md"
    
    # Générer la structure
    print(f"Génération de la structure à partir de: {auditshield_dir}")
    
    from datetime import datetime
    structure_lines = [f"# Structure Hiérarchique du Projet AUDITSHIELD\n"]
    structure_lines.append(f"**Généré le:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    structure_lines.append("---\n\n")
    structure_lines.append("```\n")
    structure_lines.append(f"{auditshield_dir.name}/\n")
    
    tree_lines = get_tree_structure(auditshield_dir, max_depth=10)
    structure_lines.extend(tree_lines)
    
    structure_lines.append("\n```\n\n")
    
    # Ajouter des notes
    structure_lines.append("## Notes\n\n")
    structure_lines.append("- Les fichiers de sauvegarde (`.bak`, `backup-`) sont exclus\n")
    structure_lines.append("- Les dossiers `__pycache__`, `node_modules`, `staticfiles` sont exclus\n")
    structure_lines.append("- L'environnement virtuel (`Active-le`) est exclu\n")
    structure_lines.append("- Les fichiers compressés (`.gz`) sont exclus\n")
    structure_lines.append("- Profondeur maximale: 10 niveaux\n\n")
    structure_lines.append("## Applications Django\n\n")
    structure_lines.append("- **config**: Configuration principale du projet (settings, urls, wsgi)\n")
    structure_lines.append("- **core**: Pages principales (home, about, contact, CGV, politique)\n")
    structure_lines.append("- **store**: Gestion des produits, offres, paiements (CinetPay), commandes\n")
    structure_lines.append("- **downloads**: Gestion des téléchargements sécurisés et catégories\n")
    structure_lines.append("- **legal**: Pages légales (mentions légales, etc.)\n")
    
    # Écrire le fichier
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines([line + '\n' if not line.endswith('\n') else line for line in structure_lines])
    
    print(f"Structure générée dans: {output_file}")
    print(f"Nombre total de lignes: {len(structure_lines)}")

if __name__ == "__main__":
    main()

