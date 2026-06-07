from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from translations import translations_messages as tm
from translations import translations_buttons as tb
import keyboards as kbs
import aiohttp, os, aiofiles, logging, json, uuid
from datetime import datetime, timezone
from db import User

# OnlySq Cloud REST API v2
API_BASE = "https://cloud.onlysq.ru"
SHARE_UI = f"{API_BASE}/v2/ui/s"
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB

class UserStates(StatesGroup):
    AWAITING_FILE_UPLOAD = State()
    AWAITING_TOKEN_INPUT = State()

router = Router()


# region helpers
def _auth(user_token: str) -> dict:
    """Build the Authorization header for API v2 Bearer auth."""
    return {"Authorization": f"Bearer {user_token}"}


def _human_size(num: int) -> str:
    try:
        num = float(num)
    except (TypeError, ValueError):
        return "?"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num) < 1024.0:
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.2f} {unit}"
        num /= 1024.0
    return f"{num:.2f} PB"


def _fmt_date(value: str) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return value


async def check_token(user_token: str) -> bool:
    """Validate a Bearer token via GET /v2/quota.

    /v2/me (alias /auth/me) does NOT accept the Bearer token (it is for the
    SAuth cookie session), so we hit a real Bearer-protected endpoint instead.
    """
    if not user_token:
        return False
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE}/v2/quota"
        async with session.get(url, headers=_auth(user_token)) as response:
            logging.info(f"Token check status: {response.status}")
            if response.status != 200:
                return False
            try:
                data = await response.json()
            except aiohttp.ContentTypeError:
                return False
            return bool(data.get("ok"))


async def list_files(user_token: str):
    """Return the list of files in the user's root, or None on failure."""
    url = f"{API_BASE}/v2/files"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params={"root": 1}, headers=_auth(user_token)) as response:
            logging.info(f"List files status: {response.status}")
            if response.status != 200:
                return None
            data = await response.json()
            if not data.get("ok"):
                return None
            return data.get("files", [])


async def upload_file(file_path: str, user_token: str):
    """POST /v2/files/upload — returns the parsed JSON or None.

    Note: aiohttp's FormData needs a synchronous file object, so we read the
    bytes with aiofiles first and hand the buffer to the multipart field.
    """
    url = f"{API_BASE}/v2/files/upload"
    async with aiofiles.open(file_path, 'rb') as f:
        content = await f.read()
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field(
            'file',
            content,
            filename=os.path.basename(file_path),
            content_type='application/octet-stream'
        )
        async with session.post(url, data=data, headers=_auth(user_token)) as response:
            body = await response.text()
            logging.info(f"Upload status: {response.status}; body: {body}")
            if response.status == 200:
                try:
                    return json.loads(body)
                except (ValueError, TypeError):
                    return None
            return None


async def get_info_file(file_uid: str, user_token: str):
    """GET /v2/files/<uid> — single file metadata."""
    url = f"{API_BASE}/v2/files/{file_uid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_auth(user_token)) as response:
            logging.info(f"File info status for {file_uid}: {response.status}")
            if response.status != 200:
                return None
            data = await response.json()
            if not data.get("ok"):
                return None
            # API may return {ok, file:{...}} or the file object directly
            return data.get("file", data)


async def create_share_link(file_uid: str, user_token: str):
    """POST /v2/files/<uid>/share (role viewer) — returns the public share URL or None."""
    url = f"{API_BASE}/v2/files/{file_uid}/share"
    payload = {"role": "viewer"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=_auth(user_token)) as response:
            logging.info(f"Share create status for {file_uid}: {response.status}")
            if response.status not in (200, 201):
                return None
            data = await response.json()
            if not data.get("ok"):
                return None
            token = (data.get("share") or {}).get("token")
            return f"{SHARE_UI}/{token}" if token else None


async def _get_user(telegram_id: int):
    """Fetch the user row, creating it if missing. Never raises DoesNotExist."""
    user = await User.filter(telegram_id=telegram_id).first()
    if user is None:
        user = await User.create(
            telegram_id=telegram_id,
            created_at=datetime.now(timezone.utc),
            user_token=None,
        )
    return user



# region help
@router.message(Command("help"))
async def send_help(message: Message, state: FSMContext):
    language = message.from_user.language_code
    await state.clear()
    await message.answer(tm["help_message"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))


