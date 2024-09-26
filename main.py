import random
import time
import requests
import asyncio
import aiohttp
import telebot
from datetime import datetime, timedelta

# Initialize bot with token
token = input('Enter your bot token: ')
bot = telebot.TeleBot(token)

# Dictionary to track last request time for each user
# Dictionary to track last request time for each user
user_last_request = {}
request_limit_time = 5  # time limit in seconds for requests

# Helper function to safely make a request
def safe_request(url):
    try:
        return requests.get(url)
    except requests.exceptions.RequestException:
        return None

# Rate limiting check
def is_request_allowed(user_id):
    now = datetime.now()
    last_request_time = user_last_request.get(user_id)

    if last_request_time is None or (now - last_request_time) > timedelta(seconds=request_limit_time):
        user_last_request[user_id] = now
        return True
    return False

# Check if website has captcha
def check_captcha(url):
    response = safe_request(url)
    if response is None:
        return False
    if ('https://www.google.com/recaptcha/api' in response.text or
        'captcha' in response.text or
        'verifyRecaptchaToken' in response.text or
        'grecaptcha' in response.text or
        'www.google.com/recaptcha' in response.text):
        return True
    return False

# Check for multiple payment systems in the website
def check_credit_card_payment(url):
    response = safe_request(url)
    if response is None:
        return 'Error accessing the website'
    
    gateways = []
    if 'stripe' in response.text:
        gateways.append('Stripe')
    if 'Cybersource' in response.text:
        gateways.append('Cybersource')
    if 'paypal' in response.text:
        gateways.append('Paypal')
    if 'authorize.net' in response.text:
        gateways.append('Authorize.net')
    if 'Bluepay' in response.text:
        gateways.append('Bluepay')
    if 'Magento' in response.text:
        gateways.append('Magento')
    if 'woo' in response.text:
        gateways.append('WooCommerce')
    if 'Shopify' in response.text:
        gateways.append('Shopify')
    if 'adyen' in response.text or 'Adyen' in response.text:
        gateways.append('Adyen')
    if 'braintree' in response.text:
        gateways.append('Braintree')
    if 'square' in response.text:
        gateways.append('Square')
    if 'payflow' in response.text:
        gateways.append('Payflow')
    
    return ', '.join(gateways) if gateways else 'No recognized payment gateway found'

# Check for cloud services in the website
def check_cloud_in_website(url):
    response = safe_request(url)
    if response is None:
        return False
    if 'cloudflare' in response.text.lower():
        return True
    return False

# Check for GraphQL
def check_graphql(url):
    response = safe_request(url)
    if response is None:
        return False
    if 'graphql' in response.text.lower() or 'query {' in response.text or 'mutation {' in response.text:
        return True
    
    # Optionally, try querying the /graphql endpoint directly
    graphql_url = url.rstrip('/') + '/graphql'
    graphql_response = safe_request(graphql_url)
    if graphql_response and graphql_response.status_code == 200:
        return True
    
    return False

# Check if the path /my-account/add-payment-method/ exists
def check_auth_path(url):
    auth_path = url.rstrip('/') + '/my-account/add-payment-method/'
    response = safe_request(auth_path)
    if response is not None and response.status_code == 200:
        return 'Auth'
    return 'None'

# Get the status code
def get_status_code(url):
    response = safe_request(url)
    if response is not None:
        return response.status_code
    return 'Error'

# Check for platform (simplified)
def check_platform(url):
    response = safe_request(url)
    if response is None:
        return 'None'
    if 'wordpress' in response.text.lower():
        return 'WordPress'
    if 'shopify' in response.text.lower():
        return 'Shopify'
    return 'None'

# Check for error logs (simplified)
def check_error_logs(url):
    response = safe_request(url)
    if response is None:
        return 'None'
    if 'error' in response.text.lower() or 'exception' in response.text.lower():
        return 'Error logs found'
    return 'None'

# Generate credit card numbers based on a BIN
def generate_credit_card_numbers(bin_number, amount):
    card_numbers = []
    for _ in range(amount):  # Generate 'amount' card numbers
        # Create a 16-digit card number using the BIN
        card_number = bin_number + ''.join([str(random.randint(0, 9)) for _ in range(10)])  
        expiration_date = f"{random.randint(1, 12):02}|{random.randint(2024, 2030)}"  # MM|YYYY
        cvv = f"{random.randint(100, 999)}"  # CVV
        card_numbers.append(f"{card_number}|{expiration_date}|{cvv}")
    return card_numbers

