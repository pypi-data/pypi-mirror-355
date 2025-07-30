from openai import OpenAI
import pyperclip

system_prompt_code = '''Ты — эксперт по NLP, помогающий студенту с кодом на экзамене. Отвечай **только кодом**, без пояснений, если не указано иное.  

#### **Формат ответа:**  
- Только код.  
- Мелкие "учебные" недочёты допустимы.  

#### **Стиль кода:**  
- Используй `transformers`, `torch`, `nltk`, `sklearn`.  
- Разрешён "студенческий" стиль: явные циклы, простые пайплайны.  
- Только одинарные кавычки.  
- Код должен выглядеть как ручная работа студента.

#### Примеры запросов и ответов:**  
▸ *'Токенизируй текст с помощью NLTK и построй частотный словарь'*  
→  
```python  
from nltk.tokenize import word_tokenize  
from collections import Counter  
  
text = 'Пример текста для анализа.'  
tokens = word_tokenize(text.lower())  
freq = Counter(tokens)
▸ 'Используй трансформер BERT для классификации текста на PyTorch'
→
 from transformers import BertTokenizer, BertModel  
import torch  
  
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')  
model = BertModel.from_pretrained('bert-base-uncased')  
  
inputs = tokenizer('Example input', return_tensors='pt')  
outputs = model(**inputs)  
 
    '''

system_prompt_theory = '''
            Я сейчас готовлюсь к экзамену по NLP (обработке естественного языка). На экзамене даны теоретические вопросы, на которые нужно отвечать в форме кратких и чётких конспектов. Ответ должен быть:

    Структурированным

    Написанным "от руки" (без ИИ-стиля)

    С примерами, где уместно

    Уместной длины (10–15 минут на переписывание)

    Примеры удачных ответов:
    вопрос: Модуль Transformer: общая архитектура Transformer, работа self-attention и multi-head attention.
    ответ: ###Принцип работы Self-Attention###  
- Каждое слово напрямую сопоставляется со всеми словами в предложении  
- Для каждой пары слов вычисляется вес их взаимосвязи (скалярное произведение «запрос–ключ»), после чего применяется softmax  
- Итоговое представление каждого слова получается как взвешенная сумма векторов значений (Values)  
- Формально:  
$$
  \mathrm{Attention}(Q, K, V) \;=\; \mathrm{softmax}\!\bigl(\tfrac{QK^\top}{\sqrt{d_k}}\bigr)\,V,
$$  
где \(Q\), \(K\), \(V\) — матрицы запросов, ключей и значений соответственно, \(d_k\) — размерность ключей  
###Ключевые преимущества###
- Прямой доступ к любому слою последовательности O(1)
- Параллельное вычисления для всей последовательности
- Динамечский учет контекста

###Идея Multi-Head Attention###  
- Несколько модулей self-attention работают параллельно  
- Каждая «голова» учится искать свой тип связей (синтаксические, семантические, позиционные и т. д.)  
- В стандартных моделях используют \(h=8\)–12 голов  
- Процесс:  
  1. Проекция входного вектора в \(h\) различных пар \((Q_i, K_i, V_i)\)  
  2. Параллельный расчёт  
$$
\mathrm{Attention}(Q, K, V)
$$
     для каждой головы  
  3. Конкатенация выходов всех голов  
  4. Линейное преобразование в вектор исходной размерности

  вопрос: Word2vec: модель CBOW.
ответ: CBOW (Continuous Bag of Words) - архитектура, суть которой: предсказать слово в зависимости от контекста, в котором находится это слово.
То есть максимизирует следующую функцию правдоподобия:
$\frac{1}{T}\sum_{t=1}^{T}{ln\ p(w_{t}|w_{t-K}, ..., w_{t-1}, w_{t+1}, ..., w_{t+K})} → max_{θ}$
Здесь T - общая длина текста, K - длина контекста в примере и θ - настраиваемые параметры.
Для этого обучается модель, где на вход подаются контекст ($2*К$ one-hot векторов), они проходят через скрытый слой для каждого слова получается ембеддинг, после чего все эти эмбединги суммируются в один: $u_c = \sum_{-K≼i≼K, i≠0} u_{w_{i+1}}$.  
Вероятность оценивается через SoftMax: $p(w_{t}|w_{t-K}, ..., w_{t-1}, w_{t+1}, ..., w_{t+K}) = \frac{exp(u_c^Tv_{w_t})}{\sum_i^S{exp(u_c^Tv_{w_i})}}$
Тут $v_{w_i}$ - это выходные эмбеденги для слова $w_i$, S - количество уникальных слов в корпусе.
После обучения мы забираем $v_{w_i}$ - выходные эмбеденги для каждого слова.

Итого CBOW:
* Предсказывает целевое слово по контексту
* Лучше для частых слов
* Быстро обучается
* Усредняет контекст
    '''

