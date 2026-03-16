import os

def collect_files(output_filename="result_code.txt"):
    target_extensions = ('.py', '.html', '.css')
    exclude_dirs = {'venv', '.git', '__pycache__'}

    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk('.'):
            # Исключаем ненужные папки
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith(target_extensions):
                    file_path = os.path.join(root, file)
                    
                    # Формируем аккуратный заголовок
                    outfile.write(f"\n{'='*50}\n")
                    outfile.write(f"FILE: {file_path}\n")
                    outfile.write(f"{'='*50}\n\n")

                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"[Ошибка при чтении файла {file_path}: {e}]\n")
                    
                    outfile.write("\n")

    print(f"Готово! Весь код собран в: {output_filename}")

if __name__ == "__main__":
    collect_files()