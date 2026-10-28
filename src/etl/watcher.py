#Não está sendo utilizado na pipeline, mas pode ser útil para monitorar a pasta de uploads e processar arquivos automaticamente

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from pipeline import run_pipeline


PASTA_RAW = r"C:\sharepoint\uploads"
PASTA_PROCESSED = r"C:\sharepoint\processed"
PASTA_ARCHIVE = r"C:\sharepoint\archive"


class Handler(FileSystemEventHandler):

    def on_created(self, event):

        if event.src_path.endswith(".xlsx"):

            print("Novo arquivo detectado")

            time.sleep(5)

            run_pipeline(
                PASTA_RAW,
                PASTA_PROCESSED,
                PASTA_ARCHIVE
            )


observer = Observer()

observer.schedule(
    Handler(),
    PASTA_RAW,
    recursive=False
)

observer.start()

print("Monitorando pasta...")

while True:
    time.sleep(10)
