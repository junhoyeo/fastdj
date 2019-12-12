import os, sys, platform
try:
    setup_file = __import__(sys.argv[1])
except:
    print("Try with an argument")
    exit()

from template import Template


class ProjectCommand:  # class about project initializing, like commands
    def __init__(self, prj_name):
        self.prj_name = prj_name

    def setup_venv(self):
        command = ""
        if platform.system() == 'Windows':
            command = "python "
        else:
            command = "python3 "
        command += "-m venv myvenv"
        os.system(command)

    def install_requirements(
            self
    ):  # pip install django djangorestframework django-cors-headers
        os.system("pip install --upgrade pip")
        os.system("pip install django djangorestframework django-cors-headers")

    def start_project(self):
        os.system("django-admin startproject " + str(self.prj_name))

    def create_app(self, app_name):
        origin_directory = os.getcwd()
        os.chdir(f"{os.getcwd()}/{self.prj_name}/")
        os.system(f"python manage.py startapp {app_name}")
        open(f"{os.getcwd()}/{app_name}/urls.py", 'w').close()
        os.chdir(origin_directory)

    def makemigrations(self):
        origin_directory = os.getcwd()
        os.chdir(f"{os.getcwd()}/{self.prj_name}/")
        os.system(f"python manage.py makemigrations")
        os.chdir(origin_directory)

    def migrate(self):
        origin_directory = os.getcwd()
        os.chdir(f"{os.getcwd()}/{self.prj_name}/")
        os.system(f"python manage.py migrate")
        os.chdir(origin_directory)


class ProjectConfigurations:
    def __init__(self, project_name):
        self.settings_file_path = f"{os.getcwd()}/{project_name}/{project_name}/settings.py"
        self.urls_file_path = f"{os.getcwd()}/{project_name}/{project_name}/urls.py"

    def load_settings(self):
        settings_file = open(self.settings_file_path, 'r')
        self.settings = settings_file.read()
        settings_file.close()

    def set_language_code(self, language):
        self.settings = self.settings.replace("LANGUAGE_CODE = en-us",
                                              f"LANGUAGE_CODE = '{language}'")

    def set_timezone(self, timezone):
        self.settings = self.settings.replace("TIME_ZONE = 'UTC'",
                                              f"TIMEZONE = '{timezone}'")

    def load_urls(self):
        urls_file = open(self.urls_file_path, 'r')
        self.urls = urls_file.read()
        urls_file.close()

    def add_module(self, module_name):
        installed_apps_index = self.settings.find("INSTALLED_APPS")
        last_module_index = self.settings.find(
            "]", installed_apps_index) - 1  # except itself and the '\n
        self.settings = self.settings[:
                                      last_module_index] + "\n\t# added by fastdj\n\t'" + module_name + "'," + self.settings[
                                          last_module_index:]

    def add_installed_modules(self):  # djangorestframework django-cors-headers
        modules = ['rest_framework', 'corsheaders']
        for module in modules:
            self.add_module(module)

    def add_token_login_model(self):  # token login model
        self.settings += "\n# added by fastdj\nREST_FRAMEWORK = {\n\t'DEFAULT_AUTHENTICATION_CLASSES': (\n\t\t'rest_framework.authentication.BasicAuthentication',\n\t\t'rest_framework.authentication.TokenAuthentication',\n\t),\n}\n"
        self.add_module('rest_framework.authtoken')

    def set_cross_origin_all(self):  # cors origin allow all
        self.settings += "\n# added by fastdj\nCORS_ORIGIN_ALLOW_ALL = True\nCORS_ALLOW_CREDENTIALS = True\n"

    def set_allowed_hosts_all(self):  # set allowed hosts to all
        self.settings = self.settings.replace("ALLOWED_HOSTS = []",
                                              "ALLOWED_HOSTS = ['*']")

    def add_url_include_module(self):
        self.urls = self.urls.replace("from django.urls import path",
                                      "from django.urls import path, include")

    def add_url_path(self, app_name):
        urlpatterns_index = self.urls.find("urlpatterns")
        last_path_index = self.urls.find(
            "]", urlpatterns_index) - 1  # except itself and the '\n
        self.urls = f"{self.urls[:last_path_index]}\n\t# added by fastdj\n\tpath('{app_name}/', include('{app_name}.urls'), name='{app_name}'),{self.urls[last_path_index:]}\n"

    def save_settings(self):
        file = open(self.settings_file_path, 'w')
        file.write(self.settings)
        file.close()

    def save_urls(self):
        file = open(self.urls_file_path, 'w')
        file.write(self.urls)
        file.close()


