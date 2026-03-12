#!/bin/bash

# Имя выходного файла
OUTPUT="project_code.txt"

# Очищаем или создаем файл
> "$OUTPUT"

echo "🚀 Собираю файлы (.py, .html, .css)..."
echo "📂 Игнорирую: .git, .venv, venv, __pycache__"

# Поиск файлов с исключением ненужных директорий
find . -type d \( -name ".git" -o -name ".venv" -o -name "venv" -o -name "__pycache__" \) -prune -o \
     -type f \( -name "*.py" -o -name "*.html" -o -name "*.css" \) -print | while read -r file; do
    
    # Пропускаем сам файл вывода, если он попал в поиск
    if [[ "$file" == "./$OUTPUT" ]]; then continue; fi

    # Записываем заголовок в нужном формате
    echo -e "\n---- $file ----" >> "$OUTPUT"
    
    # Добавляем содержимое файла
    cat "$file" >> "$OUTPUT"
    
    # Добавляем пустую строку для разделения между файлами
    echo "" >> "$OUTPUT"
    
    echo "Добавлен: $file"
done

echo "--------------------------------------"
echo "✅ Готово! Результат в файле: $OUTPUT"
echo "📊 Всего строк кода собрано: $(wc -l < "$OUTPUT")"