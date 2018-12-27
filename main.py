#####################################################################################################################
# Descripcion: Script de backup
#
# Notas:       - Este script realiza un backup con duply realizando previamente un volcado de todas las bases de datos
#                Mysql. Además informa por email del resultado y posibles errores.
#
# Version:     1.0.0.0
# Autor:       David Poza Suarez
# Fecha:       27 Febrero 2018
#####################################################################################################################
from datetime import datetime
import platform
import os
import sys
import re
from subprocess import run, PIPE

now = datetime.now()
fecha = str(now.year) + "_" + str(now.month) + "_" + str(now.day) + "_" +  str(now.hour) + "_" + str(now.minute)
host = platform.node()
me = sys.argv[0]
##############################################################################
# Configuracion
# -----------------------------------------------------------------------------
jobname = "profile" #nombre del perfil de duply
mysqlUser = "root"
mysqlPass = "xxxxxxxxxxxxxxxxxxx"
# mysqlDbList = ["DB1", "OTRADB1", "OTRADB2"]
# mysqlContainerName = "nextcloud_db_1"
dirLogs = "/var/log/"
fileLog = dirLogs + "back_" + fecha + ".log"
# directorio para el volcado mysql
dirMysql = "/mnt/nextcloud/data/dump"
# logEmailRecipients = "correo1@gmail.com, correo2@gmail.com"
logEmailRecipients = "correo1@gmail.com"
logEmailFrom = "admin@tuserver.com"
#####################################################################


def dateNow():
    now = datetime.now()
    fecha = str(now.year) + "_" + str(now.month) + "_" + str(now.day) + "_" +  str(now.hour) + "_" + str(now.minute)
    return fecha


################################################################################
# Descripcion: Manda un email
# Parametros: Asunto y cuerpo del mensaje
################################################################################
def sendMail(subject, body=""):
    sendmail_location = "/usr/sbin/sendmail"  # sendmail location
    p = os.popen("%s -t" % sendmail_location, "w")
    p.write("From: %s\n" % logEmailFrom)
    p.write("To: %s\n" % logEmailRecipients)
    p.write("Subject: " + subject + "\n")
    p.write("\n")  # blank line separating headers from body
    p.write(body)
    return p.close()


###############################################################################
# Descripcion: Escribe un mensaje en el log
# Parametros: Mensaje
###############################################################################
def writeLog(msg):
    try:
        log = open(fileLog, "a+")
    except:
        print(dateNow() + ": Problemas al crear el fichero de log\n")
        return -1
    log.write(dateNow() + ": " + msg + "\n")
    log.close()
    return 0


################################################################################
# Descripcion: hace un volcado de la base de datos
#              que se encuentra en un contenedor docker. Y la guarda en un
#              fichero dump.sql en el directorio definido en "dirMysql".
# Parametros: nombre del contenedor de la bd, usuario, password y lista de bases
#             de datos separadas por comas.
################################################################################
def doMysqlBackDocker(container, user, password, dbs):
    ret = run(
        [
            "docker",
            "exec",
            container,
            "mysqldump",
            "--single-transaction",
            "-u", user,
            "-p"+password,
            "-B",
            dbs
            ], stdout=open(dirMysql + "/dump.sql", "w"), stderr=PIPE
    )

    if (ret.returncode != 0):
        log.write(dateNow() + ": Error al crear backup de base de datos\n")
        log.write(dateNow() + ":" + ret.stderr.decode("utf-8") +"\n")
        sendMail("Error de backup - "+host, ret.stderr.decode("utf-8"))
    else:
        log.write(dateNow() + ": Volcado de mysql OK\n")
    return ret.returncode


################################################################################
# Descripcion: obtiene un array con los nombres de bases de datos que existen
# Parametros: usuario, password
################################################################################
def getDatabases(user, password):
    db = MySQLdb.connect(host = "localhost", user = user, passwd = password)
    c = db.cursor()
    c.execute("SHOW DATABASES")
    l = c.fetchall()
    l = [ i[0] for i in l ]
    db.close()
    return l


################################################################################
# Descripcion: hace un volcado de la base de datos dada
#              Y la guarda en un fichero con el nombre.sql en el directorio
#              definido en "dirMysql".
# Parametros: nombre del contenedor de la bd, usuario, password y bd
################################################################################
def doMysqlBack(user, password, db):
    ret = run(
        [
            "mysqldump",
            "--single-transaction",
            "-u", user,
            "-p"+password,
            "-B",
            db
            ], stdout=open(dirMysql + "/"+db+".sql", "w"), stderr=PIPE
    )

    if (ret.returncode != 0):
        log.write(dateNow() + ": Error al crear backup de base de datos\n")
        log.write(dateNow() + ":" + ret.stderr.decode("utf-8") +"\n")
        sendMail("Error de backup - "+host, ret.stderr.decode("utf-8"))
    else:
        log.write(dateNow() + ": Volcado de mysql OK\n")
    return ret.returncode



################################################################################
# Descripcion: Borra el fichero de volcado de la base de datos.
#              Este fichero solo se incluye antes de hacer la copia, para que
#              vaya dentro, pero luego se borra para dejar espacio a
#              la siguiente copia.
################################################################################
def delMysqlBack():
    return os.remove(dirMysql + "/dump.sql")


################################################################################
# Descripcion: Llama a duply y escribe la salida en el log y lo envia por email
################################################################################
def doDuplyBackup(jobname):
    ret = run(
        [
            "duply", jobname, "backup"
        ],
        stdout=PIPE, stderr=PIPE
    )

    if (ret.returncode != 0):
        log.write(dateNow() + ": Error al realizar duply\n")
        log.write(dateNow() + ":" + ret.stderr.decode("utf-8") +"\n")
        sendMail("Error de backup - "+host, ret.stderr.decode("utf-8"))
    else:
        log.write(dateNow() + ": Backup OK\n")
        sendMail("Backup OK - "+host, ret.stdout.decode("utf-8"))
    return ret.returncode



################################################################################
# Descripcion: Programa principal
################################################################################
if __name__ == '__main__':
    os.chmod(me, 700)
    if os.geteuid() != 0:
        print("dpsBackups debe ser ejecutado como root\n")

    ret = run(["mkdir", "-p", dirMysql])

    # comprobamos que el fichero de log se ha creado/abierto, en modo append
    try:
        log = open(fileLog, "a+")
    except:
        print(dateNow() + ": Problemas al crear el fichero de log\n")
        sys.exit()

    # obtenemos un array con todos los nombres de las bases de datos
    dbs = getDatabases(mysqlUser, mysqlPass)

    # volcado de todas las bases de datos
    for db in dbs:
        ret = doMysqlBack(mysqlUser, mysqlPass, db)
        if(ret != 0):
            log.close()
            sys.exit()

    # backup
    ret = doDuplyBackup(jobname)
    if(ret != 0):
        log.close()
        sys.exit()

    delMysqlBack()

    # si todo ha ido ok borramos el log
    os.remove(fileLog)

    log.write("\n")
    log.close()

