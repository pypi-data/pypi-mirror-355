import g4f
import re
import argparse
import sys
import os
import shutil
import socket

def check_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def get_response_with_retries(prompt, model="gpt-4", max_attempts=3):
    attempts = max_attempts
    while attempts > 0:
        response = g4f.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        if "Status: 403" not in response:
            return response
        attempts -= 1
    raise RuntimeError("Failed to get valid response after multiple attempts due to Status 403.")

def split_response_parts(text):
    pattern = re.compile(r"(.*?)```python\s+(.*?)```(.*)", re.DOTALL | re.IGNORECASE)
    match = pattern.match(text)
    if match:
        top_text = match.group(1).strip()
        code = match.group(2).strip()
        bottom_text = match.group(3).strip()
        return top_text, code, bottom_text
    else:
        return "", "", ""

def escape_docstring(text):
    """
    Экранирует тройные кавычки в тексте, чтобы можно вставить в многострочный строковый литерал
    """
    return text.replace('"""', '\\"\\"\\"')

def main():
    parser = argparse.ArgumentParser(description="pycaf — Python Code Assistant Free")
    parser.add_argument("filename", type=str, help="Имя файла для записи/редактирования кода")
    parser.add_argument("--command", type=str, required=True, help="Запрос к GPT-4, описание программы или изменение")
    parser.add_argument("--createnewversion", action="store_true",
                        help="Записать новую версию кода в файл с суффиксом _new_version (исходный не трогать)")
    parser.add_argument("--createminiinstruction", action="store_true",
                        help="Вставлять в файл дополнительно полный ответ как документирующий комментарий")
    args = parser.parse_args()

    if not check_internet():
        print("ERROR: Проверьте подключение к интернету и повторите попытку.")
        sys.exit(1)

    file_exists = os.path.isfile(args.filename)
    filename = args.filename

    code_to_edit = None
    if file_exists:
        with open(filename, "r", encoding="utf-8") as f:
            code_to_edit = f.read().strip()

    # Формируем запрос
    if not file_exists or code_to_edit is None:
        question = f"Напиши приложение на python: {args.command}"
    else:
        question = f"{code_to_edit}\n\n— внеси в этот код изменения по следующему запросу: {args.command}"

    print(f"INFO: Запрос принят. Ваш запрос: {args.command}.")

    try:
        response = get_response_with_retries(question)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("INFO: Генерация кода окончена")

    if args.createminiinstruction:
        top_text, code, bottom_text = split_response_parts(response)
        if not code:
            print("INFO: Не удалось сгенерировать код по вашему запросу")
            sys.exit(0)
        top_comment = f'"""\n{escape_docstring(top_text)}\n"""\n\n' if top_text else ""
        bottom_comment = f'\n\n"""\n{escape_docstring(bottom_text)}\n"""' if bottom_text else ""
        text_to_write = f"{top_comment}{code}{bottom_comment}"
    else:
        pattern = re.compile(r"```python\s+(.*?)```", re.DOTALL | re.IGNORECASE)
        matches = pattern.findall(response)
        if matches:
            text_to_write = "\n\n".join(match.strip() for match in matches)
        else:
            print("INFO: Не удалось сгенерировать код по вашему запросу")
            sys.exit(0)

    if args.createnewversion:
        base, ext = os.path.splitext(filename)
        new_filename = f"{base}_new_version{ext}"
        write_to = new_filename
    else:
        write_to = filename

    with open(write_to, "w", encoding="utf-8") as f:
        f.write(text_to_write)

    print(f"INFO: Код записан в файл {write_to}")

if __name__ == "__main__":
    main()