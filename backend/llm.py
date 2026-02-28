import os
from groq import Groq
from dotenv import load_dotenv
from typing import List, Generator

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL  = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Tu es UniHelp, un assistant IA universitaire expert et bienveillant pour l'Institut International de Technologie (IIT) / NAU en Tunisie.

RÔLE : Aider les étudiants avec toutes les questions liées à la vie universitaire.
DOMAINES : inscriptions, certificats, bourses, stages, absences, examens, paiements, règlement intérieur, calendrier académique, PFE, orientation.

RÈGLES :
1. Langue : français par défaut, arabe si l'étudiant écrit en arabe, anglais si en anglais
2. Structure : réponses claires avec listes numérotées ou à puces quand pertinent
3. Précision : si du contexte documentaire est fourni, base-toi dessus EN PRIORITÉ
4. Honnêteté : si tu ne sais pas, dis-le et oriente vers le secrétariat
5. Ton : chaleureux, professionnel, encourageant
6. Format : utilise **gras** pour les informations importantes"""

def build_messages(question: str, context: str, history: List) -> List[dict]:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-8:]:
        msgs.append({"role": m.role, "content": m.content})
    if context:
        content = f"""Question : {question}

━━━ CONTEXTE OFFICIEL ━━━
{context}
━━━━━━━━━━━━━━━━━━━━━━━━

Réponds en te basant prioritairement sur ce contexte. Complète avec tes connaissances générales si nécessaire."""
    else:
        content = f"""Question : {question}

Réponds de façon précise et structurée. Ne mentionne PAS l'absence de documents ou de contexte. Réponds directement avec tes connaissances sur les universités tunisiennes."""
    msgs.append({"role": "user", "content": content})
    return msgs

def get_answer(question: str, context: str = "", history: List = []) -> str:
    r = client.chat.completions.create(
        model=MODEL, messages=build_messages(question, context, history),
        temperature=0.25, max_tokens=1200, top_p=0.9,
    )
    return r.choices[0].message.content

def stream_answer(question: str, context: str = "", history: List = []) -> Generator[str, None, None]:
    stream = client.chat.completions.create(
        model=MODEL, messages=build_messages(question, context, history),
        temperature=0.25, max_tokens=1200, top_p=0.9, stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content

def generate_email(email_type: str, student_name: str = "", reason: str = "") -> str:
    templates = {
        "Demande d'attestation de scolarité": "attestation prouvant l'inscription en cours",
        "Demande de stage PFE": "convention de stage de fin d'études (PFE)",
        "Réclamation de note": "révision ou vérification d'une note d'examen",
        "Justification d'absence": "justification d'une absence aux cours ou examens",
        "Demande de transfert": "transfert vers un autre établissement ou filière",
        "Demande de bourse": "attribution ou renouvellement d'une bourse d'études",
    }
    prompt = f"""Rédige un email administratif formel en français pour une université tunisienne.

OBJET : {email_type}
CONTEXTE : L'étudiant demande {templates.get(email_type, email_type.lower())}.
NOM : {student_name or "[Prénom NOM]"}
DÉTAILS : {reason or "[À compléter]"}

Structure : Objet / Formule d'appel / Introduction / Corps / Clôture / Formule de politesse / Signature complète.
Laisse [entre crochets] les champs à personnaliser. Email complet et prêt à l'emploi."""

    r = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}],
        temperature=0.3, max_tokens=900,
    )
    return r.choices[0].message.content