class Field:
    def __init__(self,
                 app_name,
                 name,
                 template=None,
                 field=None,
                 options=list(),
                 serializers={},
                 **kwargs):
        self.name = name
        self.app_name = app_name
        self.field = field
        self.serializers = serializers
        self.options = options
        self.choices = kwargs.get('choices')
        if template == Template.model_owner:
            self.field = "ForeignKey"
            self.options = [
                "'auth.user'", f"related_name='{self.app_name}_{name}'",
                "on_delete=models.CASCADE", "null=False"
            ]
            self.serializers = {
                "field": "ReadOnlyField",
                "options": ["source='writer.username'"]
            }

    def get_code(self):
        if not self.choices == None:
            self.options.append(f"choices={self.choices}")
        options_str = ""
        for option in self.options:
            options_str += option + ", "
        options_str = options_str[:-2]  # to remove last ", "
        code = ""
        code += f"\t{self.name} = models.{self.field}({options_str})\n"
        return code


class Model:
    def __init__(self, name):
        self.name = name
        self.fields = list()

    def add_field(self, field):
        self.fields.append(field)

    def get_serializers_code(self):
        code = ""
        for field in self.fields:
            options_str = ""
            for option in field.serializers.get("options", list()):
                options_str += option + ", "
            options_str = options_str[:-2]  # to remove last ", "
            field_object = field.serializers.get('field')
            if field_object == None:
                break
            code += f"\t{field.name} = serializers.{field_object}({options_str})\n"
        code += "\tclass Meta:\n"
        code += f"\t\tmodel = {self.name}\n"
        fields_str = ""
        for field in self.fields:
            fields_str += field.name + ", "
        fields_str = fields_str[:-2]  # to remove last ", "
        code += f"\t\tfields = ({fields_str})"
        return code

    def get_model_code(self):
        code = f"class {self.name}(models.Model):\n"
        for field in self.fields:
            code += field.get_code()
        return code


