import os

from fabric.api import env, run, cd


#TODO consider configging w/ django
ssh_user = os.environ.get('SSH_USER')
shell_hostname = os.environ.get('EC2_HOSTNAME')
print os.environ.get('EC2_HOSTNAME')
eventkit_cwd = os.environ.get('EVENTKIT_CWD')
database_url = os.environ.get('DATABASE_URL')

if not ssh_user:
    raise ValueError("EC2_HOSTNAME env var required")

if not shell_hostname:
    raise ValueError("EC2_HOSTNAME env var required")

env.user = ssh_user
env.hosts = []
env.hosts.append(shell_hostname)


def deploy_ec2():
    with cd(eventkit_cwd):
        # stop/remove old containers
        run('sudo docker-compose down')

        # remove celery container images
        try:
            run('sudo docker rmi -f $(sudo docker images | grep celery | tr -s \' \' | cut -f 3 -d " " | uniq)')
        except:
            pass
        # TODO: remove intermediate and discarded container images

        run('sudo docker-compose build celery-beat')   
        run('sudo docker-compose build celery')   

        # install new containers
        run(
            'sudo docker-compose run -T '
            '--entrypoint "sh" celery '
            '/var/lib/eventkit/scripts/celery-entrypoint.sh %s' % (database_url,)
        )

        run(
            'sudo docker-compose run -T '
            '--entrypoint "sh" celery-beat '
            '/var/lib/eventkit/scripts/celery-beat-entrypoint.sh %s' % (database_url,)
        )