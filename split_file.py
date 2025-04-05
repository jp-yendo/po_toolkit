import os
import argparse
import polib

def split_po_file(input_file, items_per_file=300):
    # 入力ファイルのパスとファイル名を分析
    input_dir = os.path.dirname(input_file)
    input_basename = os.path.basename(input_file)
    filename_without_ext = os.path.splitext(input_basename)[0]

    # polibを使用してPOファイルを読み込む
    po = polib.pofile(input_file)

    # エントリの総数を取得
    total_entries = len(po)
    print(f"Total entries: {total_entries}")

    # 指定された数ごとにファイルを作成
    for i in range(0, total_entries, items_per_file):
        part_num = i // items_per_file + 1
        # 元のファイルパスを維持しながら連番を付与
        output_file = os.path.join(input_dir, f'{filename_without_ext}.{part_num}.po')

        # 新しいPOオブジェクトを作成
        new_po = polib.POFile()

        # メタデータをコピー
        new_po.metadata = po.metadata.copy()

        # エントリをコピー
        for entry in po[i:i + items_per_file]:
            new_po.append(entry)

        # ファイルに保存
        new_po.save(output_file)

        print(f'Created {output_file} with {len(new_po)} entries')

# コマンドライン引数の設定
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='POファイルを指定した項目数ごとに分割します')
    parser.add_argument('input_file', help='分割するPOファイルのパス')
    parser.add_argument('--items', type=int, default=100, help='各ファイルに含める項目数（デフォルト: 100')

    args = parser.parse_args()

    # 入力ファイルが存在するか確認
    if not os.path.exists(args.input_file):
        print(f"エラー: ファイル '{args.input_file}' が見つかりません。")
        exit(1)

    # ファイルを分割
    split_po_file(args.input_file, args.items)
