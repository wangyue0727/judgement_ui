from django.template import Context, loader, RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from assess.models import *
from collections import defaultdict
import datetime
import base64
import json

def assessor_logout(request) :
  '''
  Log users out and re-direct them to the main page.
  '''
  logout(request)

  '''
  Return to the previous page if possible.
  Thanks to:
  http://stackoverflow.com/questions/8327078/
  '''
  if 'HTTP_REFERER' in request.META :
    return HttpResponseRedirect(request.META['HTTP_REFERER'])
  else :
    return HttpResponseRedirect(reverse('assess.views.home'))

@login_required
def home(request) :
  try :
    assessor = Assessor.objects.get(user=request.user)
  except Assessor.DoesNotExist :
    return render_to_response('error.html', {
      'error_message': "You are not a valid assessor.",
    })

  if assessor.user.is_staff :
    assessor_list = Assessor.objects.all()
    return render_to_response('staff_home.html', {
      'staff': assessor, 'assessor_list': assessor_list
    })
  else:
    return render_to_response('assessor_home.html', {'assessor': assessor})

def start(request) :
  return render_to_response('start.html')
  
@login_required
def query(request, query_id) :
  try :
    assessor = Assessor.objects.get(user=request.user)
  except Assessor.DoesNotExist :
    return render_to_response('error.html', {
      'error_message': "You are not a valid assessor.",
    })

  try :
    query = Query.objects.get(pk=query_id)
  except Query.DoesNotExist :
    return render_to_response('error.html', {
      'error_message': "Invalid query.",
      'assessor': assessor,
    })

  if query.assessor != assessor :
    if False == assessor.user.is_staff :
      return render_to_response('error.html', {
        'error_message': "You do not have access to the query.",
        'assessor': assessor,
    })

  total_count = get_count(query,"total")
  done_count = get_count(query,"done")
  left_count = get_count(query,"left")

  return render_to_response('query.html', {
    'assessor': assessor, 'query': query, 'done': done_count,
    'left': left_count}, context_instance=RequestContext(request))

def get_count(query, count_type):
  d =dict()
  count=0
  if count_type == "total":
    for e in Assessment.objects.filter(query=query):
      if e.document.doc_id in d:
        continue
      else:
        count+=1
        d[e.document.doc_id]=1     
    return count
  elif count_type == "done":
    for e in Assessment.objects.filter(query=query,has_assessed=True):
      if e.document.doc_id in d:
        continue
      else:
        count+=1
        d[e.document.doc_id]=1     
    return count
  elif count_type == "left":
    for e in Assessment.objects.filter(query=query,has_assessed=False):
      if e.document.doc_id in d:
        continue
      else:
        count+=1
        d[e.document.doc_id]=1     
    return count


@login_required
def assessment(request, assessment_id) :
  try :
    assessor = Assessor.objects.get(user=request.user)
  except Assessor.DoesNotExist :
    return render_to_response('error.html', {
      'error_message': "You are not a valid assessor.",
    })

  try :
    assessment = Assessment.objects.get(pk=assessment_id)
  except Assessment.DoesNotExist :
    return render_to_response('error.html', {
      'error_message': "Invalid assessment.",
      'assessor': assessor,
    })

  try :
    query = Query.objects.get(pk=assessment.query.pk)
  except Query.DoesNotExist :
    return render_to_response('error.html', {
      'error_message': "Invalid query in assessment.",
      'assessor': assessor,
    })

  if query.assessor != assessor :
    if False == assessor.user.is_staff :
      return render_to_response('error.html', {
        'error_message': "You do not have access to the query.",
        'assessor': assessor,
    })

  return_list=[]
  term_list = []
  assessment_all = []
  try :
    docs = Document.objects.filter(doc_id=assessment.document.doc_id)
    for document in docs:
      if assessor.user.is_staff:
        assessment = Assessment.objects.get(document=document.pk,assessor=assessment.assessor_id)
        assessment.aspect=assessment.aspect.replace(" ", "")
      else:
        assessment = Assessment.objects.get(document=document.pk,assessor=assessor.pk)
        assessment.aspect=assessment.aspect.replace(" ", "")
      assessment_all.append(assessment)
    category = Categories.objects.filter(category=assessment.document.category).order_by('pk')
  except Document.DoesNotExist :
    raise Http404
  return render_to_response('assessment.html', {
    'assessor': assessor, 'query': query, 'sentences': assessment_all, 'assessment': assessment, 'category' : category},
    context_instance=RequestContext(request))
  # return render_to_response('assessment.html', {
  #   'assessor': assessor, 'query': query, 'assessment': assessment},
  #   context_instance=RequestContext(request))

