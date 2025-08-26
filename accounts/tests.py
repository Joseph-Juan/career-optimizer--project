# accounts/tests.py

import io
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class CVWorkflowTests(TestCase):
    def setUp(self):
        # Create and log in a test student user
        self.username = 'teststudent'
        self.password = 'correcthorsebatterystaple'
        self.user = User.objects.create_user(
            username=self.username,
            email='student@example.com',
            password=self.password,
            is_admin=False
        )
        self.client.login(username=self.username, password=self.password)

    def test_cv_editor_get(self):
        """The CV editor page should load successfully and include the form."""
        url = reverse('accounts:student_cv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check that our CV form fields are in the HTML
        self.assertContains(response, 'name="cv-full_name"')
        self.assertContains(response, 'name="cv-email"')
        self.assertContains(response, 'name="cv-phone"')
        self.assertContains(response, 'id="experience-list"')
        self.assertContains(response, 'id="language-list"')

    def test_cv_submission_minimal(self):
        """Submitting a minimal CV should return a PDF."""
        url = reverse('accounts:student_cv')

        # Build POST data for one CV + one experience + one language
        post_data = {
            # main CVForm prefixed "cv"
            'cv-full_name': 'Jane Q. Tester',
            'cv-email':     'jane@example.com',
            'cv-phone':     '+1 555-0000',
            'cv-address':   'Testville, TX',

            # one experience block (prefix exp_0_)
            'exp_0_job_title':   'Intern',
            'exp_0_company':     'Acme Corp',
            'exp_0_start_date':  '2020-01',
            'exp_0_end_date':    '2021-01',
            'exp_0_description': 'Did some testing.',

            # one language block (prefix language_0 etc)
            'language_0': 'English',
            'speaking_0': 'C2',
            'writing_0':  'C2',
        }

        response = self.client.post(url, post_data)
        # It should return a PDF, not redirect back to form
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        # The first few bytes of a PDF file are "%PDF-"
        pdf_start = response.content[:5]
        self.assertEqual(pdf_start, b'%PDF-')

    def test_invalid_dates(self):
        """Submitting end_date before start_date should still generate PDF but you might handle in future."""
        url = reverse('accounts:student_cv')
        post_data = {
            'cv-full_name': 'Edge Case',
            'cv-email':     'edge@example.com',
            'cv-phone':     '',
            'cv-address':   '',

            'exp_0_job_title':  'Something',
            'exp_0_company':    'Nowhere',
            'exp_0_start_date': '2025-01',
            'exp_0_end_date':   '2024-12',
            'exp_0_description':'Dates backwards.',

            'language_0': 'English',
            'speaking_0': 'A1',
            'writing_0':  'A1',
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
