#!/usr/bin/env python
import dockercloud
import os
from datetime import datetime

def service_envvar(service, varname):
  for var in service.calculated_envvars:
    if var['key'] == varname:
      return var['value']

  return None

def mysql_password(service):
  pwd = service_envvar(service, 'MYSQL_ROOT_PASSWORD')
  if pwd == None:
    if service_envvar(service, 'MYSQL_ALLOW_EMPTY_PASSWORD') == 'yes':
      return ""
    else:
      return None
  else:
    return pwd

s3_bucket = os.getenv('S3_BUCKET')
containers = dockercloud.Container.list()

for container in containers:
  if container.image_name.startswith('mysql:') and container.state == 'Running':
    service = dockercloud.Utils.fetch_by_resource_uri(container.service)
    stack_name = service.stack or "Unknown"

    # Determine MySQL root password
    root_password = mysql_password(service)
    if root_password == None:
      print("Could not determine MySQL password for container {0}".format(container.name))
      continue
    if root_password == '':
      password_arg = ''
    else:
      password_arg = "-p{0}".format(root_password)

    # Enumerate databases to backup
    cmd = "mysql -u root {0} -h {1} -s --skip-column-names -e 'show databases'".format(password_arg, container.private_ip)
    dbs_output = os.popen(cmd).read()

    for db in dbs_output.splitlines():
      # Skip system databases
      if db in ['mysql', 'sys', 'performance_schema', 'information_schema']:
        continue

      # Execute backup, compress and upload to S3
      print("Backing up {0}/{1}".format(container.name, db))
      backup_cmd = "mysqldump -u root {0} -h {1} --single-transaction {2}".format(password_arg, container.private_ip, db)
      filename = "{0}-{1}.sql.gz".format(db, datetime.now().isoformat())
      backup_and_upload_cmd = "{0} | gzip | aws s3 cp - s3://{1}/{2}/{3}/{4}".format(backup_cmd, s3_bucket, stack_name, service.name, filename)
      os.system(backup_and_upload_cmd)
