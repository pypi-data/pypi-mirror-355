def hlp():
    print(''' q1() -  код, q1_th() - теория
    q1 - Наивное умножение матрицы на вектор и умножение матриц
    q2 - Иерархия памяти, план кеша и LRU, промахи в обращении к кешу
    q3 - Алгоритм Штрассена
    q4 - Собственные векторы, собственные значения (важность, Google PageRank)
    q5 - Разложение Шура и QR-алгоритм
    q6 - Степенной метод
    q7 - Круги Гершгорина
    q8 - Разложение Шура, теорема Шура
    q9 - Нормальные матрицы, эрмитовы матрицы, унитарно диагонализуемые матрицы, верхне-гессенбергова форма матриц
    q10 - Спектр и псевдоспектр
    q11 - Неявный QR алгоритм (со сдвигами)
    q12 - Алгоритм на основе стратегии "разделяй и властвуй"
    q13 - Разреженные матрицы, форматы хранения разреженных матриц, прямые методы для решения больших разреженных систем
    q14 - Обыкновенные дифференциальные уравнения, задача Коши
    q15 - Локальная, глобальная ошибки
    q16 - Метод центральной разности
    q17 - Метод Эйлера
    q18 - Метод предиктора-корректора
    q19 - Метод Рунге-Кутты 1-4 порядков
    q19_ex - пример рунге кутты 4 порядка + фазовый портрет
    q20 - Методы Адамса-Мултона, методы Адамса-Бэшфорта
    q20_ex - пример реализации Адамса-Мултона
    q21 - Метод Милна
    q22 - Согласованность, устойчивость, сходимость, условия устойчивости
    q23 - Моделирование волны с использованием математических инструментов (амплитуда, период, длина волны, частота, Герц, дискретизация, частота дискретизации, фаза, угловая частота)
    q24_ex - пример решения дискретный фурье
    q24_ex2 - пример решения дискретный фурье с фильтрацией
    q24 - Дискретное преобразование Фурье, обратное дискретное преобразование Фурье их ограничения, симметрии в дискретном преобразовании Фурье
    q25 - Быстрое преобразование Фурье, его принципы, фильтрация сигнала с использованием быстрого преобразования Фурье
    q25_ex - пример быстрого преобразования Фурье
    q26 - Операции свёртки, связь с быстрым преобразованием Фурье, операции дискретной свёртки
    q27 - Дискретная свёртка и Тёплицевы матрицы (Ганкелевы матрицы)
    q28 - Циркулянтные матрицы. Матрицы Фурье.
    q29 - Быстрый матвек с циркулянтом
    q30 - метод вращений
    q31 - метод непосредственного развертывания''')
    
    
    
    
    
def activities():
    import pyperclip
    result = '''import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import Dataset, DataLoader


df = pd.read_csv('activities.csv')
df = df[['Text', 'Review-Activity']].dropna()
print(df)


label_encoder = LabelEncoder()
df['Review-Activity'] = label_encoder.fit_transform(df['Review-Activity'])


vectorizer = TfidfVectorizer(max_features=5000)
X_tfidf = vectorizer.fit_transform(df['Text']).toarray()
y = df['Review-Activity'].values

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X_tfidf, y, test_size=0.2, random_state=42, stratify=y
)


class TfidfDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
    def __len__(self):
        return len(self.X)
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_dataset = TfidfDataset(X_train, y_train)
test_dataset = TfidfDataset(X_test, y_test)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)


class MLPClassifier(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(MLPClassifier, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        x = self.relu1(self.fc1(x))
        x = self.fc2(x)
        return x

input_dim = X_train.shape[1]
output_dim = len(np.unique(y))
model = MLPClassifier(input_dim, 128, output_dim)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)


num_epochs = 10
train_losses = []

for epoch in range(num_epochs):
    model.train()
    running_loss = 0
    for X_batch, y_batch in train_loader:
        
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        running_loss += loss.item()
        
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        
    
    epoch_loss = running_loss / len(train_loader)
    train_losses.append(epoch_loss)
    print(f"Epoch {epoch+1}/{num_epochs} Loss: {epoch_loss:.4f}")


plt.plot(train_losses)
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Loss over Epochs')
plt.show()


model.eval()
with torch.no_grad():
    X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
    outputs = model(X_test_tensor)
    _, predictions = torch.max(outputs, 1)


print(classification_report(y_test, predictions.numpy(), target_names=label_encoder.classes_))
'''
    pyperclip.copy(result)
    
    
def news():
    import pyperclip
    result = '''import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from nltk.tokenize import wordpunct_tokenize



df = pd.read_csv('news.csv')
df = df[['Title', 'Class Index']].dropna()

tokenized_titles = [wordpunct_tokenize(t.lower()) for t in df['Title']]
all_words = [word for title in tokenized_titles for word in title]
word_freq = Counter(all_words)
vocab = ['<PAD>', '<UNK>'] + [word for word, freq in word_freq.items() if freq > 1]
word2idx = {word: idx for idx, word in enumerate(vocab)}


def encode_title(title):
    return [word2idx.get(word, word2idx['<UNK>']) for word in title]

encoded_titles = [encode_title(title) for title in tokenized_titles]
max_len = max(len(seq) for seq in encoded_titles)


def pad_sequence(seq, max_len):
    return seq + [word2idx['<PAD>']] * (max_len - len(seq))

X = [pad_sequence(seq, max_len) for seq in encoded_titles]
y = [elem - 1 for elem in df['Class Index'].tolist()]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)



class NewsDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.long)
        self.y = torch.tensor(y, dtype=torch.long)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_dataset = NewsDataset(X_train, y_train)
test_dataset = NewsDataset(X_test, y_test)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32)


class RNNClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim):
        super(RNNClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.rnn = nn.RNN(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        embedded = self.embedding(x)
        output, hidden = self.rnn(embedded)
        return self.fc(hidden.squeeze(0))

vocab_size = len(vocab)
embed_dim = 100
hidden_dim = 128
output_dim = len(set(y))

model = RNNClassifier(vocab_size, embed_dim, hidden_dim, output_dim)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)


train_losses, test_losses = [], []
num_epochs = 10

for epoch in range(num_epochs):
    model.train()
    train_loss = 0
    for X_batch, y_batch in train_loader:
        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
    
    model.eval()
    test_loss = 0
    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            test_loss += loss.item()
    
    train_losses.append(train_loss / len(train_loader))
    test_losses.append(test_loss / len(test_loader))
    
    print(f"Epoch {epoch+1}/{num_epochs} - Train Loss: {train_losses[-1]:.4f}, Test Loss: {test_losses[-1]:.4f}")


plt.plot(train_losses, label='Train Loss')
plt.plot(test_losses, label='Test Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Loss over Epochs')
plt.legend()
plt.show()


model.eval()
all_preds, all_labels = [], []
with torch.no_grad():
    for X_batch, y_batch in test_loader:
        outputs = model(X_batch)
        _, preds = torch.max(outputs, 1)
        all_preds.extend(preds.tolist())
        all_labels.extend(y_batch.tolist())


print(classification_report(all_labels, all_preds))
print(confusion_matrix(all_labels, all_preds))



def decode_title(encoded):
    return ' '.join([vocab[idx] for idx in encoded if idx != word2idx['<PAD>']])
for i in range(5):
    sample = torch.tensor([X_test[i]], dtype=torch.long)
    with torch.no_grad():
        output = model(sample)
        _, pred = torch.max(output, 1)
    print(f"Title: {decode_title(X_test[i])}")
    print(f"True: {y_test[i]}")
    print(f"Predicted: {pred.item()}")
    print()'''
    pyperclip.copy(result)
    
def corona():
    import pyperclip
    result = '''import pandas as pd
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
from nltk.tokenize import wordpunct_tokenize
from torchtext.vocab import build_vocab_from_iterator
from torch.nn.utils.rnn import pad_sequence



df = pd.read_csv("corona.csv")

print(df.columns)
df = df[['OriginalTweet', 'Sentiment']].dropna()
df.columns = ['text', 'label']



label2id = {label: i for i, label in enumerate(df['label'].unique())}
id2label = {v: k for k, v in label2id.items()}
df['label'] = df['label'].map(label2id)


def tokenize(text):
    return wordpunct_tokenize(text.lower())


vocab = build_vocab_from_iterator(map(tokenize, df['text']), specials=['<pad>', '<unk>'])
vocab.set_default_index(vocab['<unk>'])
pad_idx = vocab['<pad>']

class TweetDataset(Dataset):
    def __init__(self, df):
        self.texts = df['text'].tolist()
        self.labels = df['label'].tolist()
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        tokens = vocab(tokenize(self.texts[idx]))
        return torch.tensor(tokens), torch.tensor(self.labels[idx])

def collate_batch(batch):
    texts, labels = zip(*batch)
    lengths = torch.tensor([len(x) for x in texts])
    padded = pad_sequence(texts, batch_first=True, padding_value=pad_idx)
    return padded, torch.tensor(labels), lengths



train_df, test_df = train_test_split(df, test_size=0.2, stratify=df['label'], random_state=42)

train_dl = DataLoader(TweetDataset(train_df), batch_size=32, shuffle=True, collate_fn=collate_batch)
test_dl = DataLoader(TweetDataset(test_df), batch_size=32, shuffle=False, collate_fn=collate_batch)

class RNNClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_size, output_size):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.rnn = nn.GRU(embed_dim, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x, lengths):
        emb = self.embedding(x)
        packed = nn.utils.rnn.pack_padded_sequence(emb, lengths.cpu(), batch_first=True, enforce_sorted=False)
        _, hidden = self.rnn(packed)
        return self.fc(hidden[-1])

    

model = RNNClassifier(len(vocab), 100, 64, len(label2id))

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

train_losses = []

for epoch in range(10):
    model.train()
    total_loss = 0
    for xb, yb, lengths in train_dl:
        
        preds = model(xb, lengths)
        loss = criterion(preds, yb)
        total_loss += loss.item()
        
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        
    
    avg_loss = total_loss / len(train_dl)
    train_losses.append(avg_loss)
    print(f"Epoch {epoch+1}: Train Loss = {avg_loss:.4f}")
    

plt.plot(train_losses)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Loss over epochs")
plt.legend()
plt.show()

model.eval()
all_preds, all_labels = [], []

with torch.no_grad():
    for xb, yb, lengths in test_dl:
        out = model(xb, lengths)
        preds = out.argmax(1)
        all_preds.extend(preds)
        all_labels.extend(yb)

print(classification_report(all_labels, all_preds, target_names=label2id.keys()))
print(confusion_matrix(all_labels, all_preds))


for i in range(3):
    text = test_df.iloc[i]['text']
    true_label = id2label[test_df.iloc[i]['label']]
    
    input_ids = torch.tensor([vocab(tokenize(text))])
    length = torch.tensor([input_ids.shape[1]])
    
    with torch.no_grad():
        pred_label_id = model(input_ids, length).argmax(1).item()
    
    print(f'Tweet: {text}')
    print(f'True class: {true_label} Predicted: {id2label[pred_label_id]}')
    print()'''
    pyperclip.copy(result)


def tweet_cat():
    import pyperclip
    result = '''import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


df = pd.read_csv('tweet_cat.csv')
df = df[['text', 'type']].dropna()

le = LabelEncoder()
df['label'] = le.fit_transform(df['type'])

train_df, temp_df = train_test_split(df, test_size=0.3, stratify=df['label'], random_state=42)
val_df, test_df = train_test_split(temp_df, test_size=0.5, stratify=temp_df['label'], random_state=42)



import torch
from torchtext.vocab import build_vocab_from_iterator
from torch.nn.utils.rnn import pad_sequence
from nltk.tokenize import wordpunct_tokenize
import re


def tokenize(text):
    return wordpunct_tokenize(text.lower())

vocab = build_vocab_from_iterator(map(tokenize, train_df['text']), specials=["<PAD>", "<UNK>"])
vocab.set_default_index(vocab["<UNK>"])

def encode(text):
    return torch.tensor(vocab(tokenize(text)), dtype=torch.long)

pad_idx = vocab["<PAD>"]
num_classes = len(df['label'].unique())


from torch.utils.data import DataLoader, Dataset

class TweetDataset(Dataset):
    def __init__(self, df):
        self.texts = df['text'].tolist()
        self.labels = df['label'].tolist()

    def __getitem__(self, idx):
        return encode(self.texts[idx]), torch.tensor(self.labels[idx], dtype=torch.long)

    def __len__(self):
        return len(self.labels)

def collate_batch(batch):
    texts, labels = zip(*batch)
    lengths = torch.tensor([len(x) for x in texts])
    padded = pad_sequence(texts, batch_first=True, padding_value=pad_idx)
    return padded, torch.stack(labels), lengths

train_dl = DataLoader(TweetDataset(train_df), batch_size=32, shuffle=True, collate_fn=collate_batch)
val_dl = DataLoader(TweetDataset(val_df), batch_size=32, collate_fn=collate_batch)
test_dl = DataLoader(TweetDataset(test_df), batch_size=32, collate_fn=collate_batch)


import torch.nn as nn

class TextRNN(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_size, num_classes):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.rnn = nn.GRU(embed_dim, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x, lengths):
        embedded = self.embed(x)
        packed = nn.utils.rnn.pack_padded_sequence(embedded, lengths.cpu(), batch_first=True, enforce_sorted=False)
        out, h = self.rnn(packed)
        return self.fc(h[-1])

    

from sklearn.metrics import f1_score

model = TextRNN(len(vocab), 100, 128, num_classes)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

best_val_f1 = 0
patience, patience_counter = 3, 0

for epoch in range(20):
    model.train()
    for xb, yb, lengths in train_dl:

        
        preds = model(xb, lengths)
        loss = criterion(preds, yb)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

    # Validation
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for xb, yb, lengths in val_dl:
            logits = model(xb, lengths)
            preds = logits.argmax(dim=1).cpu()
            y_true.extend(yb)
            y_pred.extend(preds)

    val_f1 = f1_score(y_true, y_pred, average='macro')
    print(f"Epoch {epoch+1}: val F1 = {val_f1:.4f}")

    if val_f1 > best_val_f1:
        best_val_f1 = val_f1
        patience_counter = 0
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print("Early stopping.")
            break


            
from sklearn.metrics import classification_report

#выведем f1 через classification report
model.eval()
y_true, y_pred = [], []
with torch.no_grad():
    for xb, yb, lengths in test_dl:
        logits = model(xb, lengths)
        preds = logits.argmax(dim=1).cpu()
        y_true.extend(yb)
        y_pred.extend(preds)

print(classification_report(y_true, y_pred, target_names=le.classes_))  


for i in range(3):
    text = test_df.iloc[i]['text']
    label = test_df.iloc[i]['type']
    input_ids = encode(text).unsqueeze(0)
    length = torch.tensor([input_ids.shape[1]])
    pred = model(input_ids, length).argmax(dim=1).item()
    pred_label = le.inverse_transform([pred])[0]
    print(f"Text: {text}")
    print(f"True label: {label}  Predicted: {pred_label}")
    print()
'''
    pyperclip.copy(result)
    
    
def quotes():
    import pyperclip
    result = '''import json
from sklearn.model_selection import train_test_split
import re

with open("quotes.json", "r") as f:
    data = json.load(f)

data = list(set([re.sub(r'[^A-Za-z ]', '',elem["Quote"]) for elem in data]))
text = "\n".join(data)
chars = sorted(set(text))
vocab_size = len(chars)

stoi = {ch: i for i, ch in enumerate(chars)}
itos = {i: ch for ch, i in stoi.items()}

def encode(s):
    return [stoi[c] for c in s]

def decode(ids):
    return ''.join(itos[i] for i in ids)

data_encoded = encode(text)



import torch

block_size = 128
batch_size = 64
train_ratio = 0.9

split_idx = int(len(data_encoded) * train_ratio)
train_data = data_encoded[:split_idx]
test_data = data_encoded[split_idx:]

def get_batch(data):
    ix = torch.randint(0, len(data) - block_size, (batch_size,))
    x = torch.stack([torch.tensor(data[i:i+block_size]) for i in ix])
    y = torch.stack([torch.tensor(data[i+1:i+block_size+1]) for i in ix])
    return x, y


import torch.nn as nn

class CharRNN(nn.Module):
    def __init__(self, vocab_size, embedding_dim=64, hidden_size=128):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embedding_dim)
        self.rnn = nn.RNN(embedding_dim, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, vocab_size)

    def forward(self, x, hidden=None):
        x = self.embed(x)
        out, hidden = self.rnn(x, hidden)
        logits = self.fc(out)
        return logits, hidden



import torch.nn.functional as F
import matplotlib.pyplot as plt


model = CharRNN(vocab_size)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

n_epochs = 500
losses = []

for epoch in range(n_epochs):
    model.train()
    x, y = get_batch(train_data)

    optimizer.zero_grad()
    logits, _ = model(x)
    loss = F.cross_entropy(logits.view(-1, vocab_size), y.view(-1))
    loss.backward()
    optimizer.step()

    losses.append(loss.item())
    print(f"Epoch {epoch+1} Train loss {round(loss.item(),4)}")
    
    
plt.plot(losses)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Training loss")
plt.show()


def test_acc(model, data):
    model.eval()
    x, y = get_batch(data)

    with torch.no_grad():
        logits, _ = model(x)
        preds = torch.argmax(logits, dim=-1)
        acc = (preds == y).float().mean().item()
    return acc

acc = test_acc(model, test_data)
print(f"Test ccuracy: {round(acc, 4)}")



def generate_quote(model, start_text, max_new_tokens=25):
    model.eval()
    input_ids = torch.tensor([encode(start_text)], dtype=torch.long)
    output = list(input_ids[0].numpy())

    for i in range(max_new_tokens):
        logits, hidden = model(input_ids)
        next_token_logits = logits[:, -1, :]
        probs = F.softmax(next_token_logits, dim=-1)
        next_id = torch.multinomial(probs, num_samples=1).item()

        output.append(next_id)
        input_ids = torch.tensor([[next_id]], dtype=torch.long)

    return decode(output)


print(generate_quote(model, start_text="I want to "))
print(generate_quote(model, start_text="A good "))'''
    pyperclip.copy(result)
    

def pos():
    import pyperclip
    result = '''import torch
import torch.nn as nn
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from nltk.tokenize import wordpunct_tokenize

with open('pos.json', 'r') as f:
    data = json.load(f)  
for sample in data:
    sample["tokens"] = wordpunct_tokenize(sample["sentence"])

word2idx = {"<PAD>": 0, "<UNK>": 1}
tag2idx = {"<PAD>": 0}
cleaned_data = []
for sample in data:
      if len(sample['tokens']) == len(sample['tags']): #если есть какие-то ошибки в данных и длины не совпадают - то отбрасываем эти примеры
        cleaned_data.append(sample)
        for token in sample['tokens']:
            if token not in word2idx:
                word2idx[token] = len(word2idx)
        for tag in sample['tags']:
            if tag not in tag2idx:
                tag2idx[tag] = len(tag2idx)




from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset

class PosDataset(Dataset):
    def __init__(self, data, word2idx, tag2idx):
        self.data = data
        self.word2idx = word2idx
        self.tag2idx = tag2idx

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        tokens = [self.word2idx.get(t, 1) for t in self.data[idx]['tokens']]
        tags = [self.tag2idx[t] for t in self.data[idx]['tags']]
        return torch.tensor(tokens), torch.tensor(tags)

def collate_fn(batch):
    tokens, tags = zip(*batch)
    tokens_padded = pad_sequence(tokens, batch_first=True, padding_value=word2idx["<PAD>"])
    tags_padded = pad_sequence(tags, batch_first=True, padding_value=tag2idx["<PAD>"])
    return tokens_padded, tags_padded


train_data, test_data = train_test_split(cleaned_data, test_size=0.2, random_state=42)

train_dataset = PosDataset(train_data, word2idx, tag2idx)
test_dataset = PosDataset(test_data, word2idx, tag2idx)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, collate_fn=collate_fn)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)


class POSModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, tagset_size):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=word2idx["<PAD>"])
        self.rnn = nn.RNN(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, tagset_size)

    def forward(self, x):
        x = self.embedding(x)            
        x, _ = self.rnn(x)               
        return self.fc(x)          


model = POSModel(len(word2idx), 100, 128, len(tag2idx))
optimizer = torch.optim.Adam(model.parameters())
criterion = nn.CrossEntropyLoss(ignore_index=tag2idx["<PAD>"])
loss_history = []

for epoch in range(10):
    model.train()
    total_loss = 0
    for tokens, tags in train_loader:
        outputs = model(tokens)  
        outputs = outputs.view(-1, outputs.shape[-1]) 
        tags = tags.view(-1) 
        
        loss = criterion(outputs.view(-1, len(tag2idx)), tags.view(-1))
        total_loss += loss.item()

        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

    avg_loss = total_loss / len(train_loader)
    loss_history.append(avg_loss)

    print(f"Epoch {epoch+1}, Train Loss: {avg_loss:.4f}")



import matplotlib.pyplot as plt

plt.plot(loss_history)
plt.ylabel('loss value')
plt.xlabel('epoch')
plt.title('Loss over epochs')


true_vals = []
preds_lst = []
true_tokens = []

model.eval()
with torch.no_grad():
      for tokens, tags in test_loader:
        outputs = model(tokens)
        preds = torch.argmax(outputs, dim=2)

        for i in range(tokens.size(0)):  
                true_len = (tokens[i] != 0).sum().item()  # не считаем паддинг 
                true_vals.extend(tags[i][:true_len].tolist())
                preds_lst.extend(preds[i][:true_len].tolist())
                true_tokens.extend(tokens[i][:true_len].tolist())


  

from sklearn.metrics import confusion_matrix, classification_report

tag2idx_inv = {v:k for k,v in tag2idx.items()}
word2idx_inv = {v:k for k,v in word2idx.items()}
true_vals = [tag2idx_inv[elem] for elem in true_vals]
preds_lst = [tag2idx_inv[elem] for elem in preds_lst]
print(classification_report(true_vals, preds_lst))
print(confusion_matrix(true_vals, preds_lst))
pd.DataFrame({'text': ' '.join([word2idx_inv[elem] for elem in test_dataset[1][0].tolist()]), 'prediction': ' '.join(preds_lst[:len(test_dataset[1][0].tolist())])}, index=[0])'''
    
    pyperclip.copy(result)


    
    
    
    
    
    
def cnn():
    print('''data_dir = "unpacked_eng_handwritten/eng_handwritten"

# Предобработка изображений
transform = transforms.Compose([
    transforms.Resize((300,300)),
    transforms.ToTensor()
])

# Загрузка данных
full_dataset = ImageFolder(data_dir, transform=transform)

#train_size = int(0.7 * len(full_dataset))
#test_size = len(full_dataset) - train_size
#train_dataset, test_dataset = torch.utils.data.random_split(full_dataset, [train_size, test_size])

images, labels = [], []
for img, lbl in full_dataset:
    images.append(img)
    labels.append(lbl)
    
X = torch.stack(images)
y = torch.tensor(labels)

X_train, X_test, y_train, y_test = train_test_split(X,y, test_size = 0.3, random_state=42)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

train_loader = DataLoader(train_dataset, batch_size = 64, shuffle = True)
test_loader = DataLoader(test_dataset, batch_size = 64, shuffle = True)


class CNN(nn.Module):
    def __init__(self, n_classes=26 ):
        super(CNN, self).__init__()
        
        self.conv1 = nn.Sequential(nn.Conv2d(3, 64, kernel_size = 3, padding = 1, bias=False),
                                   nn.ReLU(),
                                   nn.MaxPool2d(kernel_size = 2, stride = 2) #300x300 -> 150X150
                                  )
        self.conv2 = nn.Sequential(nn.Conv2d(64, 128, kernel_size = 3, padding = 1, bias=False),
                                   nn.ReLU(),
                                   nn.MaxPool2d(kernel_size = 5, stride = 5) #150x150 -> 30X30
                                  )
        self.conv3 = nn.Sequential(nn.Conv2d(128, 256, kernel_size = 3, padding = 1,bias=False),
                                   nn.ReLU(),
                                   nn.MaxPool2d(kernel_size = 2, stride = 2) # 30X30 -> 15x15
                                  )
        self.fc = nn.Sequential(nn.Flatten(),
                               nn.Linear(256*15*15, 32),
                               nn.ReLU(),
                               nn.Linear(32, 64),
                               nn.ReLU(),
                               nn.Linear(64, n_classes)
                               )

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.fc(x)
        return x
    
    
batch_size = 64
num_epochs = 10
print_every = 1
num_classes = len(full_dataset.classes)


model = CNN()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr = 0.01)


for epoch in range(num_epochs):
    epoch_loss = 0
    epoch_loss_test = 0
    model.train()
    for batch_X, batch_y in train_loader:
        y_pred = model(batch_X)
        
        loss = criterion(y_pred, batch_y.long())
        epoch_loss+=loss.item()
        
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        
    for batch_X, batch_y in test_loader:
        y_pred = model(batch_X)
        
        loss = criterion(y_pred, batch_y.long())
        epoch_loss_test+=loss.item()
        
    epoch_loss /= len(train_dataset)
    epoch_loss_test /= len(test_dataset)
    
    if (epoch+1) % print_every == 0:
        print(f'Epoch {epoch+1}/{num_epochs}, Loss: {epoch_loss:.4f}, ...')''')
