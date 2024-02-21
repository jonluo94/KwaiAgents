all: pip-install

pip-install:
	pip install -r requirements.txt
	pip install -r benchmark/requirements.txt

start-fschat-kagentlms_qwen_7b_mat:
	pip install vllm
	pip install "fschat[model_worker,webui]"
	nohup python -m fastchat.serve.controller  --host 0.0.0.0 &
	nohup python -m fastchat.serve.vllm_worker --model-path /home/jonluo/huggingface2/kagentlms_qwen_7b_mat --trust-remote-code --dtype half --max-model-len=4096 &
	nohup python -m fastchat.serve.openai_api_server --host localhost --port 8888 &

stop-fschat:
	@echo "stop-fschat:"
	@for f in $(shell ps -ef | grep 'fastchat' | head -3 | awk '{print $$2}'); do \
        kill -9 $$f; \
        echo "kill $$f"; \
    done

run-docker-compose-postgres:
	docker-compose -f docker-compose-postgres.yml up