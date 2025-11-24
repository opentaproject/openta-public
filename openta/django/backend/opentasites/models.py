import logging
import random

from django_json_widget.widgets import JSONEditorWidget

from django import forms
from django.contrib import admin

# from django.contrib.sites.models import Site
from django.db import IntegrityError, models
from django.db.models import JSONField

logger = logging.getLogger(__name__)


def random_db_name(subdomain):
    return "%s-%s" % (str(subdomain), random.randint(10000, 99999))


class OpenTASite(models.Model):
    subdomain = models.CharField(max_length=4096, editable=True)
    course_key = models.CharField(max_length=4096, default="", editable=True)
    db_name = models.CharField(max_length=4096, editable=True)
    db_label = models.CharField(max_length=4096, default="", editable=True)
    creator = models.CharField(max_length=4096, default="", editable=True)
    last_activity = models.DateTimeField(auto_now=True)
    data = JSONField(default=dict)

    # objects = models.Manager()

    class Meta:
        # constraints = [ models.UniqueConstraint(fields=['db_name'],name="Database must be unique" ),
        #                models.UniqueConstraint(fields=['subdomain'],name="Subdomain value must be unique" ) ]
        unique_together = ("subdomain", "course_key")

    def __str__(self):
        return self.subdomain

    def save(self, *args, **kwargs):
        #logger.error("SAVING MODEL %s " % self.subdomain)
        if self.db_name is None:
            self.db_name = self.subdomain + "-" + str(random.randint(11111, 99999))
        if self.db_label is None:
            self.db_name = self.subdomain
        try:
            super(OpenTASite, self).save(*args, **kwargs)
        except IntegrityError:
            logger.error(f"INTEGRITY_ERROR SAVING  ERROR {self.subdomain} ")
        except Exception as e:
            logger.error(f"ERROR_SAVING  {self.subdomain} {type(e).__name__}")

    # def getSite(self ):
    #    return Site.objects.get_or_create(name=self.subdomain)


schema = {
    "type": "dict",  # or 'object'
    "keys": {  # or 'properties'
        "creator": {"type": "string"},
        "creation_date": {"type": "string"},
    },
}


class OpenTASiteAdminForm(forms.ModelForm):
    class Meta:
        model = OpenTASite
        fields = ("id", "subdomain", "course_key", "db_name", "db_label", "data")
        widgets = {"data": JSONEditorWidget}


class OpenTASiteAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        ro_fields = super(OpenTASiteAdmin, self).get_readonly_fields(request, obj)
        if request.user.username == "super":
            ro_fields = ()
        return ro_fields

    def get_queryset(self, request):
        # qs = super(OpenTASiteAdmin,self).get_queryset(request)
        qs = OpenTASite.objects.using("opentasites").all()
        if request.user.username == "super":
            return qs
        else:
            subdomain = request.META["HTTP_HOST"].split(".")[0].split(":")[0]  # circular import avoided
            qs = qs.filter(subdomain=subdomain)
            data = list(qs.values_list("data", flat=True))[0]
            if not "description" in data.keys():
                opentasite = OpenTASite.objects.using("opentasites").filter(subdomain=subdomain)[0]
                opentasite.data["description"] = ""
                opentasite.save()
        return qs

    # def get_queryset(self,request ) :
    #   qs = super(OpenTASiteAdmin,self).get_queryset(request)
    #   if request.user.username == 'super' :
    #       return qs
    #   else :
    #       return qs.filter(subdomain=settings.SUBDOMAIN)

    model = OpenTASite
    list_display = ["id", "subdomain", "course_key", "db_label", "last_activity", "creator", "data"]
    readonly_fields = ("id", "subdomain", "db_name", "db_label", "last_activity", "creator")
    form = OpenTASiteAdminForm


# def getfirstOpenTASite() :
#    logger.debug("GET FIRRST OPENTA SITE")
#    logger.debug("SUBDOMAIN = ", settings.SUBDOMAIN)
#    obj, created = OpenTASite.objects.get_or_create(subdomain=settings.SUBDOMAIN)
#    return obj.id


admin.site.register(OpenTASite, OpenTASiteAdmin)
