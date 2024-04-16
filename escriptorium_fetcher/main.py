import io
import os 
import typer
import srsly
import getpass
import requests 

from escriptorium_connector import EscriptoriumConnector
from pathlib import Path
from rich import print
from rich.progress import track
from typing_extensions import Annotated
from zipfile import ZipFile

app = typer.Typer()


@app.command()
def fetch(
    reset_password: Annotated[bool, typer.Option(help="Reset the password for the escriptorium account.")] = False,
    no_images: Annotated[
        bool, typer.Option(help="Do not download or upload images.")
    ] = False,
    no_transcriptions: Annotated[
        bool, typer.Option(help="Do not download or upload transcriptions.")
    ] = False,
):
    """
    🐕 escriptorium-fetcher 🐕
    A CLI for downloading data from an eScriptorium server.
    """
    ESCRIPTORIUM_URL = (
        input(f'Please enter your Escriptorium Url [{os.environ.get("ESCRIPTORIUM_URL","")}]: ')
        or os.environ.get("ESCRIPTORIUM_URL")
    )
    os.environ["ESCRIPTORIUM_URL"] = ESCRIPTORIUM_URL
    
    ESCRIPTORIUM_USERNAME = (
        input(f"Please enter your Escriptorium Username [{os.environ.get('ESCRIPTORIUM_USERNAME','')}]: ")
        or os.environ.get("ESCRIPTORIUM_USERNAME")
    )
    os.environ["ESCRIPTORIUM_USERNAME"] = ESCRIPTORIUM_USERNAME

    if reset_password or not os.environ.get("ESCRIPTORIUM_PASSWORD"):
        if reset_password:
            os.environ["ESCRIPTORIUM_PASSWORD"] = ""        
        while not os.environ.get("ESCRIPTORIUM_PASSWORD"):
            ESCRIPTORIUM_PASSWORD = getpass.getpass(
                f"Please enter your Escriptorium Password: "
            )
            os.environ["ESCRIPTORIUM_PASSWORD"] = ESCRIPTORIUM_PASSWORD

    IMAGE_PATH = (
        input(f"Please enter the path to the images [{os.environ.get('IMAGE_PATH') or str(Path.cwd() / 'images')}]: ")
        or str(Path.cwd() / 'images')
    )
    if IMAGE_PATH[-1] == "/":
        IMAGE_PATH = IMAGE_PATH[:-1]
    if not Path(IMAGE_PATH).exists():
        Path(IMAGE_PATH).mkdir(parents=True, exist_ok=True)
    os.environ["IMAGE_PATH"] = IMAGE_PATH
    
    TRANSCRIPTION_PATH = (
        input(f"Please enter the path to the transcriptions [{os.environ.get('TRANSCRIPTION_PATH') or str(Path.cwd() / 'alto')} ]: ")
        or str(Path.cwd() / 'alto')
    )
    if TRANSCRIPTION_PATH[-1] == "/":
        TRANSCRIPTION_PATH = TRANSCRIPTION_PATH[:-1]
    if not Path(TRANSCRIPTION_PATH).exists():
        Path(TRANSCRIPTION_PATH).mkdir(parents=True, exist_ok=True)
    os.environ["TRANSCRIPTION_PATH"] = TRANSCRIPTION_PATH

    # connect to escriptorium
    E = EscriptoriumConnector(
        os.environ.get("ESCRIPTORIUM_URL"),
        os.environ.get("ESCRIPTORIUM_USERNAME"),
        os.environ.get("ESCRIPTORIUM_PASSWORD")
    )
    # get list of projects
    projects = requests.get(f"{os.environ.get('ESCRIPTORIUM_URL')}/api/projects", headers=E.http.headers )
    if projects.status_code == 200:
        projects = projects.json()
        project_results = projects['results']
        project_names = [p['name'] for p in project_results]
        for i, name in enumerate(project_names):
            print(
                f"[bold green_yellow]{i}[/bold green_yellow] [bold white]{name}[/bold white]"
            )
        project_name = typer.prompt("🐾 Select a project to fetch")
        # if the user enters a number, use that to select the document
        if project_name.isdigit():
            proj_name = project_results[int(project_name)]['name']
            project_slug = project_results[int(project_name)]['slug']
           
            print(
            f"[bold green_yellow] 🦴 Fetching {project_slug}...[/bold green_yellow]"
            )
        else:
            project_slug = None
    
    # get each document in the project
    documents = E.get_documents()
    documents = [d for d in documents.results if d.project == project_slug]
    # get document parts, images, and transcriptions
    if not no_transcriptions:
        transcriptions = E.get_document_transcriptions(documents[0].pk)
        transcription_names = [t.name for t in transcriptions]
        for i, name in enumerate(transcription_names):
            print(
                f"[bold green_yellow]{i}[/bold green_yellow] [bold white]{name}[/bold white]"
            )
        selection = typer.prompt("Please select a transcription to fetch")
        # if the user enters a number, use that to select the document
        if selection.isdigit():
            transcription_pk = transcriptions[int(selection)].pk
            transcription_name = transcriptions[int(selection)].name
            print(
                f"[bold green_yellow] 🐶 Fetching text from {transcription_name}...[/bold green_yellow]"
            )
        else:
            print("Please enter the number of the transcription to fetch 🐩")

    for document in documents:
        parts = E.get_document_parts(document.pk)
        for part in track(parts.results, description=f"Downloading {document.name} 🐕‍🦺"):
            try:
                if not no_images:
                    #img_binary = E.get_document_part_image(document.pk, part.pk) does not work if there is metadata is an issue
                    img_binary = E.get_image(part.image.uri)
                    if not Path(
                        str(os.environ.get("IMAGE_PATH") + "/" + document.name)
                    ).exists():
                        Path(str(os.environ.get("IMAGE_PATH") + "/" + document.name)).mkdir(
                            parents=True, exist_ok=True
                        )
                    Path(
                        str(
                            os.environ.get("IMAGE_PATH")
                            + "/"
                            + document.name
                            + "/"
                            + part.filename
                        )
                    ).write_bytes(img_binary)
                if not no_transcriptions:
                    transcription = E.download_part_alto_transcription(
                        document.pk, part.pk, transcription_pk
                    )
                    with ZipFile(io.BytesIO(transcription)) as z:
                        with z.open(z.namelist()[0]) as f:
                            transcription = f.read()
                            if not Path(
                                str(os.environ.get("TRANSCRIPTION_PATH") + "/" + document.name)
                            ).exists():
                                Path(
                                    str(
                                        os.environ.get("TRANSCRIPTION_PATH")
                                        + "/"
                                        + document.name
                                    )
                                ).mkdir(parents=True, exist_ok=True)
                            Path(
                                str(
                                    os.environ.get("TRANSCRIPTION_PATH")
                                    + "/"
                                    + document.name
                                    + "/"
                                    + part.filename.split(".")[0]
                                    + ".xml"
                                )
                            ).write_bytes(transcription)
            except Exception as e:
                print(f"[bold red]Error[/bold red] {part.title}: {e}")
    print("🦮 All Done 🦮")


if __name__ == "__main__":
    app()
