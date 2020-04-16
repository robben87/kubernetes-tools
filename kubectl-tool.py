#!/usr/bin/env python
import sys
import os
import argparse
import shutil
import base64
from jinja2 import Environment, FileSystemLoader
import numpy as np
import pandas as pd
from kubernetes import config,client
config.load_kube_config()

def EnvDefinition():
    global WorkDir
    global Date
    global NowDir

def ViewDeploy():
    if all([ args.namespace ,args.actualreplicas ]):
        v1 = client.AppsV1Api()

        list_deployment = v1.list_namespaced_deployment(namespace=args.namespace)
        data = np.array([['','NAME','READY_REPLICAS','REPLICAS','UNAVAILABLE','STRATEGY']])
        for deploy in list_deployment.items:
            name = deploy.metadata.name
            deploy = v1.read_namespaced_deployment(name=name,namespace=args.namespace)
            name_read = deploy.metadata.name
            ready_rep = deploy.status.ready_replicas
            replicas = deploy.status.replicas
            not_ready = deploy.status.unavailable_replicas
            strategy = deploy.spec.strategy.type
            if str(args.actualreplicas) == str(replicas):
                data = np.append(data,[['',name_read,ready_rep,replicas,not_ready,strategy]],axis=0)

        df=pd.DataFrame(data=data[1:,0:],index=data[1:,0],columns=data[0,0:])
        print(df)
        sys.exit()

    if args.namespace:
        cmd=('kubectl get deployments -n %s ' % (args.namespace))
        print("-----------------------------------------------------")
        print("view all deployments of namespace %s" %(args.namespace))
        print("-----------------------------------------------------")
        os.system(cmd)
        sys.exit()

def ScaleDeploy():
    WorkDir = "/tmp/scale_deploy"

    Template = os.path.join(WorkDir,"template.yaml")
    List = os.path.join(WorkDir,"lista.deploy.txt")
   #DEBUG  print (Template)
   #DEBUG  print (List)
    try:
        #Create WorkDir
        if os.path.exists(WorkDir) :
            # DEBUG Abilitare il debug, inutile printare sempre questo output <----
            #print("--WorkDir %s exists, continue ..." %(WorkDir))
            print("")
        else:
            os.makedirs(WorkDir)
        #Clean Old files
        if os.path.exists(Template):
            os.remove(Template)
        if os.path.exists(List):
            os.remove(List)
    except:
        print("somthing Wrong in creating directories")

    cmd=('kubectl get deployments -n %s  | grep "%s/%s" | awk \'{print $1}\' > %s' % (args.namespace,args.actualreplicas,args.actualreplicas,List))
    os.system(cmd)
    #print ("-----------LEGGO FILE-------------")

    #\\ Template File creation \\#
    file=open(Template,"w")
    file.write("apiVersion: extensions/v1beta1\n")
    file.write("kind: Deployment\n")
    file.write("metadata:\n")
    file.write("  name: {{ name }}\n")
    file.write("spec:\n")
    file.write("  replicas: {{ replicas }}\n")
    file.close()

    with open(List) as name:
        for line in name:
            deploy_name=line.replace('\n','')
            line=line.replace('\n','')
            line=line+".yaml"
            patch_file=os.path.join(WorkDir,line)
            shutil.copyfile(Template,patch_file)
            #\\ Rendering Template  \\#
            # Capture our current directory
            THIS_DIR = os.path.dirname(os.path.abspath(Template))
            #print(THIS_DIR)
            # Create the jinja2 environment.
            # Notice the use of trim_blocks, which greatly helps control whitespace.
            j2_env = Environment(loader=FileSystemLoader(THIS_DIR),trim_blocks=True)
            output=j2_env.get_template('template.yaml').render(name=deploy_name,replicas=args.replicas)
            file=open(patch_file,"w")
            #print(file)
            file.write(str(output))
            file.close()
            cmd=('kubectl patch deployments/%s --patch "$(cat %s)" -n %s'%(deploy_name,patch_file,args.namespace))
            #print("----Scaling deployment----")
            os.system(cmd)

    if os.path.exists(WorkDir) and os.path.isdir(WorkDir):
        shutil.rmtree(WorkDir)

