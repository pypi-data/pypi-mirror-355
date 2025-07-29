"""
:authors: @litemat
:license: The MIT License (MIT), see LICENSE file
:copyright: (c) 2025 @litemat
"""

import cloudscraper
import logging
import json

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Статичные ссылки энд-поинтов
static = {
    "login": "https://altel.kz/b2b/main/api/auth/login",
    "subscribers": "https://altel.kz/b2b/main/api/main/subscriber",
    "details": "https://altel.kz/b2b/main/api/main/details/{}",
    "block": "https://altel.kz/b2b/main/api/main/block",
    "unblock": "https://altel.kz/b2b/main/api/main/unblock",
    "register_imei": "https://altel.kz/b2b/main/api/main/v2/register-device",
    "company_info": "https://altel.kz/b2b/main/api/main/v2/company-info",
    "admins": "https://altel.kz/b2b/main/api/main/admins",
    "accounts": "https://altel.kz/b2b/main/api/main/accounts"
}


class AltelB2B:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.scraper = cloudscraper.create_scraper()
        self.authenticated = False

    def login(self) -> str:
        """
        Вход в систему, получение токенов.

        :return: JSON-строка
        """
        resp = self.scraper.post(static["login"], json={"username": self.username, "password": self.password})
        token = self.scraper.cookies.get("access_token")
        if token:
            self.scraper.headers.update({
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "xservicename": "subscribers",
                "User-Agent": "Mozilla/5.0"
            })
            self.authenticated = True
        else:
            logger.error("Login failed: %s %s", resp.status_code, resp.text)
        return json.dumps({"authenticated": self.authenticated})

    def all_subscribers(self, limit: int = 0) -> str:
        """
        Список всех абонентов, с лимитом.
        Если limit = 0, вывод всех (не рекомендуется).

        :param limit:
        :return: JSON-строка
        """
        if not self.authenticated:
            return json.dumps({"error": "Not authenticated"})

        all_accounts = []
        page = 1
        per_page = 40

        while True:
            params = {"page": page, "limit": per_page, "status": "0,1,2,3,4,5"}
            try:
                resp = self.scraper.get(static["subscribers"], params=params, timeout=10)
                data = resp.json()
                accounts = data.get("accounts", [])
            except Exception as e:
                return json.dumps({"error": str(e)})

            if not accounts:
                break

            all_accounts.extend(accounts)
            if limit and len(all_accounts) >= limit:
                return json.dumps(all_accounts[:limit], ensure_ascii=False)

            page += 1

        return json.dumps(all_accounts, ensure_ascii=False)

    def search_subscriber(self, number: str) -> str:
        """
        Поиск абонента по номеру.

        :param number:
        :return: JSON-строка
        """
        if not self.authenticated:
            return json.dumps({"error": "Not authenticated"})
        try:
            resp = self.scraper.get(static["subscribers"], params={
                "page": 1,
                "limit": 40,
                "status": "0,1,2,3,4,5",
                "search": number
            }, timeout=10)
            return json.dumps(resp.json().get("accounts", []), ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def change_status(self, number: str, status_code: int) -> str:
        """
        Метод для изменения статуса абонента.
        2 - заблокирован, 1 - активен.
        (не рекомендуется к использованию напрямую).

        :param number:
        :param status_code:
        :return: JSON-строка
        """
        if not self.authenticated:
            return json.dumps({"error": "Not authenticated"})
        subs = json.loads(self.search_subscriber(number))
        if not subs:
            return json.dumps({"success": False, "message": f"Абонент {number} не найден"})

        sub = subs[0]
        sub_id = sub.get("subscriberId")
        payload = [{"subscriberId": sub_id, "status": status_code}]
        url = static["block"] if status_code == 2 else static["unblock"]

        try:
            resp = self.scraper.post(url, json=payload, timeout=10)
            data = resp.json()
        except Exception as e:
            data = {"raw": str(e)}

        return json.dumps({
            "success": resp.status_code == 200,
            "subscriberId": sub_id,
            "msisdn": sub.get("msisdn"),
            "response": data
        }, ensure_ascii=False)

    def block(self, number: str) -> str:
        """
        Блокирование абонента по номеру.

        :param number:
        :return: JSON-строка
        """
        if not self.authenticated:
            return json.dumps({"error": "Not authenticated"})
        return self.change_status(number, 2)

    def unblock(self, number: str) -> str:
        """
        Разблокирование абонента по номеру.

        :param number:
        :return: JSON-строка
        """
        if not self.authenticated:
            return json.dumps({"error": "Not authenticated"})
        return self.change_status(number, 1)

    def get_details(self, msisdn: str) -> str:
        """
        Метод для получения детального отчета по абоненту.
        (не рекомендуется к использованию напрямую).

        :param msisdn:
        :return: JSON-строка
        """
        if not self.authenticated:
            raise Exception("Not authenticated")

        url = static["details"].format(msisdn)
        try:
            resp = self.scraper.get(url, timeout=10)
            return json.dumps(resp.json(), ensure_ascii=False)
        except Exception as e:
            logger.error("Ошибка при получении деталей: %s", str(e))
            return json.dumps({
                "raw": str(e),
                "status_code": resp.status_code if 'resp' in locals() else None
            }, ensure_ascii=False)

    def register_imei(self, number: str, uin: str) -> str:
        """
        Регистрация IMEI абонента.
        По IMEI, ИИН(БИН).

        :param number:
        :param uin:
        :return: JSON-строка
        """
        if not self.authenticated:
            return json.dumps({"error": "Not authenticated"})
        sub = self.get_details(number)
        try:
            sub = json.loads(sub) if isinstance(sub, str) else sub
        except Exception as e:
            return json.dumps({"success": False, "message": "Ошибка при разборе данных абонента", "raw": str(e)},
                              ensure_ascii=False)

        if not sub or "data" not in sub:
            return json.dumps({"success": False, "message": f"Абонент {number} не найден или данные недоступны"},
                              ensure_ascii=False)

        info = sub["data"].get("subscriberInfo", {})
        payload = {"imei": info.get("imei"), "msisdn": number, "uin": uin}

        try:
            resp = self.scraper.post(static["register_imei"], json=payload, timeout=10)
            data = resp.json()
        except Exception as e:
            logger.error("Ошибка при регистрации IMEI: %s", str(e))
            data = {"raw": str(e)}
            return json.dumps({
                "success": False,
                "subscriberId": info.get("subscriberId"),
                "msisdn": number,
                "response": data
            }, ensure_ascii=False)

        return json.dumps({
            "success": resp.status_code == 200,
            "subscriberId": info.get("subscriberId"),
            "msisdn": number,
            "response": data if data is True or data == "true" else data["message"]
        }, ensure_ascii=False)

    def company_info(self) -> str:
        """
        Информация о компании.

        :return: JSON-строка
        """
        if not self.authenticated:
            return json.dumps({"error": "Not authenticated"})

        headers = {"xservicename": "profile"}
        try:
            resp = self.scraper.get(static["company_info"], headers=headers, timeout=10)
            data = resp.json()
        except Exception as e:
            data = {"raw": str(e)}

        return json.dumps({"success": resp.status_code == 200, "response": data}, ensure_ascii=False)

    def admins(self) -> str:
        """
        Список админов (пользователей компании).

        :return: JSON-строка
        """
        if not self.authenticated:
            return json.dumps({"error": "Not authenticated"})

        headers = {"xservicename": "users"}
        try:
            resp = self.scraper.get(static["admins"], headers=headers, timeout=10)
            data = resp.json()
        except Exception as e:
            data = {"raw": str(e)}

        return json.dumps({"success": resp.status_code == 200, "response": data}, ensure_ascii=False)

    def profiles(self) -> str:
        """
        Список лицевых счетов компании.

        :return: JSON-строка
        """
        if not self.authenticated:
            return json.dumps({"error": "Not authenticated"})

        headers = {"xservicename": "accounts"}
        try:
            resp = self.scraper.get(static["accounts"], headers=headers, timeout=10)
            data = resp.json()
        except Exception as e:
            return json.dumps({"success": False, "error": str(e), "response": None})

        if isinstance(data, dict):
            return json.dumps({
                "success": resp.status_code == 200 and data.get("data") is not None,
                "response": data.get("data", data)
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "success": False,
                "error": f"Неверный формат ответа от API - {type(data)}",
                "response": data
            }, ensure_ascii=False)
