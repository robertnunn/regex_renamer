from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile, Slot
from PySide2.QtWidgets import QApplication
import sys
import json
import re
import os


@Slot()
def preview():
    search_pattern = widget.searchPattern.text()
    search_re = re.compile(search_pattern)
    rep_pattern = widget.repPattern.text()

    # (?<!\\)\$(\d{1,})   finds dollar sign tokens ($1, $2, etc)
    file_list = widget.origList.toPlainText().split("\n")
    new_names = list()
    for i in file_list:
        result = search_re.search(i)
        if result is not None:
            new_name = replace_tokens(rep_pattern, result)
            new_names.append(new_name)

    if len(new_names) > 0:
        widget.renamedList.setPlainText("\n".join(new_names))
    else:
        widget.renamedList.setPlainText("No files matched search criteria!")


def replace_tokens(template_text, match_obj):
    global token_re
    results = set(token_re.findall(template_text))
    new_text = template_text

    for i in results:
        new_text = new_text.replace(f"${i}", match_obj.group(int(i)))

    return new_text


@Slot()
def apply():
    info = get_basics()
    dir_path = info['path']
    search_pattern = info['search']
    rep_pattern = info['replace']

    rename_files(dir_path, search_pattern, rep_pattern)
    dir_changed(dir_path)
    widget.renamedList.clear()


def rename_files(dir_path, search_pattern, rep_pattern):
    if os.path.exists(dir_path):
        file_list = [i.name for i in os.scandir(dir_path) if i.is_file()]
        search_re = re.compile(search_pattern)
        for i in file_list:
            result = search_re.search(i)
            if result is not None:
                new_name = replace_tokens(rep_pattern, result)
                os.rename(f"{dir_path}/{result.group(0)}", f"{dir_path}/{new_name}")
    else:
        print(f'Error: "{dir_path}" does not exist!')


@Slot()
def dir_changed(text):
    if os.path.exists(text):
        orig_list = widget.origList
        orig_list.clear()
        file_list = [i.name for i in os.scandir(text) if i.is_file()]
        widget.origList.setPlainText("\n".join(file_list))
    else:
        pass


@Slot()
def save_preset():
    global presets
    preset_name = widget.presetBox.currentText()
    preset = get_basics()
    presets[preset_name] = {"search": preset["search"], "replace": preset["replace"]}
    save_presets(presets)
    load_presets()
    widget.presetBox.setCurrentText(preset_name)


def save_presets(preset_dict, file_name="presets.json"):
    with open(file_name, "w") as p:
        p.write(json.dumps(preset_dict, indent=4))


def get_basics():
    path = widget.dirPath.text()
    search = widget.searchPattern.text()
    rep = widget.repPattern.text()
    basics = {"path": path, "search": search, "replace": rep}
    return basics


@Slot()
def delete_preset():
    global presets
    del_text = widget.presetBox.currentText()
    if del_text in presets.keys():
        del presets[del_text]
        save_presets(presets)
        init_presets()


def load_presets():
    preset_box = widget.presetBox
    global presets
    with open("presets.json", "r") as p:
        presets = json.loads(p.read())

    preset_box.clear()
    preset_list = [i for i in presets.keys()]
    preset_list.sort()
    preset_box.addItems(preset_list)


@Slot()
def change_preset(index):
    preset = widget.presetBox.currentText()
    if preset != "":
        try:
            new_search_pattern = presets[preset]["search"]
            new_rep_pattern = presets[preset]["replace"]
            widget.searchPattern.setText(new_search_pattern)
            widget.repPattern.setText(new_rep_pattern)
        except Exception as e:
            # print(f"Error changing preset: {e}")
            pass
    else:
        widget.searchPattern.setText("")
        widget.repPattern.setText("")


def set_blank_preset():
    widget.presetBox.setCurrentText("")
    widget.searchPattern.setText("")
    widget.repPattern.setText("")


def init_presets():
    load_presets()
    set_blank_preset()


token_pattern = r"(?<!\\)\$(\d{1,})"
token_re = re.compile(token_pattern)
presets = dict()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    ui_filename = "main.ui"
    app = QApplication([])
    ui_file = QFile(ui_filename)
    loader = QUiLoader()
    widget = loader.load(ui_file, None)
    ui_file.close()
    if not widget:
        print(loader.errorString())
        sys.exit(-1)

    widget.previewChanges.clicked.connect(preview)
    widget.applyChanges.clicked.connect(apply)
    widget.dirPath.textChanged.connect(dir_changed)
    widget.saveButton.clicked.connect(save_preset)
    widget.deleteButton.clicked.connect(delete_preset)
    widget.presetBox.currentTextChanged.connect(change_preset)
    widget.clearButton.clicked.connect(set_blank_preset)
    init_presets()

    widget.show()
    app.exec_()

    # test = r'something $1 else $2 entirely $1'
    # res = re.search(r'^(\d{1,}) - .*(\..{3,})$', '2 - 21xoES.png')
    # print(replace_tokens(test, res))