def RollingDeploy():
   WorkDir = "/tmp/Rolling_deploy"

   Template = os.path.join(WorkDir,"template.yaml")
   List = os.path.join(WorkDir,"lista.deploy.txt")
   #DEBUG  print (Template)
   #DEBUG  print (List)
   try:
       #Create WorkDir
       if os.path.exists(WorkDir) :
           # DEBUG Abilitare il debug, inutile printare sempre questo output <----
           #print("--WorkDir %s exists, continue ..." %(WorkDir))
           print("")
       else:
           os.makedirs(WorkDir)
       #Clean Old files
       if os.path.exists(Template):
           os.remove(Template)
       if os.path.exists(List):
           os.remove(List)
   except:
       print("somthing Wrong in creating directories")

   cmd=('kubectl get deployments %s -n %s  --no-headers | awk \'{print $1}\' > %s' % (args.deployment,args.namespace,List))
   os.system(cmd)
   #print(cmd)
   #\\ Template File creation \\#
   file=open(Template,"w")
   file.write("kind: Deployment\n")
   file.write("metadata:\n")
   file.write("  name: {{ name }}\n")
   file.write("spec:\n")
   file.write("  template:\n")
   file.write("    metadata:\n")
   file.write("      labels:\n")
   file.write("        app1: RollingUpdate{{ range(1, 1000) | random }}\n")
   file.close()
   with open(List) as name:
       for line in name:
           deploy_name=line.replace('\n','')
           line=line.replace('\n','')
           line=line+".yaml"
           patch_file=os.path.join(WorkDir,line)
           shutil.copyfile(Template,patch_file)
           #\\ Rendering Template  \\#
           # Capture our current directory
           THIS_DIR = os.path.dirname(os.path.abspath(Template))
           #print(THIS_DIR)
           # Create the jinja2 environment.
           # Notice the use of trim_blocks, which greatly helps control whitespace.
           j2_env = Environment(loader=FileSystemLoader(THIS_DIR),trim_blocks=True)
           output=j2_env.get_template('template.yaml').render(name=args.deployment)
           file=open(patch_file,"w")
           #print(file)
           file.write(str(output))
           file.close()
           cmd=('kubectl patch deployments/%s --patch "$(cat %s)" -n %s'%(deploy_name,patch_file,args.namespace))
           #print("----Rolling deployment----")
           os.system(cmd)

   #Delete working Dirs
   if os.path.exists(WorkDir) and os.path.isdir(WorkDir):
       shutil.rmtree(WorkDir)

def DecodeSecrets():
    v1 = client.CoreV1Api()

    if all([ args.namespace ,args.secret ]):
        secrets = v1.read_namespaced_secret(name=args.secret,namespace=args.namespace,pretty='True')
        print ("\n------- Decoding Secret: "+secrets.metadata.name.upper()+" -------\n")
        secrets_data = (secrets.data)
        for key,value in secrets_data.items():
            value_decoded = base64.b64decode(value)
            keys = str(key+":")
            print("%-15s\t%-15s" % (keys,value_decoded.decode('utf-8',errors='ignore')))
        sys.exit()

    if  args.namespace:
        secrets_list = v1.list_namespaced_secret(args.namespace)
        for sec in secrets_list.items:
            print("\n------- Decoding All Secrets for namespace :"+args.namespace.upper()+" -------\n")
            print("\n-------"+sec.metadata.name.upper()+"-------\n")
            secret_name = sec.metadata.name
            secret_single = v1.read_namespaced_secret(name=secret_name,namespace="docfly")
            secrets_data = (secret_single.data)
            for key,value in secrets_data.items():
                value_decoded = base64.b64decode(value)
                keys = str(key+":")
                print("%-15s\t%-15s" % (key,value_decoded.decode('utf-8',errors='ignore')))
        sys.exit()

if __name__=='__main__':

    #Call Functions:
    EnvDefinition()

    #Argparse e help menu
    #createthetop-levelparser
    parser=argparse.ArgumentParser()
    subparsers=parser.add_subparsers()

    #createtheparserforthe"view"command
    parser_view=subparsers.add_parser("view",help="List deployments for a namespace (The default namespace is  default)")
    parser_view.add_argument("-n","--namespace",help="Specify namespace",default="default")
    parser_view.add_argument("-ar","--actualreplicas", help="Search for deployments that has same int value of replica",action="store",required=False)
    parser_view.set_defaults(func=ViewDeploy)

    #createtheparserforthe"scale"command
    parser_scale=subparsers.add_parser("scale",help="Scale deployments at desired replicas")
    parser_scale.add_argument("-n","--namespace",help="Specify namespace",default="default")
    parser_scale.add_argument("-r","--replicas", help="Specify for which replicas you want to scale",required=False)
    parser_scale.add_argument("-ar","--actualreplicas", help="Search for deployments that has same int value of replica",action="store",required=False)
    parser_scale.set_defaults(func=ScaleDeploy)

#    #createtheparserforthe"events"command
#    parser_events=subparsers.add_parser("events",help="View events ordered by time")
#    parser_events.add_argument("-w","--watch",help="tail events",default=None,required=False,action='store_true')
#    parser_events.add_argument("-n","--namespace",help="specify namespace",default=None,required=False)
#    parser_events.set_defaults(func=GetEvents)

    #createtheparserforthe"RollingUpdate"command
    parser_rolling=subparsers.add_parser("rolling-update",help="Execute rolling Update for deployments")
    parser_rolling.add_argument("-d","--deployment",help="Deploy",action="store",required=False)
    parser_rolling.add_argument("-n","--namespace",help="Specify namespace",default="default")
    parser_rolling.set_defaults(func=RollingDeploy)

    #Create the parser for the "DecodeSecrets" command
    parser_decode=subparsers.add_parser("decode-secrets",help="Decode secrets contents")
    parser_decode.add_argument("-s","--secret",help="Secret name to be decoded",action="store",required=False)
    parser_decode.add_argument("-n","--namespace",help="Specify namespace. Without secret specified it will print all secrets decoded for the namespace",default="default")
    parser_decode.set_defaults(func=DecodeSecrets)

    if len(sys.argv[1:])==0:
        parser.print_help()

    args=parser.parse_args()

    if "view" in sys.argv:
        ViewDeploy()
    elif "scale" in sys.argv:
        ScaleDeploy()
    # TODO
    # elif "events" in sys.argv:
        # GetEvents()
    elif "rolling-update" in sys.argv:
        RollingDeploy()
    elif "decode-secrets" in sys.argv:
        DecodeSecrets()
    else:
        print("nulla")
