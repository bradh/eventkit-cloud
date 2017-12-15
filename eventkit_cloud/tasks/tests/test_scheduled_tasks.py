# -*- coding: utf-8 -*-
import logging

from django.contrib.auth.models import Group, User
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.test import TestCase
from django.utils import timezone
from django.conf import settings
from django.template.loader import get_template

from eventkit_cloud.jobs.models import Job, DataProvider, DataProviderTask
from eventkit_cloud.tasks.models import ExportRun, ExportTaskRecord, DataProviderTaskRecord, FileProducingTaskResult
from eventkit_cloud.tasks.scheduled_tasks import expire_runs, send_warning_email, \
    remove_outliers, get_file_size, create_size_averages
from mock import patch

logger = logging.getLogger(__name__)

# Marked for deletion
# class TestPurgeUnpublishedExportsTask(TestCase):
#     def setUp(self, ):
#         Group.objects.create(name='TestDefaultExportExtentGroup')
#         self.user = User.objects.create(username='demo', email='demo@demo.com', password='demo')
#         # bbox = Polygon.from_bbox((-7.96, 22.6, -8.14, 27.12))
#         bbox = Polygon.from_bbox((-10.85, 6.25, -10.62, 6.40))
#         the_geom = GEOSGeometry(bbox, srid=4326)
#         created_at = timezone.now() - timezone.timedelta(hours=50)  # 50 hours ago
#         Job.objects.create(name='TestJob', created_at=created_at, published=False,
#                            description='Test description', user=self.user, the_geom=the_geom)
#         Job.objects.create(name='TestJob', created_at=created_at, published=True,
#                            description='Test description', user=self.user, the_geom=the_geom)
#
#     def test_purge_export_jobs(self, ):
#         jobs = Job.objects.all()
#         self.assertEquals(2, jobs.count())
#         task = PurgeUnpublishedExportsTask()
#         self.assertEquals('Purge Unpublished Exports', task.name)
#         task.run()
#         jobs = Job.objects.all()
#         self.assertEquals(1, jobs.count())
#         self.assertTrue(jobs[0].published)


class TestExpireRunsTask(TestCase):
    def setUp(self,):
        Group.objects.create(name='TestExpireRunsTaskGroup')
        self.user = User.objects.create(username='test', email='test@test.com', password='test')
        bbox = Polygon.from_bbox((-10.85, 6.25, -10.62, 6.40))
        the_geom = GEOSGeometry(bbox, srid=4326)
        created_at = timezone.now() - timezone.timedelta(days=7)
        Job.objects.create(name="TestJob", created_at=created_at, published=False,
                                 description='Test description', user=self.user, the_geom=the_geom)


    @patch('eventkit_cloud.tasks.scheduled_tasks.send_warning_email')
    def test_expire_runs(self, send_email):
        job = Job.objects.all()[0]
        now_time = timezone.now()
        ExportRun.objects.create(job=job, user=job.user, expiration=now_time + timezone.timedelta(days=8))
        ExportRun.objects.create(job=job, user=job.user, expiration=now_time + timezone.timedelta(days=6))
        ExportRun.objects.create(job=job, user=job.user, expiration=now_time + timezone.timedelta(days=1))
        ExportRun.objects.create(job=job, user=job.user, expiration=now_time - timezone.timedelta(hours=5))

        with patch('eventkit_cloud.tasks.scheduled_tasks.timezone.now') as mock_time:

            mock_time.return_value = now_time

            self.assertEquals('Expire Runs', expire_runs.name)
            expire_runs.run()
            site_url = getattr(settings, "SITE_URL", "cloud.eventkit.dev")
            expected_url = '{0}/status/{1}'.format(site_url.rstrip('/'), job.uid)
            send_email.assert_any_call(date=now_time + timezone.timedelta(days=1), url=expected_url,
                                       addr=job.user.email, job_name=job.name)
            send_email.assert_any_call(date=now_time + timezone.timedelta(days=6), url=expected_url,
                                       addr=job.user.email, job_name=job.name)
            self.assertEqual(3, ExportRun.objects.all().count())


class TestEmailNotifications(TestCase):

    @patch('eventkit_cloud.tasks.scheduled_tasks.EmailMultiAlternatives')
    def test_send_warning_email(self, alternatives):
        now = timezone.now()
        site_url = getattr(settings, "SITE_URL", "http://cloud.eventkit.dev")
        url = '{0}/status/1234'.format(site_url.rstrip('/'))
        addr = 'test@test.com'
        job_name = "job"

        ctx = {'url': url, 'date': str(now), 'job_name': job_name}

        text = get_template('email/expiration_warning.txt').render(ctx)
        html = get_template('email/expiration_warning.html').render(ctx)
        self.assertIsNotNone(html)
        self.assertIsNotNone(text)
        send_warning_email(date=now, url=url, addr=addr, job_name=job_name)
        alternatives.assert_called_once_with("Your EventKit DataPack is set to expire.",
                                                 text, to=[addr], from_email='Eventkit Team <eventkit.team@gmail.com>')
        alternatives().send.assert_called_once()

