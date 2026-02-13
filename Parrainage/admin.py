from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import CharWidget
from .models import EtudiantNiveau1, EtudiantNiveau2, Parrainage

from import_export import widgets
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import random
from django.db.models import Count, Q
from .models import Parrainage, EtudiantNiveau2

def executer_attribution_auto(filleul):
    """Logique d'attribution pour un seul étudiant N1"""
    if hasattr(filleul, "parrainage"):
        return None

    # Recherche de parrains (Mention > Parcours > Année)
    parrains = EtudiantNiveau2.objects.filter(mention__iexact=filleul.mention, actif=True)
    
    parrains_parcours = parrains.filter(parcours__iexact=filleul.parcours)
    if parrains_parcours.exists():
        parrains = parrains_parcours

    if not parrains.exists():
        return None

    # Répartition équitable
    # On compte combien de filleuls chaque parrain a ACTUELLEMENT
    parrains = parrains.annotate(nb_filleuls=Count('filleuls'))
    min_filleuls = parrains.order_by('nb_filleuls').first().nb_filleuls
    
    parrains_eligibles = parrains.filter(nb_filleuls=min_filleuls)
    parrain_choisi = random.choice(list(parrains_eligibles))

    return Parrainage.objects.create(parrain=parrain_choisi, filleul=filleul)


import openpyxl
from django.contrib import admin, messages
from django.http import HttpResponse
from .models import EtudiantNiveau1, EtudiantNiveau2, Parrainage
from django.utils import timezone

