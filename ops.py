import bpy
import datetime
from bpy.types import Context, Event
from . import border_strip_utils


CUSTOM_KEY_GENERATER = "generated_by"
CUSTOM_KEY_STRIP_TYPE = "strip_type"
CUSTOM_KEY_PLACEHOLDER_ID = "placeholder_id"
ADDON_NAME = "add_border_strip"
STRIP_TYPE_PLACEHOLDER = "placeholder"
STRIP_TYPE_BORDER = "border"


def get_current_meta_strip(context):
    meta_stack = context.scene.sequence_editor.meta_stack
    if meta_stack:
        return meta_stack[-1]
    return None


def adjust_meta_duration(context, added_strip):
    meta_stack = context.scene.sequence_editor.meta_stack
    if meta_stack and meta_stack[-1].frame_final_end < added_strip.frame_final_end:
        meta_stack[-1].frame_final_end = added_strip.frame_final_end


def guess_available_channel(frame_start, frame_end, target_channel, seqs):
    unavailable_channels = set()
    for s in seqs:
        seq: bpy.types.Sequence = s
        if seq.channel in unavailable_channels:
            continue
        elif (
            seq.frame_final_end <= frame_start <= seq.frame_final_end
            or seq.frame_final_end <= frame_end <= seq.frame_final_end
        ):
            unavailable_channels.add(seq.channel)

    if target_channel not in unavailable_channels:
        return target_channel

    last_no = sorted(unavailable_channels)[-1]
    candidate = set(range(target_channel, last_no + 2))
    diff = sorted(candidate - unavailable_channels)
    # print(f"unavailable: {unavailable_channels}, candidate: {candidate}, diff: {diff}")
    # 使われていない最小のチャンネルを返す
    return diff[0]


class AddPlaceholderStripOpertaion(bpy.types.Operator):
    bl_idname = "add_border_strip.add_placeholder_strip"
    bl_label = "Add Placeholder Strip"
    bl_description = "枠線画像を挿入するための位置決め用のストリップを追加する"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.border_props
        cur_frame = bpy.context.scene.frame_current
        bpy.ops.sequencer.select_all(action="DESELECT")

        current_meta = get_current_meta_strip(context)
        if current_meta:
            seqs = current_meta.sequences
        else:
            seqs = context.scene.sequence_editor.sequences

        frame_start = cur_frame
        frame_end = cur_frame + props.placeholder_duration
        target_channel = guess_available_channel(
            frame_start, frame_end, props.placeholder_channel, seqs
        )
        print("target_channel: ", target_channel)

        placeholder_strip = seqs.new_effect(
            name=f"placeholder_{datetime.datetime.now().timestamp()}",
            type="COLOR",
            frame_start=frame_start,
            frame_end=frame_end,
            channel=target_channel,
        )
        placeholder_strip.transform.origin[0] = 0
        placeholder_strip.transform.origin[1] = 1.0
        placeholder_strip.transform.scale_x = props.placeholder_scale_x
        placeholder_strip.transform.scale_y = props.placeholder_scale_y
        screen = border_strip_utils.StripRect.fromScreen()
        placeholder_strip.transform.offset_x = (
            (1.0 - props.placeholder_scale_x) * screen.width / 2
        )
        placeholder_strip.transform.offset_y = (
            (props.placeholder_scale_y - 1.0) * screen.height / 2
        )

        placeholder_strip.color = props.placeholder_color[0:3]
        placeholder_strip.blend_alpha = props.placeholder_color[3]
        placeholder_strip[CUSTOM_KEY_GENERATER] = ADDON_NAME
        placeholder_strip[CUSTOM_KEY_STRIP_TYPE] = STRIP_TYPE_PLACEHOLDER
        placeholder_strip[CUSTOM_KEY_PLACEHOLDER_ID] = placeholder_strip.name

        # current_meta = get_current_meta_strip(context)
        # if current_meta:
        #     adjust_meta_duration(context, placeholder_strip)
        #     context.scene.sequence_editor.display_stack(current_meta)

        context.scene.sequence_editor.active_strip = placeholder_strip

        return {"FINISHED"}


