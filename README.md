# kubernetes-tools

this Tool requires python jinja2

 `yum install python-pip`
 
 `pip install jinja2`


`kubernetes-tools]# ./kubectl-tool.py --help`
 usage: kubectl-tool.py [-h] {view,scale,rolling-update,decode-secrets} ...
 
 positional arguments:
   {view,scale,rolling-update,decode-secrets}
     view                List deployments for a namespace (The default
                         namespace is default)
     scale               Scale deployments at desired replicas
     rolling-update      Execute rolling Update for deployments
     decode-secrets      Decode secrets contents
 
 optional arguments:
   -h, --help            show this help message and exit`
