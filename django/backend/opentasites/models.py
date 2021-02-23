from django.db import models
import uuid
from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib import admin
import random

# Create your models here.





def random_db_name( subdomain ):
    return "%s-%s" % ( str( subdomain ), random.randint(10000,99999) )

class OpenTASite(models.Model ):

    subdomain = models.CharField(max_length=4096, editable=True) 
    db_name = models.CharField(max_length=4096,  editable=True)
    db_label= models.CharField(max_length=4096,  editable=True)
    objects = models.Manager()

    def __str__(self):
        return self.subdomain
    
    def save(self, *args, **kwargs):
        if self.db_name is None:
            self.db_name = self.subdomain + '-' + str( random.randint( 11111,99999) )
        if self.db_label is None:
            self.db_name = self.subdomain 
        super(OpenTASite, self).save(*args, **kwargs)

    #def getSite(self ):
    #    return Site.objects.get_or_create(name=self.subdomain) 




class OpenTASiteAdminForm(forms.ModelForm):

    class Meta :
        model = OpenTASite
        fields = ('id','subdomain','db_name',)

class OpenTASiteAdmin( admin.ModelAdmin ):
    model = OpenTASite
    list_display = ['id','subdomain','db_name']
    form = OpenTASiteAdminForm



#def getfirstOpenTASite() :
#    print("GET FIRRST OPENTA SITE")
#    print("SUBDOMAIN = ", settings.SUBDOMAIN)
#    obj, created = OpenTASite.objects.get_or_create(subdomain=settings.SUBDOMAIN)
#    return obj.id



admin.site.register( OpenTASite, OpenTASiteAdmin)
