# Generated manually for Orange Money integration
from django.db import migrations, models
import django.db.models.deletion
import django.contrib.contenttypes.models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0016_clientinquiry_complexity_clientinquiry_docs_count_and_more'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrangeMoneyPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(db_index=True, help_text='Référence interne unique (ex: OM-{uuid})', max_length=64, unique=True)),
                ('external_transaction_id', models.CharField(blank=True, db_index=True, help_text='ID transaction côté Orange Money', max_length=128, null=True)),
                ('status', models.CharField(choices=[('initiated', 'Initiated'), ('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('error', 'Error')], db_index=True, default='initiated', max_length=20)),
                ('amount', models.DecimalField(decimal_places=0, help_text='Montant en XOF', max_digits=10)),
                ('currency', models.CharField(default='XOF', max_length=8)),
                ('customer_msisdn', models.CharField(blank=True, help_text='Numéro téléphone client (MSISDN)', max_length=32, null=True)),
                ('merchant_id', models.CharField(blank=True, help_text='ID marchand Orange Money', max_length=128)),
                ('raw_request_payload', models.JSONField(blank=True, help_text='Payload de la requête API initiale', null=True)),
                ('raw_response_payload', models.JSONField(blank=True, help_text="Réponse de l'API lors de l'initiation", null=True)),
                ('callback_payload', models.JSONField(blank=True, help_text='Payload du webhook/callback Orange Money', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Paiement Orange Money',
                'verbose_name_plural': 'Paiements Orange Money',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrangeMoneyPaymentLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('init', 'Initiation'), ('callback', 'Callback/Webhook'), ('retry', 'Retry'), ('error', 'Error'), ('status_check', 'Status Check')], db_index=True, max_length=32)),
                ('payload', models.JSONField(default=dict, help_text="Payload de l'événement (requête, réponse, erreur, etc.)")),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='store.orangemoneypayment')),
            ],
            options={
                'verbose_name': 'Log Paiement Orange Money',
                'verbose_name_plural': 'Logs Paiements Orange Money',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='orangemoneypayment',
            index=models.Index(fields=['reference'], name='store_oran_referen_idx'),
        ),
        migrations.AddIndex(
            model_name='orangemoneypayment',
            index=models.Index(fields=['external_transaction_id'], name='store_oran_externa_idx'),
        ),
        migrations.AddIndex(
            model_name='orangemoneypayment',
            index=models.Index(fields=['status', 'created_at'], name='store_oran_status_idx'),
        ),
        migrations.AddIndex(
            model_name='orangemoneypayment',
            index=models.Index(fields=['content_type', 'object_id'], name='store_oran_content_idx'),
        ),
        migrations.AddIndex(
            model_name='orangemoneypaymentlog',
            index=models.Index(fields=['payment', 'event_type'], name='store_oran_payment_idx'),
        ),
        migrations.AddIndex(
            model_name='orangemoneypaymentlog',
            index=models.Index(fields=['created_at'], name='store_oran_created_idx'),
        ),
    ]

