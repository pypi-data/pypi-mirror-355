# datathing

📊 Python-модуль для автоматического анализа, визуализации и статистических тестов над табличными данными (pandas.DataFrame).

---

## Установка

```bash
pip install datathing
```

---

## Пример использования

```python
import pandas as pd
from datathing import get_summary_report

df = pd.read_csv("sales.csv")
get_summary_report(df, "revenue")
```

---

## Возможности

* Поиск аномалий (3σ, IQR)
* Визуализация (гистограммы, boxplot, heatmap, pairplot)
* Корреляции
* Проверка нормальности
* Стат. тесты (T-test, U-test, χ²)
* Декомпозиция временных рядов

---

