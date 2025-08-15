import unittest
import tempfile
import random
import string
from unittest.mock import patch, MagicMock
from pathlib import Path

from sqlalchemy import Integer, String

from tunely.utils.config import ConfigManager, Base


# Mock the logger and constants to prevent side effects
@patch('tunely.utils.logger.Logger', new=MagicMock())
@patch('tunely.utils.constants.Constants', new=MagicMock())
class TestConfigManager(unittest.TestCase):
    """
    Unit tests for the ConfigManager class.

    This suite uses a temporary SQLite database file for each test case to
    ensure a clean and isolated environment. Dependencies like the logger
    and constants are mocked to avoid external side effects.
    """

    def setUp(self):
        """
        Set up a temporary database file for each test.

        The test now creates a temporary Path object for the database file
        and passes it directly to ConfigManager.init(). It also clears
        the SQLAlchemy metadata to prevent conflicts between tests.
        """
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = Path(self.temp_dir.name) / "test.db"

        # Reset the ConfigManager class variables for each test
        ConfigManager._engine = None
        ConfigManager._models = {}
        # Clear the SQLAlchemy metadata to prevent table re-creation errors
        Base.metadata.clear()

    def tearDown(self):
        """
        Clean up the temporary database file and directory after each test.
        """
        if ConfigManager._engine:
            ConfigManager._engine.dispose()
            ConfigManager._engine = None

        self.temp_dir.cleanup()

    def _get_unique_section_name(self, prefix="TestSection"):
        """Generates a unique section name to prevent SQLAlchemy warnings."""
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"{prefix}_{suffix}"

    def test_init_creates_database_file_and_engine(self):
        """
        Test that init() successfully creates the database file and an engine.
        """
        self.assertFalse(self.db_file.exists())

        ConfigManager.init(config_file_path=self.db_file)

        self.assertTrue(self.db_file.exists())
        self.assertIsNotNone(ConfigManager._engine)

    def test_create_section_creates_table_and_model(self):
        """
        Test that create_section() creates a table and registers a model.
        """
        ConfigManager.init(config_file_path=self.db_file)

        section_name = self._get_unique_section_name("UserSettings")
        fields = {"username": String, "theme": String}
        ConfigManager.create_section(section_name, fields)

        # Check if the model was registered
        self.assertIn(section_name, ConfigManager._models)

        # Verify the table exists in the database
        engine = ConfigManager._engine
        self.assertTrue(engine.dialect.has_table(engine.connect(), section_name.lower()))

        # Verify the model has the correct columns
        model = ConfigManager._models[section_name]
        self.assertTrue(hasattr(model, 'username'))
        self.assertTrue(hasattr(model, 'theme'))

    def test_create_section_with_defaults(self):
        """
        Test that create_section() correctly applies default values.
        """
        ConfigManager.init(config_file_path=self.db_file)

        section_name = self._get_unique_section_name("AppDefaults")
        fields = {"version": String, "path": String}
        defaults = {"version": "1.0.0", "path": "/data/app"}
        ConfigManager.create_section(section_name, fields, defaults)

        # Read the values back to verify defaults were set
        self.assertEqual(ConfigManager.read_value(section_name, "version"), "1.0.0")
        self.assertEqual(ConfigManager.read_value(section_name, "path"), "/data/app")

    def test_set_and_read_value_creates_and_updates(self):
        """
        Test the full cycle of setting and reading a value.
        """
        ConfigManager.init(config_file_path=self.db_file)
        section_name = self._get_unique_section_name("UserPreferences")
        fields = {"volume": Integer, "language": String}
        ConfigManager.create_section(section_name, fields)

        # Test creating a new value
        ConfigManager.set_value(section_name, "volume", 75)
        self.assertEqual(ConfigManager.read_value(section_name, "volume"), 75)

        # Test updating an existing value
        ConfigManager.set_value(section_name, "volume", 90)
        self.assertEqual(ConfigManager.read_value(section_name, "volume"), 90)

        # Test creating another new value
        ConfigManager.set_value(section_name, "language", "en-US")
        self.assertEqual(ConfigManager.read_value(section_name, "language"), "en-US")

    def test_set_section_defaults_initializes_missing_values(self):
        """
        Test that set_section_defaults() populates a new section with defaults.
        """
        ConfigManager.init(config_file_path=self.db_file)
        section_name = self._get_unique_section_name("AudioSettings")
        fields = {"volume": Integer, "mute": Integer}
        ConfigManager.create_section(section_name, fields)

        defaults = {"volume": 50, "mute": 0}
        ConfigManager.set_section_defaults(section_name, defaults)

        self.assertEqual(ConfigManager.read_value(section_name, "volume"), 50)
        self.assertEqual(ConfigManager.read_value(section_name, "mute"), 0)

    def test_set_section_defaults_does_not_overwrite_existing_values(self):
        """
        Test that set_section_defaults() does not overwrite values that already exist.
        """
        ConfigManager.init(config_file_path=self.db_file)
        section_name = self._get_unique_section_name("AudioSettings")
        fields = {"volume": Integer, "mute": Integer}
        ConfigManager.create_section(section_name, fields)

        # Set an initial value
        ConfigManager.set_value(section_name, "volume", 100)

        defaults = {"volume": 50, "mute": 0}
        ConfigManager.set_section_defaults(section_name, defaults)

        # The volume should still be 100, and mute should be set to 0
        self.assertEqual(ConfigManager.read_value(section_name, "volume"), 100)
        self.assertEqual(ConfigManager.read_value(section_name, "mute"), 0)

    def test_read_section_returns_whole_object(self):
        """
        Test that read_section() returns the full database object.
        """
        ConfigManager.init(config_file_path=self.db_file)
        section_name = self._get_unique_section_name("DisplaySettings")
        fields = {"brightness": Integer, "resolution": String}
        ConfigManager.create_section(section_name, fields)

        ConfigManager.set_value(section_name, "brightness", 80)
        ConfigManager.set_value(section_name, "resolution", "1920x1080")

        section_data = ConfigManager.read_section(section_name)

        self.assertEqual(section_data.brightness, 80)
        self.assertEqual(section_data.resolution, "1920x1080")

    def test_delete_value_sets_value_to_none(self):
        """
        Test that delete_value() sets a specific value to None.
        """
        ConfigManager.init(config_file_path=self.db_file)
        section_name = self._get_unique_section_name("NotificationSettings")
        fields = {"email_notifications": Integer, "sms_notifications": Integer}
        ConfigManager.create_section(section_name, fields)

        ConfigManager.set_value(section_name, "email_notifications", 1)
        ConfigManager.set_value(section_name, "sms_notifications", 1)

        ConfigManager.delete_value(section_name, "email_notifications")

        self.assertIsNone(ConfigManager.read_value(section_name, "email_notifications"))
        self.assertEqual(ConfigManager.read_value(section_name, "sms_notifications"), 1)

    # --- Error Handling Tests ---

    def test_set_value_raises_error_for_invalid_section(self):
        """
        Test that set_value() raises a ValueError for a non-existent section.
        """
        ConfigManager.init(config_file_path=self.db_file)
        with self.assertRaises(ValueError):
            ConfigManager.set_value("NonExistentSection", "key", "value")

    def test_set_value_raises_error_for_invalid_key(self):
        """
        Test that set_value() raises a TypeError for a non-existent column
        when a new row is being created.
        """
        ConfigManager.init(config_file_path=self.db_file)
        section_name = self._get_unique_section_name()
        fields = {"key1": String}
        ConfigManager.create_section(section_name, fields)

        with self.assertRaises(TypeError):
            ConfigManager.set_value(section_name, "non_existent_key", "value")

    def test_set_value_raises_error_for_invalid_key_on_existing_row(self):
        """
        Test that set_value() raises a KeyError for a non-existent column
        when a row already exists.
        """
        ConfigManager.init(config_file_path=self.db_file)
        section_name = self._get_unique_section_name()
        fields = {"key1": String}
        ConfigManager.create_section(section_name, fields)
        ConfigManager.set_value(section_name, "key1", "initial_value")

        with self.assertRaises(KeyError):
            ConfigManager.set_value(section_name, "non_existent_key", "value")

    def test_read_value_raises_error_for_invalid_section(self):
        """
        Test that read_value() raises a ValueError for a non-existent section.
        """
        ConfigManager.init(config_file_path=self.db_file)
        with self.assertRaises(ValueError):
            ConfigManager.read_value("NonExistentSection", "key")

    def test_read_value_raises_error_for_no_data(self):
        """
        Test that read_value() raises a ValueError if the section has no data.
        """
        ConfigManager.init(config_file_path=self.db_file)
        section_name = self._get_unique_section_name("EmptySection")
        fields = {"key": String}
        ConfigManager.create_section(section_name, fields)

        with self.assertRaises(ValueError):
            ConfigManager.read_value(section_name, "key")

    def test_read_value_raises_error_for_invalid_key(self):
        """
        Test that read_value() raises a KeyError for a non-existent column.
        """
        ConfigManager.init(config_file_path=self.db_file)
        section_name = self._get_unique_section_name()
        fields = {"key1": String}
        ConfigManager.create_section(section_name, fields)
        ConfigManager.set_value(section_name, "key1", "value")

        with self.assertRaises(KeyError):
            ConfigManager.read_value(section_name, "non_existent_key")

    def test_delete_value_raises_error_for_invalid_section(self):
        """
        Test that delete_value() raises a ValueError for a non-existent section.
        """
        ConfigManager.init(config_file_path=self.db_file)
        with self.assertRaises(ValueError):
            ConfigManager.delete_value("NonExistentSection", "key")

    def test_delete_value_raises_error_for_no_data(self):
        """
        Test that delete_value() raises a ValueError if the section has no data.
        """
        ConfigManager.init(config_file_path=self.db_file)
        section_name = self._get_unique_section_name("EmptySection")
        fields = {"key": String}
        ConfigManager.create_section(section_name, fields)

        with self.assertRaises(ValueError):
            ConfigManager.delete_value(section_name, "key")

    def test_delete_value_raises_error_for_invalid_key(self):
        """
        Test that delete_value() raises a KeyError for a non-existent column.
        """
        ConfigManager.init(config_file_path=self.db_file)
        section_name = self._get_unique_section_name()
        fields = {"key1": String}
        ConfigManager.create_section(section_name, fields)
        ConfigManager.set_value(section_name, "key1", "value")

        with self.assertRaises(KeyError):
            ConfigManager.delete_value(section_name, "non_existent_key")


if __name__ == '__main__':
    unittest.main()
