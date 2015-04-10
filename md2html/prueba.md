Title:   SMSC v5.4 Service Pack 7 / HF18
title:   Documento de instalación
Author:  Jesús Fernández
email:   jesusmanuel.fernandez@acision.com
css:     acision.css
         codehilite.css
theme:   theme-redish
         layout-reverse
date:    07 Abril 2015

# 1. Requisitos previos


| Fichero                   |Tamaño (Bytes)|  MD5                             |
|---------------------------|--------------|----------------------------------|
| SMSC_R5_4-07_IA64_KIT.ZIP    |139029532  | a0d8f87501ca88e26239bb08e1aad6d5 |
| SMSC_R5_4-07_IA64_SCRIPTS.ZIP|  7527111  | aba4b9e007434587b2faddb8e2dc4ad6 |
| patches.zip                  |  29607107 | e845326217cee0c697dcf215588d86fe |



    #!bash
    $ backup /record /log /ignore=interlock /image /data_format=compress
    /label=BACKUP_SP7 SMSC_LOG1: directorio_backup:backup_SMSC_LOG1.bck

    backup /record /log /ignore=interlock /image /data_format=compress 
    /label=BACKUP_SP7 SMSC_LOG2: directorio_backup:backup_SMSC_LOG2.bck


- Reiniciar el centro al menos 2 días antes de la fecha prevista para la
actualización.
- Comprobar que, tras el reinicio, no se observen anomalías en el
funcionamiento normal del centro.
- Limpiar los ficheros no necesarios del directorio SMSC$ROOT (y 
subdirectorios). Borrar y purgar ficheros temporales y de log.
- No realizar cambios en la configuración en el periodo comprendido entre el
reinicio previo y la actualización de versión.
- Comprobar que el disco SMSC_RDB tenga al menos 8.000.000 bloques libres:

        :::bat
        show dev SMSC_RDB /full

- Realizar backup de todas las unidades de LOGSRV:
    
- Other stuff

            #!/bin/python
            import antigravity
            from matplotlib import plt as pyplot


- ETC

        :::python
        import another
    

Asdiaposdapsd opas dposam dpaosdmpoasdpo m

:::text
Monospaced code lorem ipsum blahblahblah
aspdion sdogfiuns fdpfgdffposfd f]sdfpksdpfoksd 
sdfpio sdofins doifn sdoifn onqoen iusdfboi fof 
    
# 2. Instalación


> Todas las actividades deben realizarse en el nodo #1 del clúster como usuario
**SYSTEM**.


### Primeros pasos

    :::text
    ! Acceder al directorio de instalación y limpiar los ficheros
    ! de instalación de Service Pack antiguos.
    SET DEFAULT DSA0:[GOLD]
    @CLEANUP_KIT

    ! Copiar los ficheros de instalación en DSA0:[GOLD]
    ! y comprobar el hash MD5
    md5sum SMSC_R5_4-07_IA64_KIT.ZIP
    md5sum SMSC_R5_4-07_IA64_SCRIPTS.ZIP
    md5sum patches.zip

    ! Descomprimir el archivo de scripts y hacer una 
    ! copia de seguridad del aplicativo SMSC
    unzip -o SMSC_R5_4-07_IA64_SCRIPTS.ZIP
    @backup_nodes





### Parada del aplicativo
```

MC SYSMAN SET ENVIRONMENT /CLUSTER
SYSMAN> DO @SNMP_SCRIPTS:SNMP_SA STOP SMSCAGENT
SYSMAN> DO @SNMP_SCRIPTS:SNMP_SA STOP OPCOMAGENT
SYSMAN> EXIT

! Detener la recogida de estadísticas
PMS_STOP
@t4$sys:t4$stop all

! Detener los trabajos en las colas de ejecución
SHOW QUEUE /BATCH
DELETE /entry=<CMG_CLEANUP entry ID>
DELETE /ENTRY=<BILLING_PP entry ID>
DELETE /ENTRY=<MON_PML entry ID>

! Hacer copia de seguridad de la base de datos SDB
@sbr$root:[scripts]bck_mimer_rdb.com dsa0:[backup]previo_sp7.rbf

! Detener el aplicativo
@SYS$STARTUP:SMSC_SHUTDOWN

```

