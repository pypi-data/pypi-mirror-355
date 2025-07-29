import os
import mimetypes
import re
import subprocess

from kabaret import flow
from kabaret.app import resources
from libreflow.baseflow.task import Task
from libreflow.baseflow.file import GenericRunAction
from libreflow.baseflow.runners import FILE_EXTENSION_ICONS

from libreflow.baseflow.file import (
    RenderAEPlayblast,
    SelectAEPlayblastRenderMode,
    TrackedFile,
    TrackedFolder,
    MarkImageSequence,
    WaitProcess,
)

from . import scripts


#
#       PLAYBLAST
#


class RenderQualityChoiceValue(flow.values.ChoiceValue):
    CHOICES = ["Preview", "Final"]


class AfterFX_Playblast_Comp(SelectAEPlayblastRenderMode):
    # Action startup with parameter selection

    ICON = ("icons.libreflow", "afterfx")

    render_quality = flow.Param("Preview", RenderQualityChoiceValue)

    def get_buttons(self):
        return ["Render", "Cancel"]

    def run(self, button):
        if button == "Cancel":
            return

        # Get AfterEffects templates configured in current site
        site = self.root().project().get_current_site()
        render_settings = (site.ae_render_settings_templates.get() or {}).get(
            self.render_settings.get()
        )
        output_module = (site.ae_output_module_templates.get() or {}).get(
            self.output_module.get()
        )
        audio_output_module = site.ae_output_module_audio.get()

        if button == "Render":
            render_action = self._file.render_ae_playblast
            render_action.render_quality.set(self.render_quality.get())
            render_action.revision.set(self.revision.get())
            render_action.render_settings.set(render_settings)
            render_action.output_module.set(output_module)
            render_action.audio_output_module.set(audio_output_module)
            render_action.start_frame.set(self.start_frame.get())
            render_action.end_frame.set(self.end_frame.get())

            if (
                self.start_frame.get() is not None or self.end_frame.get() is not None
            ) and self._has_render_folder():
                return self.get_result(
                    next_action=self._file.select_ae_playblast_render_mode_page2.oid()
                )

            render_action.run("Render")


class AfterFX_Render_Playblast(RenderAEPlayblast):
    # Render img sequence in after fx

    render_quality = flow.Param()

    def _render_wait(self, folder_name, revision_name, render_pid, export_audio_pid):
        render_wait = self._file.final_render_wait
        render_wait.folder_name.set(folder_name)
        render_wait.revision_name.set(revision_name)
        render_wait.wait_pid(render_pid)
        render_wait.wait_pid(export_audio_pid)
        render_wait.run(None)

    def run(self, button):
        if button == "Cancel":
            return

        revision_name = self.revision.get()

        # Render image sequence
        ret = self._render_image_sequence(
            revision_name,
            self.render_settings.get(),
            self.output_module.get(),
            self.start_frame.get(),
            self.end_frame.get(),
        )
        render_runner = (
            self.root()
            .session()
            .cmds.SubprocessManager.get_runner_info(ret["runner_id"])
        )
        # Export audio
        ret = self._export_audio(revision_name, self.audio_output_module.get())
        export_audio_runner = (
            self.root()
            .session()
            .cmds.SubprocessManager.get_runner_info(ret["runner_id"])
        )

        folder_name = self._file.name()[: -len(self._file.format.get())]
        folder_name += "render"

        if self.render_quality.get() == "Preview":
            # Configure and start image sequence marking for preview output
            self._mark_image_sequence(
                folder_name,
                revision_name,
                render_pid=render_runner["pid"],
                export_audio_pid=export_audio_runner["pid"],
            )

        if self.render_quality.get() == "Final":
            # Configure and start image sequence conversion for final output
            self._render_wait(
                folder_name,
                revision_name,
                render_pid=render_runner["pid"],
                export_audio_pid=export_audio_runner["pid"],
            )