def bike():
    print('''X = data.drop(columns = ['cnt'])
y = data['cnt']

#categorical_cols = X.select_dtypes(include='category').columns
#numerical_cols = X.select_dtypes(include='number').columns
categorical_cols = ['workingday', 'weathersit', 'holiday']
numerical_cols = ['season', 'yr', 'mnth', 'hr', 'weekday', 'temp', 'atemp', 'hum', 'windspeed', 'instant']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(), categorical_cols)
    ])

X_processed = preprocessor.fit_transform(X.drop(columns=['dteday']))
#y = np.array(y)


y_scaler = StandardScaler()

y = y_scaler.fit_transform(y.values.reshape(-1, 1))
y = np.array(y)

X_train, X_test, y_train, y_test = train_test_split(X_processed, y, test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

class Model(nn.Module):
    def __init__(self, n_input=18):
        super(Model, self).__init__()
        
        self.fc1 = nn.Linear(n_input,128)
        self.fc2 = nn.Linear(128,256)
        self.fc3 = nn.Linear(256,1)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout()
        
    def forward(self, x):
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.dropout(self.relu(self.fc2(x)))
        x = self.fc3(x)
        return x

batch_size = 64
epochs = 100
print_every = 10


model = Model()
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)

lst_test = []
lst_train = []

for epoch in range(epochs):
    epoch_loss = 0
    epoch_loss_test = 0
    model.train()
    for batch_X, batch_y in train_loader:
        #print(batch_X.shape)
        y_pred = model(batch_X)
        loss = criterion(y_pred, batch_y)
        epoch_loss += loss.item()
        
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        
    model.eval()
    for batch_X, batch_y in test_loader:
        y_pred = model(batch_X)
        loss = criterion(y_pred, batch_y)
        epoch_loss_test += loss.item()
        
    epoch_loss /= len(train_dataset)
    epoch_loss_test /= len(test_dataset)
    lst_train.append(epoch_loss)
    lst_test.append(epoch_loss_test)
    
    if (epoch+1) % print_every == 0:
        print(f'Epoch {epoch+1}/{epochs}, Loss: {epoch_loss:.4f}, Test Loss: {epoch_loss_test:.4f}')''')
    
def cl():
    print('''from sklearn.utils.class_weight import compute_class_weight
import numpy as np
from sklearn.preprocessing import LabelEncoder
X = data.drop(columns=['deposit'])
y = data['deposit']

categorical_cols = X.select_dtypes(include = ['object']).columns
numerical_cols = X.select_dtypes(include = ['number']).columns

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(), categorical_cols)
    ])


X_processed = preprocessor.fit_transform(X)#.toarray()
lb = LabelEncoder()
y = lb.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(X_processed, y, test_size=0.2, stratify=y, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

classes = np.unique(y)

# Compute class weights
class_weights = compute_class_weight(class_weight='balanced', classes=classes, y=y)

for i, weight in enumerate(class_weights):
    print(f"Class {classes[i]}: {weight}")

class Model(nn.Module):
    def __init__(self, input_size, output_size):
        super(Model, self).__init__()
        self.fc1 = nn.Linear(input_size, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 2) 
        
        self.relu = nn.ReLU()
        

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        
        return x

batch_size = 64
epochs = 20
print_every = 2
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)
plot_list_test = []
plot_list_train = []

for optimizer in [optim.Adam]:
  print('-'*20)
  print(f'Optimizer: {str(optimizer).split(".")[-1]}')
  model = Model(X_processed.shape[1], 2)
  criterion = nn.CrossEntropyLoss(weight = torch.tensor(class_weights, dtype=torch.float32))
  optimizer = optimizer(model.parameters(), lr=0.0001)
  train_losses = []
  test_losses = []
  pred_metrics = []
  true_metrics = []

  

  for epoch in range(epochs):
      epoch_loss = 0
      test_loss = 0
      accuracy = 0
      
      model.train()
      for batch_X, batch_y in train_loader:
          pred = model(batch_X).squeeze()
          loss = criterion(pred, batch_y.long())
          epoch_loss +=loss.item()
          loss.backward()
          optimizer.step()
          optimizer.zero_grad()

      model.eval()
      with torch.no_grad():
        for test_X, test_y in test_loader:
          pred_test = model(test_X).squeeze()
          loss = criterion(pred_test, test_y.long())
          test_loss += loss.item()
          accuracy += accuracy_score(torch.argmax(pred_test, dim=1), test_y)
          

      epoch_loss /= len(train_loader)
      test_loss /= len(test_loader)
      accuracy /= len(test_loader)

      test_losses.append(test_loss)
      train_losses.append(epoch_loss)

      if (epoch+1) % print_every == 0:
          print(f'Epoch {epoch+1}/{epochs}, Train Loss: {epoch_loss:.4f}, Test Loss: {test_loss:.4f}, Accuracy Loss: {accuracy:.4f}')
  plot_list_test.append(test_losses)
  plot_list_train.append(train_losses)
  


plt.figure(figsize=(10, 5))

plt.plot(plot_list_train[0], label='Adam')

plt.title('Train')
plt.legend()

plt.figure(figsize=(10, 5))

plt.plot(plot_list_test[0], label='Adam')

plt.title('Test')
plt.legend()''')    

def re():
    print('''X = data.drop(columns=['Silver_T-22',
        'Platinum_T-22', 'Palladium_T-22', 'Gold_T-22'])
y = data[['Silver_T-22',
        'Platinum_T-22', 'Palladium_T-22', 'Gold_T-22']]

categorical_cols = X.select_dtypes(include = ['object']).columns
numerical_cols = X.select_dtypes(include = ['number']).columns

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(), categorical_cols)
    ])

X_processed = preprocessor.fit_transform(X)#.toarray()
y = np.array(y)

X_train, X_test, y_train, y_test = train_test_split(X_processed, y, test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

class Model(nn.Module):
    def __init__(self, input_size, output_size=4):
        super(Model, self).__init__()
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64,128)
        self.fc3 = nn.Linear(128, output_size)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return x

batch_size = 64
epochs = 100
print_every = 10
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
plot_list_test = []
plot_list_train = []

for optimizer in [optim.SGD, optim.Adam, optim.AdamW]:
  print('-'*20)
  print(f'Optimizer: {str(optimizer).split(".")[-1]}')
  model = Model(X.shape[1])
  criterion = nn.MSELoss()
  optimizer = optimizer(model.parameters(), lr=0.001)
  train_losses = []
  test_losses = []
  pred_metrics = []
  true_metrics = []

  

  for epoch in range(epochs):
      epoch_loss = 0
      test_loss = 0
      mse, mae,r2_value = 0,0,0
      model.train()
      for batch_X, batch_y in train_loader:
          pred = model(batch_X).squeeze()
          loss = criterion(pred, batch_y)
          epoch_loss +=loss.item()
          loss.backward()
          optimizer.step()
          optimizer.zero_grad()

      model.eval()
      with torch.no_grad():
        for test_X, test_y in test_loader:
          pred_test = model(test_X).squeeze()
          loss = criterion(pred_test, test_y)
          test_loss += loss.item()
          #print(pred_test.shape, test_y.shape)
          mse += mean_squared_error(pred_test, test_y)
          mae += mean_absolute_error(pred_test, test_y)
          r2_value += r2_score(pred_test.numpy(), test_y.numpy())
          

      epoch_loss /= len(train_loader)
      test_loss /= len(test_loader)
      mse /= len(test_loader)
      mae /= len(test_loader)
      r2_value /= len(test_loader)
      test_losses.append(test_loss)
      train_losses.append(epoch_loss)

      if (epoch+1) % print_every == 0:
          print(f'Epoch {epoch+1}/{epochs}, Train Loss: {epoch_loss:.4f}, Test Loss: {test_loss:.4f}')
  plot_list_test.append(test_losses)
  plot_list_train.append(train_losses)
  print(f'MSE: {mse}, MAE: {mae}, R2: {r2_value}')


plt.figure(figsize=(10, 5))
plt.plot(plot_list_train[0], label='SGD')
plt.plot(plot_list_train[1], label='Adam')
plt.plot(plot_list_train[2], label='AdamW')
plt.title('Train')
plt.legend()

plt.figure(figsize=(10, 5))
plt.plot(plot_list_test[0], label='SGD')
plt.plot(plot_list_test[1], label='Adam')
plt.plot(plot_list_test[2], label='AdamW')
plt.title('Test')
plt.legend()''')
    