@login_required
def raw(request, doc_id) :
  return_list=[];
  try :
    docs = Document.objects.filter(doc_id=doc_id).values('data')
  except Document.DoesNotExist :
    raise Http404
  for doc in docs:
    doc = base64.b64decode(doc.get('data'))
    return_list.append(doc);


  '''
  check whether the document is in plain text or not, and render using
  different templates
  '''
  t = loader.get_template('raw.html')
  c = RequestContext(request, {'sentences': return_list})
  return HttpResponse(t.render(c))

def error_json_response(msg) :
  item = dict()
  item['error_msg'] = msg
  return HttpResponse(json.dumps(item), status=404,
    content_type='application/json')

@login_required
def label(request, assessment_id) :
  # route GET request to the assessment page
  if "POST" != request.method :
    return HttpResponseRedirect(reverse('assess.views.assessment',
      args=[assessment_id]))
  
  # disable the assessment
  # msg = 'Assessment closed.'
  # return error_json_response(msg)
  
  try :
    assessment = Assessment.objects.get(pk=assessment_id)
  except Assessment.DoesNotExist :
    msg = 'Invalid assessment!'
    return error_json_response(msg)

  try :
    query = Query.objects.get(pk=assessment.query.pk)
  except Query.DoesNotExist :
    msg = 'Invalid query in assessment!'
    return error_json_response(msg)

  try :
    assessor = Assessor.objects.get(user=request.user)
  except Assessor.DoesNotExist :
    msg = 'You are not a valid assessor!'
    return error_json_response(msg)

  if query.assessor != assessor :
    if False == assessor.user.is_staff :
      msg = 'You do not have access to the query!'
      return error_json_response(msg)

  # post_content = base64.b64decode(request.POST.['keywords'])
  posted_content = request.POST.dict()

  docs = Document.objects.filter(doc_id=assessment.document.doc_id)

  for doc in docs:
    try:
      target = Assessment.objects.get(document_id=doc.pk,query_id=assessment.query.pk)  
      target.has_assessed = True 
      rel_index=doc.sentence_id+"-relevance"
      asp_index="aspect-"+doc.sentence_id
      key_index="keywords-"+doc.sentence_id
      if 'yes' == posted_content[rel_index] :
        target.relevance = 1
        target.aspect=posted_content[asp_index]
        if target.aspect == "other":
          target.keywords = posted_content[key_index]
        else:
          target.keywords = "None"
      elif 'no' == posted_content[rel_index] :
        target.relevance = 0
        target.aspect="None"
        target.keywords = "None"
      else :
        msg = 'Unknown sentence level judgement!'
        return error_json_response(msg)
      if 'yes' == posted_content['overall-relevance'] :
        target.doc_bug = 1
      elif 'no' == posted_content['overall-relevance'] :
        target.doc_bug = 0
      else :
        msg = 'Unknown document level judgement!'
        return error_json_response(msg)
      target.assessed_by = assessor.user.username  
      now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      target.last_modified = now 
      target.save()
    except Assessment.DoesNotExist :
      msg = 'Internal Error: Cannot find the assessment!'
      return error_json_response(msg) 

  response = {'info': 'Assessment updated.',
    'redirect': reverse('assess.views.query', args=[query.pk])
    + '#' + assessment_id}
  return HttpResponse(json.dumps(response), content_type="application/json")

# show the summary of evaluation results
@login_required
def eval_summary(request) :
  try :
    assessor = Assessor.objects.get(user=request.user)
  except Assessor.DoesNotExist :
    return render_to_response('error.html', {
      'error_message': "You are not a valid assessor.",
    })

  avg_eval_list = AvgEvalItem.objects.all()
  
  return render_to_response('eval_summary.html', {
    'assessor': assessor, 'avg_eval_list': avg_eval_list})


# show the evaluation results of one retrieval function
@login_required
def eval_rf(request, rf_id) :
  try :
    assessor = Assessor.objects.get(user=request.user)
  except Assessor.DoesNotExist :
    return render_to_response('error.html', {
      'error_message': "You are not a valid assessor.",
    })

  try :
    ret_func = RetrievalFunction.objects.get(pk=rf_id)
  except Assessment.DoesNotExist :
    return render_to_response('error.html', {
      'error_message': "Invalid retrieval function.",
      'assessor': assessor,
    })

  if ret_func.user != assessor.user :
    if False == assessor.user.is_staff :
      return render_to_response('error.html', {
        'error_message': "You do not have access to the retrieval function.",
        'assessor': assessor,
    })

  eval_list = EvalItem.objects.filter(rf=ret_func)
  
  return render_to_response('eval_rf.html', {
    'assessor': assessor, 'ret_func': ret_func, 'eval_list': eval_list})