class Final_Render_Waiting(WaitProcess):
    # Image sequence conversion for Final output

    _file = flow.Parent()
    _files = flow.Parent(2)
    _task = flow.Parent(3)

    folder_name = flow.Param()
    revision_name = flow.Param()

    def get_run_label(self):
        return "Convert image sequence"

    def _ensure_file_revision(self, name, revision_name):
        mng = self.root().project().get_task_manager()
        default_files = mng.get_task_files(self._task.name())

        # Find matching default file
        match_dft_file = False
        for file_mapped_name, file_data in default_files.items():
            # Get only files
            if "." in file_data[0]:
                base_name, extension = os.path.splitext(file_data[0])
                if name == base_name:
                    extension = extension[1:]
                    path_format = file_data[1]
                    match_dft_file = True
                    break

        # Fallback to default mov container
        if match_dft_file is False:
            extension = "mov"
            path_format = mng.get_task_path_format(
                self._task.name()
            )  # get from default task

        mapped_name = name + "_" + extension

        if not self._files.has_mapped_name(mapped_name):
            file = self._files.add_file(
                name, extension, tracked=True, default_path_format=path_format
            )
        else:
            file = self._files[mapped_name]

        if not file.has_revision(revision_name):
            revision = file.add_revision(revision_name)
            file.set_current_user_on_revision(revision_name)
        else:
            revision = file.get_revision(revision_name)

        file.file_type.set("Outputs")
        file.ensure_last_revision_oid()

        return revision

    def _get_first_image_path(self, revision):
        img_folder_path = revision.get_path()

        for f in os.listdir(img_folder_path):
            file_path = os.path.join(img_folder_path, f)
            file_type = mimetypes.guess_type(file_path)[0].split("/")[0]

            if file_type == "image":
                return file_path

        return None

    def _get_audio_path(self, folder_name):
        if any("_aep" in file for file in self._files.mapped_names()):
            scene_name = folder_name.replace("_render", "_aep")
        else:
            scene_name = re.search(r"(.+?(?=_render))", folder_name).group()

        if not self._files.has_mapped_name(scene_name):
            # Scene not found
            return None

        return self._files[scene_name].export_ae_audio.get_audio_path()

    def launcher_exec_func_kwargs(self):
        return dict(
            folder_name=self.folder_name.get(), revision_name=self.revision_name.get()
        )

    def _do_after_process_ends(self, *args, **kwargs):
        self.root().project().ensure_runners_loaded()
        sequence_folder = self._files[kwargs["folder_name"]]

        rev = sequence_folder.get_revision(kwargs["revision_name"])
        path = self._get_first_image_path(rev)
        input_path = path.replace("0000.png", r"%04d.png")

        print("INPUT_PATH = " + input_path)

        output_name = kwargs["folder_name"].replace("_render", "_movie")
        output_rev = self._ensure_file_revision(output_name, kwargs["revision_name"])
        output_path = output_rev.get_path()

        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))

        print("OUTPUT PATH = " + output_path)

        audio_path = self._get_audio_path(kwargs["folder_name"])

        print("AUDIO PATH = " + audio_path)

        process = subprocess.run(
            f"ffmpeg -y -r 25 -i {input_path} -i {audio_path} -c:a aac -map 0:0 -map 1:0 -c:v prores_ks -profile:v 3 -vendor apl0 -bits_per_mb 8000 -pix_fmt yuv422p10le {output_path}",
            check=False,
            shell=True,
        )

        print(f"COMMAND:\n{' '.join(process.args)}")
        print(f"STDERR: {repr(process.stderr)}")
        print(f"STDOUT: {process.stdout}")
        print(f"RETURN CODE: {process.returncode}")

        if not os.path.exists(output_path):
            self.message.set(
                (
                    "<h2>Upload playblast to Kitsu</h2>"
                    "<font color=#FF584D>File conversion failed</font>"
                )
            )
            return self.get_result(close=False)