themes = '''Темы практики:
1. Предобработка для классификации RNN (Tweeter и обычная)
2. Классификатор и трейнлуп для RNN
3. Custom Embedding (написать слой nn.Embedding ручками)
4. Классифаер на свёртке
5. Ячейка RNN руками (один квадратик)
6. Трейнлуп Матвея
7. Индекс Жакара (Матвей)
8. Индекс Жакара (Ксюша)
9. Word2Vec руками (на CustomEmbedding)
10. Препроцессинг для генерации по словам
11. Модель генерации по словам
12. Датасет для определения части речи
13. Модель и трейнлуп для определения части речи
'''

questions = {
    1 : "import pandas as pd\nimport numpy as np\nimport torch as th\nfrom torch.utils.data import DataLoader, TensorDataset, random_split\nimport re\nimport nltk\nfrom nltk.corpus import stopwords\nfrom nltk.stem import WordNetLemmatizer\nfrom nltk.tokenize import word_tokenize\nimport emoji\nfrom sklearn.preprocessing import LabelEncoder\nfrom collections import Counter\n\nnltk.download('stopwords')\nnltk.download('wordnet')\n\n\ndef clean_tweet(tweet):\n    stop_words = set(stopwords.words('english'))\n    lemmatizer = WordNetLemmatizer()\n\n    tweet = tweet.lower()\n    tweet = re.sub(r'@\\w+', '', tweet)\n    tweet = re.sub(r'http\\S+|www.\\S+', '', tweet)\n    tweet = emoji.replace_emoji(tweet, replace='')\n    tweet = re.sub(r'[^a-z\\s]', '', tweet)\n    tweet = re.sub(r'\\s+', ' ', tweet).strip()\n    tweet = [word for word in tweet.split() if len(word) > 2]\n    tweet = [word for word in tweet if word not in stop_words]\n    tweet = list(set([lemmatizer.lemmatize(word) for word in tweet if word not in stop_words]))\n\n    return tweet\n\ndef clean_usual(text):\n    STOPWORDS = set(stopwords.words('english'))\n    text = str(text).lower()\n    text = re.sub(r'[^\\w\\s]', '', text)\n    tokens = word_tokenize(text)\n    tokens = [t for t in tokens if t not in STOPWORDS]\n    return tokens\n\ndef encode_tweet(tweet, vocab, max_len=None, pad_token='<PAD>'):\n    encoded = [vocab.get(word, vocab['<UNK>']) for word in tweet]\n    encoded = encoded + [vocab[pad_token]] * (max_len - len(encoded))\n\n    return encoded\n\n\ndata = pd.read_csv('news.csv')# csv path\ndata['clean_text'] = data['Description'].apply(clean_tweet) # text column name\ndata = data.drop(data[data['clean_text'].apply(len) == 0].index)\n\nwords_count = Counter([word for tweet in data['clean_text'] for word in tweet])\n\nvocab = {word: i+2 for i, (word, _) in enumerate(words_count.items())}\nvocab['<PAD>'] = 0\nvocab['<UNK>'] = 1\n\nmax_len = data.clean_text.apply(len).max()\ndata['encoded_text'] = [encode_tweet(t, vocab, max_len) for t in data['clean_text']]\n\nLE = LabelEncoder()\ndata['labels'] = LE.fit_transform(data['Class Index']) # target column name\n\n\ndataset = TensorDataset(\n    th.tensor(data['encoded_text'].tolist()),\n    th.tensor(data['labels'].tolist())\n)\n\ntrain_dataset, test_dataset = random_split(\n    dataset, [0.8, 0.2],\n    generator=th.Generator().manual_seed(42)\n)\n\ntrain_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)\ntest_loader = DataLoader(test_dataset, batch_size=64, shuffle=True)\n",
    2 : "import torch.nn as nn\n\nclass classifier(nn.Module):\n    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim):\n        super().__init__()\n        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)\n        self.rnn = nn.GRU(embed_dim, hidden_dim, batch_first=True)\n        self.dropout = nn.Dropout(0.3)\n        self.gelu = nn.ReLU()\n        self.fc = nn.Linear(hidden_dim, output_dim)\n    \n    def forward(self, x):\n        x = self.embedding(x)  \n        output, h_n = self.rnn(x)  \n        out = self.gelu(output[:, -1, :])  \n        return self.fc(out)\n    \n\nimport matplotlib.pyplot as plt\n# import plotly.graph_objects as go\nfrom tqdm.notebook import tqdm, trange\n\ndef trainloop(model, train_loader, test_loader, criterion, optimizer, num_epochs=5, log_every=1, early_stop=3, draw=False):\n    device = th.device('cuda' if th.cuda.is_available() else 'cpu')\n    model.train().to(device)\n    best_test_acc = 0\n    no_improve_epochs = 0\n\n    train_acc_list = []\n    test_acc_list = []\n    epoch_list = []\n\n    for epoch in trange(1, num_epochs + 1):\n        total_loss = 0\n        correct = 0\n        total = 0\n\n        for x_batch, y_batch in tqdm(train_loader, leave=False):\n            optimizer.zero_grad()\n            outputs = model(x_batch.to(device))\n            loss = criterion(outputs, y_batch.to(device))\n            loss.backward()\n            optimizer.step()\n\n            total_loss += loss.item()\n            _, preds = th.max(outputs, 1)\n            correct += (preds.to(device) == y_batch.to(device)).sum().item()\n            total += y_batch.size(0)\n\n        train_acc = correct / total\n\n        test_correct = 0\n        test_total = 0\n        model.eval()\n        with th.no_grad():\n            for x_batch, y_batch in test_loader:\n                outputs = model(x_batch.to(device))\n                _, preds = th.max(outputs, 1)\n                test_correct += (preds == y_batch.to(device)).sum().item()\n                test_total += y_batch.size(0)\n        test_acc = test_correct / test_total\n        model.train()\n\n        train_acc_list.append(train_acc)\n        test_acc_list.append(test_acc)\n        epoch_list.append(epoch)\n\n        if epoch % log_every == 0 or epoch == 1 or epoch == num_epochs:\n            print(f'epoch {epoch}/{num_epochs} | loss: {total_loss:.4f} | train acc: {train_acc:.4f} | test acc: {test_acc:.4f}')\n\n        if test_acc > best_test_acc:\n            best_test_acc = test_acc\n            no_improve_epochs = 0\n        else:\n            no_improve_epochs += 1\n            if no_improve_epochs >= early_stop:\n                print(f'early stopping {epoch}')\n                break\n\n    if draw:\n        plt.plot(epoch_list, train_acc_list, marker='o', label='train acc')\n        plt.plot(epoch_list, test_acc_list, marker='o', label='test acc')\n        plt.legend()\n        plt.grid(True)\n        plt.show()\n        # fig = go.Figure()\n        # fig.add_trace(go.Scatter(x=epoch_list, y=train_acc_list, mode='lines+markers', name='train acc'))\n        # fig.add_trace(go.Scatter(x=epoch_list, y=test_acc_list, mode='lines+markers', name='test acc'))\n        # fig.update_layout(\n        #     xaxis_title='epoch',\n        #     yaxis_title='accuracy',\n        #     template='plotly_white',\n        #     yaxis=dict(range=[0, 1])\n        # )\n        # fig.show()\n\n    return model\n\n\nmodel = classifier(vocab_size=len(vocab), embed_dim=128, hidden_dim=256, output_dim=data['labels'].nunique())\ncriterion = nn.CrossEntropyLoss()\noptimizer = th.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)\n\nmodel = trainloop(model, train_loader, test_loader, criterion, optimizer, num_epochs=35, log_every=1, early_stop=7, draw=True)\n\n",
    3 : "class CustomEmbedding(Module):\n    def __init__(self, num_embeddings, embedding_dim, padding_idx=None, max_norm=None, norm_type=2.0):\n        super(CustomEmbedding, self).__init__()\n        self.num_embeddings = num_embeddings\n        self.embedding_dim = embedding_dim\n        self.padding_idx = padding_idx\n        self.max_norm = max_norm\n        self.norm_type = norm_type\n\n        self.weight = Parameter(th.Tensor(num_embeddings, embedding_dim))\n        self.reset_parameters()\n\n    def reset_parameters(self):\n        nn.init.normal_(self.weight)\n        if self.padding_idx is not None:\n            with th.no_grad():\n                self.weight[self.padding_idx].fill_(0)\n\n    def forward(self, input):\n        if self.max_norm is not None:\n            with th.no_grad():\n                norms = th.norm(self.weight, p=self.norm_type, dim=1, keepdim=True)\n                mask = norms > self.max_norm\n\n                scaled = self.weight * (self.max_norm / (norms + 1e-7))\n                self.weight.data = th.where(mask, scaled, self.weight)\n\n        embeddings = self.weight[input]\n\n        if self.padding_idx is not None:\n            mask = (input == self.padding_idx).unsqueeze(-1)\n            embeddings = embeddings.masked_fill(mask, 0.0)\n\n        return embeddings\n",
    4 : "class classifier(nn.Module):\n    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim):\n        super().__init__()\n        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)\n        self.conv1 = nn.Conv1d(embed_dim, hidden_dim, kernel_size=3)\n        self.relu = nn.ReLU()\n        self.maxpool = nn.MaxPool1d(kernel_size=2)\n        self.flatten = nn.Flatten()\n\n        self.dropout = nn.Dropout(0.5)\n        self.fc = nn.Linear(..., output_dim) # своя размерность x.shape после flatten\n    \n    def forward(self, x):\n        x = self.embedding(x)  \n        x = x.permute(0, 2, 1)\n        x = self.conv1(x)\n        x = self.relu(x)\n        x = self.maxpool(x)\n        x = self.flatten(x)\n        out = self.fc(self.dropout(x))  \n        return out\n",
    5 : "class RNNCell(nn.Module):\n    def __init__(self, input_size, hidden_size):\n        super().__init__()\n        self.input_layer = nn.Linear(input_size, hidden_size)\n        self.hidden_layer = nn.Linear(hidden_size, hidden_size)\n        self.tanh = nn.Tanh()\n\n    def forward(self, x, hidden):\n        combined = self.input_layer(x) + self.hidden_layer(hidden)\n        new_hidden = self.tanh(combined)\n        return new_hidden\n",
    6 : "import torchmetrics as M\nepochs=20\nearly_stop=3\n\nbest_val_score = 0\nbest_model = 0\npatience = 0\n\ntrain_losses = []\ntrain_accuracies = []\ntest_accuracies = []\n\nfor epoch in tqdm(range(epochs), desc='Epochs'):\n    model.train()\n    train_loss = M.MeanMetric()\n\n    metric = M.Accuracy(task='multiclass', num_classes=4)\n    train_acc = M.MeanMetric()\n    test_acc = M.MeanMetric()\n\n    for x_batch, y_batch in tqdm(train_loader, desc='Training', leave=False):\n        optimizer.zero_grad()\n        y_pred = model(x_batch)\n        loss = criterion(y_pred, y_batch)\n        accuracy = metric(th.argmax(y_pred, dim=1), y_batch)\n        loss.backward()\n        optimizer.step()\n\n        train_loss.update(loss.item())\n        train_acc.update(accuracy)\n\n    model.eval()\n    with th.no_grad():\n        for x_batch, y_batch in tqdm(test_loader, desc='Validation', leave=False):\n            y_pred = model(x_batch)\n            accuracy = metric(th.argmax(y_pred, dim=1), y_batch)\n            \n            test_acc.update(accuracy)\n\n    train_losses.append(train_loss.compute())\n    train_accuracies.append(train_acc.compute())\n    test_accuracies.append(test_acc.compute())\n    \n    if patience < early_stop:\n        if best_val_score < test_accuracies[-1]:\n            best_model = model  \n            best_val_score = test_accuracies[-1]\n            patience = 0\n        else:\n            patience += 1\n    else:\n        print(f'Early Stooping on epoch: {epoch}')\n        break \n\n    print(f'| Epoch {epoch} | Train Loss: {train_loss.compute():.4f} | Train Acc: {train_acc.compute():.3f} | Test Acc: {test_acc.compute():.3f}')\n",
    7 : "class classifier(nn.Module):\n    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim):\n        super().__init__()\n        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)\n        self.fc1 = nn.Linear(embed_dim, hidden_dim)\n        self.relu = nn.ReLU()\n        self.dropout = nn.Dropout(0.2)\n        self.fc = nn.Linear(hidden_dim, output_dim)\n    \n    def forward(self, x):\n        x = self.embedding(x).mean(axis=1)\n        x = self.fc1(x)   \n        x = self.relu(x)\n        out = self.fc(self.dropout(x))  \n        return out\n\ntest_jac = M.MeanMetric()\njaccard = M.JaccardIndex(task='multiclass', num_classes=4) \nwith th.no_grad():\n    for x_batch, y_batch in tqdm(test_loader, desc='Validation', leave=False):\n        y_pred = model(x_batch)\n        jac = metric(th.argmax(y_pred, dim=1), y_batch)\n        \n        test_jac.update(jac)\n\nprint(f'Индекс Жакара: {test_jac.compute():.4f}')\n",
    8 : "model.eval()\nall_embeddings = []\n\nwith th.no_grad():\n    for batch_x, _ in DataLoader(dataset, batch_size=128):\n        emb = model.embedding(batch_x.to(model.embedding.weight.device)).mean(dim=1)\n        all_embeddings.append(emb.cpu())\n\nall_embeddings = th.cat(all_embeddings, dim=0).numpy()\n\ndef jaccard_top_k(a, b, k=3):\n    top_a = set(np.argsort(a)[-k:])\n    top_b = set(np.argsort(b)[-k:])\n    return len(top_a & top_b) / len(top_a | top_b)\n\njac_similarities = []\npairs = []\n\nfor i in range(len(all_embeddings)):\n    for j in range(i + 1, len(all_embeddings)):\n        sim = jaccard_top_k(all_embeddings[i], all_embeddings[j])\n        jac_similarities.append(sim)\n        pairs.append((i, j))\n\nsent1, sent2 = pairs[np.argmax(jac_similarities)]\nprint(f'Первый текст: {data['text'].iloc[sent1]}\n\nВторой текст: {data['text'].iloc[sent2]}\n\nНаивысшее значение индекса Жаккара: {np.max(jac_similarities)}')\n",
    9 : "class Word2Vec(nn.Module):\n    def __init__(self, vocab_size, embedding_dim):\n        super(Word2Vec, self).__init__()\n        self.embeddings = CustomEmbedding(vocab_size, embedding_dim)\n        self.linear = nn.Linear(embedding_dim, vocab_size)\n\n    def forward(self, x):\n        embeds = self.embeddings(x)\n        out = self.linear(embeds)\n        return F.log_softmax(out, dim=1)\n",
    10 : "def tokenize(text):\n    text = text.lower()\n    text = re.sub(r'[^a-zA-Z0-9\\s]', '', text)\n    return text.split()\n\ndata['clean_text'] = data.apply(tokenize)\nwords_count = Counter([word for tweet in data['clean_text'] for word in tweet])\n\nword2idx = {word: i+2 for i, (word, _) in enumerate(words_count.items())}\nvocab['<PAD>'] = 0\nvocab['<UNK>'] = 1\nidx2word = {idx:word for word, idx in word2idx.items()}\n\nseq_length = 7\n\ninputs = []\ntargets = []\n\nfor tokens in data['clean_text']:\n    token_ids = [word2idx[word] for word in tokens if word in word2idx]\n    for i in range(len(token_ids) - seq_length):\n        inputs.append(token_ids[i:i+seq_length])\n        targets.append(token_ids[i+seq_length])\n\nX = th.tensor(inputs)\ny = th.tensor(targets)\n\ndataset = TensorDataset(X, y)\ndataloader = DataLoader(dataset, batch_size=64, shuffle=True)\n",
    11 : "class TextGenModel(nn.Module):\n    def __init__(self, vocab_size, embed_dim, hidden_dim):\n        super().__init__()\n        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)\n        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)\n        self.fc = nn.Linear(hidden_dim, vocab_size)\n\n    def forward(self, x):\n        x = self.embedding(x)\n        output, (h, c) = self.lstm(x)\n        logits = self.fc(output[:, -1, :])\n        return logits\n\nmodel = TextGenModel(vocab_size=len(word2idx), embed_dim=128, hidden_dim=256)\n\ncriterion = nn.CrossEntropyLoss()\noptimizer = th.optim.Adam(model.parameters(), lr=0.001)\n\nepochs = 20\nearly_stop = 3\nbest_val_loss = float('inf') \nbest_model_state = None       \npatience = 0\n\ntrain_losses = []\nval_losses = []\n\nfor epoch in tqdm(range(epochs), desc='Epochs'):\n    model.train()\n    train_loss = M.MeanMetric()\n\n    for x_batch, y_batch in tqdm(train_loader, desc='Training', leave=False):\n        x_batch, y_batch = x_batch, y_batch\n\n        optimizer.zero_grad()\n        y_pred = model(x_batch)\n        loss = criterion(y_pred, y_batch)\n        loss.backward()\n        optimizer.step()\n\n        train_loss.update(loss.item())\n\n    model.eval()\n    val_loss = M.MeanMetric()\n\n    with th.no_grad():\n        for x_batch, y_batch in tqdm(test_loader, desc='Validation', leave=False):\n            x_batch, y_batch = x_batch, y_batch\n            y_pred = model(x_batch)\n            loss = criterion(y_pred, y_batch)\n            val_loss.update(loss.item())\n\n    train_losses.append(train_loss.compute())\n    val_losses.append(val_loss.compute())\n\n    if patience < early_stop:\n        if val_losses[-1] < best_val_loss:\n            best_val_loss = val_losses[-1]\n            best_model_state = model\n            patience = 0\n        else:\n            patience += 1\n    else:\n        print(f'Early stopping on epoch: {epoch}')\n        break\n\n    print(f'| Epoch {epoch} | Train Loss: {train_loss.compute():.4f} | Val Loss: {val_loss.compute():.4f}')\n\n\ndef generate_text(prompt, model, word2idx, idx2word, seq_length=5, max_words=20):\n    model.eval()\n    model\n\n    tokens = tokenize(prompt)\n    token_ids = [word2idx.get(w, 0) for w in tokens]\n\n    for _ in range(max_words):\n        input_ids = token_ids[-seq_length:]\n        if len(input_ids) < seq_length:\n            input_ids = [0] * (seq_length - len(input_ids)) + input_ids\n        \n        input_tensor = th.tensor([input_ids], dtype=th.long)\n        with th.no_grad():\n            logits = model(input_tensor)\n            next_word_id = th.argmax(logits, dim=-1).item()\n\n        token_ids.append(next_word_id)\n\n        if idx2word[next_word_id] in ['<PAD>', '<UNK>']:\n            break\n\n    generated_words = [idx2word.get(i, '<UNK>') for i in token_ids]\n    return ' '.join(generated_words)\n",
    12 : "import json\nimport torch\nfrom torch.utils.data import Dataset, DataLoader, random_split\nfrom torch.nn.utils.rnn import pad_sequence\nfrom collections import defaultdict\nimport torch.nn as nn\nfrom sklearn.metrics import classification_report\n\nwith open('/content/pos.json') as f:\n    data = json.load(f)\n\ndataset = []\nfor i in data:\n    num_words = len(i['sentence'].lower().split())\n    num_tags = len(i['tags'])\n    if num_words == num_tags:\n        dataset.append((i['sentence'].split(),  i['tags']))\n\ndata = dataset\n\nword_counts = defaultdict(int)\ntag_counts = defaultdict(int)\nfor sentence, tags in data:\n    for word in sentence:\n        word_counts[word] += 1\n    for tag in tags:\n        tag_counts[tag] += 1\n\n# Создаем словари\nword2idx = {'<PAD>': 0, '<UNK>': 1}\nfor word in word_counts:\n    word2idx[word] = len(word2idx)\n\ntag2idx = {'<PAD>': 0}\nfor tag in tag_counts:\n    tag2idx[tag] = len(tag2idx)\n\nidx2tag = {idx: tag for tag, idx in tag2idx.items()}\n\n# Параметры\nVOCAB_SIZE = len(word2idx)\nTAGSET_SIZE = len(tag2idx)\nEMBED_DIM = 128\nHIDDEN_DIM = 64\n\n\nclass POSDataset(Dataset):\n    def __init__(self, data, word2idx, tag2idx):\n        self.data = []\n        for sentence, tags in data:\n            word_ids = [word2idx.get(word, word2idx['<UNK>']) for word in sentence]\n            tag_ids = [tag2idx[tag] for tag in tags]\n            self.data.append((torch.tensor(word_ids), torch.tensor(tag_ids)))\n\n    def __len__(self):\n        return len(self.data)\n\n    def __getitem__(self, idx):\n        return self.data[idx]\n\ndef collate_fn(batch):\n    inputs = [item[0] for item in batch]\n    targets = [item[1] for item in batch]\n    inputs_padded = pad_sequence(inputs, batch_first=True, padding_value=word2idx['<PAD>'])\n    targets_padded = pad_sequence(targets, batch_first=True, padding_value=tag2idx['<PAD>'])\n    return inputs_padded, targets_padded\n\ndataset = POSDataset(data, word2idx, tag2idx)\ndataloader = DataLoader(dataset, batch_size=32, collate_fn=collate_fn)\n\n\ntrain_size = int(0.8 * len(data))\nval_size = len(data) - train_size\ntrain_data, val_data = random_split(\n    data,\n    [train_size, val_size],\n    generator=torch.Generator().manual_seed(42)\n)\n\ntrain_dataset = POSDataset(train_data, word2idx, tag2idx)\nval_dataset = POSDataset(val_data, word2idx, tag2idx)\n\ntrain_loader = DataLoader(\n    train_dataset,\n    batch_size=32,\n    collate_fn=collate_fn,\n    shuffle=True\n)\n\nval_loader = DataLoader(\n    val_dataset,\n    batch_size=32,\n    collate_fn=collate_fn\n)\n",
    13 : "class LSTMTagger(nn.Module):\n    def __init__(self, embedding_dim, hidden_dim, vocab_size, tagset_size):\n        super().__init__()\n        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=word2idx['<PAD>'])\n        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True, bidirectional=False)\n        self.fc = nn.Linear(hidden_dim, tagset_size)\n\n    def forward(self, x):\n        embeds = self.embedding(x)\n        lstm_out, _ = self.lstm(embeds)\n        tag_space = self.fc(lstm_out)\n        return tag_space\n\nmodel = LSTMTagger(EMBED_DIM, HIDDEN_DIM, VOCAB_SIZE, TAGSET_SIZE)\n\n\ndevice = torch.device('cuda' if torch.cuda.is_available() else 'cpu')\nmodel.to(device)\ncriterion = nn.CrossEntropyLoss(ignore_index=tag2idx['<PAD>'])\noptimizer = torch.optim.Adam(model.parameters(), lr=0.001)\n\nnum_epochs = 20\nbest_val_loss = float('inf')\nfor epoch in range(num_epochs):\n    # Обучение\n    model.train()\n    train_loss = 0.0\n    for inputs, targets in train_loader:\n        inputs, targets = inputs.to(device), targets.to(device)\n        optimizer.zero_grad()\n        outputs = model(inputs)\n        loss = criterion(outputs.view(-1, TAGSET_SIZE), targets.view(-1))\n        loss.backward()\n        optimizer.step()\n        train_loss += loss.item()\n\n    val_loss = 0.0\n    model.eval()\n    with torch.no_grad():\n        for inputs, targets in val_loader:\n            inputs, targets = inputs.to(device), targets.to(device)\n            outputs = model(inputs)\n            loss = criterion(outputs.view(-1, TAGSET_SIZE), targets.view(-1))\n            val_loss += loss.item()\n\n    # Средние потери\n    train_loss /= len(train_loader)\n    val_loss /= len(val_loader)\n\n    print(f'Epoch {epoch+1}/{num_epochs}')\n    print(f'Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}')\n\n\ndef evaluate(model, loader, idx2tag, device):\n    model.eval()\n    y_true = []\n    y_pred = []\n\n    with torch.no_grad():\n        for inputs, targets in loader:\n            inputs, targets = inputs.to(device), targets.to(device)\n            outputs = model(inputs)\n            predictions = torch.argmax(outputs, dim=-1)\n\n            # Убираем паддинг\n            mask = targets != 0\n            for i in range(targets.shape[0]):\n                valid_indices = mask[i].nonzero(as_tuple=True)[0]\n                true_tags = targets[i][valid_indices].cpu().numpy()\n                pred_tags = predictions[i][valid_indices].cpu().numpy()\n\n                y_true.extend([idx2tag[tag] for tag in true_tags])\n                y_pred.extend([idx2tag[tag] for tag in pred_tags])\n\n    report = classification_report(\n        y_true,\n        y_pred,\n        zero_division=0\n    )\n    return report\n\n# Расчет метрик на валидационной выборке\nval_report = evaluate(model, val_loader, idx2tag, device)\nprint('Validation Report:')\nprint(val_report)\n\n# Пример предсказания\ndef predict(model, sentence, word2idx, idx2tag, device):\n    model.eval()\n    words = [word.lower() for word in sentence]\n    word_ids = [word2idx.get(word, word2idx['<UNK>']) for word in words]\n    tensor = torch.tensor(word_ids).unsqueeze(0).to(device)\n\n    with torch.no_grad():\n        output = model(tensor)\n    predicted_ids = torch.argmax(output, dim=-1).squeeze(0).cpu().numpy()\n\n    return [idx2tag[idx] for idx in predicted_ids]\n\n# Тестирование\ntest_sentence = 'She runs fast in the morning'.split()\npredicted_tags = predict(model, test_sentence, word2idx, idx2tag, device)\nprint('\nTest Sentence:', test_sentence)\nprint('Predicted Tags:', predicted_tags)\n",
    
}

