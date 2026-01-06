from django.urls import path
from . import views



urlpatterns = [
    path('', views.connexion_etudiant, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('attribuer-parrain/', views.attribuer_parrain, name='attribuer'),
    path('accueil/', views.accueil, name='accueil'),
    path('voir-filleuls/', views.voir_filleuls, name='voir_filleuls'),
    path('voir-parrain/', views.voir_parrain, name='voir_parrain'),
    path('avis/', views.page_avis, name='avis'),
    path('signaler/', views.signaler_probleme, name='signaler'),
    path('mot-de-passe-oublie/', views.mot_de_passe_oublie, name='mot-de-passe-oublie'),
    path('api/avis/', views.soumettre_avis, name='soumettre_avis'),
    path('confidentialite/', views.rgpd, name='rgpd'),
    path('developpeur/', views.portfolio, name='developpeur'),




    
    
]

