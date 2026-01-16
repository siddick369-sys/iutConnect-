from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Q
import random
from .models import EtudiantNiveau1, EtudiantNiveau2, Parrainage, Signalement


import logging
from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from .models import EtudiantNiveau1, EtudiantNiveau2
import threading
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from .models import Signalement

# --- CLASSE POUR L'ENVOI ASYNCHRONE (THREADING) ---
class EmailThreadia(threading.Thread):
    def __init__(self, email_message):
        self.email_message = email_message
        threading.Thread.__init__(self)

    def run(self):
        # Cette méthode s'exécute en arrière-plan
        try:
            self.email_message.send()
            print("✅ Email d'alerte envoyé avec succès (Thread).")
        except Exception as e:
            print(f"❌ Erreur envoi mail (Thread) : {e}")
import unicodedata

def normaliser_texte(texte):
    """
    Normalise un texte pour l'authentification :
    - Minuscules
    - Retire les accents (é -> e, ï -> i)
    - Décompose les ligatures (œ -> oe, æ -> ae)
    Exemple: "HélÈne Cœur" -> "helene coeur"
    """
    if not texte:
        return ""
    
    # 1. Utilisation de NFKD (Compatibility Decomposition)
    # C'est la clé : cela transforme 'œ' en 'oe', 'æ' en 'ae', etc.
    texte_nfkd = unicodedata.normalize('NFKD', str(texte))
    
    # 2. On garde seulement les caractères qui ne sont pas des marques d'accent (Mn)
    texte_sans_accent = "".join([c for c in texte_nfkd if unicodedata.category(c) != 'Mn'])
    
    # 3. Minuscule et nettoyage
    return texte_sans_accent.lower().strip()

