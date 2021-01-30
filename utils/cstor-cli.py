#!/usr/bin/python
# -*- coding: UTF-8 -*-

import argparse
import sys
import os
import json
import time
import fcntl
import stat
import random
#import locale

uusvolcli = '/usr/lib/uraid/scripts/vols/vol.sh'
LOCAL_FS = 'localfs'
NFS = 'nfs'
GLUSTERFS = 'glusterfs'
UUS = 'uus'
URAID='vdiskfs'

CSTOR_DIR = '/etc/sysconfig/cstor'
CSTOR_POOL = '/etc/sysconfig/cstor/pool'
CSTOR_POOL_INVALID = '/etc/sysconfig/cstor/pool.invalid'
CSTOR_LOCALFS_POOL_TEST = '/etc/sysconfig/cstor/localfs-test'
DEF_BASE_MNT_PATH = '/var/lib/libvirt/cstor'

VERSION = 'VERSION 0.1  change 20201214-1730'

    
def main(*argv):
    parser = argparse.ArgumentParser(prog=argv[0], version=VERSION, usage='%(prog)s -h')

    sub_parser = parser.add_subparsers(title='subcommands' ,description='subcommands help use %(prog)s -h', help=VERSION)
    ###########################
    #devlist_parser = sub_parser.add_parser('dev-list',help='list storage phy-pool')
    #devlist_parser.add_argument('--type', required=True, help='localfs/nfs/glusterfs/uus')
    #devlist_parser.add_argument('--url', required=True, help='localfs:available or all \n nfs:ip/sharename \nglusterfs:ip/volname \nuus:ip:port/poolname')
    #devlist_parser.set_defaults(func=dev_list)
    
    poollist_parser = sub_parser.add_parser('pool-list',help='list storage pool')
    #poollist_parser.add_argument('--type', required=False, help='localfs/nfs/glusterfs/uus')
    #poollist_parser.add_argument('--url', required=False, help='list all pool added at this node')
    poollist_parser.set_defaults(func=pool_list)
    
    pooladd_parser = sub_parser.add_parser('pool-add',help='add storage pool')
    pooladd_parser.add_argument('--type', required=True, help='localfs nfs glusterfs vdiskfs uus')
    pooladd_parser.add_argument('--poolname', required=True, help='poolname')
    pooladd_parser.add_argument('--url', required=True, help='/mnt/localfs/xxx  ip:nfs-sharename  ip:gluster-volumename vdiskfs-name ip:uus-poolname')
    pooladd_parser.add_argument('--opt', required=False, help='comma separated key=val  see mount.nfs mount.glusterfs uus-type:iscsi,iscsi-fast,dev,dev-fast  e.g. iscsi,username=xxx,password=xxx,port=7000')
    pooladd_parser.add_argument('--uuid', required=False, help='pool uuid as node id  k8s save map uuid-->node-poolname  localfs except')
    pooladd_parser.set_defaults(func=pool_add)
    
    poolactive_parser = sub_parser.add_parser('pool-active',help='active pool')
    poolactive_parser.add_argument('--poolname', required=True, help='poolname')
    poolactive_parser.set_defaults(func=pool_active)
    
    #pooladd_local_parser = sub_parser.add_parser('pooladd-localfs',help='add local storage pool')
    #pooladd_local_parser.add_argument('--poolname', required=True, help='poolname')
    #pooladd_local_parser.add_argument('--url', required=True, help='url  /mnt/localfs/xxx')
    #pooladd_local_parser.set_defaults(func=pooladd_local)
    
    #pooladd_nfs_parser = sub_parser.add_parser('pooladd-nfs',help='add nfs storage pool')
    #pooladd_nfs_parser.add_argument('--poolname', required=True, help='poolname')
    #pooladd_nfs_parser.add_argument('--url', required=True, help='url ip:/sharename')
    #pooladd_nfs_parser.add_argument('--path', required=False, help='mount path')
    #pooladd_nfs_parser.add_argument('--opt', required=False, help='comma separated key=val')
    #pooladd_nfs_parser.set_defaults(func=pooladd_nfs)
    
    #pooladd_glusterfs_parser = sub_parser.add_parser('pooladd-glusterfs',help='add glusterfs storage pool')
    #pooladd_glusterfs_parser.add_argument('--poolname', required=True, help='poolname')
    #pooladd_glusterfs_parser.add_argument('--url', required=True, help='url ip:volname ')
    #pooladd_glusterfs_parser.add_argument('--path', required=False, help='mount path')
    #pooladd_glusterfs_parser.add_argument('--opt', required=False, help='comma separated key=val')
    #pooladd_glusterfs_parser.set_defaults(func=pooladd_glusterfs)
    
    #pooladd_uus_parser = sub_parser.add_parser('pooladd-uus',help='add uus storage pool')
    #pooladd_uus_parser.add_argument('--poolname', required=True, help='poolname')
    #pooladd_uus_parser.add_argument('--url', required=True, help='url ip:phy-poolname')
    #pooladd_uus_parser.add_argument('--opt', required=True, help='type:iscsi,iscsi-fast,dev,dev-fast  e.g. iscsi,username=admin,password=admin,port=7000 ')
    #pooladd_uus_parser.set_defaults(func=pooladd_uus)
    
    #pooladd_uraid_parser = sub_parser.add_parser('pooladd-vdiskfs',help='add vdiskfs storage pool')
    #pooladd_uraid_parser.add_argument('--poolname', required=True, help='poolname')
    #pooladd_uraid_parser.add_argument('--url', required=True, help='url vdiskfs volname or prefix name')
    #pooladd_uraid_parser.add_argument('--force', required=False, help='force add vdiskfs pool do not check mount')
    #pooladd_uraid_parser.set_defaults(func=pooladd_uraid)
    
    poolshow_parser = sub_parser.add_parser('pool-show',help='show storage pool')
    poolshow_parser.add_argument('--poolname', required=True, help='poolname')
    poolshow_parser.set_defaults(func=pool_show)
    
    poolremove_parser = sub_parser.add_parser('pool-remove',help='remove storage pool')
    poolremove_parser.add_argument('--poolname', required=True, help='poolname')
    poolremove_parser.set_defaults(func=pool_remove)
    
    poolsetstatus_parser = sub_parser.add_parser('pool-set-status',help='remove storage pool')
    poolsetstatus_parser.add_argument('--poolname', required=True, help='poolname')
    poolsetstatus_parser.add_argument('--status', required=True, help='normal/maintain')
    poolsetstatus_parser.set_defaults(func=pool_set_status)
    
    ##########################
    
    ##############create##################
    create_parser = sub_parser.add_parser('vdisk-create',help='create volume')
    create_parser.add_argument('--poolname', required=True, help='storage pool')
    create_parser.add_argument('--name', required=True, help='volume name')
    create_parser.add_argument('--size', required=True, help='volume size M G T,default B')
    #create_parser.add_argument('--type', required=False, help='default qcow2, raw, block')
    create_parser.set_defaults(func=create_volume)
    
    ##############remove##################
    remove_parser = sub_parser.add_parser('vdisk-remove', help='remove volume')
    remove_parser.add_argument('--poolname', required=True, help='storage pool')
    remove_parser.add_argument('--name', required=True, help='volume name') 
    remove_parser.set_defaults(func=remove_volume)
    
    ################show###################
    show_parser = sub_parser.add_parser('vdisk-show', help='show volume info')
    show_parser.add_argument('--poolname', required=True, help='storage pool')
    show_parser.add_argument('--name', required=True, help='volume name')   
    show_parser.set_defaults(func=show_volume)
    
    ################expand###################
    expand_parser = sub_parser.add_parser('vdisk-expand',help='expand volume to new size')
    expand_parser.add_argument('--poolname', required=True, help='storage pool')
    expand_parser.add_argument('--name', required=True, help='volume name')
    expand_parser.add_argument('--size', required=True, help='volume new size M G T,default B')
    expand_parser.add_argument('--vmname', required=False, help='live vmname')
    expand_parser.set_defaults(func=expand_volume)
    
    ################add snapshot###################
    add_ss_parser = sub_parser.add_parser('vdisk-add-ss',help='create volume snapshot')
    add_ss_parser.add_argument('--poolname', required=True, help='storage pool')
    add_ss_parser.add_argument('--name', required=True, help='volume name')
    add_ss_parser.add_argument('--sname', required=True, help='snapshot name')
    add_ss_parser.add_argument('--vmname', required=False, help='live vmname')      
    add_ss_parser.set_defaults(func=add_volume_snapshot)
    
    ################show snapshot###################
    show_ss_parser = sub_parser.add_parser('vdisk-show-ss',help='create volume snapshot')
    show_ss_parser.add_argument('--poolname', required=True, help='storage pool')
    show_ss_parser.add_argument('--name', required=True, help='volume name')
    show_ss_parser.add_argument('--sname', required=True, help='snapshot name') 
    show_ss_parser.add_argument('--vmname', required=False, help='live vmname')     
    show_ss_parser.set_defaults(func=show_volume_snapshot)
    
    ################recover snapshot###################
    recover_ss_parser = sub_parser.add_parser('vdisk-rr-ss',help='recover volume snapshot')
    recover_ss_parser.add_argument('--poolname', required=True, help='storage pool')
    recover_ss_parser.add_argument('--name', required=True, help='volume name')
    recover_ss_parser.add_argument('--sname', required=True, help='snapshot name')
    recover_ss_parser.add_argument('--vmname', required=False, help='live vmname')  
    recover_ss_parser.set_defaults(func=recover_volume_snapshot)
    
    ################remvoe snapshot###################
    rm_ss_parser = sub_parser.add_parser('vdisk-rm-ss',help='remove volume snapshot')
    rm_ss_parser.add_argument('--poolname', required=True, help='storage pool')
    rm_ss_parser.add_argument('--name', required=True, help='volume name')
    rm_ss_parser.add_argument('--sname', required=True, help='snapshot name')
    rm_ss_parser.add_argument('--vmname', required=False, help='live vmname')   
    rm_ss_parser.set_defaults(func=remove_volume_snapshot)
    
    ################clone##################
    clone_parser = sub_parser.add_parser('vdisk-clone',help='clone volume')
    clone_parser.add_argument('--poolname', required=True, help='storage pool')
    clone_parser.add_argument('--name', required=True, help='volume name')
    clone_parser.add_argument('--clonename', required=True, help='clone name')
    clone_parser.add_argument('--vmname', required=False, help='live vmname')
    clone_parser.set_defaults(func=clone_volume)    
    
    affinity_parser = sub_parser.add_parser('vdisk-affinity',help='set disk affinity')
    affinity_parser.add_argument('--uuid', required=True, help='vm uuid')
    affinity_parser.add_argument('--name', required=True, help='vdisk name  comma separated')
    affinity_parser.set_defaults(func=affinity_volume)
    
    ##############prepare vol##############
    prep_vol_parser = sub_parser.add_parser('vdisk-prepare',help='connect volume')
    prep_vol_parser.add_argument('--poolname', required=True, help='storage pool')
    prep_vol_parser.add_argument('--name', required=True, help='volume name')
    prep_vol_parser.add_argument('--uni', required=True, help='volume or snapshot uni')
    prep_vol_parser.add_argument('--sname', required=False, help='snapshot name')
    prep_vol_parser.set_defaults(func=prepare_volume)
    
    ##############release vol##############
    release_vol_parser = sub_parser.add_parser('vdisk-release',help='connect volume')
    release_vol_parser.add_argument('--poolname', required=True, help='storage pool')
    release_vol_parser.add_argument('--name', required=True, help='volume name')
    release_vol_parser.add_argument('--uni', required=True, help='volume or snapshot uni')
    release_vol_parser.add_argument('--sname', required=False, help='snapshot name')
    release_vol_parser.set_defaults(func=release_volume)
    ##########################################################

    args = parser.parse_args()
    args.func(args)


