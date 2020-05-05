# kubernetes-tools

this Tool requires python3 , kubernetes_python3_api_client and python3_jinja2
```
yum install python3-pip.noarch
pip3 install --user pipenv
pip3 install pipenv-shebang #Link --> https://github.com/laktak/pipenv-shebang

export PATH=~/.local/bin:$PATH

cd in directory script
pipenv install
```

```
kubernetes-tools]# ./kubectl-tool.py --help
usage: kubectl-tool.py [-h] {view,rolling-update,decode-secrets} ...

positional arguments:
  {view,rolling-update,decode-secrets}
    view                List deployments for a namespace, with --scale option
                        can increse or decrease deployments with same
                        replicaset (The default namespace is default)
    rolling-update      Execute rolling Update for deployments
    decode-secrets      Decode secrets contents

optional arguments:
  -h, --help            show this help message and exit
```
