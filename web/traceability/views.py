from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import View, TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from .models import *
from django.http import Http404
from traceability import utils

# Create your views here.
class Index(TemplateView):
    template_name = 'traceability/index.html'

class ActiveKeysList(ListView):
    model = Key
    template_name = 'traceability/keys/keyslist_active.html'
    queryset = Key.objects.filter(current_status = 'active')
    context_object_name = 'keys_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['remote_register'] = utils.get_register_status()
        return context

class PendingKeysList(ListView):
    model = Key
    template_name = 'traceability/keys/keyslist_pending.html'
    queryset = Key.objects.filter(current_status = 'new')
    context_object_name = 'keys_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['remote_register'] = utils.get_register_status()
        return context

class InactiveKeysList(ListView):
    model = Key
    template_name = 'traceability/keys/keyslist_inactive.html'
    queryset = Key.objects.filter(current_status = 'inactive')
    context_object_name = 'keys_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['remote_register'] = utils.get_register_status()
        return context

class KeyDetails(DetailView):
    model = Key
    template_name = 'traceability/keys/key_details.html'
    slug_url_kwarg = 'hash'
    slug_field = 'hash'
    context_object_name = 'key'
    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            return redirect('keys')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

def ActivateKey(request, hash):
    try:
        k = Key.objects.get(hash = hash)
        k.current_status = 'active'
        k.save()
        messages.add_message(request, messages.SUCCESS, "La clave '" + k.name + "' se ha activado correctamente.")
    except ObjectDoesNotExist:
        messages.add_message(request, messages.ERROR, "No se ha encontrado la clave.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def DeactivateKey(request, hash):
    try:
        k = Key.objects.get(hash = hash)
        k.current_status = 'inactive'
        k.save()
        messages.add_message(request, messages.SUCCESS, "La clave '" + k.name + "' se ha desactivado correctamente.")
    except ObjectDoesNotExist:
        messages.add_message(request, messages.ERROR, "No se ha encontrado la clave.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def RemoveKey(request, hash):
    try:
        k = Key.objects.get(hash = hash)
        if k.current_status != 'new':
            messages.add_message(request, messages.ERROR, "No se pueden eliminar claves que ya han sido activadas.")
        else:
            k.delete()
            messages.add_message(request, messages.SUCCESS, "La clave '" + k.name + "' se ha eliminado correctamente.")
    except ObjectDoesNotExist:
        messages.add_message(request, messages.ERROR, "No se ha encontrado la clave.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

class NewKey(CreateView):
    model = Key
    fields = ['name', 'public_key', 'current_status', 'description']
    template_name = "traceability/keys/key_form.html"
    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Se ha registrado la nueva clave.")
        return super().form_valid(form)

class ModifyKey(UpdateView):
    model = Key
    fields = ['name', 'description']
    template_name = "traceability/keys/key_form.html"
    slug_url_kwarg = 'hash'
    slug_field = 'hash'
    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Se ha actualizado la información.")
        return super().form_valid(form)

def KeySearch(request):
    searchbox = request.GET.get('sb')
    if searchbox:
        if Key.objects.filter(hash = searchbox).exists():
            url = reverse('key_details', kwargs={'hash': searchbox})
        else:
            k = Key.objects.filter(name = searchbox)
            if k.exists():
                url = reverse('key_details', kwargs={'hash': k[0].hash})
            else:
                messages.add_message(request, messages.ERROR, "No se ha encontrado la clave.")
                url = reverse('keys')
    else:
        url = reverse('keys')
    return HttpResponseRedirect(url)

class TransactionsList(ListView):
    model = Transaction
    template_name = 'traceability/transactions/transactions_list.html'
    context_object_name = 'transactions_list'
    paginate_by = 10

    def get_queryset(self):
        q = super().get_queryset()
        return q

class TransactionDetail(DetailView):
    model = Transaction
    template_name = 'traceability/transactions/transaction_details.html'
    context_object_name = 't'
    slug_url_kwarg = 'hash'
    slug_field = 'hash'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context[self.context_object_name]:
            obj = context[self.context_object_name]
            context['sign'] = obj.verify_sign()
            if 'new_id' in obj.transaction_data: newid = obj.transaction_data['new_id']
            else: newid = None
            if 'product' in obj.transaction_data:
                context['product'] = self.make_product_list(obj.transaction_data['product'], newid)
                self.set_quantity(context['product'], obj.updated_quantity)
                self.set_pre_transactions(context['product'], obj.hash)
                self.set_post_transactions(context['product'], obj.hash)
            else:
                context['product_in'] = self.make_product_list(obj.transaction_data['product_in'])
                context['product_out'] = self.make_product_list(obj.transaction_data['product_out'], newid)
                self.set_quantity(context['product_in'], obj.updated_quantity)
                self.set_pre_transactions(context['product_in'], obj.hash)
                self.set_post_transactions(context['product_out'], obj.hash)

        return context

    def make_product_list(self, p_list, newid = None):
        l = []
        for p in p_list:
            l.append({})
            l[-1]['product'] = p[0]
            if newid:
                l[-1]['newid'] = newid
            elif isinstance(p[1], str):
                l[-1]['id'] = p[1]
            else:
                l[-1]['quantity'] = p[1]
        return l

    def set_quantity(self, p_list, updated_quantity):
        for p in p_list:
            if 'quantity' in p and p['quantity'] == None:
                p['quantity'] = updated_quantity[p['product']]

    def set_pre_transactions(self, p_list, hash):
        for p in p_list:
            in_list = list(TransactionInput.objects.filter(t_hash = hash, product = p['product']).values_list('input', flat=True))
            p['pre'] = in_list

    def set_post_transactions(self, p_list, hash):
        for p in p_list:
            out_list = list(TransactionInput.objects.filter(input = hash, product = p['product']).values_list('t_hash', flat=True))
            p['post'] = out_list

def ChangeRemoteRegisterStatus(request, value):
    if value == 'on' or value == 'off':
        utils.set_register_status(value)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))