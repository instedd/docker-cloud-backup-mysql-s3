#!/usr/bin/env python
import dockercloud
import os
from datetime import datetime

class DbContainer:
  def __init__(self, container):
    self.container = container
    self.service = dockercloud.Utils.fetch_by_resource_uri(container.service)
    self.stack_name = self.service_envvar('DOCKERCLOUD_STACK_NAME') or "Unknown"

  def service_envvar(self, varname):
    for var in self.service.calculated_envvars:
      if var['key'] == varname:
        return var['value']

    return None

  def run_and_upload(self, dbname, cmd, s3_bucket):
    print("Backing up {0}/{1}".format(container.name, dbname))
    filename = "{0}-{1}.sql.gz".format(dbname, datetime.now().isoformat())
    backup_and_upload_cmd = "{0} | gzip | aws s3 cp - s3://{1}/{2}/{3}/{4}".format(cmd, s3_bucket, self.stack_name, self.service.name, filename)
    os.system(backup_and_upload_cmd)


class MysqlContainer(DbContainer):
  def backup(self, s3_bucket):
    print("Backing up databases in MySQL container '{0}/{1}'".format(self.stack_name, self.container.name))
    # Determine MySQL root password
    root_password = self.mysql_password()
    if root_password == None:
      print("Could not determine MySQL password for container '{0}/{1}'".format(self.stack_name, self.container.name))
      return
    if root_password == '':
      password_arg = ''
    else:
      password_arg = "-p{0}".format(root_password)

    # Enumerate databases to backup
    cmd = "mysql -u root {0} -h {1} -s --skip-column-names -e 'show databases'".format(password_arg, self.container.private_ip)
    dbs_output = os.popen(cmd).read()

    for db in dbs_output.splitlines():
      # Skip system databases
      if db in ['mysql', 'sys', 'performance_schema', 'information_schema']:
        continue

      # Execute backup, compress and upload to S3
      backup_cmd = "mysqldump -u root {0} -h {1} --single-transaction {2}".format(password_arg, self.container.private_ip, db)
      self.run_and_upload(db, backup_cmd, s3_bucket)

  def mysql_password(self):
    pwd = self.service_envvar('MYSQL_ROOT_PASSWORD')
    if pwd == None:
      if self.service_envvar('MYSQL_ALLOW_EMPTY_PASSWORD') == 'yes':
        return ""
      else:
        return None
    else:
      return pwd

s3_bucket = os.getenv('S3_BUCKET')
for container in dockercloud.Container.list():
  if container.state != 'Running':
    continue

  if container.image_name.startswith('mysql:'):
    MysqlContainer(container).backup(s3_bucket)

