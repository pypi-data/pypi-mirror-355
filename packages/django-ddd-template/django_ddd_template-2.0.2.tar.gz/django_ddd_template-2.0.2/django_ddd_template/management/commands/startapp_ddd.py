import os
import shutil
from django.core.management.base import BaseCommand, CommandError
from django.template import Template, Context
from django.template import Engine
from django_ddd_template.templates_registry import TEMPLATES


class Command(BaseCommand):
    help = "Create a Django app with a DDD structure and initial implementation"

    def add_arguments(self, parser):
        parser.add_argument("app_name", type=str)
        parser.add_argument("--base-url", type=str, default=None,
                            help="Custom base URL for the API endpoints")

    def handle(self, *args, app_name=None, **kwargs):
        if not app_name.isidentifier() or app_name != app_name.lower():
            raise CommandError(
                "The app name must be a valid lowercase Python identifier."
            )
        if not app_name:
            raise CommandError("You must provide an app_name")

        base_path = os.getcwd()
        target_path = os.path.join(base_path, app_name)
        template_structure_path = os.path.join(os.path.dirname(__file__), "../../templates/ddd_app")
        engine = Engine(
        dirs=[],
        app_dirs=False,
        context_processors=[],
        debug=False,
        loaders=[],
        string_if_invalid='',
        file_charset='utf-8',
        )

        if os.path.exists(target_path):
            raise CommandError(f"The folder '{app_name}' already exists.")

        # 1. Copiar estructura de carpetas
        shutil.copytree(template_structure_path, target_path)

        # 2. Preparar contexto para las plantillas
        context = {
            "app_name": app_name.lower(),
            "AppName": app_name.title().replace('_', ''),
            "app_name_snake": app_name.lower(),
            "app_name_camel": app_name.title().replace('_', ''),
            "base_url": kwargs.get('base_url') or f"{app_name.lower()}s"
        }

        # 3. Procesar plantillas desde el diccionario TEMPLATES
        for rel_path, template_content in TEMPLATES.items():
            # Procesar nombre del archivo con formato Django
            processed_rel_path = rel_path.format(
                app_name=context["app_name"],
                AppName=context["AppName"]
            )

            # Ruta completa de destino
            dest_path = os.path.join(target_path, processed_rel_path)

            # Asegurar que existe el directorio destino
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # Procesar el contenido de la plantilla con Django Templates
            template = Template(template_content, engine=engine)
            processed_content = template.render(Context(context))

            # Escribir archivo resultante
            with open(dest_path, "w") as f:
                f.write(processed_content)

        self.stdout.write(self.style.SUCCESS(f"App '{app_name}' created with DDD structure and implementation"))