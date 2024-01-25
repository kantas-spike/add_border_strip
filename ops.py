import bpy
import datetime
from bpy.types import Context, Event
from . import border_strip_utils


class AddPlaceholderStripOpertaion(bpy.types.Operator):
    bl_idname = "add_border_strip.add_placeholder_strip"
    bl_label = "Add Placeholder Strip"
    bl_description = "枠線画像を挿入するための位置決め用のストリップを追加する"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.border_props
        se = bpy.context.scene.sequence_editor
        cur_frame = bpy.context.scene.frame_current
        placeholder_strip: bpy.types.ColorSequence = se.sequences.new_effect(
            name="placeholder",
            type="COLOR",
            channel=props.placeholder_channel,
            frame_start=cur_frame,
            frame_end=cur_frame + props.placeholder_duration,
        )

        placeholder_strip.transform.scale_x = props.placeholder_scale_x
        placeholder_strip.transform.scale_y = props.placeholder_scale_y
        placeholder_strip.color = props.placeholder_color[0:3]
        placeholder_strip.blend_alpha = props.placeholder_color[3]
        placeholder_strip["generated_by"] = "add_border_strip"
        placeholder_strip["strip_type"] = "placeholder"
        placeholder_strip[
            "placeholder_id"
        ] = f"{placeholder_strip.name}_{datetime.datetime.now().timestamp()}"
        strip = se.active_strip
        if strip is not None:
            strip.select = False
        se.active_strip = placeholder_strip

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
            target_strip = context.scene.sequence_editor.active_strip
            ret = self.add_border_strip(context, target_strip)
            self._timer = None
            return ret
        else:
            return {"RUNNING_MODAL"}

    def invoke(self, context: Context, event: Event):
        if self._timer:
            self.report({"WARNING"}, "処理中のためキャンセル")
            return {"CANCELLED"}
        self.report({"INFO"}, "処理中...")
        self._timer = context.window_manager.event_timer_add(1.0, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def add_border_strip(self, context, target_strip):
        if target_strip is None:
            self.report({"WARNING"}, "Active Stripがありません")
            return {"CANCELLED"}
        if target_strip.get("strip_type") != "placeholder":
            self.report({"WARNING"}, "Placeholderが選択されていません")
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


class_list = [
    AddBorderMainOperation,
    AddPlaceholderStripOpertaion,
]
