from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.http import HttpResponse
from django.utils import simplejson
from IR.models import *
import urllib2
from bs4 import BeautifulSoup

LIRC = 'http://lirc.sourceforge.net/remotes/'

@login_required
def main(request):
    context = {}
    context['transceivers'] = Transceivers.objects.filter(type='IR')
    context['devices'] = IR_Devices.objects.all()
    return render_to_response('ir.html', context, context_instance=RequestContext(request))

@login_required
def help(request):
    context = {}
    return render_to_response('ir_help.html', context, context_instance=RequestContext(request))

@login_required
def transceivers(request):
    context = {}
    context['type'] = 'IR'
    if request.method == 'POST':
        if 'addTransceiver' in request.POST:
            newTForm = TransceiversForm(request.POST)
            if newTForm.is_valid():
                newTran = newTForm.save()
                newTran.assignID()
            else:
                context['error'] = "Transciever was invalid."
        elif 'deleteTransceiver' in request.POST:
            Transceivers.objects.filter(id=request.POST['deleteTransceiver'])[0].delete()
        elif 'resetTransceivers' in request.POST:
            resetAllTransceivers()
    context['transceivers'] = Transceivers.objects.filter(type=context['type'])
    context['transceiversForm'] = TransceiversForm()
    return render_to_response('transceivers.html', context, context_instance=RequestContext(request))

@login_required
def devices(request):
    context = {}
    if request.method == 'POST':
        if 'addDevice' in request.POST:
            newDeviceForm = IR_DevicesForm(request.POST)
            if newDeviceForm.is_valid():
                newDeviceForm.save()
            else:
                context['error'] = "Device was invalid."
        elif 'deleteDevice' in request.POST:
            IR_Devices.objects.filter(id=request.POST['deleteDevice'])[0].delete()
    context['devices'] = IR_Devices.objects.select_related().all()
    context['deviceForm'] = IR_DevicesForm()
    return render_to_response('devices.html', context, context_instance=RequestContext(request))

@login_required
def actions(request):
    return render_to_response('actions.html', context, context_instance=RequestContext(request))

@login_required
def device(request, num="1"):
    context = {}
    device = Devices.objects.filter(id=int(num))[0]
    deviceForm = IR_DevicesForm()
    actionForm = IR_ActionsForm()
    if request.method == 'POST':
        if 'updateDevice' in request.POST:
            updatedDevice = deviceForm(request.POST, instance=device.getSubclassInstance())
            if updatedDevice.is_valid():
                updatedDevice.save()
            else:
                context['error'] = "New value(s) was invalid."
        elif 'addAction' in request.POST:
            actionType = device.getCorrespondingCommandType()
            action = actionType(device=device)
            newAction = actionForm(request.POST, instance=action)
            if newAction.is_valid():
                newAction.save()
            else:
                context['error'] = "Action was invalid."
        elif 'deleteAction' in request.POST:
            IR_Actions.objects.filter(id=request.POST['deleteAction']).delete()
    device = Devices.objects.filter(id=int(num))[0]
    context['device'] = device
    context['deviceForm'] = IR_DevicesForm(instance=device.getSubclassInstance())
    context['actions'] = device.actions_set.all()
    context['actionForm'] = actionForm
    return render_to_response('device.html', context, context_instance=RequestContext(request))


#@login_required
#def runActionView(request, deviceNum="1", action="0"):
#    # should be a permissions check here if it isn't already in the runcommand...
#    context = runAction(deviceNum, action)
#    return render_to_response('index.html', context, context_instance=RequestContext(request))


@login_required
def recordAction(request):
    if request.method == 'POST':
        newActionInfo = simplejson.loads(request.raw_post_data)
        device = Devices.objects.filter(id=int(newActionInfo[0]))[0]
        action = IR_Actions(device=device, name=newActionInfo[1])
        if action.recordAction():
            action.save()
        print 'returned'
    return HttpResponse(simplejson.dumps(''), mimetype='application/javascript')

@login_required
def searchLIRC(request, deviceID):
    device = Devices.objects.filter(id=int(deviceID))[0]
    brand = device.getSubclassInstance().brand.lower()
    deviceModelNumber = device.getSubclassInstance().deviceModelNumber.lower()
    remoteModelNumber = device.getSubclassInstance().remoteModelNumber.lower()
    deviceActions = device.actions_set.all()
    
    response = urllib2.urlopen(LIRC).read()
    soup = BeautifulSoup(response)
    brands = soup.table.findAll('a')
    matches = []

    for b in brands:
        # This could maybe benefit from fuzzy matching
        if brand in b.text.lower():
            brandURL = LIRC + b.text
            print 'Found brand match at ' + brandURL
            response = urllib2.urlopen(brandURL).read()
            soup = BeautifulSoup(response)
            remotes = soup.table.findAll('a')
            foundRemote = False
            for r in remotes:
                if len(deviceModelNumber) and deviceModelNumber.lower() in r.text.lower():
                    print 'found device model number: ' + r.text.lower() + deviceModelNumber
                    foundRemote = True
                    break
                if len(remoteModelNumber) and remoteModelNumber.lower() in r.text.lower():
                    print 'found remote model number: ' + r.text.lower() + remoteModelNumber
                    foundRemote = True
                    break

            if not foundRemote:
                for r in remotes:
                    remoteURL = LIRC + b.text + r.text
                    try:
                        response = urllib2.urlopen(remoteURL).read()
                        matchCount = 0
                        for action in deviceActions:
                            readCodes = False
                            recordedCodeData = action.getSubclassInstance().code[8:].replace('\n', '')
                            for line in response.splitlines():
                                if 'end codes' in line:
                                    readCodes = False

                                if readCodes:
                                    name, code = line.split()
                                    if recordedCodeData.lower() in code.lower():
                                        matchCount += 1
                                        break

                                if 'begin codes' in line:
                                    readCodes = True
                        if len(deviceActions) == matchCount and len(deviceActions):
                            matches.append(remoteURL)
                        print remoteURL
                    except:
                        print 'invalid url'
    return HttpResponse(simplejson.dumps(matches), mimetype='application/javascript')

@login_required
def addFromLIRC(request, deviceID):
    context = {}
    if request.method == 'POST':
        remoteURL = simplejson.loads(request.raw_post_data)
        device = Devices.objects.filter(id=int(deviceID))[0]

        # Get the code type and length from previously recorded commands
        code = device.actions_set.all()[0].getSubclassInstance().code
        codeType =  code[:4]
        codeLen = code[4:8]

        response = urllib2.urlopen(remoteURL).read()
        readCodes = False
        try:
            for line in response.splitlines():
                if 'end codes' in line:
                    readCodes = False

                if readCodes:
                    name, code = line.split()
                    code = codeType + codeLen + code[2:]
                    action = IR_Actions(name=name, code=code, device=device)
                    action.save()

                if 'begin codes' in line:
                    readCodes = True
        except:
            print 'failed to add actions'
    return HttpResponse(simplejson.dumps(''), mimetype='application/javascript')

@login_required
def exportIR(request):
    return HttpResponse(simplejson.dumps(''), mimetype='application/javascript')