# Configuration du logger (pour garder une trace des erreurs en prod)
logger = logging.getLogger(__name__)
def connexion_etudiant(request):
    # CAS 1 : L'utilisateur envoie le formulaire (POST)
    if request.method == "POST":
        
        # 1. PROTECTION ANTI-BRUTE FORCE
        ip_client = request.META.get('REMOTE_ADDR')
        cache_key = f"login_attempts_{ip_client}"
        attempts = cache.get(cache_key, 0)

        if attempts >= 5:
            messages.error(request, "Trop de tentatives échouées. Réessayez dans 5 minutes.")
            logger.warning(f"Blocage Brute Force IP: {ip_client}")
            return render(request, "connexion.html")

        # 2. NETTOYAGE
        matricule_input = request.POST.get("matricule", "").strip().upper()
        nom_prenom_input = request.POST.get("nom_prenom", "").strip()
        mention_input = request.POST.get("mention", "").strip()
        telephone_input = request.POST.get("telephone", "").strip()

        # Vérification des champs
        if not all([matricule_input, nom_prenom_input, mention_input, telephone_input]):
            messages.error(request, "Tous les champs sont obligatoires.")
            # On retourne le render pour garder les champs pré-remplis si besoin, 
            # ou redirect pour nettoyer. Render est souvent mieux ici pour l'UX.
            return render(request, "connexion.html")
        try:
            # 3. RECHERCHE (On nettoie le téléphone pour la recherche)
            # On enlève les espaces du téléphone envoyé par le user pour être sûr
            telephone_clean = telephone_input.replace(" ", "")

            # On cherche d'abord par matricule uniquement (c'est l'identifiant le plus fiable)
            # On ne filtre PAS tout de suite par téléphone pour voir si le matricule existe au moins
            etudiant = EtudiantNiveau1.objects.filter(matricule__iexact=matricule_input).first()

            if not etudiant:
                etudiant = EtudiantNiveau2.objects.filter(matricule__iexact=matricule_input).first()
            
            # DEBUG : Voir ce qu'on a trouvé
            if not etudiant:
                print(f"❌ AUCUN étudiant trouvé avec le matricule {matricule_input}")
            else:
                print(f"✅ Étudiant trouvé en DB : {etudiant.nom_prenom} | Tel DB: {etudiant.telephone}")

            if etudiant:
                # --- VÉRIFICATION MANUELLE SOUPLE ---
                
                # A. Vérification Téléphone (On nettoie tout avant de comparer)
                # On enlève les espaces dans le tel de la DB et celui du user
                db_tel = str(etudiant.telephone).replace(" ", "").strip()
                user_tel = telephone_clean
                
                if db_tel != user_tel:
                    print(f"❌ Erreur Téléphone: DB({db_tel}) != User({user_tel})")
                    etudiant = None # Rejet
                
                # B. Vérification Nom (On vérifie si les mots clés sont présents)
                # Au lieu de l'égalité stricte, on vérifie l'inclusion
                else:
                    db_nom = normaliser_texte(etudiant.nom_prenom)
                    user_nom = normaliser_texte(nom_prenom_input)
                    
                    # On sépare les mots (ex: ["abdoul", "nassir"])
                    db_parts = set(db_nom.split())
                    user_parts = set(user_nom.split())
                    
                    # On vérifie si l'utilisateur a entré au moins une partie significative du nom
                    # intersection() trouve les mots communs
                    common_parts = db_parts.intersection(user_parts)
                    
                    if len(common_parts) == 0:
                        print(f"❌ Erreur Nom: DB({db_nom}) vs User({user_nom}) -> Pas de mots communs")
                        etudiant = None # Rejet

                # C. Vérification Mention (OPTIONNELLE ou SOUPLE)
                # Je conseille souvent de NE PAS bloquer sur la mention car les étudiants se trompent tout le temps
                # Si le matricule + tel + nom sont bons, c'est bon.
                # Si tu veux vraiment vérifier :
                if etudiant:
                    db_mention = normaliser_texte(etudiant.mention)
                    user_mention = normaliser_texte(mention_input)
                    
                    # On vérifie si l'un est contenu dans l'autre
                    # Ex: "GIM" dans "Génie Industriel..." (non) mais "Informatique" dans "Génie Informatique" (oui)
                    # Pour GIM vs Génie, c'est dur à gérer sans dictionnaire de mapping.
                    # Mieux vaut vérifier que la mention n'est pas totalement absurde, ou sauter cette étape.
                    print(f"ℹ️ Info Mention : DB({db_mention}) vs User({user_mention})")
                    # Je commente le blocage strict ici pour tester :
                    # if user_mention not in db_mention and db_mention not in user_mention:
                    #    etudiant = None 

            if etudiant and etudiant.actif is False:
                print("❌ Compte inactif")
                messages.error(request, "Votre compte n'est pas activé.")
                etudiant = None
            if etudiant:
                # 4. SUCCÈS
                request.session.flush() # Sécurité
                
                request.session["user_id"] = etudiant.id
                request.session["matricule"] = etudiant.matricule
                request.session["nom_prenom"] = etudiant.nom_prenom
                request.session["mention"] = etudiant.mention
                request.session["parcours"] = etudiant.parcours
                request.session["niveau"] = str(etudiant.niveau) # Convertir en str pour éviter soucis de comparaison
                request.session["annee"] = etudiant.annee_academique
                request.session["is_logged_in"] = True 

                cache.delete(cache_key) # Reset tentatives
                
                messages.success(request, f"Bienvenue {etudiant.nom_prenom} 👋")
                logger.info(f"Connexion réussie : {matricule_input}")
                
                # CORRECTION MAJEURE ICI : REDIRECT vers la vue accueil
                # Cela permet d'exécuter la logique de la vue 'accueil'
                return redirect("accueil") 

            else:
                # 5. ECHEC
                cache.set(cache_key, attempts + 1, 300)
                logger.warning(f"Échec connexion : {matricule_input}")
                messages.error(request, "Informations incorrectes.")
                return render(request, "connexion.html")

        except Exception as e:
            logger.error(f"Erreur critique : {str(e)}")
            messages.error(request, "Une erreur technique est survenue.")
            return render(request, "connexion.html")

    # CAS 2 : L'utilisateur arrive sur la page (GET)
    else:
        # On affiche simplement la page de connexion vide
        return render(request, "connexion.html")
    

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import EtudiantNiveau1, EtudiantNiveau2, Parrainage