def tobd():
    print('''
Вопросы к экзамену ТОБД

1.Большие данные – определение и причины возникновения задач обработки больших данных

Big Data — это крупные массивы разнообразной информации и стек специальных технологий для работы с ней. Термин применяется к таким объемам данных, с которыми пользовательский компьютер и офисные программы не справятся. С помощью анализа больших данных бизнес может получить возможность принимать решения по развитию продукта и завоевывать конкурентное преимущество.
Области применения Big Data разнообразны. Технология применяется там, где можно собрать и обработать нужные массивы информации.
​​
Причины возникновения задач обработки больших данных
Рост объема данных:
Расширение интернета и использование онлайн-платформ, социальных сетей, электронной коммерции.
Увеличение скорости генерации данных:
Технологии в реальном времени, например, потоки данных с датчиков или событий в финансовых системах.
Разнообразие источников данных:
Требования к анализу и прогнозированию:
Необходимость извлекать ценную информацию из данных для принятия бизнес-решений.
Развитие машинного обучения и искусственного интеллекта, которые требуют больших объемов данных для обучения.
Развитие технологий:
Таким образом, задачи обработки больших данных возникли как следствие стремительного роста объемов информации, ее разнообразия и скорости генерации, что делает традиционные методы анализа неэффективными.
(из файла)
Большие данные — это разнообразные данные, которые поступают с постоянно растущей скоростью и объем которых постоянно растет. Таким образом, три основных свойства больших данных — разнообразие, высокая скорость поступления и большой объем. 
Причины возникновения задач обработки больших данных следующие: 
• Объемы данных 
Хранилища достигли невероятных размеров. Только за 2009 и 2010 годы в базах было сохранено больше информации, чем за всю предыдущую историю человечества. 
• Связанность данных 
Информация перестала быть изолированной. Каждый кусочек знаний как-то связан с данными в других хранилищах информации.
 • Обработка данных при помощи независимых сервисов 
Обработка информации происходит параллельно во множестве изолированных систем, зачастую принадлежащих разным владельцам. Все чаще поставщики данных не участвуют в интеграции систем, а предоставляют их «как есть». 
• Слабая структурированность данных
 Пример: описание товара в магазине. Если раньше было достаточно 5–6 полей, чтобы описать товар, то теперь их бывает до нескольких десятков (причем различных для разных товаров). Стало очень сложно поддерживать структуру базы данных.
2.Специфика современного аппаратного обеспечения для обработки больших данных и проблема масштабируемости параллельных вычислений
Специфика современного аппаратного обеспечения для обработки больших данных
Современное аппаратное обеспечение для обработки больших данных отличается высокой производительностью, возможностью работы с большими объемами данных и поддержкой параллельных вычислений. Основные особенности:
Распределенные системы:
Используются кластеры серверов, объединенных в единую сеть, для выполнения задач обработки больших данных. Пример – Hadoop Distributed File System (HDFS).
Каждый узел в кластере обрабатывает часть данных, обеспечивая масштабируемость и отказоустойчивость.
Облачные платформы:
Популярны облачные решения (AWS, Google Cloud, Microsoft Azure), которые предоставляют масштабируемые вычислительные ресурсы и хранение.
Облака позволяют динамически изменять объем ресурсов в зависимости от потребностей.
Высокоскоростные хранилища данных:
Используются SSD-диски вместо традиционных HDD для увеличения скорости чтения и записи.
Графические процессоры (GPU):
GPU отлично подходят для задач, требующих большого числа параллельных вычислений, например, для обработки изображений, обучения моделей машинного обучения и анализа данных.
Специализированные процессоры:
TPU (Tensor Processing Unit) – процессоры от Google, оптимизированные для задач машинного обучения.
Проблема масштабируемости параллельных вычислений
Масштабируемость параллельных вычислений – это возможность эффективно увеличивать производительность системы с ростом числа процессоров или узлов. Однако в этой области существует ряд проблем:
Распределённые вычисления требуют координации между процессорами. Чем больше узлов, тем больше времени уходит на синхронизацию и передачу данных. Это снижает эффективность параллельной обработки.
С ростом числа узлов вероятность отказа одного из них увеличивается. Система должна быть устойчивой к сбоям, что добавляет сложности в ее разработку.
Параллельные вычисления требуют минимизации объемов передачи данных между узлами. Если данные распределены неэффективно, это приводит к задержкам.
(из файла)
Специфика современного аппаратного обеспечения для обработки больших данных:
Горизонтальная масштабируемость - Для Больших данных необходима настоящая масштабируемость приложений.
 Отказоустойчивость - Методы работы с большими данными должны учитывать возможность сбоев и переживать их без каких-либо значимых последствий. 
Локальность данных - по возможности обрабатываем данные на той же машине, на которой их храним. 
Проблема масштабируемости параллельных вычислений хорошо описана законом Амдала – “ В случае, когда задача разделяется на несколько частей, суммарное время её выполнения на параллельной системе не может быть меньше времени выполнения самого длинного фрагмента”. Согласно этому закону, ускорение выполнения программы за счет распараллеливания её инструкций на множестве вычислителей ограничено временем, необходимым для выполнения ее последовательных инструкций.

3.Выбор типичных средств обработки данных, адекватных различным объемам данных; принцип обработки данных на базе операций map / filter / reduce

Обработка больших данных может быть произведена с помощью распределенных вычислений (map-reduce). MapReduce — это фреймворк для вычисления некоторых наборов распределенных задач с использованием большого количества компьютеров (называемых «нодами»), образующих кластер. Работа MapReduce состоит из двух шагов: Map и Reduce, названных так по аналогии с одноименными функциями высшего порядка, map и reduce. Для обработки не больших данных можно использовать pandas и другие методы. 
Принцип обработки данных на базе операций map / filter / reduce 
На Map-шаге происходит предварительная обработка входных данных. Для этого один из компьютеров (называемый главным узлом — master node) получает входные данные задачи, разделяет их на части и передает другим компьютерам (рабочим узлам — worker node) для предварительной обработки. На Reduce-шаге происходит свёртка предварительно обработанных данных. Главный узел получает ответы от рабочих узлов и на их основе формирует результат — решение задачи, которая изначально формулировалась.


4.Многопроцессорные архитектуры с общей и разделяемой памятью – специфика и сравнение

Многопроцессорные архитектуры с общей памятью имеет следующую специфику: 
● несколько процессоров работают независимо, но совместно используют общую память 
● изменения в памяти осуществляемые одним процессором видны всем другим процессорам 
Многопроцессорные архитектуры с разделяемой памятью имеет следующую специфику:
 ● несколько процессоров работают с собственной памятью, недоступной напрямую для других процессоров (отсутствует общая адресация памяти)
 ● обмен данными между процессорами производится через коммуникационную сеть и явно определяется исполняемой программой



5.Подходы к декомпозиции крупных вычислительных задач на подзадачи для параллельного исполнения

Подходы к декомпозиции задач на параллелизуемые подзадачи: 
1.) Функциональная декомпозиция (Task/Functional decomposition) 
 Распределение вычислений по подзадачам
 2.) Декомпозиция по данным 
Распределение данных по подзадачам o Высокая масштабируемость (многие тысячи ядер) 
Возможность использовать недорогие массовые компоненты (CPU, RAM, сети) 
3.) Геометрическая декомпозиция o Данные задачи разбиваются на области (желательно равного размера) по "геометрическому" принципу (например n-мерная решетка с регулярным шагом) 
С каждой областью данных ассоциируется свой обработчик, обычно применяется стандартный алгоритм обработки и при необходимости, обмениваться данными с обработчиками, работающими с соседними областями.
 4.) Рекурсивный параллелизм  
Операции Split и Merge могут стать узким местом т. к. выполняются последовательно. 
Задания порождаются динамически (балансировка загрузки потоков) 
Степень параллелизма изменяется в ходе выполнения алгоритма

6.Модели параллельного программирования и их сочетаемость с архитектурами параллельных вычислительных систем

Разделяемая память (shared memory): 
● Аналогия - доска объявлений 
● Подзадачи используют общее адресное пространство (оперативной памяти) 
● Подзадачи взаимодействуют асинхронно читая и записывая информацию в общем пространстве 
● Реализация: многопоточные приложения, OpenMP 
Передача сообщений (message passing): 
● Аналогия – отправка писем с явным указанием отправителя и получателя 
● Каждая подзадача работает с собственными локальными данными 
● Подзадачи взаимодействуют за счет обмена сообщениями 
● Реализация: MPI (message passing interface) 
Параллельная обработка данных (data parallelization): 
● Строго описанные глобальные операции над данными 
● (Может обозначаться как чрезвычайная параллельность (embarrassingly parallel) – очень хорошо распараллеливаемые вычисления) 
● Обычно данные равномерно разделяются по подзадачам 
● Подзадачи выполняются как набор независимых операций 
● Реализация может быть сделана как с помощью разделяемой памяти, так и с помощью передачи сообщений 
Все эти модели параллельного программирования могут быть реализованы на архитектуре с разделяемой памятью

 7.Профилирование реализации алгоритмов на Python, принципы решения задачи оптимизации производительности алгоритма

Профилирование – это сбор характеристик работы программы, таких как: 
● время выполнения отдельных фрагментов (например, функций)
● число верно предсказанных условных переходов 
● число кэш-промахов 
●объем используемой оперативной памяти

 Инструмент, используемый для анализа работы, называют профайлером (profiler). Обычно профилирование выполняется в процессе оптимизации программы. 

Магические функции IPython для профилирования:
 ● %time - длительность выполнения отдельного оператора; 
● %timeit - длительность выполнения отдельного оператора при неоднократном повторе (может использоваться для обеспечения большей точности оценки); 
● %prun - выполнение кода с использованием профилировщика; 
● %lprun - пошаговое выполнение кода с применением профилировщика;
 ●%memit - оценка использования оперативной памяти для отдельного оператора; ●%mprun - пошаговое выполнение кода с применением профилировщика памяти. 

Принципы решения задачи оптимизации производительности алгоритма следующие: 
● Компромиссы. Оптимизация в основном фокусируется на одиночном или повторном времени выполнения, использовании памяти, дискового пространства, пропускной способности или некотором другом ресурсе. Это обычно требует компромиссов — один параметр оптимизируется за счет других. 
● Узкие места. Для оптимизации требуется найти узкое место: критическую часть кода, которая является основным потребителем необходимого ресурса. Утечка ресурсов (памяти, дескрипторов и т. д.) также может привести к падению скорости выполнения программы. Для поиска таких утечек используются специальные отладочные инструменты, а для обнаружения узких мест применяются программы — профайлеры.

8.Проблема Global Interpreter Lock в Python и способы обхода ее ограничений

Global Interpreter Lock – способ синхронизации потоков используемый в рефернсной реализации Python (CPython) и в реализациях некоторых других интерпретируемых языков программирования. 
● Интерпретатор CPython НЕ является потоково-безопасным (Потоковая безопасность – специфика кода (например функций или библиотек), позволяющая использовать его из нескольких потоков одновременно) т.к. некоторые ключевые структуры данных могут быть одновременно доступны только одному потоку. 
● GIL является самым простым и быстрым при исполнении однопоточных приложений способом обеспечения потоковой безопасности при одновременном обращении разных потоков к одним и тем же участкам памяти. 
● Наличие GIL не является требованием языка программирования Python, а только спецификой реализации самого популярного интерпретатора CPython, существуют другие интерпретаторы Python не имеющие GIL. 

Для обхода проблемы GIL для реализации параллельных вычислений в Python вместо многопоточного подхода с разделяемой памятью используется более тяжеловесная конструкция: 
● множество процессов, в каждом из которых работает собственный интерпретатор с собственным GIL и имеется собственная копия данных и кода 
обмен данными между процессами обычно производится не через разделяемую память (это иногда возможно, но чревато ошибками), а через передачу данных и кода с помощью сериализации по сути, это вариация на тему модели параллельного программирования на основе передачи сообщений (реализуемой в т.ч. при вычислении на компьютере с разделяемой памятью) 

9.Модуль multiprocessing – назначение и основные возможности, API multiprocessing.Pool

multiprocessing – обеспечение параллельных вычислений на основе процессов и поддержка соответствующей инфраструктуры. Модуль multiprocessing включен в стандартную библиотеку Python.
Позволяет избегать ограничения GIL для параллельных вычислений
Позволяет избегать использования примитивов для синхронизации (модель передачи сообщений)
Включает абстракции с интерфейсом, похожим на threading.Thread
Класс Process
Создание процессов: Модуль multiprocessing предоставляет класс Process, который можно использовать для создания нового процесса. Каждый процесс имеет свое собственное исполняемое пространство и может выполнять задачи независимо от других процессов.


Обмен данными между процессами: Модуль multiprocessing предоставляет различные способы обмена данными между процессами, такие как через разделяемую память (shared memory), очереди (queues) и конвейеры (pipelines).
Класс Pool
Более простой способ поддерживать упорядоченный список результатов - использовать функции Pool.apply и Pool.map, которые мы обсудим в следующем разделе.
Другой, более удобный подход для простых задач параллельной обработки - это класс Pool. Особенно интересны четыре метода:
Pool.apply
Pool.map
Pool.apply_async
Pool.map_async
close(): Завершает пул процессов и больше не принимает новые задачи для выполнения.
join(): Блокирует вызывающий процесс до завершения выполнения всех задач в пуле.
Методы Pool.apply и Pool.map эквивалентны встроенным методам apply и map.
Прежде чем мы перейдем к асинхронным вариантам методов Pool, давайте рассмотрим простой пример с использованием Pool.apply и Pool.map. Здесь мы установим количество процессов на 4, что означает, что класс Pool разрешит запускать только 4 процесса одновременно.


Pool.map и Pool.apply блокируют основную программу до тех пор, пока все процессы не будут завершены, что очень полезно, если мы хотим получить результаты в определенном порядке для определенных приложений (потребителей).
Напротив, варианты async стартуют все процессы сразу и получат результаты, как только они будут готовы. Еще одно отличие состоит в том, что нам нужно использовать метод get после вызова apply_async(), чтобы получить возвращаемые значения завершенных процессов.
10.Различия между потоками и процессами, различие между различными планировщиками в Dask




Планировщик задач исполняет задачи из графа зависимостей задач с учетом зависимостей и по возможности задачи не зависимые по данным исполняет параллельно. 

Имеется несколько реализаций планировщика, подходящих для различных архитектур (простота замены планировщика обеспечивает легкость адаптации к различным уровням масштабирования и архитектурам) 

После того, как мы создадим график задач, мы используем планировщик для его запуска. В настоящее время Dask реализует несколько различных планировщиков: 

● dask.threaded.get: планировщик, поддерживаемый пулом потоков 
● dask.multiprocessing.get: планировщик, поддерживаемый службой пула процессов 
● dask.get: синхронный планировщик, подходящий для распределенной отладки 
● distributed.Client.get: распределенный планировщик для выполнения графиков на нескольких машинах.Это живет во внешнем распределенном проекте. 

В коллекции есть планировщик по умолчанию:

dask.array и dask.dataframe по умолчанию используют многопоточный планировщик
dask.bag по умолчанию использует многопроцессорный планировщик. В большинстве случаев хорошим выбором являются настройки по умолчанию. 

11.Граф зависимосте й задач – суть структуры данных, ее построение и использование в Dask

Граф зависимостей задач.
Распространенным подходом к параллельным вычислениям является планирование задач.
При этом подходе программа разбивается на большое количество задач (tasks) среднего размера (блоков последовательных вычислений, обычно представляющих собой вызов функции для некоторого набора данных).
Эти задачи представляются в виде вершин ориентированного графа зависимостей задач (task graph),
с дугами отражающими зависимость одной задачи от данных, рассчитанных другой задачей.
Этот подход позволяет программисту явно определить участки кода, подлежащие распараллеливанию.
import numpy as np
import dask




#задачи
def inc(i):
    return i + 1


def add(i, j):
    return i + j


#вычисления
a = 1
x = 10


b = inc(a)
y = inc(x)


z = add(b, y)


#задание зависимости
dsk = {
    'a': 1,
    'x': 10,
    'b': (inc, 'a'),
    'y': (inc, 'x'),
    'z': (add, 'b', 'y')
}


import dask.threaded as dthr
dthr.get(dsk, 'z')


12.Три ключевых структуры данных Dask: их специфика и принцип выбора структуры данных при решении задач

Ключевые структуры данных Dask: 
1. Array (аналог структуры ndarray) 
2. Bag (прямого аналога структуры нет, но в какой-то степени это аналог списка) 
3. DataFrame (аналог структуры – pandas) 

Dask Array 
● Эта техника позволяет: 
оперировать массивами, большими чем оперативная память использовать все доступные ядра. 
● Координация задач, возникающих при исполнении блочной формы алгоритмов, осуществляется при помощи реализованного в Dask графа зависимостей задач. 

Dask Array поддерживает большинство интерфейсов NumPy, в частности: 
● Арифметические операции и скалярные функции: +, *, exp, log, ... 
● Агрегирующие функции (в т.ч. вдоль осей): sum(), mean(), std(), sum(axis=0), ... 
● Умножение матриц, свертка тензоров: tensordot 
● Получение срезов: x[:100, 500:100:-2] 
● Прихотливое индексирование вдоль одной оси: x[:, [10, 1, 5]] ● Работу с протоколами массивов __array__ и __array_ufunc__ 
● Некоторые операции линейной алгебры: svd, qr, solve, solve_triangular, lstsq 

Мотивация: Dask DataFrame целесообразно использовать для анализа и обработки данных: 
● имеющих табличный формат 
● и имеющих размер больший, чем оперативная память. В частности, если операции с вашим массивом данных в Pandas приводят к ошибкам MemoryError, то использование Dask DataFrame позволяет обойти эту проблему. 

Издержки: 
● Операции Dask DataFrame используют вызовы функций pandas. 
● Обычно они выполняются с той же скоростью что и операции в pandas. 
● Небольшие дополнительные накладные расходы добавляет инфраструктура Dask (около 1 мс. на задачу, при выполнении достаточно крупных задач этими издержками можно пренебречь).

13.Dask.Array – структура данных, специфика реализации и применения, процедура создания

Dask Array 
● Dask Array реализует подмножество интерфейса NumPy ndarray, используя алгоритмы в блочной форме 
Большой массив разбивается на относительно небольшие блоки которые обрабатываются независимо 
● Эта техника позволяет: 
оперировать массивами, большими чем оперативная память
 использовать все доступные ядра. 
● Координация задач, возникающих при исполнении блочной формы алгоритмов, осуществляется при помощи реализованного в Dask графа зависимостей задач. 

Реализация Dask Array: 
● Dask Array представляет собой сетку из массивов NumPy, обработку которых он организует порождая для каждой операции со всем массивом множество операций с массивами NumPy. 
● Массивы NumPy могут: 
находится в оперативной в памяти 
находится в распределенной оперативной в памяти кластера (т.е. хранится на узлах кластера) 
находится на диске (по крайней мере часть времени вычислений)


Пример строки реализации, где «data_set» является переменной, хранящей в себе набор неких числовых данных. 


Процедура создания Dask.Array:

Импорт библиотеки: Начните с импорта модуля dask.array из библиотеки Dask.
import dask.array as da

Создание массива данных: Используйте функцию da.from_array() для создания Dask.Array из существующего массива NumPy или другой поддерживаемой структуры данных.
import numpy as np


arr = np.array([1, 2, 3, 4, 5])
darr = da.from_array(arr, chunks=2)

В этом примере создается Dask.Array из массива NumPy arr. Параметр chunks указывает размер блока данных, на которые будет разделен массив.
Выполнение операций: Вы можете выполнять различные операции над Dask.Array так же, как и над массивами NumPy. Например:
result = darr.mean()

В этом примере вычисляется среднее значение Dask.Array darr.
Получение результатов: Для получения конечных результатов выполните операцию compute() над Dask.Array.
final_result = result.compute()

В этом примере final_result будет содержать окончательное значение среднего значения массива.
Dask.Array обеспечивает гибкость и эффективность при работе с большими массивами данных, позволяя выполнять операции параллельно на распределенных вычислительных системах.
14.Dask.Array – поддерживаемые операции и отличия от NumPy ndarray
Основные возможности Dask Array
Dask Array поддерживает большинство интерфейсов NumPy, в частности: 
● Арифметические операции и скалярные функции: +, *, exp, log, ... 
● Агрегирующие функции (в т.ч. вдоль осей): sum(), mean(), std(), sum(axis=0), ... 
● Умножение матриц, свёртка тензоров: tensordot 
● Получение срезов: x[:100, 500:100:-2] 
● Прихотливое индексирование вдоль одной оси: x[:, [10, 1, 5]] 
● Работу с протоколами массивов __array__ и __array_ufunc__ 
● Некоторые операции линейной алгебры: svd, qr, solve, solve_triangular, lstsq 
Но, Dask Array не поддерживает следующих возможностей NumPy: 
● Не реализована большая часть пакета np.linalg 
● Не поддерживаются операции с массивами неизвестного размера 
● Операции наподобие sort , которые по своей сути сложно выполнять параллельно не поддерживаются. Зачастую, вместо таких операций предлагается альтернативная функция, дружественная к параллельному вычислению 
● Не поддерживаются операции типа tolist, т.к. это очень неэффективно для больших наборов данных, тем более что, обход этих данных в циклах очень неэффективен.

15.Распараллеливание алгоритмов с помощью dask.delayed – принцип и примеры использования

При помощи dask.delayed можно распараллелить произвольный алгоритм, написанный на Python. 
● dask.delayed имеет смысл применять, если работа алгоритма плохо ложится на логику, предлагаемую dask.Bag, dask.Array или dask.DataFrame. 
● dask.delayed позволяет быстро превратить существующий алгоритм, имеющий потенциал распараллеливания, в параллельный. Для этого очень удобно использовать аннотации @delayed. 
● Использование dask.delayed позволяет генерировать граф зависимостей задач, который будет исполняться параллельно с помощью планировщика Dask. 
● Параллельную обработку данных с помощью dask.delayed можно сочетать с использованием dask.Bag, dask.Array или dask.DataFrame за счет применения функций from_delayed to_delayed.


16.Дополнительные параметры декоратора dask.delayed – назначение и примеры использования

Декоратор - это функция, которая принимает функцию или метод в качестве аргумента и возвращает новую функцию или метод, включающую декорированную функцию или метод, с дополнительными функциональными возможностями. 

В Python есть специальный синтаксис для декорирования функций во время их определения. 

В большинстве случаев более удобным способом использования dask.delayed является его применение в виде декоратора @delayed . Но, нужно иметь в виду, что этот способ не подходит для функций, описанных во внешних библиотеках. 

Декоратор dask.delayed кроме оборачиваемого объекта может принимать необязательные параметры. 

В том числе имеется необязательный параметр: 

pure:bool , optional - указывает является ли возвращаемый объект отложенных вычислений чистой функцией. Если значение параметра True для вызовов будет создаваться поисковая таблица для оптимизации за счет совместного использования результатов идентичных обращений к функции. Если значение параметра не передано, то значение по умолчанию будет соответствовать глобальному параметру delayed_pure или False , в случае, если этот параметр не установлен.
 
17.Использование dask.delayed для объектов и операции над объектами dask.delayed, включая ограничения их использования

Объекты Delayed поддерживают большинство операций Python, каждая из которых создает новый объект Delayed, который представляет результат операции: 
● Большинство операторов (*, -, и т.д.) 
● Доступ к объектам и срезы (a[0]) 
● Доступ к атрибутам (a.size) 
● Вызовы методов (a.index(0)) 

Объекты Delayed НЕ поддерживают следующие операции: 
● Операции изменяющие значение объекта Delayed, такие как: a += 1 
● Операции изменяющие значение объекта Delayed, такие как: __setitem__/__setattr__ (a[0] = 1, a.foo = 1) 
● Итерацию по объекту Delayed: for i in a: ... 
● Использование объекта Delayed в условии ветвления: if a: ... 
Два последних пункта означают, что объекты Delayed не могут использоваться для управления потоком вычислений (не могут использоваться в качестве условия if и в качестве итерируемого объекта). Эти ограничения связаны с тем, что граф зависимостей задач, построенный при помощи dask.delayed, не меняется во время выполнения вычисления. Использование Delayed в условном операторе или в качестве объекта для итерации потребовало бы динамического изменения графа в зависимости от фактических значений Delayed. 

При этом, объекты Delayed могут использоваться: 
● внутри тела цикла (см пример выше) 
● внутри тела условного оператора

18.Dask.DataFrame - структура данных, специфика реализации и применения, процедура создания Dask.DataFrame
Dask DataFrame это большой, предназначенный для параллельной обработки, DataFrame состоящий из множества дата фреймов Pandas. Дата Фреймы, из которых состоит Dask DataFrame: 

● представляют собой фрагменты большого DataFrame, разбитого по индексу.
● могут располагаться на диске, для вычислений с данными, большими, чем оперативная память, как на одной машине, так и на разных машинах, входящих в кластер. Dask DataFrame имеет интерфейс, максимально похожий на Pandas DataFrame, при этом: 
● одна операция с Dask DataFrame порождает множество операций с датафрэймами Pandas 
● вычисления управляются с помощью инфраструктуры Dask, которая позволяет:  
распараллеливать расчеты 
выполнять расчеты поэтапно, что дает возможность обрабатывать объемы данных, большие чем оперативная память. 
Каждый блок данных в разбиении называется сегментом (partition) а его верхняя и нижняя граница разделителем (division).

 ● Dask может хранить информацию о разделителях. 
● Разбиение на сегменты важно для выполнения эффективных запросов.
 ● Сегменты станут важны при написании собственных функций, которые необходимо применить к элементам в Dask DataFrame. 

Мотивация: Dask DataFrame целесообразно использовать для анализа и обработки данных: 
● имеющих табличный формат 
● и имеющих размер больший, чем оперативная память. В частности, если операции с вашим массивом данных в Pandas приводят к ошибкам MemoryError, то использование Dask DataFrame позволяет обойти эту проблему. 

Издержки:
● Операции Dask DataFrame используют вызовы функций pandas. 
● Обычно они выполняются с той же скоростью что и операции в pandas. 
● Небольшие дополнительные накладные расходы добавляет инфраструктура Dask (около 1 мс. на задачу, при выполнении достаточно крупных задач этими издержками можно пренебречь).




19.Ограничения использования Dask.DataFrame и операции мэппинга в Dask.DataFrame

Какие функции не работают? 
Dask DataFrame покрывает только небольшую но наиболее востребованную часть API pandas.  Причинами такого положения являются, то, что: 

● Pandas обладает гигантским API
 ● Некоторые операции по своей природе сложно выполнить параллельно (например, сортировку) 

Кроме того, некоторые важные операции, такие как set_index работают, но существенно медленнее, чем в Pandas, так как по своей сути требуют группировки (shuffling) данных и могут потребовать записи данных на диск.

Какие функции определенно работают 
● Тривиально распараллеливаемые операции (работают быстро): 
Elementwise operations: df.x + df.y 
Row-wise selections: df[df.x > 0] 
Loc: df.loc[4.0:10.5] 
Common aggregations: df.x.max() 
Is in: df[df.x.isin([1, 2, 3])] 
Datetime/string accessors: df.timestamp.month 
● Операции, требующие нетривиальной организации параллельной работы (работают быстро):
 groupby-aggregate (with common aggregations): df.groupby(df.x).y.max() value_counts: df.x.value_counts 
Drop duplicates: df.x.drop_duplicates() 
Join on index: dd.merge(df1, df2, left_index=True, right_index=True) 
● Операции требующие группировки (shuffle) (медленно, если не по индексу) 
Set index: df.set_index(df.x)
groupby-apply (with anything): df.groupby(df.x).apply(myfunc) 
Join not on the index: pd.merge(df1, df2, on='name') 
● Операции загрузки данных 
Files: dd.read_csv, dd.read_parquet, dd.read_json, dd.read_orc, etc. 
Pandas: dd.from_pandas 
Anything supporting numpy slicing: dd.from_array 
From any set of functions creating sub dataframes via dd.from_delayed. 
Dask.bag: mybag.to_dataframe(columns=[...]) 
Мэппинг: 

В dask.dataframe есть несколько функций для применения собственных функций к данным, хранящихся в dataframe. Для работы с Series в Dask имеются следующие функции: 

● map мэппинг значений из series используя сопоставление из словаря, другой серии или функции 
● apply применение более сложных функций к элементам из series 
● map_partitions применение функции к каждой секции Dask.DataFrame 
● map_overlap применение функции к каждой секции Dask.DataFrame с возможностью доступа к значениям из смежных секций. 

map(arg, na_action=None, meta='__no_default__') мэппинг значений из series используя сопоставление из словаря, другой серии или функции

Параметры: 
● arg: функция, словарь или серия - определяет преобразование элементов 
● na_action: {None, ‘ignore’} при значении ‘ignore’, значения NA распространяются без применения преобразования 

meta: метаданные возвращаемого результата, определяющие структуру и типы столбцов возвращаемого значения, метаданные могут быть заданы одним из из типов: pd.DataFrame, pd.Series, dict, iterable, tuple, optional. Пустой pd.DataFrame или pd.Series имеющие последовательность, названия и типы столбцов (dtype) соответствующие возвращаемому значению. Альтернативой может быть словарь вида {name: dtype} или итерируемый объект состоящий из кортежей (name, dtype). В случае отсутствия метаданных Dask попытается автоматически их определить, что может привести к непредвиденным ошибкам.


20.Поддержка Dask.DataFrame операций работающих со скользящим окном



21.Совместное использование промежуточных результатов в Dask: принцип работы и примеры использования
При работе с DataFrame некоторые вычисления могут проделывать более одного раза. Для большинства операций dask.dataframe сохраняет промежуточные результаты так, что они могут повторно использоваться. Но для этого эти промежуточные результаты должны рассматриваться в рамках одного процесса вычислений, запущенного вызовом compute (или его неявным аналогом). 

Рассмотрим пример расчета суммы и среднего значения для одного столбца dask.dataframe.



Для расчета среднего значения используется суммирование по столбцу, что и составляет основную трудоемкость операции. (не случайно выполнение каждой из функций занимает примерно одно время). Использование промежуточных результатов суммирования для вычисления среднего значения могло бы существенно его ускорить. 

Для этого обе функции нужно рассчитать в рамках одного вызова функции compute.


Использование dask.compute для одновременного расчета двух функций сократило время расчета в 2 раза. Это произошло из-за того, что графы зависимостей задач для вычисления каждой функции были объединены, что позволило однократно выполнять вычисления встречающиеся в каждом из графов. 

В частности однократно выполнялись операции:

 ● загрузка данных из файла (функция read_csv) 
● фильтрация (df[df.amount > 0]) ● часть операций в свертках (функции sum, count)


22.Dask.Bag - структура данных, специфика реализации и применения, процедура создания DaskBag

Принципы Dask Bag 
Структура данных Bag 

Мультимножество (bag, multiset) в математике - обобщение понятия множества, допускающее включение одного и того же элемента по нескольку раз. Число элементов в мультимножестве, с учётом повторяющихся элементов, называется его размером или мощностью. 

● list: упорядоченная коллекция, допускающая повторы элементв. Пример: [1, 2, 3, 2] 
● set: неупорядоченная коллекция, не допускающая повторы элементов. Пример: {1, 2, 3}
 ● bag: неупорядоченная коллекция, допускающая повторы элементов. Пример: 1, 2, 2, 3 Таким образом, bag можно рассматривать как список, не гарантирующий порядка элементов.

 Dask.Bag
(Dask.Bag) - это структура данных в библиотеке Dask, которая представляет собой коллекцию элементов (обычно непоследовательных), подобных списку или набору. Dask Bag обеспечивает распределенную обработку данных, позволяя эффективно работать с большими объемами информации, превышающими объем доступной оперативной памяти.

 Dask.Bag реализует такие операции, как map, filter, fold (аналог reduce) и groupby над коллекциями объектов Python. 

Реализация Dask.Bag основана на координации множества списков или итераторов, каждый из которых представляет собой сегмент большой коллекции. 

Данная реализация обеспечивает: 
● параллельное выполнение операций 
● потребность в небольшом объеме памяти за счет использования итераторов Python и ленивых вычислений. Это обеспечивает возможность обработки данных больших чем объем оперативной памяти, даже при использовании всего одного сегмента. 


Специфика реализации 
По умолчанию, Dask.Bag использует для исполнения планировщик dask.multiprocessing. 
● Это позволяет обойти проблему GIL и полноценно использовать несколько процессорных ядер для объектов реализованных на чистом Python. 
● Минусом этого подхода является наличие больших накладных расходов при обмене данных между исполнителями, что важно для производительности вычислений, требующих интенсивного обмена данными. Это редко бывает проблемой, так как типичный поток задач для Dask.Bag подразумевает: 
или чрезвычайно параллельные вычисления
 или обмен небольшим объемом данных в процессе свертки (англ. folding, также известна как reduce, accumulate).

(с диска Насти)
Специфика реализации и применения Dask Bag:
Ленивая вычислительная модель: Dask Bag работает в ленивом режиме, что означает, что он не выполняет вычисления немедленно, а создает вычислительный граф, который можно оптимизировать и выполнить при необходимости. Это позволяет эффективно обрабатывать большие объемы данных, разбивая их на более мелкие части и распределяя вычисления на доступные ресурсы.
Распределенная обработка данных: Dask Bag позволяет обрабатывать данные, превышающие объем доступной оперативной памяти, путем распределения вычислений на кластеры или другие вычислительные ресурсы. Он автоматически разбивает и распределяет данные между узлами вычислительного кластера, обеспечивая параллельную обработку и управление памятью.
Гибкие операции: Dask Bag предоставляет мощные операции для манипуляции данными, включая фильтрацию, маппинг, сортировку, сведение и агрегацию. Он также поддерживает пользовательские функции для более сложных операций.


Процедура создания Dask Bag:
Импорт библиотеки:

Создание Bag: Создайте объект Bag с помощью одного из доступных методов:
from_sequence: Создает Bag из Python последовательности, такой как список или кортеж.
from_url: Загружает Bag из текстового файла или URL-адреса.
from_filenames: Создает Bag из списка файлов.
from_delayed: Создает Bag из отложенных (ленивых) вычислений.

Выполнение вычислений: Примените операции к созданному объекту Bag. Эти операции не выполняются немедленно, но создают вычислительный граф.

Выполнение вычислений: Для выполнения вычислений используйте метод compute(), который запускает выполнение вычислительного графа и возвращает результат.


В результате выполнения этих шагов будет создан объект Dask Bag, который можно использовать для манипуляции и обработки данных. Для получения результата выполнения вычислений вызывается метод compute(), который запускает вычисления и возвращает результат.

Dask Bag предоставляет удобный и эффективный способ работы с большими объемами данных и распределенных вычислений, что делает его полезным инструментом в анализе данных и параллельных вычислениях.

23.Организация вычислений с помощью Map / Filter / Reduce : общий принцип и специфика параллельной реализации обработки данных в Dask.Bag

​​Встроенная функция map() позволяет применить функцию к каждому элементу последовательности 
● Функция имеет следующий формат: 
mар(<Функция>, <Последовательность 1>[, ... , <Последовательность N>])
 ● Функция возвращает объект, поддерживающий итерацию, а не список.




Функция filter() позволяет выполнить проверку элементов последовательности. 
● Формат функции: filter(<Функция>, <Последовательность>)
 ● Если в первом параметре вместо названия функции указать значение None, то каждый элемент последовательности будет проверен на соответствие булевскому  значению True. 
● Если элемент в логическом контексте возвращает значение False, то он не будет добавлен в возвращаемый результат.
 ● Функция возвращает объект, поддерживающий итерацию, а не список.
functools.reduce(funct, iterable[, initializer])
Вычисляет функцию от двух элементов последовательно для элементов последовательности слева направо таким образом, что результатом вычисления становится единственное значение, которое становится первым аргументом для следующей итерации применения funct.

Левый аргумент функции funct (аргумента reduce) - это аккумулированное значение, правый аргумент - очередное значение из списка. 

Если передан необязательный аргумент initializer, то он используется в качестве левого аргумента при первом применении функции (исходного аккумулированного значения). 
Если initializer не перередан, а последовательность имеет только одно значение, то возвращается это значенние. 

Чрезвычайная параллельность (embarrassingly parallel) - тип задач в системах параллельных вычислений, для которых не требуется прилагать больших усилий при разделении на несколько отдельных параллельных задач (распараллеливании). 

● Чаще всего не существует зависимости (или связи) между параллельными задачами, то есть их результаты не влияют друг на друга. 
● Чрезвычайно параллельные задачи практически не требуют согласования между результатами выполнения отдельных этапов, что отличает их от задач распределённых вычислений, которые требуют связи промежуточных результатов. 
● Такие задачи легки для исполнения массово паралельных системах (кластерах с очень большим количеством вычислительных узлов).




(с диска насти) на всякий случай


24.API Dask.Bag – функции мэппинга, фильтрации и преобразования

Объекты Bag поддерживают стандартное API, аналогичное имеющемуся в стандартной библиотеке Python и библиотеках toolz или pyspark. В частности, имеются функции, отвечающие за маппинг (map и т.п.), фильтрацию и группировку (filter, groupby и т.п.) и свертку (reduce и т.п.).
Операции над объектом Bag, создают новые объекты Bag, таким образом формируются задачи для отоложенных вычислений.
Для старта вычислений необходимо вызвать для объекта Bag функцию compute().
Результат compute() для объектов Bag будет представлен в виде списка (или единичного значения при операциях свертки).
Получение итератора по bag приводит к выполнению compute(). Таким образом list(bag) автоматически стартует вычисления.







25.API Dask.Bag – функции группировки и свертки

Объекты Bag поддерживают стандартное API, аналогичное имеющемуся в стандартной библиотеке Python и библиотеках toolz или pyspark. В частности, имеются функции, отвечающие за маппинг (map и т.п.), фильтрацию и группировку (filter, groupby и т.п.) и свертку (reduce и т.п.).
Операции над объектом Bag, создают новые объекты Bag, таким образом формируются задачи для отложенных вычислений.
Для старта вычислений необходимо вызвать для объекта Bag функцию compute().
Результат compute() для объектов Bag будет представлен в виде списка (или единичного значения при операциях свертки).
Получение итератора по bag приводит к выполнению compute(). Таким образом list(bag) автоматически стартует вычисления.


















(с диска насти)

foldby комбинирует свертку и группировку и выполняет эту операцию намного эффективнее	последовательного применения groupby и reduce. 			
		



26.Принципы работы Apache Hadoop.
Что такое Hadoop?
Apache Hadoop («Хадуп») — это набор инструментов для построения системы работы с большими данными. Он предназначен для сбора, хранения и распределенной обработки сотен терабайт информации, которая поступает непрерывным потоком. Именно на его основе строят озёра данных — объемные хранилища, в которых хранится неструктурированная информация для будущей аналитики.

Hadoop работает по принципу MapReduce, то есть распределения данных. Его суть в том, что система состоит из кластеров — групп отдельных под серверов, или узлов, которые используются как единый ресурс. Когда на кластер поступает обширная задача, Hadoop делит её на много мелких подзадач и выполняет каждую на своем узле. Это позволяет параллельно решать несколько задач и быстрее выдать конечный результат.


Архитектура экосистемы Hadoop
Внутри проекта Hadoop — четыре основных модуля:

1.Hadoop Common.
 Набор инструментов, которые используются для создания инфраструктуры и работы с файлами. По сути, это управляющая система для остальных модулей и связи с дополнительными инструментами.

2.HDFS (Hadoop Distributed File System).
 Распределенная файловая система для хранения данных на различных узлах. В неё встроена система дублирования данных, чтобы обеспечить их надежность и сохранность даже при отказе отдельных серверов. Здесь хранятся неструктурированные данные, извлекать которые нужно не просто запросами, а специальными средствами и инструментами.

3.YARN (Yet Another Resource Negotiator).
 Система управления кластером Hadoop, которая позволяет приложениям использовать вычислительные мощности.

4.Hadoop MapReduce.
 Платформа, которая отвечает за MapReduce-вычисления, то есть распределяет входные данные по узлам.

Также в системе Hadoop есть многочисленные дополнительные компоненты, например:

●Hive.
 Хранилище, которое позволяет запрашивать из HDFS большие наборы данных и создавать сложные задания MapReduce. Использует язык запросов HQL, который напоминает SQL. Именно с этим хранилищем, как правило, работают аналитики данных.

●Pig.
 Инструмент для преобразования данных, который умеет подготавливать данные различных форматов для будущего использования.

●Flume.
 Инструмент для приёма больших данных и отправки их в HDFS. Умеет собирать большие потоковые данные, например, из логов.

●Zookeeper.
 Координатор, который помогает эффективнее распределять информацию по разным узлам.
27.Принципы работы Apache Spark.
Что такое Apache Spark
Apache Spark — это фреймворк для обработки и анализа больших объемов информации, входящий в инфраструктуру Hadoop. Он позволяет быстро выполнять операции с данными в вычислительных кластерах и поддерживает такие языки программирования, как Scala, Java, Python, R и SQL.
Spark ускоряет обработку больших данных, распределяя вычисления между сотнями и тысячами машин, объединенных в кластеры. Это не новая технология — за несколько лет до появления Spark в Hadoop с аналогичной целью использовался MapReduce.


Подход Spark выгодно отличается от классической парадигмы MapReduce и позволяет добиться большей скорости обработки данных. Это стало возможным благодаря ряду особенностей фреймворка.


Обработка в памяти (in-memory processing). Spark хранит и обрабатывает данные в оперативной памяти. Такой подход обеспечивает гораздо большую скорость, чем загрузка и чтение данных с диска, как в MapReduce.
Ленивые вычисления. Spark использует концепцию отложенного выполнения вычислений. Это означает, что операции над данными проводятся только перед непосредственным использованием результатов этих операций. Благодаря этому вычислительные мощности не тратятся на вычисления, которые понадобятся когда-то в будущем.
Resilient distributed datasets (RDD). Эта структура хранит датасеты и информацию о выполненных преобразованиях сразу на нескольких узлах кластерной сети. RDD позволяет Spark восстановить данные в случае сбоя и оптимизировать вычисления.
Параллельная обработка и комбинирование операций. Spark распределяет данные и вычисления по нескольким узлам в кластере, выполняя разные операции обработки параллельно в режиме реального времени. Это отличает его от MapReduce, при использовании которого каждый следующий этап работы с датасетом требует завершения предыдущего.
Благодаря этим особенностям Spark имеет в десятки раз большую скорость работы с данными, чем MapReduce.

28.Сценарии использования Faiss.
Что такое Faiss?
Faiss (Facebook* AI Similarity Search) – это библиотека для эффективного поиска похожих векторов, разработанная Facebook* AI Research. Она предоставляет ряд алгоритмов для быстрого поиска ближайших соседей в больших наборах данных. Она используется в приложениях машинного обучения и обработки естественного языка для решения задач, связанных с анализом текста и поиска схожих запросов.
Использование с ChatGPT
Для эффективной работы чат-ботов, основанных на модели ChatGPT, часто требуется быстрый поиск наиболее подходящего ответа на основе запроса пользователя. Faiss предоставляет возможность быстрого поиска наиболее похожих ответов в заранее подготовленной базе данных.
Основные сценарии применения:
1. Поиск похожих изображений
Задача: Имеется большая база изображений, и необходимо быстро находить визуально похожие изображения по заданному образцу.
Решение с Faiss:
Изображения преобразуются в векторные представления с помощью моделей глубокого обучения (например, ResNet или VGG). Затем Faiss используется для поиска ближайших соседей среди векторов, представляющих изображения.
2. Рекомендательные системы
Задача: Системы рекомендаций часто работают с векторами, представляющими пользователей и товары.
Решение с Faiss:
После обучения модели эмбеддингов товаров и пользователей Faiss может использоваться для поиска наиболее релевантных товаров для конкретного пользователя на основе схожести их векторных представлений.
3. Кластеризация данных
Задача: Большие наборы данных, такие как тексты, изображения или события, часто требуют группировки схожих элементов.
Решение с Faiss:
Faiss поддерживает поиск ближайших соседей, что позволяет эффективно реализовать алгоритмы кластеризации, такие как k-means.
4. Поиск по текстам (semantic search)
Задача: Поиск текстов на основе их семантического содержания, а не ключевых слов.
Решение с Faiss:
Тексты преобразуются в векторные представления с помощью моделей, таких как BERT или Sentence-BERT. Faiss используется для быстрого поиска ближайших векторов в базе документов.
5. Детекция аномалий
Задача: Необходимо обнаружить аномальные события, отличающиеся от нормальных данных.
Решение с Faiss:
Faiss позволяет быстро находить ближайшие объекты. Если ближайший сосед объекта находится на слишком большом расстоянии, это может свидетельствовать о наличии аномалии.
6. Построение графов k-ближайших соседей (k-NN Graphs)
Задача: Построение графов, где узлы соединяются, если они являются ближайшими соседями.
Решение с Faiss:
Faiss позволяет быстро находить ближайших соседей для каждой точки, что удобно для построения k-NN графов.
7. Поиск похожих аудиофрагментов
Задача: Найти аудиофрагменты, схожие по звучанию или содержанию.
Решение с Faiss:
Аудиофайлы конвертируются в векторные эмбеддинги с помощью моделей глубокого обучения, таких как VGGish или OpenL3. Faiss обеспечивает быстрый поиск схожих аудиофрагментов по этим эмбеддингам.
8. Генерация плейлистов и персонализация контента
Задача: Автоматическая генерация персонализированных плейлистов на основе предпочтений пользователя.
Решение с Faiss:
Пользовательские предпочтения и треки представляются в виде векторов, а Faiss позволяет искать треки, наиболее схожие с предпочтениями пользователя.


29.Сценарии использования Redis.

Понимание Redis: 
Redis , что означает Remote Dictionary Server, представляет собой хранилище структур данных в памяти с открытым исходным кодом , которое можно использовать в качестве базы данных «ключ-значение», кэша и брокера сообщений. 
В качестве базы данных в памяти Redis хранит свои данные непосредственно в оперативной памяти, предлагая значительно более высокую скорость вычислений по сравнению с традиционными реляционными базами данных 
Реальные приложения Redis: сценарии использования
Универсальность и высокая производительность Redis делают его идеальным для нескольких реальных сценариев использования:
Кэширование : Redis является популярным выбором для кэширования из-за его возможностей быстрого извлечения данных. Выступая в качестве промежуточного хранилища данных между приложением и его основным источником данных, Redis может значительно сократить время отклика и снизить нагрузку на основную базу данных.
Управление сеансом : веб-приложения часто полагаются на данные сеанса для идентификации и хранения информации о пользователе во время сеанса просмотра. Redis обеспечивает эффективный способ управления данными сеанса благодаря своей высокой производительности и гибкости.
Аналитика и мониторинг в реальном времени : Redis обеспечивает аналитику и мониторинг в реальном времени, обеспечивая быстрый и эффективный доступ к большим наборам данных. Это особенно полезно в случаях использования, которые требуют немедленного понимания или постоянного мониторинга ключевых показателей.
Очереди сообщений и ограничение скорости : Redis можно использовать в качестве брокера сообщений для управления очередями сообщений и выполнения задач по ограничению скорости. Его функция Pub/Sub делает его отличным выбором для приложений, требующих общения в реальном времени, таких как системы уведомлений или системы живого чата.
Таблицы лидеров и статистические счетчики . Структура данных Redis с отсортированными наборами может использоваться для хранения и управления таблицами лидеров или статистическими счетчиками в таких приложениях, как онлайн-игровые платформы, приложения для социальных сетей или веб-сайты электронной коммерции.
Индексация геопространственных данных : Redis включает поддержку геопространственных данных . Это позволяет разработчикам легко создавать приложения, требующие анализа географических данных или отслеживания местоположения пользователя в режиме реального времени. Это всего лишь несколько примеров того, как Redis можно использовать для решения различных реальных задач. Его высокая производительность и универсальные структуры данных делают его мощным инструментом управления данными для различных приложений и отраслей.




''')
    
