import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from migrateit.models import ChangelogFile, SupportedDatabase
from migrateit.tree import (
    create_changelog_file,
    create_migration_directory,
    create_new_migration,
    load_changelog_file,
    save_changelog_file,
)


@patch("migrateit.reporters.output.write_line_b", lambda *_: None)
class TestTreeUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.migrations_dir = self.temp_dir / "migrations"
        self.migrations_file_path = self.temp_dir / "changelog.json"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_create_migrations_dir_success(self):
        create_migration_directory(self.migrations_dir)
        self.assertTrue(os.path.exists(self.migrations_dir))

    def test_create_migrations_dir_already_exists(self):
        os.makedirs(self.migrations_dir)
        create_migration_directory(self.migrations_dir)
        self.assertTrue(os.path.exists(self.migrations_dir))

    def test_create_migrations_file_success(self):
        create_changelog_file(self.migrations_file_path, SupportedDatabase.POSTGRES)
        self.assertTrue(os.path.exists(self.migrations_file_path))

    def test_create_migrations_file_already_exists(self):
        Path(self.migrations_file_path).touch()
        with self.assertRaises(ValueError):
            create_changelog_file(self.migrations_file_path, SupportedDatabase.POSTGRES)

    def test_create_migrations_file_invalid_extension(self):
        bad_path = self.temp_dir / "migrations.txt"
        with self.assertRaises(ValueError):
            create_changelog_file(bad_path, SupportedDatabase.POSTGRES)

    def test_load_migrations_file_success(self):
        file = ChangelogFile(version=1, path=self.migrations_file_path)
        with open(self.migrations_file_path, "w") as f:
            f.write(file.to_json())

        loaded = load_changelog_file(self.migrations_file_path)
        self.assertIsInstance(loaded, ChangelogFile)
        self.assertEqual(loaded.version, 1)

    def test_load_migrations_file_not_exists(self):
        with self.assertRaises(FileNotFoundError):
            load_changelog_file(self.migrations_file_path)

    def test_save_migrations_file_success(self):
        file = ChangelogFile(version=2, path=self.migrations_file_path)
        Path(self.migrations_file_path).touch()
        save_changelog_file(file)

        with open(self.migrations_file_path) as f:
            content = f.read()
        self.assertIn('"version": 2', content)

    def test_save_migrations_file_not_exists(self):
        file = ChangelogFile(version=1, path=self.migrations_file_path)
        with self.assertRaises(FileNotFoundError):
            save_changelog_file(file)

    def test_create_new_migration_success(self):
        os.makedirs(self.migrations_dir)
        create_changelog_file(self.migrations_file_path, SupportedDatabase.POSTGRES)
        changelog = load_changelog_file(self.migrations_file_path)

        create_new_migration(changelog, self.migrations_dir, "init")
        created_files = os.listdir(self.migrations_dir)

        self.assertEqual(len(created_files), 1)
        self.assertRegex(created_files[0], r"0000_init\.sql")

        migrations = load_changelog_file(self.migrations_file_path)
        self.assertEqual(len(migrations.migrations), 1)
        self.assertTrue(migrations.migrations[0].name.endswith("init.sql"))

    def test_create_new_migration_with_dependencies(self):
        os.makedirs(self.migrations_dir)
        create_changelog_file(self.migrations_file_path, SupportedDatabase.POSTGRES)
        changelog = load_changelog_file(self.migrations_file_path)

        create_new_migration(changelog, self.migrations_dir, "init")
        create_new_migration(changelog, self.migrations_dir, "add_users", dependencies=["0000"])
        created_files = os.listdir(self.migrations_dir)
        created_files.sort()

        self.assertEqual(len(created_files), 2)
        self.assertRegex(created_files[0], r"0000_init\.sql")
        self.assertRegex(created_files[1], r"0001_add_users\.sql")

        migrations = load_changelog_file(self.migrations_file_path)
        self.assertEqual(len(migrations.migrations), 2)
        self.assertTrue(migrations.migrations[1].name.endswith("add_users.sql"))
        self.assertIn("init", migrations.migrations[1].parents[0])

    def test_create_new_migration_invalid_name(self):
        os.makedirs(self.migrations_dir)
        create_changelog_file(self.migrations_file_path, SupportedDatabase.POSTGRES)
        changelog = load_changelog_file(self.migrations_file_path)

        with self.assertRaises(ValueError):
            create_new_migration(changelog, self.migrations_dir, "123-bad-name")

        with self.assertRaises(ValueError):
            create_new_migration(changelog, self.migrations_dir, "")
