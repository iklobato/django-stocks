from django.test import TestCase
from unittest.mock import patch, MagicMock
from .stock_callback import process_stock_request

class StockCallbackTest(TestCase):
    """Test the stock callback function used by RabbitMQ"""
    
    @patch('stocks.stock_callback.requests.get')
    def test_process_stock_request_success(self, mock_get):
        """Test successful stock request processing"""
        # Mock CSV response
        mock_response = MagicMock()
        mock_response.content = b'Symbol,Name,Open,High,Low,Close,Volume\nAAPL,APPLE INC,150.0,155.0,149.0,152.0,1000000'
        mock_get.return_value = mock_response
        
        # Call the function
        result = process_stock_request({'stock_code': 'AAPL'})
        
        # Verify result
        self.assertEqual(result['status'], 200)
        self.assertEqual(result['data']['symbol'], 'AAPL')
        self.assertEqual(result['data']['name'], 'APPLE INC')
        self.assertEqual(result['data']['open'], 150.0)
        self.assertEqual(result['data']['high'], 155.0)
        self.assertEqual(result['data']['low'], 149.0)
        self.assertEqual(result['data']['close'], 152.0)
        self.assertEqual(result['data']['volume'], 1000000)
        
    def test_process_stock_request_missing_code(self):
        """Test stock request with missing stock code"""
        result = process_stock_request({})
        self.assertEqual(result['status'], 400)
        self.assertIn('error', result)
        
    @patch('stocks.stock_callback.requests.get')
    def test_process_stock_request_na_data(self, mock_get):
        """Test stock request with N/A data"""
        # Mock CSV response with N/A values
        mock_response = MagicMock()
        mock_response.content = b'Symbol,Name,Open,High,Low,Close,Volume\nAAPL,APPLE INC,N/A,N/A,N/A,N/A,0'
        mock_get.return_value = mock_response
        
        # Call the function
        result = process_stock_request({'stock_code': 'AAPL'})
        
        # Verify result
        self.assertEqual(result['status'], 404)
        self.assertIn('error', result)