def q25_ex():
    print('''
    import numpy as np
import matplotlib.pyplot as plt

# Пример функции
def f(k):
    if abs(k) <= 3:
        return k * np.sin(3 * k) * np.arctan(2 * k)
    else:
        return 0

# Реализация FFT
def FFT(x):
    N = len(x)
    if N == 1:
        return x
    else:
        X_even = FFT(x[::2])
        X_odd = FFT(x[1::2])
        factor = np.exp(-2j * np.pi * np.arange(N) / N)
        X = np.concatenate([X_even + factor[:N // 2] * X_odd,
                            X_even + factor[N // 2:] * X_odd])
        return X

# Реализация IFFT
def IFFT(X):
    N = len(X)
    if N <= 1:
        return X
    even = IFFT(X[::2])
    odd = IFFT(X[1::2])
    factor = np.exp(2j * np.pi * np.arange(N) / N)
    return np.concatenate([even + factor[:N // 2] * odd,
                           even - factor[:N // 2] * odd]) / 2

# Генерация значений функции
K = np.linspace(-3.5, 3.5, 128) #длина массива должна быть степенью двойки!!
x = np.array([f(elem) for elem in K])

# Применение FFT
res = FFT(x)
N = len(K)
n = np.arange(N)
sr = 1 / ((K[-1] - K[0]) / (len(K) - 1))  # Частота дискретизации
T = N / sr
freq = n / T

# Построение графика амплитуды FFT
plt.figure(figsize=(8, 4))
plt.stem(freq, abs(res), 'b', markerfmt=" ")
plt.xlabel('Частота (Гц)')
plt.ylabel('Амплитуда FFT')
plt.show()

# Применение IFFT
k = IFFT(res)
plt.figure(figsize=(8, 4))
plt.plot(K, k.real, 'b')  # Используем только действительную часть
plt.xlabel('Время')
plt.ylabel('Амплитуда')
plt.show()
''')

def q19_ex():
    print('''
    def method_rk4(f, h, x_end, y0):
    N = int(x_end / h)
    t = np.linspace(0, x_end, N+1)

    y = np.zeros((N+1, len(y0)))
    k1 = np.zeros_like(y0)
    k2 = np.zeros_like(y0)
    k3 = np.zeros_like(y0)
    k4 = np.zeros_like(y0)
    y[0, :] = y0

    for n in range(N):
        k1 = h * f(t[n], y[n, :])
        k2 = h * f(t[n] + h/2, y[n, :] + k1/2)
        k3 = h * f(t[n] + h/2, y[n, :] + k2/2)
        k4 = h * f(t[n] + h, y[n, :] + k3)

        y[n + 1, :] = y[n, :] + (k1 + 2 * (k2 + k3) + k4) / 6

    return t, y

def fsimple(t, y): #y - это array, хранящий значения [x,y]
    x_val, y_val = y[0], y[1]
    return np.array([x_val + y_val, y_val - x_val])

t_1, y_1 = method_rk4(fsimple, 0.01, 1, [1, 0])

#фазовый портрет
plt.plot([elem[0] for elem in y_1], [elem[1] for elem in y_1])
plt.grid()''')
def q20_ex():
    print('''
    import matplotlib.pyplot as plt

def dydx(x, y=0):
    return x*y + np.arctan(x)
def AdamsMoulton(dydx, x_start, x_end, y0, endx=2, h=0.02):
    yl = [y0]
    xl = np.arange(x_start, x_end, h).tolist()

    # узнаем y для Трех точек через метод Рунге-Кутты
    for i in range(2):
        k1 = h * dydx(xl[i], yl[i])
        k2 = h * dydx(xl[i] + h/2, yl[i] + 1/2* k1)
        k3 = h * dydx(xl[i] +h/2, yl[i]+ 1/2 * k2)
        k4 = h * dydx(xl[i] + h, yl[i] + k3)

        yn = yl[i] + 1/6 * (k1 + 2*k2+ 2*k3 + k4)

        yl.append(yn)

    # Метод Адамса-Мултона
    for i in range(2, len(xl)-1):
        yn = yl[i] + h/12 * (5*dydx(xl[i+1]) + 8*dydx(xl[i])- dydx(xl[i-1]))
        yl.append(yn)
    xl.append(endx)

    return np.array(xl), np.array(yl)


x,y = AdamsMoulton(dydx, 0, 2, 1, endx=2,h=0.01)

plt.plot(x[:-1],y)''')
def q6():
    print('''
    def vec_norm(a):
    return (sum(i**2 for i in a))**0.5

def mat_vec_mult(matrix, vector): #перемножение матрицы на вектор
    num_rows = len(matrix)
    num_cols = len(matrix[0])
    result = [0] * num_rows
    for i in range(num_rows):
        for j in range(num_cols):
            result[i] += matrix[i][j] * vector[j]
    return result

def vec_dot(a, b): #произведение двух векторов
    return sum(ai * bi for ai, bi in zip(a, b))

def transpose_vector(vector): #Транспонирование вектора -> в одномерный список
    return [vector[i] for i in range(len(vector))]

def vec_mat_mult(vec, matrix): #перемножение вектора матрицу
    num_cols = len(matrix[0])
    result = [0] * num_cols

    for j in range(num_cols):
        for i in range(len(vec)):
            result[j] += vec[i] * matrix[i][j]
    return result


# Матрица A
A = [[6, 2, 1, 4],
     [2, 7, 3, 1],
     [1, 3, 8, 2],
     [4, 1, 2, 2]]

# Вектор x
x = [1, 1, 1, 1]

# Параметры алгоритма
tol = 1e-10
max_iter = 10000
lam_prev = 0

for i in range(max_iter):
    # Умножаем матрицу на вектор и нормируем результат
    x = mat_vec_mult(A, x)
    norm = vec_norm(x)
    x = [xi / norm for xi in x]

    # Считаем приближенное собственное значение
    xt = transpose_vector(x)
    lam = vec_dot(vec_mat_mult(xt, A), x) / vec_dot(xt, x)

    # Проверяем условие остановки
    if abs(lam - lam_prev) < tol:
        break
    lam_prev = lam

print(f'Наибольшее собственное значение: {lam}')
print(f'Собственный вектор:')
print(transpose_vector(x))

print('-----------------------')
eigenvalues, eigenvectors = np.linalg.eig(A)
print(f'Настоящие собственные значения:')
print(eigenvalues)
print(f'Настоящие собственные векторы:')
print(eigenvectors)''')
def q8():
    print('''
    # только с базовыми

def triu(matrix, k): # np.triu
    rows, cols = matrix.shape
    result = np.zeros_like(matrix)
    for i in range(rows):
        for j in range(cols):
            if j >= i + k:
                result[i, j] = matrix[i, j]
    return result

def matmul(A, B):
  n = A.shape[0]
  k = A.shape[1]
  m = B.shape[1]
  c = np.zeros((n, m))
  for i in range(n):
    for j in range(m):
      for s in range(k):
        c[i, j] += A[i, s] * B[s, j]
  return c

def vec_dot(a, b):
  return sum(ai * bi for ai, bi in zip(a, b))


def qr_decomposition(A):
  n, m = A.shape
  Q = np.zeros((m, n))
  R = np.zeros((n,n))
  for j in range(n):
    v = A[:, j]
    for i in range(j):
      R[i, j] = vec_dot(Q[:, i], A[:, j])
      v = v - R[i, j] * Q[:, i]
    R[j, j] = (sum(i**2 for i in v))**0.5
    Q[:, j] = [i/R[j,j] for i in v]
  return Q, R


def shur_dec(A, eps = 0.001):
  n = A.shape[0]
  U = np.eye(A.shape[0])
  while triu(A, 1).max() >= eps:
    Q, R = qr_decomposition(A)
    A = matmul(R, Q)
    U = matmul(U, Q)
  T = A
  return U, T

A = np.array([[1, 5, 3,6],
       [2, 7, 4,7],
       [1, 8, 9,8],
      [1,2,3,4]])
U, T = shur_dec(A)

print("Матрица U (унитарная):")
print(U)

print("Матрица T (верхнетреугольная):")
print(T)

# Проверка
print("Проверка разложения Шура (A ≈ U @ T @ U^*):")
print(np.allclose(A, U @ T @ U.T.conj()))''')
def q31():
    print('''
    import numpy as np
A = np.array([[7, 2, 1, 5], [2, 8, 3, 1], [1, 3, 6, 2], [5, 1, 2, 3]])

cf = np.poly(A)
ev_roots = np.roots(cf)

print(cf)
print(ev_roots)
print(np.linalg.eigvals(A))''')
def q31_th():
    print('''
    Метод непосредственного развёртывания предполагает решение характеристического уравнения для нахождения собственных значений.

$$\det\left(A - \lambda I \right) = 0$$

Данный метод хорошо подходит для нахождения собственных значений матриц не очень большого порядка (примерно $n \le 10$).

Естественно, сам метод предполгаеат нахождение корней полинома $n$, что представляет из себя отдельную довольно тяжёлую задачу как с точки зрения точности полученных решений, так и с точки зрения сложности вычислений. В случае матриц высших порядков как правило применяют иные методы, выбор метода в таком случае уже зависит от характера задачи (нахождение полного спектра матрицы или только наибольшего собственного значения, например).''')
def q30_th():
    print('''
    Метод вращений предназначен для поиска собственных значений и собственных векторов симметричных матриц. Основная идея заключается в последовательном обнулении внедиагональных элементов матрицы путём применения матриц вращения.

Метод используется для решения полной проблемы собственных значений симметрической матрицы и основан на преобразовании подобия исходной матрицы $A \in \mathbb{R}^{n \times n}$ с помощью ортогональной матрицы $H$.

Две матрицы $A$ и $A^{(i)}$ называются подобными ($A \sim A^{(i)}$ или $A^{(i)} \sim A$), если:

$$ A^{(i)} = H^{-1} A H \quad \text{или} \quad A = H A^{(i)} H^{-1},$$

где $H$ — невырожденная матрица.

В методе вращений в качестве $H$ берется ортогональная матрица, такая, что:

$$ H H^\top = H^\top H = E, \quad \text{т. е.} \quad H^\top = H^{-1}.$$



**Плюсы:**
1. Метод особенно эффективен для симметричных матриц, гарантируя высокую точность вычисленных собственных значений.
2. Алгоритм относительно прост в программировании и не требует сложных операций.
3. Метод хорошо работает с небольшими и средними симметричными матрицами.

**Минусы**
1. Для больших матриц метод требует много итераций, что делает его менее эффективным по сравнению с другими алгоритмами.
2. Для несоответствующих матриц этот метод не работает.
3. Для очень больших матриц вычислительные и временные затраты могут стать значительными.

---

**Сравнение метода вращений и QR-алгоритма**

| **Критерий**          | **Метод вращений (Якоби)**         | **QR-алгоритм**                     |
|------------------------|------------------------------------|-------------------------------------|
| **Применимость**      | Только для симметричных матриц    | Для всех квадратных матриц         |
| **Сходимость**        | Медленная                         | Быстрая для большинства матриц     |
| **Сложность**         | \( O(n^3) \) за итерацию           | \( O(n^3) \) за итерацию            |
| **Точность**          | Высокая для симметричных матриц   | Хорошая, но может страдать для плохо обусловленных матриц |
| **Масштабируемость**  | Плохо подходит для больших матриц | Более эффективно работает с большими матрицами |
| **Численная устойчивость** | Стабильный для симметричных матриц | Устойчив для большинства случаев   |''')
def q30():
    print('''
    def diag(matrix): # np.diag
    rows, cols = matrix.shape
    return np.array([matrix[i, i] for i in range(rows)])

def matmul(matrix_1, matrix_2):
    n = matrix_1.shape[0]
    k = matrix_1.shape[1]
    m = matrix_2.shape[1]

    result = np.zeros((n, m))

    for i in range(n):
        for j in range(m):
            for s in range(k):
                result[i][j] += matrix_1[i][s]*matrix_2[s][j]
    return result

def jacobi_method(A, eps=1e-8, max_iter=100):
    n = A.shape[0]
    vecs = np.eye(n)

    for i in range(max_iter):
        # находим наибольшее по модулю значение в верхней наддиагональной части матрицы
        max_val = 0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(A[i, j]) > abs(max_val):
                    max_val = A[i, j]
                    p, q = i, j

        # проверка условия окончания процесса
        if abs(max_val) < eps:
            break

        # находим угол phi
        if A[p, p] == A[q, q]:
            phi = np.pi / 4
        else:
            phi = 0.5 * np.arctan(2 * A[p, q] / (A[p, p] - A[q, q]))

        # составляем матрицу вращения
        H = np.eye(n)
        H[p, p] = np.cos(phi)
        H[q, q] = np.cos(phi)
        H[p, q] = -np.sin(phi)
        H[q, p] = np.sin(phi)

        # matmul - наивное умножение матриц, из вопроса 1
        A = matmul(matmul(H.T, A), H)
        vecs = matmul(vecs, H)

    vals = diag(A)
    return vals, vecs

A = np.array([
    [1, 2, 3],
    [2, 6, 4],
    [3, 4, 5]
])

true_eigvals, true_eigvec = np.linalg.eig(A)
print("numpy:")
print("values:")
display(true_eigvals)
print("vectors:")
for v in true_eigvec:
    display(v)

print("jacobi:")
eigvals, eigvec = jacobi_method(A)
print("values:")
display(eigvals)
print("vectors:")
for v in eigvec:
    display(v)''')
def q29():
    print('''
    import time
import numpy as np
import scipy as sp
import scipy.linalg

n = 5000

c = np.random.randn(n)
C = sp.linalg.circulant(c)
x = np.random.randn(n)

def circulant_matvec(c, x):
    return np.fft.ifft(np.fft.fft(c) * np.fft.fft(x))

y_full = C.dot(x)
full_time = %timeit -q -o C.dot(x)

print(f'Время полного матвека = {full_time.average}')

y_fft = circulant_matvec(c, x)
fft_time = %timeit -q -o circulant_matvec(c, x)

print(f'Время FFT= {fft_time.average}')

print(f'Относительная ошибка = {np.linalg.norm(y_full - y_fft) / np.linalg.norm(y_full)}')''')
def q27():
    print('''
    #пример теплицевой матрицы
import numpy as np
from scipy.linalg import toeplitz

row_0 = [1,2,3,4,5]
column_0 = [1,6,7,8,9]

a = toeplitz(row_0, column_0)
a''')
def q25():
    print('''
    import matplotlib.pyplot as plt
import numpy as np
from numpy.fft import fft, ifft

def concatenate(arrays): # np.concatenate вроде использовать нельзя
    result = []
    for arr in arrays:
        result.extend(arr)

    return np.array(result)

def FFT(x):
    N = len(x)

    if N == 1:
        return x
    else:
        X_even = FFT(x[::2])
        X_odd = FFT(x[1::2])
        factor = np.exp(-2j*np.pi*np.arange(N)/N)

        X = np.concatenate([X_even + factor[:int(N/2)] * X_odd,
                            X_even + factor[int(N/2):] * X_odd])

        return X

sr = 128 # Частота дискретизации. Здесь - степень 2
ts = 1/sr

t = np.arange(0, 1, ts)

freq = 1
x = 3 * np.sin(2*np.pi*freq*t)

freq = 4
x += 1 * np.sin(2*np.pi*freq*t)

freq = 7
x += 0.5 * np.sin(2*np.pi*freq*t)

plt.figure(figsize = (8, 4))
plt.plot(t, x, 'b')
plt.xlabel('Время')
plt.ylabel('Амплитуда')
plt.show()

X = FFT(x)

N = len(x)
n = np.arange(N)
T = N/sr
freq = n/T

plt.figure(figsize = (8, 4))
plt.subplot(121)
plt.stem(freq, abs(X), 'b', markerfmt = " ", basefmt = "-b")
plt.xlabel('Частота (Гц)')
plt.ylabel('Амплитуда DFT')

n_oneside = N//2
f_oneside = freq[:n_oneside]

X_oneside = X[:n_oneside]/n_oneside

plt.subplot(122)
plt.stem(f_oneside, abs(X_oneside), 'b', markerfmt = " ", basefmt = "-b")
plt.ylabel('Амплитуда')

plt.show()

def IFFT(X):
    N = len(X)
    if N <= 1:
        return X
    even = IFFT(X[::2])
    odd = IFFT(X[1::2])
    factor = np.exp(2j * np.pi * np.arange(N) / N)
    return np.concatenate([even + factor[:N // 2] * odd, even - factor[:N // 2] * odd]) /2

x = IFFT(X)
plt.figure(figsize = (8, 4))
plt.plot(t, x, 'b')
plt.xlabel('Время')
plt.ylabel('Амплитуда')
plt.show()''')
def q24_ex2():
    print('''
    #дискретный Фурье с фильтрацией
#пример
def f(t):
    return np.sin(2*np.pi*t)+np.cos(6*np.pi*t)

t = np.linspace(-1,1,100)
plt.plot(t, [f(elem) for elem in t])
plt.xlabel('время')
plt.ylabel('амплитуда')
plt.show()

#дискретное преобразование Фурье
def DFT(x):
    N = len(x)
    n = np.arange(N)
    k = n.reshape((N, 1))
    e = np.exp(-2j * np.pi * k * n / N)
    X = np.dot(e, x)
    return X

res = DFT(np.array([f(elem) for elem in t]))
N = len(t)
n = np.arange(N)
sr = 1/((t[-1]-t[0])/(len(t)-1))#частота дискретизации = 1 / ((конечное значение - начальное) / (кол-во точек - 1))
T = N/sr
freq = n/T


plt.figure(figsize = (8, 4))
plt.stem(freq, res, 'b', markerfmt = " ")
plt.xlabel('Частота (Гц)')
plt.ylabel('Амплитуда DFT')
plt.show()


#убираем частоты выше 5гц
# (В задании сказано удалить частоты, выше 5Гц, то есть по идее надо удалять по оси частот, т.е. по x, а не по величине амплитуды, надеемся что это ему и нужно)
res[5:] = 0
# res[res >= 5] = 0

plt.figure(figsize = (8, 4))
plt.stem(freq, res, 'b', markerfmt = " ")
plt.xlabel('Частота (Гц)')
plt.ylabel('Амплитуда DFT')
plt.show()


#обратное преобразование Фурье
def IDFT(X):
    N = len(X)
    n = np.arange(N)
    k = n.reshape((N, 1))
    e = np.exp((2j * np.pi * n * k)/N)
    x = 1/N * (np.dot(e, X))
    return x

res_idft = IDFT(res)
plt.figure(figsize = (8, 4))
plt.plot(t, res_idft , 'b')
plt.plot(t,[f(elem) for elem in t])
plt.xlabel('Время')
plt.ylabel('Амплитуда')
plt.show()''')
    