class TestGetFileSize(TestCase):
    def setUp(self,):
        Group.objects.create(name='TestExpireRunsTaskGroup')
        self.user = User.objects.create(username='test', email='test@test.com', password='test')
        bbox = Polygon.from_bbox((-10.85, 6.25, -10.62, 6.40))
        self.the_geom = GEOSGeometry(bbox, srid=4326)
        created_at = timezone.now() - timezone.timedelta(days=7)
        self.data_provider = DataProvider.objects.create(name='test-provider',
                                                         slug='test',
                                                         display=True)
        self.osm_data_provider = DataProvider.objects.create(name='osm',
                                                             slug='osm',
                                                             display=True)
        self.data_provider_task = DataProviderTask.objects.create(provider=self.data_provider)
        self.osm_data_provider_task = DataProviderTask.objects.create(provider=self.osm_data_provider)
        self.job = Job.objects.create(name="TestJob",
                                      created_at=created_at,
                                      published=False,
                                      description='Test description',
                                      user=self.user,
                                      the_geom=self.the_geom)
        self.job.provider_tasks.add(self.data_provider_task, self.osm_data_provider_task)
        self.run = ExportRun.objects.create(job=self.job, user=self.user, status='COMPLETED')

    @patch('eventkit_cloud.tasks.scheduled_tasks.remove_outliers')
    @patch('eventkit_cloud.tasks.scheduled_tasks.get_file_size')
    @patch('eventkit_cloud.ui.data_estimator.get_osm_feature_count')
    def test_create_size_averages(self, mock_get_count, mock_get_size, mock_remove):
        mock_get_count.return_value = 400
        mock_get_size.return_value = 0.6
        mock_remove.return_value = [0.505]
        self.assertTrue(True)
        self.assertEqual(DataProvider.objects.get(name='test-provider').size_estimate_constant, None)
        self.assertEqual(DataProvider.objects.get(name='osm').size_estimate_constant, None)
        create_size_averages()
        self.assertEqual(DataProvider.objects.get(name='test-provider').size_estimate_constant, 0.505)
        self.assertEqual(DataProvider.objects.get(name='osm').size_estimate_constant, 0.505)

        providers = DataProvider.objects.all()
        for provider in providers:
            provider.size_estimate_constant = None
            provider.save()

        mock_get_count.side_effect = Exception('oh no')
        mock_remove.return_value = []
        self.assertEqual(DataProvider.objects.get(name='test-provider').size_estimate_constant, None)
        self.assertEqual(DataProvider.objects.get(name='osm').size_estimate_constant, None)
        create_size_averages()
        self.assertEqual(DataProvider.objects.get(name='test-provider').size_estimate_constant, None)
        self.assertEqual(DataProvider.objects.get(name='osm').size_estimate_constant, None)

        mock_get_count.side_effect = None
        mock_remove.return_value = [0.505]
        ExportRun.objects.all()[0].delete()
        create_size_averages()
        self.assertEqual(DataProvider.objects.get(name='test-provider').size_estimate_constant, None)
        self.assertEqual(DataProvider.objects.get(name='osm').size_estimate_constant, None)


    def test_get_file_size(self):
        task_record = DataProviderTaskRecord.objects.create(name='test-provider',
                                                            slug='provider',
                                                            run=self.run)
        test_result = FileProducingTaskResult.objects.create(size=600)
        export_task = ExportTaskRecord.objects.create(export_provider_task=task_record,
                                                      name='Test Export',
                                                      result=test_result)

        ret = get_file_size(run=self.run)
        self.assertEqual(ret, None)

        ret = get_file_size(provider_name='test-provider')
        self.assertEqual(ret, None)

        ret = get_file_size(run=self.run, provider_name='test-provider')
        self.assertEqual(ret, 600 * 0.001)

        test_result.size = 0
        test_result.save()
        ret = get_file_size(run=self.run, provider_name='test-provider')
        self.assertEqual(ret, 0)

        test_result.size = 50
        test_result.save()
        ret = get_file_size(run=self.run, provider_name='test-provider', min_size=51)
        self.assertEqual(ret, 0)

        ret = get_file_size(run=self.run, provider_name='some-other-provider')
        self.assertEqual(ret, 0)

    def test_remove_outliers(self):
        array = [10, 10, 10, 10, 12, 2]
        expected = [10, 10, 10, 10, 12]
        output = remove_outliers(array)
        self.assertEqual(output, expected)

        array = [2, 4, 7]
        output = remove_outliers(array)
        self.assertEqual(output, array)




