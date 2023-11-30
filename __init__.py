import bpy
from bpy.types import Context

bl_info = {
    "name": "add border strip",
    "description": "VSE内で選択されたストリップをボーダーで囲むためのイメージストリップを作成・追加する",
    "author": "kanta",
    "version": (0, 0),
    "blender": (4, 0, 1),
    "location": "VSE > Sidebar",
    "category": "Sequencer",
}


class AddBorderPanel(bpy.types.Panel):
    bl_label = "Add border strip"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Add Border Strip"

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="PLUGIN")

    def draw(self, context: Context):
        return super().draw(context)


classList = [AddBorderPanel]


def register():
    for c in classList:
        bpy.utils.register_class(c)
    print("add_border_strip: registered")


def unregister():
    for c in classList:
        bpy.utils.unregister_class(c)
    print("add_border_strip: unregistered")


if __name__ == "__main__":
    register()