def q24_ex():
    print('''
    #пример
def f(k):
  if abs(k)<=3:
    return k*np.sin(3*k)*np.arctan(2*k)
  else:
    return 0

K = np.linspace(-3.5,3.5,100)
plt.plot(K, [f(elem) for elem in K])
plt.xlabel('время')
plt.ylabel('амплитуда')
plt.show()

#дискретное преобразование Фурье
def DFT(x):
    N = len(x)
    n = np.arange(N)
    k = n.reshape((N, 1))
    e = np.exp(-2j * np.pi * k * n / N)
    X = np.dot(e, x)
    return X

res = DFT(np.array([f(elem) for elem in K]))
N = len(K)
n = np.arange(N)
sr = 1/((K[-1]-K[0])/(len(K)-1)) #частота дискретизации = 1 / ((конечное значение - начальное) / (кол-во точек - 1))
T = N/sr
freq = n/T

plt.figure(figsize = (8, 4))
plt.stem(freq, abs(res), 'b', markerfmt = " ")
plt.xlabel('Частота (Гц)')
plt.ylabel('Амплитуда DFT')
plt.show()

#обратное преобразование Фурье
def IDFT(X):
    N = len(X)
    n = np.arange(N)
    k = n.reshape((N, 1))
    e = np.exp((2j * np.pi * n * k)/N)
    x = 1/N * (np.dot(e, X))
    return x

k = IDFT(res)
plt.figure(figsize = (8, 4))
plt.plot(K, k, 'b')
plt.xlabel('Время')
plt.ylabel('Амплитуда')
plt.show()''')
def q24():
    print('''
    import matplotlib.pyplot as plt
import numpy as np
from numpy.fft import fft, ifft

sr = 100 # Частота дискретизации
ts = 1/sr

t = np.arange(0, 1, ts)

freq = 1
x = 3 * np.sin(2*np.pi*freq*t)

freq = 4
x += 1 * np.sin(2*np.pi*freq*t)

freq = 7
x += 0.5 * np.sin(2*np.pi*freq*t)

plt.figure(figsize = (8, 4))
plt.plot(t, x, 'b')
plt.xlabel('Время')
plt.ylabel('Амплитуда')
plt.show()

def DFT(x):
    N = len(x)
    n = np.arange(N)
    k = n.reshape((N, 1))
    e = np.exp(-2j * np.pi * k * n / N)
    X = np.dot(e, x)
    return X

X = DFT(x)
N = len(x)
n = np.arange(N)
T = N/sr
freq = n/T

plt.figure(figsize = (8, 4))
plt.stem(freq, abs(X), 'b', markerfmt = " ", basefmt = "-b")
plt.xlabel('Частота (Гц)')
plt.ylabel('Амплитуда DFT')
plt.show()

n_oneside = N//2
f_oneside = freq[:n_oneside]

X_oneside = X[:n_oneside]/n_oneside

fig = plt.figure(figsize = (12, 4))

plt.subplot(121)
plt.stem(f_oneside, abs(X_oneside), 'b', markerfmt = " ", basefmt = "-b")
plt.xlabel('Частота')
plt.ylabel('Амплитуда')

plt.subplot(122)
plt.stem(f_oneside, abs(X_oneside), 'b', markerfmt = " ", basefmt = "-b")
plt.xlim(0, 10)
plt.xlabel('Частота')
plt.ylabel('Амплитуда')

plt.show()

def IDFT(X):
    N = len(X)
    n = np.arange(N)
    k = n.reshape((N, 1))
    e = np.exp((2j * np.pi * n * k)/N)
    x = 1/N * (np.dot(e, X))
    return x

x = IDFT(X)
plt.figure(figsize = (8, 4))
plt.plot(t, x, 'b')
plt.xlabel('Время')
plt.ylabel('Амплитуда')
plt.show()''')
def q23():
    print('''
    sr = 100 # частота дискретизации
ts = 1/sr # шаг
t = np.arange(0, 1, ts)

freq = 5
y = np.sin(2*np.pi*freq*t)

fig = plt.figure(figsize = (8, 4))

plt.subplot(211)
plt.plot(t, y, 'b')
plt.ylabel('Амплитуда')


freq = 10
y = np.sin(2*np.pi*freq*t)

plt.subplot(212)
plt.plot(t, y, 'b')
plt.ylabel('Амплитуда')

plt.xlabel('Время')
plt.show()''')
def q21():
    print(''' 
    def func(x, y=1):
    return x*y + np.arctan(x)

def Milne(func, x, y0, h = 0.01):
    x0, x1 = x
    yl = [y0]
    xl = np.arange(x0, y0, h).tolist()

    # узнаем y для 4 точек через метод Рунге-Кутты
    for i in range(3):
        k1 = h * dydx(xl[i], yl[i])
        k2 = h * dydx(xl[i] + h/2, yl[i] + 1/2* k1)
        k3 = h * dydx(xl[i] +h/2, yl[i]+ 1/2 * k2)
        k4 = h * dydx(xl[i] + h, yl[i] + k3)

        yn = yl[i] + 1/6 * (k1 + 2*k2+ 2*k3 + k4)

        yl.append(yn)

    # Метод Милна
    for i in range(2, len(xl)-1):
        y_pred = yl[i-3] + (4*h/3) * (2*func(xl[i-2], yl[i-2]) - func(xl[i-1], yl[i-1]) + 2*func(xl[i], yl[i]))
        yn = yl[i-1] + (h/3) * (func(xl[i-1], yl[i-1]) + 4*func(xl[i], yl[i]) + f(xl[i+1], y_pred))
        yl.append(yn)
    xl.append(x1)

    return np.array(xl), np.array(yl)

x, y = Milne(func, (0, 2), 1)
plt.plot(x, y)''')
def q20():
    print('''  
    def dydx(x, y):
    return x**2 - np.sin(2*x)

def AdamsBashforth(x0, y0, endx=2, h=0.2):
    yl = [y0]
    xl = np.arange(x0, y0, h).tolist()

    # узнаем y для Трех точек через метод Рунге-Кутты
    for i in range(2):
        k1 = h * dydx(xl[i], yl[i])
        k2 = h * dydx(xl[i] + h/2, yl[i] + 1/2* k1)
        k3 = h * dydx(xl[i] +h/2, yl[i]+ 1/2 * k2)
        k4 = h * dydx(xl[i] + h, yl[i] + k3)

        yn = yl[i] + 1/6 * (k1 + 2*k2+ 2*k3 + k4)

        yl.append(yn)

    # Метод Адамса-Бэшфорта
    for i in range(2, len(xl)):
        yn = yl[i] + h/12 * (23*dydx(xl[i], yl[i]) - 16 * dydx(xl[i-1],yl[i-1]) + 5* dydx(xl[i-2], yl[i-2]))
        yl.append(yn)
    xl.append(endx)

    return np.array(xl), np.array(yl)
########################################################
def dydx(x, y=0):
    return x**2 - np.sin(2*x)

def AdamsMoulton(x0, y0, endx=2, h=0.02):
    yl = [y0]
    xl = np.arange(x0, y0, h).tolist()

    # узнаем y для Трех точек через метод Рунге-Кутты
    for i in range(2):
        k1 = h * dydx(xl[i], yl[i])
        k2 = h * dydx(xl[i] + h/2, yl[i] + 1/2* k1)
        k3 = h * dydx(xl[i] +h/2, yl[i]+ 1/2 * k2)
        k4 = h * dydx(xl[i] + h, yl[i] + k3)

        yn = yl[i] + 1/6 * (k1 + 2*k2+ 2*k3 + k4)

        yl.append(yn)

    # Метод Адамса-Мултона
    for i in range(2, len(xl)-1):
        yn = yl[i] + h/12 * (5*dydx(xl[i+1]) + 8*dydx(xl[i])- dydx(xl[i-1]))
        yl.append(yn)
    xl.append(endx)

    return np.array(xl), np.array(yl)''')
def q19():
    print('''
    def dydx(x, y):
  return x**2 - np.sin(2*x)

def rungeKutta(x0, y0, endx=2, h=0.2):
    yl = [y0]
    xl = np.arange(x0, endx, h).tolist()

    for i in range(len(xl)):

        k1 = h * dydx(xl[i], yl[i])
        k2 = h * dydx(xl[i] + h, yl[i] + k1)

        yn = yl[i] + k1/2 + k2/2

        yl.append(yn)
    xl.append(endx)
    return np.array(xl), np.array(yl)

def method_rk3(f, x_end, y0, N):
    h = x_end / N
    x = np.linspace(0, x_end, N+1)

    y = np.zeros((N+1, len(y0)))
    k1 = np.zeros_like(y0)
    k2 = np.zeros_like(y0)
    k3 = np.zeros_like(y0)
    y[0, :] = y0

    for n in range(N):
        k1 = h * f(x[n], y[n, :])
        k2 = h * f(x[n] + h/2, y[n, :] + k1/2)
        k3 = h * f(x[n] + h, y[n, :] - k1 + 2*k2)

        y[n + 1, :] = y[n, :] + (k1 + 4 * k2 + k3) / 6

    return x, y

#рунге-кутта 4-го порядка
def method_rk4(f, x_end, y0, N):
    h = x_end / N
    x = np.linspace(0, x_end, N+1)

    y = np.zeros((N+1, len(y0)))
    k1 = np.zeros_like(y0)
    k2 = np.zeros_like(y0)
    k3 = np.zeros_like(y0)
    k4 = np.zeros_like(y0)
    y[0, :] = y0

    for n in range(N):
        k1 = h * f(x[n], y[n, :])
        k2 = h * f(x[n] + h/2, y[n, :] + k1/2)
        k3 = h * f(x[n] + h/2, y[n, :] + k2/2)
        k4 = h * f(x[n] + h, y[n, :] + k3)

        y[n + 1, :] = y[n, :] + (k1 + 2 * (k2 + k3) + k4) / 6

    return x, y

def fsimple(x, y):
    return -np.sin(x)

x_1, y_1 = method_rk4(fsimple, 0.5, [1.0], 1)
x_5, y_5 = method_rk4(fsimple, 0.5, [1.0], 5)
x_50, y_50 = method_rk4(fsimple, 0.5, [1.0], 50)

print(f'Решение при х=0.5  и h=1 - {y_1[-1, 0]}')
print(f'Решение при х=0.5  и h=0.1 - {y_5[-1, 0]}')
print(f'Решение при х=0.5  и h=0.01 - {y_50[-1, 0]}')
print(f'Точное значение - {np.cos(0.5)}')


#рунге-кутта для решения системы диф.уравнений
import math

# Функция, содержащая правые части дифференциальных уравнений
def equations(x, y):
    return [y[1], math.exp(-x * y[0])]

def rk(func, x0, xf, y0, h):
    count = int((xf - x0) / h) + 1
    y = [y0[:]]  # создание массива y с начальными условиями
    x = x0

    for i in range(1, count):
        k1 = func(x, y[i - 1])
        k2 = func(x + h / 2, list(map(lambda arr1, arr2: arr1 + arr2 * h / 2, y[i - 1], k1)))
        k3 = func(x + h / 2, list(map(lambda arr1, arr2: arr1 + arr2 * h / 2, y[i - 1], k2)))
        k4 = func(x + h, list(map(lambda arr1, arr2: arr1 + arr2 * h, y[i - 1], k3)))

        y.append([])

        for j in range(len(y0)):
            y[i].append(y[i - 1][j] + h / 6 * (k1[j] + 2 * k2[j] + 2 * k3[j] + k4[j]))

        x += h

    return y
print(rk(equations, 0, 1, [0,0], 0.1))''')
def q18():
    print('''
    #задача Коши методом предиктора(явный метод эйлера)-корректора(модифицированный метод Эйлера (метод трапеций))
import numpy as np
import matplotlib.pyplot as plt

def predictor_corrector_euler(f, t_start, y0, t_end, h):
    t = np.arange(t_start, t_end + h, h)#массив значений времени
    y = np.zeros((len(t), len(y0)))  # Обработка y0 как вектора
    y[0] = y0  # Устанавливаем начальное условие

    for i in range(len(t) - 1):
        y_pred = y[i] + h * f(t[i], y[i])# Предиктор
        y[i + 1] = y[i] + (h / 2) * (f(t[i], y[i]) + f(t[i + 1], y_pred))# Корректор
    return t, y

# y' = 2y-t^2, y(0) = 1
f = lambda t, y: 2*y - t**2
t_start = 0
y0 = np.array([1])
t_end = 3
h = 0.005
t, y = predictor_corrector_euler(f, t_start, y0, t_end, h)

# Построение графика
plt.plot(t, y, label='Численное решение')
plt.xlabel('t')
plt.ylabel('y(t)')
plt.legend()
plt.title('Метод предиктора-корректора')
plt.grid(True)
plt.show()''')
def q17():
    print('''
    def euler(f, x_end, y0, N):
  h = x_end / N
  x = np.linspace(0.0, x_end, N+1)

  y = np.zeros((N+1, len(y0)))
  y[0,:] = y0
  for n in range(N):
      y[n+1, :] = y[n, :] + h*f(x[n], y[n,:])
  return x,y

def simple(x,y):
  return -np.sin(x)

x_5, y_5 = euler(simple, 0.5, [1.0], 5)
x_50, y_50 = euler(simple, 0.5, [1.0], 50)

print(f'Решение при х=0.5  и h = 0.1 -> {y_5[-1][0]}')
print(f'Решение при х=0.05  и h = 0.1 -> {y_50[-1][0]}')
print(f'Точное решение - {np.cos(0.5)}')



#решение системы дифференциальных уравнений методом Эйлера
import math

def equations(x, y): # Функция, содержащая правые части дифференциальных уравнений
    return [y[1], math.exp(-x * y[0])]

def eiler(func, x0, xf, y0, h):
    count = int((xf - x0) / h) + 1
    y = [y0[:]]  # создание массива y с начальными условиями
    x = x0
    for i in range(1, count):
        right_parts = func(x, y[i - 1])
        y.append([])  # добавление пустой строки

        for j in range(len(y0)):
            y[i].append(y[i - 1][j] + h * right_parts[j])

        x += h
    return y

print(eiler(equations, 0, 1, [0,0], 0.1))
''')
def q16():
    print('''
    def central_difference(f, x, h):
    return (f(x + h) - f(x - h)) / (2 * h)

# Пример функции
def f(x):
    return np.cos(np.pi*x)**3  # Пример функции: f(x) = cos(πx)^3

x = np.pi/2  # Точка, в которой будем вычислять производную
h = 0.01  # Шаг

# Вычисляем производную с помощью метода прямой разности
approx_derivative = central_difference(f, x, h)

# Для проверки вычислим производную с помощью библиотеки
x_sym = sp.symbols('x')
f_sym = sp.cos(sp.pi*x_sym)**3
exact_derivative = sp.diff(f_sym, x_sym).subs(x_sym, x)

print("Приближенное значение производной:", approx_derivative)
print("Точное значение производной:", exact_derivative.evalf())#evalf()-нужен, чтобы посчитать численное значение, иначе ответ будет вот таким:-3*pi*sin(1.5707963267949*pi)*cos(1.5707963267949*pi)**2''')
def q15():
    print('''
    import numpy as np
import sympy as sp
import matplotlib.pyplot as plt

def euler_method(f, t0, y0, h, t_end):
    t = np.arange(t0, t_end + h, h)
    y = np.zeros_like(t)
    y[0] = y0

    for i in range(1, len(t)):
        y[i] = y[i - 1] + h * f(t[i - 1], y[i - 1])

    return t, y # t - массив временных точек, y - массив зн-й решения


def f(t, y): # Пример задачи: dy/dt = y * sin(t)
    return y * np.sin(t)

# Параметры задачи
t0 = 0 # начальное время
y0 = 1 #  начальное условие
t_end = 5 # конечное время
h = 0.5  # шаг интегрирования

t_euler, y_euler = euler_method(f, t0, y0, h, t_end) # Численное решение методом Эйлера

#------- находим общее решение оду
t = sp.Symbol('t')   # Время
y = sp.Function('y') # Функция y(t)

func = sp.Eq(y(t).diff(t), y(t) * sp.sin(t))

solution = sp.dsolve(func, y(t))
print("Общее решение:", solution)
#--------------------------------
y_true = np.exp(-np.cos(t_euler)) # Общее решение

local_errors = np.abs(y_true - y_euler) # Локальная ошибка
global_error = local_errors[-1]

print('Локальные ошибки на каждом шаге:')
for t_i, error_i in zip(t_euler, local_errors):
    print(f't = {t_i:.2f}, локальная ошибка = {error_i:.5f}')

print(f'\nГлобальная ошибка: {global_error:.5f}')

# Построение графиков
plt.figure(figsize=(12, 6))

# Решение
plt.subplot(1, 2, 1)
plt.plot(t_euler, y_true, label="Точное решение", color="black", linewidth=2)
plt.plot(t_euler, y_euler, 'o--', label="Метод Эйлера", color="blue")
plt.xlabel("t")
plt.ylabel("y(t)")
plt.title("Решение ОДУ методом Эйлера")
plt.legend()
plt.grid(True)

# Локальная ошибка
plt.subplot(1, 2, 2)
plt.plot(t_euler, local_errors, 'o-', label="Локальная ошибка", color="red")
plt.axhline(global_error, color="green", linestyle="--", label="Глобальная ошибка")
plt.xlabel("t")
plt.ylabel("Ошибка")
plt.title("Локальные и глобальная ошибки метода Эйлера")
plt.legend()
plt.grid(True)

plt.show()''')
    
    
def q14():
    print('''
    import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

def solve_odu(f, t_span, y0, method='RK45'): # f - ф-я, t_span - кортеж (t0, tf), y0 - нач усл-е
    sol = solve_ivp(f, t_span, y0, method = method)
    return sol

def example_ode(t, y): # Пример: dy/dt = y * sin(t)
  return y * np.sin(t)

t_span = (0, 10)
y0 = np.array([1])

sol = solve_odu(example_ode, t_span, y0)

print(sol)

plt.plot(sol.t, sol.y[0, :])
plt.xlabel('t')
plt.ylabel('y(t)')
plt.title('решение оду dy/dt = y * np.sin(t)')
plt.grid(True)
plt.show()''')
    
def q13():
    print('''
    import scipy.sparse as sp
import numpy as np

# Пример разреженной матрицы
data = np.array([1, 2, 3, 4])
row_indices = np.array([0, 1, 2, 3])
col_indices = np.array([1, 2, 3, 4])

coo_matrix = sp.coo_matrix((data, (row_indices, col_indices)), shape=(5, 5))
print("COO формат:", coo_matrix)

csr_matrix = coo_matrix.tocsr()
print("CSR формат:", csr_matrix)

csc_matrix = coo_matrix.tocsc()
print("CSC формат:", csc_matrix)''')
def q12():
    print('''
    #код нерабочий, но вдруг поможет
import numpy as np

def div_conq_alg(A):
    n = A.shape[0]
    if n == 1:
        return np.array([A[0, 0]])

    A11 = A[:n//2, :n//2]    # Разделение матрицы на подматрицы
    A12 = A[:n//2, n//2:]
    A21 = A[n//2:, :n//2]
    A22 = A[n//2:, n//2:]

    eigvals_A11 = div_conq_alg(A11) # рекурсивно вычисляем собственные значения подматриц
    eigvals_A22 = div_conq_alg(A22)

    eigvals = np.concatenate((eigvals_A11, eigvals_A22)) # Комбинирование результатов

    return eigvals

A = np.array([[2, 1, 0],
              [1, 1, 5],
              [0, 3, 1]], dtype=float)  # Пример матрицы

eigenvalues_dac = div_conq_alg(A)
print("Собственные значения:", eigenvalues_dac)

true_eigvals, true_eigvec = np.linalg.eig(A)
true_eigvals''')
    
    
def q11():
    print('''
    def vec_dot(a, b):
  return sum(ai*bi for ai, bi in zip(a, b))

def matmul(A, B):
  n = A.shape[0]
  k = A.shape[1]
  m = B.shape[1]
  c = np.zeros((n, m))
  for i in range(n):
    for j in range(m):
      for s in range(k):
        c[i, j] += A[i, s] * B[s, j]
  return c

def norm2(v):
    s = 0
    for i in range(len(v)):
        s+= v[i]**2
    return s**(1/2)

def qr_decomposition(A):
    u = []
    e = []
    v = A.T[0]
    u.append(list(v))
    e.append(list(v/norm2(v)))
    for i in range(1, len(A)):
        v = A.T[i]
        u_ = v - sum([(vec_dot(u[z], v) / vec_dot(u[z], u[z])) * np.array(u[z]) for z in range(len(u))])
        u.append(list(u_))
        e.append(list(u_ / norm2(u_)))

    return np.array(e).T, np.array(e) @ A

def tril(A): # np.tril
    maxelem = -float('inf')
    for i in range(1, A.shape[0]):
        for j in range(0, i):
            maxelem = max(maxelem, A[i, j])

    return abs(maxelem)

def diag(matrix): # np.diag
    rows, cols = matrix.shape
    return np.array([matrix[i, i] for i in range(rows)])

def qr_alg_shifts(A, eps = 0.001):
  Q_final = np.eye(A.shape[0])
  Q_list = []
  while tril(A) > eps:
      Q, R = qr_decomposition(A - A[-1, -1] * np.eye(A.shape[0]))
      Q_list.append(Q)
      A = matmul(R, Q) + A[-1, -1] * np.eye(A.shape[0])
      Q_final = matmul(Q_final, Q)
  return A, diag(A), [Q_final[:, i] for i in range(Q_final.shape[1])]

A = np.array([[1, 3, 5, 7],
             [2, 4, 6, 8],
              [5, 5, 7, 9],
              [4,6,8,0]])
A_, eigval, eigvec = qr_alg_shifts(A)

eigval, np.linalg.eigvals(A)''')
    
