import os
from pathlib import Path
from gemini_framework.framework.boot_plant import setup
from gemini_framework.framework.mainmodule import MainModule

gemini_root_dir = Path(__file__).parents[2]


class App:
    def __init__(self, project_path, plant_name):
        self.project_path = project_path
        self.plant_name = plant_name

    def boot(self):
        self.plant = setup(self.project_path, self.plant_name)

        self.mainmodule = MainModule(self.plant)

    def step(self):
        self.mainmodule.step()

    def quit(self):
        # disconnect database
        self.plant.database.disconnect()


if __name__ == "__main__":

    projectpath = os.getenv('GEMINI_PROJECT_FOLDER',
                            os.path.join(gemini_root_dir, 'gemini-project'))
    plantname = os.getenv('GEMINI_PLANT', '')

    if not plantname == '':
        app = App(projectpath, plantname)
        app.boot()
        app.step()
        app.quit()
    else:
        print('plant name is not defined')
