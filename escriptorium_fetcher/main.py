import typer
from typing_extensions import Annotated
from pathlib import Path
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn, track
import srsly
from escriptorium_connector import EscriptoriumConnector
from PIL import Image
import getpass
import io
from zipfile import ZipFile

app = typer.Typer()


    

@app.command()
def fetch(clear_secrets: Annotated[bool, typer.Option(help="Delete the secrets.json file.")] = False,
            no_images: Annotated[bool, typer.Option(help="Do not download or upload images.")] = False,
            no_transcriptions: Annotated[bool, typer.Option(help="Do not download or upload transcriptions.")] = False,
          ):
    """
    🐕 escriptorium-fetcher 🐕
    A CLI for downloading and uploading data to an eScriptorium server.
    """
    if clear_secrets:
        if Path("secrets.json").exists():
            Path("secrets.json").unlink()
            print("🐕 secrets.json cleared 🐕")

    if Path("secrets.json").exists():
        secrets = srsly.read_json("secrets.json")
    else:
        secrets = {}
        secrets["ESCRIPTORIUM_URL"] = (
            input("Please enter your Escriptorium Url: ")
            or "https://escriptorium.pennds.org/"
        )
        secrets["ESCRIPTORIUM_USERNAME"] = (
            input("Please enter your Escriptorium Username: ") or "invitado"
        )
        secrets["ESCRIPTORIUM_PASSWORD"] = getpass.getpass(
            "Please enter your Escriptorium Password:"
        )

        secrets['IMAGE_PATH'] = input("Please enter the path to the images: ")
        if secrets['IMAGE_PATH'][-1] == "/":
            secrets['IMAGE_PATH'] = secrets['IMAGE_PATH'][:-1]
        if not Path(secrets['IMAGE_PATH']).exists():
            Path(secrets['IMAGE_PATH']).mkdir(parents=True, exist_ok=True)

        secrets['TRANSCRIPTION_PATH'] = input("Please enter the path to the transcriptions: ")
        if secrets['TRANSCRIPTION_PATH'][-1] == "/":
            secrets['TRANSCRIPTION_PATH'] = secrets['TRANSCRIPTION_PATH'][:-1]
        if not Path(secrets['TRANSCRIPTION_PATH']).exists():
            Path(secrets['TRANSCRIPTION_PATH']).mkdir(parents=True, exist_ok=True)

        srsly.write_json("secrets.json", secrets)
    # connect to escriptorium
    E = EscriptoriumConnector(
        secrets["ESCRIPTORIUM_URL"],
        secrets["ESCRIPTORIUM_USERNAME"],
        secrets["ESCRIPTORIUM_PASSWORD"],
    )
    # get list of projects
    projects = E.get_projects()
    project_names = [p.name for p in projects.results]
    for i, name in enumerate(project_names):
        print(
            f"[bold green_yellow]{i}[/bold green_yellow] [bold white]{name}[/bold white]"
        )
    project_name = typer.prompt("🐾 Select a project to fetch:")
    # if the user enters a number, use that to select the document
    if project_name.isdigit():
        project_pk = projects.results[int(project_name)].id
        project_slug = projects.results[int(project_name)].slug
        E.set_connector_project_by_pk(project_pk)
        print(
            f"[bold green_yellow] 🦴 Fetching {E.project_name}...[/bold green_yellow]"
        )
    else:
        project_slug = None

    # get each document in the project
    documents = E.get_documents()
    documents = [d for d in documents.results if d.project == project_slug]
    # get document parts, images, and transcriptions
    transcriptions = E.get_document_transcriptions(documents[0].pk)
    transcription_names = [t.name for t in transcriptions]
    for i, name in enumerate(transcription_names):
        print(
            f"[bold green_yellow]{i}[/bold green_yellow] [bold white]{name}[/bold white]"
        )
    selection = typer.prompt("Please select a transcription text to fetch")
    # if the user enters a number, use that to select the document
    if selection.isdigit():
        transcription_pk = transcriptions[int(selection)].pk
        transcription_name = transcriptions[int(selection)].name
        print(
            f"[bold green_yellow] 🐶 Using text from {transcription_name}...[/bold green_yellow]"
        )
    else:
        print("Please enter a number to select the transcription to fetch")

    for document in documents:
        parts = E.get_document_parts(document.pk)
        for part in track(parts.results, description=f"Downloading {document.name}..."):
            print(part)
            if not no_images:
                img_binary = E.get_document_part_image(document.pk, part.pk)
                img = Image.open(io.BytesIO(img_binary))
                if not Path(str(secrets['IMAGE_PATH'] +"/" + document.name)).exists():
                    Path(str(secrets['IMAGE_PATH'] +"/" + document.name)).mkdir(parents=True, exist_ok=True)
                img.save(str(secrets['IMAGE_PATH'] +"/" + document.name + "/" + part.filename))
            if not no_transcriptions:
                transcription = E.download_part_alto_transcription(document.pk, part.pk, transcription_pk)
                with ZipFile(io.BytesIO(transcription)) as z:
                    with z.open(z.namelist()[0]) as f:
                        transcription = f.read()
                        if not Path(str(secrets['TRANSCRIPTION_PATH'] +"/" + document.name)).exists():
                            Path(str(secrets['TRANSCRIPTION_PATH'] +"/" + document.name)).mkdir(parents=True, exist_ok=True)
                        Path(str(secrets['IMAGE_PATH'] +"/" + document.name + "/" + part.filename)).write_bytes(transcription)
                

if __name__ == "__main__":
    app()