class MarkSequencePreview(MarkImageSequence):
    # Image sequence marking and conversion for preview output

    def mark_sequence(self, revision_name):
        # Compute playblast prefix
        prefix = self._folder.name()
        prefix = prefix.replace("_render", "")

        source_revision = self._file.get_revision(revision_name)
        revision = self._ensure_file_revision(prefix + "_preview_movie", revision_name)
        revision.comment.set(source_revision.comment.get())

        # Get the path of the first image in folder
        img_path = self._get_first_image_path(revision_name)

        # Get original file name to print on frames
        if self._files.has_mapped_name(prefix + "_aep"):
            scene = self._files[prefix + "_aep"]
            file_name = scene.complete_name.get() + "." + scene.format.get()
        else:
            file_name = self._folder.complete_name.get()

        self._extra_argv = {
            "image_path": img_path,
            "video_output": revision.get_path(),
            "file_name": file_name,
            "audio_file": self._get_audio_path(),
        }

        return super(MarkImageSequence, self).run("Render")

#
#       SCENE BUILDER
#

class CompDependency(flow.Object):
    task_name = flow.Computed()
    file_name = flow.Computed()
    revision = flow.Computed()
    path = flow.Computed()

    _map = flow.Parent()

    def extension(self):
        ext = os.path.splitext(self.file_name.get())[1]
        if ext:
            ext = ext[1:]
        return ext

    def compute_child_value(self, child_value):
        if child_value is self.task_name:
            self.task_name.set(self._map.get_task_name(self.name()))
        elif child_value is self.file_name:
            self.file_name.set(self._map.get_file_name(self.name()))
        elif child_value is self.revision:
            self.revision.set(self._map.get_revision(self.name()))
        elif child_value is self.path:
            self.path.set(self._map.get_path(self.name()))


class RefreshDependencies(flow.Action):
    ICON = ("icons.libreflow", "refresh")

    _map = flow.Parent()

    def needs_dialog(self):
        return False

    def run(self, button):
        self._map.touch()


class CompDependencies(flow.DynamicMap):
    ICON = ("icons.libreflow", "dependencies")
    STYLE_BY_STATUS = {"available": ("icons.gui", "available")}

    refresh = flow.Child(RefreshDependencies)

    _action = flow.Parent()
    _sequence = flow.Parent(6)
    _shot = flow.Parent(4)

    @classmethod
    def mapped_type(cls):
        return CompDependency

    def __init__(self, parent, name):
        super(CompDependencies, self).__init__(parent, name)
        self._dependencies_data = None

    def mapped_names(self, page_num=0, page_size=None):
        if self._dependencies_data is None:
            self._dependencies_data = {}

            for task_name, file_name, revision in self._get_dependencies():
                mapped_name = "%s_%s" % (task_name, file_name.replace(".", "_"))
                self._dependencies_data[mapped_name] = {
                    "task_name": task_name,
                    "file_name": file_name,
                    "path": revision.get_path() if revision else None,
                    "revision": revision.name() if revision else None,
                }

        self._action.get_buttons()

        return self._dependencies_data.keys()

    def columns(self):
        return ["Status", "Dependency", "Revision"]

    def get_dependency(self, department, file_name):
        mapped_name = "%s_%s" % (department, file_name.replace(".", "_"))
        try:
            return self.get_mapped(mapped_name)
        except flow.exceptions.MappedNameError:
            return None

    def get_task_name(self, mapped_name):
        self.mapped_names()
        return self._dependencies_data[mapped_name]["task_name"]

    def get_file_name(self, mapped_name):
        self.mapped_names()
        return self._dependencies_data[mapped_name]["file_name"]

    def get_revision(self, mapped_name):
        self.mapped_names()
        return self._dependencies_data[mapped_name]["revision"]

    def get_path(self, mapped_name):
        self.mapped_names()
        return self._dependencies_data[mapped_name]["path"]

    def touch(self):
        self._dependencies_data = None
        super(CompDependencies, self).touch()

    def _get_dependencies(self):
        deps = [
            (("background", "background.psd"), None),
            (("animatic", "animatic_edit.mov"), None),
            (("compositing", "layers"), None),
        ]
        return [self._get_dependency_data(d) for d in deps]

    def _get_dependency_data(self, dependency):
        revision = None
        target, optional = dependency
        task_name = file_name = None

        if type(target) is tuple:
            task_name, file_name = target
            revision = self._get_target_revision(task_name, file_name)
        elif type(target) is list:
            # Get the first existing dependency
            for t, f in target:
                task_name, file_name = t, f
                revision = self._get_target_revision(task_name, file_name)
                if revision is not None:
                    break

        return task_name, file_name, revision

    def _get_target_revision(self, task_name, file_name):
        file_name = file_name.replace(".", "_")
        oid = f"{self._shot.oid()}/tasks/{task_name}/files/{file_name}"
        r = None

        try:
            f = self.root().get_object(oid)
        except (ValueError, flow.exceptions.MappedNameError):
            pass
        else:
            r = f.get_head_revision()
            if r is not None and not r.exists():
                r = None

        return r

    def _fill_row_cells(self, row, item):
        row["Status"] = ""
        row["Dependency"] = "%s/%s" % (
            item.task_name.get() or "undefined",
            item.file_name.get() or "undefined",
        )
        row["Revision"] = item.revision.get()

    def _fill_row_style(self, style, item, row):
        style["Status_icon"] = (
            "icons.libreflow",
            "warning" if item.path.get() is None else "available",
        )

        style["Dependency_icon"] = FILE_EXTENSION_ICONS.get(
            item.extension(), ("icons.gui", "folder-white-shape")
        )


