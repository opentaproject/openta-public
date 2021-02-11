from django.db import models
import uuid
from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib import admin

# Create your models here.





class OpenTASite(models.Model ):

    db_name = models.CharField(max_length=4096, unique=True, default='default',  editable=True)
    objects = models.Manager()

    def __str__(self):
        return self.db_name

    #def getSite(self ):
    #    return Site.objects.get_or_create(name=self.subdomain) 




class OpenTASiteAdminForm(forms.ModelForm):

    class Meta :
        model = OpenTASite
        fields = ('id','db_name',)

class OpenTASiteAdmin( admin.ModelAdmin ):
    model = OpenTASite
    list_display = ['id','db_name']
    form = OpenTASiteAdminForm



#def getfirstOpenTASite() :
#    print("GET FIRRST OPENTA SITE")
#    print("SUBDOMAIN = ", settings.SUBDOMAIN)
#    obj, created = OpenTASite.objects.get_or_create(subdomain=settings.SUBDOMAIN)
#    return obj.id



admin.site.register( OpenTASite, OpenTASiteAdmin)
