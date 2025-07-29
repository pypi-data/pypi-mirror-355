from jinja2 import Environment, FileSystemLoader
import os

def create(name):

    estructura = [
        "nginx/ssl",
        "nginx/sites",
        "example_entity/app",
    ]

    archivos = {
        "README.md" : "/templates/project/README.txt",
        ".env" : "templates/project/env.txt",
        "docker-compose.yaml": "templates/project/docker-compose.txt",
        "nginx/sites/example_entity.conf": "templates/project/site_example.txt",
        "example_entity/app/main.py" : "templates/project/main_example.txt",
        "example_entity/requirements.txt": "templates/project/requirements_example.txt",
        "example_entity/Dockerfile": "templates/dockerfile.txt",
    }

    env = Environment(loader=FileSystemLoader("."))

    # Crear directorio base
    os.makedirs(name, exist_ok=True)

    print(f"[INFO] Creando proyecto '{name}'...")

    # Crear subdirectorios
    for carpeta in estructura:
        os.makedirs(os.path.join(name, carpeta), exist_ok=True)

    # Crear archivos vacíos
    for archivo, path_template in archivos.items():
        print(f"[INFO] Creando archivo '{archivo}' en '{path_template}'...")
        #print(f"[INFO] Creando archivo '{archivo}' en '{archivo}'...")
        if not os.path.exists(path_template):
            print(f"[ERROR] El template del archivo'{archivo}' no existe.")
            return
        #content = env.get_template(path_template)
        #ruta_archivo = os.path.join(name, archivo)
        #with open(ruta_archivo, "w", encoding="utf-8") as f:
        #    f.write(content)

    print(f"[OK] Proyecto '{name}' creado con exito.")