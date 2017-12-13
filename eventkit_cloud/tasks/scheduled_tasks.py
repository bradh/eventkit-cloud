# -*- coding: utf-8 -*-
from django.utils import timezone
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from string import Template
from celery.utils.log import get_task_logger
from eventkit_cloud.celery import app
import numpy as np

logger = get_task_logger(__name__)


# Seems redundant to expire_runs, if not needed should be deleted for 1.0.0
# @app.task(name='Purge Unpublished Exports')
# def PurgeUnpublishedExportsTask():
#     """
#     Purge unpublished export tasks after 48 hours.
#     """
#     from eventkit_cloud.jobs.models import Job
#     time_limit = timezone.now() - timezone.timedelta(hours=48)
#     expired_jobs = Job.objects.filter(created_at__lt=time_limit, published=False)
#     count = expired_jobs.count()
#     logger.debug('Purging {0} unpublished exports.'.format(count))
#     expired_jobs.delete()

@app.task(name="Create Size Averages")
def create_size_averages():
    """
    Looks at the last n runs for each provider and calculates an average file size per sq km
    Adds the new average to the provider model 
    """
    from eventkit_cloud.tasks.models import ExportRun
    from eventkit_cloud.jobs.models import DataProvider
    from eventkit_cloud.ui.data_estimator import get_osm_feature_count

    logger.debug('Creating size average constants')
    providers = DataProvider.objects.all()
    for provider in providers:
        # get the last 100 completed runs that contain this provider in the provider tasks
        runs = ExportRun.objects.filter(job__provider_tasks__provider=provider, status='COMPLETED')[:100]
        if not runs:
            logger.info('{0} has no runs'.format(provider.slug))
            continue

        logger.info('------------- {0} -------------'.format(provider.slug))
        if provider.slug == 'osm':
            gb_per_feature_sum = []
            for run in runs:
                try:
                    total_features = get_osm_feature_count(geojson_geometry=run.job.the_geom.json)
                except Exception as e:
                    logger.error(e)
                    continue
                if total_features:
                    file_size_gb = get_file_size(run=run, provider_name=provider.name, min_size=0.5)
                    if file_size_gb:
                        gb_per_feature = file_size_gb / int(total_features)
                        gb_per_feature_sum.append(gb_per_feature)
            # if we have some gb/feature values get the average and save it to the provider model
            gb_per_feature_sum = remove_outliers(data_array=gb_per_feature_sum)
            if len(gb_per_feature_sum):
                total = 0
                for value in gb_per_feature_sum:
                    total += value
                total = total/len(gb_per_feature_sum)
                provider.size_estimate_constant = total
                provider.save()

        else:
            gb_per_sq_km_sum = []
            for run in runs:
                # get the area in sq km
                sq_m = run.job.the_geom_webmercator.area
                sq_km = sq_m * 0.000001
                file_size_gb = get_file_size(run=run, provider_name=provider.name, min_size=2)
                if file_size_gb:
                    gb_per_sq_km = file_size_gb / sq_km
                    gb_per_sq_km_sum.append(gb_per_sq_km)
            # if we have some gb/sqkm values get the average and save it to the provider model
            gb_per_sq_km_sum = remove_outliers(data_array=gb_per_sq_km_sum)
            if len(gb_per_sq_km_sum):
                total = 0
                for value in gb_per_sq_km_sum:
                    total += value
                total = total/len(gb_per_sq_km_sum)
                provider.size_estimate_constant = total
                provider.save()
    logger.info('Finished creating size average constants')


@app.task(name='Expire Runs')
def expire_runs():
    """
    Checks all runs.
    Expires all runs older than 2 weeks,
    Emails users one week before scheduled expiration time
    and 2 days before schedule expiration time.
    """
    from eventkit_cloud.tasks.models import ExportRun
    site_url = getattr(settings, "SITE_URL")
    runs = ExportRun.objects.all()

    for run in runs:
        expiration = run.expiration
        email = run.user.email
        if not email:
            break
        uid = run.job.uid
        url = '{0}/status/{1}'.format(site_url.rstrip('/'), uid)
        notified = run.notified
        now = timezone.now()
        # if expired delete the run:
        if expiration <= now:
            run.delete()

        # if two days left and most recent notification was at the 7 day mark email user
        elif expiration - now <= timezone.timedelta(days=2):
            if not notified or (notified and notified < expiration - timezone.timedelta(days=2)):
                send_warning_email(date=expiration, url=url, addr=email, job_name=run.job.name)
                run.notified = now
                run.save()

        # if one week left and no notification yet email the user
        elif expiration - now <= timezone.timedelta(days=7) and not notified:
            send_warning_email(date=expiration, url=url, addr=email, job_name=run.job.name)
            run.notified = now
            run.save()


def send_warning_email(date=None, url=None, addr=None, job_name=None):
    """
    Args:
        date: A datetime object representing when the run will expire
        url: The url to the detail page of the export
        addr: The email address to which the email will be sent

    Returns: None
    """

    subject = "Your EventKit DataPack is set to expire."
    to = [addr]
    from_email = getattr(
        settings,
        'DEFAULT_FROM_EMAIL',
        'Eventkit Team <eventkit.team@gmail.com>'
    )
    ctx = {'url': url, 'date': str(date), 'job_name': job_name}

    text = get_template('email/expiration_warning.txt').render(ctx)
    html = get_template('email/expiration_warning.html').render(ctx)
    try:
        msg = EmailMultiAlternatives(subject, text, to=to, from_email=from_email)
        msg.attach_alternative(html, "text/html")
        msg.send()
    except Exception as e:
        logger.error("Encountered an error when sending status email: {}".format(e))

def get_file_size(run=None, provider_name=None, min_size=0):
    """
    :param run: the run object for which file size should be searched 
    :param provider_name: the name of the provider the files should be for
    :param min_size: the minimum file size that can be returned
    :return: 
    """
    if not (run and provider_name):
        logger.error('Both run and provider name are required to get file size')
        return None

    from eventkit_cloud.tasks.models import ExportTaskRecord, DataProviderTaskRecord
    ignored_tasks = ['Area of Interest (.geojson)', 'Project file (.zip)']

    data_provider_task_records = DataProviderTaskRecord.objects.filter(run=run)
    for data_provider_task_record in data_provider_task_records:
        # only check export provider tasks that correspond to the provider in question
        if data_provider_task_record.name != provider_name:
            continue
        # get all the export tasks associated with the export provider task
        export_tasks = ExportTaskRecord.objects.filter(export_provider_task=data_provider_task_record)
        for export_task in export_tasks:
            # ignore zip files and aoi file
            if export_task.name not in ignored_tasks:
                result = export_task.result
                if result:
                    file_size_mb = result.size
                    if not file_size_mb or file_size_mb < min_size:
                        # ignore files with no reported size or less than 500 kb since that could be an empty file
                        return 0
                    file_size_gb = file_size_mb * 0.001
                    return file_size_gb
        return 0

def remove_outliers(data_array=[], deviations=2):
    if not len(data_array) > 3:
        return data_array
    stdev = np.std(data_array)
    median = np.median(data_array)
    upper_limit = median + (deviations * stdev)
    lower_limit = median - (deviations * stdev)
    return [value for value in data_array if lower_limit < value < upper_limit]
