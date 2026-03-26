from django.core.files.storage import FileSystemStorage


class CustomFileSystemStorage(FileSystemStorage):
    """Custom file system storage for uploaded files"""
    def get_available_name(self, name, max_length=None):
        """
        Return a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        # If the filename already exists, remove it as if it was a true file system
        if self.exists(name):
            self.delete(name)
        return super().get_available_name(name, max_length)