from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

# 1. EMPÊCHE LE STOCKAGE DANS LE NAVIGATEUR (Bouton retour sécurisé) 
def accueil(request):
    """
    Affiche la page d’accueil. 
    Sécurisé contre le cache navigateur et optimisé via les données de session.
    """
    # Récupération des données de session
    matricule = request.session.get("matricule")
    niveau = request.session.get("niveau") # Supposons que c'est "1.0", "2.0" ou "N1"
    
    # 3. VERIFICATION DE SESSION STRICTE
    if not matricule or not niveau:
        logger.warning(f"Tentative d'accès sans session valide (IP: {request.META.get('REMOTE_ADDR')})")
        messages.warning(request, "Session expirée. Veuillez vous reconnecter.")
        return redirect("connexion")

    etudiant = None

    try:
        # 4. OPTIMISATION DE LA REQUÊTE DB
        # On utilise le niveau stocké en session pour cibler directement la bonne table
        # au lieu de chercher dans les deux à chaque fois.
        
        # Adaptation selon comment tu stockes le niveau (Float 2.0 ou String "N1"/"N2")
        # Ici je gère les deux cas probables basés sur tes fichiers précédents
        if str(niveau) in ["1.0", "1", "N1"]:
            etudiant = EtudiantNiveau1.objects.filter(matricule=matricule, actif=True).first()
        elif str(niveau) in ["2.0", "2", "N2", "GEL 2"]: # Ajoute tes variantes ici
            etudiant = EtudiantNiveau2.objects.filter(matricule=matricule, actif=True).first()
        else:
            # Fallback de sécurité : Si le niveau en session est corrompu, on cherche partout
            etudiant = (
                EtudiantNiveau1.objects.filter(matricule=matricule, actif=True).first()
                or EtudiantNiveau2.objects.filter(matricule=matricule, actif=True).first()
            )

        # 5. GESTION DU COMPTE INTROUVABLE OU DÉSACTIVÉ
        if not etudiant:
            # Si l'étudiant n'est plus trouvé (ex: supprimé ou banni pendant qu'il naviguait)
            request.session.flush() # On détruit sa session immédiatement
            messages.error(request, "Votre compte n'est plus accessible. Contactez l'admin.")
            return redirect("connexion")

        # 6. LOGIQUE MÉTIER (Parrainage)
        parrainage = None
        # On uniformise la vérification du niveau
        if hasattr(etudiant, 'niveau') and str(etudiant.niveau) in ["1.0", "1", "N1"]:
            parrainage = Parrainage.objects.filter(filleul=etudiant).select_related("parrain").first()
        total_parrains = EtudiantNiveau2.objects.filter(actif=True).count()

    # 2. Compter le nombre de parrainages actés (Binômes formés)
        total_parraines = Parrainage.objects.count()
        avis_list = Avis.objects.filter(rating__gte=4).order_by('-created_at')[:5]

    # On ajoute ces chiffres au contexte
    
        context = {
        "etudiant": etudiant,
        "parrainage": parrainage,
        "niveau": niveau,
        "avis_list": avis_list,
        
        # Les stats pour le tableau de bord
        "stats": {
             "parrains": total_parrains,
            "parraines": total_parraines
        
        } }

        return render(request, "index.html", context)

    except Exception as e:
        logger.error(f"Erreur critique vue accueil pour {matricule}: {str(e)}")
        messages.error(request, "Une erreur est survenue lors du chargement de votre profil.")
        return redirect("connexion")
    
    
def page_avis(request):
    """Affiche simplement la page pour donner son avis"""
    return render(request, "avis.html")
    
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password, check_password  # <--- NOUVEAUX IMPORTS
import logging

# On garde une trace des tentatives suspectes
logger = logging.getLogger(__name__)

