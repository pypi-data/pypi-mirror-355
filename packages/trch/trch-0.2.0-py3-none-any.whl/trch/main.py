import pyperclip


class ClipboardHelper:
    def __init__(self):
        self.methods_info = {
            # датасеты:
            "activities": "",
            "activities_tf": "",
            "corona": "",
            "news": "",
            "pos": "",
            "jaccard": "",
            "word2vec_ds": "",
            "tweets_disaster": "Обучите одно- и двунаправленную рекуррентную сеть",
            "tweets_disaster_tf": "подход на основе TF-IDF с классическим классификатором",
            "quotes": "классификация через эмбеддинги и последующей классификацией с помощью полносвязной сети.",
            "reviews": "задача регрессии - предсказание оценки отзыва на основе его текста с помощью LSTM.",
            "tweet_cat": "",
            "RNN_gate": "рекуррентная нейронная сеть с гейтами",
            "RNN_sim": "посимвольная генерация текста при помощи RNN",
            "RNN_pred": "RNN предсказание след токена",
            "conv1d_ds": "использование nn.Conv1d на датасете",
            # кастоные реализации (3 задание)
            "word2vec_ns": "",
            "word2vec": "",
            "rnncell": "",
            "rnncell_g": "",
            "conv1d": "",
            "embedding": "",
            "linear": "",
            "relu": "",
            "dropout": "",
            "layernorm": "",
            "mseloss": "",
            "celoss": "",
            "pe": "",
            "gru_custom": "",
            "padtrim_custom": "",
            "attention": "",
            # модели:
            "embed_linear": "",
            "tf": "",
            "rnn": "",
            "gru": "",
            "lstm": "",
            "biLSTM": "",
            "biGRU": "",
            "biRNN": "",
            "seq2seq": ""
        }

    def activities(self):
        code = """
import pandas as pd
df = pd.read_csv('nlp/activities.csv')

texts = df['Text'].tolist()

def preprocess(texts):
    processed = []
    for t in texts:
        processed += [t.lower().split()]
    return processed

processed_text = preprocess(texts)
vocab = {"PAD": 0, "UNK": 1}
idx = 2
for s in processed_text:
    for w in s:
        if w not in vocab.keys():
            vocab[w] = idx
            idx += 1

encoded = []
for s in processed_text:
    encoded += [[vocab.get(i, "UNK") for i in s]]

max_len = max(len(t) for t in encoded)
padded = []
for seq in encoded:
    padded += [seq + [vocab.get("PAD")] * (max_len - len(seq))]

import torch
from sklearn.model_selection import train_test_split

X = torch.tensor(padded)
y_vocab = {"ACTIVITY": 0, "REVIEW": 1}
y = torch.tensor(df['Review-Activity'].map(lambda x: y_vocab[x]).tolist())
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
X_train.shape, y_train.shape

from torch.utils.data import Dataset, DataLoader

class TextDataset(Dataset):
    def __init__(self, X, y):
        super().__init__()
        self.X = X
        self.y = y
        
    def __len__(self):
        return len(self.y)
    
    def __getitem__(self, idx):
        x_tensor = torch.tensor(self.X[idx], dtype=torch.long)
        y_tensor = torch.tensor(self.y[idx], dtype=torch.long)
        return x_tensor, y_tensor

train_ds = TextDataset(X_train, y_train)
test_ds = TextDataset(X_test, y_test)
train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
test_loader = DataLoader(test_ds, batch_size=64, shuffle=False)
x, y = next(iter(test_loader))

class GRUClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size, num_classes):
        super().__init__()
        self.embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim, padding_idx=0)
        self.gru = nn.GRU(input_size=embedding_dim, hidden_size=hidden_size, batch_first=True)
        self.linear = nn.Linear(hidden_size, num_classes)
        
    def forward(self, x):
        emb = self.embed(x)
        out, h = self.gru(emb)
        logits = self.linear(h)
        return logits.squeeze(0)

import torch.optim as optim
vocab_size = len(vocab)
embed_dim = 256
hidden_size = 128
num_classes = 2
model = GRUClassifier(vocab_size, embed_dim, hidden_size, num_classes)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters())

n_epochs = 5
for epoch in range(n_epochs):
    model.train()
    total_loss = 0.
    for xb, yb in train_loader:
        optimizer.zero_grad()
        logits = model(xb)
        loss = criterion(logits, yb)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * xb.size(0)
    avg_loss = total_loss / len(train_ds)
    print(f"Epoch {epoch+1}/{n_epochs}, Loss: {avg_loss:3f}")

from sklearn.metrics import classification_report
model.eval()
all_preds = []
all_labels = []
with torch.no_grad():
    for xb, yb in test_loader:
        logits = model(xb)
        preds = torch.argmax(logits, dim=1)
        all_preds.extend(preds.tolist())
        all_labels.extend(yb.tolist())
print(classification_report(all_labels, all_preds, zero_division=0, target_names=[str(r) for r in y_vocab.keys()]))

inv_vocab = {v: k for k, v in vocab.items()}
inv_vocab_y = {v: k for k, v in y_vocab.items()}

for idx in range(len(X_test)):
    true_label = y_test[idx]
    pred_label = all_preds[idx]
    if true_label == pred_label:
        tokens = [inv_vocab[i.item()] for i in X_test[idx] if i.item() != 0]
        text = " ".join(tokens)
        print(text)
        print(true_label, pred_label)
        break

for idx in range(len(X_test)):
    true_label = y_test[idx]
    pred_label = all_preds[idx]
    
    if true_label != all_preds[idx]:
        tokens = [inv_vocab[i.item()] for i in X_test[idx] if i.item() != 0]
        text = " ".join(tokens)
        print(text)
        print(true_label, pred_label)
        break
"""
        pyperclip.copy(code)

    def activities_tf(self):
        code = """
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
df = pd.read_csv('nlp/activities.csv')
df = df.sample(frac=0.1).reset_index()
texts = df['Text'].tolist()

class_vocab = {'NOT APPLICABLE': 0, 'WINTER': 1, 'FALL': 2, 'SUMMER': 3}
y = df['Season'].map(lambda x: class_vocab[x]).tolist()

vectorizer = TfidfVectorizer(max_features=100)
X = vectorizer.fit_transform(texts)
X = X.toarray()

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

import torch
from torch.utils.data import Dataset, DataLoader

class TfIdfDataset(Dataset):
    def __init__(self, X, y):
        super().__init__()
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)

    def __len__(self):
        return len(self.y)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_ds = TfIdfDataset(X_train, y_train)
test_ds = TfIdfDataset(X_test, y_test)
train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
test_loader = DataLoader(test_ds, batch_size=64, shuffle=False)

import torch.nn as nn
import torch.optim as optim

class TfidfFCClassifier(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_classes):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_classes),
        )
    def forward(self, x):
        return self.fc(x)
    
model = TfidfFCClassifier(X.shape[1], 256, 4)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters())
n_epochs = 5

for epoch in range(n_epochs):
    total_loss = 0.
    for xb, yb in train_loader:
        optimizer.zero_grad()
        logits = model(xb)
        loss = criterion(logits, yb)
        total_loss += loss.item() * xb.size(0)
    avg_loss = total_loss / len(train_ds)
    print(f"Epoch [{epoch+1}/{n_epochs}], Loss: {avg_loss:4f}")

model.eval()
all_labels = []
all_preds = []

for xb, yb in test_loader:
    logits = model(xb)
    preds = torch.argmax(logits, dim=1)
    
    all_preds.extend(preds.tolist())
    all_labels.extend(yb.tolist())
from sklearn.metrics import classification_report
print(classification_report(all_labels, all_preds, zero_division=0, target_names=[i for i in class_vocab.keys()]))
"""
        pyperclip.copy(code)

    def corona(self):
        code = """
import pandas as pd
df = pd.read_csv("nlp/corona.csv")
targets = df['Sentiment'].tolist()
import re
import string
from ftfy import fix_text

texts = df['OriginalTweet'].fillna('').tolist()
processed = []
pattern = r"(?:#\w+|https?://[^\s.,!?;:()\[\]<>]+|www\.[^\s.,!?;:()\[\]<>]+)"

remove_pattern = r"(?:#\w+|https?://\S+|www\.\S+|\.\S+|@\w+)"
translator = str.maketrans('', '', string.punctuation)

for t in texts:
    t_fixed = fix_text(t)
    t_clean = re.sub(remove_pattern, '', t_fixed)
    tokens = t_clean.lower().translate(translator).split()
    processed.append(tokens)

vocab_x = {"PAD": 0, "UNK": 1}
idx = 2
for sent in processed:
    for w in sent:
        if w not in vocab_x.keys():
            vocab_x[w] = idx
            idx += 1

vocab_y = {"Positive": 0, "Negative": 1, "Neutral": 2, "Extremely Positive": 3, "Extremely Negative": 4}
y = [vocab_y[w] for w in targets]

encoded = []
for t in processed:
    encoded += [[vocab_x.get(w, "UNK") for w in t]]
max_len = max(len(s) for s in encoded)
padded = []
for t in encoded:
    padded += [t + [vocab_x.get("PAD")] * (max_len - len(t))]

from sklearn.model_selection import train_test_split
X = padded
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

import torch
from torch.utils.data import Dataset, DataLoader

class CoronaDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.long)
        self.y = torch.tensor(y, dtype=torch.long)
    def __len__(self):
        return len(self.y)
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_ds = CoronaDataset(X_train, y_train)
test_ds = CoronaDataset(X_test, y_test)
train_loader = DataLoader(train_ds, batch_size=16, shuffle=True)
test_loader = DataLoader(test_ds, batch_size=16, shuffle=False)

import torch.nn as nn
class TweetClassifier(nn.Module):
    def __init__(self, vocab_size, emb_dim, hidden_size, num_classes):
        super().__init__()
        self.embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=emb_dim, padding_idx=0)
        self.gru = nn.GRU(input_size=emb_dim, hidden_size=hidden_size, batch_first=True, bidirectional=True)
        self.linear = nn.Linear(hidden_size*2, num_classes)
        
    def forward(self, x):
        emb = self.embed(x)
        out, h = self.gru(emb)
        h_combined = torch.cat([h[0], h[1]],dim=1)
        logits = self.linear(h_combined)
        return logits.squeeze(0)
model = TweetClassifier(len(vocab_x), 128, 256, len(vocab_y))

import torch.optim as optim
import matplotlib.pyplot as plt

criterion = nn.CrossEntropyLoss()
optimizer = optim.AdamW(model.parameters(), weight_decay=0.0001)
num_epochs = 10

loss_history = []
acc_history = []
test_loss_history = []
test_acc_history = []

for epoch in range(num_epochs):
    total_loss = 0.0
    correct = 0
    total = 0

    for xb, yb in train_loader:
        optimizer.zero_grad()
        logits = model(xb)
        loss = criterion(logits, yb)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * xb.size(0)
        preds = torch.argmax(logits, dim = 1)
        correct += (preds == yb).sum().item()
        total += yb.size(0)
    
    avg_loss = total_loss / len(train_ds)
    acc = correct / total
    test_loss, test_acc = model_eval(model, test_loader, criterion)

    loss_history.append(avg_loss)
    acc_history.append(acc)
    test_loss_history.append(test_loss)
    test_acc_history.append(test_acc)

    print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {avg_loss:4f}, Accuracy: {acc:4f}, Test Loss: {test_loss:4f}, Test Acc: {test_acc:4f}")

def model_eval(model, test_loader, criterion):
    model.eval()
    total_loss = 0.
    correct = 0
    total = 0
    for xb, yb in test_loader:
        logits = model(xb)
        preds = logits.argmax(dim=1)
        loss = criterion(logits, yb)
        total_loss += loss.item() * yb.size(0)
        correct += (preds == yb).sum().item()
        total += yb.size(0)
    avg_loss = total_loss / total
    acc = correct / total
    return avg_loss, acc

model.eval()
all_labels = []
all_preds = []
for xb, yb in test_loader:
    logits = model(xb)
    preds = logits.argmax(dim=1)
    all_preds.extend(preds.tolist())
    all_labels.extend(yb.tolist())

from sklearn.metrics import classification_report
print(classification_report(all_labels, all_preds, zero_division=0, target_names=vocab_y.keys()))
"""
        pyperclip.copy(code)

    def news(self):
        code = """
import pandas as pd
df = pd.read_csv("nlp/news.csv")
class_names = {1: 0, 2: 1, 3: 2, 4: 3}
y = [class_names[i] for i in df['Class Index'].tolist()]
texts = (df['Title'].fillna('') + ' ' + df['Description'].fillna('')).tolist()

processed = []
for t in texts:
    processed.append([w for w in t.lower().split()])
max_len = max(len(t) for t in processed)

vocab = {"PAD": 0, "UNK": 1}
idx = 2
for t in processed:
    for w in t:
        if w not in vocab.keys():
            vocab[w] = idx
            idx += 1

from sklearn.model_selection import train_test_split
encoded = []
for t in processed:
    encoded.append([vocab.get(w, "UNK") for w in t])

padded = []
for t in encoded:
    padded.append(t + [vocab.get("PAD")] * (max_len - len(t))) # To-do: попробовать truncation

X = padded
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

import torch
from torch.utils.data import Dataset, DataLoader

class NewsDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.long)
        self.y = torch.tensor(y, dtype=torch.long)
    def __len__(self):
        return len(self.y)
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_ds = NewsDataset(X_train, y_train)
test_ds = NewsDataset(X_test, y_test)
train_loader = DataLoader(train_ds, batch_size=1, shuffle=True)
test_loader = DataLoader(test_ds, batch_size=1, shuffle=False)

import torch.nn as nn

class NewsClassifier(nn.Module):
    def __init__(self, vocab_size, emb_dim, num_classes):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.linear = nn.Linear(emb_dim, num_classes)
    def forward(self, x):
        emb = self.embed(x)
        logits = self.linear(emb.mean(dim=1))
        return logits
model = NewsClassifier(len(vocab), 50, 4)

import torch.optim as optim

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters())
num_epochs = 5

for epoch in range(num_epochs):
    total_loss = 0.
    for xb, yb in train_loader:
        optimizer.zero_grad()
        logits = model(xb)
        loss = criterion(logits, yb)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * xb.size(0)
    avg_loss = total_loss / len(train_ds)
    print(f"epoch [{epoch+1}/{num_epochs}], loss: {avg_loss:4f}")
"""
        pyperclip.copy(code)

    def pos(self):
        code = """
import json
import torch
from torch.utils.data import Dataset, DataLoader
import torch.nn as nn
import torch.optim as optim

with open('nlp/pos.json', 'r') as f:
    data = json.load(f)
X, y = [], []
for d in data:
    if len(d['sentence'].split()) == len(d['tags']):
        X += [d['sentence'].lower().split()]
        y += [d['tags']]

vocab_x = {"PAD": 0, "UNK": 1}
idx = 2
for sent in X:
    for w in sent:
        if w not in vocab_x.keys():
            vocab_x[w] = idx
            idx += 1

vocab_y = {"PAD": 0, "UNK": 1}
idx = 2
for sent in y:
    for pos in sent:
        if pos not in vocab_y.keys():
            vocab_y[pos] = idx
            idx += 1

encoded_X = []
encoded_y = []
for sent, pos_sent in zip(X, y):
    print(sent, pos_sent)
    encoded_X += [[vocab_x.get(w, 0) for w in sent]]
    encoded_y += [[vocab_y.get(w, 0) for w in pos_sent]]
max_len = max(len(sent) for sent in X)

padded_x = []
padded_y = []
for sent, pos_sent in zip(encoded_X, encoded_y):
    padded_x += [sent + [vocab_x.get("PAD")] * (max_len - len(sent))]
    padded_y += [pos_sent + [vocab_y.get("PAD")] * (max_len - len(pos_sent))]

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(padded_x, padded_y, test_size=0.25, random_state=42)

class PosDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y
    def __len__(self):
        return len(self.y)
    def __getitem__(self, idx):
        return torch.tensor(self.X[idx]), torch.tensor(self.y[idx])

train_ds = PosDataset(X_train, y_train)
test_ds = PosDataset(X_test, y_test)
train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
test_loader = DataLoader(test_ds, batch_size=64, shuffle=False)

class BiGRUClassifier(nn.Module):
    def __init__(self, vocab_size, emb_dim, hidden_size, num_classes):
        super().__init__()
        self.embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=emb_dim, padding_idx=0)
        self.gru = nn.GRU(input_size=emb_dim, hidden_size=hidden_size, batch_first=True, bidirectional=True)
        self.linear = nn.Linear(hidden_size*2, num_classes)
    
    def forward(self, x):
        emb = self.embed(x)
        out, _ = self.gru(emb)
        logits = self.linear(out)
        return logits

vocab_size = len(vocab_x)
emb_dim = 200
hidden_size = 128
num_classes = 23
model = BiGRUClassifier(vocab_size, emb_dim, hidden_size, num_classes)
criterion = nn.CrossEntropyLoss(ignore_index=0)
optimizer = optim.Adam(model.parameters())

n_epochs = 5
for epoch in range(n_epochs):
    total_loss = 0.
    for xb, yb in train_loader:
        optimizer.zero_grad()
        output = model(xb)
        output = output.view(-1, num_classes)
        yb = yb.view(-1)

        loss = criterion(output, yb)
        loss.backward()
        optimizer.step()

        acc = token_accuracy(output, yb)
        total_loss += loss.item() * xb.size(0)
    avg_loss = total_loss / len(train_ds)
    print(f"Epoch [{epoch+1}/{n_epochs}], Loss: {avg_loss:4f}, Acc: {acc:4f}")

def token_accuracy(logits, targets, pad_idx=0):
    preds = logits.argmax(dim=-1)
    mask = targets != pad_idx
    correct = (preds == targets) & mask
    acc = correct.sum().item() / mask.sum().item()
    return acc

all_preds = []
all_labels = []

model.eval()

for xb, yb in test_loader:
    logits = model(xb)
    preds = logits.argmax(dim=-1)
    for pred_seq, true_seq in zip(preds, yb):
        for pred_token, true_token in zip(pred_seq, true_seq):
            if true_token.item() != 0:
                all_preds.append(pred_token.item())
                all_labels.append(true_token.item())

from sklearn.metrics import classification_report
inv_vocab_y = {v:k for k,v in vocab_y.items() if v != 1 and v !=0}
print(classification_report(
    all_labels, 
    all_preds, 
    zero_division=0,
    target_names=list(inv_vocab_y.values())
))
"""
        pyperclip.copy(code)

    def jaccard(code):
        code = """
import torch
data = torch.load("sents/jaccard.pt")
sents_pairs = torch.load("sents/sents_pairs.pt")

pad_idx = 0
jaccards = []
for pair in sents_pairs:
    s1 = set(pair[0].tolist()) - {pad_idx}
    s2 = set(pair[1].tolist()) - {pad_idx}
    inter = s1 & s2
    union = s1 | s2
    j = float(len(inter)) / float(len(union)) if union else 0.0
    jaccards.append(j)
jaccard = torch.tensor(jaccards, dtype=torch.float32)
torch.save(jaccard, "sents/jaccard_computed.pt")

from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split

X = torch.load("sents/sents_pairs.pt")
y = torch.load("sents/jaccard_computed.pt")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

train_ds = TensorDataset(X_train, y_train)
test_ds = TensorDataset(X_test, y_test)
train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
test_loader = DataLoader(test_ds, batch_size=64, shuffle=False)

import torch.nn as nn
import torch.optim as optim

class JaccardNet(nn.Module):
    def __init__(self, vocab_size, emb_dim=128, hidden_dim=64):
        super().__init__()
        self.embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=emb_dim, padding_idx=0)
        self.fc = nn.Sequential(
            nn.Linear(2*emb_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
    def forward(self, x):
        s1, s2 = x[:, 0], x[:, 1]
        e1 = self.embed(s1).mean(dim=1)
        e2 = self.embed(s2).mean(dim=1)
        out = torch.cat([e1, e2], dim=1)
        return self.fc(out).squeeze(-1)

itos = json.load(open("sents/sents_pairs_itos.json"))
model = JaccardNet(vocab_size=len(itos))

optimizer = optim.Adam(model.parameters())
criterion = nn.MSELoss()
num_epochs = 10

for epoch in range(num_epochs):
    model.train()
    total_loss = 0.0
    for xb, yb in train_loader:
        optimizer.zero_grad()
        pred = model(xb)
        loss = criterion(pred, yb)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * xb.size(0)
    print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {total_loss/len(train_ds):4f}")

model.eval()
maes = []

for xb, yb in test_loader:
    pred = model(xb)
    mae = torch.mean(torch.abs(pred - yb))
    maes += [mae.item()]
torch.tensor(maes).mean()

for xb, yb in test_loader:
    for idx, elem in enumerate(xb):
        pred = model(xb[idx, :, :].unsqueeze(0))
        tok1, tok2 = xb[idx, 0, :].tolist(), xb[idx, 1, :].tolist()
        s1 = " ".join([itos[t] for t in tok1 if t!=0])
        s2 = " ".join([itos[t] for t in tok2 if t!=0])
        print("sent 1: ", s1)
        print("==========")
        print("sent 2: ", s2)
        print("==========")
        print("jaccard_pred: ", pred)
        print("jaccard_true: ", yb[idx])
        break
    break
"""
        pyperclip.copy(code)

    def word2vec_ns(self):
        code = """
import torch
import torch.nn as nn
import torch.nn.functional as F

class SkipGramNegativeSamplingCustom(nn.Module):
    def __init__(self, vocab_size, emb_dim):
        super().__init__()
        self.in_embed = nn.Embedding(vocab_size, emb_dim)
        self.out_embed = nn.Embedding(vocab_size, emb_dim)
    def forward(self, center_idxs, pos_idxs, neg_idxs):
        v_c = self.in_embed(center_idxs)
        v_pos = self.out_embed(pos_idxs)
        v_negs = self.out_embed(neg_idxs)
        pos_score = torch.sum(v_c * v_pos, dim=-1)
        neg_score = torch.bmm(v_negs, v_c.unsqueeze(2)).squeeze(2)
        return pos_score, neg_score

def negative_sampling_loss(pos_score, neg_score):
    loss_pos = F.logsigmoid(pos_score).mean()
    loss_neg = F.logsigmoid(-neg_score).mean()
    return - (loss_pos + loss_neg)

B, V, D, K = 16, 1000, 64, 10  # batch, vocab, emb_dim, neg samples
model = SkipGramNegativeSamplingCustom(vocab_size=V, emb_dim=D)
center = torch.randint(0, V, (B,))
pos = torch.randint(0, V, (B,))
negs = torch.randint(0, V, (B, K))
pos_score, neg_score = model(center, pos, negs)
print("pos_score.shape:", pos_score.shape)  # → [16]
print("neg_score.shape:", neg_score.shape)  # → [16, 10]
loss = negative_sampling_loss(pos_score, neg_score)
"""

        pyperclip.copy(code)

    def word2vec_ds(self):
        code = """
import pandas as pd
df = pd.read_csv("nlp/news.csv")
texts_raw = (df['Title'].fillna('') + ' ' + df['Description'].fillna('')).tolist()
tokens = [row.lower().split() for row in texts_raw]
freq = {}
for sent in tokens:
    for w in sent:
        freq[w] = freq.get(w, 0) + 1

vocab = {"<PAD>": 0, "<UNK>": 1}
for w, c in freq.items():
    if c >= 5:
        vocab[w] = len(vocab)
itos = {i:w for w,i in vocab.items()}
indexed = [[vocab.get(w, 1) for w in sent] for sent in tokens]

import random
from torch.utils.data import Dataset, DataLoader

class SGSoftmaxDataset(Dataset):
    def __init__(self, texts, vocab, window=2):
        self.pairs = []
        for sent in texts:
            L = len(sent)
            for i, center in enumerate(sent):
                win = random.randint(1, window)
                left = sent[max(0, i-win):i]
                right = sent[i+1:min(L, i+1+win)]
                for ctx in left + right:
                    self.pairs.append((center, ctx))
    def __len__(self):
        return len(self.pairs)
    def __getitem__(self, idx):
        center, context = self.pairs[idx]
        return torch.tensor(center), torch.tensor(context)
dataset = SGSoftmaxDataset(indexed, vocab, window=2)
loader = DataLoader(dataset, batch_size=512, shuffle=True)

class SkipGramSoftmax(nn.Module):
    def __init__(self, vocab_size, emb_dim):
        super().__init__()
        self.in_embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=emb_dim)
        self.out_embed = nn.Linear(emb_dim, vocab_size)
    def forward(self, center_idxs):
        v_c = self.in_embed(center_idxs)
        scores = self.out_embed(v_c)
        return scores

import torch.optim as optim
model = SkipGramSoftmax(vocab_size=len(vocab), emb_dim=100)
optimizer = optim.Adam(model.parameters())
criterion = nn.CrossEntropyLoss()

num_epochs = 5
for epoch in range(num_epochs):
    total_loss = 0.
    for centers, contexts in loader:
        optimizer.zero_grad()
        logits = model(centers)
        loss = criterion(logits, contexts)
        loss.backward()
        optimizer.step()
        
        
        total_loss += loss.item() * centers.size(0)
    print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {total_loss/len(dataset):4f}")
word_vectors = model.in_embed.weight.data
"""
        pyperclip.copy(code)

    def word2vec(self):
        code = """
class SkipGramSoftmaxTest(nn.Module):
    def __init__(self, vocab_size, emb_dim):
        super().__init__()
        self.in_embed = nn.Embedding(vocab_size, emb_dim)
        self.out_embed = nn.Linear(emb_dim, vocab_size)
    
    def forward(self, center_idxs):
        v_c = self.in_embed(center_idxs)
        scores = self.out_embed(v_c)
        log_probs = F.log_softmax(scores, dim=1)
        return log_probs

B, V, D = 16, 1000, 64
model = SkipGramSoftmaxTest(vocab_size=V, emb_dim=D)

center = torch.randint(0, V, (B,))
pos = torch.randint(0, V, (B,))
log_probs = model(center)
criterion = nn.NLLLoss()
loss = criterion(log_probs, pos)
"""
        pyperclip.copy(code)

    def rnncell(self):
        code = """
import torch, torch.nn as nn
class RNNCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super().__init__()
        self.i2h = nn.Linear(input_size, hidden_size)
        self.h2h = nn.Linear(hidden_size, hidden_size)

    def forward(self, x, h):
        return torch.tanh(self.i2h(x) + self.h2h(h))

b, I, H = 3, 4, 5
cell = RNNCell(I, H)
x = torch.randn(b, I, requires_grad=True)
h0 = torch.randn(b, H, requires_grad=True)
out = cell(x, h0)
"""
        pyperclip.copy(code)

    def rnncell_g(self):
        code = """
class OneGateRNNCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super().__init__()
        self.i2g = nn.Linear(input_size, hidden_size)
        self.h2g = nn.Linear(hidden_size, hidden_size)
        self.i2c = nn.Linear(input_size, hidden_size)
        self.h2c = nn.Linear(hidden_size, hidden_size)
    def forward(self, x, h):
        g = torch.sigmoid(self.i2g(x) + self.h2g(h))
        c = torch.tanh(self.i2c(x) + self.h2c(h))
        return (1 - g) * h + g * c

class GatedRNN(nn.Module):
    def __init__(self, input_size, hidden_size):
        super().__init__()
        self.hidden_size = hidden_size
        self.cell = OneGateRNNCell(input_size, hidden_size)
    def forward(self, x, h0=None):
        b, seq_len, _ = x.size()
        if h0 is None:
            h = x.new_zeros(b, self.hid_sz)
        else:
            h = h0
        outputs = []
        for t in range(seq_len):
            h = self.cell(x[:, t, :], h)
            outputs.append(h.unsqueeze(1))
        out_seq = torch.cat(outputs, dim=1)
        return out_seq, h
"""
        pyperclip.copy(code)

    def conv1d(self):
        code = """
import torch, torch.nn as nn, torch.nn.functional as F

class CustomConv1D(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.weight = nn.Parameter(torch.randn(out_channels, in_channels, kernel_size))
        self.bias = nn.Parameter(torch.randn(out_channels))
    def forward(self, x):
        x_padded = F.pad(x, (self.padding, self.padding))
        patches = x_padded.unfold(2, self.kernel_size, self.stride)
        b, in_c, L_out, k = patches.shape
        patches = patches.permute(0, 2, 1, 3).reshape(b, L_out, in_c * k)
        w_flat  = self.weight.view(self.out_channels, in_c * k)
        out = patches @ w_flat.t() + self.bias
        return out.permute(0, 2, 1)

batch, in_c, seq_len = 2, 3, 10
out_c, k_sz, stride, pad = 4, 3, 2, 1
layer = CustomConv1D(in_c, out_c, k_sz, stride=stride, padding=pad)
x = torch.randn(batch, in_c, seq_len, requires_grad=True)
out_custom = layer(x)

conv = nn.Conv1d(in_c, out_c, k_sz, stride=stride, padding=pad)
conv.weight.data = layer.weight.data.clone()
conv.bias.data  = layer.bias.data.clone()
out_ref = conv(x)
"""
        pyperclip.copy(code)

    def embedding(self):
        code = """
import torch
import torch.nn as nn

class CustomEmbedding(nn.Module):
    def __init__(self, num_embeddings, embedding_dim, padding_idx=None, max_norm=None, norm_type=None):
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.padding_idx = padding_idx
        self.max_norm = max_norm
        self.norm_type = norm_type  
        emb_layer = torch.randn(size=(self.num_embeddings, self.embedding_dim))
        self.emb_layer = emb_layer
                    
    def forward(self, x):
        if self.padding_idx is not None:
            self.emb_layer[self.padding_idx] = torch.zeros(self.embedding_dim)
        if self.max_norm:
            current_norm = torch.norm(self.emb_layer, dim=1, p=self.norm_type)
            mask = current_norm > max_norm
            self.emb_layer[mask] /= current_norm[mask].unsqueeze(1)
        return self.emb_layer[x]

vocab_size = 5
emb_dim = 8
embedding_layer = CustomEmbedding(vocab_size, emb_dim, padding_idx=0, max_norm=1, norm_type=None)
print(embedding_layer(torch.tensor([0, 1, 2, 3, 4])))
"""
        pyperclip.copy(code)

    def linear(self):
        code = """
class CustomLinear(nn.Module):
    def __init__(self, in_features, out_features, bias=False, custom_weights=None):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.bias = bias
        self.custom_weights = custom_weights
        k = 1/self.in_features
        limit = k**0.5
        if self.custom_weights is None:
            self.w = nn.Parameter(torch.empty(self.out_features, self.in_features).uniform_(-limit, limit))
        else:
            if self.custom_weights.size(0) == self.out_features and self.custom_weights.size(1) == self.in_features:
                self.w = nn.Parameter(self.custom_weights)
    
        if self.bias:
            self.b = nn.Parameter(torch.empty(self.out_features).uniform_(-limit, limit))
        else:
            self.b = None

    def forward(self, x):
        if x.ndim == 1:
            x = x.unsqueeze(0)
        if self.b is None:
            return x @ self.w.T
        else:
            return x @ self.w.T + self.b
"""
        pyperclip.copy(code)

    def relu(self):
        code = """
class CustomReLU(nn.Module):
    def __init__(self):
        super().__init__()
    def forward(self, x):
        return torch.where(x < 0, torch.zeros_like(x), x)
"""
        pyperclip.copy(code)

    def dropout(self):
        code = """
import random

class CustomDropout(nn.Module):
    def __init__(self, p=0.2):
        super().__init__()
        self.p = p
    def forward(self, x):
        if not self.training:
            return x
        mask = (torch.rand_like(x) > self.p).float()
        return x * mask / (1 - self.p)
"""

        pyperclip.copy(code)

    def layernorm(self):
        code = """
class CustomLayerNorm(nn.Module):
    def __init__(self, normalized_shape, eps=1e-05, elementwise_affine=True):
        super().__init__()
        self.normalized_shape = normalized_shape
        self.eps = eps
        self.elementwise_affine = elementwise_affine
        self.gamma = nn.Parameter(torch.rand(self.normalized_shape))
        self.beta = nn.Parameter(torch.rand(self.normalized_shape))
        self.norm_dims = tuple(range(-len(self.normalized_shape), 0))
    def forward(self, x):
        mean = x.mean(dim=self.norm_dims, keepdim=True)
        var = x.var(dim=self.norm_dims, keepdim=True)
        x_norm = (x - mean) / torch.sqrt(var + self.eps)
        if self.elementwise_affine:
            x_norm = x_norm * self.gamma + self.beta
            return x_norm
        return x_norm
"""
        pyperclip.copy(code)

    def mseloss(self):
        code = """
import torch.nn as nn
class CustomMSELoss(nn.Module):
    def __init__(self, reduction="mean"):
        super().__init__()
        self.reduction = reduction
    def forward(self, x, y):
        loss = 1/(len(x.squeeze(0))) * (x - y) ** 2
        if self.reduction == "none":
            return loss
        if self.reduction == "mean":
            return torch.mean(loss)
        if self.reduction == "sum":
            return torch.sum(loss)
"""
        pyperclip.copy(code)

    def celoss(self):
        code = """
class CustomCrossEntropyLoss(nn.Module):
    def __init__(self, reduction='mean'):
        super().__init__()
        assert reduction in ['mean', 'sum', 'none']
        self.reduction = reduction

    def forward(self, logits, target):
        max_logits = torch.max(logits, dim=1, keepdim=True)[0]  # For numerical stability
        log_softmax = logits - max_logits - torch.log(torch.sum(torch.exp(logits - max_logits), dim=1, keepdim=True))  # (B, C)
        losses = -log_softmax[torch.arange(logits.size(0)), target]  # (B,)
        if self.reduction == 'mean':
            return torch.mean(losses)
        elif self.reduction == 'sum':
            return torch.sum(losses)
        else:
            return losses

logits = torch.randn(3, 5, requires_grad=True)
target = torch.tensor([1, 0, 4])
criterion = CustomCrossEntropyLoss(reduction='mean')
loss = criterion(logits, target)
"""
        pyperclip.copy(code)

    def pe(self):
        code = """
def get_positional_encoding(seq_len, d_model):
    pos = torch.arange(seq_len, dtype=torch.float32).unsqueeze(1)
    i = torch.arange(d_model, dtype=torch.float32).unsqueeze(0)
    angle_rates = 1.0 / (10000 ** (i / d_model))
    angle_rads = pos * angle_rates
    pe = torch.zeros_like(angle_rads)
    pe[:, 0::2] = torch.sin(angle_rads[:, 0::2])
    pe[:, 1::2] = torch.cos(angle_rads[:, 1::2])
    return pe

seq_len = 10
d_model = 16
pe = get_positional_encoding(seq_len, d_model)
"""

    def gru_custom(self):
        code = """
import torch
import torch.nn.functional as F
class CustomGRUCell:
    def __init__(self, input_size, hidden_size):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.W_z = torch.randn(input_size, hidden_size, requires_grad=True)
        self.U_z = torch.randn(hidden_size, hidden_size, requires_grad=True)
        self.b_z = torch.zeros(hidden_size, requires_grad=True)
        self.W_r = torch.randn(input_size, hidden_size, requires_grad=True)
        self.U_r = torch.randn(hidden_size, hidden_size, requires_grad=True)
        self.b_r = torch.zeros(hidden_size, requires_grad=True)
        self.W_h = torch.randn(input_size, hidden_size, requires_grad=True)
        self.U_h = torch.randn(hidden_size, hidden_size, requires_grad=True)
        self.b_h = torch.zeros(hidden_size, requires_grad=True)
        self.params = [self.W_z, self.U_z, self.b_z,
                       self.W_r, self.U_r, self.b_r,
                       self.W_h, self.U_h, self.b_h]

    def __call__(self, x, h_prev):
        z = torch.sigmoid(x @ self.W_z + h_prev @ self.U_z + self.b_z)
        r = torch.sigmoid(x @ self.W_r + h_prev @ self.U_r + self.b_r)
        h_tilde = torch.tanh(x @ self.W_h + (r * h_prev) @ self.U_h + self.b_h)
        h = (1 - z) * h_prev + z * h_tilde
        return h

input_size = 4
hidden_size = 6
seq_len = 3
batch_size = 1

x_seq = torch.randn(batch_size, seq_len, input_size)
h = torch.zeros(batch_size, hidden_size)
gru_cell = CustomGRUCell(input_size, hidden_size)
for t in range(seq_len):
    x_t = x_seq[:, t, :]  # (B, D)
    h = gru_cell(x_t, h)
    print(f"Step {t+1}, hidden state: {h}")
"""
        pyperclip.copy(code)

    def padtrim_custom(self):
        code = """
class CustomPadTrim(nn.Module):
    def __init__(self, max_len, pad_token_id=0, special_token_id=None, add_to='none'):
        super().__init__()
        assert add_to in ['start', 'end', 'none']
        self.max_len = max_len
        self.pad_token_id = pad_token_id
        self.special_token_id = special_token_id
        self.add_to = add_to

    def forward(self, sequences):
        processed = []
        for seq in sequences:
            seq = seq.clone()
            if self.special_token_id is not None:
                if self.add_to == 'start':
                    seq = torch.cat([torch.tensor([self.special_token_id], dtype=seq.dtype), seq])
                elif self.add_to == 'end':
                    seq = torch.cat([seq, torch.tensor([self.special_token_id], dtype=seq.dtype)])
            
            if len(seq) > self.max_len:
                seq = seq[:self.max_len]
            else:
                pad_len = self.max_len - len(seq)
                pad = torch.full((pad_len,), self.pad_token_id, dtype=seq.dtype)
                seq = torch.cat([seq, pad])
            processed.append(seq)
        return torch.stack(processed)
sequences = [
    torch.tensor([1, 2, 3]),
    torch.tensor([4, 5]),
    torch.tensor([6, 7, 8, 9, 10])
]
layer = CustomPadTrim(max_len=5, pad_token_id=0, special_token_id=101, add_to='start')
output = layer(sequences)
"""
        pyperclip.copy(code)

    def attention(self):
        code = """
class CustomAttention(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, query, key, value):
        d_k = query.size(-1)
        scores = torch.matmul(query, key.transpose(-2, -1)) / d_k**0.5
        attention_weights = F.softmax(scores, dim=-1)
        attention_output = torch.matmul(attention_weights, value)
        return attention_weights, attention_output

B, T_q, T_k, D, D_v = 2, 4, 6, 8, 10
query = torch.randn(B, T_q, D)
key = torch.randn(B, T_k, D)
value = torch.randn(B, T_k, D_v)
attn = CustomAttention()
weights, output = attn(query, key, value)
"""
        pyperclip.copy(code)

    def embed_linear(self):
        code = """
class SimpleClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, num_classes):
        super().__init__()
        self.embedding = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim, padding_idx=0)
        self.fc = nn.Linear(embedding_dim, num_classes)
    
    def forward(self, x):
        emb = self.embedding(x)
        mask = (x != 0).unsqueeze(-1).float()
        summed = (emb * mask).sum(dim=1)
        lengths = mask.sum(dim=1).clamp(min=1)
        avg = summed/lengths
        out = self.fc(avg)
        return out
"""
        pyperclip.copy(code)

    def tf(self):
        code = """
class TfidfFCClassifier(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_classes):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_classes),
        )
    def forward(self, x):
        return self.fc(x)
model = TfidfFCClassifier(X.shape[1], 256, 4)
"""
        pyperclip.copy(code)

    def rnn(self):
        code = """
class RNNClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size, num_classes):
        super().__init__()
        self.embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim, padding_idx=0)
        self.rnn = nn.RNN(input_size=embedding_dim, hidden_size=hidden_size, batch_first=True)
        self.fc1 = nn.Linear(hidden_size, 64)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(64, 2)
    def forward(self, x):
        emb = self.embed(x)
        out, h = self.rnn(emb)
        logits = self.fc2(self.relu(self.fc1(h)))
        return logits.squeeze(0)
"""
        pyperclip.copy(code)

    def gru(self):
        code = """
class GRUClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size, num_classes):
        super().__init__()
        self.embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim, padding_idx=0)
        self.gru = nn.GRU(input_size=embedding_dim, hidden_size=hidden_size, batch_first=True)
        self.linear = nn.Linear(hidden_size, num_classes)
    def forward(self, x):
        emb = self.embed(x)
        out, h = self.gru(emb)
        logits = self.linear(h)
        return logits.squeeze(0)
"""
        pyperclip.copy(code)

    def lstm(self):
        code = """
class LSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size, num_classes):
        super().__init__()
        self.embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(input_size=embedding_dim, hidden_size=hidden_size, batch_first=True)
        self.linear = nn.Linear(hidden_size, num_classes)
    def forward(self, x):
        emb = self.embed(x)
        out, h = self.lstm(emb)
        logits = self.linear(h)
        return logit.squeeze(0)
"""
        pyperclip.copy(code)

    def biLSTM(self):
        code = """
class BiLSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size, num_classes):
        super().__init__()
        self.embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_size, batch_first=True, bidirectional=True)
        self.linear = nn.Linear(hidden_size*2, num_classes)
    def forward(self, x):
        emb = self.embed(x)
        out, (h, c) = self.lstm(emb)
        h_fw = h[0]
        h_bw = h[1]
        h_combined = torch.cat([h_fw, h_bw], dim=1)
        logits = self.linear(h_combined)
        return logits.squeeze(-1)
"""
        pyperclip.copy(code)

    def biGRU(self):
        code = """
class BiGRUClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size, num_classes):
        super().__init__()
        self.embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim, padding_idx=0)
        self.gru = nn.GRU(embedding_dim, hidden_size, batch_first=True, bidirectional=True)
        self.linear = nn.Linear(hidden_size * 2, num_classes)
    def forward(self, x):
        emb = self.embed(x)
        out, h = self.gru(emb)
        h_fw = h[0]
        h_bw = h[1]
        h_combined = torch.cat([h_fw, h_bw], dim=1)
        logits = self.linear(h_combined)
        return logits.squeeze(-1)
"""
        pyperclip.copy(code)

    def biRNN(self):
        code = """
class BiRNNClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size, num_classes):
        super().__init__()
        self.embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim, padding_idx=0)
        self.rnn = nn.RNN(embedding_dim, hidden_size, batch_first=True, bidirectional=True)
        self.linear = nn.Linear(hidden_size * 2, num_classes)

    def forward(self, x):
        emb = self.embed(x)
        out, h = self.rnn(emb)
        h_fw = h[0]
        h_bw = h[1]
        h_combined = torch.cat([h_fw, h_bw], dim=1)
        logits = self.linear(h_combined)
        return logits.squeeze(-1)
"""
        pyperclip.copy(code)

    def seq2seq(self):
        code = """
class Encoder(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.gru = nn.GRU(embedding_dim, hidden_size, batch_first=True)
    def forward(self, src):
        embedded = self.embed(src)
        outputs, hidden = self.gru(embedded)
        return hidden

class Decoder(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.gru = nn.GRU(embedding_dim, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, vocab_size)
    def forward(self, tgt, hidden):
        embedded = self.embed(tgt)
        output, hidden = self.gru(embedded, hidden)
        logits = self.fc(output)
        return logits, hidden
"""
        pyperclip.copy(code)

    def tweets_disaster(self):
        """Обучите одно- и двунаправленную рекуррентную сеть tweets_disaster"""
        code = """
import pandas as pd
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score
import time

df = pd.read_csv("tweets_disaster.csv", index_col=0)
texts = df['text'].values
labels = df['target'].values

train_texts, test_texts, train_labels, test_labels = train_test_split(
    texts, labels, test_size=0.2, stratify=labels, random_state=42)
df.head()

def tokenize(text):
    return text.lower().split()

from collections import Counter
counter = Counter()
for text in train_texts:
    tokens = tokenize(text)
    counter.update(tokens)

vocab = {word: index + 2 for index, (word, count) in enumerate(counter.most_common())}
vocab['<PAD>'] = 0
vocab['<UNK>'] = 1

def text_to_indices(text, vocab, max_len=50):
    tokens = tokenize(text)
    indices = [vocab.get(token, vocab['<UNK>']) for token in tokens]
    if len(indices) < max_len:
        indices = indices + [vocab['<PAD>']] * (max_len - len(indices))
    else:
        indices = indices[:max_len]
    return indices

max_seq_length = 50  

class TweetDataset(Dataset):
    def __init__(self, texts, labels, vocab, max_len):
        self.texts = texts
        self.labels = labels
        self.vocab = vocab
        self.max_len = max_len 
    def __len__(self):
        return len(self.texts)
    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        indices = text_to_indices(text, self.vocab, self.max_len)
        return torch.tensor(indices, dtype=torch.long), torch.tensor(label, dtype=torch.long)

train_dataset = TweetDataset(train_texts, train_labels, vocab, max_seq_length)
test_dataset = TweetDataset(test_texts, test_labels, vocab, max_seq_length)

batch_size = 64
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

class RNNClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, bidirectional=False):
        super(RNNClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.bidirectional = bidirectional
        self.rnn = nn.RNN(input_size=embed_dim, 
                          hidden_size=hidden_dim, 
                          batch_first=True, 
                          bidirectional=bidirectional)
        
        if self.bidirectional:
            self.fc = nn.Linear(hidden_dim * 2, output_dim)
        else:
            self.fc = nn.Linear(hidden_dim, output_dim)
        
    def forward(self, x):
        embedded = self.embedding(x)
        out, hidden = self.rnn(embedded)
        if self.bidirectional:
            hidden_forward = hidden[0]
            hidden_backward = hidden[1]
            hidden = torch.cat((hidden_forward, hidden_backward), dim=1)
        else:
            hidden = hidden.squeeze(0)
        logits = self.fc(hidden)
        return logits 

vocab_size = len(vocab)
embed_dim = 100
hidden_dim = 128
output_dim = 2 

model_uni = RNNClassifier(vocab_size, embed_dim, hidden_dim, output_dim, bidirectional=False)
model_bi = RNNClassifier(vocab_size, embed_dim, hidden_dim, output_dim, bidirectional=True)
criterion = nn.CrossEntropyLoss()
optimizer_uni = optim.Adam(model_uni.parameters(), lr=1e-3)
optimizer_bi = optim.Adam(model_bi.parameters(), lr=1e-3)

def train_model(model, optimizer, num_epochs=5):
    model.train()
    total_time = 0
    for epoch in range(num_epochs):
        epoch_loss = 0
        start_time = time.time()
        for batch_inputs, batch_labels in train_loader:
            batch_inputs, batch_labels = batch_inputs, batch_labels
            optimizer.zero_grad()
            outputs = model(batch_inputs)
            loss = criterion(outputs, batch_labels)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * batch_inputs.size(0)
            
        elapsed = time.time() - start_time
        total_time += elapsed
        epoch_loss /= len(train_dataset)
        print(f"Epoch {epoch+1}, Loss: {epoch_loss:.4f}, Time: {elapsed:.2f} sec")
    return total_time

print("Обучение однонаправленной RNN:")
time_uni = train_model(model_uni, optimizer_uni, num_epochs=5)

print("\nОбучение двунаправленной RNN:")
time_bi = train_model(model_bi, optimizer_bi, num_epochs=5)

def evaluate_model(model):
    model.eval()
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for batch_inputs, batch_labels in test_loader:
            batch_inputs, batch_labels = batch_inputs, batch_labels
            outputs = model(batch_inputs)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(batch_labels.cpu().numpy())
    return accuracy_score(all_labels, all_preds)

acc_uni = evaluate_model(model_uni)
acc_bi = evaluate_model(model_bi)

print(f"\nТочность теста однонаправленной RNN: {acc_uni:.4f}")
print(f"Точность теста двунаправленной RNN: {acc_bi:.4f}")
print(f"Общее время обучения однонаправленной модели: {time_uni:.2f} секунд")
print(f"Общее время обучения двунаправленной модели: {time_bi:.2f} секунд")
"""
        pyperclip.copy(code)

    def tweets_disaster_tf(self):
        """tweets_disaster подход на основе TF-IDF с классическим классификатором (например, логистической регрессией)"""
        code = """
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np


df = pd.read_csv("tweets_disaster.csv", index_col=0)
texts = df['text'].astype(str).values
labels = df['target'].values

X_train_texts, X_test_texts, y_train, y_test = train_test_split(
    texts, labels, test_size=0.2, stratify=labels, random_state=42
)


tfidf_vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words='english',
    max_df=0.9,
    min_df=5
)

X_train_tfidf = tfidf_vectorizer.fit_transform(X_train_texts)
X_test_tfidf = tfidf_vectorizer.transform(X_test_texts)

X_train_np = X_train_tfidf.toarray()
X_test_np = X_test_tfidf.toarray()

class TfidfDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
        
    def __len__(self):
        return self.X.shape[0]
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_dataset = TfidfDataset(X_train_np, y_train)
test_dataset = TfidfDataset(X_test_np, y_test)

batch_size = 64
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

class TfidfClassifier(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.5):
        super(TfidfClassifier, self).__init__()
        self.model = nn.Sequential(nn.Linear(input_dim, hidden_dim),nn.ReLU(),
            nn.Dropout(dropout),nn.Linear(hidden_dim, output_dim))
        
    def forward(self, x):
        return self.model(x)

input_dim = X_train_np.shape[1]  
hidden_dim = 128
output_dim = 2  

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = TfidfClassifier(input_dim, hidden_dim, output_dim).to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)


def train_model(model, train_loader, optimizer, criterion, num_epochs=5):
    model.train()
    for epoch in range(num_epochs):
        running_loss = 0.0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * batch_X.size(0)
        epoch_loss = running_loss / len(train_loader.dataset)
        print(f"Epoch {epoch+1}/{num_epochs} - Loss: {epoch_loss:.4f}")


def evaluate_model(model, test_loader):
    model.eval()
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            outputs = model(batch_X)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(batch_y.cpu().numpy())
    acc = accuracy_score(all_targets, all_preds)
    return acc, classification_report(all_targets, all_preds)


num_epochs = 5
train_model(model, train_loader, optimizer, criterion, num_epochs=num_epochs)


acc, report = evaluate_model(model, test_loader)
print(f"\nTest Accuracy: {acc:.4f}")
print("\nClassification Report:")
print(report)"""

        pyperclip.copy(code)

    def tweet_cat(self):
        """решения задачи классификации твитов по признаку type при помощи TF-IDF представления текстов и полносвязной нейросети (MLP) на PyTorch.

       tweet_cat """
        code = """
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

import numpy as np

df = pd.read_csv("tweet_cat.csv")
df.head()

 texts = df['text'].astype(str).values
 labels = df['type'].values
 
 
 le = LabelEncoder()
 labels_encoded = le.fit_transform(labels)
 
 X_train_texts, X_test_texts, y_train, y_test = train_test_split(
     texts, labels_encoded, test_size=0.2, stratify=labels_encoded, random_state=42
 )
 
 tfidf_vectorizer = TfidfVectorizer(
     lowercase=True,
     stop_words='english',
     max_df=0.9,
     min_df=3  
 )
 
 X_train_tfidf = tfidf_vectorizer.fit_transform(X_train_texts)
 X_test_tfidf = tfidf_vectorizer.transform(X_test_texts)
 
 X_train_np = X_train_tfidf.toarray()
 X_test_np = X_test_tfidf.toarray()
 
 class TfidfDataset(Dataset):
     def __init__(self, X, y):
         self.X = torch.tensor(X, dtype=torch.float32)
         self.y = torch.tensor(y, dtype=torch.long)
         
     def __len__(self):
         return self.X.shape[0]
     
     def __getitem__(self, idx):
         return self.X[idx], self.y[idx]
 
 train_dataset = TfidfDataset(X_train_np, y_train)
 test_dataset = TfidfDataset(X_test_np, y_test)
 
 batch_size = 64
 train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
 test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
 
 # 6. простой MLP для классификации
 class TfidfClassifier(nn.Module):
     def __init__(self, input_dim, hidden_dim, output_dim, dropout=0.5):
         super(TfidfClassifier, self).__init__()
         self.model = nn.Sequential(
             nn.Linear(input_dim, hidden_dim),
             nn.ReLU(),
             nn.Dropout(dropout),
             nn.Linear(hidden_dim, hidden_dim // 2),
             nn.ReLU(),
             nn.Dropout(dropout),
             nn.Linear(hidden_dim // 2, output_dim)
         )
         
     def forward(self, x):
         return self.model(x)
 
 input_dim = X_train_np.shape[1]    
 hidden_size = 128
 num_classes = len(le.classes_)        # число классов
 
 device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
 model = TfidfClassifier(input_dim, hidden_size, num_classes).to(device)
 
 criterion = nn.CrossEntropyLoss()
 optimizer = optim.Adam(model.parameters(), lr=1e-3)
 
 
 def train_model(model, train_loader, optimizer, criterion, num_epochs=5):
     model.train()
     for epoch in range(num_epochs):
         running_loss = 0.0
         for batch_X, batch_y in train_loader:
             batch_X, batch_y = batch_X.to(device), batch_y.to(device)
             
             optimizer.zero_grad()
             outputs = model(batch_X)
             loss = criterion(outputs, batch_y)
             loss.backward()
             optimizer.step()
             
             running_loss += loss.item() * batch_X.size(0)
         epoch_loss = running_loss / len(train_loader.dataset)
         print(f"Epoch {epoch+1}/{num_epochs} - Loss: {epoch_loss:.4f}")
 
 
 def evaluate_model(model, test_loader):
     model.eval()
     all_preds = []
     all_targets = []
     with torch.no_grad():
         for batch_X, batch_y in test_loader:
             batch_X, batch_y = batch_X.to(device), batch_y.to(device)
             outputs = model(batch_X)
             _, preds = torch.max(outputs, 1)
             all_preds.extend(preds.cpu().numpy())
             all_targets.extend(batch_y.cpu().numpy())
     acc = accuracy_score(all_targets, all_preds)
     report = classification_report(all_targets, all_preds, target_names=le.classes_)
     return acc, report

num_epochs = 5
train_model(model, train_loader, optimizer, criterion, num_epochs=num_epochs)


acc, report = evaluate_model(model, test_loader)
print(f"\nTest Accuracy: {acc:.4f}")
print("\nClassification Report:")
print(report)
    """
        pyperclip.copy(code)

    def quotes(self):
        """решения задачи классификации цитат по категории с использованием представления через
        эмбеддинги и последующей классификацией с помощью полносвязной сети. """

        code = """
import json
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

with open("quotes.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)
df = df[df['Category'].str.strip() != '']
df.head()

def tokenize(text):
    text = text.lower()
    text = re.sub(r'[^a-zа-яё\s]', '', text)
    return text.split()


quotes = df['Quote'].astype(str).values
categories = df['Category'].values

# Кодируем метки
le = LabelEncoder()
y = le.fit_transform(categories)
print("Найденные категории:", le.classes_)


X_train_texts, X_test_texts, y_train, y_test = train_test_split(
    quotes, y, test_size=0.2, stratify=y, random_state=42
)


from collections import Counter

def build_vocab(texts, min_freq=2):
    counter = Counter()
    for text in texts:
        tokens = tokenize(text)
        counter.update(tokens)
    vocab = {"<PAD>": 0, "<UNK>": 1}
    for word, count in counter.items():
        if count >= min_freq:
            vocab[word] = len(vocab)
    return vocab

vocab = build_vocab(X_train_texts, min_freq=2)
vocab_size = len(vocab)
print("Размер словаря:", vocab_size)

def text_to_indices(text, vocab, max_len=50):
    tokens = tokenize(text)
    indices = [vocab.get(token, vocab["<UNK>"]) for token in tokens]
    if len(indices) < max_len:
        indices = indices + [vocab["<PAD>"]] * (max_len - len(indices))
    else:
        indices = indices[:max_len]
    return indices

max_seq_length = 50 


class QuotesDataset(Dataset):
    def __init__(self, texts, labels, vocab, max_len):
        self.texts = texts
        self.labels = labels
        self.vocab = vocab
        self.max_len = max_len
        
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        indices = text_to_indices(text, self.vocab, self.max_len)
        return torch.tensor(indices, dtype=torch.long), torch.tensor(label, dtype=torch.long)

train_dataset = QuotesDataset(X_train_texts, y_train, vocab, max_seq_length)
test_dataset = QuotesDataset(X_test_texts, y_test, vocab, max_seq_length)

batch_size = 32
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

class EmbeddingClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes, dropout=0.5):
        super(EmbeddingClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.fc = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim//2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim//2, num_classes)
        )
        
    def forward(self, x):
        embeds = self.embedding(x)  
        pooled = embeds.mean(dim=1) 
        out = self.fc(pooled)
        return out
        
import torch.nn as nn

class SimpleClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, num_classes):
        super().__init__()
        self.embedding = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim, padding_idx=0)
        self.fc = nn.Linear(embedding_dim, num_classes)
    
    def forward(self, x):
        emb = self.embedding(x)
        mask = (x != 0).unsqueeze(-1).float()
        summed = (emb * mask).sum(dim=1)
        lengths = mask.sum(dim=1).clamp(min=1)
        avg = summed/lengths
        out = self.fc(avg)
        return out
        
class GRUClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size, num_classes):
        super().__init__()
        self.embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim, padding_idx=0)
        self.gru = nn.GRU(input_size=embedding_dim, hidden_size=hidden_size, batch_first=True)
        self.linear = nn.Linear(hidden_size, num_classes)
        
    def forward(self, x):
        emb = self.embed(x)
        out, h = self.gru(emb)
        logits = self.linear(h)
        return logits.squeeze(0)
        
class BiLSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size, num_classes):
        super().__init__()
        self.embed = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_size, batch_first=True, bidirectional=True)
        self.linear = nn.Linear(hidden_size*2, num_classes)
    
    def forward(self, x):
        emb = self.embed(x)
        out, (h, c) = self.lstm(emb)
        h_fw = h[0]
        h_bw = h[1]
        h_combined = torch.cat([h_fw, h_bw], dim=1)
        logits = self.linear(h_combined)
        return logits.squeeze(-1)
        
embed_dim = 100
hidden_size = 128
num_classes = len(le.classes_)
n_epochs = 5

models = [EmbeddingClassifier(vocab_size, embed_dim, hidden_size, num_classes), 
         SimpleClassifier(vocab_size, embed_dim, num_classes),
         GRUClassifier(vocab_size, embed_dim, hidden_size, num_classes),
         BiLSTMClassifier(vocab_size, embed_dim, hidden_size, num_classes)]
         
def train_model(model, train_loader, optimizer, criterion, num_epochs=10):
    model.train()
    for epoch in range(num_epochs):
        running_loss = 0.0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * batch_X.size(0)
        epoch_loss = running_loss / len(train_loader.dataset)
        print(f"Epoch {epoch+1}/{num_epochs} - Loss: {epoch_loss:.4f}")


def evaluate_model(model, test_loader):
    model.eval()
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            outputs = model(batch_X)
            _, preds = torch.max(outputs, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(batch_y.cpu().numpy())
    acc = accuracy_score(all_targets, all_preds)
    report = classification_report(all_targets, all_preds, target_names=le.classes_)
    return acc, report


for model in models:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    num_epochs = 1
    train_model(model, train_loader, optimizer, criterion, num_epochs=num_epochs)


acc, report = evaluate_model(model, test_loader)
print(f"\nTest Accuracy: {acc:.4f}")
print("\nClassification Report:")
print(report)

    """

        pyperclip.copy(code)

    def reviews(self):
        """задача регрессии - предсказание оценки отзыва на основе его текста с помощью LSTM. """

        code = """
import json
import pandas as pd
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from collections import Counter

data = []
with open('reviews.json') as f:
    for line in f:
        data.append(json.loads(line))
        
df = pd.DataFrame(data)
df.head()

df = df.dropna(subset=['reviewText', 'overall'])

def clean_text(text):
    text = text.lower() 
    text = re.sub(r'http\S+', '', text) 
    text = re.sub(r'[^a-zа-яё\s]', ' ', text)  
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['clean_review'] = df['reviewText'].astype(str).apply(clean_text)


def tokenize(text):
    return text.split()

reviews = df['clean_review'].values
ratings = df['overall'].values.astype(float)

X_train_texts, X_test_texts, y_train, y_test = train_test_split(
    reviews, ratings, test_size=0.2, random_state=42)

def build_vocab(texts, min_freq=2):
    counter = Counter()
    for text in texts:
        tokens = tokenize(text)
        counter.update(tokens)
    vocab = {"<PAD>": 0, "<UNK>": 1}
    for word, count in counter.items():
        if count >= min_freq:
            vocab[word] = len(vocab)
    return vocab

vocab = build_vocab(X_train_texts, min_freq=2)
vocab_size = len(vocab)
print("Размер словаря:", vocab_size)

def text_to_indices(text, vocab, max_len=100):
    tokens = tokenize(text)
    indices = [vocab.get(token, vocab["<UNK>"]) for token in tokens]
    if len(indices) < max_len:
        indices = indices + [vocab["<PAD>"]] * (max_len - len(indices))
    else:
        indices = indices[:max_len]
    return indices

max_seq_length = 100  


class ReviewsDataset(Dataset):
    def __init__(self, texts, ratings, vocab, max_len):
        self.texts = texts
        self.ratings = ratings
        self.vocab = vocab
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        rating = self.ratings[idx]
        indices = text_to_indices(text, self.vocab, self.max_len)
        return torch.tensor(indices, dtype=torch.long), torch.tensor(rating, dtype=torch.float32)

train_dataset = ReviewsDataset(X_train_texts, y_train, vocab, max_seq_length)
test_dataset = ReviewsDataset(X_test_texts, y_test, vocab, max_seq_length)

batch_size = 32
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)


class ReviewRegressor(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, dropout=0.5):
        super(ReviewRegressor, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(input_size=embed_dim, hidden_size=hidden_dim, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim//2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim//2, 1) 
        )
    
    def forward(self, x):

        embeds = self.embedding(x)  
        lstm_out, (hn, cn) = self.lstm(embeds)  
        hn = hn.squeeze(0)  
        output = self.fc(hn)  
        return output.squeeze(1)  

embed_dim = 100
hidden_dim = 128
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = ReviewRegressor(vocab_size, embed_dim, hidden_dim).to(device)


criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)


num_epochs = 5

def train_model(model, train_loader, optimizer, criterion, device, num_epochs):
    model.train()
    for epoch in range(num_epochs):
        epoch_loss = 0.0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * batch_X.size(0)
        epoch_loss /= len(train_loader.dataset)
        print(f"Epoch {epoch+1}/{num_epochs} - Loss: {epoch_loss:.4f}")

def evaluate_model(model, test_loader, device):
    model.eval()
    preds = []
    targets = []
    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            outputs = model(batch_X)
            preds.extend(outputs.cpu().numpy())
            targets.extend(batch_y.cpu().numpy())
    mse = mean_squared_error(targets, preds)
    return mse

print("Начало обучения:")
train_model(model, train_loader, optimizer, criterion, device, num_epochs=num_epochs)
mse = evaluate_model(model, test_loader, device)
print(f"\nTest MSE: {mse:.4f}")    
    """

        pyperclip.copy(code)

    def RNN_gate(self):
        code = """
import pandas as pd
import re
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np

df = pd.read_csv("tweet_cat.csv")
df.head()

df['text'] = df['text'].astype(str).str.strip()
df['type'] = df['type'].astype(str).str.strip()
df = df[df['text'] != '']
df = df[df['type'] != '']

def tokenize(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.split()

def build_vocab(texts, min_freq=1):
    counter = Counter()
    for text in texts:
        tokens = tokenize(text)
        counter.update(tokens)
    vocab = {"<PAD>": 0, "<UNK>": 1}
    for word, count in counter.items():
        if count >= min_freq:
            vocab[word] = len(vocab)
    return vocab

all_texts = df['text'].tolist()
vocab = build_vocab(all_texts, min_freq=2)
vocab_size = len(vocab)
print("Размер словаря:", vocab_size)

def text_to_indices(text, vocab, max_len=50):
    tokens = tokenize(text)
    indices = [vocab.get(token, vocab["<UNK>"]) for token in tokens]
    if len(indices) < max_len:
        indices += [vocab["<PAD>"]] * (max_len - len(indices))
    else:
        indices = indices[:max_len]
    return indices

texts = df['text'].tolist()
types = df['type'].tolist()
le = LabelEncoder()
labels = le.fit_transform(types)
print("Найденные классы:", list(le.classes_))
X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, stratify=labels, random_state=42)

class TextClassificationDataset(Dataset):
    def __init__(self, texts, labels, vocab, max_len=50):
        self.texts = texts
        self.labels = labels
        self.vocab = vocab
        self.max_len = max_len
    def __len__(self):
        return len(self.texts)
    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        indices = text_to_indices(text, self.vocab, self.max_len)
        return torch.tensor(indices, dtype=torch.long), torch.tensor(label, dtype=torch.long)

max_seq_length = 50
train_dataset = TextClassificationDataset(X_train, y_train, vocab, max_seq_length)
test_dataset = TextClassificationDataset(X_test, y_test, vocab, max_seq_length)
batch_size = 32
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

class GRUCell(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super(GRUCell, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.W_z = nn.Linear(input_dim + hidden_dim, hidden_dim)
        self.W_r = nn.Linear(input_dim + hidden_dim, hidden_dim)
        self.W_h = nn.Linear(input_dim + hidden_dim, hidden_dim)
    def forward(self, x, h_prev):
        combined = torch.cat([x, h_prev], dim=1)
        z = torch.sigmoid(self.W_z(combined))
        r = torch.sigmoid(self.W_r(combined))
        combined_candidate = torch.cat([x, r * h_prev], dim=1)
        h_tilde = torch.tanh(self.W_h(combined_candidate))
        h_new = (1 - z) * h_prev + z * h_tilde
        return h_new

class GRUClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, max_len):
        super(GRUClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.hidden_dim = hidden_dim
        self.max_len = max_len
        self.gru_cell = GRUCell(embed_dim, hidden_dim)
        self.fc = nn.Linear(hidden_dim, output_dim)
    def forward(self, x):
        batch_size = x.size(0)
        embeds = self.embedding(x)
        h = torch.zeros(batch_size, self.hidden_dim, device=x.device)
        for t in range(self.max_len):
            x_t = embeds[:, t, :]
            h = self.gru_cell(x_t, h)
        logits = self.fc(h)
        return logits

embed_dim = 100
hidden_dim = 128
output_dim = len(le.classes_)
model = GRUClassifier(vocab_size, embed_dim, hidden_dim, output_dim, max_seq_length)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)
num_epochs = 5

def train_model(model, train_loader, optimizer, criterion, device, num_epochs):
    model.train()
    for epoch in range(num_epochs):
        total_loss = 0.0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * batch_X.size(0)
        avg_loss = total_loss / len(train_loader.dataset)
        print(f"Epoch {epoch+1}/{num_epochs} - Loss: {avg_loss:.4f}")

def evaluate_model(model, test_loader, device):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            outputs = model(batch_X)
            _, predicted = torch.max(outputs, 1)
            total += batch_y.size(0)
            correct += (predicted == batch_y).sum().item()
    accuracy = correct / total
    return accuracy

print("Начало обучения модели")
train_model(model, train_loader, optimizer, criterion, device, num_epochs)
acc = evaluate_model(model, test_loader, device)
print(f"\nTest Accuracy: {acc:.4f}")
    """

        pyperclip.copy(code)

    def RNN_sim(self):

        code = """
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader


texts = df['text'].astype(str).tolist()
corpus = " ".join(texts)


chars = sorted(list(set(corpus)))
vocab_size = len(chars)
char2idx = {ch: i for i, ch in enumerate(chars)}
idx2char = {i: ch for i, ch in enumerate(chars)}


encoded = np.array([char2idx[ch] for ch in corpus], dtype=np.int64)

seq_length = 100
step = 1
batch_size = 64
embed_dim = 32
hidden_dim = 128
num_epochs = 3
lr = 1e-3

class TextDataset(Dataset):
    def __init__(self, data, seq_length, step):
        self.data = data
        self.seq_length = seq_length
        self.step = step
        self.num_examples = (len(data) - seq_length) // step
    def __len__(self):
        return self.num_examples
    def __getitem__(self, idx):
        start = idx * self.step
        end = start + self.seq_length
        x = self.data[start:end]
        y = self.data[start+1:end+1]
        return torch.tensor(x, dtype=torch.long), torch.tensor(y, dtype=torch.long)

dataset = TextDataset(encoded, seq_length, step)
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

class CharRNN(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim):
        super(CharRNN, self).__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim)
        self.gru = nn.GRU(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)
    def forward(self, x, hidden=None):
        x = self.embed(x)
        output, hidden = self.gru(x, hidden)
        logits = self.fc(output)
        return logits, hidden

model = CharRNN(vocab_size, embed_dim, hidden_dim)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
optimizer = optim.Adam(model.parameters(), lr=lr)
criterion = nn.CrossEntropyLoss()


model.train()
for epoch in range(num_epochs):
    total_loss = 0
    for inputs, targets in dataloader:
        inputs = inputs.to(device)
        targets = targets.to(device)
        optimizer.zero_grad()
        outputs, _ = model(inputs)
        loss = criterion(outputs.reshape(-1, vocab_size), targets.reshape(-1))
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * inputs.size(0)
    avg_loss = total_loss / len(dataset)
    print(f"Epoch {epoch+1}/{num_epochs} - Loss: {avg_loss:.4f}")

def generate_text(model, start_str, gen_length=300, temperature=1.0):
    model.eval()
    input_seq = torch.tensor([char2idx[ch] for ch in start_str], dtype=torch.long).unsqueeze(0).to(device)
    hidden = None
    generated = start_str
    with torch.no_grad():
        for _ in range(gen_length):
            output, hidden = model(input_seq, hidden)
            output = output[:, -1, :] / temperature
            prob = torch.softmax(output, dim=-1)
            char_idx = torch.multinomial(prob, num_samples=1).item()
            generated += idx2char[char_idx]
            input_seq = torch.tensor([[char_idx]], dtype=torch.long).to(device)
    return generated

start_string = "the "
print(generate_text(model, start_string))
    """
        pyperclip.copy(code)

    def RNN_pred(self):
        code = """
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

corpus = df['text'].str.cat(sep=" ")
chars = sorted(list(set(corpus)))
vocab_size = len(chars)
char2idx = {ch: i for i, ch in enumerate(chars)}
idx2char = {i: ch for i, ch in enumerate(chars)}
encoded = np.array([char2idx[ch] for ch in corpus], dtype=np.int64)

seq_len = 100
step = 1

class NextTokenDataset(Dataset):
    def __init__(self, data, seq_len, step):
        self.data = data
        self.seq_len = seq_len
        self.step = step
        self.num_samples = (len(data) - seq_len) // step
    def __len__(self):
        return self.num_samples
    def __getitem__(self, idx):
        i = idx * self.step
        x = self.data[i:i+self.seq_len]
        y = self.data[i+1:i+self.seq_len+1]
        return torch.tensor(x, dtype=torch.long), torch.tensor(y, dtype=torch.long)

dataset = NextTokenDataset(encoded, seq_len, step)
dataloader = DataLoader(dataset, batch_size=64, shuffle=True)

class RNNModel(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim):
        super(RNNModel, self).__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim)
        self.rnn = nn.GRU(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)
    def forward(self, x, hidden=None):
        x = self.embed(x)
        out, hidden = self.rnn(x, hidden)
        logits = self.fc(out)
        return logits, hidden

model = RNNModel(vocab_size, 64, 128)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
optimizer = optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.CrossEntropyLoss()

epochs = 3
model.train()
for epoch in range(epochs):
    total_loss = 0
    for x, y in dataloader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        logits, _ = model(x)
        loss = criterion(logits.view(-1, vocab_size), y.view(-1))
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print("Epoch", epoch+1, "Loss", total_loss/len(dataloader))

def predict_next_token(model, input_seq, temperature=1.0):
    model.eval()
    x = torch.tensor([char2idx[ch] for ch in input_seq], dtype=torch.long).unsqueeze(0).to(device)
    with torch.no_grad():
        logits, _ = model(x)
    last_logits = logits[0, -1, :] / temperature
    probs = torch.softmax(last_logits, dim=-1)
    token = torch.multinomial(probs, 1).item()
    return idx2char[token]

input_seq = "The"
predict_next_token(model, input_seq)
    """
        pyperclip.copy(code)

    def conv1d_ds(self):
        code = """
import pandas as pd
import re
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


df['text'] = df['text'].astype(str).str.strip()
df = df[df['text'] != '']
df = df[df['type'] != '']

def tokenize(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.split()

def build_vocab(texts, min_freq=1):
    freq = {}
    for text in texts:
        for token in tokenize(text):
            freq[token] = freq.get(token, 0) + 1
    vocab = {"<PAD>": 0, "<UNK>": 1}
    for token, count in freq.items():
        if count >= min_freq:
            vocab[token] = len(vocab)
    return vocab

texts = df['text'].tolist()
vocab = build_vocab(texts, min_freq=2)
vocab_size = len(vocab)

def text_to_indices(text, vocab, max_len=50):
    tokens = tokenize(text)
    indices = [vocab.get(token, vocab["<UNK>"]) for token in tokens]
    if len(indices) < max_len:
        indices += [vocab["<PAD>"]] * (max_len - len(indices))
    else:
        indices = indices[:max_len]
    return indices

le = LabelEncoder()
labels = le.fit_transform(df['type'].tolist())

X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, stratify=labels, random_state=42)

class TextDataset(Dataset):
    def __init__(self, texts, labels, vocab, max_len=50):
        self.texts = texts
        self.labels = labels
        self.vocab = vocab
        self.max_len = max_len
    def __len__(self):
        return len(self.texts)
    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        indices = text_to_indices(text, self.vocab, self.max_len)
        return torch.tensor(indices, dtype=torch.long), torch.tensor(label, dtype=torch.long)

max_len = 50
batch_size = 32
train_dataset = TextDataset(X_train, y_train, vocab, max_len)
test_dataset = TextDataset(X_test, y_test, vocab, max_len)
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

class CNNTextClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_classes, kernel_sizes=[3,4,5], num_filters=100, dropout=0.5):
        super(CNNTextClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.convs = nn.ModuleList([
            nn.Conv1d(in_channels=embed_dim, out_channels=num_filters, kernel_size=k)
            for k in kernel_sizes
        ])
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(len(kernel_sizes)*num_filters, num_classes)
    def forward(self, x):
        x = self.embedding(x)  # (B, L, D)
        x = x.transpose(1, 2)  # (B, D, L)
        x = [torch.relu(conv(x)) for conv in self.convs]  # each: (B, num_filters, L_out)
        x = [torch.max(feature_map, dim=2)[0] for feature_map in x]  # each: (B, num_filters)
        x = torch.cat(x, dim=1)  # (B, num_filters * len(kernel_sizes))
        x = self.dropout(x)
        logits = self.fc(x)
        return logits

embed_dim = 128
num_filters = 100
kernel_sizes = [3, 4, 5]
num_classes = len(le.classes_)
model = CNNTextClassifier(vocab_size, embed_dim, num_classes, kernel_sizes, num_filters)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

optimizer = optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.CrossEntropyLoss()
num_epochs = 10

model.train()
for epoch in range(num_epochs):
    total_loss = 0
    for inputs, targets in train_loader:
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        logits = model(inputs)
        loss = criterion(logits, targets)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * inputs.size(0)
    avg_loss = total_loss / len(train_dataset)
    print(f"Epoch {epoch+1}/{num_epochs} - Loss: {avg_loss:.4f}")

model.eval()
correct = 0
total = 0
with torch.no_grad():
    for inputs, targets in test_loader:
        inputs, targets = inputs.to(device), targets.to(device)
        logits = model(inputs)
        preds = logits.argmax(dim=1)
        correct += (preds == targets).sum().item()
        total += targets.size(0)
print(f"Test Accuracy: {correct/total:.4f}")
    """

        pyperclip.copy(code)

    def help(self):
        """Выводит справку о всех доступных методах."""
        help_message = "Справка по методам:\n"
        for method, description in self.methods_info.items():
            help_message += f"- {method}: {description}\n"
        pyperclip.copy(help_message)