# --- ACTION EXPORT EXCEL ---
@admin.action(description="Exporter la liste en Excel")
def export_parrainages_excel(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Parrainages_{timezone.now().strftime("%Y-%m-%d")}.xlsx'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Liste des Parrainages"

    # En-têtes
    headers = [
        'Nom Filleul (N1)', 'Matricule Filleul', 'Parcours Filleul',
        'Nom Parrain (N2)', 'Matricule Parrain', 'Parcours Parrain',
        'Date d\'attribution'
    ]
    ws.append(headers)

    # Données
    for p in queryset.select_related('filleul', 'parrain'):
        ws.append([
            p.filleul.nom_prenom, p.filleul.matricule, p.filleul.parcours,
            p.parrain.nom_prenom if p.parrain else "N/A",
            p.parrain.matricule if p.parrain else "N/A",
            p.parrain.parcours if p.parrain else "N/A",
            p.date_attribution.strftime("%d/%m/%Y %H:%M")
        ])

    wb.save(response)
    return response

# --- ACTION ATTRIBUTION AUTO ---
@admin.action(description="Attribuer parrains aux N1 sélectionnés")
def attribuer_auto_action(modeladmin, request, queryset):
    succes = 0
    echecs = 0
    
    for etudiant in queryset:
        try:
            result = executer_attribution_auto(etudiant)
            if result:
                succes += 1
            else:
                echecs += 1
        except Exception:
            echecs += 1
            
    messages.success(request, f"{succes} parrainages créés avec succès. {echecs} échecs (manque de parrains ou déjà parrainés).")

# # --- ENREGISTREMENT DES CLASSES ADMIN ---

# @admin.register(EtudiantNiveau1)
# class EtudiantNiveau1Admin(admin.ModelAdmin):
#     list_display = ('nom_prenom', 'matricule', 'mention', 'parcours', 'get_parrain')
#     list_filter = ('mention', 'parcours', 'annee_academique')
#     search_fields = ('nom_prenom', 'matricule')
#     actions = [attribuer_auto_action] # Bouton dans le menu déroulant "Actions"

#     def get_parrain(self, obj):
#         return obj.parrainage.parrain.nom_prenom if hasattr(obj, 'parrainage') else "Aucun"
#     get_parrain.short_description = "Parrain"

@admin.register(Parrainage)
class ParrainageAdmin(admin.ModelAdmin):
    list_display = ('filleul', 'parrain', 'date_attribution', 'actif')
    list_filter = ('filleul__mention', 'filleul__parcours', 'actif')
    actions = [export_parrainages_excel] # Bouton d'export

class EmailWidget(widgets.CharWidget):
    """Widget personnalisé pour valider les adresses e-mail."""
    def clean(self, value, row=None, *args, **kwargs):
        value = super().clean(value, row, *args, **kwargs)
        if value:
            try:
                validate_email(value)
            except ValidationError:
                raise ValidationError(f"Adresse e-mail invalide : {value}")
        return value
# ============================================================
# 🔹 RESSOURCES D'IMPORT/EXPORT
# ============================================================

class EtudiantNiveau1Resource(resources.ModelResource):
    numero = fields.Field(attribute='numero', column_name='N°', widget=CharWidget())
    matricule = fields.Field(attribute='matricule', column_name='MATRICULE', widget=CharWidget())
    nom_prenom = fields.Field(attribute='nom_prenom', column_name='NOMS ET PRENOMS')
    email = fields.Field(attribute='email', column_name='ADRESSE_EMAIL')
    telephone = fields.Field(attribute='telephone', column_name='Téléphone')
    mention = fields.Field(attribute='mention', column_name='MENTION')
    parcours = fields.Field(attribute='parcours', column_name='PARCOURS')
    niveau = fields.Field(attribute='niveau', column_name='Niveau', widget=CharWidget())
    annee_academique = fields.Field(attribute='annee_academique', column_name='Année académique', widget=CharWidget())
    #actif = fields.Field(attribute='actif', column_name='Actif', widget=CharWidget())

    class Meta:
        model = EtudiantNiveau1
        import_id_fields = ('matricule',)  # Empêche les doublons
        skip_unchanged = True
        report_skipped = True
        fields = (
            'numero', 'nom_prenom', 'matricule', 'email', 'telephone',
            'mention', 'parcours', 'niveau', 'annee_academique', 'actif'
        )
        export_order = fields


class EtudiantNiveau2Resource(resources.ModelResource):
    numero = fields.Field(attribute='numero', column_name='N°', widget=CharWidget())
    matricule = fields.Field(attribute='matricule', column_name='MATRICULE', widget=CharWidget())
    nom_prenom = fields.Field(attribute='nom_prenom', column_name='NOMS ET PRENOMS')
    email = fields.Field(attribute='email', column_name='ADRESSE_EMAIL')
    telephone = fields.Field(attribute='telephone', column_name='Téléphone')
    mention = fields.Field(attribute='mention', column_name='MENTION')
    parcours = fields.Field(attribute='parcours', column_name='PARCOURS')
    niveau = fields.Field(attribute='niveau', column_name='Niveau', widget=CharWidget())
    annee_academique = fields.Field(attribute='annee_academique', column_name='Année académique', widget=CharWidget())
    #actif = fields.Field(attribute='actif', column_name='Actif', widget=CharWidget())

    class Meta:
        model = EtudiantNiveau2
        import_id_fields = ('matricule',)
        skip_unchanged = True
        report_skipped = True
        fields = (
            'numero', 'nom_prenom', 'matricule', 'email', 'telephone',
            'mention', 'parcours', 'niveau', 'annee_academique', 'actif'
        )
        export_order = fields


# ============================================================
# 🔹 CONFIGURATION ADMIN POUR CHAQUE TABLE
# ============================================================

@admin.register(EtudiantNiveau1)
class EtudiantNiveau1Admin(ImportExportModelAdmin):
    resource_class = EtudiantNiveau1Resource
    list_display = ('numero', 'nom_prenom', 'matricule', 'mention', 'parcours', 'niveau', 'annee_academique', 'actif', 'get_parrain')
    search_fields = ('nom_prenom', 'matricule', 'mention', 'parcours')
    list_filter = ('mention', 'parcours', 'niveau', 'annee_academique', 'actif')
    ordering = ('numero',)
    actions = [attribuer_auto_action] # Bouton dans le menu déroulant "Actions"

    def get_parrain(self, obj):
        return obj.parrainage.parrain.nom_prenom if hasattr(obj, 'parrainage') else "Aucun"
    get_parrain.short_description = "Parrain"



@admin.register(EtudiantNiveau2)
class EtudiantNiveau2Admin(ImportExportModelAdmin):
    resource_class = EtudiantNiveau2Resource
    list_display = ('numero', 'nom_prenom', 'matricule', 'mention', 'parcours', 'niveau', 'annee_academique', 'actif')
    search_fields = ('nom_prenom', 'matricule', 'mention', 'parcours')
    list_filter = ('mention', 'parcours', 'niveau', 'annee_academique', 'actif')
    ordering = ('numero',)


    
from django.contrib import admin
from django.utils.html import format_html
from .models import Avis

@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    # 1. CE QUI S'AFFICHE DANS LA LISTE
    list_display = ('titre_court', 'etoiles_visuelles', 'badge_type', 'email_link', 'date_creation')
    
    # 2. LES FILTRES À DROITE
    list_filter = ('rating', 'kind', 'created_at')
    
    # 3. BARRE DE RECHERCHE (Cherche dans titre, message et email)
    search_fields = ('title', 'message', 'email')
    
    # 4. ORGANISATION DU FORMULAIRE DE DÉTAIL
    fieldsets = (
        ('Informations Principales', {
            'fields': ('rating', 'kind', 'title', 'message')
        }),
        ('Auteur', {
            'fields': ('email',)
        }),
        ('Méta-données (Lecture seule)', {
            'fields': ('ip_address', 'created_at'),
            'classes': ('collapse',) # Permet de replier cette section
        }),
    )
    
    # Champs qu'on ne peut pas modifier manuellement
    readonly_fields = ('created_at', 'ip_address')
    
    # Tri par défaut (du plus récent au plus vieux)
    ordering = ('-created_at',)

    # --- MÉTHODES PERSONNALISÉES POUR LE DESIGN ---

    def etoiles_visuelles(self, obj):
        """Affiche des étoiles jaunes au lieu du chiffre"""
        color = "#FFD700" if obj.rating >= 3 else "#FF4500" # Jaune ou Rouge selon la note
        stars = "★" * obj.rating
        return format_html('<span style="color: {}; font-size: 1.2rem;">{}</span>', color, stars)
    etoiles_visuelles.short_description = "Note"

    def badge_type(self, obj):
        """Met une couleur de fond selon le type d'avis"""
        colors = {
            'suggestion': '#17a2b8', # Bleu
            'bug': '#dc3545',        # Rouge
            'experience': '#28a745', # Vert
            'autre': '#6c757d',      # Gris
        }
        color = colors.get(obj.kind, '#333')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 0.8rem;">{}</span>',
            color, obj.get_kind_display()
        )
    badge_type.short_description = "Type"

    def titre_court(self, obj):
        """Coupe le titre s'il est trop long"""
        return (obj.title[:30] + '...') if len(obj.title) > 30 else obj.title
    titre_court.short_description = "Titre"

    def email_link(self, obj):
        """Rend l'email cliquable"""
        if obj.email:
            return format_html('<a href="mailto:{}">{}</a>', obj.email, obj.email)
        return "-"
    email_link.short_description = "Email"

    def date_creation(self, obj):
        return obj.created_at.strftime("%d/%m/%Y %H:%M")
    date_creation.short_description = "Date"
    
    
from django.contrib import admin
from django.utils.html import format_html
from .models import Signalement


@admin.register(Signalement)
class SignalementAdmin(admin.ModelAdmin):
    # CORRECTION ICI : J'ai remplacé 'statut_traitement' par 'traite' directment
    list_display = ('alerte_visuelle', 'matricule_emetteur', 'type_probleme', 'date_creation', 'traite')
    
    list_filter = ('traite', 'type_probleme', 'date_signalement')
    search_fields = ('matricule_emetteur', 'description')
    
    # Cela permet de cocher/décocher la case "traite" directement dans la liste
    list_editable = ('traite',) 
    
    readonly_fields = ('date_signalement',)

    def alerte_visuelle(self, obj):
        """Affiche un ⚠️ si non traité, sinon un ✅"""
        if not obj.traite:
            return format_html('<span style="color:red; font-weight:bold; font-size:1.2rem;">⚠️ À TRAITER</span>')
        return format_html('<span style="color:green; font-weight:bold;">✅ OK</span>')
    alerte_visuelle.short_description = "État"

    def date_creation(self, obj):
        return obj.date_signalement.strftime("%d/%m/%Y à %H:%M")
    date_creation.short_description = "Date"