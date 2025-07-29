# django_ddd_template/cli.py
import sys
from django_ddd_template.management.commands.startapp_ddd import Command

def main():
    if len(sys.argv) < 3 or sys.argv[1] != "startapp":
        print("Uso: django-ddd startapp <nombre_app>")
        return 1

    app_name = sys.argv[2]
    command = Command()
    command.handle(app_name=app_name)
    return None