class InitCompScene(GenericRunAction):
    ICON = ("icons.libreflow", "afterfx")

    dependencies = flow.Child(CompDependencies).ui(expanded=True)

    _task = flow.Parent()
    _shot = flow.Parent(3)
    _sequence = flow.Parent(5)

    def __init__(self, parent, name):
        super(InitCompScene, self).__init__(parent, name)
        self._comp_scene_path = None
        self.missing_deps = False

    def allow_context(self, context):
        return context

    def runner_name_and_tags(self):
        return "AfterEffects", []

    def get_run_label(self):
        return "Build compositing scene"

    def target_file_extension(self):
        return "aep"

    def needs_dialog(self):
        return True

    def get_buttons(self):
        msg = "<h2>Build compositing shot</h2>"
        if any(
            data["path"] is None
            for data in self.dependencies._dependencies_data.values()
        ):
            self.missing_deps = True
            msg += "\n<font color=#FFA34D>Some dependencies are not available on your site.</font>\n"
        else:
            self.missing_deps = False

        self.message.set(msg)
        return ["Build", "Cancel"]

    def extra_argv(self):
        kitsu_api = self.root().project().kitsu_api()

        script_path = resources.get("scripts", "init_comp_scene.jsx").replace("\\", "/")
        preset_path = resources.get("scripts", "vignette_effect.ffx").replace("\\", "/")
        width = 3840
        height = 1634
        fps = 25
        duration = kitsu_api.get_shot_duration(self._shot.name(), self._sequence.name())

        base_comp_name = f"{self._sequence.name()}_{self._shot.name()}"

        script_str = f"//@include '{script_path}'\n\nsetupScene('{base_comp_name}', {width}, {height}, {fps}, {duration}, '{preset_path}');\n"

        # Import Background
        background_path = self.get_dependency_path("background", "background.psd")
        if background_path is not None:
            script_str += f"importPSDBackground('{background_path}', {fps}, {duration}, '{base_comp_name}');\n"

        # Import Animatic
        animatic_path = self.get_dependency_path("animatic", "animatic_edit.mov")
        if animatic_path is not None:
            script_str += f"importAnimatic('{animatic_path}', '{base_comp_name}');\n"

        # Import TVPaint layers
        layers_path = self.get_dependency_path("compositing", "layers")
        json_name = f"{self._sequence.name()}_{self._shot.name()}_layers_data.json"
        if layers_path is not None:
            script_str += f"importAnimationLayers('{layers_path}', '{json_name}', '{base_comp_name}');\n"

        # Save After Effects file
        script_str += f"saveScene('{self._comp_scene_path}', '{base_comp_name}');\n"

        args = ["-m", "-s", script_str]
        # args = ['-m', '-s', script_str, '-noui']
        return args

    def get_dependency_path(self, task_name, file_name):
        path = None
        d = self.dependencies.get_dependency(task_name, file_name)
        if d is not None:
            path = d.path.get().replace("\\", "/")

        return path

    def get_path_format(self, task_name, file_mapped_name):
        mng = self.root().project().get_task_manager()
        if not mng.default_tasks.has_mapped_name(task_name):  # check default task
            # print(f'Scene Builder - no default task {task_name} -> use default template')
            return None

        dft_task = mng.default_tasks[task_name]
        if not dft_task.files.has_mapped_name(file_mapped_name):  # check default file
            # print(f'Scene Builder - default task {task_name} has no default file {filename} -> use default template')
            return None

        dft_file = dft_task.files[file_mapped_name]
        return dft_file.path_format.get()

    def ensure_comp_scene(self):
        files = self._task.files
        name = "compositing"
        ext = "aep"
        file_name = "%s_%s" % (name, ext)
        path_format = self.get_path_format(self._task.name(), file_name)

        if files.has_file(name, ext):
            _file = files[file_name]
        else:
            _file = files.add_file(
                name=name,
                extension=ext,
                tracked=True,
                default_path_format=path_format,
            )
        _file.create_working_copy()
        rev = _file.publish(comment="Created with comp scene builder")
        return rev.get_path()

    def run(self, button):
        if button == "Cancel":
            return
        if self.missing_deps:
            return self.get_result(close=False)

        self._comp_scene_path = self.ensure_comp_scene().replace("\\", "/")

        return super(InitCompScene, self).run(button)


