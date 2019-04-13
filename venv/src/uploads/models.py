from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0}/{1}'.format(instance.owner, filename)


# Create your models here.
class Document(models.Model):
    description = models.CharField(max_length=255, blank=False)
    document = models.ImageField(upload_to=user_directory_path,null=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    profile_user = models.ForeignKey(User,on_delete=models.CASCADE)
    def keep_owner(self,owner):
        self.owner = owner

@receiver(post_delete, sender=Document)
def photo_post_delete_handler(sender, **kwargs):
    listingImage = kwargs['instance']
    storage, path = listingImage.document.storage, listingImage.document.path
    storage.delete(path)
# class MyModel(models.Model):
#     upload = models.FileField(upload_to=user_directory_path)
