from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import DownloadCategory, DownloadableAsset

# Create your tests here.

class AdminDownloadableAssetUploadTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="password"
        )
        self.client.login(username="admin", password="password")
        self.category = DownloadCategory.objects.create(
            slug="test-category",
            title="Test Catégorie",
            page_path="/test-category"
        )

    def test_admin_upload_downloadable_asset(self):
        url = reverse('admin:downloads_downloadableasset_add')
        with open(__file__, 'rb') as f:  # Utilise ce fichier comme dummy upload
            file_data = SimpleUploadedFile('testfile.txt', f.read(), content_type='text/plain')
        data = {
            'title': 'Test Asset',
            'slug': 'test-asset',
            'category': self.category.pk,
            'description': 'Un fichier de test',
            'file': file_data,
            'ebook_code': 'AUDIT_SANS_PEUR',
            'part_code': '',
            'chapter_code': '',
            'visibility': 'PUBLIC',
            'is_active': True,
            'version': '1.0.0',
        }
        response = self.client.post(url, data, follow=True)
        if hasattr(response, 'context') and response.context and 'adminform' in response.context:
            errors = response.context['adminform'].form.errors
            print('Admin form errors:', errors)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(DownloadableAsset.objects.filter(title='Test Asset').exists())
