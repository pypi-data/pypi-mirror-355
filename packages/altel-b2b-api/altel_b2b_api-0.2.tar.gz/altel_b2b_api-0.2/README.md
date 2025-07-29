# Altel B2B API Client (Python)

#### Разработчик: [@litemat](https://github.com/litemat)

#### Версия: 0.1

---

#### IMPORTANT DISCLAIMER! (ENGLISH):

⚠️ This project is an unofficial tool for educational or internal use. \
⚠️ Use at your own risk. The author is not affiliated with Altel.kz or its partners. \
⚠️ This code interacts with web services that may be protected by terms of service.

#

#### ВАЖНЫЙ ДИСКЛЕЙМЕР! (РУССКИЙ):

⚠️ Этот проект является неофициальным инструментом, предназначенным для образовательных или внутренних целей. \
⚠️ Используйте на свой страх и риск. Автор не имеет отношения к Altel.kz или его партнёрам. \
⚠️ Этот код взаимодействует с веб-сервисами, которые могут быть защищены условиями использования.

#

#### МАҢЫЗДЫ ЕСКЕРТУ! (ҚАЗАҚША):

⚠️ Бұл жоба — оқу немесе ішкі мақсаттарға арналған ресми емес құрал. \
⚠️ Пайдалану — сіздің тәуекеліңізде. Автор Altel.kz немесе оның серіктестерімен байланысы жоқ. \
⚠️ Бұл код пайдалану шарттарымен қорғалған веб-сервистермен әрекеттесуі мүмкін.

---

## Возможности (v0.1)

Библиотека предоставляет удобный интерфейс для взаимодействия с Altel B2B API — системой управления абонентами и услугами сотового оператора Altel (Казахстан). Основной акцент сделан на простоту авторизации, отправку POST/GET-запросов и работу с абонентскими данными.

- 🔐 Авторизация через API (автоматическое получение токена)
- 🔍 Поиск абонентов по номеру телефона
- 📄 Получение детальной информации об абоненте (ID, тариф, статус, баланс, квота и т.д.)
- 🔒 Блокировка и разблокировка абонентов

> ⚠️ Функционал библиотеки будет активно расширяться: добавление статистики трафика, массовых операций и прочего.

---

## Установка

```bash
pip install altel_b2b_api
```

---

## Пример использования

```python
from altel_b2b_api import AltelB2B

client = AltelB2B(username="747XXXXXXX", password="ваш_пароль")

if client.login():
    subs = client.search_subscriber(number="7001234567")
    if subs:
        print(subs)
```

---

## Интерфейс API

### Авторизация

```python
client.login() -> str
```

Авторизуется через `https://altel.kz/b2b/main/api/auth/login` и сохраняет access_token для дальнейших запросов.

### Поиск абонентов

```python
client.search_subscriber(number: str) -> str
```

Ищет абонента по номеру телефона. Возвращает список словарей с полями:

- `subscriberId`
- `employee`
- `icc`
- `msisdn`
- `fee`
- `activationDate`
- `status`
- `tariffId`
- `tariffName`
- `balance`
- `nextWriteOff`
- `clientTypeId`
- `account`
- `balanceLevel`
- `contractNumber`
- `quota`
- `quotaUnused`
- `resources`

---

### Блокировка / Разблокировка

```python
client.block(msisdn: str) -> str
client.unblock(msisdn: str) -> str
```

Изменяет статус абонента через соответствующие API-эндпоинты.

---

## Архитектура

- Используется `cloudscraper` для обхода защиты Cloudflare
- Все сессии повторно используют полученные cookie и токен
- Конфигурация разделена по URL API-эндпоинтов (логин, блокировка, поиск и т.д.)

---

## Планы на развитие

- [ ] Работа с детализацией по услугам
- [ ] История операций
- [ ] Массовая обработка абонентов (batch requests)
- [ ] Мониторинг и отчёты
- [ ] Telegram / Webhook интеграции

---

## Полная документация

### Класс: `AltelB2B`

```python
client = AltelB2B(username="700XXXXXXX", password="ваш_пароль")
```