class ViewSet:
    def __init__(self, app_name, name, **kwargs):
        self.name = name
        self.app_name = app_name
        self.template = kwargs.get('template')
        self.model_name = kwargs.get('model_name')
        self.options = kwargs.get('options', list())
        self.permissions = kwargs.get('permissions', "")
        self.url_getters = kwargs.get('url_getters', "")
        self.SERIALIZER = f"{self.model_name}Serializer"
        self.modules = list()
        self.modules.append(
            f"from {self.app_name}.model import {self.model_name}")
        self.modules.append(
            f"from {self.app_name}.serializers import {self.SERIALIZER}")
        self.owner_field_name = kwargs.get('owner_field_name')
        self.code = str()

    def _use_generic_based_template(self):
        self.modules.append("from rest_framework import generics")
        self.modules.append("from rest_framework import permissions")

    def _get_template_code(self):
        code = f"\tqueryset = {self.model_name}.objects.all()\n"
        code += f"\tserializer_class = {self.SERIALIZER}\n"
        code += f"\tpermission_classes = (permissions.{self.permissions})\n"
        return code

    def update_code(self):  # test required
        code = str()
        self.modules.append("from rest_framework.response import Response")
        if self.template == Template.detail_view:
            self._use_generic_based_template()
            code = f"class {self.name}(generics.RetreiveAPIView):\n"
            code += self._get_template_code()
        elif self.template == Template.detail_view_u:
            self._use_generic_based_template()
            code = f"class {self.name}(generics.RetreiveUpdateAPIView):\n"
            code += self._get_template_code()
        elif self.template == Template.detail_view_d:
            self._use_generic_based_template()
            code = f"class {self.name}(generics.RetreiveDestroyAPIView):\n"
            code += self._get_template_code()
        elif self.template == Template.detail_view_ud:
            self._use_generic_based_template()
            code = f"class {self.name}(generics.RetreiveUpdateDestroyAPIView):\n"
            code += self._get_template_code()
        elif self.template == Template.all_objects_view:
            self._use_generic_based_template()
            self.modules.append("from django.http import JsonResponse")
            code = f"class {self.name}(generics.ListAPIView, APIView):\n"
            code += self._get_template_code()
            code += "\n\tdef post(self, request):\n"
            code += "\t\tif request.user.is_authenticated:\n"
            code += f"\t\t\tserializer = {self.SERIALIZER}(data=request.data)\n"
            code += f"\t\t\tif serializer.is_valid():\n"
            code += f"\t\t\t\tserializer.save({self.owner_field_name}=request.user)\n"
            code += f"\t\t\t\treturn JsonResponse(serializer.data, status=status.HTTP_201_CREATED)\n"
            code += f"\t\t\treturn Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)\n"
            code += f"\t\treturn Response(status=status.HTTP_401_UNAUTHORIZED)\n"
        elif self.template == Template.filter_objects_view:
            self.modules.append(
                "from rest_framework.decorators import api_view")
            code = f"@api_view(['GET'])\n"
            code += f"def {self.name}(request, {self.url_getters})\n"
            options_str = ""
            for option in self.options:
                options_str += option + ", "
            options_str = options_str[:-2]  # to remove last ", "
            code += f"\tobject = get_object_or_404({self.model_name}, {options_str}).values()\n"
            code += f"\treturn Response(object)"
        elif self.template == Template.user_register_view:
            self.modules.append(
                "from rest_framework.decorators import api_view")
            self.modules.append(
                f"from {self.app_name}.forms import RegisterForm")
            code = f"""@api_view(['POST'])
def register(request):  # 회원가입
    form = RegisterForm(request.POST)
    if form.is_valid():
        user = form.save(commit=False)
        user.save()
        profile = Profile.objects.get(user=user)
        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(status=status.HTTP_201_CREATED)
    return Response(form.errors, status=status.HTTP_406_NOT_ACCEPTABLE)
            """
            import pdb
            pdb.set_trace()
        else:
            code = ""
        self.code = code

    def get_code(self):
        return self.code


class App:
    def __init__(self, name, project_name):
        self.name = name
        self.project_name = project_name
        self.models = list()
        self.views = list()
        self.models_code = ""
        self.views_code = ""

    def add_model(self, model):
        self.models.append(model)

    def add_view(self, view):
        self.views.append(view)

    def get_models_code(self):
        code = ""
        if self.name == "custom_user":
            code += "from django.conf import settings\n"
        for model in self.models:
            code += model.get_model_code() + "\n"
        return code

    def get_serializers_code(self):
        code = "from rest_framework import serializers\n"
        code += f"from {self.name}.models import {self.name}\n"

        for model in self.models:
            code += f"class {model.name}Serializer(serializers.ModelSerializer):\n"
            code += model.get_serializers_code()
            code += "\n"
        return code

    def get_views_code(self):
        modules_code = ""
        code = ""
        modules = list()
        for view in self.views:
            view.update_code()
            for module in set(view.modules):
                modules.append(module)
            code += view.get_code() + "\n"
        for module in set(modules):  # used set to remove duplicates
            modules_code += module + "\n"
        return modules_code + "\n" + code

    def save_models(self):
        file = open(f"{os.getcwd()}/{self.project_name}/{self.name}/models.py",
                    'a')
        file.write(self.get_models_code())
        file.close()

    def save_serializers(self):
        file = open(
            f"{os.getcwd()}/{self.project_name}/{self.name}/serializers.py",
            'w')
        file.write(self.get_serializers_code())
        file.close()

    def save_views(self):
        file = open(f"{os.getcwd()}/{self.project_name}/{self.name}/views.py",
                    'w')
        file.write(self.get_views_code())
        file.close()

    def save_views(self):
        file = open(f"{os.getcwd()}/{self.project_name}/{self.name}/views.py",
                    'w')
        file.write(self.get_views_code())
        file.close()