@never_cache  # 1. Empêche le stockage dans l'historique
@require_http_methods(["GET", "POST"])  # 2. On autorise POST pour la saisie du code PIN
def voir_filleuls(request):
    """
    Affiche les filleuls UNIQUEMENT pour le parrain authentifié ET ayant déverrouillé son coffre-fort.
    """
    
    # --- A. VERIFICATION DE LA SESSION ---
    session_matricule = request.session.get("matricule")
    session_niveau = request.session.get("niveau")

    if not session_matricule:
        messages.warning(request, "Veuillez vous identifier pour accéder à cet espace.")
        return redirect("connexion")

    # --- B. CONTROLE D'ACCÈS BASÉ SUR LE RÔLE (RBAC) ---
    if str(session_niveau) not in ["2", "2.0", "N2", "GEL 2"]:
        logger.warning(f"Tentative d'accès illégale par {session_matricule}")
        messages.error(request, "Accès refusé. Réservé aux étudiants de Niveau 2.")
        return redirect("accueil")

    # --- C. RECUPERATION SECURISEE DU PARRAIN ---
    try:
        parrain = EtudiantNiveau2.objects.get(matricule=session_matricule, actif=True)
    except EtudiantNiveau2.DoesNotExist:
        logger.error(f"Session orpheline pour matricule {session_matricule}")
        request.session.flush()
        messages.error(request, "Votre compte n'est pas actif ou a été suspendu.")
        return redirect("connexion")

    # =========================================================================
    # --- D. LOGIQUE DE SECURITÉ RENFORCÉE (COFFRE-FORT / 2FA) ---
    # =========================================================================

    # CAS 1 : Le parrain n'a pas encore de code secret -> On l'oblige à en créer un
    if not parrain.code_secret:
        if request.method == "POST":
            nouveau_code = request.POST.get("nouveau_code", "").strip()
            if len(nouveau_code) != 4:
                messages.error(request,"le code doit avoir 4 caractere")
                return redirect("accueil")
                
            # Validation simple
            if len(nouveau_code) == 4 and nouveau_code.isdigit():
                # Hachage et sauvegarde
                parrain.code_secret = make_password(nouveau_code)
                parrain.save()
                
                # On marque le coffre comme ouvert pour cette session
                request.session['coffre_ouvert'] = True
                messages.success(request, "Code secret configuré avec succès !")
                return redirect("voir_filleuls") # Refresh propre
            else:
                messages.error(request, "Le code doit comporter exactement 4 chiffres.")
        
        # Affiche le template de création (à créer si tu ne l'as pas fait)
        return render(request, "creation_code.html")

    # CAS 2 : Le code existe mais le coffre n'est pas ouvert en session
    if not request.session.get('coffre_ouvert'):
        if request.method == "POST":
            code_saisi = request.POST.get("code_secret", "").strip()
            
            # Vérification cryptographique
            if check_password(code_saisi, parrain.code_secret):
                request.session['coffre_ouvert'] = True
                messages.success(request, "Identité confirmée 🔓")
                return redirect("voir_filleuls") # Refresh pour passer en GET
            else:
                # Log de sécurité pour tentative de brute force sur le PIN
                logger.warning(f"Mauvais code PIN saisi par {session_matricule}")
                messages.error(request, "Code incorrect ⛔")
        
        # Affiche le template de verrouillage (celui que je t'ai donné avant)
        return render(request, "verrouillage.html")

    # =========================================================================
    # --- E. ACCÈS AUX DONNÉES (Seulement si tout le reste est passé) ---
    # =========================================================================

    filleuls_relations = Parrainage.objects.filter(parrain=parrain).select_related("filleul")
    
    # On filtre pour ne garder que les filleuls actifs
    liste_filleuls = [rel.filleul for rel in filleuls_relations if rel.filleul.actif]

    context = {
        "parrain": parrain,
        "filleuls": liste_filleuls,
        "total": len(liste_filleuls),
    }
    
    return render(request, "voir_filleuls.html", context)