def q10():
    print('''
    
A = np.array([[1, 1], [0, 1]]) # Пример матрицы

# Вычисление спектра
w, v = np.linalg.eig(A)
print("Спектр матрицы A:", w)


def pseudo_spectrum(A, epsilon): # Функция для вычисления псевдоспектра
    w, v = np.linalg.eig(A)
    pseudo_spectrum_vals = []
    for val in w:
      pseudo_spectrum_vals.append(val + epsilon) # примерное вычисление, требует уточнения в зависимости от задачи
    return np.array(pseudo_spectrum_vals)

# Вычисление псевдоспектра
epsilon = 0.01
pseudo_w = pseudo_spectrum(A, epsilon)
print(f"Псевдоспектр матрицы A (epsilon = {epsilon}):", pseudo_w)

# Визуализация (пример)
plt.figure(figsize=(8, 6))
plt.scatter(np.real(w), np.imag(w), label="Спектр", marker='o', s=100, color='blue')
plt.scatter(np.real(pseudo_w), np.imag(pseudo_w), label=f"Псевдоспектр (epsilon = {epsilon})", marker='x', s=100, color='red')
plt.xlabel("Действительная часть")
plt.ylabel("Мнимая часть")
plt.title("Спектр и псевдоспектр матрицы")
plt.legend()
plt.grid(True)''')
def q9():
    print('''
    from collections import OrderedDict
import scipy.linalg
# Пример нормальной матрицы
A = np.array([[4, 1], [1, 4]])
# Проверка нормальности
is_normal = np.allclose(A.T.conj() @ A, A @ A.T.conj())
print("Матрица нормальна:", is_normal)


# Пример эрмитовой матрицы
B = np.array([[3, 2+1j], [2-1j, 1]])
# Проверка эрмитовости
is_hermitian = np.allclose(B, B.T.conj())
print("Матрица эрмитова:", is_hermitian)


# Проверка унитарной диагонализуемости
def is_unitarily_diagonalizable(A, tol=1e-10):
    A_star = A.conj().T  # Эрмитово-сопряжённая матрица A
    norm_diff = np.linalg.norm(A @ A_star - A_star @ A)  # Норма разности A A* и A* A
    return norm_diff < tol
# Пример использования
A = np.array([[1, 0], [0, 1]], dtype=complex)
print(is_unitarily_diagonalizable(A))  # Вывод: True или False


# Пример приведения к верхне-гессенберговой форме
D = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
# Use scipy.linalg.hessenberg instead of np.linalg.hessenberg
H = scipy.linalg.hessenberg(D) # scipy.linalg contains the hessenberg function
print("Верхне-гессенбергова форма:")
H''')
def q7():
    print('''
    n = 3
fig, ax = plt.subplots(1, 1)
a = np.array([[5, 1, 1], [1, 0, 0.5], [2, 0, 10]])
a = a + 2 * np.random.randn(n, n)
xg = np.diag(a).real
yg = np.diag(a).imag
rg = np.zeros(n)
ev = np.linalg.eigvals(a)
for i in range(n):
    rg[i] = np.sum(np.abs(a[i, :])) - np.abs(a[i, i])
    crc = plt.Circle((xg[i], yg[i]), radius=rg[i], fill=False)
    ax.add_patch(crc)
plt.scatter(ev.real, ev.imag, color='r', label="Eigenvalues")
plt.axis('equal')
plt.legend()
ax.set_title('Eigenvalues and Gershgorin circles')
fig.tight_layout()''')
def q5():
    print('''
    def vec_dot(a, b):
  return sum(ai*bi for ai, bi in zip(a, b))

def matmul(A, B):
  n = A.shape[0]
  k = A.shape[1]
  m = B.shape[1]
  c = np.zeros((n, m))
  for i in range(n):
    for j in range(m):
      for s in range(k):
        c[i, j] += A[i, s] * B[s, j]
  return c

def norm2(v):
    s = 0
    for i in range(len(v)):
        s+= v[i]**2
    return s**(1/2)

def qr_decomposition(A):
    u = []
    e = []
    v = A.T[0]
    u.append(list(v))
    e.append(list(v/norm2(v)))
    for i in range(1, len(A)):
        v = A.T[i]
        u_ = v - sum([(vec_dot(u[z], v) / vec_dot(u[z], u[z])) * np.array(u[z]) for z in range(len(u))])
        u.append(list(u_))
        e.append(list(u_ / norm2(u_)))

    return np.array(e).T, np.array(e) @ A

def tril(A): # max elem in trie matrix
    maxelem = -float('inf')
    for i in range(1, A.shape[0]):
        for j in range(0, i):
            maxelem = max(maxelem, A[i, j])

    return abs(maxelem)

def diag(matrix): # np.diag
    rows, cols = matrix.shape
    return np.array([matrix[i, i] for i in range(rows)])

def QR_method(A, eps = 0.001):
  Q_final = np.eye(A.shape[0])
  Q_list = []
  while tril(A) > eps:
    Q, R = qr_decomposition(A)
    Q_list.append(Q)
    A = matmul(R, Q)
    Q_final = matmul(Q_final, Q)
  return A, np.diag(A), [Q_final[:, i] for i in range(Q_final.shape[1])]

A = np.array([[1, 3, 5, 7], [2, 4, 6, 8], [4, 5, 7, 9], [4, 6, 8, 0]])

Q, R = qr_decomposition(A)
A_, nums, vecs = QR_method(A)
print(f'Результат QR-разложения:\n{Q.round(5)}\n\n{R.round(5)}')
print('Результат QR - алгоритма')
print(A_)
print("Собственные значения:") #диагональные элементы матрицы A
print(nums)
print("Собственные векторы:") #произведение всех Q, полученных в результате алгоритма
list(map(display, vecs));
''')
    
def q3():
    print('''
    def strassen_multiply(A, B):
    n = A.shape[0]

    # Базовый случай: умножение 1x1 матриц -> база рекурсии
    if n == 1:
        return A * B

    # Разделение матриц на блоки
    mid = n // 2
    A11, A12, A21, A22 = A[:mid, :mid], A[:mid, mid:], A[mid:, :mid], A[mid:, mid:]
    B11, B12, B21, B22 = B[:mid, :mid], B[:mid, mid:], B[mid:, :mid], B[mid:, mid:]

    # Вычисление 7 промежуточных матриц
    M1 = strassen_multiply(A11 + A22, B11 + B22)
    M2 = strassen_multiply(A21 + A22, B11)
    M3 = strassen_multiply(A11, B12 - B22)
    M4 = strassen_multiply(A22, B21 - B11)
    M5 = strassen_multiply(A11 + A12, B22)
    M6 = strassen_multiply(A21 - A11,B11 + B12)
    M7 = strassen_multiply(A12 - A22, B21 + B22)

    # Сборка результирующей матрицы
    C11 = M1 +M4 - M5 + M7
    C12 = M3 + M5
    C21 = M2 + M4
    C22 = M1 + M3 - M2 + M6

    C = np.zeros((n, n))  # Создаем пустую матрицу для результата
    C[:mid, :mid] = C11
    C[:mid, mid:] = C12
    C[mid:, :mid] = C21
    C[mid:, mid:] = C22

    return C

A = np.random.randint(0,10,(8,8))
B = np.random.randint(0,10,(8,8))
C = strassen_multiply(A, B)
print("Результат умножения матриц:")
print(C)
print(A@B)''')

def q29_th(): 
    print('''
    Для проведения быстрого матвека может понадобится следующее важное свойство Циркулянта, связывающее его с матрицей Фурье:

$$C = \frac{1}{n} F_n^* diag(F_n \cdot c) F_n$$

$$(c - \text{столбец матрицы} \  C)$$

Для **быстрого матвека** с циркулянтом:

1. Вложим Теплицеву матрицу, построенную по необходимому вектору, в циркулянт:

$$C = \begin{pmatrix} c_0 & c_{-1} & c_{-2} & c_2 & c_1 \\ c_1 & c_0 & c_{-1} & c_{-2} & c_2 \\ c_2 & c_1 & c_0 & c_{-1} & c_{-2} \\ c_{-2} & c_2 & c_1 & c_0 & c_{-1} \\ c_{-1} & c_{-2} & c_2 & c_1 & c_0 \end{pmatrix}$$

2. Получаем произведение:

$$\begin{pmatrix} y_1 \\ y_2 \\ y_3 \\ * \\ * \end{pmatrix} = \begin{pmatrix} c_0 & c_{-1} & c_{-2} & c_2 & c_1 \\ c_1 & c_0 & c_{-1} & c_{-2} & c_2 \\ c_2 & c_1 & c_0 & c_{-1} & c_{-2} \\ c_{-2} & c_2 & c_1 & c_0 & c_{-1} \\ c_{-1} & c_{-2} & c_2 & c_1 & c_0 \end{pmatrix} \cdot \begin{pmatrix} x_1 \\ x_2 \\ x_3 \\ 0 \\ 0 \end{pmatrix}$$

3. Умножение на теплицеву => умножение на циркулянт. Из связи циркулянта с преобразованием Фурье получаем ($\circ$ - поэлементное множение):

$$\begin{pmatrix} y_1 \\ y_2 \\ y_3 \\ * \\ * \end{pmatrix} = ifft\bigg( fft(\begin{pmatrix} c_0 \\ c_1 \\ c_2 \\ c_{-2} \\ c_{-1} \end{pmatrix}) \circ fft(\begin{pmatrix} x_1 \\ x_2 \\ x_3 \\ 0 \\ 0 \end{pmatrix}) \bigg)$$''')
def q28_th(): 
    print('''
    **Циркулянт** или **циркулянтная матрица** — это матрица вида $$C = \begin{pmatrix} c_1 & c_n & ... & c_2 \\ c_2 & c_1 & ... & c_3 \\ \vdots & \vdots & ... & \vdots \\ c_n & c_{n - 1} & ... & c_1 \end{pmatrix}$$ Т.е. матрица, в которой любая следующая строка (столбец), начиная с первой (с первого) получается циклической алфавитной перестановкой элементов предыдущей строки (столбца).

**Матрица Фурье**

Дискретное преобразование Фурье является линейным преобразованием, которое переводит вектор временных отсчётов в вектор спектральных отсчётов той же длины. Таким образом преобразование может быть реализовано как умножение симметричной квадратной матрицы на вектор:

$$X = \mathcal{F}x$$

Где $\mathcal{F}$ - **матрица Фурье**

**Матрица Фурье** задаётся следующим образом: $\mathcal{F}(i, k) = w^{(i-1)(k-1)}, w = \exp\{-j \cdot \frac{2\pi}{N}\}$ и выглядит:

$$\mathcal{F} = \frac{1}{\sqrt{N}}\begin{pmatrix} 1 & 1 & 1 & ... & 1 \\ 1 & w & w^2 & ... & w^{N-1} \\ 1 & w^2 & w^4 & ... & w^{2(N-1)} \\ \vdots & \vdots & \vdots & ... & \vdots \\ 1 & w^{N-1} & w^{2(N-1)} & ... & w^{(N-1)^2} \end{pmatrix}$$''')
    
def q27_th(): 
    print('''
    **Дискретная свёртка и Тёплицевы матрицы**

Дискретную свёртку можно представить как умножение матрицы на вектор:

$$z_i = \sum_{j=0}^{n-1} x_j y_{i-j}, \Leftrightarrow z = Ax,$$

где элементы матрицы $A$ равны $a_{ij} = y_{i-j}$, то есть они зависят только от разности между индексами строки и столбца(и получается, что матрица A - Теплицева матрица)

**Тёплицевы матрицы**

Матрица называется Тёплицевой, если её элементы определены как $a_{ij} = t_{i-j}$

* Тёплицева матрица полностью определяется первой строкой и первым столбцом (то есть $2n-1$ параметр).

* Это плотная матрица, однако она имеет структуру, то есть определяется $O(n)$ параметрами (сравните с разреженными матрицами)

* Основная операция для вычисления дискретной свёртки – это произведение Тёплицевой матрицы на вектор.
''')
def q26_th(): 
    print('''
    **Свёртка**

* Одна из основных операций в обработке сигналов/машинном обучении – это свёртка двух функций

* Пусть $x(t)$ и $y(t)$ две данные функции. Их свёртка определяется как $$(x * y)(t) = ∫_{-∞}^{∞} x(τ) y(t - τ) dτ$$



**Теорема о свёртке и преобразование Фурье**(связь свертки и Фурье)

Широко известный факт: свёртка во временном пространстве (time domain) эквивалентна произведению в частотном пространстве (frequency domain).

* Преобразование из одного пространства в другое осуществляется с помощью преобразования Фурье:

$$\hat{x}(w) = (F(x))(w) = ∫_{-∞}^{∞}
 e^{iwt} x(t) dt$$

* Тогда $$F(x*y) = F(x)F(y)$$

* Таким образом, алгоритм вычисления свёртки можно записать следующим образом:

  1. Вычислить преобразование Фурье от $x(t)$ и $y(t)$
  2. Вычислить их произведение
  3. Применить к результату обратное преобразование Фурье


**Операция дискретной свёртки**

* Если приблизим интеграл $(x * y)(t) = ∫_{-∞}^{∞} x(τ) y(t - τ) dτ$ с помощью суммы значений подынтегрального выражения на равномерной сетке, тогда нам останется просуммировать выражение $$z_i = \sum_{j=0}^{n-1} x_j y_{i-j},$$

  которое называется **дискретной свёрткой**. Его можно рассматривать как применение фильтра с коэффициентами $x$ к сигналу $y$.''')
    
def q25_th(): 
    print('''
    Быстрое преобразование Фурье — алгоритм ускоренного вычисления дискретного преобразования Фурье, позволяющий получить результат за время, меньшее чем $O(N^2)$.

В основе алгоритма лежат идеи о симметрии ДПФ и принципы динамического программирования. Для снижения времени вычисления исходная последовательность делится на две подпоследовательности, работать с которыми значительно проще.

**Алгоритм БПФ:**

1. Разделение последовательности на две подпоследовательности из элементов на чётных и нечётных позициях.

$$x_{even}(n)=x(2n), \quad x_{odd}(n)=x(2n + 1)$$

2. Для каждой подпоследовательности рекурсивно выполняется алгоритм БПФ, пока длина последовательности не станет достаточно маленькой для прямого вычисления преобразования Фурье или пока длина последовательности не станет равна 1, в таком случае значение ДПФ равно самому элементу последовательности.

3. Комбинирование результатов. Для учёта вклада нечётных компонент рассчтывается величина $W_k=\exp\{-j \cdot \frac{2\pi k}{N}\}$. Результаты комбинируются следующим образом:

$$X(k)=X_{even}​(k)+W_k\cdot​X_{odd​}(k), \quad X(𝑘+𝑁/2)=X_{even}​(k)-W_k\cdot​X_{odd​}(k)$$

**Фильтрацяи сигнала с использованием БПФ:**

1. Сигнал разбивается на фрагменты
2. К каждому фрагменту применяется БПФ
3. Определяются частоты, которые необходимо отфильтровать. Их мощность ставится равной 0.
4. К каждому фрагменту применяем обратное преобразование Фурье, чтобы получить очищенный исходный сигнал.''')
def q24_th(): 
    print('''
    Для некоторой периодической последовательности отсчётов $\{x(k)\}$ с периодом $N$ верны следующие выражения.

Дискретное преобразование Фурье является спектром дискретного периодического сигнала, то есть, его разложением на гармоники.

**Дискретное преобразование Фурье:**

$$X(n) = \sum\limits_{k=0}^{N-1} x(k) \exp\{-j \cdot \frac{2\pi n k}{N}\}$$

**Обратное дискретное преобразование Фурье:**

$$x(k) = \frac{1}{N}\sum\limits_{k=0}^{N-1} X(n) \exp\{j \cdot \frac{2\pi n k}{N}\}$$

**Симметрии в дискретном преобразовании Фурье:**

1. Для вещественнозначных сигналов ДПФ является Эрмитовым (то есть имеет место симметрия:) $$X(-n) = X^*(n)$$
(Т.е. положительные частоты являются комплексно-сопряжёнными соответствующим отрицательным частотам)
2. Чётная и нечётная симметрии

    Если сигнал чётный ($x(k) = x(N-k)$), то его ДПФ будет вещественнозначным и чётным.

    Если сигнал нечётный ($x(k) = -x(N-k)$), то его ДПФ будет комплексным и нечётным.

**Ограничения и недостатки ДПФ:**
1. Алиасинг или наложение частот

    Неправильная дискретизация аналогового сигнала приводит к тому, что высокочастотные его составляющие накладываются на низкочастотные, в результате чего восстановление сигнала во времени приводит к его искажениям. Для предотвращения этого эффекта частота дискретизации должна быть достаточно высокой, а сигнал должен быть надлежащим образом отфильтрован перед оцифровкой.

2. Сложность вычислений

    Из выражений ДПФ можно видеть, что для вычисления каждой гармоники нужно $N$ операций комплексного умножения и сложения и соответственно $N^2$ операций на полное выполнение ДПФ.''')
def q23_th(): 
    print('''
    Моделирование волны основывается на математическом описании периодических колебаний, которые можно выразить с помощью тригонометрических функций, например, синуса или косинуса:  

y(t) = A * sin(ω * t + φ)

где:  
- A — амплитуда  
- ω — угловая частота  
- t — время  
- φ — фаза  

**Амплитуда (A)** - Максимальное отклонение волны от её среднего значения (обычно нуля). Определяет высоту волны.  

**Период (T)** - Время, за которое волна совершает один полный цикл.  

T = 1 / f, где f — частота.  

**Длина волны (lambda)** - Расстояние, которое волна проходит за один полный период.  

λ = v * T = v / f, где v — скорость распространения волны.  

**Частота (f)** - Количество циклов волны в единицу времени. Измеряется в Герцах.  

f = 1 / T

**Герц (Hz)** - Единица измерения частоты. 1 Герц равен одному циклу в секунду.  **Пример**: Если f = 2 Hz, это означает, что волна совершает два полных колебания за одну секунду.  

**Дискретизация** - Процесс преобразования непрерывного сигнала в последовательность дискретных точек.  **Зачем это нужно?** Для моделирования волны на компьютере, где все данные хранятся в цифровом формате.  

**Частота дискретизации**  - Количество измерений (сэмплов) волны в единицу времени.  

**Фаза (phi)** - Начальное смещение волны относительно нуля во времени.  


**Угловая частота (omega)** - Измеряется в радианах в секунду и показывает скорость изменения фазы волны.  ''')
def q22_th(): 
    print('''
    Условия сходимости:

1. Для неявного метода
$$y_{n + i} = h \frac{\boldsymbol{\beta}_k}{\boldsymbol{\alpha}_k} f\left(\mathbf{x}_{n + k}, y\left(\mathbf{x}_{n + k}\right)\right) + \mathbf{g}_n,\quad \boldsymbol{\beta}_k \neq 0.$$

если $\lim_{h \to 0} (y_n - y(x_n))=0$ - сходится

2. Метод класса $\sum{i=0}^k \alpha_i y_{n+i} - h \sum_{i=0}^n \beta_i f\left(x_{n+i}, y_{n+i}\right)$, $n=0,1,2,...$ сходится, если для каждой задачи Коши $y_n \rightarrow y\left(x_0\right)$ при $h \rightarrow 0$, $n=\frac{x-x_0}{h}$. Для любых $x \in [x_0, x_k]$.

Метод должен удовлетворять условию минимального уровня локальной
точности

---
Невязка $\rho_{n+k}$ которая получается после подстановки точного решения $y(x)$ дифференциального уравнения в разностное,
$$
\rho_{n+k}=\sum_{i=0}^k \alpha_i y_{n+i}-h \sum_{i=0}^n \beta_i f\left(x_{n+i}, y\left(x_{n+i}\right)\right)
$$
имеет порядок $O(h^{s+1})$ и называется погрешностью аппроксимации. Число s называется порядком аппроксимации или степенью разностного уравнения, а $r_{n+k}=(\rho_{n+k})/h$ – погрешностью дискретизации.

Метод является согласованным, если
$$
\max _{0 \leq n \leq N} \frac{r_{n+k}}{h_n} \rightarrow 0 \quad \text { при } h \rightarrow 0
$$
и имеет порядок согласованности $S$,
$$
\max _{0 \leq n \leq N} \frac{\| r_{n+k} \|}{O(h^i)} = O\left(h^i\right)
$$

---

Метод из класса $\sum_{i=0}^{n} \alpha_i y_{n+i}=h\sum_{i=0}^n \beta_i f(x_{n+i},y(x_{n+i}))$, $n=0,1,2,\ldots$ удовлетворяет корневую условность, если все корни характеристического полинома $\rho(\theta)$ лежат внутри единичной окружности или на самой окружности, причем те корни, которые лежат на единичной окружности, являются простыми.

Если метод согласован, то $\rho(\theta)$ обязательно имеет корень $\theta_1 = +1$.

Корни характеристического полинома классифицируются следующим образом:

$\theta_1 = +1$ - главный корень;

$|\theta| \leq 1$, $i=2,3,\ldots$, $k$- посторонние корни.

---

Метод удовлетворяющий корневому условию называют **нуль-устойчивым.**

**Согласованность** – определяет величину погрешности аппроксимации, **нуль-устойчивость** – определяет характер развития этой и других погрешностей в пределе при $h \rightarrow 0$, $Nh = x_k - x_0$.

Метод из класса
$\sum_{i=0}^k \alpha_i y_{n+i} = h \sum_{i=0}^{\infty} \beta_i f\left(x_{n+i}, y\left(x_{n+i}\right)\right)$, $n = 0,1,2,...$
сходится тогда и только тогда, когда он является согласованным и нуль-устойчивым.

---
**Устойчивость** численного метода - непрерывная зависимость численных результатов от входных данных и ограниченность погрешности при заданных пределах изменения параметров метода (шагов сетки, числа итераций и т.д.)

**Сходимость** численного метода - стремление численных результатов к точному решению, при стремлении параметров метода к определенным предельным значениям, например, шага сетки к 0 или количества итераций к бесконечности.''')
def q21_th(): 
    print('''
    Метод Милна относится к многошаговым методам и представляет один из методов прогноза и коррекции. Для решения дифференциального уравнения с использованием метода Милна необходимо начать с выбора начального условия и шага интегрирования. Решение производится в два этапа. Первый – прогнозирование значения функции, второй – коррекция полученного значения. Если полученное значение после коррекции существенно отличается от спрогнозированного, то проводят еще один этап коррекции. Если такая ситуация повторяется, коррекция проводится до того момента, пока значение не будет удовлетворять требуемому. Однако очень часто ограничиваются одним этапом коррекции.

Метод Милна не является «самодостаточным», для его применения требуется получить исходные данные с помощью какого – либо одношагового метода.

Обычно для получения исходных значений для применения метода Милна используют метод Рунге-Кутты. С его помощью находят исходные значения.

Алгоритм:

1) По предсказывающей формуле вычисляется грубое значение y на правом конце интервала: yk + 1: yk + 1 = yk – 3 + 4/3 · (2 · fk – fk – 1 + 2 · fk – 2) · Δt.

2) Рассчитывается производная в k + 1 точке: fk + 1 = f(t + Δt, yk + 1).

3) Снова рассчитывается yk + 1 по уточненной формуле, используя уже новое значение производной в точке k + 1: yk + 1 = yk – 1 + 1/3 · (fk + 1 + 4 · fk + fk – 1) · Δt.

4) Рассчитывается производная в k + 1 точке с учетом вновь вычисленного более точного значения yk + 1: fk + 1 = f(t + Δt, yk + 1). Здесь же производится подсчет итераций счетчиком i: i := i + 1.

5) Проверка точности: |yk + 1i-я итерация – yk + 1(i + 1)-я итерация| ≤ ε. Если условие выполнено, и точность ε достигнута, то переходим на следующий шаг 6, иначе осуществляется переход на шаг 3 и процесс уточнения повторяется с новыми значениями y и f, причем их старое значение берется с предыдущей итерации.

6) Подготовка к новому шагу: изменение счетчика времени t, изменение номера шага k:
t := t + Δt
k := k + 1.

7) Проверка окончания расчета: t ≤ T. Если условие выполняется, то расчет продолжается для следующей точки, и осуществляется переход на шаг 1, иначе — конец.''')
def q20_th(): 
    print('''
    Сравнивая явные и неявные методы Адамса, можно отметить следующее:
 1. Недостаток неявных методов состоит в необходимости на каждом шаге решать уравнение относительно неизвестной величины $у_{n+1}$.
 2. Некоторое преимущество неявных методов состоит в точности: при одной и той же шаговости к неявные методы имеют порядок сходимости к + 1, в отличие от явных, у которых по рядок сходимости к.
 3. Главное преимущество неявных методов состоит в возможности решать жесткие системы


Сравнивая метод Адамса с методом Рунге-Кутта той же точности, отмечаем его экономичность, поскольку он требует вычисления лишь одного значения правой части на каждом шаге (метод Рунге-Кутта – четырех). При этом, метод Адамса неудобен тем, что невозможно начать счет по одному лишь известному значению y. Расчет может быть начат лишь с узла x3.

Явный метод Адама: Использует предыдущие значения $y_n$, $y_{n-1}$, ... для аппроксимации следующего значения $y_{n+1}$. Формула для трехшагового метода Адамса-Баффорта:
$$ y_{n+1} = y_n + \frac{h}{12}(23 f(t_n, y_n) - 16 f(t_{n-1}, y_{n-1}) + 5 f(t_{n-2}, y_{n-2})) $$


Неявный метод Адама: Использует текущие и будущие значения для более точного результата. Формула для трехшагового метода Адамса-Мултона:
$$ y_{n+1} = y_n + \frac{h}{12}((5f(t_{n+1}, y_{n+1}) + 8f(t_n, y_n) - f(t_{n-1}, y_{n-1})))$$

---

Явные методы

Преимущества: Простота реализации и вычислительная эффективность.
Недостатки: Ограниченная стабильность, особенно для жестких систем.

Неявные методы

Преимущества: Более высокая стабильность, подходящая для жестких систем.
Недостатки: Более сложная реализация и необходимость решения нелинейных уравнений на каждом шаге.''')
    
    
    
