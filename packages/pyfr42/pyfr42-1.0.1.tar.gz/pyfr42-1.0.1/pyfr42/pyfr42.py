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

themes = '''
Темы практики:
1. Предобработка для классификации RNN (Tweeter и обычная)
2. Классификатор и трейнлуп для RNN
'''

questions = {
    1 : "import pandas as pd\nimport numpy as np\nimport torch as th\nfrom torch.utils.data import DataLoader, TensorDataset, random_split\nimport re\nimport nltk\nfrom nltk.corpus import stopwords\nfrom nltk.stem import WordNetLemmatizer\nfrom nltk.tokenize import word_tokenize\nimport emoji\nfrom sklearn.preprocessing import LabelEncoder\nfrom collections import Counter\n\nnltk.download('stopwords')\nnltk.download('wordnet')\n\n\ndef clean_tweet(tweet):\n    stop_words = set(stopwords.words('english'))\n    lemmatizer = WordNetLemmatizer()\n\n    tweet = tweet.lower()\n    tweet = re.sub(r'@\\w+', '', tweet)\n    tweet = re.sub(r'http\\S+|www.\\S+', '', tweet)\n    tweet = emoji.replace_emoji(tweet, replace='')\n    tweet = re.sub(r'[^a-z\\s]', '', tweet)\n    tweet = re.sub(r'\\s+', ' ', tweet).strip()\n    tweet = [word for word in tweet.split() if len(word) > 2]\n    tweet = [word for word in tweet if word not in stop_words]\n    tweet = list(set([lemmatizer.lemmatize(word) for word in tweet if word not in stop_words]))\n\n    return tweet\n\ndef clean_usual(text):\n    STOPWORDS = set(stopwords.words('english'))\n    text = str(text).lower()\n    text = re.sub(r'[^\\w\\s]', '', text)\n    tokens = word_tokenize(text)\n    tokens = [t for t in tokens if t not in STOPWORDS]\n    return tokens\n\ndef encode_tweet(tweet, vocab, max_len=None, pad_token='<PAD>'):\n    encoded = [vocab.get(word, vocab['<UNK>']) for word in tweet]\n    encoded = encoded + [vocab[pad_token]] * (max_len - len(encoded))\n\n    return encoded\n\n\ndata = pd.read_csv('news.csv')# csv path\ndata['clean_text'] = data['Description'].apply(clean_tweet) # text column name\ndata = data.drop(data[data['clean_text'].apply(len) == 0].index)\n\nwords_count = Counter([word for tweet in data['clean_text'] for word in tweet])\n\nvocab = {word: i+2 for i, (word, _) in enumerate(words_count.items())}\nvocab['<PAD>'] = 0\nvocab['<UNK>'] = 1\n\nmax_len = data.clean_text.apply(len).max()\ndata['encoded_text'] = [encode_tweet(t, vocab, max_len) for t in data['clean_text']]\n\nLE = LabelEncoder()\ndata['labels'] = LE.fit_transform(data['Class Index']) # target column name\n\n\ndataset = TensorDataset(\n    th.tensor(data['encoded_text'].tolist()),\n    th.tensor(data['labels'].tolist())\n)\n\ntrain_dataset, test_dataset = random_split(\n    dataset, [0.8, 0.2],\n    generator=th.Generator().manual_seed(42)\n)\n\ntrain_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)\ntest_loader = DataLoader(test_dataset, batch_size=64, shuffle=True)\n",
    2 : 'import torch.nn as nn\n\nclass classifier(nn.Module):\n    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim):\n        super().__init__()\n        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)\n        self.rnn = nn.GRU(embed_dim, hidden_dim, batch_first=True)\n        self.dropout = nn.Dropout(0.3)\n        self.gelu = nn.ReLU()\n        self.fc = nn.Linear(hidden_dim, output_dim)\n    \n    def forward(self, x):\n        x = self.embedding(x)  \n        output, h_n = self.rnn(x)  \n        out = self.gelu(output[:, -1, :])  \n        return self.fc(out)\n    \n\nimport matplotlib.pyplot as plt\n# import plotly.graph_objects as go\nfrom tqdm.notebook import tqdm, trange\n\ndef trainloop(model, train_loader, test_loader, criterion, optimizer, num_epochs=5, log_every=1, early_stop=3, draw=False):\n    device = th.device(\'cuda\' if th.cuda.is_available() else \'cpu\')\n    model.train().to(device)\n    best_test_acc = 0\n    no_improve_epochs = 0\n\n    train_acc_list = []\n    test_acc_list = []\n    epoch_list = []\n\n    for epoch in trange(1, num_epochs + 1):\n        total_loss = 0\n        correct = 0\n        total = 0\n\n        for x_batch, y_batch in tqdm(train_loader, leave=False):\n            optimizer.zero_grad()\n            outputs = model(x_batch.to(device))\n            loss = criterion(outputs, y_batch.to(device))\n            loss.backward()\n            optimizer.step()\n\n            total_loss += loss.item()\n            _, preds = th.max(outputs, 1)\n            correct += (preds.to(device) == y_batch.to(device)).sum().item()\n            total += y_batch.size(0)\n\n        train_acc = correct / total\n\n        test_correct = 0\n        test_total = 0\n        model.eval()\n        with th.no_grad():\n            for x_batch, y_batch in test_loader:\n                outputs = model(x_batch.to(device))\n                _, preds = th.max(outputs, 1)\n                test_correct += (preds == y_batch.to(device)).sum().item()\n                test_total += y_batch.size(0)\n        test_acc = test_correct / test_total\n        model.train()\n\n        train_acc_list.append(train_acc)\n        test_acc_list.append(test_acc)\n        epoch_list.append(epoch)\n\n        if epoch % log_every == 0 or epoch == 1 or epoch == num_epochs:\n            print(f"epoch {epoch}/{num_epochs} | loss: {total_loss:.4f} | train acc: {train_acc:.4f} | test acc: {test_acc:.4f}")\n\n        if test_acc > best_test_acc:\n            best_test_acc = test_acc\n            no_improve_epochs = 0\n        else:\n            no_improve_epochs += 1\n            if no_improve_epochs >= early_stop:\n                print(f"early stopping {epoch}")\n                break\n\n    if draw:\n        plt.plot(epoch_list, train_acc_list, marker=\'o\', label=\'train acc\')\n        plt.plot(epoch_list, test_acc_list, marker=\'o\', label=\'test acc\')\n        plt.legend()\n        plt.grid(True)\n        plt.show()\n        # fig = go.Figure()\n        # fig.add_trace(go.Scatter(x=epoch_list, y=train_acc_list, mode=\'lines+markers\', name=\'train acc\'))\n        # fig.add_trace(go.Scatter(x=epoch_list, y=test_acc_list, mode=\'lines+markers\', name=\'test acc\'))\n        # fig.update_layout(\n        #     xaxis_title=\'epoch\',\n        #     yaxis_title=\'accuracy\',\n        #     template=\'plotly_white\',\n        #     yaxis=dict(range=[0, 1])\n        # )\n        # fig.show()\n\n    return model\n\n\nmodel = classifier(vocab_size=len(vocab), embed_dim=128, hidden_dim=256, output_dim=data[\'labels\'].nunique())\ncriterion = nn.CrossEntropyLoss()\noptimizer = th.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)\n\nmodel = trainloop(model, train_loader, test_loader, criterion, optimizer, num_epochs=35, log_every=1, early_stop=7, draw=True)\n'
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
