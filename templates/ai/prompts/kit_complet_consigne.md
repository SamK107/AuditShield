# 🧩 KIT COMPLET DE PRÉPARATION À L'AUDIT — BLOOM SHIELD GOUVERNANCE  
*(Version automatisable – jusqu'à 10 fichiers réglementaires)*

---

## 🎯 OBJECTIF GÉNÉRAL

À partir des textes réglementaires transmis par l'agent public (max : 10 fichiers de 10 Mo chacun), produire un **document structuré et professionnel** intitulé :

> **« Kit complet de préparation à l'audit »**

Ce document doit :
- résumer chaque texte réglementaire transmis ;
- proposer des **questionnaires de préparation** (20 questions max / document + 20 générales) ;
- dresser des **tableaux d'irrégularités** (20 irrégularités max / document + 10 générales) ;
- formuler des **recommandations pratiques et un plan d'action** pour renforcer la conformité.

---

## 🪶 PAGE DE COUVERTURE

**Titre :** Kit complet de préparation à l'audit  
**Sous-titre :** Bloom Shield Gouvernance  
**Mention de propriété :**  
> Préparé à partir des textes réglementaires transmis par : {{ inquiry.contact_name|default_if_none:"" }} / {{ inquiry.organization_name|default_if_none:"" }} / {{ inquiry.email|default_if_none:"" }}

*(Aucune pagination sur la couverture.)*

---

## 🧭 SOMMAIRE

- Introduction générale  
- Informations générales – Questionnaire  
- Informations générales – Irrégularités  
- [Document 1 : Titre du texte]  
- [Document 2 : Titre du texte]  
- …  
- [Document 10 : Titre du texte]  
- Synthèse et recommandations  
- Mentions de propriété  

*(Pagination à partir de l'introduction.)*

---

## 1️⃣ INTRODUCTION GÉNÉRALE

### Objectif  
Présenter la finalité du kit, le nombre de documents traités et le profil de l'agent.

### À générer automatiquement :
- **Résumé synthétique des textes reçus** (titre, objet, domaine)  
- **Principes communs** (transparence, responsabilité, traçabilité)  
- **Risques globaux** (disciplinaires, financiers, réputationnels)  
- **Bonnes pratiques** applicables à tous les services publics  

**Contexte de la demande :**
- Organisation : {{ inquiry.organization_name|default_if_none:"Non renseigné" }}
- Statut juridique : {{ inquiry.statut_juridique|default_if_none:"Non renseigné" }}
- Localisation : {{ inquiry.location|default_if_none:"Non renseigné" }}
- Secteur : {{ inquiry.sector|default_if_none:"Non renseigné" }}
- Budget : {{ inquiry.budget_range|default_if_none:"Non renseigné" }}
- Missions : {{ inquiry.mission_text|default_if_none:"Non renseigné" }}
- Contexte / Présentation : {{ inquiry.context_text|default_if_none:"Non renseigné" }}
- Sources de financement : {{ inquiry.funding_sources|join:", "|default_if_none:"Non renseigné" }}
- Types d'audit/contrôle : {{ inquiry.audits_types|join:", "|default_if_none:"Non renseigné" }}
- Fréquence des audits : {{ inquiry.audits_frequency|default_if_none:"Non renseigné" }}
- Taille de l'organisation : {{ inquiry.staff_size|default_if_none:"Non renseigné" }}
- Organigramme : {{ inquiry.org_chart_text|default_if_none:"Non renseigné" }}
- Notes diverses : {{ inquiry.notes_text|default_if_none:"Non renseigné" }}

---

## 2️⃣ QUESTIONNAIRES DE PRÉPARATION

### 🔹 Bloc A — Informations générales (20 questions max)
Questions globales sur :
- Organisation interne du service  
- Gestion documentaire et traçabilité  
- Communication et reporting  
- Application des procédures budgétaires  
- Coordination avec les organes de contrôle  

*(Format attendu : question + réponse idéale + réponse partielle + réponse à éviter + conseil pratique)*

---

### 🔹 Bloc B — Par document réglementaire (jusqu'à 10 fichiers, 20 questions chacun)

#### Exemple de structure automatique :

#### 📘 Document 1 : [Titre du texte]
1. Question 1  
   - ✅ Réponse attendue :  
   - ⚠️ Réponse partielle :  
   - ❌ Réponse à éviter :  
   - 💡 Conseil :  
2. Question 2  
   …  
(20 questions max)

---

## 3️⃣ TABLEAUX DES IRRÉGULARITÉS

### 🔹 Bloc A — Irrégularités générales (10 max)

| Irrégularité | Référence | Acteurs concernés | Solution corrective | Gravité | Conséquences |
|---------------|------------|--------------------|----------------------|----------|---------------|
| Exemple : Absence de visa du contrôle financier | Article 12 du Décret X | Ordonnateur | Mettre en place un circuit de validation préalable | Élevée | Suspension de crédits |

---

### 🔹 Bloc B — Irrégularités par document (20 max par texte)

#### 📘 Document 1 : [Titre du texte]

| Irrégularité | Référence | Acteurs concernés | Solution corrective | Gravité | Conséquences |
|---------------|------------|--------------------|----------------------|----------|---------------|
| … | … | … | … | … | … |

---

## 4️⃣ SYNTHÈSE FINALE ET RECOMMANDATIONS

À générer automatiquement :
- **Tableau récapitulatif** des points critiques (document, thème, niveau de risque, action proposée)  
- **Plan d'action simplifié** :  
  - Priorité : Élevée / Moyenne / Faible  
  - Responsable : [Nom du service]  
  - Délai : [Court / Moyen / Long terme]  
- **Recommandations générales** pour améliorer la conformité et renforcer le contrôle interne.

---

## 5️⃣ PRÉSENTATION FINALE

- **Format :** PDF A4 ou 6×9  
- **Pied de page :** "Kit complet de préparation à l'audit — Bloom Shield Gouvernance"  
- **Pagination automatique et sommaire cliquable**  
- **Mention légale :**
  > © Bloom Shield Gouvernance — AuditSansPeur.com  
  > Document personnalisé pour usage interne exclusivement.  
  > Toute reproduction sans autorisation écrite est interdite.

---

## 🧠 INSTRUCTIONS POUR L'IA

1. Lire les textes transmis par l'agent (max 10).  
2. Identifier les thématiques, obligations, et articles clés.  
3. Générer pour chaque texte :  
   - Résumé analytique (10 lignes max)  
   - 20 questions max avec réponses ;  
   - 20 irrégularités max avec solutions.  
4. Générer ensuite les **sections générales** (questions + irrégularités).  
5. Conclure par une **synthèse et un plan d'action global**.  
6. Fournir le résultat en **Markdown ou Word/PDF** selon la plateforme.

---

## ✅ RAPPEL DES LIMITES

| Élément | Limite |
|----------|---------|
| Nombre de fichiers | 10 (max 10 Mo/fichier) |
| Questions par document | 20 max |
| Questions générales | 20 max |
| Irrégularités par document | 20 max |
| Irrégularités générales | 10 max |

---

📘 *Ce modèle peut être utilisé avec ChatGPT / GPT-4/5, Mistral, Claude, Llama 3 ou tout moteur local (LM Studio, Ollama, etc.) en lui fournissant les textes réglementaires et ce fichier comme prompt de base pour la génération automatique du kit.*

