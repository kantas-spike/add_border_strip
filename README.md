# add_border_strip

BlenderのVSE内で、配置されたプレイスホルダーを枠線画像に置き換えるためのアドオンです。

OSはmacOS、Blenderはv4.0でのみ動作確認しています。

## インストール方法

1. Blenderのアドオンディレクトリにプロジェクトをクローンする。

   - macOSの場合

   ```shell
   cd ~/Library/Application Support/Blender/<blender_version>/scripts/addons
   git clone https://github.com/kantas-spike/add_border_strip.git
   ```

2. Blenderを起動し、`Preferences`-`Add-ons`から`Sequencer: Add Border`をチェックして有効にします。

## 使い方

`Add Border`は、Blenderの`Video Editing`用のアドオンです。

主な操作手順は以下になります。

1. プレイスホルダー(カラーストリップ)を追加する
2. プレイスホルダーの位置サイズを調整する
3. プレイスホルダーを枠線(イメージストリップ)に変換する

詳細な手順は、以下を確認してください。

![](./doc/usage.gif)