# Check single URL with /check command
@bot.message_handler(commands=['check'])
def check_url(message):
    if len(message.text.split()) < 2:
        bot.reply_to(message, 'Please provide a valid URL after the /check command.')
        return

    user_id = message.from_user.id
    if not is_request_allowed(user_id):
        bot.reply_to(message, 'Please wait a few seconds before making another request.')
        return

    url = message.text.split()[1]

    try:
        captcha = check_captcha(url)
    except:
        captcha = 'Error checking captcha'

    cloud = check_cloud_in_website(url)
    payment = check_credit_card_payment(url)
    graphql = check_graphql(url)
    auth_path = check_auth_path(url)
    platform = check_platform(url)
    error_logs = check_error_logs(url)
    status_code = get_status_code(url)

    loading_message = bot.reply_to(message, '<strong>[~]-Loading... 🥸</strong>', parse_mode="HTML")
    time.sleep(1)

    captcha_emoji = "😞" if captcha else "🔥"
    cloud_emoji = "😞" if cloud else "🔥"

    # Create formatted message with <code> tag for the URL
    response_message = (
        "🔍 Gateways Fetched Successfully ✅\n"
        "━━━━━━━━━━━━━━\n"
        f"🔹 URL: <code>{url}</code>\n"
        f"🔹 Payment Gateways: {payment}\n"
        f"🔹 Captcha: {captcha} {captcha_emoji}\n"
        f"🔹 Cloudflare: {cloud} {cloud_emoji}\n"
        f"🔹 GraphQL: {graphql}\n"
        f"🔹 Auth Path: {auth_path}\n"
        f"🔹 Platform: {platform}\n"
        f"🔹 Error Logs: {error_logs}\n"
        f"🔹 Status: {status_code}\n"
        "\nBot by: @ZodMadara"
    )

    bot.edit_message_text(response_message, message.chat.id, loading_message.message_id, parse_mode='HTML')


@bot.message_handler(content_types=['document'])
def handle_txt_file(message):
    file_info = bot.get_file(message.document.file_id)
    file_extension = file_info.file_path.split('.')[-1]

    if file_extension != 'txt':
        bot.reply_to(message, 'Please upload a .txt file containing URLs.')
        return

    file = bot.download_file(file_info.file_path)
    urls = file.decode('utf-8').splitlines()

    # Validate URL count (should be between 50 and 100)
    if len(urls) < 50 or len(urls) > 100:
        bot.reply_to(message, 'Please provide a .txt file with between 50 and 100 URLs.')
        return

    bot.reply_to(message, 'Processing your URLs... This may take some time.')

    results = []
    for url in urls:
        try:
            captcha = check_captcha(url)
        except:
            captcha = 'Error checking captcha'

        cloud = check_cloud_in_website(url)
        payment = check_credit_card_payment(url)
        graphql = check_graphql(url)
        auth_path = check_auth_path(url)
        platform = check_platform(url)
        error_logs = check_error_logs(url)
        status_code = get_status_code(url)

        captcha_emoji = "😞" if captcha else "🔥"
        cloud_emoji = "😞" if cloud else "🔥"

        # Create result message with <code> tag for the URL
        result_message = (
            "━━━━━━━━━━━━━━\n"
            f"🔹 URL: <code>{url}</code>\n"
            f"🔹 Payment Gateways: {payment}\n"
            f"🔹 Captcha: {captcha} {captcha_emoji}\n"
            f"🔹 Cloudflare: {cloud} {cloud_emoji}\n"
            f"🔹 GraphQL: {graphql}\n"
            f"🔹 Auth Path: {auth_path}\n"
            f"🔹 Platform: {platform}\n"
            f"🔹 Error Logs: {error_logs}\n"
            f"🔹 Status: {status_code}\n"
        )
        results.append(result_message)

    # Send all results back to the user with HTML parsing
    final_response = "\n".join(results)
    bot.reply_to(message, final_response, parse_mode='HTML')