# region upload
@router.callback_query(F.data == "upload")
async def callback_upload(callback_query, state: FSMContext):
    language = callback_query.from_user.language_code

    user = await User.get(telegram_id=callback_query.from_user.id)
    if user.user_token is None:
        await callback_query.message.edit_text(tm["upload_no_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        return

    await callback_query.message.edit_text(tm["upload_prompt"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    await state.set_state(UserStates.AWAITING_FILE_UPLOAD)
    await callback_query.answer()

@router.message(Command("upload"))
async def prompt_upload(message: Message, state: FSMContext):
    language = message.from_user.language_code
    await state.clear()

    user = await _get_user(message.from_user.id)

    if user.user_token is None:
        await message.answer(tm["upload_no_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        return

    await message.answer(tm["upload_prompt"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    await state.set_state(UserStates.AWAITING_FILE_UPLOAD)

# region my files
@router.callback_query(F.data == "myfiles")
async def callback_myfiles(callback_query: CallbackQuery):
    language = callback_query.from_user.language_code
    await callback_query.message.edit_text(tm["geting_files"].get(language, "en"))
    user = await _get_user(callback_query.from_user.id)
    if user.user_token is None:
        await callback_query.message.edit_text(tm["upload_no_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        return
    files = await list_files(user.user_token)
    if files is None:
        await callback_query.message.edit_text(tm["file_list_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    elif not files:
        await callback_query.message.edit_text(tm["no_files"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    else:
        markup = kbs.get_files_keyboard(files, 1, language)
        await callback_query.message.edit_text(tm["files"].get(language, "en"), reply_markup=markup)
    await callback_query.answer()

@router.message(Command("myfiles"))
async def list_user_files(message: Message, state: FSMContext):
    language = message.from_user.language_code
    await state.clear()
    user = await _get_user(message.from_user.id)
    if user.user_token is None:
        await message.answer(tm["upload_no_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        return
    files = await list_files(user.user_token)
    if files is None:
        await message.answer(tm["file_list_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    elif not files:
        await message.answer(tm["no_files"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    else:
        markup = kbs.get_files_keyboard(files, 1, language)
        await message.answer(tm["files"].get(language, "en"), reply_markup=markup)

@router.callback_query(F.data.startswith("page_"))
async def callback_pagination_handler(callback_query: CallbackQuery):
    next_page = int(callback_query.data.split("_")[1])
    language = callback_query.from_user.language_code

    user = await _get_user(callback_query.from_user.id)
    if user.user_token is None:
        await callback_query.answer(tm["invalid_token"].get(language, 'en'), show_alert=True)
        return

    files = await list_files(user.user_token)
    if files is None:
        await callback_query.answer(tm["file_list_failure"].get(language, "en"), show_alert=True)
    else:
        markup = kbs.get_files_keyboard(files, next_page, language)
        await callback_query.message.edit_reply_markup(reply_markup=markup)

    await callback_query.answer()

# region menu
@router.callback_query(F.data == "menu")
async def callback_menu(callback_query: CallbackQuery, state: FSMContext):
    language = callback_query.from_user.language_code
    markup = kbs.get_welcome_keyboard(language)
    await callback_query.message.edit_text(tm["start_message"].get(language, "en"), reply_markup=markup)
    await callback_query.answer()
    await state.clear()

# region settings
@router.callback_query(F.data == "settings")
async def callback_settings(callback_query: CallbackQuery):
    language = callback_query.from_user.language_code
    markup = kbs.get_settings_keyboard(language)
    user = await _get_user(callback_query.from_user.id)
    user_token = user.user_token if user.user_token else "Not set"
    await callback_query.message.edit_text(tm["settings_message"].get(language, "en").format(user_token), reply_markup=markup)
    await callback_query.answer()

# region set token
@router.callback_query(F.data == "settoken")
async def callback_settoken(callback_query: CallbackQuery, state: FSMContext):
    language = callback_query.from_user.language_code
    await state.clear()
    await callback_query.message.edit_text(tm["set_token_prompt"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    await state.set_state(UserStates.AWAITING_TOKEN_INPUT)
    await callback_query.answer()

@router.message(Command("settoken"))
async def set_user_token(message: Message):
    language = message.from_user.language_code
    try:
        token = message.text.split(" ")[1]
    except IndexError:
        await message.answer("Please provide a token. Usage: /settoken YOUR_TOKEN", reply_markup=kbs.get_menu_keyboard(language))
        return
    if not await check_token(token):
        await message.answer(tm["invalid_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        return
    if not await User.filter(telegram_id=message.from_user.id).exists():
        await User.create(telegram_id=message.from_user.id, created_at=datetime.now(timezone.utc), user_token=token)
    else:
        user = await User.get(telegram_id=message.from_user.id)
        user.user_token = token
        await user.save()

    await message.answer(tm["token_set_success"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))

# region awaiting file upload
@router.message(UserStates.AWAITING_FILE_UPLOAD)
async def handle_file_upload(message: Message, state: FSMContext, bot: Bot):
    language = message.from_user.language_code
    await message.answer(tm['uploading_file'].get(language, 'en'))

    user = await _get_user(message.from_user.id)
    if user.user_token is None:
        await message.answer(tm["upload_no_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        await state.clear()
        return

    os.makedirs("downloads", exist_ok=True)
    # Unique temp prefix so concurrent/retried uploads never clobber each other.
    prefix = f"downloads/{message.from_user.id}_{uuid.uuid4().hex[:8]}_"
    file_path = None

    def _too_big(size) -> bool:
        return (size or 0) > MAX_FILE_SIZE

    try:
        # Handle document
        if message.document:
            if _too_big(message.document.file_size):
                await message.answer("File size exceeds 2 GB limit.", reply_markup=kbs.get_menu_keyboard(language))
                await state.clear()
                return
            file = await bot.get_file(message.document.file_id)
            safe_name = os.path.basename(message.document.file_name or "file")
            file_path = prefix + safe_name
            await bot.download_file(file.file_path, destination=file_path, timeout=600)

        # Handle photo
        elif message.photo:
            if _too_big(message.photo[-1].file_size):
                await message.answer("File size exceeds 2 GB limit.", reply_markup=kbs.get_menu_keyboard(language))
                await state.clear()
                return
            file = await bot.get_file(message.photo[-1].file_id)
            file_path = prefix + "photo.jpg"
            await bot.download_file(file.file_path, destination=file_path, timeout=600)

        # Handle video
        elif message.video:
            if _too_big(message.video.file_size):
                await message.answer("File size exceeds 2 GB limit.", reply_markup=kbs.get_menu_keyboard(language))
                await state.clear()
                return
            file = await bot.get_file(message.video.file_id)
            file_path = prefix + "video.mp4"
            await bot.download_file(file.file_path, destination=file_path, timeout=600)

        # Handle audio
        elif message.audio:
            if _too_big(message.audio.file_size):
                await message.answer("File size exceeds 2 GB limit.", reply_markup=kbs.get_menu_keyboard(language))
                await state.clear()
                return
            file = await bot.get_file(message.audio.file_id)
            file_path = prefix + "audio.mp3"
            await bot.download_file(file.file_path, destination=file_path, timeout=600)

        # Handle text
        elif message.text:
            file_path = prefix + "text.txt"
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(message.text)

        else:
            await message.answer(tm["upload_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
            await state.clear()
            return

        # Upload file to server
        response = await upload_file(file_path, user.user_token)
        if response and response.get("ok"):
            file_obj = response.get("file", {})
            uid = file_obj.get("uid", "?")
            name = file_obj.get("name", os.path.basename(file_path))
            size = _human_size(file_obj.get("size", 0))
            share_link = await create_share_link(uid, user.user_token) or "-"
            logging.info(f"File uploaded for user {message.from_user.id}: {uid}")
            await message.answer(
                tm["upload_success"].get(language, "en").format(uid, name, size, share_link),
                reply_markup=kbs.get_menu_keyboard(language)
            )
        else:
            await message.answer(tm["upload_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))

    except Exception as e:
        logging.error(f"Upload error for user {message.from_user.id}: {e}")
        await message.answer(tm["upload_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                logging.warning(f"Failed to remove temp file {file_path}: {e}")
        await state.clear()

# region awaiting token input
@router.message(UserStates.AWAITING_TOKEN_INPUT)
async def handle_token_input(message: Message, state: FSMContext):
    language = message.from_user.language_code
    token = message.text.strip()
    if not await check_token(token):
        await message.answer(tm["invalid_token"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
        return
    if not await User.filter(telegram_id=message.from_user.id).exists():
        await User.create(telegram_id=message.from_user.id, created_at=datetime.now(timezone.utc), user_token=token)
    else:
        user = await User.get(telegram_id=message.from_user.id)
        user.user_token = token
        await user.save()

    await message.answer(tm["token_set_success"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    await state.clear()

# region file
@router.callback_query(F.data.startswith("file_"))
async def callback_file_details(callback_query: CallbackQuery):
    language = callback_query.from_user.language_code
    file_uid = callback_query.data.split("_", 1)[1]
    user = await _get_user(callback_query.from_user.id)
    if user.user_token is None:
        await callback_query.answer(tm["invalid_token"].get(language, "en"), show_alert=True)
        return
    file_info = await get_info_file(file_uid, user.user_token)
    if not file_info:
        await callback_query.answer(tm["file_list_failure"].get(language, "en"), show_alert=True)
        return
    share_link = await create_share_link(file_uid, user.user_token) or "-"
    await callback_query.message.edit_text(
        tm["file_details"].get(language, "en").format(
            file_info.get("name", "?"),
            _human_size(file_info.get("size", 0)),
            file_info.get("mime", "-"),
            file_info.get("views", 0),
            _fmt_date(file_info.get("created_at", "")),
            share_link,
        ),
        reply_markup=kbs.get_file_action_keyboard(file_uid, language)
    )

@router.callback_query(F.data.startswith("download_"))
async def callback_file_download(callback_query: CallbackQuery):
    language = callback_query.from_user.language_code
    file_uid = callback_query.data.split("_", 1)[1]
    user = await _get_user(callback_query.from_user.id)
    if user.user_token is None:
        await callback_query.answer(tm["invalid_token"].get(language, "en"), show_alert=True)
        return
    file_info = await get_info_file(file_uid, user.user_token)
    if not file_info:
        await callback_query.answer(tm["file_download_failure"].get(language, "en"), show_alert=True)
        return

    download_url = f"{API_BASE}/v2/files/{file_uid}/stream"
    file_name = os.path.basename(file_info.get("name") or file_uid)

    async with aiohttp.ClientSession() as session:
        async with session.get(download_url, params={"mode": "dl"}, headers=_auth(user.user_token)) as response:
            if response.status != 200:
                await callback_query.answer(tm["file_download_failure"].get(language, "en"), show_alert=True)
                return

            os.makedirs("downloads", exist_ok=True)
            destination_path = os.path.join("downloads", file_name)

            try:
                async with aiofiles.open(destination_path, 'wb') as file:
                    async for chunk in response.content.iter_chunked(8192):
                        await file.write(chunk)
                async with aiofiles.open(destination_path, 'rb') as file:
                    file_content = await file.read()
                file_content = BufferedInputFile(file_content, filename=file_name)
                await callback_query.message.answer_document(document=file_content)
                os.remove(destination_path)
            except IOError as e:
                logging.error(f"Failed to write file {file_name}: {e}")
                await callback_query.message.answer(tm["file_download_failure"].get(language, "en"))
    await callback_query.answer()

@router.callback_query(F.data.startswith("delete_"))
async def callback_file_delete(callback_query: CallbackQuery):
    language = callback_query.from_user.language_code
    file_uid = callback_query.data.split("_", 1)[1]
    user = await _get_user(callback_query.from_user.id)
    if user.user_token is None:
        await callback_query.answer(tm["invalid_token"].get(language, "en"), show_alert=True)
        return
    url = f"{API_BASE}/v2/files/{file_uid}"
    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=_auth(user.user_token)) as response:
            logging.info(f"Delete file {file_uid} status for user {callback_query.from_user.id}: {response.status}")
            ok = False
            try:
                ok = response.status == 200 and (await response.json()).get("ok", False)
            except aiohttp.ContentTypeError:
                ok = response.status == 200
            if ok:
                await callback_query.message.edit_text(tm["file_delete_success"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
            else:
                await callback_query.message.edit_text(tm["file_delete_failure"].get(language, "en"), reply_markup=kbs.get_menu_keyboard(language))
    await callback_query.answer()

@router.callback_query(F.data == "generate_token")
async def callback_gentoken(callback_query: CallbackQuery):
    # API v2 tokens are created in the web UI; show instructions instead of auto-generating.
    language = callback_query.from_user.language_code
    await callback_query.message.edit_text(
        tm["generate_token_info"].get(language, "en"),
        reply_markup=kbs.get_menu_keyboard(language)
    )
    await callback_query.answer()