class AddBorderReplaceCurrentPlaceholderOperation(bpy.types.Operator):
    bl_idname = "add_border_strip.replace_current_placeholder"
    bl_label = "Rplace Current Placeholder to Border Image"
    bl_description = "現在選択しているプレイスホルダーを枠線画像に置換する"
    bl_options = {"REGISTER", "UNDO"}

    _timer = None

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"

    def modal(self, context: Context, event: Event):
        if event.type == "TIMER":
            context.window_manager.event_timer_remove(self._timer)
            target_strip = context.scene.sequence_editor.active_strip
            bpy.ops.sequencer.select_all(action="DESELECT")
            ret = add_border_strip(self, context, target_strip)
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


def add_border_strip(op, context, target_strip):
    if target_strip is None:
        op.report({"WARNING"}, "置換対象のStripがありません")
        return {"CANCELLED"}
    if not is_placeholder(target_strip):
        op.report({"WARNING"}, "Placeholderが選択されていません")
        return {"CANCELLED"}
    props = context.scene.border_props
    abs_image_dir = border_strip_utils.normalize_image_dir(props.image_dir)
    # print(f"abs_image_dir: {abs_image_dir}")
    if abs_image_dir is None:
        op.report(
            type={"WARNING"},
            message="画像出力先ディレクトリに相対パスが指定されました。.blendファイルを保存してから実行してください",
        )
        return {"CANCELLED"}
    # オペレーターのプロパティーで、imageストリップのdurationを調整可能に
    img_strip = border_strip_utils.create_border_strip(
        target_strip,
        abs_image_dir,
        props.shape_type,
        props.border_size,
        props.border_color,
    )
    img_strip[CUSTOM_KEY_GENERATER] = ADDON_NAME
    img_strip[CUSTOM_KEY_STRIP_TYPE] = STRIP_TYPE_BORDER
    ph_id = target_strip.get(CUSTOM_KEY_PLACEHOLDER_ID)
    org_channel = target_strip.channel

    current_meta = get_current_meta_strip(context)
    if current_meta:
        img_strip.move_to_meta(current_meta)
        current_meta.sequences.remove(target_strip)
    else:
        bpy.context.scene.sequence_editor.sequences.remove(target_strip)

    img_strip.channel = org_channel
    bpy.context.scene.sequence_editor.active_strip = img_strip

    op.report({"INFO"}, f"Placeholder({ph_id})を置換しました。")
    return {"FINISHED"}


def get_all_placeholder_strips(context: Context):
    seqs = context.scene.sequence_editor.sequences
    current_meta = get_current_meta_strip(context)
    if current_meta:
        seqs = current_meta.sequences

    targets = []
    for strip in seqs:
        if is_placeholder(strip):
            targets.append(strip)
    return targets


def is_placeholder(strip):
    if (
        strip.get(CUSTOM_KEY_GENERATER) == ADDON_NAME
        and strip.get(CUSTOM_KEY_STRIP_TYPE) == STRIP_TYPE_PLACEHOLDER
    ):
        return True
    return False


class AddBorderReplaceAllPlaceholdersOperation(bpy.types.Operator):
    bl_idname = "add_border_strip.replace_all_placeholders"
    bl_label = "Rplace All Placeholders to Border Images"
    bl_description = "統べてのプレイスホルダーを枠線画像に置換する"
    bl_options = {"REGISTER", "UNDO"}

    _timer = None

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"

    def modal(self, context: Context, event: Event):
        if event.type == "TIMER":
            context.window_manager.event_timer_remove(self._timer)
            target_list = get_all_placeholder_strips(context)
            if len(target_list) == 0:
                self.report({"WARNING"}, "処理対象のPlaceholderがありません")
                return {"CANCELLED"}
            bpy.ops.sequencer.select_all(action="DESELECT")
            for target_strip in target_list:
                add_border_strip(self, context, target_strip)
            self._timer = None
            return {"FINISHED"}
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


class_list = [
    AddPlaceholderStripOpertaion,
    AddBorderReplaceCurrentPlaceholderOperation,
    AddBorderReplaceAllPlaceholdersOperation,
]
