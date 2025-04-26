#!/usr/bin/env python3

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call
import subprocess
import time

# Add the src directory to the Python path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils.logger import Logger, LogLevel
from tools.bluetooth import (
    AudioRouter,
    AudioSink,
    AudioSource,
    with_retries,
    send_notification,
    BluetoothManager,
    get_bluetooth_manager,
    AudioRoutingError
)


class TestWithRetries(unittest.TestCase):
    """Test the with_retries decorator"""

    def test_successful_execution(self):
        """Test that the decorated function executes successfully"""
        mock_function = MagicMock(return_value="success")
        decorated_function = with_retries()(mock_function)
        result = decorated_function()
        self.assertEqual(result, "success")
        mock_function.assert_called_once()

    def test_retry_on_exception(self):
        """Test that the function retries on exception"""
        mock_function = MagicMock(side_effect=[ValueError("Error"), "success"])
        decorated_function = with_retries(max_retries=2)(mock_function)
        result = decorated_function()
        self.assertEqual(result, "success")
        self.assertEqual(mock_function.call_count, 2)

    def test_max_retries_exhausted(self):
        """Test that the function raises exception after max retries"""
        error = ValueError("Error")
        mock_function = MagicMock(side_effect=[error, error, error])
        decorated_function = with_retries(max_retries=3)(mock_function)
        with self.assertRaises(ValueError):
            decorated_function()
        self.assertEqual(mock_function.call_count, 3)

    def test_timeout(self):
        """Test that the function times out"""
        def slow_function():
            time.sleep(0.2)
            return "success"
        
        decorated_function = with_retries(timeout=0.1)(slow_function)
        with self.assertRaises(TimeoutError):
            decorated_function()


class TestSendNotification(unittest.TestCase):
    """Test the send_notification function"""

    def setUp(self):
        self.logger = MagicMock(spec=Logger)

    @patch('subprocess.run')
    def test_successful_notification(self, mock_run):
        """Test successful notification"""
        mock_run.return_value.returncode = 0
        result = send_notification("Test Title", "Test Message", self.logger)
        self.assertTrue(result)
        mock_run.assert_called_once()
        
    @patch('subprocess.run')
    def test_failed_notification(self, mock_run):
        """Test failed notification"""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Error"
        result = send_notification("Test Title", "Test Message", self.logger)
        self.assertFalse(result)
        self.logger.log.assert_called_once_with(LogLevel.Warn, "Failed to send notification: Error")


