from django import template
from assess.models import *

register = template.Library()

@register.filter(name='done_count')
def done_count(value) :
  d = dict()
  count=0
  for e in Assessment.objects.filter(query=value, has_assessed=True):
    if e.document.doc_id in d:
      continue
    else:
      count+=1
      d[e.document.doc_id]=1

  return count

@register.filter(name='left_count')
def left_count(value) :
  d = dict()
  count=0
  for e in Assessment.objects.filter(query=value, has_assessed=False):
    if e.document.doc_id in d:
      continue
    else:
      count+=1
      d[e.document.doc_id]=1
  return count

@register.filter(name='total_count')
def total_count(value) :
  d = dict()
  count=0
  for e in Assessment.objects.filter(query=value):
    if e.document.doc_id in d:
      continue
    else:
      count+=1
      d[e.document.doc_id]=1
  return count

@register.filter(name='all_done')
def all_done(value) :
  done_count = Assessment.objects.filter(query=value,has_assessed=True).count()
  all_count = Assessment.objects.filter(query=value).count()
  return done_count == all_count