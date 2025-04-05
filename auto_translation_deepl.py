import os
import re
import argparse
import polib
from dotenv import load_dotenv
import deepl
from langcodes import Language

load_dotenv(override=True)
api_key = os.getenv("DEEPL_API_KEY")

# DeepLクライアントの初期化
translator = deepl.Translator(api_key)

def protect_placeholders(text):
    """
    テキスト内の埋め込み文字列（%s、%dなど）を一時的に置換して保護します

    Args:
        text (str): 保護するテキスト

    Returns:
        tuple: (保護されたテキスト, 置換マッピング)
    """
    # 置換マッピングを保存する辞書
    placeholders = {}

    # 埋め込み文字列のパターン（%s、%d、%f、%r、%c、%i、%u、%o、%x、%X、%e、%E、%g、%G、%%）
    pattern = r'%[sdifrceiouoxXeEgG%]'

    # 置換カウンター
    counter = 0

    # 置換関数
    def replace_placeholder(match):
        nonlocal counter
        placeholder = match.group(0)
        replacement = f"__PLACEHOLDER_{counter}__"
        placeholders[replacement] = placeholder
        counter += 1
        return replacement

    # テキスト内の埋め込み文字列を置換
    protected_text = re.sub(pattern, replace_placeholder, text)

    return protected_text, placeholders

def restore_placeholders(text, placeholders):
    """
    保護されたテキスト内のプレースホルダーを元の埋め込み文字列に戻します

    Args:
        text (str): 保護されたテキスト
        placeholders (dict): 置換マッピング

    Returns:
        str: 元の埋め込み文字列が復元されたテキスト
    """
    restored_text = text

    # プレースホルダーを元の埋め込み文字列に戻す
    for replacement, placeholder in placeholders.items():
        restored_text = restored_text.replace(replacement, placeholder)

    return restored_text

def translate(lang_from, lang_to, content):
    """
    DeepL APIを使用してテキストを翻訳します

    Args:
        lang_from (str): 翻訳元の言語コード
        lang_to (str): 翻訳先の言語コード
        content (str): 翻訳するテキスト

    Returns:
        str: 翻訳されたテキスト
    """
    # 埋め込み文字列を保護
    protected_content, placeholders = protect_placeholders(content)

    # DeepLの言語コードに変換
    # DeepLは一部の言語コードが異なるため、変換が必要
    deepl_lang_from = convert_to_deepl_lang_code(lang_from)
    deepl_lang_to = convert_to_deepl_lang_code(lang_to)

    # 翻訳を実行
    result = translator.translate_text(protected_content, source_lang=deepl_lang_from, target_lang=deepl_lang_to)

    # 翻訳結果から埋め込み文字列を復元
    translated_text = restore_placeholders(result.text, placeholders)

    # 翻訳結果を返す
    return translated_text

def convert_to_deepl_lang_code(lang_code):
    """
    標準的な言語コードをDeepLの言語コードに変換します

    Args:
        lang_code (str): 標準的な言語コード

    Returns:
        str: DeepLの言語コード
    """
    # DeepLの言語コードマッピング
    deepl_lang_map = {
        "en": "EN",
        "ja": "JA",
        "zh": "ZH",
        "ko": "KO",
        "fr": "FR",
        "de": "DE",
        "es": "ES",
        "it": "IT",
        "nl": "NL",
        "pl": "PL",
        "pt": "PT",
        "ru": "RU",
        "bg": "BG",
        "cs": "CS",
        "da": "DA",
        "el": "EL",
        "et": "ET",
        "fi": "FI",
        "hu": "HU",
        "id": "ID",
        "lt": "LT",
        "lv": "LV",
        "ro": "RO",
        "sk": "SK",
        "sl": "SL",
        "sv": "SV",
        "tr": "TR",
        "uk": "UK"
    }

    # 言語コードを小文字に変換
    lang_code = lang_code.lower()

    # マッピングに存在する場合は変換、存在しない場合は元のコードを大文字に変換
    return deepl_lang_map.get(lang_code, lang_code.upper())

def translate_po_file(po_file_path, lang_from, lang_to, save_interval=100):
    """
    POファイル内の未翻訳の行を翻訳し、ファイルを更新します

    Args:
        po_file_path (str): POファイルのパス
        lang_from (str): 翻訳元の言語コード
        lang_to (str): 翻訳先の言語コード
        save_interval (int): 保存間隔（行数）

    Returns:
        int: 翻訳された行数
    """
    # POファイルを読み込む
    po = polib.pofile(po_file_path)

    # 翻訳が必要なエントリをカウント
    untranslated_count = 0
    for entry in po.untranslated_entries():
        untranslated_count += 1

    if untranslated_count == 0:
        print(f"翻訳が必要な行はありません: {po_file_path}")
        return 0

    print(f"翻訳が必要な行: {untranslated_count}行")
    print(f"保存間隔: {save_interval}行")

    # 未翻訳のエントリを翻訳
    translated_count = 0

    for entry in po.untranslated_entries():
        # 翻訳元のテキストを取得
        source_text = entry.msgid

        # 翻訳を実行
        translated_text = translate(lang_from, lang_to, source_text)

        # 翻訳結果を設定
        entry.msgstr = translated_text
        entry.comment = f"Translated by DeepL API from {lang_from} to {lang_to}"
        entry.flags.append("fuzzy")

        translated_count += 1
        print(f"翻訳完了: {translated_count}/{untranslated_count}")

        # 指定間隔ごとに保存
        if translated_count % save_interval == 0:
            po.save(po_file_path)
            print(f"中間保存: {translated_count}行の翻訳を保存しました")

    # 最終保存
    po.save(po_file_path)
    print(f"翻訳完了: {po_file_path} に {translated_count} 行の翻訳を保存しました")

    return translated_count

def main():
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='POファイルの未翻訳行をDeepL APIで翻訳します')
    parser.add_argument('po_file', help='翻訳対象のPOファイルパス')
    parser.add_argument('--from-lang', '--from', required=True, help='翻訳元の言語コード (例: en)')
    parser.add_argument('--to-lang', '--to', required=True, help='翻訳先の言語コード (例: ja)')
    parser.add_argument('--save-interval', '-i', type=int, default=100, help='保存間隔（行数、デフォルト: 100）')

    args = parser.parse_args()

    # 翻訳を実行
    translate_po_file(args.po_file, args.from_lang, args.to_lang, args.save_interval)

if __name__ == "__main__":
    main()