def q19_th(): 
    print('''
    Классический **метод Рунге-Кутты 2-го порядка**, он же Метод Эйлера с
пересчетом, описывается следующим уравнением:

$y_i = y_{i-1} + h \cdot f(x_i, y_i)$

Схема является неявной, так как искомое значение $y_i$
входит в обе части
уравнения.
Затем вычисляют значение производной в точке $(x_i, y_i)$ и окончательно
полагают:

$y_i = y_{i-1} + h \cdot \cfrac{f(x_{i-1}, y_{i-1}) + f(x_i, y_i^*)}{2}$

то есть усредняют значения производных в начальной точке и в точке “грубого
приближения”. Окончательно запишем рекуррентную формулу метода РунгеКутты 2-го порядка в следующем виде:

$y_i = y_{i-1} + \frac{h}{2} \cdot (k_1 + k_2)$

где:

$k_1 = f(x_{i-1}, y_{i-1})$

$k_2 = f(x_{i-1} + h, y_{i-1} + h \cdot k_1)$

Метод имеет второй порядок точности: Локальная погрешность метода Рунге–Кутты 2–го порядка $e_2 = C∙h^3$, где C –
некоторая постоянная, и пропорциональна кубу шага интегрирования: при
уменьшении шага в 2 раза локальная погрешность уменьшится в 8 раз.


**Метод Рунге-Кутты 3-го порядка:**

$y_{n+1} = y_n + \cfrac{(k_1 + 4k_2 + k_3)}{6}$

$k_1 = h * f(x_n, y_n)$

$k_2 = h * f(x_n + \frac{h}{2}, y_n + \frac{k_1}{2})$

$k_3 = h * f(x_n + h, y_n - k_1 + 2k_2)$

**Метод Рунге-Кутты 4-го порядка:**

$y_{n+1} = y_n + \cfrac{(k_1 + 2(k_2 + k_3) + k_4)}{6}$

$k_1 = h * f(x_n, y_n)$

$k_2 = h * f(x_n + \frac{h}{2}, y_n + \frac{k_1}{2})$

$k_3 = h * f(x_n + \frac{h}{2}, y_n + \frac{k_2}{2})$

$k_4 = h * f(x_n + h, y_n + k_3)$

Локальная ошибка - $O(h^5)$

Глобальная ошибка - $O(h^4)$''')
def q18_th(): 
    print('''
    Рассмотрим еще одно семейство многошаговых методов, которые
используют неявные схемы, – метод прогноза и коррекции (они
называются также методами **предиктор-корректор**). Суть этих
методов состоит в следующем.
На каждом шаге вводятся два этапа, использующих многошаговые
методы:

1) с помощью явного метода (**предиктора**) по известным значениям
функции в предыдущих узлах находится начальное приближение
$𝑦_{𝑖+1} = 𝑦_{𝑖+1}^{(0)}$
в новом узле.

2) используя неявный метод (**корректор**), в результате итераций
находятся приближения $𝑦_{𝑖+1}^{(1)}, 𝑦_{𝑖+1}^{(2)}, ...$


К методам «предиктор-корректор» относится, например, метод Эйлера – Коши, где мы вычисляем

$y_{i+1}^{(0)} = y_i + h \cdot f(x_i, y_i)$

начальное приближение, с помощью явного метода – Эйлера (предиктор), затем

$y_{i+1}^{(1)} = y_i + h \cdot \cfrac{f(x_i, y_i) + f(x_{i+1}, y_{i+1}^{(0)})}{2}$

– следующее приближение значения функции $y_{i+1}$ в $x_{i+1}$-ой точке, $y_{i+1}^{(1)}$(корректор).


Один из вариантов метода прогноза и
коррекции может быть получен на основе
метода Адамса четвертого порядка:

на этапе предиктора
$y_{i+1} = y_i + \frac{h}{24}(55f_i - 59f_{i-1} + 37f_{i-2} - 9f_{i-3})$

на этапе корректора
$y_{i+1} = y_i + \frac{h}{24}(9f_{i+1} + 19f_i - 5f_{i-1} + f_{i-2})$

Явная схема используется на каждом шаге
один раз, а с помощью неявной схемы
строится итерационный процесс вычисления
$y_{i+1}$
, поскольку это значение входит в правую часть выражения $f_{i+1} = f(x_{i+1},
y_{i+1})$. Расчет по этому методу может быть начат только со значения y4
.
Необходимые при этом y1
, y2
, y3 находятся по методу Рунге-Кутта, y0
задается начальным условием.''')
    
    
def q17_th(): 
    print('''
    $\textbf{Метод Эйлера}$ — это один из самых простых методов численного решения обыкновенных дифференциальных уравнений (ОДУ). Он основан на аппроксимации решения с использованием касательной к графику функции и позволяет шаг за шагом приближённо вычислять значение функции.

**Формулировка метода**

Рассмотрим задачу Коши для ОДУ первого порядка:

$\frac{dy}{dx} = f(x,y), \space \space \space \space  y(x_0) = y_0$

Метод Эйлера позволяет найти приближённое значение y в следующей точке $x_{n+1} = x_n+h(h-шаг)$ по формуле:

$y_{n+1} = y_n+h \cdot f(x_n, y_n)$,

где $y_n$ - приближенное значение функции в точке $x_n$

Геометрическая интерпретация
Метод Эйлера можно рассматривать как последовательное построение касательных к кривой $y= y(x)$. На каждом шаге рассчитывается наклон касательной (то есть значение производной $f(x,y))$, и вдоль этой касательной проводится линейное приближение на длину шага $h$.

**Плюсы метода Эйлера**

1) $\it\text{Простота реализации}$:

Метод легко реализовать программно, он не требует сложных вычислений.

2) $\it\text{Интуитивная понятность}$:

Метод основан на простых геометрических и алгебраических принципах.


**Минусы метода Эйлера**

1) $\it\text{Низкая точность}$:

Ошибка метода Эйлера имеет порядок $O(h)$, что означает, что точность решения сильно зависит от величины шага $h$. Для достижения приемлемой точности шаг должен быть очень маленьким, что увеличивает количество вычислений.

2) $\it\text{Накопление ошибок}$:

Поскольку метод основан на последовательных шагах, ошибки на каждом шаге суммируются, что приводит к значительному отклонению от истинного решения.''')
def q16_th(): 
    print('''
    $\textbf{Метод центральной разности}$ — это численный метод для приближённого вычисления производной функции. Он используется, когда аналитическое нахождение производной либо невозможно, либо затруднено.

**Плюсы метода:**

1) $\it\text{Более высокая точность}$:

По сравнению с методами односторонних разностей (прямой и обратной), метод центральной разности обладает более высокой точностью, поскольку ошибка аппроксимации составляет $𝑂(h^2)$, тогда как в методах односторонних разностей —  $𝑂(h)$

2) $\it\text{Cимметричность}$:

Метод симметричен относительно точки
𝑥, что делает его более устойчивым и точным для гладких функций.






**Минусы метода:**

1) $\it\text{Невозможность вычисления на краях интервала}$:

Если требуется вычислить производную на границе заданного интервала, метод центральной разности использовать нельзя, поскольку он требует значений функции с обеих сторон от точки 𝑥.

2) $\it\text{Чувствительность к шагу ℎ}$:

Слишком маленький шаг может привести к накоплению ошибок округления, а слишком большой шаг уменьшает точность аппроксимации.''')
def q15_th(): 
    print('''
    **Локальные ошибки** - погрешности, образовавшиеся на каждом шаге (разница между точным и вычисленным значением на каждом шаге) = невязка метода

**Глобальные ошибки (накопленные)** - погрешности, образовавшиеся за $n$ шагов

Порядок глобальной погрешности относительно шага интегрирования на единицу ниже, чем порядок локальной погрешности. Таким образом, глобальная ошибка метода Эйлера есть  $O(h)$, т. е. данный метод имеет первый порядок. Иными словами, размер шага и ошибка для метода Эйлера связаны линейно. Практическим следствием этого факта является ожидание того, что при уменьшении приближенное решение будет все более точным и при стремлении к нулю будет стремиться к точному решению с линейной скоростью ; т.е. ожидаем, что при уменьшении шага вдвое ошибка уменьшится примерно в два раза.

Порядок численного метода для решения ОДУ определяется порядком его глобальной погрешности. Он может быть также опрделён, как количество вычислений значения производной $f(x, y)$ искомой ф-ии на каждом шаге. В соответствии с этим метод Эйлера является методом первого порядка.

для методов Рунге-Кутты глобальная ошибка — $O(h^p)$, где $p$ зависит от порядка метода (например, для метода Рунге-Кутты 4-го порядка — это $O(h^4))$''')
    
    
    
def q14_th(): 
    print('''
    Обыкновенные дифференциальные уравнения (оду) - ур-я, содержащие одну или несколько производных от искомой ф-и:

$F(x,y, y^,, y^{,,}, ..., y^{(n)}) = 0$

x - независимая переменная, y = y(x) - искомая ф-я

Наисвысший порядок производной n, входящей в предыдущее уравнение, называют порядком дифференциального ур-я

Рассмотрим с-му ОДУ первого порядка, записанную в виде:

$y^{'} (x) = f(x, y(x))$

Решение: любая ф-я y(x), которая удовлетворяет ур-ю. Решением ОДУ на интервале (a,b) называется ф-я $y = Φ(x)$, которая при её подстановке в исходное уравнение обращает его в тождество на (a, b)

Решение ОДУ в неявном виде $\Phi (x, y) = 0$ называется интегралом ОДУ

Существует мн-во возможных решенийю Для одного уникального решения необходимо указать независимые условия (для с-мы размером n)

Например, когда n условий заданы для одной точки.

$y(0) = y_0$

Это задача Коши (задача с начальными условиями). Либо дифференциальная задача''')
    
    
def q13_th(): 
    print('''
    **Определение разреженных матриц**

* Разреженные матрицы – это матрицы, такие что количество ненулевых элементов в них существенно меньше общего числа элементов в матрице.

* Из-за этого вы можете выполнять базовые операции линейной алгебры (прежде всего решать линейные системы) гораздо быстрее по сравнению с использованием плотных матриц.


**Приложения разреженных матриц**
Разреженные матрицы возникают в следующих областях:

* математическое моделирование и решение уравнений в частных производных
* обработка графов(графы представляют в виде матриц смежности, которые чаще всего разрежены
), например анализ социальных сетей
* рекомендательные системы
* в целом там, где отношения между объектами "разрежены"

**Хранение разреженных матриц**

1. $\it\text{COO (координатный формат)}$
* Простейший формат хранения разреженной матрицы – координатный.
* В этом формате разреженная матрица – это набор индексов и значений в этих индексах -> $i, j, val$
где $i, j$ массивы индексов, $val$ массив элементов матрицы.
* Таким образом, нам нужно хранить $ 3\cdot nnz$ элементов, где $nnz$ обозначает число ненулевых элементов в матрице.

  $\it{Недостатки}:$
  * Он неоптимален по памяти
  * Он неоптимален для умножения матрицы на вектор
  * Он неоптимален для удаления элемента
  Первые два недостатка решены в формате CSR.

2. $\it\text{CSR - Compressed sparse row}$

  В формате CSR матрица хранится также с помощью трёх массивов, но других: $ia, ja, sa$, где:
  * $ia$ (начало строк) массив целых чисел длины
  * $ja$ (индексы столбцов) массив целых чисел длины $nnz$
  * sa (элементы матрицы) массив действительных чисел длины $nnz$

  Всего необходимо хранить $2 \cdot nnz + n + 1$
 элементов.

3. $\it\text{LIL (список списков)}$

4. $\it\text{CSC (compressed sparse column)}$
5. $\it\text{блочные варианты}$

В scipy представлены конструкторы для каждого из этих форматов, например

scipy.sparse.lil_matrix(A).

**Прямые методы для решения больших разреженных систем:**
(прямые методы - численные методы, которые находят точное решение систем линейных уравнений вида Ax=b)
* LU разложение (Для разреженных матриц часто используют модифицированные алгоритмы LU-разложения, которые минимизируют заполнение(добавление новых ненулевых элементов в ходе вычислений) с помощью перестановок строк и столбцов)
* Различные методы переупорядочивания для минимизации заполнения факторов''')
    
    
    
def q12_th(): 
    print('''
    **Метод разделяй и властвуй** вычисления собственных значений и векторов трёхдиагональной матрицы - наиболее быстрый из существующих методов вычисления всех собственных значений и собственных векторов трехдиагональной матрицы, начиная с порядка n, который примерно равен 26. (Точное значение этого порогового порядка в конкретном случае зависит от компьютера.)
Пусть у нас есть трёхдиагональная матрица и мы разделили её на блоки:

   $$
      T = \begin{pmatrix}
      T_1 & B  \\
      B^T & T_2
      \end{pmatrix}
  $$

Можем записать матрицу $T$ в виде

   $$
      T = \begin{pmatrix}
      T_1 & B  \\
      B^T & T_2
      \end{pmatrix} + \rho vv^*
  $$

где $v^*$ – эрмитово-сопряжённый вектор, $v = (0, ..., 0, 1, 1, 0, ..., 0)^T$

Пусть мы уже разложили матрицы $T_1$ и $T_2$:

$T_1 = Q_1 Ʌ_1 Q^*_1$

$T_2 = Q_2 Ʌ_2 Q^*_2$


Тогда (проверьте!),

   $$
       \begin{pmatrix}
      Q_1^* & 0  \\
      0 & Q_2^*
      \end{pmatrix} T    
      \begin{pmatrix}
      Q_1^* & 0  \\
      0 & Q_2^*
      \end{pmatrix} = D + \rho uu^*
  $$  
  
  $$
      D = \begin{pmatrix}
      Ʌ_1 & 0  \\
      0 & Ʌ_2
      \end{pmatrix}
  $$

то есть мы свели задачу к задаче вычисления собственных значений у матрицы вида "диагональная матрица плюс матрица малого ранга"

**Матрица вида диагональная матрица плюс матрица малого ранга**

Собственные значения матрицы вида $D + \rho uu^*$ вычислить не просто.
Характеристический многочлен имеет вид

$det(D + \rho uu^* - \lambda I) = det(D - \lambda I) det (I + \rho (D - \lambda I)^{-1}uu^*) = 0$

Тогда:

$det(I + \rho (D - \lambda I)^{-1}uu^*) = 1 + \rho \sum_{i=1}^n \frac{|u_i|^2}{d_i - \lambda} = 0$

**Характеристическое уравнение**

$1 + \rho \sum_{i=1}^n \frac{|u_i|^2}{d_i - \lambda} = 0$''')
    
def q11_th(): 
    print('''
    **Сходимость QR алгоритма**

Если у нас есть разложение вида:  
$$A = X \Lambda X^{-1}, \quad A = \begin{bmatrix} A_{11} & A_{12} \\ A_{21} & A_{22} \end{bmatrix} $$  

и  
$$
\Lambda = \begin{bmatrix} \Lambda_1 & 0 \\ 0 & \Lambda_2 \end{bmatrix},  
\quad \lambda(\Lambda_1) = \{\lambda_1, \dots, \lambda_m\},  
\quad \lambda(\Lambda_2) = \{\lambda_{m+1}, \dots, \lambda_r\},
$$

а также есть зазор между собственными значениями в матрицах $ \Lambda_1 $ и  $ \Lambda_2 $:  
$$
|\lambda_1| \geq \dots \geq |\lambda_m| > |\lambda_{m+1}| \geq \dots \geq |\lambda_r| > 0,
$$

тогда блок $ A_{21}^{(k)} $ матрицы $ A_k $ сходится к нулевому в процессе работы QR алгоритма со скоростью  
$$
\|A_{21}^{(k)}\| \leq Cq^k, \quad q = \left| \frac{\lambda_{m+1}}{\lambda_m} \right|,
$$
где $ m $ — размер матрицы $ \Lambda_1 $.  

Таким образом, нам нужно увеличить зазор между $ \Lambda_1 $ и $ \Lambda_2 $. Это можно сделать с помощью **QR алгоритма со сдвигами**.

QR-алгоритм со сдвигами – это модификация базового QR-алгоритма, которая ускоряет его сходимость. В ней вводится сдвиг $s_k$
 , чтобы быстрее выделить собственные значения матрицы.

**QR алгоритм со сдвигами**

$A_k - s_kI = Q_kR_k$

$A_{k+1} = R_kQ_k+s_kI$

Сходимость такого алгоритма линейная с фактором $$\big|\frac{\lambda_{m+1} - s_k}{\lambda_m - s_k}\big|$$

где $\lambda_m$– $m$-ое большее по модулю собственное значение. Если сдвиг близок к собственному вектору, сходимость более быстрая - становится почти квадратичной

* Существуют различные стратегии выбора сдвигов.

* Использование сдвигов – это общий подход к ускорению сходимости итерационных методов вычисления собственных значений.''')
    
    
def q10_th(): 
    print('''
    **Спектр** — это спектр линейного оператора, который представляет собой множество собственных значений оператора.

**Псевдоспектр** матрицы $A$ — это обобщение спектра, которое учитывает влияние малых возмущений на собственные значения. Он определяется как множество комплексных чисел $\lambda$, для которых матрица $(A−\lambda I)$ становится почти вырожденной, то есть:
$$||(A−λI)^{-1}||\ge \frac{1}{\epsilon}$$

для некоторого малого
$\epsilon>0$, где $||\cdot||$ — операторная норма.

* Для динамических систем с матрицей $A$, спектр может много сообщить о поведении системы (например, о её устойчивости)

* Однако для не нормальных матриц, спектр может быть неустойчивым относительно малых возмущений матрицы

* Для измерения подобных возмущений было разработана концепция псевдоспектра.

Рассмотрим объединение всех возможных собственных значений для всевозможных возмущений матрицы $A$.

$$\Lambda_{\epsilon}(A) = \{ \lambda \in \mathbb{C}: \exists E, x \ne 0: (A + E) x = \lambda x, \quad \Vert E \Vert_2 \leq \epsilon. \}$$

Для малых $E$ и нормальных $A$ это круги вокруг собственных значений, для не нормальных матриц, структура может сильно отличаться.''')

def q9_th(): 
    print('''
    **Определение.** Нормальная матрица — это квадратная матрица $A$, которая коммутирует со своей эрмитово-сопряжённой матрицей $
A^*$, то есть матрица $A$ нормальная, если
$$ AA^* = A^* A. $$

**Нормальные матрицы**

**Теорема**: $A$ – **нормальная матрица**, тогда и только тогда, когда существует такая унитарная матрица $U$, что $$A = U \Lambda U^*$$, где $\Lambda$-диагональная матрица, содержащая собственные значения матрицы $A$ на диагонали.

**Важное следствие**
Любая нормальная матрица – **унитарно диагонализуема**. Это означает, что она может быть приведена к диагональному виду с помощью унитарной матрицы $U$. Другими словами, каждая нормальная матрица имеет ортогональный базис из собственных векторов.

**Эрмитова** (или самосопряжённая) ма́трица — квадратная матрица, элементы которой являются комплексными числами, и которая, будучи транспонирована, равна комплексно сопряжённой:
$A^T = \overline{A}$. То есть для любого столбца $i$ и строки $j$ справедливо равенство $a_{ij} = \overline{a_{ji}}$ где $\overline{a}$— комплексно сопряжённое число к $a$, или $A = (\overline{A})^T = A^*$,
где * — эрмитово сопряжение. То есть эрмитова матрица — это квадратная матрица, которая равна своей эрмитово-сопряжённой матрице.

**Эрмитово - сопряженная матрица(сопряженно-транспонированная)** - матрица $A^*$ с комплексными элементами, полученная из исходной матрицы $A$ транспонированием и заменой каждого эелемента комплексно-сопряженным ему.

Пример:

$$\begin{equation*}
A =
\begin{pmatrix}
3 & 2+i\\
2 - i & 1\\
\end{pmatrix}
\end{equation*}$$

$$\begin{equation*}
A^* =
\begin{pmatrix}
3 & 2+2i\\
2-i & 1
\\
\end{pmatrix}
\end{equation*}$$

**Унитарно - диагонализуемые матрицы**: матрица $A$ унитарно - диагонализуемая, если сущетвует унитарная матрица $U$ такая, что $U^*AU$ - диагональная матрица.

(Унитарная матрица - квадратная матрица с комплексными элементами, результат умножения которой на эрмитово - сопряженную равен единичной матрице $U^*U = UU^* = I$. Иначе говоря, матрица унитарна тогда и т.т., когда существует обратная к ней матрица, удовлетворяющая условию $U^{-1} = U^*$)

**Верхне-гессенбергова форма матрицы**
Матрица $A$ имеет верхне-гессенбергову форму, если $$a_{ij} = 0, при \space i\geq j+2.$$

$$H =
\begin{bmatrix}
* & * & * & * & * \\
* & * & * & * & * \\
0 & * & * & * & * \\  
0 & 0 & * & * & * \\
0 & 0 & 0 & * & *  
\end{bmatrix}
$$


**Приведение произвольной матрицы к верхне-гессенберговой форме**

С помощью отражений Хаусхолдера можно привести любую матрицу к верхне-гессенберговой форме:
$$U^*AU = H$$

* Единственное отличие от вычисления разложения Шура заключается в занулении последних $n-2, n-3,...$
 элементов в первом, втором и так далее столбцах

* Сложность такого приведения $O(n^3)$ операций

* Если матрица приведена к верхне-гессенберговой форме, то одна итерация QR алгоритма имеет сложность
$O(n^2)$ операций (например, используя вращения Гивенса)

* Также верхне-гессенбергова форма матрицы сохраняется после выполнения одной итерации QR алгоритма.


вся теория

**Определение.** Нормальная матрица — это квадратная матрица $A$, которая коммутирует со своей эрмитово-сопряжённой матрицей $
A^*$, то есть матрица $A$ нормальная, если
$$ AA^* = A^* A. $$

**Нормальные матрицы**

**Теорема**: $A$ – **нормальная матрица**, тогда и только тогда, когда существует такая унитарная матрица $U$, что $$A = U \Lambda U^*$$, где $\Lambda$-диагональная матрица, содержащая собственные значения матрицы $A$ на диагонали.

**Важное следствие**
Любая нормальная матрица – **унитарно диагонализуема**. Это означает, что она может быть приведена к диагональному виду с помощью унитарной матрицы $U$. Другими словами, каждая нормальная матрица имеет ортогональный базис из собственных векторов.

-----
**Эрмитова** (или самосопряжённая) ма́трица — квадратная матрица, элементы которой являются комплексными числами, и которая, будучи транспонирована, равна комплексно сопряжённой:
$A^T = \overline{A}$. То есть для любого столбца $i$ и строки $j$ справедливо равенство $a_{ij} = \overline{a_{ji}}$ где $\overline{a}$— комплексно сопряжённое число к $a$, или $A = (\overline{A})^T = A^*$,
где * — эрмитово сопряжение. То есть эрмитова матрица — это квадратная матрица, которая равна своей эрмитово-сопряжённой матрице.

**Эрмитово - сопряженная матрица(сопряженно-транспонированная)** - матрица $A^*$ с комплексными элементами, полученная из исходной матрицы $A$ транспонированием и заменой каждого эелемента комплексно-сопряженным ему.

Пример:

$$\begin{equation*}
A =
\begin{pmatrix}
3 & 2+i\\
2 - i & 1\\
\end{pmatrix}
\end{equation*}$$

$$\begin{equation*}
A^* =
\begin{pmatrix}
3 & 2+2i\\
2-i & 1
\\
\end{pmatrix}
\end{equation*}$$

-----
**Унитарно - диагонализуемые матрицы**: матрица $A$ унитарно - диагонализуемая, если сущетвует унитарная матрица $U$ такая, что $U^*AU$ - диагональная матрица.

(Унитарная матрица - квадратная матрица с комплексными элементами, результат умножения которой на эрмитово - сопряженную равен единичной матрице $U^*U = UU^* = I$. Иначе говоря, матрица унитарна тогда и т.т., когда существует обратная к ней матрица, удовлетворяющая условию $U^{-1} = U^*$)

----
**Верхне-гессенбергова форма матрицы**
Матрица $A$ имеет верхне-гессенбергову форму, если $$a_{ij} = 0, при \space i\geq j+2.$$

$$H =
\begin{bmatrix}
* & * & * & * & * \\
* & * & * & * & * \\
0 & * & * & * & * \\  
0 & 0 & * & * & * \\
0 & 0 & 0 & * & *  
\end{bmatrix}
$$


**Приведение произвольной матрицы к верхне-гессенберговой форме**

С помощью отражений Хаусхолдера можно привести любую матрицу к верхне-гессенберговой форме:
$$U^*AU = H$$

* Единственное отличие от вычисления разложения Шура заключается в занулении последних $n-2, n-3,...$
 элементов в первом, втором и так далее столбцах

* Сложность такого приведения $O(n^3)$ операций

* Если матрица приведена к верхне-гессенберговой форме, то одна итерация QR алгоритма имеет сложность
$O(n^2)$ операций (например, используя вращения Гивенса)

* Также верхне-гессенбергова форма матрицы сохраняется после выполнения одной итерации QR алгоритма.''')
    
    
def q8_th(): 
    print('''
    $\LargeТеорема\spaceШура$


**Теорема:** Пусть матрица $A \in \mathbb{C}^{n \times n}$. ТОгда существует матрица $U$ унитарная и матрица $T$ верхнетреугольная такие, что $$T = U^*AU$$

$A = UTU^* - $разложение Шура

**Набросок доказательства**.
1. Каждая матрица имеет как минимум один ненулевой собственный вектор (для корня характеристического многочлена матрица $(A-\lambda I)$ вырождена и имеет нетривиальное ядро). Пусть

$$Av_1 = \lambda_1 v_1, \quad \Vert v_1 \Vert_2 = 1.$$

2. Пусть $U_1 = [v_1,v_2,\dots,v_n]$, где $v_2,\dots, v_n$ любые векторы ортогональные $v_1$. Тогда
  
  $$
      U^*_1 A U_1 = \begin{pmatrix}
      \lambda_1 & *  \\
      0 & A_2
      \end{pmatrix},
  $$
  
  где $A_2$ матрица размера $(n-1) \times (n-1)$. Это называется **блочнотреугольной формой**. Теперь мы можем проделать аналогичную процедуру для матрицы $A_2$ и так далее.  
  
  
**Замечание**: Поскольку в доказательстве необходимы собственные векторы, оно не является практичным алгоритмом.

**Приложение теоремы Шура**

Важное приложение теоремы Шура связано с так называемыми **нормальными матрицами**.  

**Определение.** Матрица $A$ называется **нормальной матрицей**, если  

$$ AA^* = A^* A. $$

**Q:** Какие примеры нормальных матриц вы можете привести?

Примеры: эрмитовы матрицы, унитарные матрицы.

$\LargeРазложение\spaceШура$
- Нужно найти унитарную матрицу $U$ и верхнетреугольную матрицу $T$, такие что для данной матрице $A$ выполнено

$$ A = U T U^*. $$

- <font color='red'> **Не путайте** QR алгоритм и QR разложение! </font>

- QR разложение – это представление матрицы в виде произведения двух матриц, а QR алгоритм использует QR разложение для вычисления разложения Шура.

Зачем нужно разложение Шура?

- Численные методы:
Разложение Шура часто используется как основа для численного поиска собственных значений. В частности, QR-алгоритм сводится к нахождению разложения Шура.

- Контроль собственных значений:
Так как разложение Шура даёт матрицу $T$, где на диагонали стоят собственные значения, оно полезно для анализа спектра матрицы.

**Путь к QR алгоритму**

Рассмотрим выражение

$$A = Q T Q^*,$$

и перепишем его в виде

$$
   Q T = A Q.
$$

Слева замечаем QR разложение матрицы $AQ$.

Используем его чтобы записать одну итерацию метода неподвижной точки для разложения Шура.

**Вывод QR алгоритма из уравнения неподвижной точки**

Запишем следующий итерационный процесс

$$
    Q_{k+1} R_{k+1} = A Q_k, \quad Q_{k+1}^* A = R_{k+1} Q^*_k
$$

Введём новую матрицу

$$A_k = Q^* _k A Q_k = Q^*_k Q_{k+1} R_{k+1} = \widehat{Q}_k R_{k+1}$$

тогда аппроксимация для $A_{k+1}$ имеет вид

$$A_{k+1} = Q^*_{k+1} A Q_{k+1} = ( Q_{k+1}^* A = R_{k+1} Q^*_k)  = R_{k+1} \widehat{Q}_k.$$

Итак, мы получили стандартную форму записи QR алгоритма.

Финальные формулы обычно записывают в **QRRQ**-форме:

1. Инициализируем $A_0 = A$.
2. Вычислим QR разложение матрицы $A_k$: $A_k = Q_k R_k$.
3. Обновим аппроксимацию $A_{k+1} = R_k Q_k$.

Продолжаем итерации пока $A_k$ не станет достаточно треугольной (например, норма подматрицы под главной диагональю не станет достаточно мала).

**Что известно о сходимости и сложности**

**Утверждение**

Матрицы $A_k$ унитарно подобны матрице $A$

$$A_k = Q^*_{k-1} A_{k-1} Q_{k-1} = (Q_{k-1} \ldots Q_1)^* A (Q_{k-1} \ldots Q_1)$$

а произведение унитарных матриц – унитарная матрица.

Сложность одной итерации $\mathscr{O}(n^3)$, если используется QR разложение для общего случая.

Мы ожидаем, что $A_k$ будет **очень близка к треугольной матрице** для достаточно большого $k$.''')
    
    
def q7_th(): 
    print('''
    $\textbf{Круги Гершгорина}$

Есть интересная теорема, которая часто помогает локализовать собственные значения.
Она называется $\it\text{теоремой Гершгорина}$.

Она утверждает, что все собственные значения $\lambda_i, i = \overline{1,n}$ находятся внутри объединения кругов Гершгорина $C_i$, где $C_i$– окружность на комплексной плоскости с центром в $a_{ii}$ и радиусом $r_i = \sum_{j \neq i} |a_{ij}|$


Более того, если круги не пересекаются, то они содержат по одному собственному значению внутри каждого круга.


**Доказательство**(на всякий случай)

Сначала покажем, что если матрица $A$ обладает строгим диагональным преобладанием, то есть $$|a_{ii}| > \sum_{j \neq i} |a_{ij}|,$$

тогда такая матрица невырождена.


Разделим диагональную и недиагональную часть и получим $$A = D+S = D(I+D^{-1}S),$$

где $||D^{-1}S||_1 < 1$. Поэтому, в силу теоремы о ряде Неймана, матрица $I + D^{-1}S$ обратима и, следовательно, матрица $A$ также обратима.

Теперь докажем утверждение теоремы от противного:

* если любое из собственных чисел лежит вне всех кругов, то матрица $(A - \lambda I)$ обладает свойством строгого диагонального преобладания
* поэтому она обратима
* это означает, что если $(A - \lambda I)x = 0$, то $x = 0$.''')
    
    
def q6_th():
    print('''
    $\it\textbf{Степенной метод}$

* Часто в вычислительной практике требуется найти не весь спектр, а только некоторую его часть, например самое большое или самое маленькое собственые значения.
* Также отметим, что для Эрмитовых матриц $(A = A^*)$
 собственные значения всегда действительны.

* Степенной метод – простейший метод вычисления $\it\text{максимального по модулю}$ собственного значения. Это также первый пример итерационного метода и Крыловского метода.

**Что необходимо помнить о степенном методе**

* Степенной метод даёт оценку для максимального по модулю собственного числа или спектрального радиуса матрицы
* Одна итерация требует одного умножения матрицы на вектор. Если можно умножить вектор на матрицу зa $O(n)$(например, она разреженная), тогда степенной метод можно использовать для больших $n$
* Сходимость может быть медленной
* Для грубой оценки максимального по модулю собственного значения и соответствующего вектора достаточно небольшого числа итераций

**Степенной метод: вид**

Задача на собственые значения $$Ax = \lambda x, ||x||_2 = 1 \text{(для устройчивости)}$$

может быть записана как итерации с неподвижной точкой, которые называются $\it\text{степенным методом}$ и дают максимальное по модулю собственное значение матрицы $A$.

Степенной метод имеет вид
$$x_{k+1} = Ax_k, x_{k+1} := \frac{x_{k+1}}{||x_{k+1}||_2}$$
и $x_{k+1} → v_1$, где $Av_1 = \lambda_1v_1 $ и $\lambda_1$ максимальное по модулю собственное значение, и $v_1$ – соответствующий собственный вектор.

На $(k+1)$-ой итерации приближение для $\lambda_1$ может быть найдено следующим образом $$\lambda^{k+1} = (Ax_{k+1}, x_{k+1})$$

Заметим, что $\lambda^{(k+1)}$ не требуется для $(k+2)$-ой итерации, но может быть полезно для оценки ошибки на каждой итерации: $||Ax_{k+1} - \lambda^{(k+1)}x_{k+1}||$
.

Метод сходится со скоростью геометричекой прогрессии, с константой $q = |\frac{\lambda_2}{\lambda_1}| < 1$, где $\lambda_1 > \lambda_2 \geq ... \geq \lambda_n$
. Это означает, что сходимость может быть сколь угодно медленной при близких значениях у $\lambda_1$ и $\lambda_2$.

**Общая сложность степенного метода**

Пусть $k$ — число итераций, необходимых для достижения заданной точности $ε$. Тогда общая сложность метода будет равна:
$O(k⋅n^2)$''')
    
