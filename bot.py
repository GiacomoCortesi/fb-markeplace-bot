import os
import urllib.parse

from crawler import city_dict, crawl

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class MarketplaceBot:
    def __init__(self, api_token="", polling_interval=60, chat_id=""):
        self.selected = ""
        self.monitor_targets = {}
        if not api_token:
            api_token = os.getenv("TELEGRAM_API_TOKEN")
        self.api_token = api_token
        if not chat_id:
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.chat_id = chat_id
        self.polling_interval = polling_interval

        application = ApplicationBuilder().token(api_token).build()
        self.application = application
        self.job_queue = self.application.job_queue
        self.job_queue.run_repeating(self.poll_fb_api_callback, interval=self.polling_interval, name="crawling-job")

        # add telegram command handlers
        add_handler = CommandHandler('add', self._add)
        self.application.add_handler(add_handler)
        delete_handler = CommandHandler('delete', self._delete)
        self.application.add_handler(delete_handler)
        select_handler = CommandHandler('select', self._select)
        self.application.add_handler(select_handler)
        interval_handler = CommandHandler('interval', self._interval)
        self.application.add_handler(interval_handler)

        show_handler = CommandHandler('show', self._show)
        self.application.add_handler(show_handler)
        selected_handler = CommandHandler('selected', self._selected)
        self.application.add_handler(selected_handler)

        keywords_handler = CommandHandler('keywords', self._keywords)
        self.application.add_handler(keywords_handler)
        price_handler = CommandHandler('price', self._price)
        self.application.add_handler(price_handler)
        location_handler = CommandHandler('location', self._location)
        self.application.add_handler(location_handler)
        radius_handler = CommandHandler('radius', self._radius)
        self.application.add_handler(radius_handler)

    def run(self):
        self.application.run_polling()

    @staticmethod
    def valid_target(monitor_target):
        valid = True
        if not monitor_target.get("keywords"):
            valid = False
        if not monitor_target.get("location_id"):
            valid = False
        return valid

    @staticmethod
    def build_url(monitor_target):
        base_url = f'https://www.facebook.com/marketplace/{monitor_target.get("location_id")}/search?'
        query = f"query={urllib.parse.quote_plus(monitor_target.get('keywords'))}"
        url = f"{base_url}{query}"

        if monitor_target.get('min_price'): url += f"&minPrice={monitor_target.get('min_price')}"
        if monitor_target.get('max_price'): url += f"&maxPrice={monitor_target.get('max_price')}"
        if monitor_target.get('radius'): url += f"&radius={monitor_target.get('radius')}"
        return url

    async def poll_fb_api_callback(self, context: CallbackContext):
        for key in self.monitor_targets:
            if not self.valid_target(self.monitor_targets[key]):
                continue
            url = self.build_url(self.monitor_targets[key])
            title_regex = '|'.join(self.monitor_targets[key]["keywords"].split(' '))
            crawl_result = crawl(url, title_regex=title_regex)
            if not crawl_result["ok"]:
                continue
            for product in crawl_result["products"]:
                text = f"Found an hot deal for {key}\n"
                text += f"name: {product['name']}\nprice: {product['price']}\nlocation: {product['location']}\nlink: https://wwww.facebook.com/{product['link']}\n"
                await context.bot.send_message(chat_id=self.chat_id, text=text)

    def add_monitor(self, monitor_name: str):
        if not self.monitor_targets.get(monitor_name):
            self.monitor_targets[monitor_name] = {}

    def set_keywords(self, monitor_name: str, keywords: str):
        self.monitor_targets[monitor_name]["keywords"] = keywords

    def set_location(self, monitor_name: str, postal_code: str, country: str):
        fb_id = city_dict.get((postal_code, country))
        self.monitor_targets[monitor_name]["location_id"] = fb_id
        self.monitor_targets[monitor_name]["postal_code"] = postal_code
        self.monitor_targets[monitor_name]["country"] = country

    def set_price_range(self, monitor_name: str, min_price: str, max_price: str):
        self.monitor_targets[monitor_name]['min_price'] = min_price
        self.monitor_targets[monitor_name]['max_price'] = max_price

    def set_radius(self, monitor_name: str, radius: int):
        self.monitor_targets[monitor_name]['radius'] = radius

    async def _interval(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 1:
            return
        self.polling_interval = int(context.args[0])
        [job.schedule_removal() for job in self.job_queue.get_jobs_by_name("crawling-job")]
        self.job_queue.run_repeating(self.poll_fb_api_callback, interval=self.polling_interval, name="crawling-job")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"configured facebook crawling interval to: {context.args[0]} seconds")

    async def _keywords(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keywords = ' '.join(context.args)
        self.set_keywords(self.selected, keywords)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"configured search keywords to: {keywords}")

    async def _location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 2:
            return
        postal_code = context.args[0]
        country = context.args[1]
        self.set_location(self.selected, postal_code, country)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"configured location to: {postal_code} {country}")

    async def _price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 2:
            return
        min_price = context.args[0]
        max_price = context.args[1]
        self.set_price_range(self.selected, min_price, max_price)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"configured price range to: {min_price} {max_price}")

    async def _radius(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 1:
            return
        self.set_radius(self.selected, context.args[0])
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"configured search radius to {context.args[0]} kilometers")

    async def _selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"currently selected target: {self.selected}")

    async def _select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 1:
            return
        if self.monitor_targets.get(context.args[0]):
            self.selected = context.args[0]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Selected target: {self.selected}")

    async def _show(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = "Currently configured monitoring targets"
        for key, value in self.monitor_targets.items():
            text += f"\ntarget: {key}"
            if value.get("keywords"): text += f'\nkeywords: {value["keywords"]}'
            if value.get("postal_code") and value.get(
                "country"): text += f'\nlocation: {value["postal_code"]} {value["country"]}'
            if value.get("min_price") and value.get(
                "max_price"): text += f'\nprice range: {value["min_price"]} {value["max_price"]}'
            if value.get("radius"): text += f'\nradius: {value["radius"]}'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    async def _add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        monitor_name = ' '.join(context.args)
        self.add_monitor(monitor_name)
        self.selected = monitor_name
        text = f"""Added and selected monitoring target: {monitor_name}
        You can now configure:
         - facebook search keywords with /keywords your product search keywords
         - location with /location postal_code country
         - price range with /price min max - optional
         - radius to expand the research to with /radius km-radius - optional
        """
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    async def _delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        monitor_name = ' '.join(context.args)
        del self.monitor_targets[monitor_name]
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Deleted monitoring target {monitor_name}")
