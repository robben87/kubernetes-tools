#!/usr/bin/env pipenv-shebang
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

def ViewDeploy():
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
                ready_rep = deploy.status.ready_replicas
                replicas = deploy.status.replicas
                not_ready = deploy.status.unavailable_replicas
                strategy = deploy.spec.strategy.type
                if str(replicas) >= str(3):
                        if str(replicas) != "None":
                                data = data.append({'NAME': name_read,'READY_REPLICAS': ready_rep,'REPLICAS': replicas,'UNAVAILABLE': not_ready,'STRATEGY': strategy}, ignore_index=True)
                                output = data.to_string(justify='center',index=False)

    if data.empty:
        print("")
        print("NO PODS TO SCALE")
        sys.exit(0);    
    else:
        print(output)
        sys.exit(1);

if __name__=='__main__':

    parser=argparse.ArgumentParser()
    subparsers=parser.add_subparsers()

    #createtheparserforthe"view"command
    parser_view=subparsers.add_parser("view",help="List deployments for a namespace (The default namespace is  default)")
    parser_view.add_argument("-n","--namespace",help="Specify namespace",default="default")
    parser_view.add_argument("-ar","--actualreplicas", help="Search for deployments that has same int value of replica",action="store",required=False)
    parser_view.set_defaults(func=ViewDeploy)

    if len(sys.argv[1:])==0:
        parser.print_help()

    args=parser.parse_args()

    if "view" in sys.argv:
        ViewDeploy()
    else:
        print("nulla")