def json_load_file(path, filename):
    fullname = '%s/%s' % (path, filename)
    if not path_exist(CSTOR_POOL):
        mkdir_p(CSTOR_POOL)
    if not path_exist(fullname):
        return {}
        
    load_dict = {}
    with open(fullname, 'r') as f:
        load_dict = json.load(f)
        if load_dict and path == CSTOR_POOL:
            if not load_dict.has_key('maintain'):
                if load_dict.has_key('maintenance'):
                    load_dict['maintain'] = load_dict['maintenance']
                    del load_dict['maintenance']
                else:
                   load_dict['maintain'] = 'normal'
                   
                json_dump_file(path, filename, load_dict)
                           
    return load_dict    

def json_dump_file(path, filename, new_dict):
    fullname = '%s/%s' % (path, filename)
    if not path_exist(CSTOR_POOL):
        mkdir_p(CSTOR_POOL)
        
    with open(fullname, "w") as f:
        json.dump(new_dict,f)
    return 0

def file_read_str(path, filename):
    fullname = '%s/%s' % (path, filename)
    f = open(fullname, "r")
    str1 = f.read()
    f.close()
    return str1

def file_write_str(path, filename, str1):
    fullname = '%s/%s' % (path, filename)
    f = open(fullname, "w")
    f.write(str1)
    f.close()
    
def path_exist(p):
    return os.path.exists(p)

def path_exist_sh(p):
    cmd = 'timeout  --preserve-status --foreground 5 ls -d %s >/dev/null' % p
    return exec_system(cmd)

