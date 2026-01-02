import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import tempfile

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.telegram_bot import TelegramBot


class TestTelegramBot(unittest.TestCase):
    """Test cases for TelegramBot class"""

    def setUp(self):
        """Set up test fixtures"""
        with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
            self.bot = TelegramBot()

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up any database changes if needed
        pass

    @patch('models.telegram_bot.requests.post')
    def test_send_message_success(self, mock_post):
        """Test successful message sending"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.bot.send_message(123, "Test message")

        self.assertTrue(result)
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('chat_id', call_args[1]['json'])
        self.assertIn('text', call_args[1]['json'])

    @patch('models.telegram_bot.requests.post')
    def test_send_message_failure(self, mock_post):
        """Test message sending failure"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        result = self.bot.send_message(123, "Test message")

        self.assertFalse(result)

    @patch('models.telegram_bot.requests.post')
    def test_delete_message_success(self, mock_post):
        """Test successful message deletion"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        result = self.bot.delete_message(123, 456)

        self.assertTrue(result)

    @patch('models.telegram_bot.requests.post')
    def test_delete_message_failure(self, mock_post):
        """Test message deletion failure"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"ok": False}
        mock_post.return_value = mock_response

        result = self.bot.delete_message(123, 456)

        self.assertFalse(result)

    @patch('models.telegram_bot.requests.post')
    def test_send_keyboard_success(self, mock_post):
        """Test successful keyboard sending"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        keyboard = [["Button 1", "Button 2"]]
        result = self.bot.send_keyboard(123, "Test message", keyboard)

        self.assertTrue(result)
        mock_post.assert_called_once()

    def test_get_user_language_pair_default(self):
        """Test getting default language pair"""
        with patch.object(self.bot.db, 'get_user_preferences', return_value=None):
            result = self.bot.get_user_language_pair(123)
            self.assertEqual(result, ('en', 'ru'))

    def test_get_user_language_pair_from_db(self):
        """Test getting language pair from database"""
        with patch.object(self.bot.db, 'get_user_preferences', return_value=('es', 'fr', 'translation')):
            result = self.bot.get_user_language_pair(123)
            self.assertEqual(result, ('es', 'fr'))

    def test_set_user_language_pair_valid(self):
        """Test setting valid language pair"""
        with patch.object(self.bot.db, 'set_user_preferences', return_value=True):
            result = self.bot.set_user_language_pair(123, 'en', 'es')
            self.assertTrue(result)

    def test_set_user_language_pair_invalid_same_lang(self):
        """Test setting invalid language pair (same languages)"""
        result = self.bot.set_user_language_pair(123, 'en', 'en')
        self.assertFalse(result)

    def test_set_user_language_pair_invalid_lang(self):
        """Test setting invalid language pair (invalid language)"""
        result = self.bot.set_user_language_pair(123, 'en', 'invalid')
        self.assertFalse(result)

    @patch('models.telegram_bot.requests.post')
    def test_answer_callback_query_success(self, mock_post):
        """Test successful callback query answer"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.bot.answer_callback_query("callback_123", "Answered")

        self.assertTrue(result)

    def test_create_language_keyboard(self):
        """Test language keyboard creation"""
        keyboard = self.bot._create_language_keyboard()
        self.assertIsInstance(keyboard, list)
        self.assertGreater(len(keyboard), 0)

        # Check that each row has buttons
        for row in keyboard:
            self.assertIsInstance(row, list)
            for button in row:
                self.assertIsInstance(button, tuple)
                self.assertEqual(len(button), 2)  # (text, callback_data)

    def test_create_language_keyboard_with_exclude(self):
        """Test language keyboard creation with excluded language"""
        keyboard = self.bot._create_language_keyboard('en')
        all_buttons = [button for row in keyboard for button in row]
        en_buttons = [btn for btn in all_buttons if btn[1] == 'en']
        self.assertEqual(len(en_buttons), 0)

    def test_get_language_flag(self):
        """Test getting language flags"""
        flag = self.bot._get_language_flag('en')
        self.assertIsInstance(flag, str)
        self.assertNotEqual(flag, '🌍')  # Should not be default

        # Test unknown language
        flag_unknown = self.bot._get_language_flag('unknown')
        self.assertEqual(flag_unknown, '🌍')

    def test_get_language_code_from_button(self):
        """Test extracting language code from button text"""
        # Test valid button format
        code = self.bot._get_language_code_from_button('🇺🇸 English')
        self.assertEqual(code, 'en')

        # Test invalid format
        code_invalid = self.bot._get_language_code_from_button('Invalid')
        self.assertIsNone(code_invalid)

    @patch.object(TelegramBot, 'send_message')
    def test_process_message_text_message(self, mock_send):
        """Test processing text message"""
        update = {
            'message': {
                'chat': {'id': 123},
                'from': {'id': 456, 'first_name': 'Test'},
                'text': 'Hello world',
                'message_id': 789
            }
        }

        with patch.object(self.bot, '_handle_text_message') as mock_handle:
            self.bot.process_message(update)
            mock_handle.assert_called_once()

    @patch.object(TelegramBot, 'send_message')
    def test_process_message_voice_message(self, mock_send):
        """Test processing voice message"""
        update = {
            'message': {
                'chat': {'id': 123},
                'from': {'id': 456, 'first_name': 'Test'},
                'voice': {'file_id': 'voice_123', 'duration': 5}
            }
        }

        with patch.object(self.bot, '_handle_voice_message') as mock_handle:
            self.bot.process_message(update)
            mock_handle.assert_called_once()

    def test_process_message_callback_query(self):
        """Test processing callback query"""
        update = {
            'callback_query': {
                'id': 'callback_123',
                'message': {'chat': {'id': 123}, 'message_id': 456},
                'data': 'test_data'
            }
        }

        with patch.object(self.bot, '_handle_callback_query') as mock_handle:
            self.bot.process_message(update)
            mock_handle.assert_called_once()

    @patch.object(TelegramBot, 'send_message')
    @patch.object(TelegramBot, 'get_user_language_pair')
    @patch.object(TelegramBot, 'update_user_stats')
    def test_handle_text_message_success(self, mock_stats, mock_pair, mock_send):
        """Test successful text message handling"""
        mock_pair.return_value = ('en', 'es')

        message = {
            'chat': {'id': 123},
            'from': {'id': 456, 'first_name': 'Test'},
            'text': 'Hello world',
            'message_id': 789
        }

        with patch.object(self.bot.translator, 'detect_language', return_value='en'), \
             patch.object(self.bot.translator, 'translate_text', return_value='Hola mundo'), \
             patch.object(self.bot.db, 'store_message_translation', return_value=True):

            self.bot._handle_text_message(message, 123, 456, 'Test', 'Hello world')

            # Should call send_message with translation
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            self.assertIn('Hello world', call_args[1])
            self.assertIn('Hola mundo', call_args[1])

    @patch.object(TelegramBot, 'send_message')
    def test_handle_text_message_already_in_target_lang(self, mock_send):
        """Test text message already in target language"""
        with patch.object(self.bot, 'get_user_language_pair', return_value=('en', 'es')), \
             patch.object(self.bot.translator, 'detect_language', return_value='es'):

            message = {
                'chat': {'id': 123},
                'from': {'id': 456, 'first_name': 'Test'},
                'text': 'Hola mundo'
            }

            self.bot._handle_text_message(message, 123, 456, 'Test', 'Hola mundo')

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            self.assertIn('Already in', call_args[1])

    @patch.object(TelegramBot, 'send_message')
    @patch.object(TelegramBot, '_send_transcription_error')
    @patch.object(TelegramBot, 'get_user_language_pair')
    def test_handle_voice_message_no_pair(self, mock_pair, mock_error, mock_send):
        """Test voice message handling when no language pair is set"""
        mock_pair.return_value = ('', '')

        message = {
            'chat': {'id': 123},
            'from': {'id': 456, 'first_name': 'Test'},
            'voice': {'file_id': 'voice_123', 'duration': 5}
        }

        with patch.object(self.bot, '_transcribe_with_fallback', return_value=('Hello', 'en')), \
             patch.object(self.bot, '_send_transcription_only') as mock_transcription:

            self.bot._handle_voice_message(message, 123, 456, 'Test')

            mock_transcription.assert_called_once()

    @patch.object(TelegramBot, 'send_message')
    @patch.object(TelegramBot, 'get_user_language_pair')
    @patch.object(TelegramBot, 'update_user_stats')
    def test_handle_voice_message_success(self, mock_stats, mock_pair, mock_send):
        """Test successful voice message handling"""
        mock_pair.return_value = ('en', 'es')

        message = {
            'chat': {'id': 123},
            'from': {'id': 456, 'first_name': 'Test'},
            'voice': {'file_id': 'voice_123', 'duration': 5},
            'message_id': 789
        }

        with patch.object(self.bot, '_transcribe_with_fallback', return_value=('Hello', 'en')), \
             patch.object(self.bot.translator, 'translate_text', return_value='Hola'), \
             patch.object(self.bot.db, 'store_message_translation', return_value=True), \
             patch.object(self.bot, '_determine_target_language', return_value='es'):

            self.bot._handle_voice_message(message, 123, 456, 'Test')

            mock_send.assert_called_once()

    def test_determine_target_language_en_to_es(self):
        """Test target language determination: English to Spanish"""
        result = self.bot._determine_target_language('en', 'en', 'es')
        self.assertEqual(result, 'es')

    def test_determine_target_language_es_to_en(self):
        """Test target language determination: Spanish to English"""
        result = self.bot._determine_target_language('es', 'en', 'es')
        self.assertEqual(result, 'en')

    def test_determine_target_language_not_in_pair(self):
        """Test target language determination: language not in pair"""
        result = self.bot._determine_target_language('fr', 'en', 'es')
        self.assertIsNone(result)

    @patch.object(TelegramBot, 'send_keyboard')
    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_start(self, mock_send, mock_keyboard):
        """Test /start command"""
        self.bot._handle_command(123, 456, '/start')

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        self.assertIn('Welcome', call_args[1])

    @patch.object(TelegramBot, 'send_keyboard')
    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_setpair(self, mock_send, mock_keyboard):
        """Test /setpair command"""
        with patch.object(self.bot.db, 'clear_language_selection_state', return_value=True), \
             patch.object(self.bot.db, 'set_language_selection_state', return_value=True), \
             patch.object(self.bot, '_create_language_keyboard') as mock_create_keyboard:

            mock_create_keyboard.return_value = [['Button1', 'Button2']]

            self.bot._handle_command(123, 456, '/setpair')

            mock_keyboard.assert_called_once()
            call_args = mock_keyboard.call_args[0]
            self.assertIn('Step 1', call_args[1])

    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_stats(self, mock_send):
        """Test /stats command"""
        with patch.object(self.bot.db, 'get_user_stats', return_value={'translations': 10, 'joined': '2023-01-01'}), \
             patch.object(self.bot, 'get_user_language_pair', return_value=('en', 'es')):

            self.bot._handle_command(123, 456, '/stats')

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            self.assertIn('Translation Stats', call_args[1])

    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_unknown(self, mock_send):
        """Test unknown command"""
        self.bot._handle_command(123, 456, '/unknown')

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        self.assertIn('Unknown command', call_args[1])

    @patch.object(TelegramBot, 'send_message')
    @patch.object(TelegramBot, 'delete_message')
    def test_handle_callback_query_language_selection(self, mock_delete, mock_send):
        """Test callback query for language selection"""
        callback_query = {
            'id': 'callback_123',
            'message': {'chat': {'id': 123}, 'message_id': 456},
            'data': 'en'
        }

        with patch.object(self.bot.db, 'get_language_selection_state', return_value={'step': 'first_lang'}), \
             patch.object(self.bot, '_handle_language_selection') as mock_handle:

            self.bot._handle_callback_query(callback_query)

            mock_handle.assert_called_once()

    @patch.object(TelegramBot, 'answer_callback_query')
    @patch.object(TelegramBot, 'send_message')
    def test_handle_callback_query_invalid_data(self, mock_send, mock_answer):
        """Test callback query with invalid data"""
        callback_query = {
            'id': 'callback_123',
            'message': {'chat': {'id': 123}, 'message_id': 456},
            'data': 'invalid_data'
        }

        with patch.object(self.bot.db, 'get_language_selection_state', return_value=None):
            self.bot._handle_callback_query(callback_query)

            mock_send.assert_called_once()
            mock_answer.assert_called_once()

    def test_extract_language_code_direct(self):
        """Test extracting language code directly"""
        result = self.bot._extract_language_code('en')
        self.assertEqual(result, 'en')

    def test_extract_language_code_from_button(self):
        """Test extracting language code from button text"""
        with patch.object(self.bot, '_get_language_code_from_button', return_value='es'):
            result = self.bot._extract_language_code('🇪🇸 Spanish')
            self.assertEqual(result, 'es')

    @patch.object(TelegramBot, 'delete_message')
    @patch.object(TelegramBot, 'send_keyboard')
    @patch.object(TelegramBot, 'send_message')
    def test_handle_first_language_selection(self, mock_send, mock_keyboard, mock_delete):
        """Test first language selection"""
        with patch.object(self.bot.db, 'set_language_selection_state', return_value=True):
            self.bot._handle_first_language_selection(123, 'en', 456)

            mock_delete.assert_called_once_with(123, 456)
            mock_keyboard.assert_called_once()

    @patch.object(TelegramBot, 'delete_message')
    @patch.object(TelegramBot, 'send_message')
    def test_handle_second_language_selection_success(self, mock_send, mock_delete):
        """Test successful second language selection"""
        state = {'first_lang': 'en'}

        with patch.object(self.bot.db, 'get_language_selection_state', return_value=state), \
             patch.object(self.bot, 'set_user_language_pair', return_value=True), \
             patch.object(self.bot, '_send_language_pair_confirmation') as mock_confirm, \
             patch.object(self.bot.db, 'clear_language_selection_state') as mock_clear:

            self.bot._handle_second_language_selection(123, 'es', 456)

            mock_delete.assert_called_once_with(123, 456)
            mock_confirm.assert_called_once_with(123, 'en', 'es')
            mock_clear.assert_called_once_with(123)

    @patch.object(TelegramBot, 'send_message')
    def test_send_language_pair_confirmation(self, mock_send):
        """Test language pair confirmation message"""
        self.bot._send_language_pair_confirmation(123, 'en', 'es')

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        self.assertIn('Language pair set', call_args[1])

    def test_handle_legacy_language_selection(self):
        """Test legacy language selection format"""
        with patch.object(self.bot, '_get_language_from_flag') as mock_flag, \
             patch.object(self.bot, 'set_user_language_pair', return_value=True), \
             patch.object(self.bot, 'send_message') as mock_send:

            mock_flag.side_effect = ['en', 'es']

            self.bot._handle_legacy_language_selection(123, '🇺🇸|🇪🇸')

            mock_send.assert_called_once()

    def test_get_language_from_flag(self):
        """Test getting language from flag emoji"""
        result = self.bot._get_language_from_flag('🇺🇸')
        self.assertEqual(result, 'en')

        result_unknown = self.bot._get_language_from_flag('🏳️')
        self.assertIsNone(result_unknown)

    @patch.object(TelegramBot, 'send_message')
    def test_handle_edited_message_with_translation(self, mock_send):
        """Test handling edited message with previous translation"""
        previous_translation = {
            'translated_text': 'Old translation',
            'source_lang': 'en',
            'target_lang': 'es'
        }

        message = {
            'chat': {'id': 123},
            'from': {'id': 456, 'first_name': 'Test'},
            'text': 'New text',
            'message_id': 789
        }

        with patch.object(self.bot.db, 'get_message_translation', return_value=previous_translation), \
             patch.object(self.bot, '_build_edit_response_header') as mock_build_header, \
             patch.object(self.bot, '_get_target_language_for_edit', return_value='es'), \
             patch.object(self.bot, '_build_new_translation_response') as mock_build_new:

            mock_build_header.return_value = "Header text"
            mock_build_new.return_value = "New translation"

            self.bot._handle_edited_message_with_previous_translation(message, 123, 456, 789, 'New text', previous_translation)

            mock_send.assert_called_once()

    @patch.object(TelegramBot, 'send_message')
    def test_handle_edited_message_no_translation(self, mock_send):
        """Test handling edited message without previous translation"""
        message = {
            'chat': {'id': 123},
            'from': {'id': 456, 'first_name': 'Test'},
            'text': 'New text',
            'message_id': 789
        }

        with patch.object(self.bot.db, 'get_message_translation', return_value=None), \
             patch.object(self.bot, '_handle_message') as mock_handle:

            self.bot._handle_edited_message(message)

            mock_handle.assert_called_once_with(message)

    @patch.object(TelegramBot, 'send_message')
    def test_send_transcription_only(self, mock_send):
        """Test sending transcription-only response"""
        self.bot._send_transcription_only(123, 'Test', 'Hello world', 'en', tip=True)

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        self.assertIn('Transcription', call_args[1])
        self.assertIn('Hello world', call_args[1])

    @patch.object(TelegramBot, 'send_message')
    def test_send_transcription_error(self, mock_send):
        """Test sending transcription error"""
        self.bot._send_transcription_error(123, 'Test')

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        self.assertIn('transcription failed', call_args[1].lower())

    @patch.object(TelegramBot, 'send_message')
    def test_send_translation_error(self, mock_send):
        """Test sending translation error"""
        self.bot._send_translation_error(123, 'Test', 'Hello world')

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        self.assertIn('translation failed', call_args[1].lower())

    @patch.object(TelegramBot, 'send_message')
    def test_handle_successful_voice_translation(self, mock_send):
        """Test handling successful voice translation"""
        message = {'message_id': 789}

        with patch.object(self.bot, 'update_user_stats'), \
             patch.object(self.bot.db, 'store_message_translation'):

            self.bot._handle_successful_voice_translation(123, message, 456, 'Test', 'Hello', 'Hola', 'en', 'es')

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            self.assertIn('Voice Translation', call_args[1])

    def test_transcribe_with_fallback_success(self):
        """Test transcription with fallback success"""
        with patch.object(self.bot.voice_transcriber, 'transcribe_voice_message_with_confidence') as mock_transcribe, \
             patch.object(self.bot.translator, 'detect_language', return_value='en'):

            mock_result = MagicMock()
            mock_result.text = 'Hello world'
            mock_result.service = 'whisper'
            mock_result.confidence = 0.9
            mock_transcribe.return_value = mock_result

            result = self.bot._transcribe_with_fallback('file_123')

            self.assertEqual(result, ('Hello world', 'en'))

    def test_transcribe_with_fallback_failure(self):
        """Test transcription with fallback failure"""
        with patch.object(self.bot.voice_transcriber, 'transcribe_voice_message_with_confidence', return_value=None):
            result = self.bot._transcribe_with_fallback('file_123')
            self.assertIsNone(result)

    def test_update_user_stats(self):
        """Test updating user statistics"""
        with patch.object(self.bot.db, 'update_user_stats', return_value=True):
            result = self.bot.update_user_stats(456)
            self.assertTrue(result)

    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_help(self, mock_send):
        """Test /help command"""
        self.bot._handle_command(123, 456, '/help')

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        self.assertIn('Help', call_args[1])

    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_languages(self, mock_send):
        """Test /languages command"""
        self.bot._handle_command(123, 456, '/languages')

        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        self.assertIn('Supported Languages', call_args[1])

    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_chatmode_toggle_to_chat(self, mock_send):
        """Test /chatmode command toggle to chat mode"""
        with patch.object(self.bot.db, 'get_chat_mode', return_value='translation'), \
             patch.object(self.bot.db, 'set_chat_mode', return_value=True), \
             patch.object(self.bot, 'get_user_language_pair', return_value=('en', 'es')):

            self.bot._handle_command(123, 456, '/chatmode')

            # Should send message about enabling chat mode
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            self.assertIn('Chat Mode Enabled', call_args[1])

    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_chatmode_toggle_to_translation(self, mock_send):
        """Test /chatmode command toggle to translation mode"""
        with patch.object(self.bot.db, 'get_chat_mode', return_value='chat'), \
             patch.object(self.bot.db, 'set_chat_mode', return_value=True), \
             patch.object(self.bot, 'get_user_language_pair', return_value=('en', 'es')):

            self.bot._handle_command(123, 456, '/chatmode')

            # Should send message about enabling translation mode
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            self.assertIn('Translation Mode Enabled', call_args[1])

    def test_create_google_credentials_success(self):
        """Test creating Google credentials successfully"""
        import json
        with patch.dict(os.environ, {'GOOGLE_APPLICATION_CREDENTIALS_JSON': '{"type": "service_account"}'}), \
             patch('models.telegram_bot.json.loads', return_value={'type': 'service_account'}), \
             patch('models.telegram_bot.service_account.Credentials.from_service_account_info') as mock_creds:

            mock_creds.return_value = MagicMock()
            result = self.bot._create_google_credentials()
            self.assertIsNotNone(result)
            mock_creds.assert_called_once()

    def test_create_google_credentials_no_json(self):
        """Test creating Google credentials with no JSON"""
        with patch.object(self.bot.voice_transcriber, 'google_credentials_json', ''):
            result = self.bot._create_google_credentials()
            self.assertIsNone(result)

    def test_transcribe_with_google_speech_success(self):
        """Test Google Speech transcription success"""
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name

        try:
            mock_response = MagicMock()
            mock_response.results = [MagicMock(alternatives=[MagicMock(transcript='Hello world')])]

            with patch('models.telegram_bot.speech.SpeechClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client.recognize.return_value = mock_response
                mock_client_class.return_value = mock_client

                result = self.bot._transcribe_with_google_speech(temp_path, 'en-US')
                self.assertEqual(result, 'Hello world')

        finally:
            os.unlink(temp_path)

    def test_transcribe_with_google_speech_no_results(self):
        """Test Google Speech transcription with no results"""
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name

        try:
            mock_response = MagicMock()
            mock_response.results = []

            with patch('models.telegram_bot.speech.SpeechClient') as mock_client_class:
                mock_client = MagicMock()
                mock_client.recognize.return_value = mock_response
                mock_client_class.return_value = mock_client

                result = self.bot._transcribe_with_google_speech(temp_path, 'en-US')
                self.assertIsNone(result)

        finally:
            os.unlink(temp_path)

    @patch.object(TelegramBot, 'send_message')
    def test_handle_edited_message_no_previous_translation(self, mock_send):
        """Test handling edited message without previous translation"""
        message = {
            'chat': {'id': 123},
            'from': {'id': 456, 'first_name': 'Test'},
            'text': 'New text',
            'message_id': 789
        }

        with patch.object(self.bot.db, 'get_message_translation', return_value=None), \
             patch.object(self.bot, '_handle_message') as mock_handle:

            self.bot._handle_edited_message(message)

            mock_handle.assert_called_once_with(message)

    @patch.object(TelegramBot, 'send_message')
    def test_handle_edited_message_with_previous_translation(self, mock_send):
        """Test handling edited message with previous translation"""
        previous_translation = {
            'translated_text': 'Old translation',
            'source_lang': 'en',
            'target_lang': 'es'
        }

        message = {
            'chat': {'id': 123},
            'from': {'id': 456, 'first_name': 'Test'},
            'text': 'New text edited',
            'message_id': 789
        }

        with patch.object(self.bot.db, 'get_message_translation', return_value=previous_translation), \
             patch.object(self.bot, '_build_edit_response_header', return_value='Header text'), \
             patch.object(self.bot, '_get_target_language_for_edit', return_value='es'), \
             patch.object(self.bot, '_build_new_translation_response', return_value='New translation text'):

            self.bot._handle_edited_message_with_previous_translation(message, 123, 456, 789, 'New text edited', previous_translation)

            mock_send.assert_called_once()

    def test_get_target_language_for_edit_found(self):
        """Test getting target language for edited message when found"""
        with patch.object(self.bot, 'get_user_language_pair', return_value=('en', 'es')), \
             patch.object(self.bot.translator, 'detect_language', return_value='en'):

            result = self.bot._get_target_language_for_edit(123, 'New text')
            self.assertEqual(result, 'es')

    def test_get_target_language_for_edit_not_found(self):
        """Test getting target language for edited message when not found"""
        with patch.object(self.bot, 'get_user_language_pair', return_value=('en', 'es')), \
             patch.object(self.bot.translator, 'detect_language', return_value='fr'):

            result = self.bot._get_target_language_for_edit(123, 'New text')
            self.assertIsNone(result)

    @patch.object(TelegramBot, 'send_message')
    def test_build_new_translation_response_with_translation(self, mock_send):
        """Test building new translation response when translation succeeds"""
        with patch.object(self.bot.translator, 'translate_text', return_value='Nueva traducción'), \
             patch.object(self.bot.db, 'store_message_translation'):

            result = self.bot._build_new_translation_response('New text', 'en', 'es', 123, 789, 456)
            self.assertIn('New Translation', result)

    def test_build_new_translation_response_already_in_target(self):
        """Test building new translation response when text is already in target language"""
        result = self.bot._build_new_translation_response('New text', 'es', 'es', 123, 789, 456)
        self.assertIn('already in target language', result)

    def test_build_new_translation_response_failed(self):
        """Test building new translation response when translation fails"""
        with patch.object(self.bot.translator, 'translate_text', return_value=None):
            result = self.bot._build_new_translation_response('New text', 'en', 'es', 123, 789, 456)
            self.assertIn('failed', result)

    def test_build_edit_response_header(self):
        """Test building edit response header"""
        previous_translation = {'translated_text': 'Old translation'}
        result = self.bot._build_edit_response_header('TestUser', 'New text', previous_translation)

        self.assertIn('Message Edited', result)
        self.assertIn('TestUser', result)
        self.assertIn('New text', result)
        self.assertIn('Old translation', result)

    @patch.object(TelegramBot, 'send_message')
    def test_handle_legacy_language_selection_success(self, mock_send):
        """Test handling legacy language selection successfully"""
        with patch.object(self.bot, '_get_language_from_flag', side_effect=['en', 'es']), \
             patch.object(self.bot, 'set_user_language_pair', return_value=True):

            self.bot._handle_legacy_language_selection(123, '🇺🇸|🇪🇸')

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            self.assertIn('Language pair set', call_args[1])

    def test_handle_legacy_language_selection_invalid_flag(self):
        """Test handling legacy language selection with invalid flag"""
        with patch.object(self.bot, '_get_language_from_flag', side_effect=[None, 'es']), \
             patch.object(self.bot, 'set_user_language_pair', return_value=False):

            # Should not crash, just not send message or handle error gracefully
            self.bot._handle_legacy_language_selection(123, 'invalid|🇪🇸')

    def test_get_language_from_flag_known_flags(self):
        """Test getting language from various known flag emojis"""
        test_cases = [
            ('🇺🇸', 'en'),
            ('🇪🇸', 'es'),
            ('🇷🇺', 'ru'),
            ('🇨🇳', 'zh'),
            ('🇯🇵', 'ja'),
            ('🇰🇷', 'ko'),
            ('🇩🇪', 'de'),
            ('🇫🇷', 'fr'),
            ('🇮🇹', 'it'),
            ('🇵🇹', 'pt'),
        ]

        for flag, expected_lang in test_cases:
            with self.subTest(flag=flag):
                result = self.bot._get_language_from_flag(flag)
                self.assertEqual(result, expected_lang)

    def test_get_language_from_flag_unknown_flag(self):
        """Test getting language from unknown flag emoji"""
        result = self.bot._get_language_from_flag('🏴')
        self.assertIsNone(result)

    @patch('models.telegram_bot.requests.post')
    def test_answer_callback_query_with_text(self, mock_post):
        """Test answering callback query with custom text"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = self.bot.answer_callback_query("callback_123", "Custom text")

        self.assertTrue(result)
        call_args = mock_post.call_args
        self.assertIn('text', call_args[1]['json'])
        self.assertEqual(call_args[1]['json']['text'], 'Custom text')

    @patch.object(TelegramBot, 'send_message')
    def test_send_message_with_parse_mode(self, mock_send):
        """Test sending message with custom parse mode"""
        mock_send.return_value = True
        result = self.bot.send_message(123, "*Bold text*", parse_mode='Markdown')
        self.assertTrue(result)

    @patch.object(TelegramBot, 'send_keyboard')
    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_setpair_with_existing_state(self, mock_send, mock_keyboard):
        """Test /setpair command when language selection state already exists"""
        with patch.object(self.bot.db, 'clear_language_selection_state'), \
             patch.object(self.bot.db, 'set_language_selection_state', return_value=True), \
             patch.object(self.bot, '_create_language_keyboard', return_value=[['Button']]):

            self.bot._handle_command(123, 456, '/setpair')

            mock_keyboard.assert_called_once()

    def test_process_message_edited_message(self):
        """Test processing edited message"""
        update = {
            'edited_message': {
                'chat': {'id': 123},
                'from': {'id': 456, 'first_name': 'Test'},
                'text': 'Edited text',
                'message_id': 789
            }
        }

        with patch.object(self.bot, '_handle_edited_message') as mock_handle:
            self.bot.process_message(update)
            mock_handle.assert_called_once()

    @patch.object(TelegramBot, 'send_message')
    def test_handle_text_message_with_chat_mode(self, mock_send):
        """Test text message handling in chat mode"""
        with patch.object(self.bot.db, 'get_chat_mode', return_value='chat'):
            message = {
                'chat': {'id': 123},
                'from': {'id': 456, 'first_name': 'Test'},
                'text': 'Hello in chat mode'
            }

            self.bot._handle_text_message(message, 123, 456, 'Test', 'Hello in chat mode')

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            self.assertIn('Chat Mode', call_args[1])

    @patch.object(TelegramBot, 'send_message')
    def test_handle_text_message_translation_failure(self, mock_send):
        """Test text message handling when translation fails"""
        with patch.object(self.bot.db, 'get_chat_mode', return_value='translation'), \
             patch.object(self.bot, 'get_user_language_pair', return_value=('en', 'es')), \
             patch.object(self.bot.translator, 'detect_language', return_value='en'), \
             patch.object(self.bot.translator, 'translate_text', return_value=None):

            message = {
                'chat': {'id': 123},
                'from': {'id': 456, 'first_name': 'Test'},
                'text': 'Hello world'
            }

            self.bot._handle_text_message(message, 123, 456, 'Test', 'Hello world')

            # Should send error message
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            self.assertIn('Translation failed', call_args[1])


if __name__ == '__main__':
    unittest.main()
