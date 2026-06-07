translations_messages = {
    "start_message": {
        "en": "Welcome to TeleCloud Bot!\nUse the buttons below to navigate.",
        "ru": "Добро пожаловать в TeleCloud Бот!\nИспользуйте кнопки ниже для навигации."
    },
    "help_message": {
        "en": "To upload a file, click the <b>Upload file</b> button.\nFor more assistance, contact @ImSkaiden.",
        "ru": "Чтобы загрузить файл, нажмите кнопку <b>Загрузить файл</b>.\nДля получения дополнительной помощи свяжитесь с @ImSkaiden."
    },
    "upload_prompt": {
        "en": "Please send the file you want to upload.\nUp to <b>2</b> GB.",
        "ru": "Пожалуйста, отправьте файл, который вы хотите загрузить.\nДо <b>2</b> ГБ."
    },
    "upload_success": {
        "en": "Your file has been uploaded successfully!\nFile ID: <code>{}</code>\nName: {}\nSize: {}\nShare link: {}",
        "ru": "Ваш файл успешно загружен!\nID файла: <code>{}</code>\nИмя: {}\nРазмер: {}\nСсылка для доступа: {}"
    },
    "upload_failure": {
        "en": "Failed to upload the file. Please try again later and check your token.",
        "ru": "Не удалось загрузить файл. Пожалуйста, попробуйте позже и проверьте свой токен."
    },
    "upload_quota": {
        "en": "Upload failed: quota exceeded or file too large.",
        "ru": "Не удалось загрузить: превышена квота или файл слишком большой."
    },
    "upload_tg_fail": {
        "en": "Telegram temporarily failed to process the file. Please try again.",
        "ru": "Telegram временно не смог обработать файл. Попробуйте ещё раз."
    },
    "upload_no_token": {
        "en": "You need to set your API token before uploading files.\nCreate one at https://cloud.onlysq.ru/v2/ui/settings and send it via /settoken.",
        "ru": "Вам нужно установить API-токен перед загрузкой файлов.\nСоздайте его на https://cloud.onlysq.ru/v2/ui/settings и отправьте через /settoken."
    },
    "files": {
        "en": "Your files:",
        "ru": "Ваши файлы:"
    },
    "no_files": {
        "en": "You have no files uploaded.",
        "ru": "У вас нет загруженных файлов."
    },
    "file_list_failure": {
        "en": "Failed to retrieve files.",
        "ru": "Не удалось получить файлы."
    },
    "geting_files":{
        "en": "Retrieving your files...",
        "ru": "Получение ваших файлов..."
    },
    "token_set_success": {
        "en": "Your token has been set successfully.",
        "ru": "Ваш токен успешно установлен."
    },
    "settings_message": {
        "en": "Settings:\nAPI token: <span class='tg-spoiler'>{}</span>",
        "ru": "Настройки:\nAPI-токен: <span class='tg-spoiler'>{}</span>"
    },
    "quota_line": {
        "en": "Storage: {} / {} used",
        "ru": "Хранилище: {} / {} использовано"
    },
    "file_details": {
        "en": "File Name: {}\nSize: {}\nType: {}\nViews: {}\nUploaded: {}\nShare link: {}",
        "ru": "Имя файла: {}\nРазмер: {}\nТип: {}\nПросмотры: {}\nЗагружен: {}\nСсылка для доступа: {}"
    },
    "file_download_failure": {
        "en": "Failed to download the file.",
        "ru": "Не удалось скачать файл."
    },
    "set_token_prompt": {
        "en": "Send token.",
        "ru": "Отправьте токен."
    },
    "file_delete_success": {
        "en": "File deleted successfully.",
        "ru": "Файл успешно удален."
    },
    "file_delete_failure": {
        "en": "Failed to delete the file.",
        "ru": "Не удалось удалить файл."
    },
    "invalid_token": {
        "en": "The provided token is invalid. Please check and try again.",
        "ru": "Предоставленный токен недействителен. Пожалуйста, проверьте и попробуйте снова."
    },
    "token_generated_success": {
        "en": "Token was generated: <span class='tg-spoiler'>{}</span>",
        "ru": "Токен был сгенерирован: <span class='tg-spoiler'>{}</span>"
    },
    "token_generated_failure": {
        "en": "Failed to generate token. Please try again later.",
        "ru": "Не удалось сгенерировать токен. Пожалуйста, попробуйте позже."
    },
    "uploading_file": {
        "en": "Uploading file...",
        "ru": "Выгружаю файл..."
    },
    "generate_token_info": {
        "en": "API tokens are created in the web UI.\n\n1. Open https://cloud.onlysq.ru/v2/ui/settings\n2. Create a new token (scopes: read, write, share)\n3. Copy the <code>tck_...</code> token and send it here via /settoken",
        "ru": "API-токены создаются в веб-интерфейсе.\n\n1. Откройте https://cloud.onlysq.ru/v2/ui/settings\n2. Создайте новый токен (scopes: read, write, share)\n3. Скопируйте токен <code>tck_...</code> и отправьте сюда через /settoken"
    }
    

}

translations_buttons = {
    "upload_button": {
        "en": "Upload file",
        "ru": "Загрузить файл"
    },
    "download_button": {
        "en": "Download file",
        "ru": "Скачать файл"
    },
    "help_button": {
        "en": "Help",
        "ru": "Помощь"
    },
    "my_files_button": {
        "en": "My Files",
        "ru": "Мои файлы"
    },
    "menu_button": {
        "en": "Menu",
        "ru": "Меню"
    },
    "set_token_button": {
        "en": "Set token",
        "ru": "Установить токен"
    },
    "settings_button": {
        "en": "Settings",
        "ru": "Настройки"
    },
    "delete_button": {
        "en": "Delete file",
        "ru": "Удалить файл"
    },
    "generate_token": {
        "en": "Generate token",
        "ru": "Сгенерировать токен"
    },
    "next_page_button": {
        "en": ">>",
        "ru": ">>"
    },
    "previous_page_button": {
        "en": "<<",
        "ru": "<<"
    },
    
}