### `login() -> str`

Авторизация через Cloudflare и API. Сохраняет токены, если успешно.

### `all_subscribers(limit: int = 0) -> str`

Получает всех абонентов.

- `limit=0` — получить всех
- `limit=N` — получить N первых

### `search_subscriber(number: str) -> str`

Поиск абонента по номеру.

- `number`: формат 700XXXXXXX

### `change_status(number: str, status_code: int) -> str`

Изменяет статус абонента (Не рекомендован к использованию напрямую):

- `status_code=2` — блокировка
- `status_code=1` — разблокировка

Возвращает:

```json
{
	"success": true,
	"subscriberId": 12345678,
	"msisdn": "7001234567",
	"response": []
}
```

### `block(number: str) -> str`

Блокирует абонента. Аналогично `change_status(number, 2)`.

### `unblock(number: str) -> str`

Разблокирует абонента. Аналогично `change_status(number, 1)`.

### `get_details(msisdn: str) -> str`

Возвращает подробную информацию об абоненте (IMEI, UIN, статус и т.д.)

### `register_imei(number: str, uin: str) -> str`

Привязка IMEI к абоненту по ИИН/БИН (Успешно активировано):

```json
{
	"success": true,
	"subscriberId": 12345678,
	"msisdn": "7001234567",
	"response": true
}
```

ИЛИ (IMEI - связка уже существует):

```json
{
	"success": false,
	"subscriberId": 12345678,
	"msisdn": "7001234567",
	"response": "IMEI - Bundle already exists"
}
```

### `company_info() -> dict`

Информация о компании (название, BIN и т.д.)

### `admins() -> dict`

Список администраторов и пользователей компании.

### `profiles() -> dict`

Список лицевых счетов компании.

---

## Статусы абонентов

###

| Код   | Статус       |
| ----- | ------------ |
| 1     | Активен      |
| 2     | Заблокирован |
| n > 2 | Неизвестно   |

---

## Примеры ответов API

### Поиск абонента

```json
[
	{
		"subscriberId": 12345678,
		"employee": null,
		"icc": "89990000000000000000",
		"msisdn": "7001234567",
		"fee": 0,
		"activationDate": "2020-01-01T10:10:20",
		"status": 1,
		"tariffId": 123,
		"tariffName": "Tariff Name",
		"balance": 0,
		"nextWriteOff": null,
		"clientTypeId": 12,
		"account": "123456789",
		"balanceLevel": 0,
		"contractNumber": "01234567890  ",
		"quota": 123,
		"quotaUnused": 0,
		"resources": []
	}
]
```

### Ошибка авторизации

```json
ERROR:altel_api.api: Login failed: 401
{
  "error": "bad_credentials",
  "error_description": "Invalid phone number or password. Try again.",
  "message": "Invalid phone number or password. Try again."
}

```

---

## Лицензия

###

#### IMPORTANT DISCLAIMER! (ENGLISH):

⚠️ This project is an unofficial tool for educational or internal use. \
⚠️ Use at your own risk. The author is not affiliated with Altel.kz or its partners. \
⚠️ This code interacts with web services that may be protected by terms of service.

#

#### ВАЖНЫЙ ДИСКЛЕЙМЕР! (РУССКИЙ):

⚠️ Этот проект является неофициальным инструментом, предназначенным для образовательных или внутренних целей. \
⚠️ Используйте на свой страх и риск. Автор не имеет отношения к Altel.kz или его партнёрам. \
⚠️ Этот код взаимодействует с веб-сервисами, которые могут быть защищены условиями использования.

#

#### МАҢЫЗДЫ ЕСКЕРТУ! (ҚАЗАҚША):

⚠️ Бұл жоба — оқу немесе ішкі мақсаттарға арналған ресми емес құрал. \
⚠️ Пайдалану — сіздің тәуекеліңізде. Автор Altel.kz немесе оның серіктестерімен байланысы жоқ. \
⚠️ Бұл код пайдалану шарттарымен қорғалған веб-сервистермен әрекеттесуі мүмкін.

#

[![Software License](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat-square)](LICENSE.md)