def info():
    '''
    Добавляет в буфер обмена список тем, по которым потом обращаться при помощи функции get(n), где n - номер темы
    '''
    pyperclip.copy(themes)

def info_cl():
    '''
    Создает класс, в документации которого список тем, по которым потом обращаться при помощи функции get(n), где n - номер темы
    '''
    class sol():
        __doc__ = themes
        
    return sol()

def get(n):
    '''
    Добавляет в буфер обмена ответ по теме (n - номер темы; m = 0 => теория, m = 1 => практика)
    '''
    if 0 < n < len(questions) + 1:
        pyperclip.copy(questions[n])
    else:
        pyperclip.copy('Неправильный выбор номера темы')


def get_cl(n):
    '''
    Создает объект класса, в документации (shift + tab) которого лежит ответ по теме (n - номер темы; m = 0 => теория, m = 1 => практика)
    '''
    class sol:
        def __init__(self, n):
            self.n = n
            self.doc = questions[self.n]

        @property
        def __doc__(self):
            return self.doc  

    return sol(n)

def api_call(prompt, system_pr=True, r1=False, code=True):
    client = OpenAI(api_key="sk-b1cd11f28cf9473296a9a9a4074de9ee", base_url="https://api.deepseek.com")
    model = 'deepseek-reasoner' if r1 else 'deepseek-chat'
    if system_pr:
        if code:
            system_prompt = system_prompt_code
            temperature = 0
        else:
            system_prompt = system_prompt_theory
            temperature = 1
    else:
        system_prompt = ''
        temperature = 1
    response = client.chat.completions.create(
        model = model,
        messages= [
            {'role' : 'system', 'content' : system_prompt},
            {"role": "user", "content": prompt}
            ],
        stream=False,
        temperature=temperature)
    return response.choices[0].message.content

def d_get(prompt, system_pr=True, r1=False, code=True):
    '''
    Добавляет в буфер обмена респонс модели по промпту
    system_pr : True => использовать мои систем промпты (я адаптировал их для экза), False : не использовать
    r1 : True => использовать reasoning, False => использовать обычный дипсик
    code : True => систем промпт для кода, False => систем промпт для теории
    '''
    pyperclip.copy(api_call(prompt, system_pr, r1, code))

class d_get_cl:
    '''
    Добавляет в документацию класса респонс модели по промпту
    system_pr : True => использовать мои систем промпты (я адаптировал их для экза), False : не использовать
    r1 : True => использовать reasoning, False => использовать обычный дипсик
    code : True => систем промпт для кода, False => систем промпт для теории
    '''
    def __init__(self, prompt, system_pr=True, r1=False, code=True):
        self.doc = api_call(prompt, system_pr, r1, code)

    @property
    def __doc__(self):
        return self.doc  
