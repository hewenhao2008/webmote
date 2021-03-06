from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from webmote_django.webmote.models import *

@login_required
def bookmarkActions(request):
    context = {}
    context['devices'] = []
    for device in Devices.objects.all():
        device.actions = device.actions_set.all()
        context['devices'].append(device)
    actions = []
    for action in Actions.objects.filter(device=None):
        actualAction = action.getSubclassInstance()
        if hasattr(actualAction, 'visible'):
            if actualAction.visible:
                actions.append(action.id)
        else:
            actions.append(action.id)
    context['actions'] = Actions.objects.filter(id__in=actions)
    return render_to_response('bookmark_actions.html', context, context_instance=RequestContext(request))

@login_required
def bookmark(request, actionID):
    context = {}
    action = Actions.objects.filter(id=int(actionID))[0]
    action.runAction()
    context['name'] = action.name
    return render_to_response('bookmark.html', context, context_instance=RequestContext(request))
