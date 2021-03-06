from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField
from django.urls import reverse

from collections import OrderedDict
import json

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

#Modelo clave, representa una clave pública de una etapa de la cadena de producción
class Key(models.Model):
    hash = models.CharField(max_length=64, primary_key=True)
    public_key = models.TextField('Clave Pública', max_length=300)
    status_choices = (('active', 'Activa'), ('inactive', 'Inactiva'), ('new', 'Pendiente de Aprobación'))
    current_status = models.CharField('Estado', max_length=8, choices=status_choices, default='new')
    name = models.CharField('Nombre', max_length=50)
    description = models.TextField('Descripción', max_length=300, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.hash = SHA256.new(self.public_key.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('key_details', kwargs={'hash': self.hash})

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'keys'

#Modelo transacción, representa una transacción registrada en el sistema
class Transaction(models.Model):
    hash = models.CharField(max_length=64, primary_key=True)
    type = models.IntegerField()
    mode = models.IntegerField()
    transmitter = models.ForeignKey(Key, on_delete=models.CASCADE, related_name='transmitter', db_column='transmitter')
    receiver = models.ForeignKey(Key, on_delete=models.CASCADE, related_name='receiver', db_column='receiver', null = True)
    server_timestamp = models.DateTimeField()
    client_timestamp = models.DateTimeField()
    raw_client_timestamp = models.CharField(max_length = 24)
    transaction_data = JSONField()
    sign = models.CharField(max_length=256)
    updated_quantity = JSONField()
    errors = ArrayField(models.CharField(max_length = 64))

    class Meta:
        db_table = 'transactions'
        ordering = ('-client_timestamp',)
    
    def __str__(self):
        return self.hash

    def verify_sign(self):
        ordered_data = OrderedDict(sorted(self.transaction_data.items()))
        transaction = [("type", self.type), ("mode", self.mode), ("transmitter", self.transmitter.hash)]
        if(self.receiver):
            transaction.append(("receiver", self.receiver.hash))
        transaction.extend([("timestamp", self.raw_client_timestamp), ("data", ordered_data)])
        transaction = OrderedDict(transaction)
        serialized_transaction = json.dumps(transaction, separators = (',',':'))
        calculated_hash = SHA256.new(serialized_transaction.encode('utf-8'))

        if self.hash != calculated_hash.hexdigest():
            return False

        keyobject = RSA.importKey(self.transmitter.public_key)
        verifier = PKCS1_v1_5.new(keyobject)
        return verifier.verify(calculated_hash, bytes.fromhex(self.sign))

#Modelo entrada de transacción, representa un enlace entre dos transacciones
class TransactionInput(models.Model):
    t_hash = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='transaction', db_column='t_hash')
    input = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='input', db_column='input')
    product = models.CharField(max_length=64)

    class Meta:
        db_table = 't_inputs'
        unique_together = (('t_hash', 'input', 'product'),)

#Modelo identificador de producto, mantiene el identificador y los detalles de un determinado producto
class ProductID(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    product = models.CharField(max_length=64)
    first_transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='first_t', db_column='first_transaction')
    last_transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='last_t', db_column='last_transaction')
    owner = models.ForeignKey(Key, on_delete=models.CASCADE, related_name='owner', db_column='owner', null=True)
    destination = models.CharField(max_length=64, null=True)

    class Meta:
        db_table = 'product_id'

#Modelo producto, identifica un tipo de producto y añade información extra a las transacciones que lo utilicen
class Product(models.Model):
    code = models.CharField('Código', max_length=64, primary_key=True)
    name = models.CharField('Nombre', max_length=64)
    measure_unit = models.CharField('Unidad de medida', max_length=20)
    multiplier = models.IntegerField('Multiplicador', blank=True, default=1)
    description = models.TextField('Descripción', max_length=300, null=True, blank=True)
    
    class Meta:
        db_table = 'product_types'

    def get_absolute_url(self):
        return reverse('product_details', kwargs={'code': self.code})

#Modelo origen, añade información extra a un origen
class Origin(models.Model):
    code = models.CharField('Código', max_length=64, primary_key=True)
    name = models.CharField('Nombre', max_length=64)
    description = models.TextField('Descripción', max_length=300, null=True, blank=True)
    
    class Meta:
        db_table = 'origins'

    def get_absolute_url(self):
        return reverse('origin_details', kwargs={'code': self.code})

#Modelo destino, añade información extra a un destion
class Destination(models.Model):
    code = models.CharField('Código', max_length=64, primary_key=True)
    name = models.CharField('Nombre', max_length=64)
    description = models.TextField('Descripción', max_length=300, null=True, blank=True)
    
    class Meta:
        db_table = 'destinations'

    def get_absolute_url(self):
        return reverse('destination_details', kwargs={'code': self.code})