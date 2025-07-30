from django.contrib import admin
from djangoldp.admin import DjangoLDPAdmin
from djangoldp.models import Model
from djangoldp_blog.models import Article

class ArticleAdmin(admin.ModelAdmin):
    class Media:
        js = [
            '/static/js/tinymce/jquery.tinymce.min.js', 
            '/static/js/tinymce/tinymce.min.js', 
            '/static/js/tinymce/textarea.js', 
        ]

admin.site.register(Article, ArticleAdmin)