def mkdir_p(path):
    err = 1
    try:
        os.makedirs(path)
        os.chmod(path, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        err = 0
    except OSError as e:
        if e.errno == 17:
            err = 0
    return err  
    
def execcmd_str(cmd):
    process = os.popen(cmd) # return file
    restr = process.read()
    process.close()
    return restr
    
def exec_system(cmd):
    err = os.system(cmd)
    if not err:
        err = 0
    else:
        err = err >> 8
    return err

def execcmd_json(cmd):
    process = os.popen(cmd) # return file
    restr = process.read()
    process.close()
    result = {}
    result['msg'] = 'no output'
    result['code'] = 200
    rj = {}
    rj['result'] = result
    rj['data'] = {}
    if restr:
        rj = json.loads(restr)
    return rj   
    
def get_resultjson(errcode, errmsg, objtag):
     rj = """ {"result":{"code":%d, "msg":"%s"}, "data":{}, "obj":"%s"} """ % (errcode, errmsg, objtag)
     
     return rj
     
def get_resultjson_errcode(jsonobj):
    err = -1
    if isinstance(jsonobj, dict) and jsonobj.has_key('result'):
        resultobj = jsonobj['result']
        err = resultobj['code']
    return err      
     
def print_resultjson(errcode, errmsg, objtag):
     rj = """ {"result":{"code":%d, "msg":"%s"}, "data":{}, "obj":"%s"} """ % (errcode, errmsg, objtag)
     print rj
     return errcode
    
def print_datajson(errcode, errmsg, objtag, obj_dict):
    jsonobj = json.dumps(obj_dict)
    rj = """ {"result":{"code":%d, "msg":"%s"}, "data":%s, "obj":"%s"} """ % (errcode, errmsg, jsonobj, objtag)
    print rj
    return errcode

def create_file_vdisk(filepath, size, ftype):
    #qemu-img create -f qcow2 /root/vm/uus.qcow2 40G
    if path_exist(filepath):
        return 1
    cmd_str = 'qemu-img create -f %s %s %sG >/dev/null' % (ftype, filepath, size)
    return exec_system(cmd_str)

def rm_file_empty_dir(path):
    err = 1
    if os.path.isfile(path):
        try:
           os.remove(path)
           err = 0
        except OSError as e:
            if e.errno == 2:
                err = 0    
    elif os.path.isdir(path):   
        #try:
        #    shutil.rmtree(path)
        #    err = 0
        #except OSError as e:
        #    if e.errno == 2:
        #        err = 0
        try :
            os.rmdir(path)
            err = 0
        except OSError as e:
            if e.errno == 2:
                err = 0     
    else:
        if not os.path.exists(path):
            err = 0
                
    return err

def get_opt_param(optarray, pname):
    #param = ('', '')
    param = ''
    if pname == 'uus-type':
        for item in optarray:
            if item == 'iscsi' or item  == 'iscsi-fast' or item  == 'dev' or item  == 'dev-fast':
                param = item
                break
    else:   
        for item in optarray:
            if item.find(pname) == 0:
                item = item.split('=')
                if len(item) == 1:
                    param = item[0]
                else:
                    param = item[1]
                break
                
    return param


def open_with_lock(filename):
    f = open(filename, "r+")
    
    while 1:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except:
            time.sleep(0.2)
        
    return f

def fstab_remove_line(rm_mount_path):
    
    err = 1
    filename = '/etc/fstab'
    f = open_with_lock(filename)
    
    lines = f.readlines()
    
    #index1 = 0
    for item in lines:
        col = item.split()
        if len(col) != 6:
            continue
            
        mounturl = col[0]
        mountpath = col[1]
        mountfs = col[2]
        if mounturl[0] != '#' and (mountfs == 'nfs' or mountfs == 'glusterfs') and mountpath == rm_mount_path:
            err = 0
            #del lines[index1]
            lines.remove(item)
            break
        #else:
        #    index1 += 1
            
    if not err:        
        f.seek(0)
        f.truncate(0)
        
        f.writelines(lines)
        
        
    fcntl.flock(f, fcntl.LOCK_UN)
    f.close()
    return err
    
def fstab_add_line(mount_url, add_mount_path, mount_fs, mount_opt):
    
    err = 0
    filename = '/etc/fstab'
    f = open_with_lock(filename)
    
    lines = f.readlines()
    
    #index1 = 0
    for item in lines:
        col = item.split()
        if len(col) != 6:
            continue
            
        mounturl = col[0]
        mountpath = col[1]
        mountfs = col[2]
        
        if mounturl[0] != '#' and (mountfs == 'nfs' or mountfs == 'glusterfs') and mountpath == add_mount_path:
            err = 1
            break
        #else:
        #    index1 += 1
            
    if not err:        
        f.seek(0)
        f.truncate(0)
        
        if not mount_opt or mount_opt == '':
            mount_opt = 'defaults'
        line = '%s %s %s %s 0 0\n' % (mount_url, add_mount_path, mount_fs, mount_opt)
        lines.append(line)
        f.writelines(lines)
        
    f.close()
    return err    
############################################    
def localfs_dev_pool(all, dirname):
    
    mountlist = []
    
    if dirname != '' and path_exist(CSTOR_LOCALFS_POOL_TEST):
        devname = '/dev/just-test'
        mountpath = dirname
        add_item = 'localfs://%s:%s' % (devname, mountpath)
        add_dict = {'url':add_item, 'tag': devname}
        add_dict.update(get_mount_used(mountpath))
        mountlist.append(add_dict)
    else:
        cmd = 'mount|grep "/dev/sd\|/root/loopfile.img"'
        lines = execcmd_str(cmd)
        for line in lines.split('\n'):
            if line :
                line = line.split()
                devname = line[0]
                mountpath = line[2]
                if mountpath.find('/mnt/localfs/') == 0:#mountpath != '/' and mountpath != '/boot':
                    if not all:
                       cmd = 'ls %s/.cstor-tag* >/dev/null' % (mountpath)
                       if exec_system(cmd):
                            add_item = 'localfs://%s:%s' % (devname, mountpath)
                            add_dict = {'url':add_item, 'tag': devname}
                            add_dict.update(get_mount_used(mountpath))
                            
                            mountlist.append(add_dict)
                    else:
                        add_item = 'localfs://%s:%s' % (devname, mountpath)
                        add_dict = {'url':add_item, 'tag': devname}
                        add_dict.update(get_mount_used(mountpath))
                        mountlist.append(add_dict)
            
    return mountlist

def get_nfs_gluster_dev_pool(proto, url):
    tmppath = '/tmp/cstor/%d' % os.getpid() 
    mkdir_p(tmppath)
    cmd = 'mount -t %s %s %s >/dev/null' % (proto, url, tmppath)
    err = exec_system(cmd)
    
    used = {}
    
    if err:
        used = get_inactive_used()
        
    else:
        if proto == NFS:
            used = get_mount_used_nfs(tmppath, url)
        else:
            used = get_mount_used(tmppath)
            
        cmd = 'umount %s' % tmppath
        exec_system(cmd)
        rm_file_empty_dir(tmppath)

    return used 
    
def uus_parse_url(url):
    #uname:pwd@ip:port
    conf = url.split('@')
    ip = conf[1]
    user = conf[0].split(':')
    uname = user[0]
    pwd = user[1]
    return (uname, pwd, ip)
    
def uus_dev_pool(url):
    '''
    /etc/sysconfig/cstor/uus.conf
    {
        "uus-iscsi-independent":{"n":4,"m":2,"k":0,"strip":32,"prealloc":1,"tag":"uus-iscsi-fast","export-mode":"3"},
        "uus-iscsi":{"n":4,"m":2,"k":0,"strip":32,"prealloc":1,"tag":"uus-iscsi","export-mode":"3"},
        "uus-dev-independent":{"n":4,"m":2,"k":0,"strip":32,"prealloc":1,"tag":"uus-dev-fast","export-mode":"3"},
        "uus-dev":{"n":4,"m":2,"k":0,"strip":32,"prealloc":1,"tag":"uus-dev","export-mode":"3"}
    }
    '''
    #oldurl ip:port/poolname
    #neturl user:pwd@ip:port
    import base64
    
    ret = []    
    
    uname, pwd, ip = uus_parse_url(url)
    upwd = base64.b64encode(pwd)
    
    cmd = 'curl http://%s/uraidapi/pool/list?tmptoken=%s@@%s 2>/dev/null' % (ip, uname, upwd)
    jsonobj = execcmd_json(cmd)
    
    uus_conf = json_load_file(CSTOR_DIR, 'uus.conf')
    
    if jsonobj and uus_conf:
        err = get_resultjson_errcode(jsonobj)
        if not err:
            data_arr = jsonobj['data']
            for poolobj in data_arr:
                poolname = poolobj['pool_name']
                cap_total = poolobj['cap_total'] * 1000000000000
                cap_free = poolobj['cap_free'] * 1000000000000
                cap_used = cap_total - cap_free             
       
                for key,val in uus_conf.items():
                    item = {}
                    item['url'] = '%s://%s:%s@%s/%s/%d/%d/%d/%d/%d/%s' % (key, uname, pwd, ip, poolname, val['n'], val['m'], val['k'], val['strip'], val['prealloc'], val['export-mode'])
                    item['total'] = cap_total
                    item['free'] = cap_free
                    item['used'] = cap_used
                    item['tag'] = '%s@%s' % (val['tag'], poolname)
                    item['status'] = 'active'
                    ret.append(item)    
    return ret

def uraid_dev_pool(all):
    #cmd = 'OFMT=JSON ucli vol list local mount gluster'
    cmd = 'perl /usr/lib/uraid/scripts/vols/callfun usb_get_volumes_json ,1,1,gluster,notused'
    rj = execcmd_json(cmd)
    mountlist = []
    if rj.has_key('data'):
        all_dev = rj['data']
        for json_dev in all_dev:
            dev = json_dev['device_path']
            mountpath = json_dev['mount_path']
            devname = json_dev['name']
            if not all:
                cmd = 'ls %s/.cstor-tag* >/dev/null' % (mountpath)
                if exec_system(cmd):
                    add_item = 'uraid://%s:%s' % (dev, mountpath)                   
                    add_dict = {'url':add_item, 'tag': devname}
                    add_dict.update(get_mount_used(mountpath))
                    
                    mountlist.append(add_dict)
            else:
                add_item = 'uraid://%s:%s' % (dev, mountpath)
                add_dict = {'url':add_item, 'tag': devname}
                add_dict.update(get_mount_used(mountpath))
                mountlist.append(add_dict)
                    
    return mountlist    

######################################  
def get_inactive_used():
    used = {}
    used['total'] = 0
    used['used'] = 0
    used['free'] = 0
    used['status'] = 'inactive'
    return used
    
def get_mount_used(dir):
    cmd = 'timeout --preserve-status --foreground 10 df  %s|grep -v Filesystem' % dir
    strused = execcmd_str(cmd)
    used = {}
    if strused:
        ua = strused.split()
        used['total'] = long(ua[1]) << 10
        used['used'] = long(ua[2]) << 10
        used['free'] = long(ua[3]) << 10
        used['status'] = 'active'
    else:
        used = get_inactive_used()
    return used

def get_mount_used_nfs(dir, url):
    url = url.split(':')
    cmd = 'timeout --preserve-status --foreground 60 showmount -e %s|grep "%s " >/dev/null' % (url[0], url[1])
    if exec_system(cmd) == 0:
        cmd = 'df  %s|grep -v Filesystem' % dir
        strused = execcmd_str(cmd)
        used = {}
        if strused:
            ua = strused.split()
            used['total'] = long(ua[1]) << 10
            used['used'] = long(ua[2]) << 10
            used['free'] = long(ua[3]) << 10
            used['status'] = 'active'
        else:
            used = get_inactive_used()
    else:
        used = get_inactive_used()
    return used

def get_callid():
    cid = random.randint(1, 10000)
    return 'CALLID=%d' % cid

def get_uusmount_used(pool_desc, poolname):
    ret = get_inactive_used()
    jsonobj = uus_make_http_request(pool_desc, 'pool', 'list', '', 1, '0')
    if jsonobj:
        err = get_resultjson_errcode(jsonobj)
        if not err:
            data_arr = jsonobj['data']
            
            for poolobj in data_arr:
                if poolname and poolname != poolobj['pool_name']:
                    continue
                #poolname = poolobj['pool_name']
                cap_total = poolobj['cap_total'] * 1000000000000
                cap_free = poolobj['cap_free'] * 1000000000000
                cap_used = cap_total - cap_free
                item = {}
                item['total'] = cap_total
                item['free'] = cap_free
                item['used'] = cap_used
                item['status'] = 'active'
                ret = item
                break
    return ret

def prepare_uraid(uraidname):
    err = 0
    is_runing = 0

        
    cur_nodeid = uus_node_id()
    if cur_nodeid <= 0:
        err = 100
    else:
        cmd = 'OFMT=JSON ucli vol show %s' % uraidname
        rj = execcmd_json(cmd)
        #print cmd
        if not rj:
            err = 100
        else:
            err = rj['result']['code']
            if err: #not exist
                err = 100
            else:
                dataobj = rj['data'][0]
                
                if not dataobj.has_key('now_host'): 
                    is_runing = 0
                else:#uraid is run
                    active_node = dataobj['now_host']
                    
                    if active_node > 0 and cur_nodeid != active_node: #run at other node
                        cmd = 'env %s node=%d ucli vol stop %s >/dev/null' % (get_callid(), active_node, uraidname)
                        err = exec_system(cmd)
                        #print cmd
                        if not err:
                            is_runing = 0
                    else:
                        is_runing = 1 #run at this node                    
                    
                if not err and not is_runing: #need run at this node
                    cmd = '%s ucli vol run %s >/dev/null' % (get_callid(), uraidname)
                    err = exec_system(cmd)
                    #print cmd
                    if not err:
                        #wait mount
                        sleep_cnt = 100
                        cmd = 'mount |grep "/mnt/usb/%s type" >/dev/null' % uraidname
                        while sleep_cnt > 0:
                            err = exec_system(cmd)
                            if not err:
                                is_runing = 1
                                break
                            else:
                                time.sleep(0.1)
                                sleep_cnt = sleep_cnt - 1
    
    if not is_runing:
        err = 100
    
    return err
    
#only used in  pool_add  pool_get_json  
def check_mount(pool_desc, force_run):
    proto = pool_desc['proto']
    poolname = pool_desc['poolname']
    url = pool_desc['url']    
    
    if proto == LOCAL_FS:
        path = pool_desc['mountpath'] 
        if not path_exist(CSTOR_LOCALFS_POOL_TEST):
            cmd = 'mount |grep "on %s type " >/dev/null' % path
            err = exec_system(cmd)
            if err:
                return 100
        return 0
    elif proto == NFS or proto == GLUSTERFS:
        path = pool_desc['mountpath']
        
        if path[-1] == '/':
            path = path[0:-1]

        err = path_exist_sh(path)
        if err == 2:
            mkdir_p(path)
        elif err == 143:
            return 100
            
        opt = ''
        if pool_desc.has_key('opt') and pool_desc['opt']:
            opt = ' -o %s' % pool_desc['opt']
            
        #cmd = 'mount |grep "%s on %s type nfs" >/dev/null' % (url, path)
        cmd = 'mount |grep " on %s type nfs" >/dev/null' % (path)
        
        if proto == GLUSTERFS:
            cmd = 'mount |grep "%s on %s type fuse.glusterfs" >/dev/null' % (url, path)

        
        if exec_system(cmd):            
            #mkdir_p(path)           
            cmd = 'timeout --preserve-status --foreground 5 mount -t %s %s %s %s >/dev/null' % (proto, opt, url, path)
            err = exec_system(cmd)
            if err:
                return 100 #print_resultjson(100, 'failed', 'check mount')

        return 0
    elif proto == UUS:
        #make sure link dir
        
        if not pool_desc.has_key('mountpath') or pool_desc['mountpath'] == '':
             pool_desc['mountpath'] = '%s/%s' % (DEF_BASE_MNT_PATH, poolname)
             
        path = pool_desc['mountpath']
        if not path_exist(path):
            mkdir_p(path)
        return 0
    elif proto == URAID:
        
        path = pool_desc['mountpath']
        uraidname = path.split('/')[3]
        
        cmd = 'mount |grep "/mnt/usb/%s type" >/dev/null' % uraidname
        err = exec_system(cmd)
        
        if err:
            if not force_run:
                # make sure vdisk exist, not mounted vdisk pool is inactive
                '''cmd = 'OFMT=JSON ucli vol show %s' % uraidname
                rj = execcmd_json(cmd)
                # print cmd
                if not rj:
                    err = 100
                else:
                    err = rj['result']['code']
                    if err:  # not exist
                        err = 100
                    else:
                        err = 0
                        dirname = '/mnt/usb/%s' % uraidname
                        if not path_exist(dirname):
                            mkdir_p(dirname)
                '''
                if not path_exist(path):
                    mkdir_p(path)
                err = 100
                return err
            else:
                return prepare_uraid(uraidname)
        return 0            
            
    return 1

def pool_add(args):
    args_dict = vars(args)
    pooltype = args_dict['type']
    poolurl = args_dict['url']
    
    if poolurl.find('//') >= 0 or poolurl[-1:] == '/':
        return print_resultjson(110, 'invalid url', poolname)
    
    if pooltype == 'localfs':
        return pooladd_localfs(args_dict)
    elif pooltype == 'nfs':
        return pooladd_nfs(args_dict)
    elif pooltype == 'glusterfs':
        return pooladd_glusterfs(args_dict)
    elif pooltype == 'vdiskfs':
        return pooladd_vdiskfs(args_dict)
    elif pooltype == 'uus':
        return pooladd_uus(args_dict)
    
    return print_resultjson(115, 'invalid type', 'pool-add')
    
def pool_add_inter(poolname, data, force_add):
    
    mount_exist = 1
    filename = '%s/%s' % (CSTOR_POOL, poolname)
    if path_exist(filename):
        return print_resultjson(106, 'pool exist', poolname)
    
    data['poolname'] = poolname
    data['maintain'] = 'normal'
    err = check_mount(data, 0)
    if err:
        if not force_add:
            return print_resultjson(err, 'failed', 'check mount')
        else:
            mount_exist = 0
            
    if data['disktype'] == 'file' and mount_exist:       
        
        mountpath = data['mountpath'] 
        if not path_exist(mountpath):
            mkdir_p(mountpath)
        
        if not path_exist(mountpath):
             return print_resultjson(107, 'mount path not exist', poolname)
        
        cmd = 'touch %s/.cstor-tag.%s >/dev/null' % (mountpath, poolname)
        err = exec_system(cmd)
        if err:
            return print_resultjson(108, 'pool create failed', poolname)
            
        pooldatadir = '%s/%s' % (mountpath, poolname)
        mkdir_p(pooldatadir)
        
    json_dump_file(CSTOR_POOL, poolname, data)
    
    pooljson = pool_get_json(poolname, 1, 0, 0)
    return print_datajson(0, 'success', 'pooladd', pooljson)
    
def pooladd_localfs(args_dict):
    #args_dict = vars(args)
    poolname = args_dict['poolname']
    url = args_dict['url'] #old url localfs:///dev/sda2:/etc/uraid
    #new url /mnt/localfs/abc
    puuid = args_dict['uuid']
    
    if len(url) <= 13 or url.find('/mnt/localfs/') != 0 or not path_exist(url):
        return print_resultjson(110, 'invalid url', poolname)
        
    mountdev = 'test'
    if not path_exist(CSTOR_LOCALFS_POOL_TEST):
        cmdstr = 'mount |grep "%s "' % url
        mountdevstr = execcmd_str(cmdstr)
        if len(mountdevstr) < 3:
            err = 101
            strmsg = 'not a mount point'
            return print_resultjson(err, strmsg, 'pool-add')  
            
        mountdev =  mountdevstr.split()[0]    
    
    data = {}
    #url = url[10:].split(':')
    data['url'] = mountdev#url[0] #/dev/sda2
    data['proto'] = LOCAL_FS
    data['disktype'] = 'file'
    data['mountpath'] = url #url[1]
    data['uuid'] = puuid
    
    return pool_add_inter(poolname, data, 0)
    
def pooladd_nfs(args_dict):
    #args_dict = vars(args)
    poolname = args_dict['poolname']
    url = args_dict['url'] #old url nfs://ip:/sharename
    #new url ip:/sharename

    mountopt = args_dict['opt']
    puuid = args_dict['uuid']
    
    if not puuid:
        err = 113
        strmsg = 'invalid uuid'
        return print_resultjson(err, strmsg, 'pool-add')  
    
    if not mountopt:
        mountopt = ''
    
    data = {}
    data['url'] = url#[6:]
    data['proto'] = NFS
    data['opt'] = mountopt
    data['disktype'] = 'file'
    data['uuid'] = puuid    
    mountpath = '%s/%s' % (DEF_BASE_MNT_PATH, poolname)   
    data['mountpath'] = mountpath
    
    err = pool_add_inter(poolname, data, 0)
    if not err:
        fstab_add_line(url, mountpath, NFS, mountopt)   
    return err  
    
def pooladd_glusterfs(args_dict):
    #args_dict = vars(args)
    poolname = args_dict['poolname']
    url = args_dict['url'] #old url glusterfs://ip:volname
    #new url ip:volname
    mountopt = args_dict['opt']
    puuid = args_dict['uuid']
    
    if not puuid:
        err = 113
        strmsg = 'invalid uuid'
        return print_resultjson(err, strmsg, 'pool-add') 
    
    if not mountopt:
        mountopt = ''
    
    data = {}
    data['url'] = url#[12:]
    data['proto'] = GLUSTERFS
    data['opt'] = mountopt
    data['disktype'] = 'file'
    data['uuid'] = puuid
    mountpath = '%s/%s' % (DEF_BASE_MNT_PATH, poolname)   
    data['mountpath'] = mountpath
       
    err = pool_add_inter(poolname, data, 0)
    if not err:
        fstab_add_line(url, mountpath, GLUSTERFS, mountopt)
    return err  
    
def pooladd_uus(args_dict):
    #args_dict = vars(args)
    poolname = args_dict['poolname']
    url = args_dict['url']
    opt = args_dict['opt'].split(',')
    
    puuid = args_dict['uuid']
    
    if not puuid:
        err = 113
        strmsg = 'invalid uuid'
        return print_resultjson(err, strmsg, 'pool-add') 
    
    #user = args_dict['user']
    #pwd = args_dict['pwd']    
    #old url uus-iscsi://test:123456@172.18.70.214:7000/test/4/2/0/32(strip)/1(prealloc)/3(iscsimode)
    #new url ip:phy-pool
    #option iscsi,username=admin,password=admin,port=7000 (iscsi,iscsi-fast,dev,dev-fast)
    url1 = url.split(':')
    if len(url1) != 2:
        return print_resultjson(110, 'invalid url', poolname)
    uusvip = url1[0]
    uusport = '7000'
    phy_pool = url1[1]
    
    uustype = get_opt_param(opt, 'uus-type')
    if not uustype:
        return print_resultjson(114, 'invalid option', poolname)
    
    blocktype = uustype.split('-')#url[0:pos].split('-') #uus-iscsi-independent uus-iscsi uus-dev-independent uus-dev
    len_block = len(blocktype)
    if len_block != 1 and len_block != 2:
        return print_resultjson(114, 'invalid opton', poolname)
    
    if blocktype[0] != 'iscsi' and blocktype[0] != 'dev':
        return print_resultjson(114, 'invalid option', poolname)
        
    conf_key = 'uus-%s' % blocktype[0]    
    if len_block == 2:
        if blocktype[1] != 'fast':
            return print_resultjson(114, 'invalid option', poolname)
        conf_key = '%s-independent' % conf_key
    
    uname = get_opt_param(opt, 'username')
    upwd = get_opt_param(opt, 'password')
    optport = get_opt_param(opt, 'port')
    if optport:
        uusport = optport
    
    if uname == '' or upwd == '':
        return print_resultjson(114, 'invalid option', poolname)
    
    
    uus_conf = json_load_file(CSTOR_DIR, 'uus.conf')
    uus_key_conf = uus_conf[conf_key]
    
    data = {}
    data['url'] = url
    data['proto'] = UUS
    data['disktype'] = 'uus_%s' % (blocktype[0]) #iscsi or dev
    data['prealloc'] = uus_key_conf['prealloc']
    
    if len(blocktype) == 1:
        data['blocktype'] = 'lvm'
    else:
        data['blocktype'] = 'raw'
        
    data['user'] = uname
    data['pwd'] = upwd
    data['ip'] = '%s:%s' % (uusvip, uusport)
    data['inter_poolname'] = phy_pool
    data['nmk_strip'] = '%s %s %s %s' % (uus_key_conf['n'], uus_key_conf['m'], uus_key_conf['k'], uus_key_conf['strip'])
    data['export-mode'] = uus_key_conf['export-mode']
    mountpath = '%s/%s' % (DEF_BASE_MNT_PATH, poolname)
    data['mountpath'] = mountpath
    data['uuid'] = puuid
    
    
    return pool_add_inter(poolname, data, 0) 

def pooladd_vdiskfs(args_dict):
    #args_dict = vars(args)
    poolname = args_dict['poolname']
    url = args_dict['url'] #old url uraid://%s:%s' % (dev, mountpath)
    #new url volname
    
    puuid = args_dict['uuid']
    
    if not puuid:
        err = 113
        strmsg = 'invalid uuid'
        return print_resultjson(err, strmsg, 'pool-add')
    
    #get uraid devname and mount path   
    #match prefix
    #cmd = 'perl /usr/lib/uraid/scripts/vols/callfun usb_get_volumes_json ,1,1,gluster,notused'
    #json_out = execcmd_json(cmd)
    #json_conf = ''
    #if json_out.has_key('data') and len(json_out['data']) > 0:
    #    for item in json_out['data']:
    #        if item['name'].find(url) == 0:
    #            json_conf = item
    #            break
    #    if json_conf == '':
    #        return print_resultjson(110, 'invalid url', poolname)
    #else:
    #    return print_resultjson(110, 'invalid url', poolname)
        
    cmd = 'OFMT=JSON ucli vol show %s' % url
    json_out = execcmd_json(cmd)
    json_conf = ''
    if json_out.has_key('data') and len(json_out['data']) > 0:
        json_conf = json_out['data'][0]
    else:
        return print_resultjson(110, 'invalid url', poolname)

    if (not json_conf.has_key('mount_path')) or json_conf['mount_path'] == '' or json_conf['mount_path'] == None:
        return print_resultjson(107, 'mount path not exist', poolname)


    data = {}
    data['url'] = url#json_conf['device_path'] url[0]
    data['proto'] = URAID
    data['disktype'] = 'file'
    data['mountpath'] = json_conf['mount_path']#url[1]
    data['uuid'] = puuid
    
    return pool_add_inter(poolname, data, 1) 

def pool_active(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']
    pooljson = pool_get_json(poolname, 1, 1, 0)
    err = 0
    msg = 'success'
    if not pooljson:
        err = 101
        msg = 'pool not exist'
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
        
    return print_datajson(err, msg, 'poolactive', pooljson)
    
def pool_get_json(poolname, show_used, force_run, inter_call):
    pooljson = json_load_file(CSTOR_POOL, poolname)
    if pooljson:
        poolused = {}
        if check_mount(pooljson, force_run):
            if not inter_call and pooljson['proto'] == UUS:
                pooljson['url'] = '%s://%s' % (pooljson['disktype'], pooljson['ip'])
                del pooljson['inter_poolname']
                del pooljson['blocktype']
                del pooljson['ip']
                del pooljson['nmk_strip']
                del pooljson['prealloc']
                del pooljson['user']
                del pooljson['pwd']
                if pooljson.has_key('export-mode'):
                    del pooljson['export-mode']
                    
            pooljson.update(get_inactive_used())
            return pooljson
        
        if not show_used:
            pooljson['status'] = 'active'
            
        if pooljson['disktype'] == 'file':
            if show_used:
                if pooljson['proto'] == NFS:
                    poolused = get_mount_used_nfs(pooljson['mountpath'], pooljson['url'])
                else:
                    poolused = get_mount_used(pooljson['mountpath'])
                pooljson.update(poolused)
            else:
                # fs check pool dir
                pooldir = '%s/%s' % (pooljson['mountpath'], pooljson['poolname'])
                if path_exist_sh(pooldir):
                    pooljson['status'] = 'inactive'

        elif pooljson['proto'] == UUS:
            if show_used:
                poolused = get_uusmount_used(pooljson, pooljson['inter_poolname'])
                if poolused:
                    pooljson.update(poolused)
                else:
                    pooljson.update(get_inactive_used())
                    
            if not inter_call:
                pooljson['url'] = '%s://%s' % (pooljson['disktype'], pooljson['ip'])
                del pooljson['inter_poolname']
                del pooljson['blocktype']
                del pooljson['ip']
                del pooljson['nmk_strip']
                del pooljson['prealloc']
                del pooljson['user']
                del pooljson['pwd']
                if pooljson.has_key('export-mode'):
                    del pooljson['export-mode']
                                
                                    
    else:
        pooljson = {}
    return pooljson     
    
def pool_list(args):
    args_dict = vars(args)
    #fullurl = args_dict['url']
    
    if not path_exist(CSTOR_POOL):
            mkdir_p(CSTOR_POOL)
            
    pool_exist = []
    poollist = os.listdir(CSTOR_POOL)
    for pool in poollist: 
        poolitem = pool_get_json(pool, 1, 0, 0)
        if poolitem:
            pool_exist.append(poolitem)
        else:
            mkdir_p(CSTOR_POOL_INVALID)
            cmd = 'mv %s/%s %s/%s >/dev/null' % (CSTOR_POOL, pool, CSTOR_POOL_INVALID, pool)
            exec_system(cmd)
        
    return print_datajson(0, 'success', 'poollist', pool_exist) 
        
    '''if not fullurl:
        if not path_exist(CSTOR_POOL):
            mkdir_p(CSTOR_POOL)
        pool_exist = []
        poollist = os.listdir(CSTOR_POOL)
        for pool in poollist: 
            poolitem = pool_get_json(pool, 1, 0, 0)
            if poolitem:
                pool_exist.append(poolitem)
            else:
                mkdir_p(CSTOR_POOL_INVALID)
                cmd = 'mv %s/%s %s/%s >/dev/null' % (CSTOR_POOL, pool, CSTOR_POOL_INVALID, pool)
                exec_system(cmd)
        
        return print_datajson(0, 'success', 'poollist', pool_exist) 
    else:
        retarray = []
        pos = fullurl.find(':')
        
        t = fullurl[0:pos]
        url = fullurl[pos + 1:]
        
        if t == LOCAL_FS:
            dirname = ''
            showall = 0
            if url == 'all':
                showall = 1
            elif url == 'available':
                showall == 0
            else:
               dirname = url
            retarray = localfs_dev_pool(showall, dirname)
        elif t == NFS:
            if url[0] != '/':
                used = get_nfs_gluster_dev_pool(NFS, url) 
                used['url'] = 'nfs://%s' % url
                used['tag'] = url
                retarray.append(used)
        elif t == GLUSTERFS:
            if url[0] != '/':
                used = get_nfs_gluster_dev_pool(GLUSTERFS, url) 
                used['url'] = 'glusterfs://%s' % url
                used['tag'] = url
                retarray.append(used)
        elif t == UUS:
            retarray = uus_dev_pool(url)
        elif t == URAID:
            showall = 0
            if url == 'all':
                showall = 1 
            retarray = uraid_dev_pool(showall)
        else:
            pass
        
        #print retarray
        return print_datajson(0, 'success', 'poollist', retarray)
    '''

def pool_show(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']  
    pooljson = pool_get_json(poolname, 1, 0, 0)
    err = 0
    msg = 'success'
    if not pooljson:
        err = 101
        msg = 'pool not exist'
    
    return print_datajson(err, msg, 'poolshow', pooljson)
    
def pool_remove(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']

    pooljson = json_load_file(CSTOR_POOL, poolname)
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)

    force_run = 1
    mount_empty = 1
    pool_is_active = 1

    if pooljson['proto'] == URAID:
        force_run = 0

    pooljson = pool_get_json(poolname, 0, force_run, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    '''
    # check mount
    if pooljson['status'] == 'inactive':
        if pooljson['proto'] != URAID:
            return print_resultjson(102, 'pool inactive', poolname)
        else:
            pool_is_active = 0
         
    if pool_is_active and pooljson.has_key('disktype') and pooljson['disktype'] == 'file':
        #remove data dir
        pooldatadir = '%s/%s' % (pooljson['mountpath'], poolname)
        if path_exist(pooldatadir):
            if len(os.listdir(pooldatadir)):
                mount_empty = 0
                #return print_resultjson(111, 'vdisk exist', poolname)
            else:
                rm_file_empty_dir(pooldatadir)    
            #remove tag
            if mount_empty:
                fullname = '%s/.cstor-tag.%s' % (pooljson['mountpath'], poolname)
                rm_file_empty_dir(fullname)
            
            if pooljson['proto'] != URAID and pooljson['proto'] != LOCAL_FS:
                cmd = 'umount %s >/dev/null' % pooljson['mountpath']
                err = exec_system(cmd)
            
                if err:
                    return print_resultjson(112, 'umount pool err', poolname)
                else:
                    fstab_remove_line(pooljson['mountpath'])
    '''

    if pooljson['status'] == 'inactive':
        pool_is_active = 0

    if pooljson.has_key('disktype') and pooljson['disktype'] == 'file':
        if not pool_is_active:
            if pooljson['proto'] == NFS or pooljson['proto'] == GLUSTERFS:
                fstab_remove_line(pooljson['mountpath'])
        else:
            # remove data dir
            pooldatadir = '%s/%s' % (pooljson['mountpath'], poolname)
            if path_exist(pooldatadir):
                if len(os.listdir(pooldatadir)):
                    mount_empty = 0
                    # return print_resultjson(111, 'vdisk exist', poolname)
                else:
                    rm_file_empty_dir(pooldatadir)
                    # remove tag
                if mount_empty:
                    fullname = '%s/.cstor-tag.%s' % (pooljson['mountpath'], poolname)
                    rm_file_empty_dir(fullname)

                if pooljson['proto'] == NFS or pooljson['proto'] == GLUSTERFS:
                    cmd = 'umount %s >/dev/null' % pooljson['mountpath']
                    err = exec_system(cmd)

                    if err:
                        return print_resultjson(112, 'umount pool err', poolname)
                    else:
                        fstab_remove_line(pooljson['mountpath'])

    #remove block link dir              
    if pooljson['proto'] == UUS:
        mountpath = pooljson['mountpath']
        if not mountpath:
            mountpath = '%s/%s' % (DEF_BASE_MNT_PATH, poolname)
        cmd = 'rm -f %s/*' % mountpath
        exec_system(cmd)
        rm_file_empty_dir(mountpath)
        
    #remove pool conf file 
    fullname = '%s/%s' % (CSTOR_POOL, poolname)
    rm_file_empty_dir(fullname) 
    
    return print_resultjson(0, 'success', 'poolname')

def pool_set_status(args):  
    args_dict = vars(args)
    poolname = args_dict['poolname']
    status = args_dict['status']
    if status != 'normal' and status != 'maintain':
        return print_resultjson(104, 'invalid status', poolname)
    
    pooljson = json_load_file(CSTOR_POOL, poolname)
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    pooljson['maintain'] = status
    json_dump_file(CSTOR_POOL, poolname, pooljson)
    
    return print_resultjson(0, 'success', poolname)
    
##############################################  
    
def create_volume(args):
    
    args_dict = vars(args)
    poolname = args_dict['poolname']
    
    pooljson = pool_get_json(poolname, 0, 1, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
        
    if pooljson['maintain'] == 'maintain':
        return print_resultjson(103, 'pool maintain', poolname)
    
    exec_fun = '%s_create_vol' % pooljson['disktype']
    
    return eval(exec_fun)(pooljson, args_dict)  

def remove_volume(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']
    
    pooljson = pool_get_json(poolname, 0, 1, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
        
    if pooljson['maintain'] == 'maintain':
        return print_resultjson(103, 'pool maintain', poolname)
    
    exec_fun = '%s_remove_vol' % pooljson['disktype']
    
    return eval(exec_fun)(pooljson, args_dict) 

def show_volume(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']
    
    pooljson = pool_get_json(poolname, 0, 1, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
    
    if pooljson['maintain'] == 'maintain':
        return print_resultjson(103, 'pool maintain', poolname)
    
    exec_fun = '%s_show_vol' % pooljson['disktype']
    
    return eval(exec_fun)(pooljson, args_dict) 

def expand_volume(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']
    
    pooljson = pool_get_json(poolname, 0, 1, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
    
    if pooljson['maintain'] == 'maintain':
        return print_resultjson(103, 'pool maintain', poolname)
        
    exec_fun = '%s_expand_vol' % pooljson['disktype']
    
    return eval(exec_fun)(pooljson, args_dict) 

def add_volume_snapshot(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']
    
    pooljson = pool_get_json(poolname, 0, 1, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
    
    if pooljson['maintain'] == 'maintain':
        return print_resultjson(103, 'pool maintain', poolname)
        
    exec_fun = '%s_add_vol_snapshot' % pooljson['disktype']
    
    return eval(exec_fun)(pooljson, args_dict) 
     
def recover_volume_snapshot(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']
    
    pooljson = pool_get_json(poolname, 0, 1, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
        
    if pooljson['maintain'] == 'maintain':
        return print_resultjson(103, 'pool maintain', poolname)
    
    exec_fun = '%s_reocver_vol_snapshot' % pooljson['disktype']
    
    return eval(exec_fun)(pooljson, args_dict)      
    
def remove_volume_snapshot(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']
    
    pooljson = pool_get_json(poolname, 0, 1, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
    
    if pooljson['maintain'] == 'maintain':
        return print_resultjson(103, 'pool maintain', poolname)
    
    exec_fun = '%s_remove_vol_snapshot' % pooljson['disktype']
    
    return eval(exec_fun)(pooljson, args_dict) 

def show_volume_snapshot(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']
    
    pooljson = pool_get_json(poolname, 0, 1, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
        
    if pooljson['maintain'] == 'maintain':
        return print_resultjson(103, 'pool maintain', poolname)
    
    exec_fun = '%s_show_vol_snapshot' % pooljson['disktype']
    
    return eval(exec_fun)(pooljson, args_dict)     

def clone_volume(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']
    
    pooljson = pool_get_json(poolname, 0, 1, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
        
    if pooljson['maintain'] == 'maintain':
        return print_resultjson(103, 'pool maintain', poolname)
    
    exec_fun = '%s_clone_vol' % pooljson['disktype']
    
    return eval(exec_fun)(pooljson, args_dict)  

def affinity_volume(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']
    
    pooljson = pool_get_json(poolname, 0, 1, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
        
    if pooljson['maintain'] == 'maintain':
        return print_resultjson(103, 'pool maintain', poolname)
    
    exec_fun = '%s_clone_vol' % pooljson['disktype']
    
    return eval(exec_fun)(pooljson, args_dict) 
    
def prepare_volume(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']
    
    pooljson = pool_get_json(poolname, 0, 1, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
    
    if pooljson['maintain'] == 'maintain':
        return print_resultjson(103, 'pool maintain', poolname)
    
    exec_fun = '%s_prepare_vol' % pooljson['disktype']
    
    return eval(exec_fun)(pooljson, args_dict) 
    
def release_volume(args):
    args_dict = vars(args)
    poolname = args_dict['poolname']
    
    pooljson = pool_get_json(poolname, 0, 1, 1)
    
    if not pooljson:
        return print_resultjson(101, 'pool not exist', poolname)
    
    if pooljson['status'] == 'inactive':
        return print_resultjson(102, 'pool inactive', poolname)
    
    exec_fun = '%s_release_vol' % pooljson['disktype']
    
    return eval(exec_fun)(pooljson, args_dict)   

    
############################################

def file_create_vol(pool_desc, disk_desc):   
    return print_resultjson(0, 'success', 'create')
    
def file_show_vol(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'show')
    
def file_remove_vol(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'remove')
    
def file_expand_vol(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'expand')
 
def file_add_vol_snapshot(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'add snapshot')

def file_show_vol_snapshot(pool_desc, disk_desc):
   return print_resultjson(0, 'success', 'show snapshot')  
    
def file_reocver_vol_snapshot(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'recover snapshot')
    
def file_remove_vol_snapshot(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'remove snapshot') 

def file_clone_vol(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'clone')  

def file_affinity_volume(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'affinity')
    
def file_prepare_vol(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'prepare')

def file_release_vol(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'release') 

###########################################
def make_uus_dev_name(name):
    if len(name) > 30:
        name = name[0:30]
    return name

def make_uus_iscsi_name(name):
    if len(name) > 11:
        name = name[0:11]
    return name

def make_uus_link_path(mountpath, name):
    name = '%s/%s/%s' % (mountpath, name, name)
    return name

#ln -s
def uus_make_link(mountpath, name, devfullname):
    linkname = '%s/%s' % (mountpath, name)
    if not os.path.isdir(linkname):
        rm_file_empty_dir(linkname)
        mkdir_p(linkname)

    linkname = '%s/%s/%s' % (mountpath, name, name)
    if os.path.islink(linkname):
        cur_link_file = os.readlink(linkname)
        if cur_link_file == devfullname:
            return linkname
        else:
            #remove link
            try:
                os.unlink(linkname)
            except OSError as e: #e.errno == 2
                pass
    try:        
        os.symlink(devfullname, linkname)
    except OSError as e:#e.errno == 2
        pass
        
    return linkname

def uus_remove_link(mountpath, name):
    linkname = '%s/%s/%s' % (mountpath, name, name)
    if os.path.islink(linkname):
        try:
            os.unlink(linkname)
        except OSError as e: #e.errno == 2
            pass
    linkname = '%s/%s' % (mountpath, name)
    return rm_file_empty_dir(linkname)
    
def uus_check_snapshot_support(pool_desc, tag):
    if pool_desc['blocktype'] != 'lvm':
        return print_resultjson(105, 'not support', tag)
    return 0
    
def uus_vol_active_nodeid(volname):
    cmd = '%s usb_get_volume_stats_json %s' % (uusvolcli, volname)
    jsonobj = execcmd_json(cmd)
    err = get_resultjson_errcode(jsonobj)
    if err:
        return -1
        
    dataobj = jsonobj['data'][0]
    if dataobj.has_key('now_host'):
        return dataobj['now_host']
    return -1

def uus_node_id():
    jsonobj = json_load_file('/etc/uraid/conf/broker', 'broker.json')
    if jsonobj:     
        return int(jsonobj['node_id'], 16)
        
    return -1
    
def uus_dev_create_vol(pool_desc, disk_desc):
    #ucli vol hmd multi-create-uraid xname 1 -1 1 0 undefined xprealloc 0 xsizeG raw 4 1 0 128 xpoolname
    
    app_type = 'hmd'
    name = disk_desc['name']
    size = disk_desc['size']
    poolname = disk_desc['poolname']
    
    nmk_strip = pool_desc['nmk_strip']
    blocktype = pool_desc['blocktype']
    prealloc = pool_desc['prealloc']
    
    shortname = make_uus_dev_name(name)
    cmd = 'env %s OFMT=JSON TIMEOUT=3600 ucli vol hmd multi-create-uraid %s 1 -1 1 0 undefined %s 0 %s %s %s %s' % (get_callid(), shortname, prealloc, size, blocktype, nmk_strip, pool_desc['inter_poolname'])
    
    jsonobj = execcmd_json(cmd)
    
    err = get_resultjson_errcode(jsonobj)
    if err:
        return print_resultjson(err, 'failed', 'uus_dev_create_vol')
    else:
        cmd = '%s usb_volume_mark_used_json %s,%s 1>/dev/null' % (uusvolcli, shortname, app_type)
        exec_system(cmd)
        
        devpath = ''
        
        if blocktype == 'lvm':
            devpath = '/dev/%s/%s' % (shortname, shortname)          
        else:
            dataobj = jsonobj['data'][0]
            id = dataobj['id']
            devpath = '/dev/md_d%d' % id
            
         
        data = {}
        data['name'] = name
        data['poolname'] = poolname
        data['filetype'] = 'block'
        data['size'] = int(size)
        data['path'] = uus_make_link(pool_desc['mountpath'], name, devpath)
        data['uni'] = '%s://%s' % (pool_desc['proto'], devpath)
        
        return print_datajson(err, 'success', 'create', data)

def uus_dev_show_vol_inter(pool_desc, disk_desc, mklink):
    name = disk_desc['name']
    if not disk_desc.has_key('tag'):
        disk_desc['tag'] = 'show'
    cmd = 'env OFMT=JSON ucli vol show %s 2>/dev/null' % make_uus_dev_name(name)
    jsonobj = execcmd_json(cmd)
    err = get_resultjson_errcode(jsonobj)
    if err:
        return print_resultjson(err, 'get uus vol failed', disk_desc['tag'])
    else:
        dataobj = jsonobj['data'][0]
        strsize = dataobj['size'].replace('M', '')
        size = float(strsize)  * 1000 * 1000
        
        data = {}
        data['name'] = name
        data['poolname'] = disk_desc['poolname']
        data['filetype'] = 'block'
        data['size'] = size
        
        devpath = ''
        if dataobj.has_key('path'):
            devpath = dataobj['path']
        else:
            devpath = dataobj['device_path']
            
        if mklink:
            data['path'] = uus_make_link(pool_desc['mountpath'], name, devpath)
        else:
            data['path'] = make_uus_link_path(pool_desc['mountpath'], name)
            
        data['uni'] = '%s://%s' % (pool_desc['proto'], devpath)
        
        return print_datajson(err, 'success', disk_desc['tag'], data)       
        
def uus_dev_show_vol(pool_desc, disk_desc):
    
    return uus_dev_show_vol_inter(pool_desc, disk_desc, 0)

def uus_dev_remove_vol(pool_desc, disk_desc):
    name = disk_desc['name']
    uus_remove_link(pool_desc['mountpath'], name)
    cmd = 'env %s OFMT=JSON ucli vol del_hmd %s' % (get_callid(), make_uus_dev_name(name))
    jsonobj = execcmd_json(cmd)
    
    err = get_resultjson_errcode(jsonobj)
    msg = 'success'
    if err:
        msg = 'failed'
        
    return print_resultjson(err, msg, 'remove')
    
def uus_dev_expand_vol(pool_desc, disk_desc):
    err = uus_check_snapshot_support(pool_desc, 'expand')
    if err:
        return err
        
    name = disk_desc['name']
    size = disk_desc['size']
    
    cmd = '%s usb_expand_volume_json %s,%s' % (uusvolcli, make_uus_dev_name(name), size)
    jsonobj = execcmd_json(cmd)
    
    err = get_resultjson_errcode(jsonobj)
    msg = 'success'
    if err:
        msg = 'failed'
        return print_resultjson(err, msg, 'expand')
    disk_desc['tag'] = 'expand'    
    return uus_dev_show_vol(pool_desc, disk_desc)

def uus_dev_add_vol_snapshot(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'add snapshot')
    err = uus_check_snapshot_support(pool_desc, 'add snapshot')
    if err:
        return err
        
    name = disk_desc['name']
    sname = disk_desc['sname']
    
    shortname = make_uus_dev_name(name)
    shortsname = make_uus_dev_name(sname)
    
    cmd = '%s usb_create_snapshot_json %s,%s' % (uusvolcli, shortname, shortsname)    
    jsonobj = execcmd_json(cmd)
    err = get_resultjson_errcode(jsonobj)
    
    if err:
        return print_resultjson(err, 'add snapshot failed', 'sanpshot')
        
    data = {} 
    data['name'] = name
    data['poolname'] = disk_desc['poolname']
    data['filetype'] = 'block'
    data['sname'] = sname   
    
    cmd = '%s usb_get_volume_snapshots_json %s,%s' % (uusvolcli, shortname, shortsname)   
    jsonobj = execcmd_json(cmd)
    
    dataobj = jsonobj['data']['lvs']
    
    if len(dataobj) > 0:
        dataobj = dataobj[0]
        dt = dataobj['LV Creation host, time'].split()
        data['path'] = '/dev/%s/%s' % (shortname, shortsname)
        size = float(dataobj['size'].replace('M', '')) * float(dataobj['snap_percent']) * 1000 * 1000
        #data['id'] = ''
        data['vmsize'] = size
        data['date'] = '%s %s' % (dt[1], dt[2])
        data['uni'] = '%s://%s' % (pool_desc['proto'], data['path'])
    else:
        data['path'] = ''
        #data['id'] = ''
        data['vmsize'] = 0
        data['date'] = ''
        data['uni'] = ''
        
    return print_datajson(err, 'success', 'add snapshot', data) 

def uus_dev_show_vol_snapshot(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'show snapshot')
    err = uus_check_snapshot_support(pool_desc, 'show snapshot')
    if err:
        return err
    
    name = disk_desc['name']
    sname = disk_desc['sname']
    
    shortname = make_uus_dev_name(name)
    shortsname = make_uus_dev_name(sname)
    
    data = {} 
    data['name'] = name
    data['poolname'] = disk_desc['poolname']
    data['filetype'] = 'block'
    data['sname'] = sname  
    
    if not disk_desc.has_key('tag'):
        disk_desc['tag'] = 'show snapshot'
    
    cmd = '%s usb_get_volume_snapshots_json %s,%s' % (uusvolcli, shortname, shortsname)   
    jsonobj = execcmd_json(cmd)
    
    msg = 'failed'
    err = get_resultjson_errcode(jsonobj)   
    if not err: 
        msg = 'success'
        dataobj = jsonobj['data']['lvs']        
        if len(dataobj) > 0:
            dataobj = dataobj[0]
            dt = dataobj['LV Creation host, time'].split()
            data['path'] = '/dev/%s/%s' % (shortname, shortsname)
            size = float(dataobj['size'].replace('M', '')) * float(dataobj['snap_percent']) * 1000 * 1000
            #data['id'] = ''
            data['vmsize'] = size
            data['date'] = '%s %s' % (dt[1], dt[2])
            data['uni'] = '%s://%s' % (pool_desc['proto'], data['path'])
        else:
            data['path'] = ''
            #data['id'] = ''
            data['vmsize'] = 0
            data['date'] = ''
            data['uni'] = ''
        
    return print_datajson(err, msg, disk_desc['tag'], data)    

def uus_dev_reocver_vol_snapshot(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'recover snapshot')

    err = uus_check_snapshot_support(pool_desc, 'recover snapshot')
    if err:
        return err
    
    name = disk_desc['name']
    sname = disk_desc['sname']
    
    shortname = make_uus_dev_name(name)
    shortsname = make_uus_dev_name(sname)
    
    cmd = '%s lvm_recover_snap_json %s,%s' % (uusvolcli, shortname, shortsname) 
    jsonobj = execcmd_json(cmd)
    
    err = get_resultjson_errcode(jsonobj)
    msg = 'success'
    if err:
        msg = 'failed'
    return print_resultjson(err, msg, 'recover')

def uus_dev_remove_vol_snapshot(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'remove snapshot')
    err = uus_check_snapshot_support(pool_desc, 'expand')
    if err:
        return err
    
    name = disk_desc['name']
    sname = disk_desc['sname']
    
    shortname = make_uus_dev_name(name)
    shortsname = make_uus_dev_name(sname)
    
    cmd = '%s usb_remove_snapshot_json %s,%s' % (uusvolcli, shortname, shortsname) 
    jsonobj = execcmd_json(cmd)
    
    err = get_resultjson_errcode(jsonobj)
    msg = 'success'
    if err:
        msg = 'failed'
    return print_resultjson(err, msg, 'remove') 

def uus_dev_clone_vol(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'clone')
    return print_resultjson(105, 'not support', 'clone')

def uus_dev_affinity_volume(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'affinity')
    
def uus_dev_prepare_vol(pool_desc, disk_desc):
    cur_nodeid = uus_node_id()
    if cur_nodeid <= 0:
        return print_resultjson(121, 'uus not configure', 'prepare')
    
    name = disk_desc['name']
    sname = disk_desc['sname']
    poolname = disk_desc['poolname']
    
    sname = ''
    
    if sname:
        err = uus_check_snapshot_support(pool_desc, 'prepare')
        if err:
            return err
    
    shortname = make_uus_dev_name(name)
    shortsname = make_uus_dev_name(sname)
    
    active_nodeid = uus_vol_active_nodeid(shortname)
    
    if active_nodeid < 0:
        return print_resultjson(122, 'unknown vol', 'prepare')
        
    if active_nodeid != cur_nodeid:
        if active_nodeid > 0:
            cmd = '%s node=%d ucli vol stop %s >/dev/null' % (get_callid(), active_nodeid, shortname)
            err = exec_system(cmd)
            if err:
               return print_resultjson(123, 'stop vol failed', 'prepare')
               
        cmd = '%s ucli vol run %s >/dev/null' % (get_callid(), shortname)
        err = exec_system(cmd)
        if err:
            return print_resultjson(124, 'run vol failed', 'prepare')
            
            
    disk_desc['tag'] = 'prepare'
    
    if not sname:       
        return uus_dev_show_vol_inter(pool_desc, disk_desc, 1)
    else:
        cmd = '%s usb_export_snapshot_json %s,%s >/dev/null' % (uusvolcli, shortname, shortsname)
        exec_system(cmd)
        return uus_dev_show_vol_snapshot(pool_desc, disk_desc)
    
def uus_dev_release_vol(pool_desc, disk_desc):
    uus_remove_link(pool_desc['mountpath'], disk_desc['name'])
    return print_resultjson(0, 'success', 'release')
###############################################
def uus_make_http_request(pool_desc, cmd, op, param, is_json, nodeid):
    #"http://127.0.0.1:7000/uraidapi/vol/hmd?p1=multi-create-uraid%20xname%201%20-1%200%200%20undefined%20xprealloc%200%20xsizeG%20raw%204%201%200%20128%20xpoolname&outcmd=1&tmptoken=admin@@YWRtaW4="
    import base64
    p1 = ''
    if param:
        p1 = '&p1=%s' % param.replace(' ', '%20')
    
    auto_node = '&node=%s' % nodeid
    if nodeid == '-1':
        auto_node = '&uvol_auto_node=yes'
    if nodeid == '0':
        auto_node = ''
    # if nodeid not -1 or 0 use node links to map nodeid and nodeip    
        
    cmd_url = 'curl \"http://%s/uraidapi/%s/%s?tmptoken=%s@@%s%s%s&timeout=3600&%s\"  2>/dev/null' % (pool_desc['ip'], cmd, op, pool_desc['user'], base64.b64encode(pool_desc['pwd']), p1, auto_node, get_callid())
    outdata = ''
    if is_json:
        outdata = execcmd_json(cmd_url)
    else:
        outdata = execcmd_str(cmd_url)
    #print cmd_url
    #print outdata    
    return outdata

def uus_calc_nodeid(pool_desc):
    #curl "http://127.0.0.1:7000/uraidapi/vol/uvol_node?tmptoken=admin@@YWRtaW4="
    nodeid = uus_make_http_request(pool_desc, 'vol', 'uvol_node', '', 0, '0')
    nodestr = nodeid.replace('\n', '')
    return nodestr
    
def uus_iscsi_export_mode(pool_desc):
    mode = pool_desc['export-mode']
    return mode

def uus_iscsi_create_vol(pool_desc, disk_desc):
    name = disk_desc['name']
    size = disk_desc['size']
    poolname = disk_desc['poolname']
    
    nmk_strip = pool_desc['nmk_strip']
    blocktype = pool_desc['blocktype']
    prealloc = pool_desc['prealloc']
    #create disk
    nodeid = uus_calc_nodeid(pool_desc)
    param = 'multi-create-uraid %s 1 -1 1 0 undefined %s 0 %s %s %s %s' % (make_uus_iscsi_name(name), prealloc, size, blocktype, nmk_strip, pool_desc['inter_poolname'])
    jsonobj = uus_make_http_request(pool_desc, 'vol', 'uvol', param, 1, nodeid)
    err = get_resultjson_errcode(jsonobj)
    if err:
        return print_resultjson(err, 'create uus vol failed', 'create')
    #export disk
    param = "%s 0 0 %s" %  (make_uus_iscsi_name(name), uus_iscsi_export_mode(pool_desc))
    jsonobj = uus_make_http_request(pool_desc, 'uvol', 'add', param, 1, nodeid)
    err = get_resultjson_errcode(jsonobj)
    if err:
        return print_resultjson(err, 'export uus vol failed', 'create')
    
    fullname = '%s/%s'  % (jsonobj['portal'], jsonobj['tname'])
    data = {}
    data['name'] = name
    data['poolname'] = poolname
    data['filetype'] = 'block'
    data['size'] = int(size)
    data['path'] = ''#fullname
    data['uni'] = '%s://%s/0' % (pool_desc['proto'], fullname)
    return print_datajson(0, 'success', 'create', data)

def uus_iscsi_show_vol(pool_desc, disk_desc):
    name = disk_desc['name']
    param = make_uus_iscsi_name(name)
    if not disk_desc.has_key('tag'):
        disk_desc['tag'] = 'show'
        
    jsonobj = uus_make_http_request(pool_desc, 'uvol', 'show', param, 1, '0')
    err = get_resultjson_errcode(jsonobj)
    if err:
        return print_resultjson(err, 'show uus vol failed', disk_desc['tag'])
    
    fullname = '%s/%s'  % (jsonobj['portal'], jsonobj['tname'])
    data = {}
    data['name'] = name
    data['poolname'] = disk_desc['poolname']
    data['filetype'] = 'block'
    data['size'] = float(jsonobj['size'].replace('M', ''))  * 1000 * 1000
    data['path'] = ''#fullname
    data['uni'] = '%s://%s/0' % (pool_desc['proto'], fullname)
    return print_datajson(0, 'success', disk_desc['tag'], data)

def uus_iscsi_remove_vol(pool_desc, disk_desc):
    name = disk_desc['name']
    nodeid = '-1'
    param = '%s 1' % make_uus_iscsi_name(name)
    jsonobj = uus_make_http_request(pool_desc, 'uvol', 'del', param, 1, '-1')
    err = get_resultjson_errcode(jsonobj)   
    if err:
        param = make_uus_iscsi_name(name)
        jsonobj = uus_make_http_request(pool_desc, 'vol', 'show', param, 1, '0')
        err = get_resultjson_errcode(jsonobj)
        if err:
            err = 90
            return print_resultjson(err, 'not exist', 'remove')
            
        jsondata = jsonobj['data'][0]
        
        if dataobj.has_key('now_host'):
            nodeid = '%d' % jsondata['now_host']
    else:        
        nodeid = jsonobj['node']
    
    param = make_uus_iscsi_name(name)    
    jsonobj = uus_make_http_request(pool_desc, 'vol', 'del', param, 1, nodeid)
    err = get_resultjson_errcode(jsonobj)
    if err:
        return print_resultjson(err, 'remove uus vol failed', 'remove')
        
    return print_resultjson(0, 'remove uus vol success', 'remove')
    
def uus_iscsi_expand_vol(pool_desc, disk_desc):
    err = uus_check_snapshot_support(pool_desc, 'expand')
    if err:
        return err
        
    name = disk_desc['name']
    size = disk_desc['size']
    param = '%s %s' % (make_uus_iscsi_name(name), size)
    jsonobj = uus_make_http_request(pool_desc, 'uvol', 'expand', param, 1, '-1')
    err = get_resultjson_errcode(jsonobj)
    msg = 'success'
    if err:
        msg = 'failed'
        return print_resultjson(err, msg, 'expand')
    disk_desc['tag'] = 'expand'    
    return uus_iscsi_show_vol(pool_desc, disk_desc)
    
def uus_iscsi_add_vol_snapshot(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'add snapshot')
    err = uus_check_snapshot_support(pool_desc, 'add snapshot')
    if err:
        return err
    
    name = disk_desc['name']
    sname = disk_desc['sname']
    param = '%s %s' % (name, sname)
    jsonobj = uus_make_http_request(pool_desc, 'uvol', 'add-snap', param, 1, '-1')
    err = get_resultjson_errcode(jsonobj)
    if err:
        return print_resultjson(err, 'failed', 'add snapshot')
        
    nodeid = jsonobj['node']
    param = "%s %s 0 0 %s" %  (name, sname, uus_iscsi_export_mode(pool_desc))
    jsonobj = uus_make_http_request(pool_desc, 'uvol', 'export-snap', param, 1, nodeid)
    err = get_resultjson_errcode(jsonobj)
    if err:
        return print_resultjson(err, 'failed', 'export snapshot')
    
    data = {} 
    data['name'] = name
    data['poolname'] = disk_desc['poolname']
    data['filetype'] = 'block'
    data['sname'] = sname
    
    dataobj = jsonobj['data']
    
    fullname = '%s/%s' % (dataobj['portal'], dataobj['tname'])
    data['path'] = ''#fullname
    
    #data['id'] = ''
    data['vmsize'] = float(dataobj['vmsize']) * 1000 * 1000
    data['date'] = dataobj['date']
    data['uni'] = '%s://%s/0' % (pool_desc['proto'], fullname)
        
    return print_datajson(err, 'success', 'add snapshot', data) 

def uus_iscsi_show_vol_snapshot(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'show snapshot')
    err = uus_check_snapshot_support(pool_desc, 'show')
    if err:
        return err
    
    name = disk_desc['name']
    sname = disk_desc['sname']  
    param = "%s %s" %  (name, sname)
    jsonobj = uus_make_http_request(pool_desc, 'uvol', 'show-ss', param, 1, '0')
    err = get_resultjson_errcode(jsonobj)
    if err:
        return print_resultjson(err, 'failed', 'show snapshot')
    
    data = {} 
    data['name'] = name
    data['poolname'] = disk_desc['poolname']
    data['filetype'] = 'block'
    data['sname'] = sname
    
    dataobj = jsonobj
    
    fullname = '%s/%s' % (dataobj['portal'], dataobj['tname'])
    data['path'] = ''#fullname
    
    #data['id'] = ''
    data['vmsize'] = float(dataobj['vmsize']) * 1000 * 1000
    data['date'] = dataobj['date']
    data['uni'] = '%s://%s/0' % (pool_desc['proto'], fullname)
    
    return print_datajson(err, 'success', 'show snapshot', data) 

def uus_iscsi_reocver_vol_snapshot(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'recover snapshot')
    err = uus_check_snapshot_support(pool_desc, 'reocver')
    if err:
        return err
        
    name = disk_desc['name']
    sname = disk_desc['sname']  
    param = "%s %s" %  (name, sname)
    jsonobj = uus_make_http_request(pool_desc, 'uvol', 'recover-snap', param, 1, '-1')
    err = get_resultjson_errcode(jsonobj)
    msg = 'success'
    if err:
        msg = 'failed'
    
    return print_resultjson(err, msg, 'recover snapshot')

def uus_iscsi_remove_vol_snapshot(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'remove snapshot')
    err = uus_check_snapshot_support(pool_desc, 'remove')
    if err:
        return err 

    name = disk_desc['name']
    sname = disk_desc['sname']  
    param = "%s %s" %  (name, sname)
    jsonobj = uus_make_http_request(pool_desc, 'uvol', 'del-snap', param, 1, '-1')
    err = get_resultjson_errcode(jsonobj)
    msg = 'success'
    if err:
        msg = 'failed'
    
    return print_resultjson(err, msg, 'del snapshot')       

def uus_iscsi_clone_vol(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'clone')
    return print_resultjson(105, 'not support', 'clone')    

def uus_iscsi_affinity_volume(pool_desc, disk_desc):
    return print_resultjson(0, 'success', 'affinity')   
    
def uus_iscsi_make_vol_ok(exist_lun, lunid, targetname):
    luninfo = exist_lun.split()
    while luninfo[1].find('-') >= 0:
        time.sleep(0.2)
        cmd = 'lsscsi -st|awk \'{{print $1 $3 " " $4 " " $5}}\'|grep \':%s]%s,t,\'' % (lunid, targetname)
        exist_lun = execcmd_str(cmd)
        luninfo = exist_lun.split()
    return luninfo

def uus_iscsi_prepare_vol(pool_desc, disk_desc):
    
    name = disk_desc['name']
    sname = disk_desc['sname']
    uni = disk_desc['uni'].split('/')
    
    portal = uni[2]
    targetname = uni[3]
    lunid = uni[4]
    
    sname = ''
    #iscsiadm -m node
    #192.168.164.82:3260,1 iqn.2015-10.com.uit:storage.iscsi-scst-0002-4
    
    #discovery iscsiadm -m discovery -t st -p 192.167.164.194   
    #192.168.164.82:3260,1 iqn.2015-10.com.uit:storage.iscsi-scst-0002-0
    #192.168.164.82:3260,1 iqn.2015-10.com.uit:storage.iscsi-scst-0002-1
    
    #iscsiadm -m session
    #tcp: [1] 192.168.164.82:3260,1 iqn.2015-10.com.uit:storage.iscsi-scst-0002-2 (non-flash)
    #tcp: [10] 192.168.164.83:3260,1 iqn.2015-10.com.uit:storage.iscsi-scst-0003-1 (non-flash)
    
    #get host conn info   lsscsi -st|awk '{print $1 $3 " " $4 " " $5}'
    #[20:0:0:1]iqn.2015-10.com.uit:storage.iscsi-scst-0002-1,t,0x1 /dev/sddf 
    cmd = 'lsscsi -st|awk \'{{print $1 $3 " " $4 " " $5}}\'|grep \':%s]%s,t,\'' % (lunid, targetname)
    exist_lun = execcmd_str(cmd)
    if not exist_lun:
        #make sure ininame is set            
        iscsiconf = file_read_str('/etc/iscsi', 'initiatorname.iscsi')
        ininame = iscsiconf.split('=')[1].replace('\n', '')
        
        ini_name_exist = 0
        
        if not sname:
            #print 'begin show ininame'
            param = make_uus_iscsi_name(name)
            jsonobj = uus_make_http_request(pool_desc, 'uvol', 'show', param, 1, '0')
            err = get_resultjson_errcode(jsonobj)
            if err:
                err = 130
                return print_resultjson(err, 'vol not exist', 'prepare')
                
            active_nodeid = '%d' % jsonobj['active_node']
            initiatiors = jsonobj['initiators'] #array
            for ini in initiatiors:
                if ini['ininame'] == ininame:
                    ini_name_exist = 1
                    break
            
            if not ini_name_exist:
                #print 'begin add ininame'
                param = '%s %s' % (make_uus_iscsi_name(name), ininame)
                jsonobj = uus_make_http_request(pool_desc, 'uvol', 'add-initiator', param, 1, active_nodeid)
                
                err = get_resultjson_errcode(jsonobj)
                if err:
                    err = 131
                    return print_resultjson(err, 'add initiator failed', 'prepare')
                #print 'end add ininame'
                for ini in initiatiors:
                    param = '%s %s' % (make_uus_iscsi_name(name), ini)
                    uus_make_http_request(pool_desc, 'uvol', 'del-initiator', param, 1, active_nodeid)
                
        else:
            param = '%s %s' % (make_uus_iscsi_name(name), sname)
            jsonobj = uus_make_http_request(pool_desc, 'uvol', 'show-ss', param, 1, '0')
            err = get_resultjson_errcode(jsonobj)
            if err:
                err = 130
                return print_resultjson(err, 'snapshot not exist', 'prepare')
                
            active_nodeid = '%d' % jsonobj['active_node']
            initiatiors = [] #array
            if jsonobj.has_key('initiators'):
                initiatiors = jsonobj['initiators']
                for ini in initiatiors:
                    if ini['ininame'] == ininame:
                        ini_name_exist = 1
                        break
            if not ini_name_exist:
                param = '%s %s %s' % (make_uus_iscsi_name(name), sname, ininame)
                jsonobj = uus_make_http_request(pool_desc, 'uvol', 'add-ss-initiator', param, 1, active_nodeid)
                
                err = get_resultjson_errcode(jsonobj)
                if err:
                    err = 131
                    return print_resultjson(err, 'add initiator failed', 'prepare')
                
                for ini in initiatiors:
                    param = '%s %s %s' % (make_uus_iscsi_name(name), sname, ini)
                    uus_make_http_request(pool_desc, 'uvol', 'del-ss-initiator', param, 1, active_nodeid)
                    
        #discovery          
        cmd = 'iscsiadm -m node|grep %s$' % targetname
        discovery = execcmd_str(cmd)
        #print 'start discovery'
        if not discovery:            
            #discovery
            import time
            #print 'begin discovery'
            cmd = 'iscsiadm -m discovery -t st -p %s|grep %s$' % (portal, targetname)
            for cnt in range(15):
                discovery_str = execcmd_str(cmd)
                if discovery_str:
                    break
                if cnt % 3 == 0:
                    time.sleep(2)
                else:
                    time.sleep(0.1)
                    
                sys.stderr.write('discovery.......\n')
                
            if not discovery_str:
                err = 132
                return print_resultjson(err, 'discovery failed', 'prepare')
            
        #login
        #print 'begin login'
        cmd = 'iscsiadm -m node -T %s -p %s -l >/dev/null' % (targetname, portal)
        err = exec_system(cmd)
        if err:
            err = 133
            return print_resultjson(err, 'login failed', 'prepare')
        #print 'end login'    
        cmd = 'lsscsi -st|awk \'{{print $1 $3 " " $4 " " $5}}\'|grep \':%s]%s,t,\'' % (lunid, targetname)
        exist_lun = execcmd_str(cmd)
        if not exist_lun:
            err = 133
            return print_resultjson(err, 'login failed', 'prepare')
    
    luninfo = uus_iscsi_make_vol_ok(exist_lun, lunid, targetname) 
        
    #show host info
        
    sizelen = len(luninfo[2])
    pos = sizelen-2
    sizestr = luninfo[2][0:pos]
    unit = luninfo[2][pos:]
    size = 0
    if unit == 'TB':
        size = float(sizestr) * 1000 * 1000 * 1000 * 1000
    elif unit == 'GB':
        size = float(sizestr) * 1000 * 1000 * 1000
    elif unit == 'MB':
        size = float(sizestr) * 1000 * 1000
    elif unit == 'KB':
        size = float(sizestr) * 1000
    
    data = {}
    data['name'] = name
    data['poolname'] = disk_desc['poolname']
    data['filetype'] = 'block'
    data['size'] = size
    data['path'] = uus_make_link(pool_desc['mountpath'], name, luninfo[1]) #luninfo[1]
    data['uni'] = disk_desc['uni']
    return print_datajson(0, 'success', 'prepare', data)
      
def uus_iscsi_release_vol(pool_desc, disk_desc):
    
    uni = disk_desc['uni'].split('/')
    
    portal = uni[2]
    targetname = uni[3]
    #lunid = uni[4]
    uus_remove_link(pool_desc['mountpath'], disk_desc['name'])
    cmd = 'iscsiadm -m node -T %s -p %s -u >/dev/null' % (targetname, portal)
    err = exec_system(cmd)
    msg = 'success'
    if err:
        err = 129
        msg = 'failed'
   
    return print_resultjson(err, msg, 'release')
    
if __name__ == '__main__':
    #locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    os.putenv('LANG', 'en_US.UTF-8')
    err = main(*sys.argv)
    exit(err)
    
    

