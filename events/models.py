from django.db import models

# Create your models here.
class Blog(models.Model):
    name = models.CharField(max_length=20)
    tagline = models.TextField()

    class Meta:
        db_table = "blogs"

    def __str__(self):
        return self.name

class Author(models.Model):
    name = models.CharField(max_length=25)
    email = models.EmailField()

    class Meta:
        db_table = "authors"

    def __str__(self):
        return self.name

class Entry(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    headline = models.CharField(max_length=35)
    body_text = models.TextField()
    pub_date = models.DateField()
    mod_date = models.DateField()
    authors = models.ManyToManyField(Author)
    number_of_comments = models.IntegerField()
    number_of_pingbacks = models.IntegerField()
    rating = models.IntegerField()

    def __str__(self):
        return self.headline
