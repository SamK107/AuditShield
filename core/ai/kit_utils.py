"""
Utilitaires pour l'extraction de texte depuis les documents
et la conversion Markdown vers DOCX.
"""
import logging
from pathlib import Path
from typing import Optional

from django.conf import settings
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)

# Limite de caractères par document pour éviter d'envoyer trop de données
MAX_CHARS_PER_DOCUMENT = 20000


def extract_texts_from_inquiry_docs(inquiry) -> str:
    """
    Lit tous les InquiryDocument liés à la ClientInquiry
    et retourne une grande chaîne de texte structurée en Markdown.

    Args:
        inquiry: Instance de store.models.ClientInquiry

    Returns:
        Chaîne Markdown contenant les extraits de tous les documents
    """
    from store.models import InquiryDocument

    documents = InquiryDocument.objects.filter(inquiry=inquiry).order_by("uploaded_at")
    
    if not documents.exists():
        return "Aucun document fourni."
    
    sections = []
    
    for idx, doc in enumerate(documents, 1):
        doc_name = doc.original_name or doc.file.name.split("/")[-1]
        sections.append(f"## Document {idx} — {doc_name}\n")
        
        try:
            # Obtenir le chemin du fichier
            if hasattr(doc.file, "path"):
                file_path = doc.file.path
            else:
                # Si le fichier est en storage distant, on doit le télécharger
                file_path = None
                logger.warning(f"Document {doc.id} n'a pas de chemin local, tentative de téléchargement")
                # Pour l'instant, on skip ces fichiers
                sections.append("(Document non accessible localement — à analyser manuellement)\n")
                continue
            
            # Extraire le texte selon l'extension
            ext = Path(file_path).suffix.lower()
            text_content = ""
            
            if ext == ".pdf":
                text_content = _extract_pdf_text(file_path)
            elif ext in (".docx", ".doc"):
                text_content = _extract_docx_text(file_path)
            elif ext in (".txt", ".md"):
                text_content = _extract_text_file(file_path)
            elif ext in (".xls", ".xlsx"):
                text_content = "(Document Excel joint, non extrait automatiquement — à analyser manuellement)"
            else:
                text_content = f"(Document au format {ext} joint, non extrait automatiquement — à analyser manuellement)"
            
            # Tronquer si trop long
            if len(text_content) > MAX_CHARS_PER_DOCUMENT:
                text_content = text_content[:MAX_CHARS_PER_DOCUMENT] + "\n\n[... contenu tronqué ...]"
            
            sections.append(text_content)
            sections.append("\n")  # Ligne vide entre documents
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction du document {doc.id}: {e}")
            sections.append(f"(Erreur lors de l'extraction du texte: {e})\n")
            sections.append("\n")
    
    return "\n".join(sections)


def _extract_pdf_text(file_path: str) -> str:
    """
    Extrait le texte d'un fichier PDF.
    """
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            texts = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    texts.append(page_text)
            return "\n\n".join(texts)
    except ImportError:
        try:
            import PyPDF2
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                texts = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        texts.append(page_text)
                return "\n\n".join(texts)
        except ImportError:
            logger.warning("Ni pdfplumber ni PyPDF2 ne sont installés, extraction PDF impossible")
            return "(Extraction PDF impossible — bibliothèque manquante)"
    except Exception as e:
        logger.warning(f"Erreur lors de l'extraction PDF {file_path}: {e}")
        return f"(Erreur lors de l'extraction PDF: {e})"


def _extract_docx_text(file_path: str) -> str:
    """
    Extrait le texte d'un fichier DOCX.
    """
    try:
        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        logger.warning(f"Erreur lors de l'extraction DOCX {file_path}: {e}")
        return f"(Erreur lors de l'extraction DOCX: {e})"


def _extract_text_file(file_path: str) -> str:
    """
    Extrait le texte d'un fichier texte (.txt, .md).
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logger.warning(f"Erreur lors de la lecture du fichier texte {file_path}: {e}")
        return f"(Erreur lors de la lecture: {e})"


def markdown_to_docx(markdown_text: str, inquiry_id: int) -> str:
    """
    Prend le Markdown généré par l'IA et le convertit en un fichier .docx.

    Args:
        markdown_text: Contenu Markdown à convertir
        inquiry_id: ID de l'inquiry (pour le nom de fichier)

    Returns:
        Chemin absolu du fichier .docx généré
    """
    # Créer le répertoire de sortie
    output_dir = Path(settings.BASE_DIR) / "tmp" / "kit_drafts"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Nom du fichier
    filename = f"kit_inquiry_{inquiry_id}.docx"
    output_path = output_dir / filename
    
    # Créer le document Word
    doc = Document()
    
    # Ajouter un titre principal
    title = doc.add_heading("Kit complet de préparation à l'audit", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()  # Espacement
    
    # Parser le Markdown ligne par ligne
    lines = markdown_text.split("\n")
    current_para = None
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        
        # Ligne vide
        if not stripped:
            if current_para:
                current_para = None
            in_list = False
            continue
        
        # Titres
        if stripped.startswith("# "):
            doc.add_heading(stripped[2:], level=1)
            current_para = None
            in_list = False
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:], level=2)
            current_para = None
            in_list = False
        elif stripped.startswith("### "):
            doc.add_heading(stripped[4:], level=3)
            current_para = None
            in_list = False
        elif stripped.startswith("#### "):
            doc.add_heading(stripped[5:], level=4)
            current_para = None
            in_list = False
        
        # Listes à puces
        elif stripped.startswith("- ") or stripped.startswith("* "):
            para = doc.add_paragraph(stripped[2:], style="List Bullet")
            para.style.font.size = Pt(11)
            current_para = None
            in_list = True
        
        # Listes numérotées
        elif stripped[0].isdigit() and ". " in stripped[:5]:
            # Extraire le texte après le numéro
            text = stripped.split(". ", 1)[1] if ". " in stripped else stripped
            para = doc.add_paragraph(text, style="List Number")
            para.style.font.size = Pt(11)
            current_para = None
            in_list = True
        
        # Tableaux (détection basique - lignes commençant par |)
        elif stripped.startswith("|"):
            # Pour l'instant, on convertit en paragraphe simple
            # Une amélioration future pourrait parser les tableaux Markdown
            text = stripped.replace("|", " ").strip()
            para = doc.add_paragraph(text)
            para.style.font.size = Pt(11)
            current_para = None
            in_list = False
        
        # Paragraphe normal
        else:
            if in_list:
                # Fin de liste, nouveau paragraphe
                current_para = doc.add_paragraph(stripped)
                current_para.style.font.size = Pt(11)
                in_list = False
            elif current_para:
                # Continuer le paragraphe précédent
                current_para.add_run(" " + stripped)
            else:
                # Nouveau paragraphe
                current_para = doc.add_paragraph(stripped)
                current_para.style.font.size = Pt(11)
    
    # Sauvegarder le document
    doc.save(str(output_path))
    logger.info(f"Document DOCX généré: {output_path}")
    
    return str(output_path.absolute())

