# 🐕 escriptorium-fetcher 🐕
A CLI for downloading data from an eScriptorium server.


### Installation
```bash
pip install escriptorium-fetcher
```

### Usage
```bash
$ fetcher
```
You will be prompted to select a project to fetch. Enter the number next to the project that you would like to fetch and press enter. For example, if you would like to fetch the first project, enter the following and press enter:
```bash
0 initial_batch-2024-02-21
1 another_project-2024-02-21
🐾 Select a project to fetch: 0
```
By default, fetcher downloads images and transcriptions. You need to select which transcription you want to download. Enter the number next to the transcription that you would like to fetch and press enter. For example, if you would like to fetch the first transcription, enter the following and press enter:
```bash
0 vision
1 manual
Please select a transcription to fetch: 0
```

The first time that you run the script you will be prompted to enter:
- the url of the eScriptorium server
- your username for the eScriptorium server
- your password for the eScriptorium server
- a local path to save the image files
- a local path to save the transcription files (ALTO xml)

To clear  your settings and start over, run:
```bash
$ fetcher --clear-secrets
```
If you do not want to download images or transcriptions, you can use the `--no-images` or `--no-transcriptions` flags. For example:
```bash
$ fetcher --no-images
```