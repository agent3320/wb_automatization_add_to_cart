"""
Библиотека для добавления одного товара в корзину Wildberries
"""

from playwright.sync_api import sync_playwright
import time
from typing import Dict, Optional
import os
from datetime import datetime

class WBCartBot:
    """
    Бот для добавления одного товара в корзину Wildberries
    """
    
    def __init__(self, debug: bool = False):
        """
        Args:
            debug: Режим отладки (печать в консоль)
        """
        self.debug = debug
        self.playwright = None
        self.browser = None
        self.context = None
        self.main_page = None
        self.is_connected = False
    
    def _log(self, message: str):
        """Внутреннее логирование"""
        if self.debug:
            print(f"🔹 {message}")
    
    def connect(self, port: int = 9222) -> bool:
        """
        Подключение к запущенному Edge
        
        Args:
            port: Порт удаленной отладки (по умолчанию 9222)
        
        Returns:
            bool: Успешно ли подключение
        """
        self._log(f"Подключение к Edge на порту {port}...")
        
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.connect_over_cdp(f"http://localhost:{port}")
            
            if not self.browser.contexts:
                self._log("❌ Нет открытых контекстов браузера")
                return False
            
            self.context = self.browser.contexts[0]
            
            # Поиск существующей вкладки с Wildberries
            for page in self.context.pages:
                if "wildberries" in page.url.lower():
                    self.main_page = page
                    self._log("✅ Найдена вкладка с Wildberries")
                    self.is_connected = True
                    return True
            
            # Создание новой вкладки
            self._log("📌 Создание новой вкладки...")
            self.main_page = self.context.new_page()
            self.main_page.goto("https://www.wildberries.ru/")
            time.sleep(2)
            self.is_connected = True
            return True
            
        except Exception as e:
            self._log(f"❌ Ошибка подключения: {e}")
            return False
    
    def _wait_for_button(self, page, timeout: int = 20):
        """
        Ожидание появления кнопки "Добавить в корзину"
        """
        self._log(f"⏳ Ожидание кнопки (до {timeout} сек)...")
        
        for i in range(timeout):
            # Поиск кнопки
            button = page.get_by_text("Добавить в корзину").first
            
            if button.count():
                self._log(f"✅ Кнопка найдена через {i} сек")
                return button
            
            # Прокрутка для активации JS
            if i % 3 == 0:
                page.evaluate("window.scrollBy(0, 300)")
            
            time.sleep(1)
        
        # Альтернативный поиск
        alt_button = page.get_by_text("В корзину").first
        if alt_button.count():
            self._log("✅ Найдена кнопка 'В корзину'")
            return alt_button
        
        self._log("❌ Кнопка не найдена")
        return None
    
    def add_to_cart(self, url: str) -> Dict:
        """
        Добавление одного товара в корзину
        
        Args:
            url: Полная ссылка на товар
        
        Returns:
            Dict: Результат операции
        """
        result = {
            'success': False,
            'url': url,
            'message': '',
            'timestamp': datetime.now().isoformat()
        }
        
        if not self.is_connected:
            result['message'] = '❌ Нет подключения к Edge. Запусти connect()'
            return result
        
        product_page = None
        try:
            self._log(f"\n🛒 Обработка товара...")
            
            # Открываем новую вкладку
            product_page = self.context.new_page()
            
            # Переходим на страницу
            product_page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Прокрутка для активации JS
            self._log("📜 Прокрутка страницы...")
            for _ in range(3):
                product_page.evaluate("window.scrollBy(0, 400)")
                time.sleep(0.5)
            
            # Ожидание кнопки
            add_button = self._wait_for_button(product_page)
            
            if not add_button:
                result['message'] = '❌ Кнопка не найдена'
                return result
            
            # Прокрутка к кнопке
            add_button.scroll_into_view_if_needed()
            time.sleep(1)
            
            # Клик
            try:
                add_button.click(force=True)
                self._log("✅ Клик выполнен")
            except:
                # Запасной вариант через JavaScript
                product_page.evaluate("""
                    document.querySelector('button:has-text("Добавить в корзину")')?.click()
                """)
                self._log("✅ JavaScript клик выполнен")
            
            time.sleep(2)
            
            result['success'] = True
            result['message'] = '✅ Товар добавлен в корзину'
            self._log("✅ Товар добавлен!")
            
        except Exception as e:
            result['message'] = f'❌ Ошибка: {str(e)}'
            self._log(f"❌ Ошибка: {e}")
        
        finally:
            if product_page:
                product_page.close()
        
        return result
    
    def disconnect(self):
        """Отключение от браузера"""
        if self.playwright:
            self.playwright.stop()
        self.is_connected = False
        self._log("👋 Отключено")
    

    def login(self, number: str):
        buton = self.main_page.get_by_text('Войти')
        if buton.count() > 0:
            print('--> login button detected')
            buton.click()
        else:
            print('ERROR login button undetected')
    
   
        


# ============================================
# ТЕСТОВЫЙ ЗАПУСК
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("🛒 БОТ ДЛЯ WILDBERRIES (ОДИН ТОВАР)")
    print("=" * 60)
    
    # Создаем бота
    bot = WBCartBot(debug=True)
    
    # Подключаемся
    if bot.connect():
        print("\n✅ Бот готов к работе!")
        bot.login('1234')
        while True:
            url = input("\n🔗 Введите URL товара (Enter = выход): ").strip()
            if not url:
                break
        
            result = bot.add_to_cart(url)
            print(f"\n📊 Результат: {result['message']}")
        
        bot.disconnect()
    else:
        print("\n❌ Не удалось подключиться. Убедись что:")
        print("1. Edge запущен с параметром --remote-debugging-port=9222")
        print("2. Edge не закрыт")


# Добавь это в самый конец файла wb_cart.py

import asyncio
from concurrent.futures import ThreadPoolExecutor

# Создаем пул потоков для синхронных вызовов
_executor = ThreadPoolExecutor(max_workers=1)

async def add_to_cart_async(bot, url):
    """Асинхронная обертка для синхронного метода"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(_executor, bot.add_to_cart, url)
    return result