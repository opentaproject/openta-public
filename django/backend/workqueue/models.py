from django.db import models
from django.contrib.auth.models import User
import redis
from django.db.models.signals import post_delete, pre_save
from django.dispatch.dispatcher import receiver





def result_file_name(instance, filename):
    fullfile = '/'.join(
        [
            'taskresults',
            str(instance.pk)
            + "_"
            + "{:%Y%m%d_%H:%M}".format(instance.date)
            + "_"
            + instance.name.replace(' ', '_')
            + filename,
        ]
    )
    return fullfile



class QueueTask(models.Model):
    owner = models.ForeignKey(User, default=None, null=True, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    progress = models.PositiveIntegerField(default=0)
    done = models.BooleanField(default=False)
    status = models.CharField(max_length=255, default="Created")
    result_file = models.FileField(
        default=None, blank=True, null=True, upload_to=result_file_name, max_length=512
    )

    def save(self,*args,**kwargs):
        r  = redis.Redis()
        r.set(str(self.id),'1')
        super(QueueTask, self).save(*args, **kwargs)


@receiver(pre_save, sender=QueueTask)
def _queuetask_save(sender, instance, **kwargs):
    r  = redis.Redis()
    r.set(str(instance.id),'1')


@receiver(post_delete, sender=QueueTask)
def _queuetask_delete(sender, instance, **kwargs):
    print("deleting", instance.id)
    r  = redis.Redis()
    r.delete(str(instance.id))
    
    # TODO THIS SHOULD PROBABLY BE DONE WITH redis.pubsub
    #
