'''
df = df[df['price'].notnull()]

df['date'] = pd.to_datetime(df['date']) # Преобразую данные
df['parse_date'] = pd.to_datetime(df['parse_date'])

print("Размер датасета после очистки:", df.shape)

numerical_features = ['year', 'mileage', 'power', 'price'] # Базовые числовые признаки

# Посмотрим распределения признаков
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(12, 8))
for i, col in enumerate(numerical_features, 1):
    plt.subplot(2, 2, i)
    sns.histplot(df[col], kde=True, bins=30)
    plt.title(col)
plt.tight_layout()
plt.show()
'''