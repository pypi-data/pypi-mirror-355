from typer import Typer
from loguru import logger


app = Typer()


@app.command()
def update():

    from justernetes.crd import update_services
    update_services()
    
    # find  kubectl  get justniffers.knspar.github.io  -o yaml
    #response = api.get_namespaced_custom_object('knspar.github.io', 'v1', 'justserver', 'justniffers', 'justniffer')
    #print(response)
    

def main():
    app()