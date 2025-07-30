from os import link
from unicodedata import name
from django.db import models
from djangoldp.models import Model
from django.contrib.auth import get_user_model
from tinymce.models import HTMLField

class Thematic(Model):
    name = models.CharField(max_length=50, blank=True, null=True, verbose_name="nom de la thématique")
    number = models.IntegerField(blank=True, null=True, verbose_name="numéro de la thématique")
    text = models.CharField(max_length=250, blank=True, null=True, verbose_name="sous-titre de la thématique")

    def __str__(self):
        return self.name

class Article(Model):
    title = models.CharField(max_length=100, blank=True, null=True,verbose_name="Titre de l'article")
    thematic = models.ManyToManyField(Thematic, blank=True, max_length=50, verbose_name="Thématique",related_name='article')
    img = models.ImageField(blank=True, null=True, verbose_name="image de présentation")
    presentation = models.CharField(max_length=250, blank=True, null=True, verbose_name="texte de présentation de l'article")
    content = models.TextField(blank=True, null=True, verbose_name="contenu de l'article")    
    author = models.ForeignKey(get_user_model(), blank=True, null=True,on_delete=models.SET_NULL)
    createdate = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updatedate = models.DateTimeField(auto_now=True, verbose_name="Date de dernière mise à jour")

    class Meta:
        auto_author = 'author'
        owner_field = 'author'
        ordering = ['-createdate']
        container_path = "articles"
        rdf_type = 'hd:article'

    def __str__(self):
        return '{}'.format(self.title)

class Documenttype(Model):
    name = models.CharField(max_length=50, blank=True, null=True, verbose_name="nom du type de document")

    def __str__(self):
        return self.name

class Blogdocument(Model):
    name = models.CharField(max_length=250, blank=True, null=True,verbose_name="Nom du document")
    link = models.URLField(max_length=250, blank=True, null=True,verbose_name="Lien vers le document")
    thematic = models.ManyToManyField(Thematic, blank=True, max_length=50, verbose_name="Thématique",related_name='document')
    documenttype = models.ManyToManyField(Documenttype, blank=True, max_length=50, verbose_name="Type de document",related_name='documenttype')

    class Meta(Model.Meta):
        anonymous_perms = []
        authenticated_perms = ['view', 'change', 'add']
        rdf_type = 'blog:document'

    def __str__(self):
        return self.name

class Contactlist(Model):
    name = models.CharField(max_length=250, blank=True, null=True,verbose_name="Nom de la liste de contact")
    link = models.URLField(max_length=250, blank=True, null=True,verbose_name="Lien vers la liste de contact")
    thematic = models.ManyToManyField(Thematic, blank=True, max_length=50, verbose_name="Thématique",related_name='contactlist')

    class Meta(Model.Meta):
        anonymous_perms = []
        authenticated_perms = ['view', 'change', 'add']
        rdf_type = 'blog:contactlist'

    def __str__(self):
        return self.name