import threading
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class EmailThreade(threading.Thread):
    """
    Classe qui exécute l'envoi de l'email dans un processus séparé (Thread)
    pour ne pas bloquer l'interface utilisateur.
    """
    def __init__(self, email_message):
        self.email_message = email_message
        threading.Thread.__init__(self)

    def run(self):
        # C'est ici que l'envoi réel se fait
        self.email_message.send()

def envoyer_email_nouveau_filleul(parrain, filleul):
    """
    Prépare l'email et lance le thread d'envoi.
    """
    subject = f"🎓 Nouveau Filleul Assigné : {filleul.nom_prenom}"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [parrain.email] # Assure-toi que ce champ existe dans ton modèle

    # Contexte pour le template HTML
    context = {
        'parrain': parrain,
        'filleul': filleul,
        'site_url': "https://iut-connect.onrender.com/voir-filleuls/" # Change ceci par ton vrai domaine en prod
    }

    # Rendu du HTML et de la version Texte
    html_content = render_to_string('email/notification_parrain.html', context)
    text_content = strip_tags(html_content)

    # Création de l'objet Email
    msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
    msg.attach_alternative(html_content, "text/html")

    # Envoi via Threading (Non-bloquant)
    EmailThreade(msg).start()
# ============================================================
# --- VUE DE DÉCONNEXION ---
# ============================================================
def deconnexion(request):
    """Efface proprement toutes les données de session."""
    request.session.flush()
    messages.info(request, "Vous avez été déconnecté.")
    return redirect("connexion")


# ============================================================
# --- VUE D’ATTRIBUTION DE PARRAIN ---
# ============================================================
def attribuer_parrain(request):
    """Attribue automatiquement un parrain à un étudiant de niveau 1."""
    # Vérification d’authentification
    if not request.session.get("matricule"):
        messages.warning(request, "Vous devez d’abord vous connecter.")
        return redirect("connexion")

    # Seuls les étudiants du niveau 1 peuvent recevoir un parrain
    if request.session.get("niveau") != "1":
        messages.error(request, "Seuls les étudiants du niveau 1 peuvent recevoir un parrain.")
        return redirect("accueil")

    matricule = request.session.get("matricule")
    mention = request.session.get("mention")
    parcours = request.session.get("parcours")
    annee = request.session.get("annee")

    filleul = EtudiantNiveau1.objects.filter(matricule=matricule, actif=True).first()
    if not filleul:
        messages.error(request, "Erreur interne : étudiant introuvable ou inactif.")
        return redirect("accueil")

    # Vérifie s’il a déjà un parrain
    if hasattr(filleul, "parrainage"):
        messages.info(request, "Vous avez déjà un parrain attribué.")
        return redirect("accueil")

    # --- Recherche de parrains disponibles ---
    parrains = EtudiantNiveau2.objects.filter(mention__iexact=mention, actif=True)

    # Filtrer par parcours si possible
    parrains_parcours = parrains.filter(parcours__iexact=parcours)
    if parrains_parcours.exists():
        parrains = parrains_parcours
    # sinon on garde toute la mention

    if not parrains.exists():
        messages.warning(request, "Aucun parrain disponible pour cette mention actuellement.")
        return redirect("accueil")

    # --- Option : filtrer sur l'année courante ou inférieure ---
    parrains = parrains.filter(Q(annee_academique=annee) | Q(annee_academique__lt=annee))

    # --- Répartition équitable ---
    counts = (
        Parrainage.objects.filter(parrain__in=parrains)
        .values("parrain")
        .annotate(total=Count("id"))
    )
    repartition = {c["parrain"]: c["total"] for c in counts}
    min_filleuls = min(repartition.get(p.id, 0) for p in parrains)
    parrains_eligibles = [p for p in parrains if repartition.get(p.id, 0) == min_filleuls]

    # Choix aléatoire parmi les parrains éligibles
    parrain_choisi = random.choice(parrains_eligibles)

    # --- Création du parrainage ---
    Parrainage.objects.create(parrain=parrain_choisi, filleul=filleul)
    # === ENVOI DE L'EMAIL ASYNCHRONE ===
    # On vérifie juste que le parrain a un email
    if parrain_choisi.email:
        try:
            envoyer_email_nouveau_filleul(parrain_choisi, filleul)
        except Exception as e:
            # On log l'erreur mais on ne bloque pas l'utilisateur
            logger.error(f"Erreur envoi mail : {e}")

    messages.success(
        request,
        f"🎉 Votre parrain est {parrain_choisi.nom_prenom} ({parrain_choisi.parcours})."
    )
    return redirect("accueil")


