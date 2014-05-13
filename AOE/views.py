# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render_to_response, redirect
from example.elearn.models import Topic, Question, Response, QuestionUser
from example.elearn.forms import ResponseForm
import datetime
from django.views.decorators.csrf import csrf_protect
from django.core.context_processors import csrf
from django.template import Template
from django.template.context import Context, RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate
from django.contrib import auth, messages
from django import contrib
from example import settings
import django
import random
import StringIO

class List:
    template = Template("""
    <{{listtype}} class="{{cls}}">
    {% for obj in object_list %}
      <li class='{{li}}'> <a href={{obj.get_absolute_url}}>{{obj}}</a></li>
    {% endfor %}
    </{{listtype}}>
    """)

def loginview(template=None):
    def deco(f):
        def view(request, template=template, **args):
            context = f(request, **args)
            if template is None:
                template = f.__name__
            return render_to_response('%s.html'%template, context,
                                      context_instance=RequestContext(request))    
        return view
    return deco

def render_list(title, object_list, listtype='ul',cls='generalList', li='item'):
    d = {'object_list':object_list,'listtype':listtype, 'li':li, 'title':title, 'cls':cls}
    s = List.template.render(Context(d))
    print s
    return s

def dummy(request, **args):
    #args.update({'messages':settings.s})
    return render_to_response('dummy.html', {'request':request, 'args':args})

    #args.update({'messages':settings.s})
    
    #return HttpResponse()#render_to_response('taconite.html', {'request':request, 'args':args})

#@login_required
#def user_profile(request, **args):
#    return render_to_response('user_profile.html', {'request':request, 'args': args}, 
#                              context_instance=RequestContext(request))

@login_required
def topiclist(request):    
    ctx = {
        'version': version,
        'last_login': request.session.get('social_auth_last_login_backend')
    }
    obj = Topic
    topic = 'Topics'
    title = 'Topics'
    objlist = obj.objects.all()
    if user_only:
        objlist.filter(user=request.user)
    if title is None:
        title = u'%ss' % (obj.__name__.title(),)
    return render_to_response('list.html', ctx, RequestContext(request))
    
    #return showlist(Topic, title='Topics', ctx=ctx)

@loginview()
def user_profile(request, **args):
    return {'request':request, 'args':args, 'lol':'This is lol.'}

@login_required
def topic(request, slug):
    topic = Topic.objects.get(slug=slug)
    questions = topic.question_set.order_by('qid').all()
    return render_to_response('show_topic.html', {'topic':topic, 'object_list':questions})

def isAnswered(user, question):
    return question.response_set.filter(user=user).count() != 0

@login_required
def summary(request, slug):
    topic = Topic.objects.get(slug=slug)
    #find all that are correct
    
    questions = QuestionUser.objects.filter(question__topic=topic, user=request.user).order_by('question__qid')
    ncorrect = questions.filter(score=1).count()
    return render_to_response('summary.html', {'nquestions':questions.count(), 'ncorrect':ncorrect, 'list':render_list('Summary of %s'%topic, questions)})
    #responses = Response.objects.filter(question__topic=topic, user=request.user, score=1)
    #correct_questions = responses.only('question_id').distinct()
    #incorrect_questions = topic.question_set

@csrf_protect
@login_required
def question(request, slug, qid):
    correct = False
    question = Question.objects.get(qid=qid, topic__slug=slug)
    if request.method == 'POST':
        form = ResponseForm(request.POST)
                
        print 'POST:', request.POST
        correct, message = question.check(request.POST['response'])
        
        question_user, created = QuestionUser.objects.get_or_create(
                        user=request.user, question=question)
        response = Response(response=request.POST['response'],
                    score=int(correct), question_user=question_user)
        question_user.score = max(question_user.score, int(correct))
        question_user.save()
        response.save()
        status = 'Correct' if correct else 'Error'
    else:
        form = ResponseForm()
        status = 'Not answered'
        message = ''
    nquestions = Question.objects.filter(topic=question.topic).count()
    print nquestions, int(qid)
    if nquestions > int(qid):
        button = {'blink':u'%s%s' % (question.topic.get_absolute_url(),int(qid)+1),
                  'blabel':u'Next'}
    else:
        button = {'blink':u'%s' % reverse('summary', kwargs={'slug':question.topic.slug}),
                  'blabel':u'Done'}
    d = {'nquestions':nquestions, 'id':question.qid, 'question':question, 'status':status, 'form':form, 'message':message}    
    d.update(csrf(request))
    d.update(button)
    return render_to_response('show_question.html', d)

