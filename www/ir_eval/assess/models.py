import datetime
from django.db import models
from django.contrib.auth.models import User

class Assessor(models.Model) :
  user = models.ForeignKey(User)
  name = models.CharField(max_length=100)

  def __unicode__(self) :
    return self.name
    #return self.user.username

class Query(models.Model) :
  qid = models.CharField(max_length=100)
  assessor = models.ForeignKey(Assessor)
  title = models.CharField(max_length=300)
  description = models.TextField()
  # category = models.CharField(max_length=100)

  def __unicode__(self) :
    # return str(self.assessor) + '-' + str(self.index) + " : " + self.title
    return str(self.assessor) + " : " + self.title

class Document(models.Model) :
  doc_id = models.CharField(max_length=100)
  sentence_id = models.CharField(max_length=100)
  # title = models.TextField()
  data = models.TextField()
  category = models.CharField(max_length=100)

  def __unicode__(self) :
    return str(self.pk) + '-' + self.doc_id + '-' + self.sentence_id


class Assessment(models.Model) :
  query = models.ForeignKey(Query)
  document = models.ForeignKey(Document)
  assessor = models.ForeignKey(Assessor)
  has_assessed = models.BooleanField()
  relevance = models.IntegerField()
  aspect = models.CharField(max_length=100)
  keywords = models.TextField()
  doc_bug = models.IntegerField()
  assessed_by = models.CharField(max_length=100)
  last_modified = models.CharField(max_length=100)

  def __unicode__(self) :
    return str(self.pk) + '-' + str(self.query.pk) + '-' \
      + str(self.document.doc_id)
  def get_doc_id(self) :
    return str(self.document.doc_id)

class Categories(models.Model) : 
  category = models.CharField(max_length=100)
  aspect = models.CharField(max_length=100)
  keywords = models.TextField()
  def __unicode__(self) :
    return str(self.aspect) + ' : ' + self.keywords
  def get_aspect(self) :
    return int(self.aspect)
  def get_keywords(self): 
    return str(self.keywords)