from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=100)
    image1 = models.ImageField(upload_to='students/')
    image2 = models.ImageField(upload_to='students/')
    image3 = models.ImageField(upload_to='students/')
    image4 = models.ImageField(upload_to='students/')
    face_encoding = models.BinaryField()  # To store the combined face encoding

    def __str__(self):
        return self.name