# views.py
from django.contrib.auth.hashers import make_password, check_password

@never_cache
def voir_parrain(request):
    # 1. Vérif Session
    session_matricule = request.session.get("matricule")
    if not session_matricule:
        return redirect("connexion")

    # 2. Récupération Filleul
    try:
        filleul = EtudiantNiveau1.objects.get(matricule=session_matricule, actif=True)
    except EtudiantNiveau1.DoesNotExist:
        return redirect("connexion")

    # === COFFRE-FORT / SÉCURITÉ ===
    
    # A. Création du code si inexistant
    if not filleul.code_secret:
        if request.method == "POST":
            nouveau_code = request.POST.get("nouveau_code")
            if len(nouveau_code) == 4 and nouveau_code.isdigit():
                filleul.code_secret = make_password(nouveau_code)
                filleul.save()
                request.session['coffre_filleul_ouvert'] = True
                messages.success(request, "Code secret créé !")
                return redirect("voir_parrain")
            else:
                messages.error(request, "Le code doit faire 4 chiffres.")
        return render(request, "creation_code.html") # Tu peux réutiliser le même template

    # B. Vérification du code (Verrouillage)
    if not request.session.get('coffre_filleul_ouvert'):
        if request.method == "POST":
            code_saisi = request.POST.get("code_secret")
            if check_password(code_saisi, filleul.code_secret):
                request.session['coffre_filleul_ouvert'] = True
                messages.success(request, "Accès autorisé 🔓")
                return redirect("voir_parrain")
            else:
                messages.error(request, "Code incorrect ⛔")
        
        # On réutilise le template de verrouillage, mais on peut passer un contexte pour changer le titre
        return render(request, "verrouillage.html", {"titre": "Accès Filleul Sécurisé"})

    # === ACCÈS DONNÉES (Si coffre ouvert) ===
    parrainage = Parrainage.objects.filter(filleul=filleul).select_related('parrain').first()
    
    context = {
        "filleul": filleul,
        "parrain": parrainage.parrain if parrainage else None
    }
    return render(request, "voir_parrain.html", context)
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt # À retirer si tu gères le CSRF token en JS
from .models import Avis
import json

