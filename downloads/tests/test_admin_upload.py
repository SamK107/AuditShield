from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
import os
from downloads.models import DownloadableAsset, AssetCategory

@override_settings(MEDIA_ROOT="/tmp/test_media/")
class AdminDownloadableAssetUploadTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="password"
        )
        self.client.login(username="admin", password="password")
        self.category = AssetCategory.objects.create(name="Test Catégorie")

    def test_admin_upload_xlsx(self):
        url = reverse('admin:downloads_downloadableasset_add')
        # Simuler un fichier XLSX factice
        file_content = b"PK\x03\x04FakeXLSXContent"
        file_data = SimpleUploadedFile(
            'testfile.xlsx', file_content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        data = {
            'title': 'Test XLSX',
            'slug': 'test-xlsx',
            'category': self.category.id,
            'file': file_data,
            'visibility': 'PUBLIC',
            'version': '1.0.0',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        asset = DownloadableAsset.objects.filter(title='Test XLSX').first()
        self.assertIsNotNone(asset)
        # Vérifier que le fichier est bien stocké dans downloads/YYYY/MM/
        now = timezone.now()
        expected_path = f"downloads/{now.year}/{now.month:02d}/testfile.xlsx"
        self.assertTrue(asset.file.name.endswith("testfile.xlsx"))
        self.assertIn(f"downloads/{now.year}/{now.month:02d}/", asset.file.name)
        # Vérifier que le champ size_bytes est bien mis à jour
        self.assertEqual(asset.size_bytes, len(file_content))