class TestAudioRouter(unittest.TestCase):
    """Test the AudioRouter class"""

    def setUp(self):
        self.logger = MagicMock(spec=Logger)
        self.router = AudioRouter(self.logger)
        
    @patch('subprocess.run')
    def test_list_sinks(self, mock_run):
        """Test listing audio sinks"""
        mock_run.return_value.stdout = "0\talsa_output.pci-0000_00_1f.3.analog-stereo\tFamily 17h/19h HD Audio Controller Analog Stereo\n" + \
                                      "1\tbluez_sink.00_11_22_33_44_55.a2dp_sink\tWH-1000XM4 A2DP Sink"
        mock_run.return_value.returncode = 0
        
        sinks = self.router.list_sinks()
        
        self.assertEqual(len(sinks), 2)
        self.assertEqual(sinks[0].name, "alsa_output.pci-0000_00_1f.3.analog-stereo")
        self.assertFalse(sinks[0].is_bluetooth)
        self.assertEqual(sinks[1].name, "bluez_sink.00_11_22_33_44_55.a2dp_sink")
        self.assertTrue(sinks[1].is_bluetooth)
        
    @patch('subprocess.run')
    def test_list_sources(self, mock_run):
        """Test listing audio sources"""
        mock_run.return_value.stdout = "0\talsa_input.pci-0000_00_1f.3.analog-stereo\tFamily 17h/19h HD Audio Controller Analog Stereo\n" + \
                                      "1\tbluez_source.00_11_22_33_44_55.a2dp_source\tWH-1000XM4 A2DP Source"
        mock_run.return_value.returncode = 0
        
        sources = self.router.list_sources()
        
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0].name, "alsa_input.pci-0000_00_1f.3.analog-stereo")
        self.assertFalse(sources[0].is_bluetooth)
        self.assertEqual(sources[1].name, "bluez_source.00_11_22_33_44_55.a2dp_source")
        self.assertTrue(sources[1].is_bluetooth)
    
    @patch('subprocess.run')
    def test_get_current_sink(self, mock_run):
        """Test getting current sink"""
        mock_run.return_value.stdout = "bluez_sink.00_11_22_33_44_55.a2dp_sink"
        mock_run.return_value.returncode = 0
        
        sink = self.router.get_current_sink()
        
        self.assertEqual(sink, "bluez_sink.00_11_22_33_44_55.a2dp_sink")
        
    @patch('subprocess.run')
    def test_set_default_sink(self, mock_run):
        """Test setting default sink"""
        # Mock list_sinks to return valid sinks
        self.router.list_sinks = MagicMock(return_value=[
            AudioSink(0, "sink1", "Sink 1", False),
            AudioSink(1, "sink2", "Sink 2", True)
        ])
        
        # Mock _save_sink_state
        self.router._save_sink_state = MagicMock()
        
        # Create a test callback
        callback = MagicMock()
        self.router.register_callback(callback)
        
        # Test setting a valid sink
        result = self.router.set_default_sink("sink2")
        
        self.assertTrue(result)
        mock_run.assert_called_once()
        self.router._save_sink_state.assert_called_once_with("sink2")
        callback.assert_called_once_with("sink2")
        
    @patch('subprocess.run')
    def test_set_default_sink_invalid(self, mock_run):
        """Test setting an invalid sink"""
        # Mock list_sinks to return valid sinks
        self.router.list_sinks = MagicMock(return_value=[
            AudioSink(0, "sink1", "Sink 1", False),
            AudioSink(1, "sink2", "Sink 2", True)
        ])
        
        # Test setting an invalid sink
        with self.assertRaises(AudioRoutingError):
            self.router.set_default_sink("nonexistent_sink")
            
        mock_run.assert_not_called()
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="test_sink")
    def test_restore_saved_sink_success(self, mock_file, mock_exists):
        """Test restoring a saved sink"""
        mock_exists.return_value = True
        self.router.list_sinks = MagicMock(return_value=[
            AudioSink(0, "test_sink", "Test Sink", False)
        ])
        self.router.set_default_sink = MagicMock(return_value=True)
        
        result = self.router.restore_saved_sink()
        
        self.assertTrue(result)
        self.router.set_default_sink.assert_called_once_with("test_sink")
        
    @patch('pathlib.Path.exists')
    def test_restore_saved_sink_no_file(self, mock_exists):
        """Test restoring when no saved sink file exists"""
        mock_exists.return_value = False
        
        result = self.router.restore_saved_sink()
        
        self.assertFalse(result)
        
    @patch('time.sleep')
    @patch('subprocess.run')
    def test_switch_to_bluetooth_audio(self, mock_run, mock_sleep):
        """Test switching to Bluetooth audio"""
        self.router.list_sinks = MagicMock(return_value=[
            AudioSink(0, "normal_sink", "Normal Sink", False),
            AudioSink(1, "bluez_sink", "Bluetooth Sink", True)
        ])
        self.router.list_sources = MagicMock(return_value=[
            AudioSource(0, "normal_source", "Normal Source", False),
            AudioSource(1, "bluez_source", "Bluetooth Source", True)
        ])
        self.router.set_default_sink = MagicMock()
        self.router.set_default_source = MagicMock()
        
        result = self.router.switch_to_bluetooth_audio("/org/bluez/hci0/dev_00_11_22_33_44_55")
        
        self.assertTrue(result)
        self.router.set_default_sink.assert_called_once_with("bluez_sink")
        self.router.set_default_source.assert_called_once_with("bluez_source")

    @patch('time.sleep')
    @patch('subprocess.run')
    def test_switch_to_default_audio(self, mock_run, mock_sleep):
        """Test switching to default audio"""
        self.router.list_sinks = MagicMock(return_value=[
            AudioSink(0, "normal_sink", "Normal Sink", False),
            AudioSink(1, "bluez_sink", "Bluetooth Sink", True)
        ])
        self.router.list_sources = MagicMock(return_value=[
            AudioSource(0, "normal_source", "Normal Source", False),
            AudioSource(1, "bluez_source", "Bluetooth Source", True)
        ])
        self.router.set_default_sink = MagicMock()
        self.router.set_default_source = MagicMock()
        
        result = self.router.switch_to_default_audio()
        
        self.assertTrue(result)
        self.router.set_default_sink.assert_called_once_with("normal_sink")
        self.router.set_default_source.assert_called_once_with("normal_source")


class TestBluetoothManager(unittest.TestCase):
    """Basic tests for the BluetoothManager class"""
    
    def setUp(self):
        """Set up test environment"""
        self.logger = MagicMock(spec=Logger)
        
        # Mock dependencies to avoid real D-Bus calls
        self.dbus_patcher = patch('tools.bluetooth.dbus')
        self.dbus_mock = self.dbus_patcher.start()
        
        self.glib_patcher = patch('tools.bluetooth.GLib')
        self.glib_mock = self.glib_patcher.start()
        
        # Mock AudioRouter
        self.audio_router_patcher = patch('tools.bluetooth.AudioRouter')
        self.audio_router_mock = self.audio_router_patcher.start()
        
    def tearDown(self):
        """Tear down test environment"""
        self.dbus_patcher.stop()
        self.glib_patcher.stop()
        self.audio_router_patcher.stop()
        
    @patch('tools.bluetooth.BluetoothManager._init_dbus')
    def test_initialization(self, mock_init_dbus):
        """Test manager initialization"""
        manager = BluetoothManager(self.logger)
        
        mock_init_dbus.assert_called_once()
        self.audio_router_mock.assert_called_once_with(self.logger)
        
    @patch('tools.bluetooth.BluetoothManager._init_dbus')
    @patch('tools.bluetooth.BluetoothManager.find_adapter')
    def test_get_bluetooth_status(self, mock_find_adapter, mock_init_dbus):
        """Test get_bluetooth_status method"""
        manager = BluetoothManager(self.logger)
        manager.adapter = MagicMock()
        manager.adapter.Get.return_value = True
        
        status = manager.get_bluetooth_status()
        
        self.assertTrue(status)
        manager.adapter.Get.assert_called_once_with(
            "org.bluez.Adapter1", "Powered"
        )
        
    @patch('tools.bluetooth.BluetoothManager._init_dbus')
    def test_bluetooth_supported(self, mock_init_dbus):
        """Test bluetooth_supported method"""
        manager = BluetoothManager(self.logger)
        
        # Test when adapter_path is set
        manager.adapter_path = "/org/bluez/hci0"
        self.assertTrue(manager.bluetooth_supported())
        
        # Test when adapter_path is not set
        manager.adapter_path = None
        self.assertFalse(manager.bluetooth_supported())


if __name__ == '__main__':
    unittest.main()