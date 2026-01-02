import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from src.models.telegram_bot import TelegramBot
from src.models.language_detector import LanguageDetector


class TestTelegramBot:
    """Test cases for TelegramBot class"""

    def setup_method(self):
        """Set up test environment"""
        # Clear environment variables for testing
        self.original_env = {}
        for key in ['TELEGRAM_BOT_TOKEN']:
            if key in os.environ:
                self.original_env[key] = os.environ[key]
                del os.environ[key]

    def teardown_method(self):
        """Restore environment variables"""
        for key, value in self.original_env.items():
            os.environ[key] = value

    @patch('src.models.telegram_bot.DatabaseManager')
    @patch('src.models.telegram_bot.FreeTranslator')
    @patch('src.models.telegram_bot.VoiceTranscriber')
    def test_init_success(self, mock_voice, mock_translator, mock_db):
        """Test successful bot initialization"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'

        bot = TelegramBot()

        assert bot.token == 'test_token'
        assert bot.base_url == 'https://api.telegram.org/bottest_token'
        assert mock_db.called
        assert mock_translator.called
        assert mock_voice.called

    def test_init_missing_token(self):
        """Test initialization failure when token is missing"""
        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN environment variable is required"):
            TelegramBot()

    @patch('src.models.telegram_bot.requests.post')
    def test_answer_callback_query_success(self, mock_post):
        """Test successful callback query answer"""
        mock_post.return_value.status_code = 200

        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot.answer_callback_query('callback_123', 'Text')

        assert result == True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json']['callback_query_id'] == 'callback_123'
        assert call_args[1]['json']['text'] == 'Text'

    @patch('src.models.telegram_bot.requests.post')
    def test_answer_callback_query_failure(self, mock_post):
        """Test callback query answer failure"""
        mock_post.return_value.status_code = 400

        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot.answer_callback_query('callback_123')

        assert result == False

    @patch('src.models.telegram_bot.requests.post')
    def test_send_message_success(self, mock_post):
        """Test successful message sending"""
        mock_post.return_value.status_code = 200

        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot.send_message(123, 'Hello world', 'HTML')

        assert result == True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json']['chat_id'] == 123
        assert call_args[1]['json']['text'] == 'Hello world'
        assert call_args[1]['json']['parse_mode'] == 'HTML'

    @patch('src.models.telegram_bot.requests.post')
    def test_send_message_failure(self, mock_post):
        """Test message sending failure"""
        mock_post.return_value.status_code = 400

        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot.send_message(123, 'Hello world')

        assert result == False

    @patch('src.models.telegram_bot.requests.post')
    def test_delete_message_success(self, mock_post):
        """Test successful message deletion"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'ok': True}

        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot.delete_message(123, 456)

        assert result == True

    @patch('src.models.telegram_bot.requests.post')
    def test_delete_message_failure(self, mock_post):
        """Test message deletion failure"""
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {'ok': False}

        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot.delete_message(123, 456)

        assert result == False

    @patch('src.models.telegram_bot.requests.post')
    def test_send_keyboard_success(self, mock_post):
        """Test successful keyboard sending"""
        mock_post.return_value.status_code = 200

        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        keyboard = [['Button 1', 'Button 2']]
        result = bot.send_keyboard(123, 'Choose option:', keyboard)

        assert result == True
        mock_post.assert_called_once()

    @patch('src.models.telegram_bot.requests.post')
    def test_send_keyboard_failure(self, mock_post):
        """Test keyboard sending failure"""
        mock_post.return_value.status_code = 400

        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        keyboard = [['Button 1']]
        result = bot.send_keyboard(123, 'Choose option:', keyboard)

        assert result == False

    def test_get_language_flag(self):
        """Test language flag retrieval"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        assert bot._get_language_flag('en') == '🇺🇸'
        assert bot._get_language_flag('th') == '🇹🇭'
        assert bot._get_language_flag('unknown') == '🌍'

    def test_get_language_code_from_button(self):
        """Test language code extraction from button text"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        # Test valid button text
        result = bot._get_language_code_from_button('🇹🇭 Thai')
        assert result == 'th'

        # Test invalid button text
        result = bot._get_language_code_from_button('Invalid')
        assert result is None

    def test_create_language_keyboard(self):
        """Test language keyboard creation"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        keyboard = bot._create_language_keyboard()

        assert isinstance(keyboard, list)
        assert len(keyboard) > 0
        # Check that each row has buttons
        for row in keyboard:
            assert isinstance(row, list)
            for button in row:
                assert isinstance(button, tuple)
                assert len(button) == 2

    def test_create_language_keyboard_with_exclude(self):
        """Test language keyboard creation with excluded language"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        keyboard = bot._create_language_keyboard('en')

        # Check that 'en' is not in the keyboard
        for row in keyboard:
            for button in row:
                assert button[1] != 'en'  # callback_data should not be 'en'

    @patch.object(TelegramBot, 'get_user_language_pair')
    @patch.object(TelegramBot, 'send_message')
    def test_get_user_language_pair_default(self, mock_send, mock_get_pair):
        """Test getting default language pair"""
        mock_get_pair.return_value = ('en', 'ru')

        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot.get_user_language_pair(123)

        assert result == ('en', 'ru')
        mock_get_pair.assert_called_once_with(123)

    @patch.object(TelegramBot, 'send_message')
    def test_set_user_language_pair_success(self, mock_send):
        """Test successful language pair setting"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot.set_user_language_pair(123, 'en', 'ru')

        assert result == True

    @patch.object(TelegramBot, 'send_message')
    def test_set_user_language_pair_invalid_lang(self, mock_send):
        """Test language pair setting with invalid language"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot.set_user_language_pair(123, 'invalid', 'en')

        assert result == False

    @patch.object(TelegramBot, 'send_message')
    def test_set_user_language_pair_same_lang(self, mock_send):
        """Test language pair setting with same languages"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot.set_user_language_pair(123, 'en', 'en')

        assert result == False

    def test_process_message_invalid_update(self):
        """Test processing invalid update"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        # Should not raise exception
        bot.process_message({})

    def test_process_message_with_edited_message(self):
        """Test processing edited message"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        update = {
            'edited_message': {
                'chat': {'id': 123},
                'from': {'id': 456, 'first_name': 'Test'},
                'message_id': 789,
                'text': 'Edited message'
            }
        }

        with patch.object(bot, '_handle_edited_message') as mock_handle:
            bot.process_message(update)
            mock_handle.assert_called_once()

    def test_process_message_with_callback_query(self):
        """Test processing callback query"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        update = {
            'callback_query': {
                'id': 'callback_123',
                'message': {'chat': {'id': 123}, 'message_id': 456},
                'data': 'test_data'
            }
        }

        with patch.object(bot, '_handle_callback_query') as mock_handle:
            bot.process_message(update)
            mock_handle.assert_called_once()

    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_unknown(self, mock_send):
        """Test handling unknown command"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        bot._handle_command(123, 456, '/unknown')

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert 'Unknown command' in call_args[0][1]

    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_start(self, mock_send):
        """Test handling /start command"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        bot._handle_command(123, 456, '/start')

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert 'Welcome' in call_args[0][1]

    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_help(self, mock_send):
        """Test handling /help command"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        bot._handle_command(123, 456, '/help')

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert 'Help' in call_args[0][1]

    @patch.object(TelegramBot, 'send_keyboard')
    @patch.object(TelegramBot, '_create_language_keyboard')
    def test_handle_command_setpair(self, mock_create_keyboard, mock_send_keyboard):
        """Test handling /setpair command"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        mock_create_keyboard.return_value = [['button1', 'button2']]

        bot._handle_command(123, 456, '/setpair')

        mock_send_keyboard.assert_called_once()

    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_languages(self, mock_send):
        """Test handling /languages command"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        bot._handle_command(123, 456, '/languages')

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert 'Supported Languages' in call_args[0][1]

    @patch.object(TelegramBot, 'get_user_language_pair')
    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_stats(self, mock_send, mock_get_pair):
        """Test handling /stats command"""
        mock_get_pair.return_value = ('en', 'ru')

        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        bot._handle_command(123, 456, '/stats')

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert 'Translation Stats' in call_args[0][1]

    @patch.object(TelegramBot, 'get_user_language_pair')
    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_chatmode_translation_to_chat(self, mock_send, mock_get_pair):
        """Test switching from translation to chat mode"""
        mock_get_pair.return_value = ('en', 'ru')

        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        bot._handle_command(123, 456, '/chatmode')

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert 'Chat Mode Enabled' in call_args[0][1]

    @patch.object(TelegramBot, 'get_user_language_pair')
    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_chatmode_chat_to_translation(self, mock_send, mock_get_pair):
        """Test switching from chat to translation mode"""
        mock_get_pair.return_value = ('en', 'ru')

        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        # First call to set chat mode
        bot._handle_command(123, 456, '/chatmode')
        # Second call to switch back to translation
        bot._handle_command(123, 456, '/chatmode')

        # Should have been called twice
        assert mock_send.call_count == 2
        # Second call should mention translation mode
        second_call_args = mock_send.call_args_list[1]
        assert 'Translation Mode Enabled' in second_call_args[0][1]

    def test_extract_language_code_direct(self):
        """Test extracting language code directly"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot._extract_language_code('en')
        assert result == 'en'

    def test_extract_language_code_from_button(self):
        """Test extracting language code from button text"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot._extract_language_code('🇹🇭 Thai')
        assert result == 'th'

    def test_extract_language_code_invalid(self):
        """Test extracting invalid language code"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        result = bot._extract_language_code('invalid')
        assert result is None

    def test_send_language_pair_confirmation(self):
        """Test sending language pair confirmation"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        with patch.object(bot, 'send_message') as mock_send:
            bot._send_language_pair_confirmation(123, 'en', 'ru')

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert 'Language pair set' in call_args[0][1]
            assert '🇺🇸' in call_args[0][1]  # English flag
            assert '🇷🇺' in call_args[0][1]  # Russian flag

    @patch.object(TelegramBot, 'send_message')
    def test_send_transcription_only_no_lang(self, mock_send):
        """Test sending transcription-only response without detected language"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        bot._send_transcription_only(123, 'TestUser', 'Hello world')

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert 'Voice Transcription' in call_args[0][1]
        assert 'Hello world' in call_args[0][1]

    @patch.object(TelegramBot, 'send_message')
    def test_send_transcription_only_with_lang(self, mock_send):
        """Test sending transcription-only response with detected language"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        bot._send_transcription_only(123, 'TestUser', 'Hello world', 'en')

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert 'Voice Transcription' in call_args[0][1]
        assert 'Hello world' in call_args[0][1]
        assert 'English' in call_args[0][1]  # English language name

    @patch.object(TelegramBot, 'send_message')
    def test_send_transcription_error(self, mock_send):
        """Test sending transcription error message"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        bot._send_transcription_error(123, 'TestUser')

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert 'Voice transcription failed' in call_args[0][1]

    @patch.object(TelegramBot, 'send_message')
    def test_send_translation_error(self, mock_send):
        """Test sending translation error message"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        bot._send_translation_error(123, 'TestUser', 'Hello world')

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert 'Voice translation failed' in call_args[0][1]

    def test_get_language_from_flag(self):
        """Test getting language code from flag emoji"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        assert bot._get_language_from_flag('🇹🇭') == 'th'
        assert bot._get_language_from_flag('🇺🇸') == 'en'
        assert bot._get_language_from_flag('invalid') is None

    @patch.object(TelegramBot, 'send_message')
    def test_handle_legacy_language_selection(self, mock_send):
        """Test handling legacy language selection"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        bot._handle_legacy_language_selection(123, '🇹🇭|🇺🇸')

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert 'Language pair set' in call_args[0][1]

    @patch.object(TelegramBot, 'send_keyboard')
    @patch.object(TelegramBot, 'delete_message')
    @patch.object(TelegramBot, '_create_language_keyboard')
    def test_handle_first_language_selection(self, mock_create_keyboard, mock_delete, mock_send_keyboard):
        """Test handling first language selection"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        mock_create_keyboard.return_value = [['button1']]

        bot._handle_first_language_selection(123, 'en', 456)

        mock_delete.assert_called_once_with(123, 456)
        mock_send_keyboard.assert_called_once()

    @patch.object(TelegramBot, 'delete_message')
    @patch.object(TelegramBot, '_send_language_pair_confirmation')
    def test_handle_second_language_selection(self, mock_confirm, mock_delete):
        """Test handling second language selection"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        # Mock the database state
        with patch.object(bot.db, 'get_language_selection_state') as mock_get_state:
            mock_get_state.return_value = {'first_lang': 'en'}

            bot._handle_second_language_selection(123, 'ru', 456)

            mock_delete.assert_called_once_with(123, 456)
            mock_confirm.assert_called_once_with(123, 'en', 'ru')

    @patch.object(TelegramBot, 'send_message')
    def test_handle_callback_query_invalid_data(self, mock_send):
        """Test handling callback query with invalid data"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        bot = TelegramBot()

        callback_query = {
            'id': 'callback_123',
            'message': {'chat': {'id': 123}, 'message_id': 456},
            'data': 'invalid_data'
        }

        with patch.object(bot.db, 'get_language_selection_state', return_value=None):
            bot._handle_callback_query(callback_query)

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert 'Invalid callback data' in call_args[0][1]
