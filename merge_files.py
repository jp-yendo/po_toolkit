import os
import glob
import argparse
import polib

def merge_po_files(input_file):
    # 入力ファイルのパスとパターンを作成
    input_dir = os.path.dirname(input_file)
    input_basename = os.path.splitext(os.path.basename(input_file))[0]
    pattern = os.path.join(input_dir, f'{input_basename}.*.po')

    # 全ての分割ファイルを取得
    part_files = sorted(glob.glob(pattern),
                       key=lambda x: int(x.split('.')[-2]))  # 数字部分でソート

    if not part_files:
        print(f"No part files found matching pattern: {pattern}")
        return

    # 新しいPOオブジェクトを作成
    merged_po = polib.POFile()

    # 最初のファイルからメタデータを取得
    first_po = polib.pofile(part_files[0])
    merged_po.metadata = first_po.metadata.copy()

    # 各パートファイルのエントリを結合
    total_entries = 0
    for part_file in part_files:
        po = polib.pofile(part_file)
        for entry in po:
            merged_po.append(entry)
        total_entries += len(po)
        print(f"Added {len(po)} entries from {part_file}")

    # 出力ファイル名（元のファイル名を使用）
    output_file = input_file

    # ファイルに保存
    merged_po.save(output_file)

    print(f'Created merged file: {output_file} with {total_entries} total entries')

# コマンドライン引数の設定
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='分割されたPOファイルを結合します')
    parser.add_argument('input_file', help='結合するPOファイルのベース名（例: ja_JP/cheatengine-x86_64.po）')

    args = parser.parse_args()

    # 入力ファイルのディレクトリが存在するか確認
    input_dir = os.path.dirname(args.input_file)
    if input_dir and not os.path.exists(input_dir):
        print(f"エラー: ディレクトリ '{input_dir}' が見つかりません。")
        exit(1)

    # ファイルを結合
    merge_po_files(args.input_file)
