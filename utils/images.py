"""Project storage control for image"""
import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage


def upload_to(instance, filename):
    extension = filename.split(".")[1]
    if filename == "images/users/default.png":
        return filename
    return f"images/users/{instance.id.hex}.{extension}"


class OverwriteImage(FileSystemStorage):
    def get_available_name(self, name, max_length=100):
        """Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        Found at http://djangosnippets.org/snippets/976/
        This file storage solves overwrite on upload problem. Another
        proposed solution was to override the save method on the model
        like so (from https://code.djangoproject.com/ticket/11663):
        def save(self, *args, **kwargs):
            try:
                this = MyModelName.objects.get(id=self.id)
                if this.MyImageFieldName != self.MyImageFieldName:
                    this.MyImageFieldName.delete()
            except: pass
            super(MyModelName, self).save(*args, **kwargs)
        """
        # If the filename already exists,
        # remove it as if it was a true file system
        if self.exists(name.split(".")[0] + ".jpg"):
            os.remove(os.path.join(settings.MEDIA_ROOT, name.split(".")[0] + ".jpg"))
        elif self.exists(name.split(".")[0] + ".jpeg"):
            os.remove(os.path.join(settings.MEDIA_ROOT, name.split(".")[0] + ".jpeg"))
        elif self.exists(name.split(".")[0] + ".png"):
            os.remove(os.path.join(settings.MEDIA_ROOT, name.split(".")[0] + ".png"))
        return name
