# 🧠 Async Binance Trading Bot

---

## 📦 Установка

### 1. Клонируй репозиторий

```bash
git clone https://github.com/loujessler/AraviaFintech.git
cd AraviaFintech
poetry install
cp .env-copy .env
```
## ⚙️ Настройка

### 2. Добавить актуальные Binance API ключ и секретный ключ
API_KEY=your_binance_testnet_api_key
API_SECRET=your_binance_testnet_api_secret

## 🧪 Пример запуска
```bash
poetry run python src/main.py \
--symbol BTCUSDT \
--quantity 0.0001 \
--profit 0.25 \
--loss 0.25 \
--wait 60 \
--cooldown 30
```

| Параметр     | Описание                                  |
|--------------|:------------------------------------------|
| --symbol     | Торговая пара (например BTCUSDT)          |
| --quantity   | Кол-во криптовалюты на сделку             |
| --profit     | Порог прибыли в %                         |
| --loss       | Порог убытка в %                          |
| --wait       | Максимальное время удержания (в секундах) |
| --cooldown   | Задержка между сделками после продажи     |