# Command to check sk_live key
@bot.message_handler(commands=['sk'])
def check_sk_key(message):
    if len(message.text.split()) < 2:
        bot.reply_to(message, 'Please provide a valid sk_live key after the /sk command.')
        return

    user_id = message.from_user.id
    if not is_request_allowed(user_id):
        bot.reply_to(message, 'Please wait a few seconds before making another request.')
        return

    key = message.text.split()[1]
    balance_response = requests.get('https://api.stripe.com/v1/balance', auth=(key, ''))
    account_response = requests.get('https://api.stripe.com/v1/account', auth=(key, ''))

    if balance_response.status_code == 200 and account_response.status_code == 200:
        account_info = account_response.json()
        balance_info = balance_response.json()

        # Collect account information
        publishable_key = account_info.get('keys', {}).get('publishable', 'Not Available')
        account_id = account_info.get('id', 'Not Available')
        charges_enabled = account_info.get('charges_enabled', 'Not Available')
        live_mode = account_info.get('livemode', 'Not Available')
        country = account_info.get('country', 'Not Available')
        currency = balance_info.get('currency', 'Not Available')
        available_balance = balance_info.get('available', [{'amount': '0'}])[0]['amount']
        pending_balance = balance_info.get('pending', [{'amount': '0'}])[0]['amount']
        payments_enabled = account_info.get('payouts_enabled', 'Not Available')
        name = account_info.get('business_name', 'Not Available')
        phone = account_info.get('support_phone', 'Not Available')
        email = account_info.get('email', 'Not Available')
        url = account_info.get('url', 'Not Available')

        response = (
    f'''[ϟ] 𝗦𝗸 𝗞𝗘𝗬\n<code>{key}</code>\n\n'''
    f'''[ϟ] 𝗣𝗸 𝗞𝗘𝗬\n<code>{publishable_key}</code>\n'''
    "－－－－－－－－－－－－－－－\n"
    f'''[✮] 𝐀𝐜𝐜𝐨𝐮𝐧𝐭 𝐈𝐃 ⬇️ [✮]\n{account_id}\n'''
    "－－－－－－－－－－－－－－－\n"
    "[✮] 𝐊𝐞𝐲 𝐈𝐧𝐟𝐨 ⬇️ [✮]\n"
    f"[ϟ] 𝗖𝗵𝗮𝗿𝗴𝗲𝘀 𝗘𝗻𝗮𝗯𝗹𝗲𝗱 : {charges_enabled}\n"
    f"[ϟ] 𝗟𝗶𝘃𝗲 𝗠𝗼𝗱𝗲 : {live_mode}\n"
    f"[ϟ] 𝗣𝗮𝘆𝗺𝗲𝗻𝘁𝘀 : {payments_enabled}\n"
    f"[ϟ] 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 : {available_balance}\n"
    f"[ϟ] 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 : {available_balance}\n"
    f"[ϟ] 𝗣𝗲𝗻𝗱𝗶𝗻𝗴 𝗕𝗮𝗹𝗮𝗻𝗰𝗲 : {pending_balance}\n"
    f"[ϟ] 𝗖𝘂𝗿𝗿𝗲𝗻𝗰𝘆 : {currency}\n"
    f"[ϟ] 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 : {country}\n"
    "－－－－－－－－－－－－－－－\n"
    "[✮] 𝐀𝐜𝐜𝐨𝐮𝐧𝐭 𝐈𝐧𝐟𝐨 ⬇️ [✮]\n"
    f"[ϟ] 𝗡𝗮𝗺𝗲 : {name}\n"
    f"[ϟ] 𝗣𝗵𝗼𝗻𝗲 : {phone}\n"
    f"[ϟ] 𝗘𝗺𝗮𝗶𝗹 : {email}\n"
    f'''[ϟ] 𝗨𝗿𝗹 : <code>{url}</code>\n'''
)

        bot.reply_to(message, response, parse_mode='HTML')
    else:
        bot.reply_to(message, f'Invalid or expired API key❌.\nKey: <code>{key}</code>', parse_mode='HTML')