@require_POST
def soumettre_avis(request):
    try:
        # On récupère les données (supporte FormData ou JSON)
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        # Création de l'avis
        avis = Avis.objects.create(
            rating=data.get('rating', 5),
            kind=data.get('kind', 'experience'),
            email=data.get('email', ''),
            title=data.get('title', ''),
            message=data.get('message', ''),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({'success': True, 'message': 'Avis enregistré avec succès !'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    
from django.core.mail import send_mail
import random
import string
import threading
from django.core.mail import send_mail

class EmailThread(threading.Thread):
    def __init__(self, subject, message, from_email, recipient_list):
        self.subject = subject
        self.message = message
        self.from_email = from_email
        self.recipient_list = recipient_list
        threading.Thread.__init__(self)

    def run(self):
        # Cette partie s'exécute en arrière-plan
        try:
            send_mail(
                self.subject,
                self.message,
                self.from_email,
                self.recipient_list,
                fail_silently=False,
            )
            print("✅ Email envoyé avec succès (Thread).")
        except Exception as e:
            print(f"❌ Erreur d'envoi email : {e}")

def mot_de_passe_oublie(request):
    if request.method == "POST":
        matricule = request.POST.get("matricule").upper()
        # On cherche dans les deux tables
        user = EtudiantNiveau1.objects.filter(matricule=matricule).first()
        niveau = "1"
        
        if not user:
            user = EtudiantNiveau2.objects.filter(matricule=matricule).first()
            niveau = "2"
            
        if user and user.email:
            # 1. Génération du Code
            temp_code = ''.join(random.choices(string.digits, k=6))
            
            # 2. Sauvegarde en Base de Données (Priorité absolue)
            # On stocke ce code temporaire (hashé)
            user.code_secret = make_password(temp_code[:4]) # On prend les 4 premiers pour le PIN
            user.save()

            # 3. Préparation des données de l'email
            sujet = 'Réinitialisation Code Secret - IUT Connect+'
            message = f"""Bonjour {user.nom_prenom},Votre code secret temporaire est : {temp_code[:4]}.Connectez-vous et utilisez ce code pour accéder à votre espace.(Vous pourrez le changer ensuite)."""
            expediteur = 'siddick369@gmail.com' # Ton email
            destinataires = [user.email]

            # 4. Envoi Asynchrone (Threading)
            # Le script continue immédiatement sans attendre que Gmail réponde
            EmailThread(sujet, message, expediteur, destinataires).start()

            # 5. Feedback immédiat à l'utilisateur
            messages.success(request, "Un code temporaire a été envoyé à votre adresse email.")
            return redirect("connexion") # Ou la page pour entrer le code
        

        else:
            messages.error(request, "Matricule introuvable ou pas d'email associé.")
    
    return render(request, "forgot_password.html")




@never_cache
def signaler_probleme(request):
    if request.method == "POST":
        matricule = request.session.get("matricule")
        niveau = request.session.get("niveau")
        
        type_pb = request.POST.get("type_probleme")
        description = request.POST.get("description")

        if matricule and description:
            signalement=Signalement.objects.create(
                matricule_emetteur=matricule,
                niveau_emetteur=niveau,
                type_probleme=type_pb,
                description=description
            )
           
# ... (ton code précédent : récupération matricule, if user, etc.) ...

            # 1. Préparation des données
            # 2. Préparation de l'Email HTML
            try:
                sujet = f"⚠️ ALERTE : {type_pb.upper()} - {matricule}"
                
                # Contexte pour le template HTML
                context = {
                    'matricule': matricule,
                    'niveau': niveau,
                    'type_display': signalement.get_type_probleme_display(), # Affiche "Binôme Injoignable" au lieu de "absent"
                    'description': description,
                    # Construit l'URL absolue vers l'admin (ex: http://tonsite.com/admin/...) 
                }

                # Rendu du HTML en string
                html_content = render_to_string('email/alerte_signalement.html', context)
                text_content = strip_tags(html_content) # Version texte brut pour les vieux clients mail

                # Création de l'objet Email
                email = EmailMultiAlternatives(
                    subject=sujet,
                    body=text_content, # Contenu texte par défaut
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.DEFAULT_FROM_EMAIL]
                )
                email.attach_alternative(html_content, "text/html") # Attache la version HTML stylée

                # 3. Lancement du Thread (Envoi en arrière-plan)
                # Le serveur n'attend pas la réponse SMTP pour continuer
                EmailThreadia(email).start()
            

            except Exception as e:
                # Si la préparation du mail échoue, on log l'erreur mais on ne bloque pas l'utilisateur
                print(f"Erreur préparation mail : {e}")

            # On renvoie du JSON pour le gérer via AJAX sans recharger la page
            return JsonResponse({"success": True, "message": "Signalement envoyé à l'administration."})
        
        return JsonResponse({"success": False, "error": "Formulaire incomplet."})
        
    return redirect("accueil")


from django.shortcuts import render

def rgpd(request):
    """
    Affiche la page de Politique de Confidentialité (RGPD).
    Accessible à tous (même sans être connecté).
    """
    return render(request, 'rgpd.html')

def portfolio(request):
    """
    Affiche la page Portfolio technique / Développeur.
    """
    return render(request, 'developpeur.html')