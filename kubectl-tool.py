#!/usr/bin/env pipenv-shebang
import sys
import os
import argparse
import shutil
import base64
from jinja2 import Environment, FileSystemLoader
import pandas as pd
from tabulate import tabulate
from kubernetes import config,client
config.load_kube_config()

def EnvDefinition():
    global WorkDir
    global Date
    global NowDir

def viewdeploy():
    if all([ args.namespace ,args.actualreplicas ]):
        v1 = client.AppsV1Api()

        list_deployment = v1.list_namespaced_deployment(namespace=args.namespace)
        data = pd.DataFrame(columns=['NAME','READY_REPLICAS','REPLICAS','UNAVAILABLE','STRATEGY'])
        for deploy in list_deployment.items:
            name = deploy.metadata.name
            deploy = v1.read_namespaced_deployment(name=name,namespace=args.namespace)
            name_read = deploy.metadata.name
            ready_rep = checkOrDefault(deploy.status.ready_replicas)
            replicas = checkOrDefault(deploy.status.replicas)
            not_ready = checkOrDefault(deploy.status.unavailable_replicas)
            strategy = deploy.spec.strategy.type
            if args.actualreplicas == int(replicas):
                data = data.append({'NAME': name_read,'READY_REPLICAS': ready_rep,'REPLICAS': replicas,'UNAVAILABLE': not_ready,'STRATEGY': strategy}, ignore_index=True)
                #output = data.to_string(justify='center',index=False)
                output = data

        if data.empty:
            print("")
            print("")
            sys.exit(0);    
        elif all([ args.namespace ,args.actualreplicas ,args.scale ,args.replicas ]):
            pretty_print(output)
            print("\n scaling deploy to: "+str(args.replicas))
            namespace = args.namespace
            actual_replicas = args.actualreplicas
            replicas = args.replicas
            for deploy in list_deployment.items:
                name = deploy.metadata.name
                deploy = v1.read_namespaced_deployment(name=name,namespace=args.namespace)
                name_read = deploy.metadata.name
                replicas = deploy.status.replicas
                repl_toscale = args.replicas
                if str(args.actualreplicas) == str(replicas):
                    scaledeploy(name,namespace,repl_toscale)
            sys.exit(0); 
        elif all([ args.namespace ,args.actualreplicas ,args.scale]) or all([ args.namespace ,args.actualreplicas ,args.replicas]):
            print("ERROR: --scale or --replicas must be declared togheter")
            sys.exit(1);
        else:
            pretty_print(output)
            sys.exit(0);

    if args.namespace:
        v1 = client.AppsV1Api()
        deployments=v1.list_deployment_for_all_namespaces()
        data = pd.DataFrame(columns=['NAME','READY_REPLICAS','REPLICAS','UNAVAILABLE','STRATEGY'])
        for deploy in deployments.items:
            namespace = deploy.metadata.namespace
            req_namespace = args.namespace
            if str(namespace) == str(req_namespace):
                    name = deploy.metadata.name
                    deploy = v1.read_namespaced_deployment(name=name,namespace=req_namespace)
                    name_read = deploy.metadata.name
                    ready_rep = checkOrDefault(deploy.status.ready_replicas)
                    replicas = checkOrDefault(deploy.status.replicas)
                    not_ready = checkOrDefault(deploy.status.unavailable_replicas)
                    strategy = deploy.spec.strategy.type
                    data = data.append({'NAME': name_read,'READY_REPLICAS': ready_rep,'REPLICAS': replicas,'UNAVAILABLE': not_ready,'STRATEGY': strategy}, ignore_index=True)
                    output = data
        if data.empty:
            print("")
            sys.exit(0);    
        else:
            pretty_print(output)
            sys.exit(1);

#Convert NoneType output to number
def checkOrDefault(x):
    return int(0) if str(x) == "None" else int(x)

#Output Formatting
def pretty_print(df):
    print(tabulate(df, showindex=False, headers=df.columns, numalign="left"))
    