class Project:
    project_name = setup_file.project_name
    user_model = setup_file.user_model

    def __init__(self):
        self.apps = list()

        for app in setup_file.apps.keys():
            self.apps.append(App(app, self.project_name))
        self.apps.append(App('custom_user', self.project_name))

        self.cmd = ProjectCommand(self.project_name)
        self.confs = ProjectConfigurations(self.project_name)
        self.timezone = None
        self.language = None
        self.use_token_auth = self.user_model.get('use_token_auth', True)
        try:
            self.timezone = setup_file.timezone
        except:
            pass
        try:
            self.language = setup_file.language
        except:
            pass

    def menu(self):
        print("0. Create a new venv")
        print("1. Create your project")
        option_choice = int(input("Type here: "))
        if (option_choice == 0):
            self.create_venv()
        elif (option_choice == 1):
            self.create_project()
            self.create_apps()
            self.register_apps()
            # disabled till writing url feature is done
            #self.makemigrations_and_migrate()

    def create_venv(self):
        self.cmd.setup_venv()
        if platform.system() == "windows":
            print(
                "Type 'call myvenv/scripts/activate', re-execute the script and type 1!"
            )
            return
        print(
            "Type 'source myvenv/bin/activate', re-execute the script and type 1!"
        )

    def create_project(self):
        self.cmd.install_requirements()
        # setting up project
        self.cmd.start_project()
        self.confs.load_settings()
        self.confs.load_urls()
        self.confs.add_installed_modules()
        self.confs.set_cross_origin_all()
        self.confs.set_allowed_hosts_all()
        if self.use_token_auth == True:
            self.confs.add_token_login_model()
        if not self.timezone == None:
            self.confs.set_timezone(self.timezone)
        if not self.language == None:
            self.confs.set_language_code(self.language)

    def create_apps(self):
        for app in self.apps:
            self.cmd.create_app(app.name)

    def get_serialized_field(self, app_name, field_name, field_specs):
        return Field(app_name,
                     field_name,
                     field_specs.get('template'),
                     field_specs.get('field'),
                     field_specs.get('options', list()),
                     field_specs.get('serializers', {}),
                     choices=field_specs.get('choices'))

    def register_apps(self):
        self.confs.add_url_include_module()
        for app in self.apps:
            # add apps to confs and urls
            self.confs.add_module(app.name)
            self.confs.add_url_path(app.name)
            # register model spces to object
            if app.name == 'custom_user':
                model = Model("Profile")
                fields_name = field_specs = self.user_model.get(
                    'fields').keys()
                for field_name in fields_name:
                    field_specs = self.user_model.get('fields').get(
                        field_name)  # test required, not done yet
                    model.add_field(
                        self.get_serialized_field(app.name, field_name,
                                                  field_specs))
                model.add_field(self, get)
                app.add_model(model)
            else:
                models_name = setup_file.apps[app.name]['models'].keys()
                for model_name in models_name:
                    model = Model(model_name)
                    fields_name = setup_file.apps[
                        app.name]['models'][model_name].keys()
                    for field_name in fields_name:
                        field_specs = setup_file.apps[
                            app.name]['models'][model_name][field_name]
                        model.add_field(
                            self.get_serialized_field(app.name, field_name,
                                                      field_specs))
                    app.add_model(model)

            # register view specs to object
            if app.name == 'custom_user':
                if self.user_model.get('set_visibility_public', True):
                    app.add_view(
                        ViewSet(app.name,
                                "register",
                                template=Template.user_register_view,
                                model_name="Profile"))
                app.add_view(
                    ViewSet(
                        app.name,
                        "ProfileAPIView",
                        model_name="Profile",
                    ))

            else:
                for view_name in setup_file.apps[app.name]['views'].keys():
                    view = setup_file.apps[app.name]['views'].get(view_name)
                    app.add_view(
                        ViewSet(app.name,
                                view_name,
                                template=view.get('template'),
                                model_name=view.get('model'),
                                options=view.get('options', list()),
                                permissions=view.get('permissions', ""),
                                url_getters=view.get('url_getters', ""),
                                owner_field_name=view.get(
                                    'owner_field_name', None)))
            app.save_models()
            app.save_serializers()
            app.save_views()
        self.confs.save_settings()
        self.confs.save_urls()

        # save changes

    def makemigrations_and_migrate(self):
        self.cmd.makemigrations()
        self.cmd.migrate()


def main():
    project = Project()
    project.menu()


main()