### Conversión del sistema de ficheros de los discos de LOGSRV

```

! Comprobar que no haya ficheros abiertos en las unidades SMSC_LOG
SHOW DEVICE SMSC_LOG1 /FILE
SHOW DEVICE SMSC_LOG2 /FILE

!Desmontar ambas unidades de los dos nodos
DISMOUNT /CLUSTER SMSC_LOG1
DISMOUNT /CLUSTER SMSC_LOG2

! Montar solamente para la sesión actual los discos individualmente
! y convertir el sistema de ficheros de ODS-2 a ODS-5
MOUNT/OVER=IDENT $1$DGA400:
MOUNT/OVER=IDENT $1$DGA401:
SET VOLUME /STRUCTURE_LEVEL=5 $1$DGA400:
SET VOLUME /STRUCTURE_LEVEL=5 $1$DGA401:
DISMOUNT $1$DGA400:
DISMOUNT $1$DGA401:

! Volver a montar los discos en ambos nodos
MC SYSMAN SET ENVIRONMENT /CLUSTER
SYSMAN> DO @SYS$MANAGER:MOUNT_DISKS.COM
SYSMAN> EXIT

```

### Instalación de SP7 y hotfixes

```

! Instalación de SP7
@INSTALL_KIT SMSC_R5_4-07_IA64_KIT.ZIP /CCA_RUN=AFTER

! Instalación de parches adicionales
unzip -o -d smsc$root:[bin] patches *.exe
unzip -o -d smsc$root:[scripts] patches *.com
unzip -o -d smsc$root:[help] patches *.hlb
unzip -o -d smsc$root:[templates.data] patches *.txt
rename smsc$root:[scripts]calc_mula.com cmg$tools:calc_mula.com
rename smsc$root:[scripts]om_vms.com smsc$root:[scripts.ams]om_vms.com

! Actualizar fichero de errores
merge_err :== "$smsc$root:[bin]merge_err.exe"
merge_err smsc$root:[templates.data]ppl_nrsn_template.txt -
smsc$root:[data]ppl_nrsn.txt smsc$root:[data]ppl_nrsn.txt

! Actualización de la base de datos
PML> do smsc$root:[000000]dbe
@smsc$root:[scripts]smsc_db_patch.com SMSC-852
@smsc$root:[scripts]smsc_db_patch.com SMSC-903
```

> En este punto, realizar todas aquellas acciones manuales que sean necesarias,
de acuerdo con la salida del script `INSTALL_KIT`.

> El aplicativo SMSC (MD) arrancará automáticamente.

### Arrancar el resto de servicios

```

mc sysman set env/cluster
sysman> do @SNMP_SCRIPTS:SNMP_SA START SMSCAGENT
sysman> do @SNMP_SCRIPTS:SNMP_SA START OPCOMAGENT
sysman> exit
PMS
@SYS$COMMON:[SYSMGR]CMG_CLEANUP
SUBMIT /QUEUE=SYS$BATCH SMSC$ROOT:[SCRIPTS]BILLING_PP.COM
@SYS$STARTUP:CMG_START_ENTITIES
```

Comprobar el arranque correcto de todas las entidades:
`@CMG$TOOLS:SMSC_CHECK_ENTITIES`


3. Procedimiento de marcha atrás
================================

> TBD

Referencias
===========

| Documento                         | Versión   |
|-----------------------------------|-----------|
| SMSC_R5_4-07_Installation_Manual  | 5.0       |
| SMSC SP6 Release Notes            | n/a       |
| SMSC SP7 Release Notes            | n/a       |
| SMSC HF Release Notes             | HF01-HF18 |


Versiones
=========

| Versión  | Fecha      | Estado | Autor       | Cambios                   |
|----------|------------|--------|-------------|---------------------------|
| 0.1      | 20/02/2015 | DRAFT  |fernandezjm  | Versión inicial: SP7 HF09 |
| 0.2      | 07/04/2015 | DRAFT  |fernandezjm  | Actualizado a HF18        |