def q5_th():
    print('''
    $\LargeРазложение\spaceШура$
- Нужно найти унитарную матрицу $U$ и верхнетреугольную матрицу $T$, такие что для данной матрице $A$ выполнено

$$ A = U T U^*. $$
  * Собственные значения матрицы $A$ находятся на диагонали матрицы $T$.

 **Не путайте** QR алгоритм и QR разложение!

- QR разложение – это представление матрицы в виде произведения двух матриц, а QR алгоритм использует QR разложение для вычисления разложения Шура.

**Путь к QR алгоритму**

Рассмотрим выражение

$$A = Q T Q^*,$$

и перепишем его в виде

$$
   Q T = A Q.
$$

Слева замечаем QR разложение матрицы $AQ$.

Используем его чтобы записать одну итерацию метода неподвижной точки для разложения Шура.

**Вывод QR алгоритма из уравнения неподвижной точки**

Запишем следующий итерационный процесс

$$
    Q_{k+1} R_{k+1} = A Q_k, \quad Q_{k+1}^* A = R_{k+1} Q^*_k
$$

Введём новую матрицу

$$A_k = Q^* _k A Q_k = Q^*_k Q_{k+1} R_{k+1} = \widehat{Q}_k R_{k+1}$$

тогда аппроксимация для $A_{k+1}$ имеет вид

$$A_{k+1} = Q^*_{k+1} A Q_{k+1} = ( Q_{k+1}^* A = R_{k+1} Q^*_k)  = R_{k+1} \widehat{Q}_k.$$

Итак, мы получили стандартную форму записи QR алгоритма.

Финальные формулы обычно записывают в **QRRQ**-форме:

1. Инициализируем $A_0 = A$.
2. Вычислим QR разложение матрицы $A_k$: $A_k = Q_k R_k$.
3. Обновим аппроксимацию $A_{k+1} = R_k Q_k$.

Продолжаем итерации пока $A_k$ не станет достаточно треугольной (например, норма подматрицы под главной диагональю не станет достаточно мала).

**Что известно о сходимости и сложности**

**Утверждение**

Матрицы $A_k$ унитарно подобны матрице $A$

$$A_k = Q^*_{k-1} A_{k-1} Q_{k-1} = (Q_{k-1} \ldots Q_1)^* A (Q_{k-1} \ldots Q_1)$$

а произведение унитарных матриц – унитарная матрица.

Сложность одной итерации $\mathscr{O}(n^3)$, если используется QR разложение для общего случая.

Мы ожидаем, что $A_k$ будет **очень близка к треугольной матрице** для достаточно большого $k$.

**Сходимость и сложность QR алгоритма**

- QR алгоритм сходится от первого диагонального элемента к последнему.

- По крайней мере 2-3 итерации необходимо для определения каждого диагонального элемента матрицы $T$.

- Каждый шаг состоит в вычислении QR разложения и одного произведения двух матриц, в результате имеем сложность $\mathscr{O}(n^3)$.

**Q**: означает ли это итоговую сложность $\mathscr{O}(n^4)$?

**A**: к счастью, нет!

- Мы можем ускорить QR алгоритм, используя сдвиги, поскольку матрица $A_k - \lambda I$ имеет те же векторы Шура (столбцы матрицы $U$).''')
    
def q4_th():
    print('''
    Что такое собственный вектор?

**Определение**. Вектор $x \neq 0$ называется собственным для квадратной матрицы A, если найдётся такое число $\lambda$, что $$Ax = \lambda x$$


Число $\lambda$ называется $\it{собственным}$ значением.

Так как матрица $A - \lambda I$ должна иметь нетривиальное ядро (что такое ядро?), собственные значения являются корнями характеристического полинома $$det(A - \lambda I) = 0$$

**Важность**

$\it\text{Собственные значения – это частоты выбраций}$

Обычно вычисление собственных значений и собственных векторов необходимо для изучения:

* вибраций в механических структурах
* снижения сложности моделей сложных систем

**Для чего используют:**

1. Упрощение сложных преобразований
- Собственные векторы и собственные значения помогают разложить сложные преобразования на простые части. Например, поворот, масштабирование или сжатие в каком-то направлении проще понять, если выделить направления (собственные векторы), которые остаются неизменными.

2. Диагонализация матриц
- Собственные векторы и значения используются для представления матрицы в более удобной форме — диагональной. Это важно, потому что:

  - Вычисления с диагональными матрицами (например, возведение в степень) намного проще.
  - Это позволяет изучать матрицу с минимальными усилиями.

3. Машинное обучение и анализ данных

- PCA (метод главных компонент): Собственные векторы помогают найти главные направления в данных, чтобы снизить размерность и оставить только важные признаки.
- Кластеризация: Собственные значения используются в алгоритмах, таких как спектральная кластеризация.

4. Дифференциальные уравнения

- Собственные значения и векторы упрощают решение линейных дифференциальных уравнений, которые описывают многие явления в природе и технике.

**Google PageRank**

Одна из самых известных задач, сводящихся к вычислению собственного вектора, – это задача вычисления Google PageRank.

* Задача состои в ранжировании веб-страницы: какие из них являются важными, а какие нет
* В интернете страницы ссылаются друг на друга
* PageRank определяется рекурсивно.

  Обозначим $p_i$ за важность $i$-ой страницы. Тогда определим эту важность как усреднённую важность всех страниц, которые ссылаются на данную страницу. Это определение приводит к следующей линейной системе $$p_i = \sum_{j \in N(i)}\frac{p_j}{L(j)},$$



  где

  * $L(j)$ – число исходящих ссылок с $j$-ой страницы,
  * $N(i)$– число соседей $i$-ой страницы.

  Это может быть записано следующим образом $$p = Gp,   G_{ij} = \frac{1}{L(j)}$$

  

  или как задача на собственные значения $$Gp = 1p$$


  то есть мы уже знаем, что у матрицы $G$ есть собственное значение равное $1$. Заметим, что $G$ – левостохастичная матрица, то есть сумма в каждом столбце равна $1$.''')
    
def q3_th():
    print('''
    Алгоритм Штрассена — это эффективный алгоритм умножения квадратных матриц, снижающий сложность с $O(n^3)$ до $O(n^{log_27}) \approx O(n^{2.81})$. В стандартном методе умножения матриц используется 8 умножений подматриц, что приводит к сложности  $O(n^3)$. Алгоритм Штрассена заменяет 8 умножений на 7,поэтому сложность становится равной  $O(n^{log_27})$



Метод Штрассена становится быстрее наивного алгоритма, если

$$2n^3>7n^{log_27},$$ $$n>667$$

классическое понятие сходимости, как его применяют, например, к итерационным методам или методам численного интегрирования, напрямую нельзя применить к методу Штрассена, поскольку это не итерационный метод, а детерминированный алгоритм, который выполняет конечное число операций и всегда возвращает определённый результат.

Почему классическое понятие сходимости неприменимо?
* Отсутствие итеративности
  Сходимость обычно анализируют в контексте методов, которые последовательно приближаются к решению через итерации. В методе Штрассена нет итераций — он разово применяет набор рекурсивных операций для вычисления произведения матриц, поэтому понятие «приближения к решению» здесь неприменимо.

* Детерминированный результат
  Алгоритм Штрассена всегда возвращает точное произведение матриц (при отсутствии ошибок округления). В отличие от итерационных методов, он не генерирует последовательность приближений, которая может стремиться к точному решению.


Очевидный способ вычисления правой стороны — просто сделать 8 умножений и 4 сложения. Но представьте, что умножения намного дороже сложений, поэтому мы хотим уменьшить количество умножений, если это вообще возможно. Штрассен использует трюк, чтобы вычислить правую сторону с одним умножением меньше и намного большим количеством сложений (и нескольких вычитаний).

Вот 7 умножений (пока это просто хитрые умножения, тут можно не искать логику):

$
M1 = (A + D) * (E + H) = AE + AH + DE + DH \\
M2 = (C + D) * E = CE + DE \\
M3 = A * (F - H) = AF - AH \\
M4 = D * (G - E) = DG - DE \\
M5 = (A + B) * H = AH + BH \\
M6 = (C - A) * (E + F) = CE + CF - AE - AF \\
M7 = (B - D) * (G + H) = BG + BH - DG - DH \\
$


Теперь сделаем несколько простых сложений и умножений.

Для AE+BG:
1. Итак, чтобы вычислить AE+BG, начнем с M1+M7 (что дает нам члены AE и BG)
$$M1 + M7 = (AE + AH + DE + DH) + (BG + BH - DG - DH)$$
$$M1 + M7 = AE + AH + DE + BG + BH - DG$$
$$M1 + M7 = AE + BG + AH + DE  + BH - DG$$
$$M1 + M7 = (AE + BG) + (AH + DE  + BH - DG)$$
2. затем прибавим/вычтем некоторые другие M, пока AE+BG не останется всем.
$$M1 + M7 + M4 = (AE + BG) + (AH + DE  + BH - DG) + (DG - DE)$$
$$M1 + M7 + M4 = (AE + BG) + (AH + BH)$$
$$M1 + M7 + M4 - M5 = (AE + BG) + (AH + BH) - (AH + BH)$$
$$M1 + M7 + M4 - M5 = (AE + BG)$$
Чудесным образом M выбираются так, что $M1+M7+M4-M5$ работает. То же самое с другими тремя требуемыми результатами.

Для AF+BH:
$$M3 + M5 = (AF - AH) + (AH + BH)$$
$$M3 + M5 = AF + BH - AH + AH$$
$$M3 + M5 = AF + BH$$

Для CE+DG:
$$M2 + M4 = (CE + DE) + (DG - DE)$$
$$M2 + M4 = CE + DG + DE - DE$$
$$M2 + M4 = CE + DG$$

Для CF+DH:
$$M1 - M2 = (AE + AH + DE + DH) - (CE + DE)$$
$$M1 - M2 = AE + AH + DE + DH - CE - DE$$
$$M1 - M2 = AE + AH + DH - CE + DE - DE$$
$$M1 - M2 = AE + AH + DH - CE$$

$$M1 - M2 + M3 = (AE + AH + DH - CE) + (AF - AH)$$
$$M1 - M2 + M3 = AE + AH + DH - CE + AF - AH$$
$$M1 - M2 + M3 = AE + DH - CE + AF + AH - AH$$
$$M1 - M2 + M3 = AE + DH - CE + AF$$

$$M1 - M2 + M3 + M6 = (AE + DH - CE + AF) + (CE + CF - AE - AF)$$
$$M1 - M2 + M3 + M6 = AE + DH - CE + AF + CE + CF - AE - AF$$
$$M1 - M2 + M3 + M6 = DH + CF + AE - AE - CE + CE + AF - AF$$
$$M1 - M2 + M3 + M6 = DH + CF$$

Теперь просто надо понять, что это работает не только для матриц 2x2, но и для любых (четных) матриц. При этом мы рекурсивно уменьшаем каждую матрицу.
''')

def q1_th():
    print('''**Определение**. Произведение матрицы $A$ размера $n×k$ и матрицы $B$ размера $k×m$– это матрица $C$ размера $n×m$ такая что её элементы записываются как $$c_{ij}=∑_{s=1}^{k}a_{is}b_{sj},i=1,…,n,j=1,…,m$$

Для $m=k=n$ сложность наивного алгоритма составляет $2n^3−n^2=O(n^3)$:

Почему рукописная(наивная) реализация такая медленная?

1) не используется параллелилизм

2) не используются преимущества быстрой памяти, в целом архитектуры памяти

**Определение**. Произведение матрицы $A$ размера $n×k$ и вектора $B$ размера $1×k$– это вектор $C$ длины $n$, такой, что его элементы записываются как $$c_{i}=∑_{j=1}^{k}a_{ij}b_{j},i=1,…,n$$''')
    
def q1():
    print('''def matmul(a, b): #наивное перемножение матриц
        n = a.shape[0]
        k = a.shape[1]
        m = b.shape[1]
        c = np.zeros((n, m))
        for i in range(n):
            for j in range(m):
                for s in range(k):
                    c[i, j] += a[i, s] * b[s, j]
        return c


    def mat_vec_mult(matrix, vector): # Наивное перемножение матрицы на вектор
        num_rows = len(matrix)
        num_cols = len(matrix[0])
        result = [0] * num_rows

        for i in range(num_rows):
            for j in range(num_cols):
                result[i] += matrix[i,j] * vector[j]

        return result


    mat_vec_mult(np.array([[1,2],[2,3],[4,7]]),[4,5]), matmul(np.array([[1,2],[2,3]]),np.array([[1,2],[2,3]]))''')
    
    
def q2():
    print('''
    from collections import OrderedDict

    class LRUCache:
        def __init__(self, capacity: int):
            """
            Инициализация кэша с заданной ёмкостью.
            """
            self.cache = OrderedDict()
            self.capacity = capacity

        def get(self, key: int) -> int:
            """
            Получить значение из кэша по ключу.
            Если ключа нет, вернуть -1.
            """
            if key in self.cache:
                # Переместить используемый элемент в конец (считается недавно использованным)
                self.cache.move_to_end(key)
                return self.cache[key]
            return -1

        def put(self, key: int, value: int):
            """
            Добавить элемент в кэш. Если кэш заполнен, удалить наименее используемый элемент.
            """
            if key in self.cache:
                # Если ключ уже существует, обновить значение и переместить в конец
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                # Удалить первый (наименее недавно использованный) элемент
                self.cache.popitem(last=False)

    # Пример использования
    cache = LRUCache(2)

    # Операции
    cache.put(1, 1)  # Кэш: {1: 1}
    cache.put(2, 2)  # Кэш: {1: 1, 2: 2}
    print(cache.get(1))  # Вернет 1, Кэш: {2: 2, 1: 1}
    cache.put(3, 3)  # Кэш: {1: 1, 3: 3} (удален 2)
    print(cache.get(2))  # Вернет -1 (так как 2 удален)
    cache.put(4, 4)  # Кэш: {3: 3, 4: 4} (удален 1)
    print(cache.get(1))  # Вернет -1
    print(cache.get(3))  # Вернет 3, Кэш: {4: 4, 3: 3}
    print(cache.get(4))  # Вернет 4, Кэш: {3: 3, 4: 4}''')


def q2_th():
    print('''Иерархия памяти — это способ организации различных типов памяти компьютера так, чтобы ускорить работу процессора. Память делится на уровни по скорости доступа и размеру: быстрые уровни маленькие и дорогие, а медленные — большие и дешевые.

**Уровни иерархии:**

**1. Регистр процессора:**

- Самый верхний уровень.
- Находится внутри процессора.
- Скорость: сверхбыстрая, доступ за один такт процессора.
- Объем: крошечный (несколько килобайт).
- Стоимость: очень высокая.

**2. Кэш-память процессора (CPU Cache):**
Состоит из 3 уровней:
- L1 (уровень 1):
  - Самая быстрая и дорогая кэш-память.
  - Очень маленький объем (16–128 КБ).
-L2 (уровень 2):
  - Чуть медленнее, но больше (256 КБ – несколько МБ).
- L3 (уровень 3):
  - Медленнее L1 и L2, общий для всех ядер процессора.
  - Объем до десятков МБ.
- Назначение: хранение данных, часто используемых процессором, для минимизации задержек.

**3. Оперативная память (RAM):**

- Скорость: медленнее кэша, но быстрее SSD.
- Объем: значительно больше (гигабайты).
- Стоимость: относительно дорогая.
- Используется для хранения данных и инструкций программ во время выполнения.

**4. Твердотельные накопители (Solid State Drives):**

- Включают неэнергозависимую флэш-память.
- Скорость: медленнее RAM, но быстрее, чем механические жесткие диски.
- Объем: большие (терабайты).
- Стоимость: средняя.
- Используются для долговременного хранения данных.
- Механические жесткие диски (HDD):

**5. Самый нижний уровень.**
- Скорость: самая медленная.
- Объем: очень большой (терабайты).
- Стоимость: самая низкая.
- Используются для долговременного хранения данных, к которым доступ требуется редко.


**План кеша (Cache Planning)**
Кэш работает как промежуточный буфер между процессором и оперативной памятью для ускорения доступа к часто используемым данным. Процесс организации кэша включает следующие аспекты:

**1. Кэш-линии:**

- Данные организуются в блоки фиксированного размера (обычно 32–128 байт).
- При кэшировании загружается вся кэш-линия, а не только отдельный байт.

**2. Ассоциативность кэша:**

- Определяет, как строки памяти сопоставляются с блоками в кэше.
  - Прямое отображение: каждая строка памяти может храниться только в определенном блоке кэша.
  - Полностью ассоциативный кэш: каждая строка памяти может находиться в любом блоке кэша.
  - N-канальный ассоциативный кэш: компромисс между двумя подходами.
  
**3. Алгоритмы замещения:**

- Когда кэш заполняется, нужно освободить место для новых данных.
- Пример: LRU (Least Recently Used), FIFO (First In, First Out), Random Replacement.


**Алгоритм LRU (Least Recently Used)**
LRU — один из самых распространенных алгоритмов замещения данных в кэше.

**Принцип работы:**

- При кэш-промахе (отсутствие данных в кэше) заменяется тот блок данных, который дольше всех не использовался.
- Данные, к которым был последний доступ, считаются самыми "свежими".

**Реализация:**

- Используется структура данных (обычно связанный список или стек).

**При каждом доступе к данным:**

- Если данные уже в кэше — переместить их в начало списка.
- Если данных нет в кэше:
- Если кэш заполнен, удалить последний элемент списка (самый "старый").
- Добавить новые данные в начало списка.

**Плюсы:**

- Эффективно для данных с локальностью запросов.
- Снижает частоту промахов.

**Минусы:**

Увеличенные затраты на обновление структуры (в худшем случае $\mathscr{O}(n)$)''')
