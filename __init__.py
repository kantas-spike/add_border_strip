import bpy

bl_info = {
    "name": "add border strip",
    "description": "VSE内で選択されたストリップをボーダーで囲むためのイメージストリップを作成・追加する",
    "author": "kanta",
    "version": (0, 0),
    "blender": (4, 0, 1),
    "location": "VSE > Sidebar",
    "category": "Sequencer",
}


def register():
    print("add_border_strip: registered")


def unregister():
    print("add_border_strip: unregistered")


if __name__ == "__main__":
    register()
