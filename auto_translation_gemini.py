import os
import re
import argparse
import polib
from dotenv import load_dotenv
import google.generativeai as genai
from langcodes import Language

load_dotenv(override=True)
model_name = os.getenv("GEMINI_MODEL_NAME")
api_key = os.getenv("GEMINI_API_KEY")

# Configure the API key
genai.configure(api_key=api_key)

# Create the model
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name=model_name,
    generation_config=generation_config,
)

def translate(lang_from, lang_to, content, instruction=None):
    # convert lang_from and lang_to to language names
    lang_from = Language.get(lang_from).display_name()
    lang_to = Language.get(lang_to).display_name()

    # create message
    message = f"""You are a professional,authentic translation engine,only returns translations.\n
For example:\n
<Start>\n
Hello <Keep This Symbol>\n
World <Keep This Symbol>\n
<End>\n
The translation is:\n
<Start>\n
こんにちわ <Keep This Symbol>\n
世界 <Keep This Symbol>\n
<End>\n
\n
Translate the content to {lang_from} into {lang_to}:\n
"""

    # 指示がある場合はメッセージに追加
    if instruction:
        message += f"\nTranslation instructions:\n{instruction}\n\n"

    message += f"<Start>{content}<End>"

    # create chat session
    chat_session = model.start_chat(history=[])

    # send message
    response = chat_session.send_message(message)

    # remove start and end tags
    trans = re.sub(r"<Start>|<End>", "", response.text)

    # return translation
    return trans

def read_instruction(file_path):
    """
    指示ファイルから内容を読み込みます

    Args:
        file_path (str): 指示ファイルのパス

    Returns:
        str: 追加情報の内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"指示ファイルの読み込みエラー: {e}")
        return None

def translate_po_file(po_file_path, lang_from, lang_to, save_interval=100, instruction=None):
    """
    POファイル内の未翻訳の行を翻訳し、ファイルを更新します

    Args:
        po_file_path (str): POファイルのパス
        lang_from (str): 翻訳元の言語コード
        lang_to (str): 翻訳先の言語コード
        save_interval (int): 保存間隔（行数）
        instruction (str, optional): 翻訳に関する追加情報や指示

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
    if instruction:
        print(f"指示: {instruction}")

    # 未翻訳のエントリを翻訳
    translated_count = 0

    for entry in po.untranslated_entries():
        # 翻訳元のテキストを取得
        source_text = entry.msgid

        # 翻訳を実行
        translated_text = translate(lang_from, lang_to, source_text, instruction)

        # 翻訳結果を設定
        entry.msgstr = translated_text

        translated_count += 1
        print(f"{translated_count}/{untranslated_count}")

        # 指定間隔ごとに保存
        if translated_count % save_interval == 0:
            po.save(po_file_path)

    # 最終保存
    po.save(po_file_path)
    print(f"翻訳完了: {po_file_path} に {translated_count} 行の翻訳を保存しました")

    return translated_count

def main():
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='POファイルの未翻訳行をGemini APIで翻訳します')
    parser.add_argument('po_file', help='翻訳対象のPOファイルパス')
    parser.add_argument('--from-lang', '--from', required=True, help='翻訳元の言語コード (例: en)')
    parser.add_argument('--to-lang', '--to', required=True, help='翻訳先の言語コード (例: ja)')
    parser.add_argument('--save-interval', '-i', type=int, default=100, help='保存間隔（行数、デフォルト: 100）')
    parser.add_argument('--instruction', '-a', help='翻訳に関する追加情報や指示を含むファイルのパス')

    args = parser.parse_args()

    # 指示の取得
    instruction = None
    if args.instruction:
        instruction = read_instruction(args.instruction)

    # 翻訳を実行
    translate_po_file(args.po_file, args.from_lang, args.to_lang, args.save_interval, instruction)

if __name__ == "__main__":
    main()
