
def train_test_split(number):
        if number == 0:
            return'''
            1 - activites.csv - rnn,lstm, gru модель, бинарная на Review-Activity, 
            Ранняя остановка + графики loss, accuracy, f1.
            2 - activites.csv - TF_IDF, многоклассовая на Season.
            3 - corona.csv - rnn,lstm, модель, мультикласс, 
            Ранняя остановка + графики loss, accuracy, f1. инициализация ксавье
            4 - news.csv -rnn,lstm, модель, мультикласс, Ранняя остановка + графики loss, accuracy, f1. инициализация ксавье
            5 - pos.json - pos-теккинг через conv1d
            6 - quotes.json - генерация 
            7 - reviews.json - генерация
            8 - tweet_cat.csv - nn,lstm, модель, мультикласс, Ранняя остановка + графики loss, accuracy, f1. инициализация ксавье
            9 - tweets_disaster - ДОДЕЛАТЬ!!!
            10 - джакарт с conv слоями
            
            11 - кастомный RNN
            12 - реализация word2vec с помощью nn.Embedding
            13 - кастомный attention
            14 - кастомный BatchNorm
            
            20 - однонаправленная архитектура для всех классификаций'''
        elif number == 1:
            return '''
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
import matplotlib.pyplot as plt

# Загрузка данных
df = pd.read_csv('activities.csv')
# БИНАРНАЯ КЛАССИФИКАЦИЯ
df['is_activity'] = df['Review-Activity'].apply(lambda x: 1 if x == 'ACTIVITY' else 0)

#  МНОГОКЛАССОВАЯ КЛАССИФИКАЦИЯ (Только для ACTIVITIES)
# Целевая переменная: сезон, в котором происходит активность
# Классы: SUMMER (0), FALL (1), WINTER (2), SPRING (3), NOT APPLICABLE (4)
# season_df = df[df['Review-Activity'] == 'ACTIVITY'].copy()
# season_mapping = {'SUMMER': 0, 'FALL': 1, 'WINTER': 2, 'SPRING': 3, 'NOT APPLICABLE': 4}
# season_df['season_label'] = season_df['Season'].map(season_mapping)
# train_season_texts, test_season_texts, train_season, test_season = train_test_split(
#     season_df['Text'], season_df['season_label'], test_size=0.2, random_state=42)

# Создание словаря
word2idx = {}
idx = 1
max_len = 100
vocab_size = 5000
for text in df['Text']:
    for word in text.split():
        if word not in word2idx and len(word2idx) < vocab_size:
            word2idx[word] = idx
            idx += 1

def text_to_seq(text):
    return [word2idx.get(word, 0) for word in text.split()][:max_len]

# Разделение на train/test
train_texts, test_texts, train_binary, test_binary = train_test_split(
    df['Text'], df['is_activity'], test_size=0.2, random_state=42)

# Преобразование текстов в индексы + паддинг
def pad_sequences(sequences, max_len):
    padded = torch.zeros(len(sequences), max_len, dtype=torch.long)
    for i, seq in enumerate(sequences):
        padded[i, :len(seq)] = torch.tensor(seq)
    return padded

X_train_seq = [text_to_seq(text) for text in train_texts]
X_test_seq = [text_to_seq(text) for text in test_texts]

X_train_padded = pad_sequences(X_train_seq, max_len)
X_test_padded = pad_sequences(X_test_seq, max_len)
y_train_tensor = torch.tensor(train_binary.values).unsqueeze(1).float()
y_test_tensor = torch.tensor(test_binary.values).unsqueeze(1).float()

# Модель
class RNNClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, n_layers=1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.rnn = nn.RNN(embed_dim, hidden_dim, n_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        embedded = self.dropout(self.embedding(x))
        output, hidden = self.rnn(embedded)
        return self.fc(hidden.squeeze(0))  # логиты

class LSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, n_layers=1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, n_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        embedded = self.dropout(self.embedding(x))
        output, (hidden, cell) = self.lstm(embedded)
        # hidden shape: (num_layers, batch_size, hidden_dim)
        return self.fc(hidden[-1])  # берем скрытое состояние последнего слоя

class GRUClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, n_layers=1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.gru = nn.GRU(embed_dim, hidden_dim, n_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        embedded = self.dropout(self.embedding(x))
        output, hidden = self.gru(embedded)
        # hidden shape: (num_layers, batch_size, hidden_dim)
        return self.fc(hidden[-1])  # берем скрытое состояние последнего слоя

# Гиперпараметры
vocab_size = len(word2idx) + 1
embed_dim = 100
hidden_dim = 64
output_dim = 1
#model = RNNClassifier(vocab_size, embed_dim, hidden_dim, output_dim)
#model = LSTMClassifier(vocab_size, embed_dim, hidden_dim, output_dim)
model = GRUClassifier(vocab_size, embed_dim, hidden_dim, output_dim)

criterion = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(model.parameters())

patience = 2  # сколько эпох ждать улучшения
best_loss = float('inf')
counter = 0
# Обучение
epochs = 30
train_losses, test_losses = [], []
train_accuracies, test_accuracies = [], []
train_f1s, test_f1s = [], []

for epoch in tqdm(range(epochs)):
    model.train()
    optimizer.zero_grad()
    output = model(X_train_padded)
    loss = criterion(output, y_train_tensor)
    loss.backward()
    optimizer.step()
    train_losses.append(loss.item())

    # Метрики на train
    with torch.no_grad():
        probs = torch.sigmoid(output)
        preds = (probs > 0.5).long()
        acc = accuracy_score(y_train_tensor.cpu(), preds.cpu())
        f1 = f1_score(y_train_tensor.cpu(), preds.cpu())
        train_accuracies.append(acc)
        train_f1s.append(f1)

    # Метрики на test
    model.eval()
    with torch.no_grad():
        test_output = model(X_test_padded)
        test_loss = criterion(test_output, y_test_tensor)
        test_losses.append(test_loss.item())

        test_probs = torch.sigmoid(test_output)
        test_preds = (test_probs > 0.5).long()
        test_acc = accuracy_score(y_test_tensor.cpu(), test_preds.cpu())
        test_f1 = f1_score(y_test_tensor.cpu(), test_preds.cpu())
        test_accuracies.append(test_acc)
        test_f1s.append(test_f1)

    print(f'Epoch {epoch+1} | Train Loss: {loss.item():.4f}, Acc: {acc:.4f}, F1: {f1:.4f} | '
          f'Test Loss: {test_loss.item():.4f}, Acc: {test_acc:.4f}, F1: {test_f1:.4f}')

    # Ранняя остановка
    if test_loss < best_loss:
        best_loss = test_loss
        counter = 0
        # Можно сохранить лучшую модель, если хочешь:
        # torch.save(model.state_dict(), 'best_model.pth')
    else:
        counter += 1
        if counter >= patience:
            print(f'Early stopping at epoch {epoch+1}')
            break

# Визуализация, если ранняя остановка, то epochs надо поменять
epochs_range = range(1, epochs + 1)

plt.figure(figsize=(18, 5))

plt.subplot(1, 3, 1)
plt.plot(epochs_range, train_losses, label='Train Loss')
plt.plot(epochs_range, test_losses, label='Test Loss')
plt.title('Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

plt.subplot(1, 3, 2)
plt.plot(epochs_range, train_accuracies, label='Train Accuracy')
plt.plot(epochs_range, test_accuracies, label='Test Accuracy')
plt.title('Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()

plt.subplot(1, 3, 3)
plt.plot(epochs_range, train_f1s, label='Train F1')
plt.plot(epochs_range, test_f1s, label='Test F1')
plt.title('F1 Score')
plt.xlabel('Epoch')
plt.ylabel('F1 Score')
plt.legend()

plt.tight_layout()
plt.show()
# Предсказание на одном примере
def predict(text, model, word_to_idx, max_len=50):
    seq = [word_to_idx.get(word, 0) for word in text.split()[:max_len]]
    seq += [0] * (max_len - len(seq))
    x = torch.LongTensor([seq])

    model.eval()
    with torch.no_grad():
        output = model(x).squeeze()
        prob = torch.sigmoid(output).item()
        return "Activity" if prob > 0.5 else "Review"

# Пример
print(predict("beach vacation", model, word2idx))'''
        elif number == 2:
             return '''
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('wordnet')

def text_preprocessing(text):
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return ' '.join(tokens)

# Предобработка текста
df = pd.read_csv('activities.csv')
df['cleaned_Text'] = df['Text'].apply(text_preprocessing)
season_df = df[df['Review-Activity'] == 'ACTIVITY'].copy()

season_mapping = {'SUMMER': 0, 'FALL': 1, 'WINTER': 2}
season_df = season_df[season_df['Season'].isin(season_mapping)].copy()
season_df['season_label'] = season_df['Season'].map(season_mapping)

X_train, X_test, y_train, y_test = train_test_split(
    season_df['cleaned_Text'], season_df['season_label'], test_size=0.2, random_state=42
)

vectorizer = TfidfVectorizer(max_features=5000)
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# Logistic Regression
lr_model = LogisticRegression(max_iter=1000)
lr_model.fit(X_train_tfidf, y_train)
y_test_pred_lr = lr_model.predict(X_test_tfidf)

# Random Forest
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train_tfidf, y_train)
y_test_pred_rf = rf_model.predict(X_test_tfidf)

# Функция для вывода метрик и cm
def print_metrics_and_cm(y_true, y_pred, model_name, labels):
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average='macro')
    cm = confusion_matrix(y_true, y_pred)
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)

    print(f"=== {model_name} ===")
    print(f"Accuracy: {acc:.4f} | Macro F1: {f1:.4f}")
    print("Confusion Matrix:")
    print(cm_df)
    print("\n")

labels = ['SUMMER', 'FALL', 'WINTER']

print_metrics_and_cm(y_test, y_test_pred_lr, "Logistic Regression", labels)
print_metrics_and_cm(y_test, y_test_pred_rf, "Random Forest", labels)

# Примеры предсказаний для Random Forest (можно для любой модели)
print("Примеры предсказаний (Random Forest):\n")
inverse_map = {v: k for k, v in season_mapping.items()}
test_texts = X_test.reset_index(drop=True)

for i in range(5):
    print(f"Текст: {test_texts[i][:100]}...")
    print(f"Реальный класс: {inverse_map[y_test.values[i]]}")
    print(f"Предсказано:    {inverse_map[y_test_pred_rf[i]]}")
    print("-" * 60)'''
        elif number == 3:
             return '''
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from torch.nn.utils.rnn import pad_sequence
from collections import Counter
import re
import torch.optim as optim
from sklearn.metrics import accuracy_score, f1_score
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt
from tqdm import tqdm
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('wordnet')

def text_preprocessing(text):
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return ' '.join(tokens)

# Загрузка данных
df = pd.read_csv('/content/corona.csv')
df.loc[:, 'cleaned_OriginalTweet'] = df['OriginalTweet'].apply(text_preprocessing)
print(df['Sentiment'].value_counts())

# Создание словаря
word_counts = Counter()
for text in df['cleaned_OriginalTweet']:
    word_counts.update(text.split())
vocab = {word: i+2 for i, word in enumerate(word for word, count in word_counts.most_common(10000))}
vocab_size = len(vocab) + 2

# Преобразование текста в индексы
def text_to_seq(text):
    return [vocab.get(word, 1) for word in text.split()]

X = [torch.tensor(text_to_seq(text)) for text in df['cleaned_OriginalTweet']]
X_padded = pad_sequence(X, batch_first=True, padding_value=0)

# Метки
sentiment_map = {
    'Extremely Negative': 0,
    'Negative': 1,
    'Neutral': 2,
    'Positive': 3,
    'Extremely Positive': 4
}
y = torch.tensor(df['Sentiment'].map(sentiment_map).values)

# Гиперпараметры
vocab_size = max(vocab.values()) + 1
embedding_dim = 256
hidden_dim = 128
num_classes = len(sentiment_map)
maxlen = max([len(seq) for seq in X])  # максимальная длина последовательности

# padding
X_padded = pad_sequence(X, batch_first=True, padding_value=0)
X_padded = X_padded[:, :maxlen]  # ограничим длину при необходимости

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X_padded, y, test_size=0.2, random_state=10)
train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=64, shuffle=True)
val_loader = DataLoader(TensorDataset(X_test, y_test), batch_size=64)

class LSTM_mult(nn.Module):
    def __init__(self, vocab_size, embedding_dim, out_features):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.rnn = nn.LSTM(embedding_dim, 128, batch_first=True, bidirectional=True, num_layers=2, dropout=0.5)
        self.out = nn.Linear(128 * 2, out_features)
        self._init_weights()

    def _init_weights(self):
        # Xavier for embedding
        nn.init.xavier_uniform_(self.embedding.weight)

    def forward(self, x):
        x = self.embedding(x)
        x, (h_n, _) = self.rnn(x)
        hh = torch.cat((h_n[-2], h_n[-1]), dim=1)
        return self.out(hh)

class RNN_mult(nn.Module):
    def __init__(self, vocab_size, embedding_dim, out_features):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.rnn = nn.RNN(
            input_size=embedding_dim,
            hidden_size=128,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.5
        )
        self.batch_norm = nn.BatchNorm1d(128 * 2)
        self.out = nn.Linear(128 * 2, out_features)

        self._init_weights()

    def _init_weights(self):
        # Xavier for embedding
        nn.init.xavier_uniform_(self.embedding.weight)

        # Xavier for RNN weights
        for name, param in self.rnn.named_parameters():
            if 'weight' in name:
                nn.init.xavier_uniform_(param)
            elif 'bias' in name:
                nn.init.constant_(param, 0)

        # Xavier for linear layer
        nn.init.xavier_uniform_(self.out.weight)
        nn.init.constant_(self.out.bias, 0)

    def forward(self, x):
        x = self.embedding(x)                         # (batch, seq_len, embedding_dim)
        x, h_n = self.rnn(x)                          # h_n: (num_layers * 2, batch, hidden)
        h_cat = torch.cat((h_n[-2], h_n[-1]), dim=1)  # (batch, hidden_size * 2)
        h_cat = self.batch_norm(h_cat)                # batch norm over features
        return self.out(h_cat)

# Инициализация
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
num_classes = 5
model = LSTM_mult(vocab_size, embedding_dim, num_classes).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Early stopping
best_val_loss = float('inf')
patience = 5
patience_counter = 0

train_losses = []
val_losses = []
val_accuracies = []
val_f1s = []

for epoch in tqdm(range(20)):
    model.train()
    total_loss = 0
    for batch_X, batch_y in train_loader:
        batch_X, batch_y = batch_X.to(device), batch_y.to(device)
        optimizer.zero_grad()
        output = model(batch_X)
        loss = criterion(output, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    # Валидация
    model.eval()
    val_loss = 0
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for batch_X, batch_y in val_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            output = model(batch_X)
            loss = criterion(output, batch_y)
            val_loss += loss.item()
            preds = torch.argmax(output, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(batch_y.cpu().numpy())

    avg_train_loss = total_loss / len(train_loader)
    avg_val_loss = val_loss / len(val_loader)
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average='macro')

    # логируем
    train_losses.append(avg_train_loss)
    val_losses.append(avg_val_loss)
    val_accuracies.append(acc)
    val_f1s.append(f1)

    print(f"Epoch {epoch+1}, Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}, Val Accuracy: {acc:.4f}, F1: {f1:.4f}")

    if avg_val_loss < best_val_loss:
        best_val_loss = avg_val_loss
        best_model_state = model.state_dict()
        patience_counter = 0
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print("Early stopping triggered.")
            break


# Загрузка наилучшей модели
model.load_state_dict(best_model_state)

# Оценка
model.eval()
all_preds = []
with torch.no_grad():
    for batch_X, _ in val_loader:
        batch_X = batch_X.to(device)
        output = model(batch_X)
        preds = torch.argmax(output, dim=1)
        all_preds.extend(preds.cpu().numpy())

print("Final Test Accuracy:", accuracy_score(y_test.numpy(), all_preds))


# Графики
epochs = range(1, len(train_losses) + 1)

plt.figure(figsize=(16, 5))

# Loss
plt.subplot(1, 3, 1)
plt.plot(epochs, train_losses, label='Train Loss')
plt.plot(epochs, val_losses, label='Val Loss')
plt.title('Loss over epochs')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

# Accuracy
plt.subplot(1, 3, 2)
plt.plot(epochs, val_accuracies, label='Val Accuracy', color='green')
plt.title('Validation Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.ylim(0, 1)
plt.legend()

# F1 Score
plt.subplot(1, 3, 3)
plt.plot(epochs, val_f1s, label='F1 Score', color='orange')
plt.title('Validation F1 Score')
plt.xlabel('Epoch')
plt.ylabel('F1 Score')
plt.ylim(0, 1)
plt.legend()

plt.tight_layout()
plt.show()
'''
        elif number == 4:
             return '''
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from torch.nn.utils.rnn import pad_sequence
from collections import Counter
import re
import torch.optim as optim
from sklearn.metrics import accuracy_score, f1_score
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt
from tqdm import tqdm
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('wordnet')

def text_preprocessing(text):
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return ' '.join(tokens)

# Загрузка данных
df = pd.read_csv('news.csv')  # Ваш датасет

# Объединяем заголовок и описание
df['text'] = df['Title'] + " " + df['Description']
df.loc[:, 'cleaned_text'] = df['text'].apply(text_preprocessing)
# Создаем словарь
word_counts = Counter()
for text in df['cleaned_text']:
    word_counts.update(text.split())
vocab = {word: i+2 for i, word in enumerate(word for word, count in word_counts.most_common(10000))}  # 0 - паддинг, 1 - OOV
vocab_size = len(vocab) + 2

# Преобразование текста в последовательности индексов
def text_to_seq(text):
    return [vocab.get(word, 1) for word in text.split()]  # 1 для неизвестных слов

X = [torch.tensor(text_to_seq(text)) for text in df['cleaned_text']]
X_padded = pad_sequence(X, batch_first=True, padding_value=0)

# Подготовка меток классов
classes = sorted(df['Class Index'].unique())
num_classes = len(classes)
y = torch.tensor(df['Class Index'].apply(lambda x: classes.index(x)))

# Гиперпараметры
vocab_size = max(vocab.values()) + 1
embedding_dim = 256
hidden_dim = 128
num_classes = len(sentiment_map)
maxlen = max([len(seq) for seq in X])  # максимальная длина последовательности

# padding
X_padded = pad_sequence(X, batch_first=True, padding_value=0)
X_padded = X_padded[:, :maxlen]  # ограничим длину при необходимости

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X_padded, y, test_size=0.2, random_state=10)
train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=64, shuffle=True)
val_loader = DataLoader(TensorDataset(X_test, y_test), batch_size=64)

class LSTM_mult(nn.Module):
    def __init__(self, vocab_size, embedding_dim, out_features):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.rnn = nn.LSTM(embedding_dim, 128, batch_first=True, bidirectional=True, num_layers=2, dropout=0.5)
        self.out = nn.Linear(128 * 2, out_features)
        self._init_weights()

    def _init_weights(self):
        # Xavier for embedding
        nn.init.xavier_uniform_(self.embedding.weight)

    def forward(self, x):
        x = self.embedding(x)
        x, (h_n, _) = self.rnn(x)
        hh = torch.cat((h_n[-2], h_n[-1]), dim=1)
        return self.out(hh)

class RNN_mult(nn.Module):
    def __init__(self, vocab_size, embedding_dim, out_features):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.rnn = nn.RNN(
            input_size=embedding_dim,
            hidden_size=128,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.5
        )
        self.batch_norm = nn.BatchNorm1d(128 * 2)
        self.out = nn.Linear(128 * 2, out_features)

        self._init_weights()

    def _init_weights(self):
        # Xavier for embedding
        nn.init.xavier_uniform_(self.embedding.weight)

        # Xavier for RNN weights
        for name, param in self.rnn.named_parameters():
            if 'weight' in name:
                nn.init.xavier_uniform_(param)
            elif 'bias' in name:
                nn.init.constant_(param, 0)

        # Xavier for linear layer
        nn.init.xavier_uniform_(self.out.weight)
        nn.init.constant_(self.out.bias, 0)

    def forward(self, x):
        x = self.embedding(x)                         # (batch, seq_len, embedding_dim)
        x, h_n = self.rnn(x)                          # h_n: (num_layers * 2, batch, hidden)
        h_cat = torch.cat((h_n[-2], h_n[-1]), dim=1)  # (batch, hidden_size * 2)
        h_cat = self.batch_norm(h_cat)                # batch norm over features
        return self.out(h_cat)

# Инициализация
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
num_classes = 5
model = RNN_mult(vocab_size, embedding_dim, num_classes).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Early stopping
best_val_loss = float('inf')
patience = 5
patience_counter = 0

train_losses = []
val_losses = []
val_accuracies = []
val_f1s = []

for epoch in tqdm(range(20)):
    model.train()
    total_loss = 0
    for batch_X, batch_y in train_loader:
        batch_X, batch_y = batch_X.to(device), batch_y.to(device)
        optimizer.zero_grad()
        output = model(batch_X)
        loss = criterion(output, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    # Валидация
    model.eval()
    val_loss = 0
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for batch_X, batch_y in val_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            output = model(batch_X)
            loss = criterion(output, batch_y)
            val_loss += loss.item()
            preds = torch.argmax(output, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(batch_y.cpu().numpy())

    avg_train_loss = total_loss / len(train_loader)
    avg_val_loss = val_loss / len(val_loader)
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average='macro')

    # логируем
    train_losses.append(avg_train_loss)
    val_losses.append(avg_val_loss)
    val_accuracies.append(acc)
    val_f1s.append(f1)

    print(f"Epoch {epoch+1}, Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}, Val Accuracy: {acc:.4f}, F1: {f1:.4f}")

    if avg_val_loss < best_val_loss:
        best_val_loss = avg_val_loss
        best_model_state = model.state_dict()
        patience_counter = 0
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print("Early stopping triggered.")
            break


# Загрузка наилучшей модели
model.load_state_dict(best_model_state)

# Оценка
model.eval()
all_preds = []
with torch.no_grad():
    for batch_X, _ in val_loader:
        batch_X = batch_X.to(device)
        output = model(batch_X)
        preds = torch.argmax(output, dim=1)
        all_preds.extend(preds.cpu().numpy())

print("Final Test Accuracy:", accuracy_score(y_test.numpy(), all_preds))


# Графики
epochs = range(1, len(train_losses) + 1)

plt.figure(figsize=(16, 5))

# Loss
plt.subplot(1, 3, 1)
plt.plot(epochs, train_losses, label='Train Loss')
plt.plot(epochs, val_losses, label='Val Loss')
plt.title('Loss over epochs')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

# Accuracy
plt.subplot(1, 3, 2)
plt.plot(epochs, val_accuracies, label='Val Accuracy', color='green')
plt.title('Validation Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.ylim(0, 1)
plt.legend()

# F1 Score
plt.subplot(1, 3, 3)
plt.plot(epochs, val_f1s, label='F1 Score', color='orange')
plt.title('Validation F1 Score')
plt.xlabel('Epoch')
plt.ylabel('F1 Score')
plt.ylim(0, 1)
plt.legend()

plt.tight_layout()
plt.show()'''

        elif number == 5:
             return '''
import json

# Чтение из файла
with open('/content/pos.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
import re
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

word_counts = Counter()
tag_counts = Counter()

for example in data:
    words = example['sentence'].split()
    tags = example['tags']
    word_counts.update(words)
    tag_counts.update(tags)

# Словари для слов и тэгов
word_to_idx = {word: i+2 for i, word in enumerate(word for word, count in word_counts.most_common())}  # 0 - паддинг, 1 - OOV
tag_to_idx = {tag: i for i, tag in enumerate(tag_counts.keys())}

vocab_size = len(word_to_idx) + 2
num_tags = len(tag_to_idx)

# Преобразование в тензоры
def prepare_example(example):
    words = example['sentence'].split()
    tags = example['tags']

    word_indices = [word_to_idx.get(word, 1) for word in words]  # 1 для OOV
    tag_indices = [tag_to_idx[tag] for tag in tags]

    return torch.tensor(word_indices), torch.tensor(tag_indices)

# Подготовка всех данных
X = []
y = []
for example in data:
    word_tensor, tag_tensor = prepare_example(example)
    X.append(word_tensor)
    y.append(tag_tensor)

# Добавление паддинга
X_padded = pad_sequence(X, batch_first=True, padding_value=0)
y_padded = pad_sequence(y, batch_first=True, padding_value=-1)  # -1 для игнорирования при вычислении потерь

class CNNTagger(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_filters, num_tags, kernel_sizes=[3, 5]):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)

        # Сверточные слои с разными размерами окон
        self.convs = nn.ModuleList([
            nn.Conv1d(embed_dim, num_filters, ks, padding=ks//2)
            for ks in kernel_sizes
        ])

        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(num_filters * len(kernel_sizes), num_tags)

    def forward(self, x):
        # x: [batch_size, seq_len]
        embedded = self.embedding(x)  # [batch_size, seq_len, embed_dim]
        embedded = embedded.permute(0, 2, 1)  # [batch_size, embed_dim, seq_len]

        # Применяем свертки и max-pooling
        conv_outputs = []
        for conv in self.convs:
            conv_out = torch.relu(conv(embedded))  # [batch_size, num_filters, seq_len]
            conv_out = conv_out.permute(0, 2, 1)  # [batch_size, seq_len, num_filters]
            conv_outputs.append(conv_out)

        # Объединяем выходы сверток
        combined = torch.cat(conv_outputs, dim=2)  # [batch_size, seq_len, num_filters*len(kernel_sizes)]
        combined = self.dropout(combined)

        return self.fc(combined)  # [batch_size, seq_len, num_tags]

# Параметры
embed_dim = 100
num_filters = 64
kernel_sizes = [3, 5]
batch_size = 32

# Инициализация
model = CNNTagger(vocab_size, embed_dim, num_filters, num_tags, kernel_sizes)
criterion = nn.CrossEntropyLoss(ignore_index=-1)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# DataLoader
from torch.utils.data import TensorDataset, DataLoader
dataset = TensorDataset(X_padded, y_padded)
loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# Обучение
for epoch in range(10):
    model.train()
    total_loss = 0

    for batch_X, batch_y in loader:
        optimizer.zero_grad()
        outputs = model(batch_X)  # [batch_size, seq_len, num_tags]

        # Reshape для вычисления потерь
        loss = criterion(
            outputs.view(-1, num_tags),
            batch_y.view(-1)
        )

        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    print(f"Epoch {epoch+1}, Loss: {total_loss/len(loader):.4f}")

def predict(sentence, model, word_to_idx, tag_to_idx):
    idx_to_tag = {v: k for k, v in tag_to_idx.items()}
    words = sentence.split()
    word_indices = [word_to_idx.get(word, 1) for word in words]
    x = torch.tensor([word_indices])

    model.eval()
    with torch.no_grad():
        outputs = model(x)
        preds = torch.argmax(outputs, dim=2).squeeze().tolist()

    return list(zip(words, [idx_to_tag[idx] for idx in preds]))

# Пример
sentence = "what is the effect of gravity"
print(predict(sentence, model, word_to_idx, tag_to_idx))
'''

        elif number == 6:
            return '''
import re
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score

import json

# Чтение из файла
with open('/content/quotes.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

data = pd.DataFrame(data)

# 1. Подготовка данных
data = data.drop_duplicates(subset=['Quote'])
data['Quote'] = data['Quote'].str.lower()
data['Quote'] = data['Quote'].apply(lambda x: re.sub('[^a-zA-Z\s]', '', x))

# Фильтрация и объединение цитат в один текст с разделителями
quotes = data['Quote'].tolist()
text = " <eos> ".join(quotes) + " <eos>"  # Добавляем специальный токен конца предложения

# Создание словаря символов
chars = sorted(list(set(text)))
char_to_idx = {ch: i for i, ch in enumerate(chars)}
idx_to_char = {i: ch for i, ch in enumerate(chars)}
vocab_size = len(chars)

# Параметры
seq_length = 40  # Длина контекста
hidden_size = 128
num_layers = 2
batch_size = 64  # Увеличим для стабильности
learning_rate = 0.005
num_epochs = 1000

# 2. Создание обучающих данных с учетом структуры предложений
def create_sequences(text, seq_length, step = 3):
    sequences = []
    for i in range(0, len(text) - seq_length, step):
        seq = text[i:i + seq_length]
        target = text[i+1:i+1+seq_length]
        sequences.append((seq, target))
    return sequences

sequences = create_sequences(text, seq_length)

class CharRNN(nn.Module):
    def __init__(self, vocab_size, hidden_size, num_layers):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.embedding = nn.Embedding(vocab_size, hidden_size)
        #self.rnn = nn.GRU(hidden_size, hidden_size, num_layers, batch_first=True)
        self.rnn = nn.LSTM(hidden_size, hidden_size, num_layers,dropout=0.2, batch_first=True)
        self.fc = nn.Linear(hidden_size, vocab_size)

    def forward(self, x, hidden):
        x = self.embedding(x)  # (batch_size, seq_len, hidden_size)
        out, hidden = self.rnn(x, hidden)
        out = self.fc(out)  # (batch_size, seq_len, vocab_size)
        return out, hidden

    def init_hidden(self, batch_size):
        return (torch.zeros(self.num_layers, batch_size, self.hidden_size),
                torch.zeros(self.num_layers, batch_size, self.hidden_size))
        #return torch.zeros(self.num_layers, batch_size, self.hidden_size)

model = CharRNN(vocab_size, hidden_size, num_layers)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)
# 4. Исправленная функция обучения
def train_batch(model, sequences, batch_size):
    model.train()
    total_loss = 0

    # Создаём батч
    batch_idx = np.random.choice(len(sequences), batch_size, replace=False)
    batch_sequences = [sequences[idx] for idx in batch_idx]

    # Подготавливаем входные данные и цели
    inputs = torch.zeros(batch_size, seq_length, dtype=torch.long)
    targets = torch.zeros(batch_size, seq_length, dtype=torch.long)

    for i, (seq, target) in enumerate(batch_sequences):
        inputs[i] = torch.tensor([char_to_idx[ch] for ch in seq])
        targets[i] = torch.tensor([char_to_idx[ch] for ch in target])

    # Инициализируем hidden state для всего батча
    hidden = model.init_hidden(batch_size)

    optimizer.zero_grad()
    output, hidden = model(inputs, hidden)
    loss = criterion(output.view(-1, vocab_size), targets.view(-1))

    loss.backward()
    optimizer.step()

    return loss.item()

losses = []
for epoch in range(num_epochs):
    loss = train_batch(model, sequences, batch_size)
    losses.append(loss)

    if (epoch+1) % 100 == 0:
        print(f'Epoch {epoch+1}, Loss: {loss:.4f}')
        
def generate(model, start_str, length=200, temperature=0.5):
    model.eval()
    with torch.no_grad():
        chars = [ch for ch in start_str]
        hidden = model.init_hidden(1)  # batch_size=1 при генерации

        for _ in range(length):
            # Подготовка последнего символа как входа
            input_tensor = torch.tensor([[char_to_idx[chars[-1]]]])  # [1, 1]

            # Прямой проход
            output, hidden = model(input_tensor, hidden)

            # Получаем последний выход и применяем температуру
            last_output = output[:, -1, :]  # Берем только последний выход
            probs = torch.softmax(last_output / temperature, dim=-1)

            # Выбираем следующий символ
            next_char = torch.multinomial(probs, 1).item()

            chars.append(idx_to_char[next_char])

            if chars[-1] == '<eos>':  # Остановка при конце предложения
                break

    return ''.join(chars)
    
# Пример генерации
print("\nGenerated text:")
print(generate(model, "life is", 200, temperature=0.9))
'''
        elif number == 7:
            return '''
import re
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

import json

data = []
with open('/content/reviews.json', 'r', encoding='utf-8') as file:
    for line in file:
        line = line.strip()
        if line:  # Пропускаем пустые строки
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Ошибка в строке: {line}\n{e}")

print(f"Успешно загружено {len(data)} записей")

data = pd.DataFrame(data)

# 1. Подготовка данных
data = data.drop_duplicates(subset=['reviewText'])
data['reviewText'] = data['reviewText'].str.lower()
data['reviewText'] = data['reviewText'].apply(lambda x: re.sub('[^a-zA-Z\s]', '', x))

# Фильтрация и объединение цитат в один текст с разделителями
quotes = data['reviewText'].tolist()
text = " <eos> ".join(quotes) + " <eos>"  # Добавляем специальный токен конца предложения

# Создание словаря символов
chars = sorted(list(set(text)))
char_to_idx = {ch: i for i, ch in enumerate(chars)}
idx_to_char = {i: ch for i, ch in enumerate(chars)}
vocab_size = len(chars)

# Параметры
seq_length = 40  # Длина контекста
hidden_size = 128
num_layers = 2
batch_size = 64  # Увеличим для стабильности
learning_rate = 0.005
num_epochs = 1000

# 2. Создание обучающих данных с учетом структуры предложений
def create_sequences(text, seq_length, step = 3):
    sequences = []
    for i in range(0, len(text) - seq_length, step):
        seq = text[i:i + seq_length]
        target = text[i+1:i+1+seq_length]
        sequences.append((seq, target))
    return sequences

sequences = create_sequences(text, seq_length)

class CharRNN(nn.Module):
    def __init__(self, vocab_size, hidden_size, num_layers):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.embedding = nn.Embedding(vocab_size, hidden_size)
        #self.rnn = nn.GRU(hidden_size, hidden_size, num_layers, batch_first=True)
        self.rnn = nn.LSTM(hidden_size, hidden_size, num_layers,dropout=0.2, batch_first=True)
        self.fc = nn.Linear(hidden_size, vocab_size)

    def forward(self, x, hidden):
        x = self.embedding(x)  # (batch_size, seq_len, hidden_size)
        out, hidden = self.rnn(x, hidden)
        out = self.fc(out)  # (batch_size, seq_len, vocab_size)
        return out, hidden

    def init_hidden(self, batch_size):
        return (torch.zeros(self.num_layers, batch_size, self.hidden_size),
                torch.zeros(self.num_layers, batch_size, self.hidden_size))
        #return torch.zeros(self.num_layers, batch_size, self.hidden_size)

model = CharRNN(vocab_size, hidden_size, num_layers)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)
# 4. Исправленная функция обучения
def train_batch(model, sequences, batch_size):
    model.train()
    total_loss = 0

    # Создаём батч
    batch_idx = np.random.choice(len(sequences), batch_size, replace=False)
    batch_sequences = [sequences[idx] for idx in batch_idx]

    # Подготавливаем входные данные и цели
    inputs = torch.zeros(batch_size, seq_length, dtype=torch.long)
    targets = torch.zeros(batch_size, seq_length, dtype=torch.long)

    for i, (seq, target) in enumerate(batch_sequences):
        inputs[i] = torch.tensor([char_to_idx[ch] for ch in seq])
        targets[i] = torch.tensor([char_to_idx[ch] for ch in target])

    # Инициализируем hidden state для всего батча
    hidden = model.init_hidden(batch_size)

    optimizer.zero_grad()
    output, hidden = model(inputs, hidden)
    loss = criterion(output.view(-1, vocab_size), targets.view(-1))

    loss.backward()
    optimizer.step()

    return loss.item()

losses = []
for epoch in range(num_epochs):
    loss = train_batch(model, sequences, batch_size)
    losses.append(loss)

    if (epoch+1) % 100 == 0:
        print(f'Epoch {epoch+1}, Loss: {loss:.4f}')
        
def generate(model, start_str, length=200, temperature=0.7):
    model.eval()
    with torch.no_grad():
        chars = [ch for ch in start_str]
        hidden = model.init_hidden(1)  # batch_size=1 при генерации

        for _ in range(length):
            # Подготовка последнего символа как входа
            input_tensor = torch.tensor([[char_to_idx[chars[-1]]]])  # [1, 1]

            # Прямой проход
            output, hidden = model(input_tensor, hidden)

            # Получаем последний выход и применяем температуру
            last_output = output[:, -1, :]  # Берем только последний выход
            probs = torch.softmax(last_output / temperature, dim=-1)

            # Выбираем следующий символ
            next_char = torch.multinomial(probs, 1).item()

            chars.append(idx_to_char[next_char])

            if chars[-1] == '<eos>':  # Остановка при конце предложения
                break

    return ''.join(chars)
    
# Пример генерации
print("\nGenerated text:")
print(generate(model, "life is", 200, temperature=0.9))
'''
        elif number == 8:
            return '''
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from torch.nn.utils.rnn import pad_sequence
from collections import Counter
import re
import torch.optim as optim
from sklearn.metrics import accuracy_score, f1_score
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt
from tqdm import tqdm
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('wordnet')

def text_preprocessing(text):
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return ' '.join(tokens)


df = pd.read_csv('/content/tweet_cat.csv')
df.loc[:, 'cleaned_text'] = df['text'].apply(text_preprocessing)
df['type'].value_counts()

# Создание словаря
word_counts = Counter()
for text in df['cleaned_text']:
    word_counts.update(text.split())
vocab = {word: i+2 for i, word in enumerate(word for word, count in word_counts.most_common(10000))}
vocab_size = len(vocab) + 2

# Преобразование текста в индексы
def text_to_seq(text):
    return [vocab.get(word, 1) for word in text.split()]

X = [torch.tensor(text_to_seq(text)) for text in df['cleaned_text']]
X_padded = pad_sequence(X, batch_first=True, padding_value=0)

# Метки
mapping = {'politics': 0,'medical': 1, 'entertainment': 2,'sports':3}
df['label'] = df['type'].map(mapping)
y = torch.tensor(df['type'].map(mapping).values)

# Гиперпараметры
vocab_size = max(vocab.values()) + 1
embedding_dim = 128
hidden_dim = 64
num_classes = 4
maxlen = max([len(seq) for seq in X])  # максимальная длина последовательности

# padding
X_padded = pad_sequence(X, batch_first=True, padding_value=0)
X_padded = X_padded[:, :maxlen]  # ограничим длину при необходимости

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X_padded, y, test_size=0.2, random_state=10)
train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=64, shuffle=True)
val_loader = DataLoader(TensorDataset(X_test, y_test), batch_size=64)

class LSTM_mult(nn.Module):
    def __init__(self, vocab_size, embedding_dim, out_features):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.rnn = nn.LSTM(embedding_dim, 64, batch_first=True, bidirectional=True, num_layers=2, dropout=0.5)
        self.out = nn.Linear(64 * 2, out_features)
        self._init_weights()

    def _init_weights(self):
        # Xavier for embedding
        nn.init.xavier_uniform_(self.embedding.weight)

    def forward(self, x):
        x = self.embedding(x)
        x, (h_n, _) = self.rnn(x)
        hh = torch.cat((h_n[-2], h_n[-1]), dim=1)
        return self.out(hh)

class RNN_mult(nn.Module):
    def __init__(self, vocab_size, embedding_dim, out_features):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.rnn = nn.RNN(
            input_size=embedding_dim,
            hidden_size=128,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.5
        )
        self.batch_norm = nn.BatchNorm1d(128 * 2)
        self.out = nn.Linear(128 * 2, out_features)

        self._init_weights()

    def _init_weights(self):
        # Xavier for embedding
        nn.init.xavier_uniform_(self.embedding.weight)

        # Xavier for RNN weights
        for name, param in self.rnn.named_parameters():
            if 'weight' in name:
                nn.init.xavier_uniform_(param)
            elif 'bias' in name:
                nn.init.constant_(param, 0)

        # Xavier for linear layer
        nn.init.xavier_uniform_(self.out.weight)
        nn.init.constant_(self.out.bias, 0)

    def forward(self, x):
        x = self.embedding(x)                         # (batch, seq_len, embedding_dim)
        x, h_n = self.rnn(x)                          # h_n: (num_layers * 2, batch, hidden)
        h_cat = torch.cat((h_n[-2], h_n[-1]), dim=1)  # (batch, hidden_size * 2)
        h_cat = self.batch_norm(h_cat)                # batch norm over features
        return self.out(h_cat)

# Инициализация
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
num_classes = 5
model = LSTM_mult(vocab_size, embedding_dim, num_classes).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Early stopping
best_val_loss = float('inf')
patience = 10
patience_counter = 0

train_losses = []
val_losses = []
val_accuracies = []
val_f1s = []

for epoch in tqdm(range(20)):
    model.train()
    total_loss = 0
    for batch_X, batch_y in train_loader:
        batch_X, batch_y = batch_X.to(device), batch_y.to(device)
        optimizer.zero_grad()
        output = model(batch_X)
        loss = criterion(output, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    # Валидация
    model.eval()
    val_loss = 0
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for batch_X, batch_y in val_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            output = model(batch_X)
            loss = criterion(output, batch_y)
            val_loss += loss.item()
            preds = torch.argmax(output, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(batch_y.cpu().numpy())

    avg_train_loss = total_loss / len(train_loader)
    avg_val_loss = val_loss / len(val_loader)
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average='macro')

    # логируем
    train_losses.append(avg_train_loss)
    val_losses.append(avg_val_loss)
    val_accuracies.append(acc)
    val_f1s.append(f1)

    print(f"Epoch {epoch+1}, Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}, Val Accuracy: {acc:.4f}, F1: {f1:.4f}")

    if avg_val_loss < best_val_loss:
        best_val_loss = avg_val_loss
        best_model_state = model.state_dict()
        patience_counter = 0
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print("Early stopping triggered.")
            break


# Загрузка наилучшей модели
model.load_state_dict(best_model_state)

# Оценка
model.eval()
all_preds = []
with torch.no_grad():
    for batch_X, _ in val_loader:
        batch_X = batch_X.to(device)
        output = model(batch_X)
        preds = torch.argmax(output, dim=1)
        all_preds.extend(preds.cpu().numpy())

print("Final Test Accuracy:", accuracy_score(y_test.numpy(), all_preds))


# Графики
epochs = range(1, len(train_losses) + 1)

plt.figure(figsize=(16, 5))

# Loss
plt.subplot(1, 3, 1)
plt.plot(epochs, train_losses, label='Train Loss')
plt.plot(epochs, val_losses, label='Val Loss')
plt.title('Loss over epochs')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

# Accuracy
plt.subplot(1, 3, 2)
plt.plot(epochs, val_accuracies, label='Val Accuracy', color='green')
plt.title('Validation Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.ylim(0, 1)
plt.legend()

# F1 Score
plt.subplot(1, 3, 3)
plt.plot(epochs, val_f1s, label='F1 Score', color='orange')
plt.title('Validation F1 Score')
plt.xlabel('Epoch')
plt.ylabel('F1 Score')
plt.ylim(0, 1)
plt.legend()

plt.tight_layout()
plt.show()'''
        elif number == 10:
             return'''
import torch
import torch.nn as nn
import torch.optim as optim

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from sklearn.model_selection import train_test_split
import numpy as np
import random
#обрезала так как не помещается в озу
pairs_tensor = torch.load('/content/sents_pairs.pt')[:10000]
jaccard_scores = torch.load('/content/jaccard.pt')[:10000]

# 1. Улучшенная модель с регуляризацией
class RobustCNNJaccardPredictor(nn.Module):
    def __init__(self, vocab_size, embed_dim=128, seq_len=50):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)

        # Более простая CNN
        self.conv_net = nn.Sequential(
            nn.Conv1d(embed_dim, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Dropout(0.2),

            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Dropout(0.3)
        )

        # Размер после сверток
        self.flatten_size = 128 * (seq_len // 4)

        # Head с регуляризацией
        self.head = nn.Sequential(
            nn.Linear(self.flatten_size * 4, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    def forward(self, x1, x2):
        emb1 = self.embedding(x1).permute(0, 2, 1)
        emb2 = self.embedding(x2).permute(0, 2, 1)

        conv_out1 = self.conv_net(emb1).flatten(1)
        conv_out2 = self.conv_net(emb2).flatten(1)

        combined = torch.cat([
            conv_out1,
            conv_out2,
            torch.abs(conv_out1 - conv_out2),
            conv_out1 * conv_out2
        ], dim=1)

        return self.head(combined)

# 2. Инициализация
vocab_size = 10000
seq_len = 50
num_pairs = 1000

# Данные
pairs_tensor = torch.randint(0, vocab_size, (num_pairs, 2, seq_len))
jaccard_scores = torch.rand(num_pairs)

# Разделение
X_train, X_test, y_train, y_test = train_test_split(
    pairs_tensor.numpy(),
    jaccard_scores.numpy(),
    test_size=0.2,
    random_state=42
)

X_train, X_test = torch.from_numpy(X_train), torch.from_numpy(X_test)
y_train, y_test = torch.from_numpy(y_train), torch.from_numpy(y_test)

# 3. Обучение с регуляризацией
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = RobustCNNJaccardPredictor(vocab_size, seq_len=seq_len).to(device)
optimizer = optim.AdamW(model.parameters(), lr=0.0005, weight_decay=1e-4)
scheduler = ReduceLROnPlateau(optimizer, 'min', patience=3, factor=0.5)
criterion = nn.HuberLoss()

# Early stopping
best_val_loss = float('inf')
patience = 5
no_improve = 0

for epoch in range(50):
    model.train()
    optimizer.zero_grad()

    # Forward
    inputs1 = X_train[:, 0, :].to(device)
    inputs2 = X_train[:, 1, :].to(device)
    targets = y_train.to(device).float().unsqueeze(1)

    outputs = model(inputs1, inputs2)
    loss = criterion(outputs, targets)

    # Backward
    loss.backward()
    optimizer.step()

    # Validation
    model.eval()
    with torch.no_grad():
        val_inputs1 = X_test[:, 0, :].to(device)
        val_inputs2 = X_test[:, 1, :].to(device)
        val_targets = y_test.to(device).float().unsqueeze(1)

        val_outputs = model(val_inputs1, val_inputs2)
        val_loss = criterion(val_outputs, val_targets)

    scheduler.step(val_loss)

    # Early stopping
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        no_improve = 0
        torch.save(model.state_dict(), 'best_model.pth')
    else:
        no_improve += 1

    print(f'Epoch {epoch+1}: Train Loss: {loss.item():.4f}, Val Loss: {val_loss.item():.4f}, LR: {optimizer.param_groups[0]["lr"]:.6f}')

    if no_improve >= patience:
        print(f'Early stopping at epoch {epoch+1}')
        break

# Загрузка лучшей модели
model.load_state_dict(torch.load('best_model.pth'))


model.eval()  # Переводим модель в режим оценки
with torch.no_grad():
    test_inputs1 = X_test[:, 0, :].to(device)
    test_inputs2 = X_test[:, 1, :].to(device)
    predictions = model(test_inputs1, test_inputs2)

# Конвертируем в numpy для удобства
predictions = predictions.cpu().numpy()
true_values = y_test.numpy()

# Выводим первые 10 предсказаний
for i in range(10):
    print(f"Пара {i+1}:")
    print(f"Истинное значение: {true_values[i]:.4f}")
    print(f"Предсказание: {predictions[i][0]:.4f}")
    print("-"*30)

# Создаем новые случайные данные для демонстрации
new_pairs = torch.randint(0, vocab_size, (5, 2, seq_len))  # 5 новых пар

# Получаем предсказания
model.eval()
with torch.no_grad():
    new_inputs1 = new_pairs[:, 0, :].to(device)
    new_inputs2 = new_pairs[:, 1, :].to(device)
    new_predictions = model(new_inputs1, new_inputs2)

# Выводим результаты
print("\nПредсказания для новых пар:")
for i in range(new_predictions.shape[0]):
    print(f"Пара {i+1}: {new_predictions[i].item():.4f}")'''
        elif number == 11:
            return '''

import torch
import torch.nn as nn

class CustomRNNCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.fc = nn.Linear(input_size + hidden_size, hidden_size)
        self.activation = nn.Tanh()

    def forward(self, x, hidden_state):
        combined = torch.cat((x, hidden_state), dim=1)
        new_hidden = self.fc(combined)
        new_hidden = self.activation(new_hidden)
        return new_hidden

class CustomRNN(nn.Module):
    def __init__(self, input_size, hidden_size, bidirectional=False):
        super().__init__()
        self.hidden_size = hidden_size
        self.bidirectional = bidirectional

        # Создаем ячейки в зависимости от режима
        if bidirectional:
            self.forward_rnn = CustomRNNCell(input_size, hidden_size)
            self.backward_rnn = CustomRNNCell(input_size, hidden_size)
        else:
            self.rnn_cell = CustomRNNCell(input_size, hidden_size)

    def forward(self, x, hidden=None):
        batch_size, seq_len, _ = x.size()

        if self.bidirectional:
            # Инициализация для двунаправленного режима
            if hidden is None:
                h_forward = torch.zeros(batch_size, self.hidden_size).to(x.device)
                h_backward = torch.zeros(batch_size, self.hidden_size).to(x.device)
            else:
                h_forward, h_backward = hidden

            # Прямой проход
            forward_outputs = []
            for t in range(seq_len):
                x_t = x[:, t, :]
                h_forward = self.forward_rnn(x_t, h_forward)
                forward_outputs.append(h_forward)

            # Обратный проход
            backward_outputs = []
            for t in reversed(range(seq_len)):
                x_t = x[:, t, :]
                h_backward = self.backward_rnn(x_t, h_backward)
                backward_outputs.insert(0, h_backward)

            # Объединяем выходы
            forward_outputs = torch.stack(forward_outputs, dim=1)
            backward_outputs = torch.stack(backward_outputs, dim=1)
            combined_outputs = torch.cat((forward_outputs, backward_outputs), dim=2)
            last_hidden = torch.cat((h_forward, h_backward), dim=1)

            return combined_outputs, last_hidden

        else:
            # Однонаправленный режим
            if hidden is None:
                hidden = torch.zeros(batch_size, self.hidden_size).to(x.device)

            outputs = []
            for t in range(seq_len):
                x_t = x[:, t, :]
                hidden = self.rnn_cell(x_t, hidden)
                outputs.append(hidden)

            outputs = torch.stack(outputs, dim=1)
            return outputs, hidden'''
        elif number == 12:
             return '''
class Word2Vec(nn.Module):
    def __init__(self, vocab_size, embed_dim):
        super().__init__()
        self.input_embedding = nn.Embedding(vocab_size, embed_dim)
        self.output_embedding = nn.Embedding(vocab_size, embed_dim)

    def forward(self, center, context, negative):
        # center shape: (batch_size)
        # context shape: (batch_size)
        # negative shape: (batch_size, num_negative)

        center_emb = self.input_embedding(center)  # (batch_size, embed_dim)
        context_emb = self.output_embedding(context)  # (batch_size, embed_dim)
        negative_emb = self.output_embedding(negative)  # (batch_size, num_negative, embed_dim)

        pos_score = torch.sum(center_emb * context_emb, dim=1)  # (batch_size)
        pos_score = torch.sigmoid(pos_score)

        neg_score = torch.bmm(negative_emb, center_emb.unsqueeze(2)).squeeze(2)  # (batch_size, num_negative)
        neg_score = torch.sigmoid(-neg_score)

        return pos_score, neg_score

# Пример использования
vocab_size = 10000
embed_dim = 100
model = Word2Vec(vocab_size, embed_dim)

center_words = torch.randint(0, vocab_size, (32,))
context_words = torch.randint(0, vocab_size, (32,))
negative_words = torch.randint(0, vocab_size, (32, 5))  # 5 negative samples

pos, neg = model(center_words, context_words, negative_words)
print(pos.shape, neg.shape)  # (32,), (32, 5)'''
        elif number == 13:
             return '''
class CustomAttention(nn.Module):
    def __init__(self, embed_dim: int):
        super().__init__()
        self.query = nn.Linear(embed_dim, embed_dim)
        self.key = nn.Linear(embed_dim, embed_dim)
        self.value = nn.Linear(embed_dim, embed_dim)
        
    def forward(self, x: Tensor) -> Tensor:
        Q = self.query(x)
        K = self.key(x)
        V = self.value(x)
        
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(x.size(-1))
        weights = F.softmax(scores, dim=-1)
        return torch.matmul(weights, V)

# Пример использования
attn = CustomAttention(embed_dim=64)
input_seq = torch.randn(5, 10, 64)  # [batch, seq_len, embed_dim]
output = attn(input_seq)
print(f"Attention output shape: {output.shape}")'''

        elif number == 14:
             return '''
class CustomBatchNorm1d(nn.Module):
    def __init__(self, num_features: int, eps: float = 1e-5, momentum: float = 0.1):
        super().__init__()
        self.gamma = nn.Parameter(torch.ones(num_features))
        self.beta = nn.Parameter(torch.zeros(num_features))
        self.register_buffer('running_mean', torch.zeros(num_features))
        self.register_buffer('running_var', torch.ones(num_features))
        self.eps = eps
        self.momentum = momentum
        
    def forward(self, x: Tensor) -> Tensor:
        if self.training:
            mean = x.mean(dim=0)
            var = x.var(dim=0, unbiased=False)
            with torch.no_grad():
                self.running_mean = (1-self.momentum)*self.running_mean + self.momentum*mean
                self.running_var = (1-self.momentum)*self.running_var + self.momentum*var
        else:
            mean = self.running_mean
            var = self.running_var
            
        x_norm = (x - mean) / torch.sqrt(var + self.eps)
        return self.gamma * x_norm + self.beta

# Тестирование
bn = CustomBatchNorm1d(5)
x = torch.randn(10, 5)
print("Input mean:", x.mean(dim=0))
print("Normalized mean:", bn(x).mean(dim=0))'''
        elif number == 20:
            return '''
class LSTM_uni(nn.Module):
    def __init__(self, vocab_size, embedding_dim, out_features):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.rnn = nn.LSTM(
            embedding_dim, 
            128, 
            batch_first=True, 
            bidirectional=False,  # Однонаправленная
            num_layers=2, 
            dropout=0.5
        )
        self.out = nn.Linear(128, out_features)  # 128 вместо 128*2
        self._init_weights()

    def _init_weights(self):
        nn.init.xavier_uniform_(self.embedding.weight)

    def forward(self, x):
        x = self.embedding(x)
        x, (h_n, _) = self.rnn(x)
        return self.out(h_n[-1])  # Берем последний слой

class RNN_uni(nn.Module):
    def __init__(self, vocab_size, embedding_dim, out_features):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.rnn = nn.RNN(
            input_size=embedding_dim,
            hidden_size=128,
            num_layers=2,
            batch_first=True,
            bidirectional=False,  # Однонаправленная
            dropout=0.5
        )
        self.batch_norm = nn.BatchNorm1d(128)  # 128 вместо 128*2
        self.out = nn.Linear(128, out_features)  # 128 вместо 128*2

        self._init_weights()

    def _init_weights(self):
        nn.init.xavier_uniform_(self.embedding.weight)
        for name, param in self.rnn.named_parameters():
            if 'weight' in name:
                nn.init.xavier_uniform_(param)
            elif 'bias' in name:
                nn.init.constant_(param, 0)
        nn.init.xavier_uniform_(self.out.weight)
        nn.init.constant_(self.out.bias, 0)

    def forward(self, x):
        x = self.embedding(x)
        x, h_n = self.rnn(x)
        h_last = h_n[-1]  # Берем последний слой
        h_last = self.batch_norm(h_last)
        return self.out(h_last)'''



