#!/usr/bin/python
import sys                                                        
import os                                                         
import time                                                                                                       
import argparse                                                   
import shutil     
from jinja2 import Environment, FileSystemLoader
#import jinja2 
#import datetime
#import logging                                                    
#import logging.handlers as handlers                               
#import subprocess                                                 
                                                                  
                                                                  
def EnvDefinition():                                              
    global WorkDir                                                
    global Date                                                   
    global NowDir                                                 

def ViewDeploy():

    if all([ args.namespace ,args.actualreplicas ]):
        cmd=('kubectl get deployments -n %s | grep "%s/%s" ' % (args.namespace,args.actualreplicas,args.actualreplicas))
        print("-----------------------------------------------------")
        print("view all deployments of namespace %s with replicas %s" %(args.namespace,args.actualreplicas))
        print("-----------------------------------------------------")
        os.system(cmd)
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

def GetEvents():
     try:
        args.namespace and args.watch
        cmd=('kubectl get events --sort-by=.metadata.creationTimestamp -n %s --watch ' % (args.namespaces))
        print(cmd)
     except :
        print("prova")

#    if all([ args.namespace ,args.watch ]) == 0:
#        cmd=('kubectl get events --sort-by=.metadata.creationTimestamp --all-namespaces')
#        print(cmd)
#    #    os.system(cmd)
#    #    sys.exit()
#
#    if all([ args.namespace ,args.watch ]):
#        cmd=('kubectl get events --sort-by=.metadata.creationTimestamp -n %s --watch ' % (args.namespaces))
#        print(cmd)
#       # os.system(cmd)
#
   # if args.namespace:
   #     cmd=('kubectl get events --sort-by=.metadata.creationTimestamp -n %s ' % (args.namespace))
   #     print(cmd)
   #  #   os.system(cmd)
   #  #   sys.exit()

if __name__=='__main__':

    #Call Functions:
    EnvDefinition()            

    #Argparse e help menu
    #createthetop-levelparser
    parser=argparse.ArgumentParser()
    subparsers=parser.add_subparsers()
    
    #createtheparserforthe"view"command
    parser_view=subparsers.add_parser("view",help="list deployments for a namespace (The default namespace is  default)")
    parser_view.add_argument("-n","--namespace",help="specify namespace",default="default")
    parser_view.add_argument("-ar","--actualreplicas", help="search for deployments that has same int value of replica",action="store",required=False)
    parser_view.set_defaults(func=ViewDeploy)
    
    #createtheparserforthe"scale"command
    parser_scale=subparsers.add_parser("scale",help="scale deployments at desired replicas")
    parser_scale.add_argument("-n","--namespace",help="specify namespace",default="default")
    parser_scale.add_argument("-r","--replicas", help="specify for which replicas you want to scale",required=False)
    parser_scale.add_argument("-ar","--actualreplicas", help="search for deployments that has same int value of replica",action="store",required=False)
    parser_scale.set_defaults(func=ScaleDeploy)

    #createtheparserforthe"events"command
    parser_events=subparsers.add_parser("events",help="View events ordered by time")
    parser_events.add_argument("-w","--watch",help="tail events",default=None,required=False,action='store_true')
    parser_events.add_argument("-n","--namespace",help="specify namespace",default=None,required=False)
    parser_events.set_defaults(func=GetEvents)

    #createtheparserforthe"RollingUpdate"command
    parser_rolling=subparsers.add_parser("rolling-update",help="Execute rolling Update for deployments")
    parser_rolling.add_argument("-d","--deployment",help="deploy",action="store",required=False)
    parser_rolling.add_argument("-n","--namespace",help="specify namespace",default="default")
    parser_rolling.set_defaults(func=RollingDeploy)

    if len(sys.argv[1:])==0:
        parser.print_help()
                                                                                           
    args=parser.parse_args()                                                               

    if "view" in sys.argv:
        ViewDeploy()
    elif "scale" in sys.argv:
        ScaleDeploy()
    elif "events" in sys.argv:
        GetEvents()
    elif "rolling-update" in sys.argv:
        RollingDeploy()
    else:
        print("nulla")
