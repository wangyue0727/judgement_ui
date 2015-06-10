import base64
from django import template
from assess.models import *

register = template.Library()

@register.filter(name='b64_decode')
def b64_decode(data) :
  missing_padding = 4 - len(data) % 4
  if missing_padding:
    data += b'='* missing_padding
	# return base64.decodestring(data)
  return base64.b64decode(data)

@register.filter(name='short_snippet')
def short_snippet(data) :
  if len(data) > 60 :
    return '%s ...' % data[0:60]
  else :
    if ' ' == data :
      data = 'N/A'
    return data

@register.filter(name='unique')
def unique(data) :
  d =dict()
  unique_list=[];
  for e in data:
    if e.document.doc_id in d:
      continue
    else:
      unique_list.append(e)
      d[e.document.doc_id]=1
  return unique_list

@register.filter(name='get_title')
def get_title(docid) :
  return Document.objects.filter(doc_id=docid,sentence_id='t').values('data')[0].get('data')