def logout(request, **args):
    auth.logout(request)
    messages.success(request, 'Sucessfully logged out!')
    return HttpResponseRedirect(reverse('login'))

def history(request):
    responses = Response.objects.filter(question_user__user=request.user).select_related()
    header = ['date', 'user', 'topic', 'question', 'result']
    def tabify(obj):
        return unicode(''.join(['<td>%s</td>'%i for i in obj]))
    object_list = [tabify([response.date, response.question_user.user, response.question_user.question.topic, 
                    response.question_user.question, 'CORRECT' if response.score else 'UNSOLVED']) 
                   for response in responses]
    header = tabify(i.title() for i in header)
    #raise Exception('lol')
    return render_to_response('history.html', {'object_list':object_list, 'table_header':header})

def graphs(request):
    responses = Response.objects.filter(question_user__user=request.user).select_related()
    header = ['date', 'user', 'topic', 'question', 'result']
    def tabify(obj):
        return unicode(''.join(['<td>%s</td>'%i for i in obj]))
    object_list = [tabify([response.date, response.question_user.user, response.question_user.question.topic, 
                    response.question_user.question, 'CORRECT' if response.score else 'UNSOLVED']) 
                   for response in responses]
    header = tabify(i.title() for i in header)
    #raise Exception('lol')
    return render_to_response('graphs.html', {'object_list':object_list, 'table_header':header})

def main(request):
    return HttpResponseRedirect(reverse('login'))

@csrf_protect
@never_cache
def login(request, authentication_form=AuthenticationForm):
    """Displays the login form and handles the login action."""
    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if request.POST['b1'] == 'create':
            return HttpResponseRedirect(reverse('elearn_create_from_login'))
        elif request.POST['b1'] == 'login':
            if form.is_valid():
                error = str(form.clean())
                auth.login(request, form.get_user())
                print 'login sucess'
                print 'is auth', form.get_user().is_authenticated()
                
                return HttpResponseRedirect(reverse('user_profile'))
            else:
                error = 'not valid'
#                username = request.POST['username']
#                password = request.POST['password']
#                user = authenticate(username=username, password=password)
#                if user is not None:
#                    if user.is_active:
#                        auth.login(request, user)
#                        return HttpResponseRedirect(reverse('user_profile'))
#                    else:
#                        error = 'That account has been disabled.'
#                else:
#                    error = 'That username does not exist in the database.'
#                    # Return an 'invalid login' error message.
#            else:
#                error = 'The form data is invalid.'
    else:
        form = authentication_form(request)
        error = ''
    return render_with_csrf(request, 'login.html', {'title':'login', 'form':form, 'error':error})
    
#    request.session.set_test_cookie()
#    
#    if Site._meta.installed:
#        current_site = Site.objects.get_current()
#    else:
#        current_site = RequestSite(request)
#    
#    return render_to_response(template_name, {
#        'form': form,
#        redirect_field_name: redirect_to,
#        'site': current_site,
#        'site_name': current_site.name,
#    }, context_instance=RequestContext(request))

def render_with_csrf(request, htmlfile, context):
    context.update(csrf(request))   
    return render_to_response(htmlfile, context, context_instance=RequestContext(request))

@csrf_protect
def create(request, redirected=False):
    print 'Redirected is ', redirected
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if not redirected:
            if form.is_valid():
                form.save()
                messages.success(request, 'You are now registered!')
                return HttpResponseRedirect(reverse('user_profile'))
            else:
                pass
    else:
        form = UserCreationForm()
    return render_with_csrf(request, 'create.html', {'title':'Create', 'form':form})

#def form_view(Form):
#    def deco(f):
#        @csrf_protect
#        def wrapper(request):
#            if request.method == 'POST':
#                form = Form(request.POST)
#                if form.is_valid():
#                    form.save()
#            else:
#                form = Form()
#                return render_to_response('base_form.html', {'title':f.func_name, 'form':form})
#        return wrapper
#    return deco

def showlist(request, obj=None, user_only=False, title=None):
    assert obj is not None
    objlist = obj.objects.all()
    if user_only:
        objlist.filter(user=request.user)
    if title is None:
        title = u'%ss' % (obj.__name__.title(),)
    return render_to_response('list.html', {'topic':topic, 'object_list':objlist, 'title':title})

def test(request, **args):
    return render_to_response('test.html', {'request':request, 'args':args})