def scaledeploy(name,namespace,repl_toscale):
    v1 = client.AppsV1Api()
    try:
        replicas = int(repl_toscale)
        body={"apiVersion": "extensions/v1beta1","kind": "Deployment","spec": {"replicas": replicas}}
        deploy=v1.patch_namespaced_deployment_scale(name=name,namespace=namespace,body=body)
        print("       deployment/"+name+" scaled")
    except:
        print("Caught error while scaling Deployment "+name)

def RollingDeploy():
   WorkDir = "/tmp/Rolling_deploy"

   Template = os.path.join(WorkDir,"template.yaml")
   List = os.path.join(WorkDir,"lista.deploy.txt")
   try:
       #Create WorkDir
       if os.path.exists(WorkDir) :
           print("")
       else:
           os.makedirs(WorkDir)
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

def decodesecrets():
    v1 = client.CoreV1Api()

    if all([ args.namespace ,args.secret ]):
        secrets = v1.read_namespaced_secret(name=args.secret,namespace=args.namespace,pretty='True')
        print ("\n------- Decoding Secret: "+secrets.metadata.name.upper()+" -------\n")
        secrets_data = (secrets.data)
        data = pd.DataFrame(columns=['KEY','VALUE'])
        for key,value in secrets_data.items():
            value_decoded = base64.b64decode(value)
            value_decoded = value_decoded.decode('utf-8',errors='ignore')
            #keys = str(key+":")
            data = data.append({'KEY': key,'VALUE': value_decoded}, ignore_index=True)
            #output = output.str.wrap(50)
            #print("%-15s\t%-15s" % (keys,value_decoded.decode('utf-8',errors='ignore')))
        output = data
        pretty_print(output)
        sys.exit()

    if  args.namespace:
        secrets_list = v1.list_namespaced_secret(args.namespace)
        for sec in secrets_list.items:
            print("\n------- Decoding All Secrets for namespace: "+args.namespace.upper()+" -------\n")
            print("\n-------"+sec.metadata.name.upper()+"-------\n")
            secret_name = sec.metadata.name
            namespace = sec.metadata.namespace
            secret_single = v1.read_namespaced_secret(name=secret_name,namespace=namespace)
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
    parser_view=subparsers.add_parser("view",help="List deployments for a namespace, with --scale option can increse or decrease deployments with same replicaset (The default namespace is  default)")
    parser_view.add_argument("-n","--namespace",help="Specify namespace",default="default",type=str)
    parser_view.add_argument("-ar","--actualreplicas", help="Search for deployments that has same int value of replica",action="store",required=False,type=int)
    parser_view.add_argument("-r","--replicas", help="Specify for which replicas you want to scale requires --scale",required=False,type=int)
    parser_view.add_argument("-sc","--scale", help="Scaling down, if defined then will scale to specified replicas arg --replicas",action="store",required=False,nargs='?', const="Y", type=str)
    parser_view.set_defaults(func=viewdeploy)

    #createtheparserforthe"RollingUpdate"command
    parser_rolling=subparsers.add_parser("rolling-update",help="Execute rolling Update for deployments")
    parser_rolling.add_argument("-d","--deployment",help="Deploy",action="store",required=False,type=str)
    parser_rolling.add_argument("-n","--namespace",help="Specify namespace",default="default",type=str)
    parser_rolling.set_defaults(func=RollingDeploy)

    #Create the parser for the "DecodeSecrets" command
    parser_decode=subparsers.add_parser("decode-secrets",help="Decode secrets contents")
    parser_decode.add_argument("-s","--secret",help="Secret name to be decoded",action="store",required=False,type=str)
    parser_decode.add_argument("-n","--namespace",help="Specify namespace. Without secret specified it will print all secrets decoded for the namespace",default="default",type=str)
    parser_decode.set_defaults(func=decodesecrets)

    if len(sys.argv[1:])==0:
        parser.print_help()

    args=parser.parse_args()

    if "view" in sys.argv:
        viewdeploy()
    elif "rolling-update" in sys.argv:
        RollingDeploy()
    elif "decode-secrets" in sys.argv:
        decodesecrets()
    else:
        print("nulla")