# Function to check if the user can make another request
# Mapping of country codes to flag emojis
country_flags = {
    "AD": "🇦🇩", "AE": "🇦🇪", "AF": "🇦🇫", "AG": "🇦🇬", "AI": "🇦🇮",
    "AL": "🇦🇱", "AM": "🇦🇲", "AO": "🇦🇴", "AR": "🇦🇷", "AS": "🇦🇸",
    "AT": "🇦🇹", "AU": "🇦🇺", "AW": "🇦🇼", "AX": "🇦🇽", "AZ": "🇦🇿",
    "BA": "🇧🇦", "BB": "🇧🇧", "BD": "🇧🇩", "BE": "🇧🇪", "BF": "🇧🇫",
    "BG": "🇧🇬", "BH": "🇧🇭", "BI": "🇧🇮", "BJ": "🇧🇯", "BL": "🇧🇱",
    "BM": "🇧🇲", "BN": "🇧🇳", "BO": "🇧🇴", "BQ": "🇧🇶", "BR": "🇧🇷",
    "BS": "🇧🇸", "BT": "🇧🇹", "BV": "🇧🇻", "BW": "🇧🇼", "BY": "🇧🇾",
    "BZ": "🇧🇿", "CA": "🇨🇦", "CC": "🇨🇨", "CD": "🇨🇩", "CF": "🇨🇫",
    "CG": "🇨🇬", "CH": "🇨🇭", "CI": "🇨🇮", "CK": "🇨🇰", "CL": "🇨🇱",
    "CM": "🇨🇲", "CN": "🇨🇳", "CO": "🇨🇴", "CR": "🇨🇷", "CU": "🇨🇺",
    "CV": "🇨🇻", "CW": "🇨🇼", "CX": "🇭🇨", "CY": "🇨🇾", "CZ": "🇨🇿",
    "DE": "🇩🇪", "DJ": "🇩🇯", "DK": "🇩🇰", "DM": "🇩🇲", "DO": "🇩🇴",
    "DZ": "🇩🇿", "EC": "🇪🇨", "EE": "🇪🇪", "EG": "🇪🇬", "EH": "🇪🇭",
    "ER": "🇪🇷", "ES": "🇪🇸", "ET": "🇪🇹", "FI": "🇫🇮", "FJ": "🇫🇯",
    "FM": "🇫🇲", "FO": "🇫🇴", "FR": "🇫🇷", "GA": "🇬🇦", "GB": "🇬🇧",
    "GD": "🇬🇩", "GE": "🇬🇪", "GF": "🇬🇫", "GG": "🇬🇬", "GH": "🇬🇭",
    "GI": "🇬🇮", "GL": "🇬🇱", "GM": "🇬🇲", "GN": "🇬🇳", "GP": "🇬🇵",
    "GQ": "🇬🇶", "GR": "🇬🇷", "GT": "🇬🇹", "GU": "🇬🇺", "GW": "🇬🇼",
    "GY": "🇬🇾", "HK": "🇭🇰", "HM": "🇭🇲", "HN": "🇭🇳", "HR": "🇭🇷",
    "HT": "🇭🇹", "HU": "🇭🇺", "ID": "🇮🇩", "IE": "🇮🇪", "IL": "🇮🇱",
    "IM": "🇮🇲", "IN": "🇮🇳", "IO": "🇮🇴", "IQ": "🇮🇶", "IR": "🇮🇷",
    "IS": "🇮🇸", "IT": "🇮🇹", "JE": "🇯🇪", "JM": "🇯🇲", "JO": "🇯🇴",
    "JP": "🇯🇵", "KE": "🇰🇪", "KG": "🇰🇬", "KH": "🇰🇭", "KI": "🇰🇮",
    "KM": "🇰🇲", "KN": "🇰🇳", "KP": "🇰🇵", "KR": "🇰🇷", "KW": "🇰🇼",
    "KY": "🇰🇾", "KZ": "🇰🇿", "LA": "🇱🇦", "LB": "🇱🇧", "LC": "🇱🇨",
    "LI": "🇱🇮", "LK": "🇱🇰", "LR": "🇱🇷", "LS": "🇱🇸", "LT": "🇱🇹",
    "LU": "🇱🇺", "LV": "🇱🇻", "LY": "🇱🇾", "MA": "🇲🇦", "MC": "🇲🇨",
    "MD": "🇲🇩", "ME": "🇲🇪", "MF": "🇲🇫", "MG": "🇲🇬", "MH": "🇲🇭",
    "MK": "🇲🇰", "ML": "🇲🇱", "MM": "🇲🇲", "MN": "🇲🇳", "MO": "🇲🇴",
    "MP": "🇲🇵", "MQ": "🇲🇶", "MR": "🇲🇷", "MS": "🇲🇸", "MT": "🇲🇹",
    "MU": "🇲🇺", "MV": "🇲🇻", "MW": "🇲🇼", "MX": "🇲🇽", "MY": "🇲🇾",
    "MZ": "🇲🇿", "NA": "🇳🇦", "NC": "🇳🇨", "NE": "🇳🇪", "NF": "🇳🇫",
    "NG": "🇳🇬", "NI": "🇳🇮", "NL": "🇳🇱", "NO": "🇳🇴", "NP": "🇳🇵",
    "NR": "🇳🇷", "NU": "🇳🇺", "NZ": "🇳🇿", "OM": "🇴🇲", "PA": "🇵🇦",
    "PE": "🇵🇪", "PF": "🇵🇫", "PG": "🇵🇬", "PH": "🇵🇭", "PK": "🇵🇰",
    "PL": "🇵🇱", "PM": "🇵🇲", "PN": "🇵🇳", "PR": "🇵🇷", "PT": "🇵🇹",
    "PW": "🇵🇼", "PY": "🇵🇾", "QA": "🇶🇦", "RE": "🇷🇪", "RO": "🇷🇴",
    "RS": "🇷🇸", "RU": "🇷🇺", "RW": "🇷🇼", "SA": "🇸🇦", "SB": "🇸🇧",
    "SC": "🇸🇨", "SD": "🇸🇩", "SE": "🇸🇪", "SG": "🇸🇬", "SH": "🇸🇭",
    "SI": "🇸🇮", "SJ": "🇸🇯", "SK": "🇸🇰", "SL": "🇸🇱", "SM": "🇸🇲",
    "SN": "🇸🇳", "SO": "🇸🇴", "SR": "🇸🇷", "SS": "🇸🇸", "ST": "🇸🇹",
    "SV": "🇸🇻", "SX": "🇸🇽", "SY": "🇸🇾", "SZ": "🇸🇿", "TC": "🇹🇨",
    "TD": "🇹🇩", "TF": "🇹🇫", "TG": "🇹🇬", "TH": "🇹🇭", "TJ": "🇹🇯", "TK": "🇹🇰",
    "TL": "🇹🇱", "TM": "🇹🇲", "TN": "🇹🇳", "TO": "🇹🇴", "TR": "🇹🇷",
    "TT": "🇹🇹", "TV": "🇹🇻", "TZ": "🇹🇿", "UA": "🇺🇦", "UG": "🇺🇬",
    "UM": "🇺🇲", "US": "🇺🇸", "UY": "🇺🇾", "UZ": "🇺🇿", "VA": "🇻🇦",
    "VC": "🇻🇨", "VE": "🇻🇪", "VG": "🇻🇬", "VI": "🇻🇮", "VN": "🇻🇳",
    "VU": "🇻🇺", "WF": "🇼🇫", "WS": "🇼🇸", "YE": "🇾🇪", "YT": "🇾🇹",
    "ZA": "🇿🇦", "ZM": "🇿🇲", "ZW": "🇿🇼"
}

