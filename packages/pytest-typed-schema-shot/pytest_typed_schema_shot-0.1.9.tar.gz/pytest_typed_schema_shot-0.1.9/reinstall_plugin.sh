#!/bin/bash

# Скрипт для переустановки pytest-typed-schema-shot плагина
# Используется для отладки обновлений

set -e  # Прерывать выполнение при ошибках

echo "🔄 Начинаю переустановку pytest-typed-schema-shot плагина..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 Удаляю старую версию плагина...${NC}"
pip uninstall pytest-typed-schema-shot -y 2>/dev/null || echo -e "${YELLOW}⚠️  Плагин не был установлен ранее${NC}"

echo -e "${BLUE}🧹 Очищаю кэш pip...${NC}"
pip cache purge

echo -e "${BLUE}🧹 Удаляю кэш Python...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo -e "${BLUE}🔨 Очищаю директорию build...${NC}"
rm -rf build/ dist/ *.egg-info/ 2>/dev/null || true

echo -e "${BLUE}🔨 Пересобираю пакет...${NC}"
python3 -m build

echo -e "${BLUE}📦 Устанавливаю плагин в режиме разработки...${NC}"
pip install -e .

echo -e "${BLUE}🔍 Проверяю установку плагина...${NC}"
if pip list | grep -q pytest-typed-schema-shot; then
    echo -e "${GREEN}✅ Плагин успешно установлен!${NC}"
    pip show pytest-typed-schema-shot
else
    echo -e "${RED}❌ Ошибка: плагин не найден после установки${NC}"
    exit 1
fi

echo -e "${BLUE}🧪 Проверяю, что pytest видит плагин...${NC}"
if pytest --help | grep -q "schemashot"; then
    echo -e "${GREEN}✅ Pytest успешно обнаружил плагин!${NC}"
else
    echo -e "${YELLOW}⚠️  Предупреждение: pytest не обнаружил опции плагина${NC}"
fi

#echo -e "${BLUE}🏃 Запускаю базовые тесты...${NC}"
#pytest tests/ -v

echo -e "${GREEN}🎉 Переустановка завершена успешно!${NC}"
echo -e "${BLUE}💡 Теперь вы можете тестировать обновления плагина${NC}"