def build_scene(parent):
    if isinstance(parent, Task) and "comp" in parent.name():
        init_comp_scene = flow.Child(InitCompScene).ui(dialog_size=(600, 450))
        init_comp_scene.name = "init_comp_scene"
        init_comp_scene.index = None
        return [
            init_comp_scene,
        ]


def afterfx_render_playblast(parent):
    if (
        isinstance(parent, TrackedFile)
        and (parent.name().endswith("_aep"))
        and (parent._task.name() == "compositing")
    ):
        r = flow.Child(AfterFX_Render_Playblast)
        r.name = "render_ae_playblast"
        r.ui(hidden=True)
        return r


def afterfx_playblast_comp(parent):
    if (
        isinstance(parent, TrackedFile)
        and (parent.name().endswith("_aep"))
        and (parent._task.name() == "compositing")
    ):
        r = flow.Child(AfterFX_Playblast_Comp)
        r.name = "render_playblast"
        r.ui(label="Render")
        return r


def mark_sequence_preview(parent):
    if isinstance(parent, TrackedFolder) and (parent._task.name() == "compositing"):
        r = flow.Child(MarkSequencePreview)
        r.name = "mark_image_sequence"
        r.ui(hidden=True)
        return r


def final_render_wait(parent):
    if isinstance(parent, TrackedFile) and (parent._task.name() == "compositing"):
        r = flow.Child(Final_Render_Waiting)
        r.name = "final_render_wait"
        r.ui(hidden=True)
        return r


def install_extensions(session):
    return {
        "2h14_comp": [
            afterfx_playblast_comp,
            afterfx_render_playblast,
            mark_sequence_preview,
            final_render_wait,
            build_scene,
        ]
    }
