from flask import Flask, request, jsonify, send_from_directory
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import os
from dig_flask_serve.base_model_handler import BaseModelHandler

class DigFlaskApp:
    def __init__(self):
        self.app = Flask(__name__)
        self._threaded_init = True
        self.models = []
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.request_count = 0
        self.fail_count = 0
        self._register_builtin_routes()

    def enable_thread_pool(self, max_workers=8):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def register_model(self, model_handler: BaseModelHandler, url='/predict', methods=['POST']):
        if self._threaded_init:
            init_thread = threading.Thread(target=model_handler.init_model)
            init_thread.start()
            init_thread.join()
        else:
            model_handler.init_model()
        self.app.add_url_rule(url, url, self._generate_predict_endpoint(model_handler), methods=methods)
        self.models.append({'handler': model_handler, 'url': url, 'methods': methods})

    def _generate_predict_endpoint(self, model_handler: BaseModelHandler):
        def predict_endpoint():
            self.request_count += 1
            input_data = request.json
            start_time = time.time()
            def _run_predict():
                try:
                    return model_handler.predict(input_data)
                except Exception as e:
                    self.fail_count += 1
                    return {'error': str(e)}
            future = self.executor.submit(_run_predict)
            result = future.result()
            return jsonify({'result': result, 'elapsed_time': round(time.time() - start_time, 3)})
        return predict_endpoint

    def _register_builtin_routes(self):
        @self.app.route('/health')
        def health():
            return jsonify({'status': 'ok', 'models': len(self.models)})
        @self.app.route('/metrics')
        def metrics():
            return jsonify({
                'total_requests': self.request_count,
                'failed_requests': self.fail_count,
                'registered_models': len(self.models)
            })

        @self.app.route('/')
        @self.app.route('/tool')
        def test_tool():
            base_dir = os.path.dirname(__file__)
            return send_from_directory(os.path.join(base_dir, 'static'), 'index.html')

    def run(self, host='0.0.0.0', port=5000, threaded=True):
        self.app.run(host=host, port=port, threaded=threaded)

def dig_flask():
    return DigFlaskApp()