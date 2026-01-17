from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.utils import timezone

# --- VALIDATEUR POUR TÉLÉPHONE ---
telephone_validator = RegexValidator(
    regex=r'^6\d{8}$',
    message="Le numéro de téléphone doit commencer par 6 et contenir exactement 9 chiffres."
)

# --- CHOIX DE MENTIONS ET PARCOURS ---
MENTIONS = [
    ('GI', 'Génie Informatique'),
    ('GM', 'Génie Mécanique'),
    ('GE', 'Génie Électrique'),
]

PARCOURS = [
    ('RT', 'Réseaux et Télécommunications'),
    ('GLO', 'Génie Logiciel'),
    ('IA', 'Intelligence Artificielle'),
    ('AUTRE', 'Autre'),
]

ANNEES = [
    ('2023-2024', '2023-2024'),
    ('2024-2025', '2024-2025'),
    ('2025-2026', '2025-2026'),
]


# --- TABLE DES ÉTUDIANTS NIVEAU 1 ---
class EtudiantNiveau1(models.Model):
    numero = models.IntegerField(null=True,blank=True)  # <-- Importé depuis l’annuaire, pas auto-généré
    nom_prenom = models.CharField(max_length=100)
    matricule = models.CharField(max_length=51, unique=False)
    email = models.EmailField(unique=False,null=True,blank=True)
    telephone = models.CharField(max_length=20, validators=[telephone_validator],blank=True,unique=False,null=True)
    mention = models.CharField(max_length=40)
    parcours = models.CharField(max_length=20)
    niveau = models.CharField(max_length=10, default='N1')
    annee_academique = models.CharField(max_length=15, choices=ANNEES)
    
    code_secret = models.CharField(max_length=128, null=True, blank=True) 

    actif = models.BooleanField(default=True)
    

    def __str__(self):
        return f"{self.nom_prenom} ({self.matricule})"


# --- TABLE DES ÉTUDIANTS NIVEAU 2 ---
class EtudiantNiveau2(models.Model):
    numero = models.IntegerField(null=True,blank=True)  # <-- Importé depuis l’annuaire aussi
    nom_prenom = models.CharField(max_length=100)
    matricule = models.CharField(max_length=50, unique=False)
    email = models.EmailField(unique=False,null=True,blank=True)
    telephone = models.CharField(max_length=9, validators=[telephone_validator], blank=True,null=True)
    mention = models.CharField(max_length=40,)
    parcours = models.CharField(max_length=20,)
    niveau = models.CharField(max_length=10, default='N2')
    annee_academique = models.CharField(max_length=15, choices=ANNEES)
    actif = models.BooleanField(default=True)

    # ... tes champs existants ...
    # Ajout du code secret (nullable au début car ils ne l'ont pas encore créé)
    code_secret = models.CharField(max_length=128, null=True, blank=True, help_text="Code PIN à 4 chiffres")

    def __str__(self):
        return f"{self.nom_prenom} ({self.matricule})"


# --- TABLE PARRAINAGE ---
class Parrainage(models.Model):
    parrain = models.ForeignKey(
        EtudiantNiveau2,
        on_delete=models.SET_NULL,
        null=True,
        related_name='filleuls'
    )
    filleul = models.OneToOneField(
        EtudiantNiveau1,
        on_delete=models.CASCADE,
        related_name='parrainage'
    )
    date_attribution = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.filleul.nom_prenom} ↔ {self.parrain.nom_prenom if self.parrain else 'Aucun'}"
    
class Signalement(models.Model):
    TYPES_PROBLEME = [
        ('absent', 'Parrain/Filleul injoignable'),
        ('inapte', 'Incompatibilité d\'humeur'),
        ('harcelement', 'Harcèlement / Comportement déplacé'),
        ('autre', 'Autre'),
    ]
    
    matricule_emetteur = models.CharField(max_length=20)
    niveau_emetteur = models.CharField(max_length=5) # "1" ou "2"
    type_probleme = models.CharField(max_length=20, choices=TYPES_PROBLEME)
    description = models.TextField()
    date_signalement = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False) # Pour l'admin

    def __str__(self):
        return f"Signalement de {self.matricule_emetteur} - {self.type_probleme}"    
    
from django.db import models

class Avis(models.Model):
    TYPE_CHOICES = [
        ('suggestion', 'Suggestion'),
        ('bug', 'Bug'),
        ('experience', 'Expérience utilisateur'),
        ('autre', 'Autre'),
    ]

    rating = models.IntegerField(default=5)  # Note de 1 à 5
    kind = models.CharField(max_length=20, choices=TYPE_CHOICES, default='experience')
    email = models.EmailField(blank=True, null=True)
    title = models.CharField(max_length=60)
    message = models.TextField(max_length=700)
    
    # Méta-données
    ip_address = models.GenericIPAddressField(blank=True, null=True) # Utile pour bloquer les spammeurs
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} ({self.rating}/5)"

    class Meta:
        verbose_name = "Avis Utilisateur"
        verbose_name_plural = "Avis Utilisateurs"
        ordering = ['-created_at']
    
    
    