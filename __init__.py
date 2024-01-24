if "bpy" in locals():
    import imp

    imp.reload(border_strip_utils)
else:
    from . import border_strip_utils

import bpy
from bpy.types import Context, Event

bl_info = {
    "name": "add border strip",
    "description": "VSE内で選択されたストリップをボーダーで囲むためのイメージストリップを作成・追加する",
    "author": "kanta",
    "version": (0, 0),
    "blender": (4, 0, 1),
    "location": "VSE > Sidebar",
    "category": "Sequencer",
}

DEFAULT_DURATION = 60


class AddMarkerStripOpertaion(bpy.types.Operator):
    bl_idname = "add_border_strip.add_marker_strip"
    bl_label = "Add Marker Strip"
    bl_description = "枠線画像を挿入するための位置決め用のストリップを追加する"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        se = bpy.context.scene.sequence_editor
        cur_frame = bpy.context.scene.frame_current
        marker_strip: bpy.types.ColorSequence = se.sequences.new_effect(
            name="marker",
            type="COLOR",
            channel=2,
            frame_start=cur_frame,
            frame_end=cur_frame + DEFAULT_DURATION,
        )
        marker_strip.transform.scale_x = 0.5
        marker_strip.transform.scale_y = 0.5
        marker_strip.color = (0, 0.5, 0)
        marker_strip.blend_alpha = 0.3
        marker_strip["generated_by"] = "add_border_strip"
        marker_strip["strip_type"] = "marker"
        se.active_strip = marker_strip

        self.report(type={"INFO"}, message="test")
        return {"FINISHED"}


class AddBorderMainOperation(bpy.types.Operator):
    bl_idname = "add_border_strip.add_border"
    bl_label = "Add Border Image Strip"
    bl_description = "枠線画像を生成しイメージストリップとして追加する"
    bl_options = {"REGISTER", "UNDO"}

    _timer = None

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"

    def modal(self, context: Context, event: Event):
        if event.type == "TIMER":
            context.window_manager.event_timer_remove(self._timer)
            ret = self.add_border_strip(context)
            self._timer = None
            return ret
        else:
            return {"RUNNING_MODAL"}

    def invoke(self, context: Context, event: Event):
        if self._timer:
            self.report({"WARNING"}, "処理中のためキャンセル")
            return {"CANCELLED"}
        self.report({"INFO"}, "処理中...")
        self._timer = context.window_manager.event_timer_add(3.0, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def add_border_strip(self, context):
        target_strip = context.scene.sequence_editor.active_strip
        if target_strip is None:
            self.report({"WARNING"}, "Active Stripがありません")
            return {"CANCELLED"}

        props = context.scene.border_props
        abs_image_dir = border_strip_utils.normalize_image_dir(props.image_dir)
        # print(f"abs_image_dir: {abs_image_dir}")
        if abs_image_dir is None:
            self.report(
                type={"WARNING"},
                message="画像出力先ディレクトリに相対パスが指定されました。.blendファイルを保存してから実行してください",
            )
            return {"CANCELLED"}
        # オペレーターのプロパティーで、imageストリップのdurationを調整可能に
        img_strip = border_strip_utils.create_border_strip(
            target_strip,
            abs_image_dir,
            props.border_size,
            props.border_color,
        )
        org_channel = target_strip.channel
        se = bpy.context.scene.sequence_editor
        se.sequences.remove(target_strip)
        img_strip.channel = org_channel
        se.active_strip = img_strip

        self.report({"INFO"}, "処理が完了しました。")
        return {"FINISHED"}


class AddBorderPanel(bpy.types.Panel):
    bl_label = "Add border strip"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Add Border Strip"
    bl_idname = "ADDBORDER_PT_MainPanel"

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="PLUGIN")

    def draw(self, context):
        props = context.scene.border_props

        layout = self.layout
        layout.label(text="画像出力先ディレクトリ")
        layout.prop(props, "image_dir", text="")
        layout.operator(AddMarkerStripOpertaion.bl_idname, text="位置決め用Stripを挿入")
        layout.separator()
        layout.label(text="ボーダー色")
        layout.prop(props, "border_color", text="")
        layout.separator()
        layout.label(text="ボーダーのサイズ(px)")
        layout.prop(props, "border_size", text="")
        layout.separator()
        row = layout.row(align=True)
        label = "イメージストリップを追加"
        row.operator(AddBorderMainOperation.bl_idname, text=label)
        strip = context.scene.sequence_editor.active_strip
        if (
            strip is not None
            and strip.get("generated_by") == "add_border_strip"
            and strip.get("strip_type") == "marker"
        ):
            row.enabled = True
        else:
            row.enabled = False


class AddBorderProperties(bpy.types.PropertyGroup):
    image_dir: bpy.props.StringProperty(subtype="DIR_PATH", default="//border_imgs")
    border_color: bpy.props.FloatVectorProperty(
        subtype="COLOR_GAMMA", min=0, max=1.0, size=4, default=(1.0, 0, 0, 1)
    )
    border_size: bpy.props.IntProperty(default=10, min=0, max=100)


classList = [
    AddBorderProperties,
    AddBorderMainOperation,
    AddMarkerStripOpertaion,
    AddBorderPanel,
]


def setup_props():
    bpy.types.Scene.border_props = bpy.props.PointerProperty(type=AddBorderProperties)


def clear_props():
    del bpy.types.Scene.border_props


def register():
    for c in classList:
        bpy.utils.register_class(c)
    setup_props()
    print("add_border_strip: registered")


def unregister():
    clear_props()
    for c in classList:
        bpy.utils.unregister_class(c)
    print("add_border_strip: unregistered")


if __name__ == "__main__":
    register()
