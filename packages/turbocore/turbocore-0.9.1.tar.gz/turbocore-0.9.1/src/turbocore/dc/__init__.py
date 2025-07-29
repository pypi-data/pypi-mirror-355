import turbocore
import yaml
import os
import os.path


def debian_dockerfile(basedir=None, filename="Dockerfile", image_spec="ubuntu:24.04", entrypoint=[], apt_packages=[], dpe_i=[], dpe_e=[], pecl_i=[]):
    filename_ = filename
    if basedir != None:
        os.makedirs(basedir)
        filename_ = os.path.join(basedir, filename)
    with open(filename_, "w") as f:
        f.write("FROM %s\n\n" % image_spec)
        f.write("ENV DEBIAN_FRONTEND=noninteractive\n\n")
        f.write("ARG TARGETPLATFORM\n\n")
        f.write("ARG BUILDPLATFORM\n\n")
        f.write("RUN apt update && apt upgrade -y\n\n")
        if len(apt_packages) > 0:
            f.write("RUN apt install -y %s\n\n" % " ".join(apt_packages))

        for n in dpe_i:
            f.write("RUN docker-php-ext-install %s\n\n" % n)

        for n in pecl_i:
            f.write("RUN pecl install %s\n\n" % n)

        for n in dpe_e:
            f.write("RUN docker-php-ext-enable %s\n\n" % n)
        
        f.write("ENTRYPOINT [%s]\n\n" % ", ".join(['"%s"' % x for x in entrypoint]))



def image_waf():
    return "owasp/modsecurity-crs:4.15.0-nginx-alpine-202506050606"


def dc_new(BASEDIR, FILENAME, PROFILE):
    os.makedirs(BASEDIR)
    svc = {
        'services': {
            'custom': {
                'build': {
                    'context': "customimg/",
                    'dockerfile': "Dockerfile"
                },
                'image': "meincustomimage",
                'container_name': "cucu",
                'restart': "always",
                'expose': [],
                'ports': [ "8080:80" ]
            },
            'php-fpm': {
                'build': {
                    'context': "php-fpm/",
                    'dockerfile': "Dockerfile"
                },
                'container_name': "php-fpm",
                'restart': "always",
                'expose': [],
                'ports': [ "8080:80" ]
            },
            'waf': {
                'image': image_waf()
            }
        }
    }
    
    debian_dockerfile(
        basedir="dockerdocker/customimg",
        apt_packages=['ca-certificates', 'nginx-extras', 'openssl', 'libnginx-mod-http-lua', 'mc'],
        entrypoint=['/usr/sbin/nginx', '-g', 'daemon off;']
        )
    
    debian_dockerfile(
        basedir="dockerdocker/php-fpm", 
        apt_packages=[
            'libvpx-dev',
            'libfreetype6-dev',
            'libjpeg62-turbo-dev',
            'libpng-dev',
            'libicu-dev',
            'libpq-dev',
            'libxpm-dev'
        ], 
        entrypoint=['php-fpm'], 
        image_spec='php:8.4-fpm',
        dpe_i=["mysqli", "pgsql", "pdo_pgsql"],
        pecl_i=["redis"],
        dpe_e=["mysqli", "redis"]
        )
    
    with open(os.path.join(BASEDIR, FILENAME), "w") as f:
        yaml.safe_dump(svc, f)


def main():
    turbocore.cli_this(__name__, "dc_")