def is_request_allowed(user_id):
    return True

def get_card_info(bin_number):
    response = requests.get(f'https://lookup.binlist.net/{bin_number}')
    if response.status_code == 200:
        return response.json()
    return None

def generate_credit_card_numbers(bin_number):
    card_numbers = []
    for _ in range(10):  # Generate 10 card numbers
        card_number = f"{bin_number}{''.join(random.choices('0123456789', k=16 - len(bin_number)))}"
        month = random.randint(1, 12)
        year = random.randint(24, 30)  # Valid until 2024-2030
        cvv = ''.join(random.choices('0123456789', k=3))
        card_numbers.append(f"{card_number}|{month:02}|20{year}|{cvv}")
    return card_numbers

@bot.message_handler(commands=['gen'])
def generate_cards(message):
    if len(message.text.split()) < 2:
        bot.reply_to(message, 'Please provide a BIN after the /gen command.')
        return

    user_id = message.from_user.id
    if not is_request_allowed(user_id):
        bot.reply_to(message, 'Please wait a few seconds before making another request.')
        return

    bin_number = message.text.split()[1]
    card_numbers = generate_credit_card_numbers(bin_number)
    bin_info = get_card_info(bin_number)

    card_info = (
        f'𝗕𝗜𝗡 ⇾ {bin_number}\n'
        f'𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ 10\n'
        f'<code>\n' + '\n'.join(card_numbers) + '\n</code>\n'
    )

    # Append BIN info if available
    if bin_info:
        scheme = bin_info.get("scheme", "Unknown").upper()
        card_type = bin_info.get("type", "Unknown").upper()
        brand = bin_info.get("brand", "Unknown").upper()
        issuer = bin_info.get("bank", {}).get("name", "Unknown").upper()
        country = bin_info.get("country", {}).get("name", "Unknown").upper()
        country_code = bin_info.get("country", {}).get("alpha2", "Unknown").upper()
        flag = country_flags.get(country_code, "")

        card_info += (
            "𝗜𝗻𝗳𝗼: \n"
            f'{scheme} - {card_type} - {brand}\n'
            f'𝐈𝐬𝐬𝐮𝐞𝐫: {issuer}\n'
            f'𝗖𝗼𝘂𝗻𝘁𝗿𝗬: {country} {flag}\n'
        )
    else:
        card_info += "𝗜𝗻𝗳𝗼: No additional BIN info available.\n"

    bot.reply_to(message, card_info, parse_mode='HTML')

# Welcome message and commands
@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_text = (
        "Welcome to the Bot! Here are the commands you can use:\n"
        "/check <URL> - Check details about the specified URL\n"
        "/sk <sk_live key> - Check the sk_live key information\n"
        "/gen <BIN> - Generate credit card numbers based on the BIN\n"
    )
    bot.reply_to(message, welcome_text)

# Start the bot
bot.polling(none_stop=True)